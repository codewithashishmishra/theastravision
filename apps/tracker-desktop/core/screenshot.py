import io

import mss
from PIL import Image


def capture_all_monitors():
    shots = []
    with mss.mss() as sct:
        for i, mon in enumerate(sct.monitors[1:], start=1):
            img = sct.grab(mon)
            pil = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            pil.save(buf, format="JPEG", quality=60, optimize=True)
            shots.append((i, buf.getvalue()))
    return shots
