"""Hero: an XY pen plotter draws the name on a drafting sheet.

Everything is computed, not keyed by hand: glyph outlines are flattened to
polylines, hatching is clipped against the outlines with an even-odd scanline,
and one timeline drives the ink (stroke-dashoffset per path), the pen head (X),
the gantry, both rail carriages and the cable (Y), the pen rack and the job
progress bar, so the pen tip is always exactly where the line is growing.
"""

from __future__ import annotations

import math

from fontTools.pens.basePen import BasePen

from motion import Spring, spring_tf
from svgkit import Doc, num, rect
from theme import *  # noqa: F403

W, H = 1200, 640
RAIL_L, RAIL_R = 51, 1149  # rail centre lines
PX0, PY0, PX1, PY1 = 104, 40, 1096, 548  # paper
PARK = (150.0, 24.0)
GANTRY = Spring(300, 28, 1.2)  # stiff stepper gantry, ~1.5% settle overshoot
FEED_SPRING = Spring(240, 26, 1.3)  # a fresh sheet pulled taut by the feed rollers

DRAW_SPEED = 2600.0  # px/s, outlines
HATCH_SPEED = 7200.0
HOP_SPEED = 6000.0
TRAVEL_SPEED = 2400.0


class FlattenPen(BasePen):
    """Collects contours as lists of points, curves subdivided by length."""

    def __init__(self, glyphset, step: float = 14.0):
        super().__init__(glyphset)
        self.step = step
        self.contours: list[list[tuple[float, float]]] = []
        self.cur: list[tuple[float, float]] = []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        n = max(2, int(math.dist(p0, p1) + math.dist(p1, p2)) // int(self.step) + 1)
        for i in range(1, n + 1):
            t = i / n
            a = (1 - t) ** 2
            b = 2 * (1 - t) * t
            c = t * t
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        n = max(3, int(math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)) // int(self.step) + 1)
        for i in range(1, n + 1):
            t = i / n
            mt = 1 - t
            self.cur.append((mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                             mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1]))

    def _closePath(self):
        if self.cur:
            if self.cur[0] != self.cur[-1]:
                self.cur.append(self.cur[0])
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


def _signed_area(c):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(c, c[1:])) / 2


def text_contours(s: str, x: float, base: float, size: float, font=DISP):
    """Glyph outlines of `s` in page pixels, overlapping contours merged.

    Fonts build letters from overlapping shapes (the F is a stem plus two
    arms); a plotter tracing those raw contours would draw the overlaps, so
    each glyph is unioned first (non-zero winding) and only the final
    silhouette is traced.
    """
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    k = size / font.upm
    glyphs, width = font.layout(s, size)
    out = []
    for ch, name, gx in glyphs:
        if ch == " ":
            continue
        pen = FlattenPen(font.glyphs, step=16)
        font.glyphs[name].draw(pen)
        outers, holes = [], []
        for c in pen.contours:
            if len(c) < 4:
                continue
            (outers if _signed_area(c) < 0 else holes).append(Polygon(c).buffer(0))
        if not outers:  # font with the opposite winding convention
            outers, holes = holes, outers
        shape = unary_union(outers)
        if holes:
            shape = shape.difference(unary_union(holes))
        for g in getattr(shape, "geoms", [shape]):
            for ring in [g.exterior, *g.interiors]:
                out.append([(x + gx + px * k, base - py * k) for px, py in ring.coords])
    return out, width


