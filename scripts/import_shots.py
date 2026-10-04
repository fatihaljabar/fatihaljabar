"""Copies raw captures into scripts/shots/<slug>/ at the size the cards embed.

    python scripts/import_shots.py /path/to/raw/shots            # every slug
    python scripts/import_shots.py /path/to/raw/shots fadlan     # only some

Raw captures are 1440 px wide desktop PNGs and 390 css px (2x) mobile PNGs.
They are stored here as WebP at 1.5x and 2x of their on-card size so the
repository stays light and the build stays reproducible.

A card shows each page as the browser showed it. Pages are never glued
together into one long page (that would scroll through a second app header);
a card that needs several screens gets them as separate pages, written as
desktop-1.webp, desktop-2.webp and so on, and cards.py visits them in order.
"""

from __future__ import annotations

import glob
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "shots")

DESKTOP_CSS_W = 1440
MOBILE_CSS_W = 390
DESKTOP_MAX_CSS_H = 3600

# What each card shows. A source is a file name, or (file name, top, bottom) in css px
# to show only part of a page (bottom None means the end of the page). A list with
# several sources is a sequence of separate pages.
DESKTOP = {
    # The bill page is barely taller than the window; /results is the long, real page.
    # One continuous capture of it (shots-work/splitbill/shoot.mjs all,altfull).
    "splitbill": ["results-full.png"],
    # Three short screens of one flow: book, confirmed, the teacher's roster.
    "ottodot": ["desktop-full.png", "booking.png", "desktop-alt.png"],
    # Every photo on this site is hot-linked from images.unsplash.com, which could not be
    # reached during capture, so the hero is an empty dark frame in every full-page shot.
    # The card shows the image-free part of the page instead: this is the real home page
    # scrolled to the category index (a genuine viewport, Short Film row hovered).
    "fadlan": ["desktop-alt.png"],
}
MOBILE = {
    # Same reason: start 40 css px above the "Jelajahi karya." heading, below the hero
    # frame (which ends at 974 css px), and run to the real end of the page.
    "fadlan": [("mobile.png", 1001, None)],
}


def load(src_dir: str, spec, css_w: int) -> Image.Image:
    name, top, bottom = (spec, 0, None) if isinstance(spec, str) else spec
    im = Image.open(os.path.join(src_dir, name)).convert("RGB")
    k = im.width / css_w
    y0 = round(top * k)
    y1 = im.height if bottom is None else round(bottom * k)
    return im.crop((0, y0, im.width, y1)) if (y0, y1) != (0, im.height) else im


def save_webp(im: Image.Image, dst: str, width: int, css_w: int, max_css_h: int | None) -> None:
    if max_css_h and im.height * css_w / im.width > max_css_h:
        im = im.crop((0, 0, im.width, round(max_css_h * im.width / css_w)))
    h = round(im.height * width / im.width)
    im.resize((width, h), Image.LANCZOS).save(dst, "WEBP", quality=82, method=6)


def write_pages(src_dir: str, out: str, stem: str, specs: list, width: int, css_w: int,
                max_css_h: int | None) -> None:
    for old in glob.glob(os.path.join(out, f"{stem}*.webp")):
        os.remove(old)
    if len(specs) == 1:
        save_webp(load(src_dir, specs[0], css_w), os.path.join(out, f"{stem}.webp"), width, css_w, max_css_h)
        return
    for i, spec in enumerate(specs, 1):
        save_webp(load(src_dir, spec, css_w), os.path.join(out, f"{stem}-{i}.webp"), width, css_w, max_css_h)


def main(raw: str, only: list[str]) -> None:
    for slug in sorted(os.listdir(raw)):
        if only and slug not in only:
            continue
        src = os.path.join(raw, slug)
        if not os.path.isfile(os.path.join(src, "desktop-full.png")):
            continue
        out = os.path.join(DEST, slug)
        os.makedirs(out, exist_ok=True)
        write_pages(src, out, "desktop", DESKTOP.get(slug, ["desktop-full.png"]), 678, DESKTOP_CSS_W,
                    DESKTOP_MAX_CSS_H)
        if os.path.isfile(os.path.join(src, "mobile.png")):
            write_pages(src, out, "mobile", MOBILE.get(slug, ["mobile.png"]), 248, MOBILE_CSS_W, None)
        if os.path.isfile(os.path.join(src, "notes.json")):
            shutil.copy(os.path.join(src, "notes.json"), os.path.join(out, "notes.json"))
        sizes = {f: os.path.getsize(os.path.join(out, f)) // 1024 for f in sorted(os.listdir(out))}
        print(slug, sizes)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
