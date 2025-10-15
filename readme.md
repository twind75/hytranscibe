# hytranscribe

Ein schlankes Transkriptions-Tool (offline via Faster-Whisper + optional OpenAI-API, mit Auto-Chunking und Watch-Folder).  
Ziel: einfache Web/GUI-Nutzung und Export als TXT.

## Aktueller Status
MVP in Arbeit. Deployment-Ziel: Render (Free Tier) + GitHub CI.

## Features (geplant/teilweise vorhanden)
- Offline-Transkription mit `faster-whisper`
- Optional Online via OpenAI API (Chunking > 15 min)
- Auto-Chunking langer Dateien (ffmpeg)
- Watch-Folder & Einzeldatei
- TXT-Export

## Quick Start (lokal)
```bash
python -m venv .venv
.\.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python scripts/offline_transcriber_gui.py
