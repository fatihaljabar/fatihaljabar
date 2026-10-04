"""Copies raw captures into scripts/shots/<slug>/ at the size the cards embed.

    python scripts/import_shots.py /path/to/raw/shots

Raw captures are 1440 px wide desktop full-page PNGs and 390 css px (2x)
mobile PNGs. They are stored here as WebP at 1.5x and 2x of their on-card
size so the repository stays light and the build stays reproducible.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "shots")


def save_webp(src: str, dst: str, width: int, max_h: int) -> None:
    im = Image.open(src).convert("RGB")
    if im.height * 1440 / im.width > max_h:
        im = im.crop((0, 0, im.width, round(max_h * im.width / 1440)))
    h = round(im.height * width / im.width)
    im.resize((width, h), Image.LANCZOS).save(dst, "WEBP", quality=82, method=6)


def main(raw: str) -> None:
    for slug in sorted(os.listdir(raw)):
        src = os.path.join(raw, slug)
        if not os.path.isfile(os.path.join(src, "desktop-full.png")):
            continue
        out = os.path.join(DEST, slug)
        os.makedirs(out, exist_ok=True)
        save_webp(os.path.join(src, "desktop-full.png"), os.path.join(out, "desktop.webp"), 678, 3600)
        if os.path.isfile(os.path.join(src, "mobile.png")):
            save_webp(os.path.join(src, "mobile.png"), os.path.join(out, "mobile.webp"), 248, 99999)
        if os.path.isfile(os.path.join(src, "notes.json")):
            shutil.copy(os.path.join(src, "notes.json"), os.path.join(out, "notes.json"))
        sizes = {f: os.path.getsize(os.path.join(out, f)) // 1024 for f in os.listdir(out)}
        print(slug, sizes)


if __name__ == "__main__":
    main(sys.argv[1])
