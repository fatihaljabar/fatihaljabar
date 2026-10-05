"""Shared fonts, palette and drawing helpers for the README assets.

Every asset that sits on GitHub's own background is built twice:
    python scripts/build_assets.py              -> assets/<name>.svg        (dark)
    THEME=light python scripts/build_assets.py  -> assets/<name>-light.svg  (light)
The README swaps them with <picture> and prefers-color-scheme.
"""

from __future__ import annotations

import os

from svgkit import Doc, Font, num, rect  # noqa: F401  (re-exported for the asset modules)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
THEME = os.environ.get("THEME", "dark")
assert THEME in ("dark", "light"), THEME

DISP = Font("a", "bricolage-grotesque-latin-800-normal.woff2")
SEMI = Font("b", "bricolage-grotesque-latin-600-normal.woff2")
BODY = Font("c", "bricolage-grotesque-latin-500-normal.woff2")
MONO = Font("m", "jetbrains-mono-latin-500-normal.woff2")
MONOB = Font("n", "jetbrains-mono-latin-700-normal.woff2")

# Surfaces and ink per theme. VOLT is the one loud accent: in dark mode it is the
# lime itself; in light mode it drops to a darker olive so lines, bars and text
# keep at least 3:1 on the pale panels. INK is always the dark tone used for text
# that sits on top of an accent fill. TEXT_DIM is for decorative strokes only:
# any text a reader needs uses TEXT or MUTED.
PALETTES = {
    "dark": dict(
        BG="#0B0C0E", PANEL="#111317", PANEL2="#171A1F", LINE="#252931", LINE2="#3A3F48",
        TEXT="#EEEBE3", MUTED="#9A9FA8", DIM="#5B606A",
        VOLT="#C9F31D", VOLT_TEXT="#C9F31D", CORAL="#FF6B3D", SKY="#7CC4FF",
        GRID="#1F2328",
    ),
    "light": dict(
        BG="#FBFAF7", PANEL="#F5F3EE", PANEL2="#ECE9E2", LINE="#DAD5CA", LINE2="#C4BEB1",
        TEXT="#15171B", MUTED="#5F636B", DIM="#9A9EA6",
        VOLT="#6E8F00", VOLT_TEXT="#4F6B00", CORAL="#C8481F", SKY="#2A78D6",
        GRID="#E6E2D8",
    ),
}
_p = PALETTES[THEME]
BG, PANEL, PANEL2, LINE, LINE2 = _p["BG"], _p["PANEL"], _p["PANEL2"], _p["LINE"], _p["LINE2"]
TEXT, MUTED, DIM = _p["TEXT"], _p["MUTED"], _p["DIM"]
VOLT, VOLT_TEXT, CORAL, SKY, GRID = _p["VOLT"], _p["VOLT_TEXT"], _p["CORAL"], _p["SKY"], _p["GRID"]
LIME = "#C9F31D"  # the brand lime as a fill (dark text on top), same in both themes
INK = "#0B0C0E"
DOT = LINE

# Physical machine parts (plotter, rollers, stamp) are dark metal in both themes.
METAL = "#2A2E35"
METAL_EDGE = "#454B56"

# The drafting sheet the plotter draws on.
PAPER = "#ECE8DE"
GRAPH = "#DCD6C8"
GRAPH2 = "#CFC8B8"
PEN = "#17191D"
PENSOFT = "#5A5D63"

OUTQ = "cubic-bezier(.16,1,.3,1)"
INOUT = "cubic-bezier(.65,0,.35,1)"
GRAVITY = "cubic-bezier(.33,0,.67,.33)"  # y = t^2, a free fall from rest

BASE_CSS = """
.fb{transform-box:fill-box;transform-origin:center}
.ft{transform-box:fill-box;transform-origin:left top}
"""


def arrow_ne(x: float, y: float, s: float, color: str, w: float = 2.2) -> str:
    """North-east arrow, top-left corner at x,y with size s."""
    return (
        f'<path d="M{num(x)} {num(y+s)} L{num(x+s)} {num(y)} M{num(x+s*0.28)} {num(y)} '
        f'L{num(x+s)} {num(y)} L{num(x+s)} {num(y+s*0.72)}" fill="none" stroke="{color}" '
        f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def arrow_right(x: float, y: float, s: float, color: str, w: float = 2.2) -> str:
    return (
        f'<path d="M{num(x)} {num(y)} L{num(x+s)} {num(y)} M{num(x+s*0.62)} {num(y-s*0.38)} '
        f'L{num(x+s)} {num(y)} L{num(x+s*0.62)} {num(y+s*0.38)}" fill="none" stroke="{color}" '
        f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def save(name: str, doc: Doc, themed: bool = True) -> None:
    """Write assets/<name>; in the light build the file becomes <stem>-light.svg.

    Pass themed=False for assets that only exist once (the hero machine)."""
    if THEME == "light":
        if not themed:
            return
        stem, ext = os.path.splitext(name)
        name = f"{stem}-light{ext}"
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc.render())
    print(f"{name:34s} {os.path.getsize(path)/1024:6.1f} KB")
