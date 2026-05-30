import io

import mss
from PIL import Image


def _monitor_to_jpeg(mon) -> bytes:
    with mss.mss() as sct:
        img = sct.grab(mon)
        pil = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=60, optimize=True)
        return buf.getvalue()


def capture_primary_monitor() -> bytes:
    with mss.mss() as sct:
        primary = sct.monitors[1]
    return _monitor_to_jpeg(primary)


def capture_all_monitors():
    shots = []
    with mss.mss() as sct:
        for i, mon in enumerate(sct.monitors[1:], start=1):
            shots.append((i, _monitor_to_jpeg(mon)))
    return shots
