"""
Create icon_64.ico from icon_256.png (fallback: icon_64.png). Run: uv run python icon/build_ico.py
Sizes 16..256 so Explorer and high-DPI look good. Window/taskbar use same file via app_icon.py.
"""
from pathlib import Path

from PIL import Image

ICON_DIR = Path(__file__).resolve().parent
PNG_256 = ICON_DIR / "icon_256.png"
PNG_64 = ICON_DIR / "icon_64.png"
OUT = ICON_DIR / "icon_64.ico"

SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

if PNG_256.exists():
    img = Image.open(PNG_256).convert("RGBA")
    if img.size != (256, 256):
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
else:
    if not PNG_64.exists():
        raise SystemExit(f"Missing {PNG_256} or {PNG_64}")
    img = Image.open(PNG_64).convert("RGBA")
    if img.size != (64, 64):
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
    img = img.resize((256, 256), Image.Resampling.LANCZOS)
img.save(OUT, format="ICO", sizes=SIZES)
print(f"Written {OUT} with sizes {SIZES}")