def hatch(contours, spacing: float, angle_deg: float = 45):
    """Even-odd hatching: returns rows of segments, each row a list of (p0, p1)."""
    a = math.radians(angle_deg)
    d = (math.cos(a), -math.sin(a))  # line direction (y down)
    n = (-d[1], d[0])  # normal
    pts = [p for c in contours for p in c]
    offs = [p[0] * n[0] + p[1] * n[1] for p in pts]
    lo, hi = min(offs), max(offs)
    rows = []
    o = lo + spacing / 2
    while o < hi:
        hits = []
        for c in contours:
            for (x0, y0), (x1, y1) in zip(c, c[1:]):
                s0 = x0 * n[0] + y0 * n[1] - o
                s1 = x1 * n[0] + y1 * n[1] - o
                if (s0 < 0) != (s1 < 0):
                    t = s0 / (s0 - s1)
                    px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                    hits.append(px * d[0] + py * d[1])
        hits.sort()
        row = []
        for i in range(0, len(hits) - 1, 2):
            u0, u1 = hits[i], hits[i + 1]
            if u1 - u0 < 1.5:
                continue
            p0 = (n[0] * o + d[0] * u0, n[1] * o + d[1] * u0)
            p1 = (n[0] * o + d[0] * u1, n[1] * o + d[1] * u1)
            row.append((p0, p1))
        if row:
            rows.append(row)
        o += spacing
    return rows


class Plotter:
    def __init__(self):
        self.t = 0.0
        self.x, self.y = PARK
        self.kx: list[tuple[float, float, str]] = [(0.0, self.x, "lin")]
        self.ky: list[tuple[float, float, str]] = [(0.0, self.y, "lin")]
        self.pen: list[tuple[float, int]] = [(0.0, 0)]
        self.ink: list[tuple[str, float, float, str, float]] = []  # d, t0, t1, colour, width
        self.marks: list[tuple[str, float]] = []  # named instants

    def _key(self, x, y, tf):
        self.kx.append((self.t, x, tf))
        self.ky.append((self.t, y, tf))

    def _retag(self, tf):
        # timing function belongs to the keyframe where a segment starts
        t, x, _ = self.kx[-1]
        self.kx[-1] = (t, x, tf)
        t, y, _ = self.ky[-1]
        self.ky[-1] = (t, y, tf)

    def pen_set(self, down: int):
        if self.pen[-1][1] != down:
            self.pen.append((self.t, down))

    def wait(self, dt):
        self._retag("lin")
        self.t += dt
        self._key(self.x, self.y, "lin")

    def move(self, x, y, kind="travel"):
        dist = math.dist((self.x, self.y), (x, y))
        if dist < 0.01:
            return
        self.pen_set(0)
        if kind == "hop":
            dt = max(0.018, dist / HOP_SPEED)
            self._retag("lin")
        else:
            dt = 0.14 + dist / TRAVEL_SPEED
            self._retag("spring")
        self.t += dt
        self.x, self.y = x, y
        self._key(x, y, "lin")

    def draw(self, pts, colour=PEN, width=2.0, speed=DRAW_SPEED, settle=0.0):
        self.move(*pts[0], kind="hop" if speed > 3000 else "travel")
        if settle:
            self.wait(settle)
        self.pen_set(1)
        t0 = self.t
        self._retag("lin")
        for p in pts[1:]:
            self.t += math.dist((self.x, self.y), p) / speed
            self.x, self.y = p
            self._key(p[0], p[1], "lin")
        d = "M" + " L".join(f"{num(px)} {num(py)}" for px, py in pts)
        self.ink.append((d, t0, self.t, colour, width))
        self.pen_set(0)

    def mark(self, name):
        self.marks.append((name, self.t))
        return self.t


def keyframes(name: str, keys, total: float, fmt) -> str:
    tfs = {"lin": "", "spring": ";" + spring_tf(GANTRY)}
    out = []
    last_pct = -1.0
    for t, v, tf in keys:
        pct = round(t / total * 100, 3)
        if pct <= last_pct:
            pct = last_pct + 0.001
        last_pct = pct
        out.append(f"{pct:g}%{{{fmt(v)}{tfs[tf]}}}")
    return f"@keyframes {name}{{" + "".join(out) + "}"


