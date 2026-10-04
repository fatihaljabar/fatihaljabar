"""Shared fonts, palette and drawing helpers for the README assets."""

from __future__ import annotations

import os

from svgkit import Doc, Font, num, rect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

DISP = Font("a", "bricolage-grotesque-latin-800-normal.woff2")
SEMI = Font("b", "bricolage-grotesque-latin-600-normal.woff2")
BODY = Font("c", "bricolage-grotesque-latin-400-normal.woff2")
MONO = Font("m", "jetbrains-mono-latin-500-normal.woff2")
MONOB = Font("n", "jetbrains-mono-latin-700-normal.woff2")
SERIF = Font("s", "instrument-serif-latin-400-italic.woff2")

# Palette: warm ink canvas, one loud volt accent, coral and sky as supporting signals.
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

SPRING = "cubic-bezier(.34,1.56,.64,1)"
OUTQ = "cubic-bezier(.16,1,.3,1)"
INOUT = "cubic-bezier(.65,0,.35,1)"

CURSOR_PATH = "M0 0 L0 23 L6.2 17.4 L10.6 27 L14.6 25.3 L10.3 15.8 L18 15.8 Z"

BASE_CSS = """
.fb{transform-box:fill-box;transform-origin:center}
.ft{transform-box:fill-box;transform-origin:left top}
"""


def dots_pattern(pid: str = "dots", gap: int = 24, color: str = DOT, r: float = 1.1) -> str:
    return (
        f'<pattern id="{pid}" width="{gap}" height="{gap}" patternUnits="userSpaceOnUse">'
        f'<circle cx="{gap/2}" cy="{gap/2}" r="{r}" fill="{color}"/></pattern>'
    )


def cursor(doc: Doc, color: str, label: str, label_color: str = INK) -> str:
    """A multiplayer cursor with a name tag, drawn at the origin."""
    tw = MONOB.width(label, 13)
    return (
        f'<path d="{CURSOR_PATH}" fill="{color}" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round"/>'
        + rect(15, 26, tw + 18, 24, 7, fill=color)
        + doc.text(label, 24, 42.5, 13, MONOB, fill=label_color)
    )


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


def pill(doc: Doc, x, y, label, font=MONO, size=14, fg=TEXT, bg="none", stroke=LINE, padx=14, h=32, cls=None, style=None, dot=None):
    tw = font.width(label, size)
    extra = 16 if dot else 0
    w = tw + padx * 2 + extra
    attrs = f' class="{cls}"' if cls else ""
    attrs += f' style="{style}"' if style else ""
    out = f"<g{attrs}>" + rect(x, y, w, h, h / 2, fill=bg, stroke=stroke, stroke_width=1.2)
    if dot:
        out += f'<circle cx="{num(x+padx+4)}" cy="{num(y+h/2)}" r="4" fill="{dot}"/>'
    out += doc.text(label, x + padx + extra, y + h / 2 + size * 0.36, size, font, fill=fg) + "</g>"
    return out, w


def save(name: str, doc: Doc) -> None:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc.render())
    print(f"{name:34s} {os.path.getsize(path)/1024:6.1f} KB")
