"""Tiny SVG toolkit used by build_assets.py.

Text is converted to outlines (glyph paths reused through <use>), so every
asset renders identically on any OS without loading web fonts. GitHub serves
README images in a sandbox where external fonts never load, so this is the
only way to keep the typography consistent.
"""

from __future__ import annotations

import os
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")


# Middle dots, bullets, en and em dashes read as AI filler on this page; the build refuses them.
BANNED = {"\u00b7", "\u2022", "\u2013", "\u2014"}


def num(v: float) -> str:
    """Compact number formatting for SVG attributes."""
    r = round(v, 2)
    if r == int(r):
        return str(int(r))
    return f"{r:g}"


class Font:
    def __init__(self, key: str, filename: str):
        self.key = key
        self.tt = TTFont(os.path.join(FONT_DIR, filename))
        self.glyphs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        self.hmtx = self.tt["hmtx"]
        self.cap = self.tt["OS/2"].sCapHeight
        self.xh = self.tt["OS/2"].sxHeight
        self._paths: dict[str, str] = {}
        self.kern = self._load_kerning()

    # Pair kerning from GPOS (PairPos format 1 and 2), good enough for display type.
    def _load_kerning(self) -> dict[tuple[str, str], int]:
        pairs: dict[tuple[str, str], int] = {}
        if "GPOS" not in self.tt:
            return pairs
        gpos = self.tt["GPOS"].table
        lookups = set()
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                lookups.update(fr.Feature.LookupListIndex)
        for li in lookups:
            lookup = gpos.LookupList.Lookup[li]
            subs = lookup.SubTable
            if lookup.LookupType == 9:
                subs = [s.ExtSubTable for s in subs]
            for st in subs:
                if getattr(st, "LookupType", 2) != 2 and lookup.LookupType != 9:
                    continue
                if not hasattr(st, "Format"):
                    continue
                cov = st.Coverage.glyphs
                if st.Format == 1:
                    for i, first in enumerate(cov):
                        for pvr in st.PairSet[i].PairValueRecord:
                            v = getattr(pvr.Value1, "XAdvance", 0) if pvr.Value1 else 0
                            if v:
                                pairs.setdefault((first, pvr.SecondGlyph), v)
                elif st.Format == 2:
                    cd1 = st.ClassDef1.classDefs
                    cd2 = st.ClassDef2.classDefs
                    seconds: dict[int, list[str]] = {}
                    for g, c in cd2.items():
                        seconds.setdefault(c, []).append(g)
                    for first in cov:
                        c1 = cd1.get(first, 0)
                        rec = st.Class1Record[c1]
                        for c2, r2 in enumerate(rec.Class2Record):
                            v = getattr(r2.Value1, "XAdvance", 0) if r2.Value1 else 0
                            if not v:
                                continue
                            for second in seconds.get(c2, []):
                                pairs.setdefault((first, second), v)
        return pairs

    def gname(self, ch: str) -> str:
        name = self.cmap.get(ord(ch))
        if name is None:
            raise ValueError(f"{self.key}: missing glyph for {ch!r} (U+{ord(ch):04X})")
        return name

    def path(self, name: str) -> str:
        if name not in self._paths:
            pen = SVGPathPen(self.glyphs, ntos=lambda v: num(v))
            self.glyphs[name].draw(pen)
            self._paths[name] = pen.getCommands()
        return self._paths[name]

    def layout(self, s: str, size: float, ls: float = 0.0):
        """Return [(char, glyph name, x offset px)] and total width px."""
        k = size / self.upm
        out = []
        x = 0.0
        prev = None
        for ch in s:
            name = self.gname(ch)
            if prev is not None:
                x += self.kern.get((prev, name), 0) * k
            out.append((ch, name, x))
            x += self.hmtx[name][0] * k + ls
            prev = name
        width = x - ls if s else 0.0
        return out, width

    def width(self, s: str, size: float, ls: float = 0.0) -> float:
        return self.layout(s, size, ls)[1]


