"""Shared fonts, palette and drawing helpers for the README assets."""

from __future__ import annotations

import os

from svgkit import Doc, Font, num, rect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

DISP = Font("a", "bricolage-grotesque-latin-800-normal.woff2")
SEMI = Font("b", "bricolage-grotesque-latin-600-normal.woff2")
BODY = Font("c", "bricolage-grotesque-latin-500-normal.woff2")
MONO = Font("m", "jetbrains-mono-latin-500-normal.woff2")
MONOB = Font("n", "jetbrains-mono-latin-700-normal.woff2")

# Palette: warm ink canvas, one loud volt accent, coral and sky as supporting signals.
# PAPER is the drafting sheet the plotter draws on; GRAPH is its printed grid.
BG = "#0B0C0E"
PANEL = "#111317"
PANEL2 = "#171A1F"
LINE = "#252931"
DOT = "#22262D"
TEXT = "#EEEBE3"
MUTED = "#8C919A"
DIM = "#5B606A"
VOLT = "#C9F31D"
CORAL = "#FF6B3D"
SKY = "#7CC4FF"
INK = "#0B0C0E"
PAPER = "#ECE8DE"
GRAPH = "#DCD6C8"
GRAPH2 = "#CFC8B8"
PEN = "#17191D"
PENSOFT = "#5A5D63"

OUTQ = "cubic-bezier(.16,1,.3,1)"
INOUT = "cubic-bezier(.65,0,.35,1)"


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



def save(name: str, doc: Doc) -> None:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc.render())
    print(f"{name:34s} {os.path.getsize(path)/1024:6.1f} KB")
