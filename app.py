from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import PlainTextResponse
import httpx
import os
import tempfile
import subprocess
from pathlib import Path

app = FastAPI()

OPENAI_BASE = "https://api.openai.com/v1"

def run_ffprobe_duration(p: Path) -> float | None:
    try:
        out = subprocess.check_output(
            ["ffprobe","-v","error","-show_entries","format=duration","-of","default=nokey=1:noprint_wrappers=1",str(p)],
            stderr=subprocess.STDOUT, text=True
        ).strip()
        return float(out) if out else None
    except Exception:
        return None

def split_to_chunks(src: Path, seconds: int = 15*60) -> list[Path]:
    tmp = Path(tempfile.mkdtemp(prefix="chunks_"))
    dst_pattern = str(tmp / "chunk_%03d" + src.suffix.lower())
    subprocess.check_call([
        "ffmpeg","-hide_banner","-loglevel","error",
        "-i", str(src),
        "-f","segment","-segment_time",str(seconds),
        "-c","copy","-reset_timestamps","1", dst_pattern
    ])
    return sorted(tmp.glob("chunk_*"+src.suffix.lower()))

async def transcribe_file(client: httpx.Client, api_key: str, model: str, p: Path) -> str:
    with open(p, "rb") as f:
        r = client.post(
            f"{OPENAI_BASE}/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (p.name, f, "application/octet-stream")},
            data={"model": model, "response_format":"text"},
            timeout=180
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.text

@app.post("/transcribe", response_class=PlainTextResponse)
def transcribe(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    model: str = Form("gpt-4o-mini-transcribe")
):
    # sichere Ablage
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or "audio").suffix) as tmp:
        tmp.write(file.file.read())
        src = Path(tmp.name)

    try:
        # ggf. in 15-Minuten-Chunks teilen (Render hat 15-min CPU-Limits auch praktisch)
        dur = run_ffprobe_duration(src)
        if dur and dur > 1400:
            chunks = split_to_chunks(src, 15*60)
            text_parts = []
            with httpx.Client(http2=False, timeout=180) as client:
                for i, ch in enumerate(chunks, 1):
                    text_parts.append(transcribe_file(client, api_key, model, ch))
            # sync gather
            final = ""
            for t in text_parts:
                final += (t if isinstance(t, str) else str(t))
            return final.strip() + "\n"
        else:
            with httpx.Client(http2=False, timeout=180) as client:
                return transcribe_file(client, api_key, model, src).strip() + "\n"
    finally:
        try: src.unlink(missing_ok=True)
        except: pass