def build() -> Doc:
    d = Doc(W, H, "Fatih: front-end developer, full-stack when it counts",
            "A pen plotter draws the name Fatih on a drafting sheet, hatches it, swaps to a lime pen for the dot and an "
            "underline, then prints the tagline 'Interfaces that feel fast and obvious, with a backend behind them that "
            "stays out of the way', notes and a title block: Fatih, front-end and full-stack developer, Indonesia, open "
            "to remote work.")
    d.style(BASE_CSS)
    p = Plotter()

    # ---- artwork geometry
    size = 236
    nx, nbase = 136, 302
    contours, nw = text_contours("Fatih", nx, nbase, size)
    dot_c = (nx + nw + 30, nbase - 22)
    rows = hatch(contours, 9.0, 52)

    # homing: touch the paper corner like a real machine finding zero
    p.wait(0.15)
    p.move(PX0 + 6, PY0 + 6)
    p.wait(0.12)

    # dimension line above the name
    dy = 104
    p.draw([(nx, dy - 10), (nx, dy + 10)], width=1.4)
    p.draw([(nx + 14, dy - 5), (nx, dy), (nx + 14, dy + 5), (nx, dy), (nx + nw / 2 - 34, dy)], width=1.4)
    p.draw([(nx + nw / 2 + 34, dy), (nx + nw, dy), (nx + nw - 14, dy - 5), (nx + nw, dy), (nx + nw - 14, dy + 5)], width=1.4)
    p.draw([(nx + nw, dy + 10), (nx + nw, dy - 10)], width=1.4)
    t_dim = p.mark("dim")

    # outlines, contour by contour, in reading order
    contours.sort(key=lambda c: min(x for x, _ in c))
    for c in contours:
        p.draw(c, width=2.2)
    p.mark("outlined")

    # hatching, boustrophedon so the pen never travels far between rows
    flip = False
    for row in rows:
        segs = row[::-1] if flip else row
        for a, b in segs:
            p.draw([b, a] if flip else [a, b], width=1.5, speed=HATCH_SPEED)
        flip = not flip
    p.mark("hatched")

    # print pass: the gantry sweeps the sheet, lines appear as it crosses them
    p.move(PX1 + 18, PY0 + 4)
    sweep_t0 = p.t
    p._retag("lin")
    sweep_speed = 900.0
    p.t += (PY1 - 4 - (PY0 + 4)) / sweep_speed
    p.x, p.y = PX1 + 18, PY1 - 4
    p._key(p.x, p.y, "lin")

    def printed_at(y):
        return sweep_t0 + (y - (PY0 + 4)) / sweep_speed

    # pen swap at the rack: drop the ink pen, pick the lime one
    rack_y = 587
    slots = {"ink": 1006.0, "volt": 1036.0, "coral": 1066.0}
    p.move(slots["ink"], rack_y)
    p.wait(0.18)
    t_drop = p.t
    p.wait(0.14)
    p.move(slots["volt"], rack_y)
    p.wait(0.18)
    t_pick = p.t
    p.wait(0.12)

    # the dot: an Archimedean spiral filled from the outside in
    r_dot = 19
    spiral = []
    turns = r_dot / 3.0
    steps = int(turns * 28)
    for i in range(steps + 1):
        f = i / steps
        r = r_dot * (1 - f)
        th = f * turns * 2 * math.pi
        spiral.append((dot_c[0] + r * math.cos(th), dot_c[1] + r * math.sin(th)))
    p.draw(spiral, colour=VOLT, width=3.6, speed=1300, settle=0.05)

    # marker underline under "fast and obvious"
    sub_x, sub_base, sub_size = 138, 376, 36
    pre = "Interfaces that feel "
    ux0 = sub_x + SEMI.width(pre, sub_size) - 4
    ux1 = sub_x + SEMI.width(pre + "fast and obvious", sub_size) + 6
    wave = [(ux0 + (ux1 - ux0) * i / 40, sub_base + 4 + 1.6 * math.sin(i / 40 * math.pi * 3)) for i in range(41)]
    p.draw(wave, colour=VOLT, width=12, speed=1100, settle=0.05)

    # put the lime pen back and pick up the ink pen, so the next sheet starts clean
    p.move(slots["volt"], rack_y)
    p.wait(0.18)
    t_drop2 = p.t
    p.wait(0.12)
    p.move(slots["ink"], rack_y)
    p.wait(0.18)
    t_pick2 = p.t
    p.wait(0.12)

    # park
    p.move(*PARK)
    p.wait(0.05)
    T = p.t

    # the machine loops like a roll-fed plotter: hold, feed the sheet out, new sheet in
    HOLD, FEED = 7.0, 1.9
    f0 = T + HOLD
    fm = f0 + FEED * 0.45
    P = f0 + FEED
    p.kx.append((P, PARK[0], "lin"))
    p.ky.append((P, PARK[1], "lin"))

    def pc(t):
        return f"{t / P * 100:.3f}".rstrip("0").rstrip(".") + "%"

    def vis(cls, spans, static_on):
        """Discrete visibility over the loop. spans: [(start, end)] in seconds."""
        pts = sorted({0.0, P, *[x for sp in spans for x in sp]})
        def on(t):
            return any(a0 <= t < a1 for a0, a1 in spans)
        frames = "".join(f"{pc(t)}{{opacity:{1 if on(min(t, P - 1e-6)) else 0}}}" for t in pts)
        d.style(f"@keyframes {cls}k{{{frames}}}"
                f".{cls}{{opacity:{1 if static_on else 0};animation:{cls}k {P:.3f}s steps(1,end) infinite}}")

    # ---- CSS for the timeline
    d.style(keyframes("hx", p.kx, P, lambda v: f"transform:translateX({v:.1f}px)"))
    d.style(keyframes("hy", p.ky, P, lambda v: f"transform:translateY({v:.1f}px)"))
    d.style(f".hx{{transform:translateX({PARK[0]}px);animation:hx {P:.3f}s linear infinite}}"
            f".hy{{transform:translateY({PARK[1]}px);animation:hy {P:.3f}s linear infinite}}")
    # cable: straight run below the bend stretches with the carriage
    cab_bottom = 616.0

    def cab_scale(y):
        return (cab_bottom - (y + 40)) / (cab_bottom - (PARK[1] + 40))
    d.style(keyframes("cs", p.ky, P, lambda v: f"transform:scaleY({cab_scale(v):.4f})"))
    d.style(f".cs{{transform-box:view-box;transform-origin:0 {cab_bottom}px;animation:cs {P:.3f}s linear infinite}}")

    # pen tip contact (down / up)
    downs, start = [], None
    for t, down in p.pen + [(T, 0)]:
        if down and start is None:
            start = t
        elif not down and start is not None:
            downs.append((start, t))
            start = None
    vis("tip", downs, False)

    # ink: each stroke draws during its window and is wiped when the sheet leaves
    css = []
    for i, (_, t0, t1, _, _) in enumerate(p.ink):
        t1 = max(t1, t0 + 0.004)
        css.append(f"@keyframes k{i}{{0%,{pc(t0)}{{stroke-dashoffset:1}}{pc(t1)},{pc(fm)}{{stroke-dashoffset:0}}"
                   f"{pc(fm + 0.01)},100%{{stroke-dashoffset:1}}}}.k{i}{{animation:k{i} {P:.3f}s linear infinite}}")
    d.style(".ink{stroke-dasharray:1 1;fill:none;stroke-linecap:round;stroke-linejoin:round}" + "".join(css))

    # paper feed: out through the top, a fresh sheet in from the bottom, settling on a spring
    travel = PY1 - PY0 + 24
    d.style(f"@keyframes feed{{0%,{pc(f0)}{{transform:translateY(0);animation-timing-function:cubic-bezier(.5,0,.9,.5)}}"
            f"{pc(fm)}{{transform:translateY(-{travel}px);animation-timing-function:steps(1,end)}}"
            f"{pc(fm + 0.01)}{{transform:translateY({travel}px);{spring_tf(FEED_SPRING)}}}"
            f"100%{{transform:translateY(0)}}}}"
            f".feed{{animation:feed {P:.3f}s linear infinite}}")
    d.style(f"@keyframes rollers{{0%,{pc(f0)}{{transform:rotate(0)}}100%{{transform:rotate(-1080deg)}}}}"
            f".rollers{{transform-box:fill-box;transform-origin:center;animation:rollers {P:.3f}s cubic-bezier(.4,0,.2,1) infinite}}")

    # ---- drawing
    d.defs.append(f'<pattern id="g1" width="12" height="12" patternUnits="userSpaceOnUse" x="{PX0}" y="{PY0}">'
                  f'<path d="M12 0V12H0" fill="none" stroke="{GRAPH}" stroke-width=".6"/></pattern>'
                  f'<pattern id="g5" width="60" height="60" patternUnits="userSpaceOnUse" x="{PX0}" y="{PY0}">'
                  f'<path d="M60 0V60H0" fill="none" stroke="{GRAPH2}" stroke-width=".9"/></pattern>'
                  f'<clipPath id="sheet"><rect x="{PX0 - 6}" y="{PY0}" width="{PX1 - PX0 + 12}" height="{PY1 - PY0}"/></clipPath>')
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill="#0F1114", stroke=LINE, stroke_width=1.5))
    d.add(rect(PX0 - 6, PY0, PX1 - PX0 + 12, PY1 - PY0, 4, fill="#08090B"))

    # rails with machined scales
    for cx, side in ((RAIL_L, -1), (RAIL_R, 1)):
        d.add(rect(cx - 25, 22, 50, 596, 9, fill=PANEL2, stroke=LINE, stroke_width=1.2))
        d.add(rect(cx - 3, 34, 6, 572, 3, fill=BG))
        ticks = []
        for y in range(PY0, 601, 10):
            long_ = (y - PY0) % 50 == 0
            x0 = cx + side * 9
            x1 = x0 + side * (9 if long_ else 5)
            ticks.append(f"M{x0} {y}H{x1}")
            if long_ and (y - PY0) % 100 == 0 and y < 590:
                d.add(d.text(str(y - PY0), cx + side * 21, y + 3.5, 8, MONO, fill=DIM, anchor="middle"))
        d.add(f'<path d="{"".join(ticks)}" stroke="{DIM}" stroke-width="1"/>')

    d.add(f'<g clip-path="url(#sheet)"><g class="feed">')
    # paper
    d.add(rect(PX0, PY0, PX1 - PX0, PY1 - PY0, 3, fill=PAPER))
    d.add(f'<rect x="{PX0}" y="{PY0}" width="{PX1-PX0}" height="{PY1-PY0}" fill="url(#g1)"/>'
          f'<rect x="{PX0}" y="{PY0}" width="{PX1-PX0}" height="{PY1-PY0}" fill="url(#g5)"/>')
    for cx, cy in ((PX0 + 16, PY0 + 16), (PX1 - 16, PY0 + 16), (PX0 + 16, PY1 - 16), (PX1 - 16, PY1 - 16)):
        d.add(f'<circle cx="{cx}" cy="{cy}" r="5" fill="none" stroke="{PENSOFT}" stroke-width=".9"/>'
              f'<path d="M{cx-9} {cy}H{cx+9}M{cx} {cy-9}V{cy+9}" stroke="{PENSOFT}" stroke-width=".9"/>')

    # printed matter (revealed by the sweep, gone with the sheet)
    def printed(svg, y, cls):
        vis(cls, [(printed_at(y), fm)], True)
        d.add(f'<g class="{cls}">{svg}</g>')

    printed(d.text("FATIHALJABAR / README", PX0 + 34, 76, 11, MONOB, fill=PENSOFT, ls=1.2), 66, "p0")
    printed(d.text("SHEET 1 OF 1   SCALE 1:1   2026", PX1 - 34, 76, 11, MONOB, fill=PENSOFT, ls=1.2, anchor="end"), 66, "p1")
    printed(d.text(f"{round(nw)}", nx + nw / 2, dy + 4.5, 13, MONOB, fill=PEN, anchor="middle"), dy, "p2")

    # marker underline sits under the tagline, so it is drawn before the text
    for i, (dd, t0, t1, col, wdt) in enumerate(p.ink):
        if col == VOLT and wdt > 10:
            d.add(f'<path class="ink k{i}" pathLength="1" d="{dd}" stroke="{col}" stroke-width="{wdt}" opacity=".9"/>')
    printed(d.text("Interfaces that feel fast and obvious,", sub_x, sub_base, sub_size, SEMI, fill=PEN), sub_base - 26, "p3")
    printed(d.text("with a backend behind them that stays out of the way.", sub_x + 1, 414, 23, BODY, fill=PENSOFT), 396, "p4")

    notes = ["React, Next.js and TypeScript every day. Vue when the job calls for it.",
             "In production: trackinglamaran.site, splitbills.site, fatihaljabar.com.",
             "Based in Indonesia, UTC+7. Open to remote work."]
    printed(d.text("NOTES", sub_x, 462, 11, MONOB, fill=PENSOFT, ls=1.2), 452, "p5")
    for i, ln in enumerate(notes):
        y = 486 + i * 21
        printed(d.text(f"{i+1}.", sub_x, y, 12, MONOB, fill=PENSOFT) + d.text(ln, sub_x + 22, y, 12, MONO, fill=PEN), y - 10, f"p6{i}")

    tb_x0, tb_x1, tb_y0, rh = 720, PX1 - 28, 446, 22
    rows_tb = [("DRAWN BY", "Fatih"), ("ROLE", "Front-end / full-stack developer"),
               ("LOCATION", "Indonesia, UTC+7"), ("STATUS", "Open to remote work")]
    tb = rect(tb_x0, tb_y0, tb_x1 - tb_x0, rh * len(rows_tb), 0, fill="none", stroke=PEN, stroke_width=1.3)
    tb += f'<path d="M{tb_x0+92} {tb_y0}V{tb_y0+rh*len(rows_tb)}' + "".join(
        f"M{tb_x0} {tb_y0+rh*i}H{tb_x1}" for i in range(1, len(rows_tb))) + f'" stroke="{PEN}" stroke-width=".8"/>'
    printed(tb, tb_y0, "p7")
    for i, (k, v) in enumerate(rows_tb):
        y = tb_y0 + rh * i + 15
        printed(d.text(k, tb_x0 + 9, y, 9.5, MONOB, fill=PENSOFT, ls=0.8)
                + d.text(v, tb_x0 + 102, y + 0.5, 13, SEMI, fill=PEN), y - 10, f"p8{i}")

    # ink
    for i, (dd, t0, t1, col, wdt) in enumerate(p.ink):
        if col == VOLT and wdt > 10:
            continue
        d.add(f'<path class="ink k{i}" pathLength="1" d="{dd}" stroke="{col}" stroke-width="{wdt}"/>')
    d.add("</g></g>")

    # feed rollers at the bottom edge of the sheet window
    for rx in (PX0 + 60, PX1 - 60):
        d.add(f'<g transform="translate({rx} {PY1 + 4})"><g class="rollers"><circle r="7" fill="#22262D" stroke="#454B56"/>'
              f'<path d="M0 -7V-3M0 7V3M-7 0H-3M7 0H3" stroke="#6B7079" stroke-width="1.4"/></g></g>')

    # status bar + pen rack
    d.add(rect(88, 558, 1024, 54, 10, fill=PANEL, stroke=LINE, stroke_width=1))
    d.add(d.text("JOB", 108, 589, 10, MONOB, fill=DIM, ls=1))
    d.add(d.text("fatih-readme.plt", 138, 589, 12, MONO, fill=TEXT))
    bx0, bw = 300, 420
    d.add(rect(bx0, 582, bw, 6, 3, fill=LINE))
    d.style(f"@keyframes prog{{0%{{transform:scaleX(0)}}{pc(T)},{pc(fm)}{{transform:scaleX(1)}}{pc(fm + 0.01)},100%{{transform:scaleX(0)}}}}"
            f".prog{{transform-box:fill-box;transform-origin:left center;animation:prog {P:.3f}s linear infinite}}")
    d.add(f'<rect class="prog" x="{bx0}" y="582" width="{bw}" height="6" rx="3" fill="{VOLT}"/>')
    vis("st1", [(0, T)], False)
    vis("st2", [(T, f0)], True)
    vis("st3", [(f0, P)], False)
    d.add(f'<g class="st1">{d.text("PLOTTING", 744, 589, 11, MONOB, fill=VOLT, ls=1.2)}</g>')
    d.add(f'<g class="st2">{d.text(f"DONE IN {T:.1f}S", 744, 589, 11, MONOB, fill=TEXT, ls=1.2)}</g>')
    d.add(f'<g class="st3">{d.text("NEW SHEET", 744, 589, 11, MONOB, fill=MUTED, ls=1.2)}</g>')
    d.add(d.text("PENS", 948, 589, 10, MONOB, fill=DIM, ls=1))
    for name, sx in slots.items():
        d.add(rect(sx - 11, 570, 22, 32, 6, fill=BG, stroke=LINE, stroke_width=1))
    vis("rk1", [(t_drop, t_pick2)], False)
    d.add(f'<g class="rk1"><circle cx="{slots["ink"]}" cy="586" r="7" fill="#2E3238"/><circle cx="{slots["ink"]}" cy="586" r="4" fill="{PEN}"/></g>')
    vis("rk2", [(0, t_pick), (t_drop2, P)], True)
    d.add(f'<g class="rk2"><circle cx="{slots["volt"]}" cy="586" r="7" fill="{VOLT}"/></g>')
    d.add(f'<circle cx="{slots["coral"]}" cy="586" r="7" fill="{CORAL}"/>')

    # cable from the left carriage down to the frame
    d.add(f'<g class="cs"><rect x="8" y="{PARK[1]+40}" width="7" height="{cab_bottom-(PARK[1]+40)}" rx="3.5" fill="#2B3038"/>'
          f'<rect x="10.5" y="{PARK[1]+40}" width="2" height="{cab_bottom-(PARK[1]+40)}" fill="{DIM}"/></g>')
    # gantry: beam + carriages + cable bend ride on Y
    beam = (rect(64, -7, W - 128, 14, 4, fill="#1C1F25", stroke="#3A3F48", stroke_width=1)
            + rect(64, -1, W - 128, 2, 1, fill="#2C3139"))
    carriages = "".join(rect(cx - 21, -18, 42, 36, 7, fill="#262A31", stroke="#3F454F", stroke_width=1.2)
                        + f'<circle cx="{cx}" cy="0" r="3" fill="{DIM}"/>' for cx in (RAIL_L, RAIL_R))
    bend = '<path d="M30 6 C12 6 11.5 22 11.5 40" fill="none" stroke="#2B3038" stroke-width="7" stroke-linecap="round"/>'
    d.add(f'<g class="hy">{bend}{beam}{carriages}</g>')
    # pen head (X inside Y); the pen it holds changes at the rack
    head = (rect(-21, -25, 42, 50, 8, fill="#2A2E35", stroke="#454B56", stroke_width=1.2)
            + '<circle r="11" fill="#15171B" stroke="#454B56"/>')
    vis("hp1", [(0, t_drop), (t_pick2, P)], True)
    vis("hp2", [(t_pick, t_drop2)], False)
    head += f'<g class="hp1"><circle r="6" fill="{PEN}" stroke="#5B606A"/></g>'
    head += f'<g class="hp2"><circle r="6" fill="{VOLT}"/></g>'
    head += f'<g class="tip"><circle r="2.2" fill="{TEXT}"/></g>'
    d.add(f'<g class="hy"><g class="hx">{head}</g></g>')

    print(f"  plotter: {len(p.ink)} strokes, {len(p.kx)} keyframes, {T:.2f}s plot, {P:.2f}s loop "
          f"(outline {dict(p.marks)['outlined'] - t_dim:.2f}s, hatch {dict(p.marks)['hatched'] - dict(p.marks)['outlined']:.2f}s)")
    return d
