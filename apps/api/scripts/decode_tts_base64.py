#!/usr/bin/env python3
"""
Decode tts_audio_base64 from a /speak/ JSON response and verify it is real speech.

Usage:
  1. Copy the tts_audio_base64 string from DevTools (no quotes).
  2. Save to tts.b64.txt OR pass as first argument.
  3. python apps/api/scripts/decode_tts_base64.py tts.b64.txt

Writes interview_decoded.mp3 and prints volume analysis.
"""

from __future__ import annotations

import base64
import re
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) > 1:
        raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        print("Paste base64 (end with empty line), then Ctrl+Z Enter on Windows:")
        raw = sys.stdin.read()
    # Strip JSON quotes / whitespace
    b64 = re.sub(r"\s+", "", raw.strip().strip('"').strip("'"))
    if b64.startswith("data:"):
        b64 = b64.split(",", 1)[-1]
    try:
        audio = base64.b64decode(b64, validate=False)
    except Exception as exc:
        print(f"Invalid base64: {exc}")
        sys.exit(1)
    out = Path("interview_decoded.mp3")
    out.write_bytes(audio)
    print(f"Wrote {out} ({len(audio)} bytes)")
    if audio[:3] == b"ID3" or (audio[0] == 0xFF and (audio[1] & 0xE0) == 0xE0):
        print("MP3 header looks valid.")
    else:
        print("WARNING: Does not look like MP3 — base64 may be truncated or wrong field.")
    if shutil.which("ffmpeg"):
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", str(out), "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=45,
        )
        for line in proc.stderr.splitlines():
            if "mean_volume" in line or "max_volume" in line:
                print(line.strip())
        if "mean_volume: -91" in proc.stderr or "mean_volume: -90" in proc.stderr:
            print("SILENT audio — re-run API test or verify xyz TTS websocket provider settings in .env")
    else:
        print("Install ffmpeg for volume check, or play interview_decoded.mp3 in VLC.")


if __name__ == "__main__":
    main()