class Doc:
    def __init__(self, w: float, h: float, title: str, desc: str = ""):
        self.w = w
        self.h = h
        self.title = title
        self.desc = desc
        self.defs: list[str] = []
        self.css: list[str] = []
        self.body: list[str] = []
        self._glyph_ids: dict[tuple[str, str], str] = {}

    # -- glyphs ---------------------------------------------------------------
    def gid(self, font: Font, name: str) -> str:
        key = (font.key, name)
        if key not in self._glyph_ids:
            gid = f"{font.key}{len(self._glyph_ids)}"
            self._glyph_ids[key] = gid
            d = font.path(name)
            if d:
                self.defs.append(f'<path id="{gid}" d="{d}"/>')
            else:
                self.defs.append(f'<path id="{gid}" d=""/>')
        return self._glyph_ids[key]

    def text(
        self,
        s: str,
        x: float,
        y: float,
        size: float,
        font: Font,
        fill: str | None = None,
        anchor: str = "start",
        ls: float = 0.0,
        cls: str | None = None,
        style: str | None = None,
        per_char: str | None = None,
        delay0: float = 0.0,
        step: float = 0.05,
        opacity: float | None = None,
    ) -> str:
        """Outline text. With per_char, every glyph gets its own animatable group
        with class `per_char` and a staggered animation-delay."""
        banned = BANNED.intersection(s)
        if banned:
            raise ValueError(f"banned glyph {sorted(banned)} in text {s!r}: use words or commas instead")
        glyphs, width = font.layout(s, size, ls)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        k = size / font.upm
        attrs = []
        if fill:
            attrs.append(f'fill="{fill}"')
        if cls:
            attrs.append(f'class="{cls}"')
        if style:
            attrs.append(f'style="{style}"')
        if opacity is not None:
            attrs.append(f'opacity="{num(opacity)}"')
        a = (" " + " ".join(attrs)) if attrs else ""
        if per_char:
            parts = [f'<g transform="translate({num(x)} {num(y)})"{a}>']
            i = 0
            for ch, name, gx in glyphs:
                if ch == " ":
                    continue
                gid = self.gid(font, name)
                d = delay0 + i * step
                parts.append(
                    f'<g transform="translate({num(gx)} 0)"><g class="{per_char}" '
                    f'style="animation-delay:{num(d)}s"><use xlink:href="#{gid}" '
                    f'transform="scale({num(k)} {num(-k)})"/></g></g>'
                )
                i += 1
            parts.append("</g>")
            return "".join(parts)
        parts = [f'<g transform="translate({num(x)} {num(y)}) scale({k:.5f} {-k:.5f})"{a}>']
        for ch, name, gx in glyphs:
            if ch == " ":
                continue
            gid = self.gid(font, name)
            ux = gx / k
            parts.append(f'<use xlink:href="#{gid}"' + (f' x="{num(ux)}"' if ux else "") + "/>")
        parts.append("</g>")
        return "".join(parts)

    def add(self, *items: str) -> None:
        self.body.extend(items)

    def style(self, css: str) -> None:
        self.css.append(css)

    def render(self) -> str:
        css = "\n".join(self.css)
        css += (
            "\n@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
        )
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {num(self.w)} {num(self.h)}" width="{num(self.w)}" height="{num(self.h)}" '
            f'role="img" aria-labelledby="t d">',
            f'<title id="t">{escape(self.title)}</title>',
            f'<desc id="d">{escape(self.desc or self.title)}</desc>',
            f"<style>{css}</style>",
            "<defs>" + "".join(self.defs) + "</defs>",
        ]
        out.extend(self.body)
        out.append("</svg>")
        return "\n".join(out)


def wrap(font: Font, s: str, size: float, max_w: float) -> list[str]:
    words = s.split(" ")
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.width(trial, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rect(x, y, w, h, r=0, **kw) -> str:
    attrs = " ".join(
        f'{"class" if k == "cls" else k.replace("_", "-")}="{v}"' for k, v in kw.items()
    )
    rr = f' rx="{num(r)}"' if r else ""
    return f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"{rr} {attrs}/>'
