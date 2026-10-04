"""Hero: an XY pen plotter drafts the name on a sheet of roll paper.

Everything is computed, not keyed by hand. Glyph outlines are flattened to
polylines and unioned, the fill is a horizontal even-odd scanline hatch, and
one timeline drives the ink (stroke-dashoffset per path), the pen head (X),
the gantry beam, both rail carriages and the cable (Y), the pen rack, the
paper feed and the status bar, so the pen tip is always exactly where the
line is growing.

Story per loop: home, print pass (header, tagline, title block and notes are
printed by the bar on the beam within the first second), dimension line with
the ink width plotted in single-stroke digits, name outlines, hatch, coral pen
for a revision cloud, lime pen for the full stop, ink pen back, park. The
finished sheet then rests for most of the loop before the roll feeds it out
and the next blank sheet is already in place.

The machine is a physical object: it is dark metal in both GitHub themes and
only one file is built (save(..., themed=False)).
"""

from __future__ import annotations

import math

from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen

from motion import FALLBACK, SNAP, response
from svgkit import Doc, num, rect
from theme import (BASE_CSS, BODY, DISP, GRAPH, GRAPH2, MONO, MONOB, PALETTES, PAPER, PEN, PENSOFT, SEMI,
                   save)

# The hero is always the dark machine, whatever THEME the build runs under.
_D = PALETTES["dark"]
FRAME, FRAME_EDGE = "#0F1114", "#3A3F48"
BED = "#08090B"
D_BG, D_PANEL, D_PANEL2, D_LINE = _D["BG"], _D["PANEL"], _D["PANEL2"], _D["LINE"]
D_TEXT, D_MUTED, D_DIM = _D["TEXT"], _D["MUTED"], _D["DIM"]
LIME = "#C9F31D"
CORAL_CAP = "#FF6B3D"  # pen cap on the dark rack
CORAL_INK = "#C8481F"  # the same pen's line on cream paper, 3.9:1
METAL, METAL_EDGE = "#2A2E35", "#454B56"
COLLAR = "#8D929B"  # the steel collar of the technical ink pen

W, H = 1200, 690
RAIL_L, RAIL_R = 51, 1149  # rail centre lines
RAIL_Y0, RAIL_Y1 = 4, 616
PX0, PY0, PX1, PY1 = 104, 40, 1096, 548  # sheet window
LEFT, RIGHT = 138, 1062  # content margins on the sheet (ink edges)
PARK = (150.0, 32.0)  # pen position; every part of the head and gantry is on canvas
PEN_OFF = 12  # the pen sits on the front of the carriage, this far below the beam centre line
HOME = (PX0 + 6.0, PY0 + 6.0)

# Roll paper: sheets follow each other at a pitch that is a multiple of both grid
# periods (12 and 60), so the blank sheet below lands exactly on the grid of the
# one it replaces.
TRAVEL = 540
FEED_TIME = 2.4
FEED_EASE = (.45, 0, .3, 1)
# Feed roller radius close to 10 px, chosen so one sheet turns the roller a whole
# number of half turns (17): its drive slot has 2-fold symmetry, so the roller looks
# identical at the loop wrap, and the peak of about 52 degrees per 60 fps frame stays
# well under the 90 degree aliasing limit of that slot.
ROLLER_HALVES = 17
ROLLER_R = TRAVEL / (ROLLER_HALVES * math.pi)

DRAW_SPEED = 3600.0  # px/s, outlines
HATCH_SPEED = 4200.0  # pen carriage across a hatch row
HATCH_STEP = 8.0  # px between hatch rows, the beam steps down this much per row
HATCH_HOP = 7000.0  # pen up over the gaps inside a row
ROW_STEP_TIME = 0.025
DIM_SPEED = 2400.0
CLOUD_SPEED = 2600.0
DOT_SPEED = 1300.0
SWEEP_SPEED = 1000.0  # print pass, constant velocity over the sheet
SWEEP_RAMP = 0.10  # s of constant acceleration before and after

PLUNGE_DOWN = 0.07  # head contents scale 1 to .93, ease-in
PLUNGE_UP = 0.25  # SNAP return
PLUNGE_CLEAR = 0.12  # after the bottom of the plunge the gripper is clear and XY may move

# Timing functions (cubic-bezier control points). None is linear.
SCURVE = (.45, 0, .25, 1)  # every gantry travel move
RING = (.37, 0, .63, 1)  # one half swing of the settle, sine-like
RAMP_IN = (1 / 3, 0, 2 / 3, 1 / 3)  # y = t^2, constant acceleration
RAMP_OUT = (1 / 3, 2 / 3, 2 / 3, 1)  # y = 2t - t^2, constant deceleration
EASE_IN = (.42, 0, 1, 1)


def bez_css(tf) -> str:
    return "cubic-bezier(" + ",".join(f"{v:.3f}".rstrip("0").rstrip(".") or "0" for v in tf) + ")"


def bez(tf, u: float) -> float:
    """CSS cubic-bezier progress at input progress u (what the browser computes)."""
    if tf is None:
        return u
    x1, y1, x2, y2 = tf
    lo, hi = 0.0, 1.0
    for _ in range(50):
        s = (lo + hi) / 2
        x = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3
        if x < u:
            lo = s
        else:
            hi = s
    s = (lo + hi) / 2
    return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s * s * y2 + s ** 3


def spring_linear(s, span: float, points: int = 24) -> str:
    """CSS linear() of the spring's real step response over `span` seconds.

    The curve is not stretched to fit: it is the physical response, cut at
    `span` where it is within a couple of percent of rest, and pinned to 1."""
    _, xs = response(s)
    n = min(len(xs) - 1, round(span * 1000))
    vals = [xs[round(i * n / (points - 1))] for i in range(points)]
    vals[0], vals[-1] = 0.0, 1.0
    return "linear(" + ",".join(f"{v:.3f}".rstrip("0").rstrip(".") or "0" for v in vals) + ")"


# ---------------------------------------------------------------- geometry
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
            a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
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


def text_shape(s: str, x: float, base: float, size: float, font=DISP):
    """Union of the glyph outlines of `s` in page pixels (shapely geometry).

    Fonts build letters from overlapping shapes (the F is a stem plus two
    arms); a plotter tracing those raw contours would draw the overlaps, so
    each glyph is unioned first (non-zero winding) and only the final
    silhouette is traced."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    k = size / font.upm
    glyphs, _ = font.layout(s, size)
    parts = []
    for ch, name, gx in glyphs:
        if ch == " ":
            continue
        pen = FlattenPen(font.glyphs, step=26)
        font.glyphs[name].draw(pen)
        outers, holes = [], []
        for c in pen.contours:
            if len(c) < 4:
                continue
            pc = [(x + gx + px * k, base - py * k) for px, py in c]
            (outers if _signed_area(c) < 0 else holes).append(Polygon(pc).buffer(0))
        if not outers:  # font with the opposite winding convention
            outers, holes = holes, outers
        shape = unary_union(outers)
        if holes:
            shape = shape.difference(unary_union(holes))
        parts.append(shape)
    return unary_union(parts)


def shape_rings(shape):
    out = []
    for g in getattr(shape, "geoms", [shape]):
        for ring in [g.exterior, *g.interiors]:
            out.append([(px, py) for px, py in ring.coords])
    return out


def ink_box(font, s: str, size: float):
    """Ink bounds of `s` set at origin 0 / baseline 0, y down: (x0, top, x1, bottom)."""
    k = size / font.upm
    glyphs, _ = font.layout(s, size)
    xs0, ys0, xs1, ys1 = [], [], [], []
    for ch, name, gx in glyphs:
        if ch == " ":
            continue
        bp = BoundsPen(font.glyphs)
        font.glyphs[name].draw(bp)
        if bp.bounds is None:
            continue
        a, b, c, d = bp.bounds
        xs0.append(gx + a * k)
        xs1.append(gx + c * k)
        ys0.append(-d * k)
        ys1.append(-b * k)
    return min(xs0), min(ys0), max(xs1), max(ys1)


def hatch_rows(rings, spacing: float):
    """Horizontal even-odd hatch: rows of (x0, x1, y), top to bottom."""
    ys = [p[1] for c in rings for p in c]
    lo, hi = min(ys), max(ys)
    n = int((hi - lo) // spacing)
    y = lo + ((hi - lo) - n * spacing) / 2  # centre the rows in the ink height
    rows = []
    while y < hi:
        hits = []
        for c in rings:
            for (x0, y0), (x1, y1) in zip(c, c[1:]):
                if (y0 < y) != (y1 < y):
                    hits.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
        hits.sort()
        row = [(hits[i], hits[i + 1], y) for i in range(0, len(hits) - 1, 2) if hits[i + 1] - hits[i] > 1.5]
        if row:
            rows.append(row)
        y += spacing
    return rows


def arc(cx, cy, rx, ry, a0, a1, step=10.0):
    n = max(2, int(abs(a1 - a0) / step) + 1)
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def revision_cloud(x0, y0, x1, y1, corner: float, chord: float, bulge: float):
    """A closed revision cloud around a rounded rectangle: equal scallops whose
    circular arcs bulge outward, cusps on the rectangle. Starts at the right end
    of the bottom edge and runs clockwise on screen."""
    r = corner

    def quarter(cx, cy, a0):
        return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(a0, a0 + 91, 3)]
    pts = ([(x1 - r, y1)] + quarter(x0 + r, y1 - r, 90) + quarter(x0 + r, y0 + r, 180)
           + quarter(x1 - r, y0 + r, 270) + quarter(x1 - r, y1 - r, 0))
    # resample the perimeter at equal arc length
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total = sum(seg)
    n = max(8, round(total / chord))
    cusps, acc, i = [], 0.0, 0
    for j in range(n):
        target = j * total / n
        while acc + seg[i] < target:
            acc += seg[i]
            i += 1
        f = (target - acc) / seg[i]
        a, b = pts[i], pts[i + 1]
        cusps.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    cusps.append(cusps[0])
    out = [cusps[0]]
    for a, b in zip(cusps, cusps[1:]):
        c = math.dist(a, b)
        rr = (c * c / 4 + bulge * bulge) / (2 * bulge)
        ux, uy = (b[0] - a[0]) / c, (b[1] - a[1]) / c
        nx, ny = uy, -ux  # outward normal for clockwise travel with y down
        ccx = (a[0] + b[0]) / 2 - nx * (rr - bulge)
        ccy = (a[1] + b[1]) / 2 - ny * (rr - bulge)
        a0 = math.atan2(a[1] - ccy, a[0] - ccx)
        a1 = math.atan2(b[1] - ccy, b[0] - ccx)
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi  # minor arc, it holds the apex
        for k in range(1, 9):
            ang = a0 + da * k / 8
            out.append((ccx + rr * math.cos(ang), ccy + rr * math.sin(ang)))
    return out


# ---------------------------------------------------------------- the machine
class Plotter:
    """Records the head path as keys (t, x, y, timing function of the segment that starts here)."""

    def __init__(self):
        self.t = 0.0
        self.x, self.y = PARK
        self.keys: list[list] = [[0.0, self.x, self.y, None]]
        self.pen: list[tuple[float, int]] = [(0.0, 0)]
        self.ink: list[tuple[str, float, float, str, float]] = []  # d, t0, t1, colour, width
        self.plunges: list[tuple[float, str]] = []
        self.marks: dict[str, float] = {}
        self.peak_settle = 0.0

    def seg(self, dt, x, y, tf=None):
        self.keys[-1][3] = tf
        self.t += dt
        self.x, self.y = x, y
        self.keys.append([self.t, x, y, None])

    def pen_set(self, down: int):
        if self.pen[-1][1] != down:
            self.pen.append((self.t, down))

    def wait(self, dt):
        self.seg(dt, self.x, self.y)

    def travel(self, x, y, settle=True):
        """One controller for every move: an S-curve whose duration grows with the
        square root of the distance (constant peak acceleration), then a settle of
        fixed length whose amplitude is bounded in pixels."""
        dist = math.dist((self.x, self.y), (x, y))
        if dist < 0.01:
            return
        self.pen_set(0)
        if dist < 1.0:  # a sub-pixel correction, not a move
            self.seg(0.004, x, y)
            return
        dt = 0.12 + 2 * math.sqrt(dist / 16000)
        a = min(2.5, 0.006 * dist) if settle else 0.0
        if a < 0.5:  # below half a pixel the ring cannot render: short moves just stop
            self.seg(dt, x, y, SCURVE)
            return
        ux, uy = (x - self.x) / dist, (y - self.y) / dist
        self.peak_settle = max(self.peak_settle, a)
        self.seg(dt, x + a * ux, y + a * uy, SCURVE)
        self.seg(0.06, x - 0.3 * a * ux, y - 0.3 * a * uy, RING)
        self.seg(0.06, x, y, RING)

    def hop(self, x, y, speed, min_dt=0.0):
        """Pen-up move inside one fill, at carriage speed."""
        dist = math.dist((self.x, self.y), (x, y))
        if dist < 0.01:
            return
        self.pen_set(0)
        self.seg(max(min_dt, dist / speed), x, y)

    def stroke(self, pts, colour=PEN, width=2.0, speed=DRAW_SPEED, approach="travel", hop_speed=None, min_dt=0.0):
        if approach == "travel":
            self.travel(*pts[0])
        else:
            self.hop(*pts[0], speed=hop_speed or speed, min_dt=min_dt)
        self.pen_set(1)
        t0 = self.t
        for p in pts[1:]:
            self.seg(math.dist((self.x, self.y), p) / speed, p[0], p[1])
        d = "M" + "L".join(f"{num(px)} {num(py)}" for px, py in pts)
        self.ink.append((d, t0, self.t, colour, width))
        self.pen_set(0)

    def plunge(self, slot: str):
        self.plunges.append((self.t, slot))
        self.wait(PLUNGE_DOWN + PLUNGE_CLEAR)

    def sweep(self, y1, v=SWEEP_SPEED, ramp=SWEEP_RAMP):
        """Print pass: trapezoidal velocity in Y (constant acceleration, constant
        speed, constant deceleration)."""
        y0 = self.y
        s = v * ramp / 2
        self.seg(ramp, self.x, y0 + s, RAMP_IN)
        self.seg((y1 - y0 - 2 * s) / v, self.x, y1 - s)
        self.seg(ramp, self.x, y1, RAMP_OUT)

    def mark(self, name):
        self.marks[name] = self.t
        return self.t

    # evaluation, used for the print reveal times and for checks
    def at(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1], ks[0][2]
        for a, b in zip(ks, ks[1:]):
            if a[0] <= t <= b[0]:
                u = 0.0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
                f = bez(a[3], u)
                return a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f
        return ks[-1][1], ks[-1][2]

    def first_time_at_y(self, y, t0, t1):
        """First instant in [t0, t1] at which the beam centre reaches y (monotonic sweep)."""
        lo, hi = t0, t1
        for _ in range(60):
            m = (lo + hi) / 2
            if self.at(m)[1] < y:
                lo = m
            else:
                hi = m
        return hi


def simplify(keys, idx):
    """Drop keys that sit on a straight line in (time, value) between linear neighbours."""
    pts = [(k[0], k[idx], k[3]) for k in keys]
    n = len(pts)
    kept = [0]
    for i in range(1, n - 1):
        k = kept[-1]
        if all(pts[j][2] is None for j in range(k, i + 1)):
            tk, vk = pts[k][0], pts[k][1]
            tn, vn = pts[i + 1][0], pts[i + 1][1]
            if tn > tk and all(abs(vk + (vn - vk) * (pts[j][0] - tk) / (tn - tk) - pts[j][1]) < 0.04
                               for j in range(k + 1, i + 1)):
                continue
        kept.append(i)
    kept.append(n - 1)
    return [pts[i] for i in kept]


def build() -> Doc:
    d = Doc(W, H, "Fatih Al Jabar: Front-End & Full-Stack Developer",
            "A pen plotter prints a drafting sheet: 'Interfaces that feel fast and obvious, with a backend behind them "
            "that stays out of the way', a title block (Fatih Al Jabar, Front-End & Full-Stack Developer, Indonesia, UTC+7, "
            "open to remote work) and notes (React, Next.js and TypeScript every day, Vue when the job calls for it; "
            "now building the Blockwave Studios marketplace for production). It then plots and hatches the name "
            "Fatih with a measured dimension line, rings 'fast and obvious' with a coral revision cloud, adds a lime "
            "full stop and parks.")
    d.style(BASE_CSS)
    p = Plotter()

    # ---------------------------------------------------------------- layout
    size, nbase = 232, 300
    fx0, _, _, _ = ink_box(DISP, "F", size)
    nx = LEFT - fx0
    name = text_shape("Fatih", nx, nbase, size)
    ix0, _, ix1, _ = name.bounds  # ink of the unioned outlines
    rings = shape_rings(name)
    r_dot = 18.0
    dot_c = (ix1 + 22 + r_dot, nbase - r_dot - 1.5)

    # title block: upper right quadrant, bottom edge on the name baseline
    # each field carries its caption in the top left corner and the value below it, so a
    # value can use the full width of the block
    tb_x0, tb_x1, rh = 784, RIGHT, 46
    rows_tb = [("DRAWN BY", "Fatih Al Jabar"), ("ROLE", "Front-End & Full-Stack Developer"),
               ("LOCATION", "Indonesia, UTC+7"), ("STATUS", "Open to remote work")]
    tb_y0 = nbase - rh * len(rows_tb)

    # tagline, with room on both sides of "fast and obvious," for the cloud
    t1_size, t2_size = 36, 23
    pre, hi_s = "Interfaces that feel", "fast and obvious,"
    pre_x = LEFT - ink_box(SEMI, "I", t1_size)[0]
    pre_ink = ink_box(SEMI, pre, t1_size)
    hb = ink_box(SEMI, hi_s, t1_size)
    gap_x = 27.0  # ink to ink between "feel" and "fast", cloud runs through the middle
    hi_x = pre_x + pre_ink[2] + gap_x - hb[0]
    y1 = nbase + 68
    cl_pad_x, cl_pad_y, bulge = 7.0, 6.0, 5.0
    cx0, cy0 = hi_x + hb[0] - cl_pad_x, y1 + hb[1] - cl_pad_y
    cx1, cy1 = hi_x + hb[2] + cl_pad_x, y1 + hb[3] - 1 + cl_pad_y
    cloud = revision_cloud(cx0, cy0, cx1, cy1, corner=14, chord=19, bulge=bulge)
    y2 = cy1 + bulge + 12 + 17
    l2_x = LEFT - ink_box(BODY, "w", t2_size)[0]

    notes = ["React, Next.js and TypeScript every day. Vue when the job calls for it.",
             "Now building the Blockwave Studios marketplace for production."]
    n_base = [492, 518]

    # ---------------------------------------------------------------- the plot
    p.wait(0.05)
    p.travel(*HOME)  # touch the sheet corner, like a real machine finding zero
    p.wait(0.06)
    sweep_t0 = p.t
    p.sweep(522 + PEN_OFF + 4)
    sweep_t1 = p.t
    p.mark("printed")

    def printed_at(y):
        """The print bar is the beam: a line is down once the beam centre has crossed its bottom."""
        return p.first_time_at_y(y + PEN_OFF, sweep_t0, sweep_t1)

    # dimension line: it measures the ink, extension lines touch the outlines
    from shapely.geometry import LineString

    def top_at(x):
        hit = name.intersection(LineString([(x, 0), (x, H)]))
        return hit.bounds[1]

    dy = 104
    e0 = top_at(ix0 + 0.4)
    e1 = top_at(ix1 - 0.4)
    width_label = str(round(ix1 - ix0))
    lw = MONOB.width(width_label, 16)
    gl = (ix0 + ix1) / 2 - lw / 2 - 12
    gr = (ix0 + ix1) / 2 + lw / 2 + 12
    al, aw = 13, 4
    # right half first so the pen ends on the F, where the outlines start
    p.stroke([(ix1, e1), (ix1, dy - 9), (ix1, dy), (ix1 - al, dy - aw), (ix1, dy), (ix1 - al, dy + aw), (ix1, dy), (gr, dy)],
             width=1.4, speed=DIM_SPEED)
    p.travel(gl, dy)
    p.stroke([(gl, dy), (ix0, dy), (ix0 + al, dy - aw), (ix0, dy), (ix0 + al, dy + aw), (ix0, dy), (ix0, dy - 9), (ix0, e0)],
             width=1.4, speed=DIM_SPEED)
    p.mark("dim")

    # outlines in reading order, each ring entered at its point nearest the pen
    left = rings[:]
    while left:
        # reading order by glyph column, nearest ring within it
        col = min(round(min(x for x, _ in c)) for c in left)
        cands = [c for c in left if min(x for x, _ in c) < col + 30]
        c = min(cands, key=lambda c: min(math.dist((p.x, p.y), q) for q in c))
        left.remove(c)
        j = min(range(len(c) - 1), key=lambda i: math.dist((p.x, p.y), c[i]))
        ring = c[j:-1] + c[:j] + [c[j]]
        p.stroke(ring, width=2.2, speed=DRAW_SPEED)
    p.mark("outlined")

    # hatch: horizontal rows, back and forth, the beam only steps down between rows
    rows = hatch_rows(rings, HATCH_STEP)
    first = rows[0]
    flip = math.dist((p.x, p.y), (first[-1][1], first[-1][2])) < math.dist((p.x, p.y), (first[0][0], first[0][2]))
    for ri, row in enumerate(rows):
        segs = [(b, a, y) for a, b, y in row[::-1]] if flip else row
        for si, (a, b, y) in enumerate(segs):
            if ri == 0 and si == 0:
                p.stroke([(a, y), (b, y)], width=1.4, speed=HATCH_SPEED)
            elif si == 0:
                p.stroke([(a, y), (b, y)], width=1.4, speed=HATCH_SPEED, approach="hop", hop_speed=HATCH_HOP,
                         min_dt=ROW_STEP_TIME)
            else:
                p.stroke([(a, y), (b, y)], width=1.4, speed=HATCH_SPEED, approach="hop", hop_speed=HATCH_HOP)
        flip = not flip
    p.mark("hatched")

    # pen rack below the sheet: ink, coral, lime
    rack_y = 590
    slots = {"ink": 900.0, "coral": 930.0, "lime": 960.0}

    def swap(drop, pick):
        p.travel(slots[drop], rack_y)
        p.plunge(drop)
        p.travel(slots[pick], rack_y)
        p.plunge(pick)

    swap("ink", "coral")
    # revision cloud around "fast and obvious", entered at its bottom right
    p.stroke(cloud, colour=CORAL_INK, width=1.6, speed=CLOUD_SPEED)
    p.mark("cloud")
    swap("coral", "lime")
    # the full stop: one full circle for a clean edge, then an Archimedean spiral
    # filled from the outside in (3 px pitch under a 3.6 px marker)
    th0 = math.atan2(rack_y - dot_c[1], slots["lime"] - dot_c[0])
    spiral = [(dot_c[0] + r_dot * math.cos(th0 + a * math.pi / 15), dot_c[1] + r_dot * math.sin(th0 + a * math.pi / 15))
              for a in range(30)]
    turns = r_dot / 3.0
    steps = int(turns * 30)
    for i in range(steps + 1):
        f = i / steps
        r = r_dot * (1 - f)
        th = th0 + f * turns * 2 * math.pi
        spiral.append((dot_c[0] + r * math.cos(th), dot_c[1] + r * math.sin(th)))
    p.stroke(spiral, colour=LIME, width=3.6, speed=DOT_SPEED)
    t_fin = p.mark("finished")
    swap("lime", "ink")
    p.travel(*PARK, settle=False)  # the gantry never overshoots toward its end stops
    T = p.t

    # the roll-fed loop: rest on the finished sheet, then feed one sheet pitch
    # The finished sheet must hold the screen for at least 65% of the loop, counted
    # from the moment the head is parked (stricter than counting from the last ink).
    REST_SHARE = 0.655
    f0 = (T + REST_SHARE * FEED_TIME) / (1 - REST_SHARE)
    P = round(f0 + FEED_TIME, 1)
    f0 = P - FEED_TIME
    p.keys[-1][3] = None
    p.keys.append([P, PARK[0], PARK[1], None])

    def pc(t):
        return f"{max(0.0, min(100.0, t / P * 100)):.4f}".rstrip("0").rstrip(".") + "%"

    def vis(cls, spans, static_on):
        """Discrete visibility over the loop. spans: [(start, end)] in seconds."""
        pts = sorted({0.0, P, *[min(P, max(0.0, x)) for sp in spans for x in sp]})

        def on(t):
            return any(a0 <= t < a1 for a0, a1 in spans)
        frames = "".join(f"{pc(t)}{{opacity:{1 if on(min(t, P - 1e-6)) else 0}}}" for t in pts)
        d.style(f"@keyframes {cls}k{{{frames}}}"
                f".{cls}{{opacity:{1 if static_on else 0};animation:{cls}k {P:.2f}s steps(1,end) infinite}}")

    def channel_css(name, idx, fmt):
        out, last = [], -1.0
        for t, v, tf in simplify(p.keys, idx):
            pct = float(pc(t)[:-1])
            if pct <= last:
                pct = last + 0.0001
            last = pct
            tfc = f";animation-timing-function:{bez_css(tf)}" if tf else ""
            out.append(f"{pct:.4f}".rstrip("0").rstrip(".") + f"%{{{fmt(v)}{tfc}}}")
        return f"@keyframes {name}{{" + "".join(out) + "}"

    # ---------------------------------------------------------------- CSS timeline
    d.style(channel_css("hx", 1, lambda v: f"transform:translateX({v:.1f}px)"))
    d.style(channel_css("hy", 2, lambda v: f"transform:translateY({v:.1f}px)"))
    d.style(f".hx{{transform:translateX({PARK[0]:g}px);animation:hx {P:.2f}s linear infinite}}"
            f".hy{{transform:translateY({PARK[1]:g}px);animation:hy {P:.2f}s linear infinite}}")

    # pen tip contact (down / up)
    downs, start = [], None
    for t, down in p.pen + [(T, 0)]:
        if down and start is None:
            start = t
        elif not down and start is not None:
            downs.append((start, t))
            start = None
    vis("tip", downs, False)

    # ink: each stroke draws during its window, then rides out with the sheet
    css = []
    for i, (_, t0, t1, _, _) in enumerate(p.ink):
        t1 = max(t1, t0 + 0.004)
        css.append(f"@keyframes k{i}{{0%,{pc(t0)}{{stroke-dashoffset:1}}{pc(t1)},100%{{stroke-dashoffset:0}}}}"
                   f".k{i}{{animation:k{i} {P:.2f}s linear infinite}}")
    d.style(".ink{stroke-dasharray:1 2;fill:none;stroke-linecap:round;stroke-linejoin:round}" + "".join(css))

    # paper feed: the roll moves one sheet pitch, the blank sheet below lands where this one started
    feed_tf = bez_css(FEED_EASE)
    d.style(f"@keyframes feed{{0%,{pc(f0)}{{transform:translateY(0);animation-timing-function:{feed_tf}}}"
            f"100%{{transform:translateY(-{TRAVEL}px)}}}}"
            f".feed{{animation:feed {P:.2f}s linear infinite}}")
    roll_deg = ROLLER_HALVES * 180  # = TRAVEL / ROLLER_R in degrees
    d.style(f"@keyframes roll{{0%,{pc(f0)}{{transform:rotate(0);animation-timing-function:{feed_tf}}}"
            f"100%{{transform:rotate(-{roll_deg}deg)}}}}"
            f".roll{{animation:roll {P:.2f}s linear infinite}}")

    # pen swaps: head contents plunge, the slot gives 1.5 px, both return on SNAP
    snap = f"{FALLBACK[SNAP]};animation-timing-function:{spring_linear(SNAP, PLUNGE_UP)}"
    ein = bez_css(EASE_IN)

    def plunge_css(cls, times, frm, to, contact=0.0):
        fr = ["0%{" + frm + "}"]
        for tp in times:
            fr.append(f"{pc(tp + contact)}{{{frm};animation-timing-function:{ein}}}")
            fr.append(f"{pc(tp + PLUNGE_DOWN)}{{{to};animation-timing-function:{snap}}}")
            fr.append(f"{pc(tp + PLUNGE_DOWN + PLUNGE_UP)}{{{frm}}}")
        fr.append("100%{" + frm + "}")
        d.style(f"@keyframes {cls}k{{{''.join(fr)}}}.{cls}{{animation:{cls}k {P:.2f}s linear infinite}}")

    plunge_css("pl", [t for t, _ in p.plunges], "transform:scale(1)", "transform:scale(.93)")
    for s in slots:
        plunge_css(f"sl{s[0]}", [t for t, sl in p.plunges if sl == s], "transform:translateY(0)",
                   "transform:translateY(1.5px)", contact=PLUNGE_DOWN / 2)

    # ---------------------------------------------------------------- frame and bed
    d.defs.append(f'<pattern id="g1" width="12" height="12" patternUnits="userSpaceOnUse" x="{PX0}" y="{PY0}">'
                  f'<path d="M12 0V12H0" fill="none" stroke="{GRAPH}" stroke-width=".6"/></pattern>'
                  f'<pattern id="g5" width="60" height="60" patternUnits="userSpaceOnUse" x="{PX0}" y="{PY0}">'
                  f'<path d="M60 0V60H0" fill="none" stroke="{GRAPH2}" stroke-width=".9"/></pattern>'
                  f'<clipPath id="sheet"><rect x="{PX0 - 6}" y="{PY0}" width="{PX1 - PX0 + 12}" height="{PY1 - PY0}"/></clipPath>'
                  f'<clipPath id="cab"><rect x="0" y="0" width="40" height="644"/></clipPath>')
    d.add(rect(0.5, 0.5, W - 1, H - 1, 22, fill=FRAME, stroke=FRAME_EDGE, stroke_width=1))
    d.add(rect(PX0 - 6, PY0, PX1 - PX0 + 12, PY1 - PY0, 4, fill=BED))

    # rails with machined scales
    for cx, side in ((RAIL_L, -1), (RAIL_R, 1)):
        d.add(rect(cx - 25, RAIL_Y0, 50, RAIL_Y1 - RAIL_Y0, 9, fill=D_PANEL2, stroke=D_LINE, stroke_width=1.2))
        d.add(rect(cx - 3, RAIL_Y0 + 12, 6, RAIL_Y1 - RAIL_Y0 - 24, 3, fill=D_BG))
        ticks = []
        for y in range(PY0, 601, 10):
            long_ = (y - PY0) % 50 == 0
            x0 = cx + side * 9
            x1 = x0 + side * (9 if long_ else 5)
            ticks.append(f"M{x0} {y}H{x1}")
        d.add(f'<path d="{"".join(ticks)}" stroke="{D_DIM}" stroke-width="1"/>')

    # ---------------------------------------------------------------- the roll
    sheet_h = PY1 - PY0
    strip_h = TRAVEL + sheet_h
    d.add(f'<g clip-path="url(#sheet)"><g class="feed">')
    d.add(f'<rect x="{PX0}" y="{PY0}" width="{PX1 - PX0}" height="{strip_h}" fill="{PAPER}"/>'
          f'<rect x="{PX0}" y="{PY0}" width="{PX1 - PX0}" height="{strip_h}" fill="url(#g1)"/>'
          f'<rect x="{PX0}" y="{PY0}" width="{PX1 - PX0}" height="{strip_h}" fill="url(#g5)"/>')
    marks = []
    for off in (0, TRAVEL):
        for cx, cy in ((PX0 + 16, PY0 + 16), (PX1 - 16, PY0 + 16), (PX0 + 16, PY1 - 16), (PX1 - 16, PY1 - 16)):
            cy += off
            marks.append(f'<circle cx="{cx}" cy="{cy}" r="5"/><path d="M{cx-9} {cy}H{cx+9}M{cx} {cy-9}V{cy+9}"/>')
    perf_y = PY1 + (TRAVEL - sheet_h) / 2
    d.add(f'<g fill="none" stroke="{PENSOFT}" stroke-width=".9">{"".join(marks)}</g>'
          f'<path d="M{PX0} {perf_y}H{PX1}" stroke="{GRAPH2}" stroke-width="1.2" stroke-dasharray="6 5"/>')

    # printed matter: the bar on the beam lays each line down as it passes
    pi = [0]

    def printed(svg, y):
        cls = f"p{pi[0]}"
        pi[0] += 1
        vis(cls, [(printed_at(y), P)], True)
        d.add(f'<g class="{cls}">{svg}</g>')

    hdr = 74
    printed(d.text("fatihaljabar / README.md", LEFT - ink_box(MONO, "f", 16)[0], hdr, 16, MONO, fill=PENSOFT)
            + d.text("Sheet 1 of 1   Scale 1:1   Units px", RIGHT, hdr, 16, MONO, fill=PENSOFT, anchor="end"), hdr + 4)

    printed(d.text(width_label, (ix0 + ix1) / 2, dy + 5.8, 16, MONOB, fill=PEN, anchor="middle"), dy + 6)

    # title block, row by row
    for i, (k, v) in enumerate(rows_tb):
        ry0 = tb_y0 + rh * i
        assert SEMI.width(v, 16) <= tb_x1 - tb_x0 - 20, v
        lines = f"M{tb_x0} {ry0}H{tb_x1}M{tb_x0} {ry0}V{ry0 + rh}M{tb_x1} {ry0}V{ry0 + rh}"
        if i == len(rows_tb) - 1:
            lines += f"M{tb_x0} {ry0 + rh}H{tb_x1}"
        svg = (f'<path d="{lines}" fill="none" stroke="{PEN}" stroke-width="1.2" stroke-linecap="square"/>'
               + d.text(k, tb_x0 + 10, ry0 + 15.5, 12, MONOB, fill=PENSOFT, ls=0.6)
               + d.text(v, tb_x0 + 10, ry0 + 37, 16, SEMI, fill=PEN))
        printed(svg, ry0 + rh)

    printed(d.text(pre, pre_x, y1, t1_size, SEMI, fill=PEN) + d.text(hi_s, hi_x, y1, t1_size, SEMI, fill=PEN), y1 + 7)
    printed(d.text("with a backend behind them that stays out of the way.", l2_x, y2, t2_size, BODY, fill=PENSOFT), y2 + 5)
    rule_y = n_base[0] - 34
    printed(f'<path d="M{LEFT} {rule_y}H{RIGHT}" stroke="{PEN}" stroke-width="1"/>', rule_y + 1)
    num_x = LEFT - ink_box(MONOB, "1", 16)[0]
    for i, ln in enumerate(notes):
        y = n_base[i]
        printed(d.text(f"{i + 1}.", num_x, y, 16, MONOB, fill=PENSOFT) + d.text(ln, num_x + 29, y, 16, MONO, fill=PEN), y + 4)

    # plotted ink
    for i, (dd, t0, t1, col, wdt) in enumerate(p.ink):
        d.add(f'<path class="ink k{i}" pathLength="1" d="{dd}" stroke="{col}" stroke-width="{wdt}"/>')
    d.add("</g></g>")

    # feed rollers pinch the strip at the bottom edge of the window
    for rx in (PX0 + 60, PX1 - 60):
        r = ROLLER_R
        d.add(f'<g transform="translate({rx} {PY1 + 4})"><g class="roll fb"><circle r="{r:.2f}" fill="#22262D" stroke="{METAL_EDGE}"/>'
              f'<path d="M-{r - 3:.1f} 0H{r - 3:.1f}" stroke="#7A808A" stroke-width="2.4" stroke-linecap="round"/></g></g>')

    # ---------------------------------------------------------------- pen rack
    rx0 = slots["ink"] - 18
    d.add(rect(rx0, rack_y - 22, slots["lime"] + 18 - rx0, 44, 9, fill="#16191E", stroke="#2C3139", stroke_width=1))
    t_drop = {s: [t + PLUNGE_DOWN for t, sl in p.plunges if sl == s] for s in slots}
    # each slot is visited twice: ink is dropped then picked, coral and lime picked then dropped
    ink_slot = (t_drop["ink"][0], t_drop["ink"][1])
    coral_head = (t_drop["coral"][0], t_drop["coral"][1])
    lime_head = (t_drop["lime"][0], t_drop["lime"][1])
    for s, sx in slots.items():
        pen_svg = {
            "ink": f'<circle cx="{sx}" cy="{rack_y}" r="7" fill="{COLLAR}"/><circle cx="{sx}" cy="{rack_y}" r="3.6" fill="{PEN}"/>',
            "coral": f'<circle cx="{sx}" cy="{rack_y}" r="7" fill="{CORAL_CAP}"/>',
            "lime": f'<circle cx="{sx}" cy="{rack_y}" r="7" fill="{LIME}"/>',
        }[s]
        if s == "ink":
            vis("rki", [ink_slot], False)
        elif s == "coral":
            vis("rkc", [(0, coral_head[0]), (coral_head[1], P)], True)
        else:
            vis("rkl", [(0, lime_head[0]), (lime_head[1], P)], True)
        d.add(f'<g class="sl{s[0]}">' + rect(sx - 11, rack_y - 16, 22, 32, 6, fill=D_BG, stroke=D_LINE, stroke_width=1)
              + f'<g class="rk{s[0]}">{pen_svg}</g></g>')

    # ---------------------------------------------------------------- status bar, below the rails
    sb_y, sb_h = 628, 40
    d.add(rect(26, sb_y, W - 52, sb_h, 10, fill=D_PANEL, stroke=D_LINE, stroke_width=1))
    tb = sb_y + sb_h / 2 + 5.5
    d.add(d.text("fatih-readme.plt", 48, tb, 16, MONO, fill=D_TEXT))
    bx0, bx1 = 236, 980
    d.add(rect(bx0, sb_y + sb_h / 2 - 3, bx1 - bx0, 6, 3, fill=D_LINE))
    d.style(f"@keyframes prog{{0%{{transform:scaleX(0)}}{pc(T)},100%{{transform:scaleX(1)}}}}"
            f".prog{{transform-box:fill-box;transform-origin:left center;animation:prog {P:.2f}s linear infinite}}")
    d.add(f'<rect class="prog" x="{bx0}" y="{sb_y + sb_h / 2 - 3}" width="{bx1 - bx0}" height="6" rx="3" fill="{LIME}"/>')
    vis("st1", [(0, T)], False)
    vis("st2", [(T, f0)], True)
    vis("st3", [(f0, P)], False)
    d.add(f'<g class="st1">{d.text("Plotting", 1004, tb, 16, MONO, fill=LIME)}</g>')
    d.add(f'<g class="st2">{d.text(f"Done in {T:.1f} s", 1004, tb, 16, MONO, fill=D_TEXT)}</g>')
    d.add(f'<g class="st3">{d.text("Feeding sheet", 1004, tb, 16, MONO, fill=D_MUTED)}</g>')

    # ---------------------------------------------------------------- cable, gantry, head
    # the cable hangs from the left carriage and runs into a grommet in the frame
    cab0 = 40 - PEN_OFF
    d.add(f'<g clip-path="url(#cab)"><g class="hy"><rect x="8" y="{cab0}" width="7" height="700" rx="3.5" fill="#2B3038"/>'
          f'<rect x="10.5" y="{cab0}" width="2" height="700" fill="{D_DIM}"/></g></g>')
    d.add(rect(4, 640, 15, 12, 4, fill="#1C1F25", stroke=FRAME_EDGE, stroke_width=1))
    by = -PEN_OFF
    beam = (rect(64, by - 6, W - 128, 12, 4, fill="#1C1F25", stroke="#3A3F48", stroke_width=1)
            + rect(64, by - 1, W - 128, 2, 1, fill="#2C3139"))
    carriages = "".join(rect(cx - 21, by - 16, 42, 32, 7, fill="#262A31", stroke="#3F454F", stroke_width=1.2)
                        + f'<circle cx="{cx}" cy="{by}" r="3" fill="{D_DIM}"/>' for cx in (RAIL_L, RAIL_R))
    bend = (f'<path d="M30 {by + 6} C12 {by + 6} 11.5 {by + 22} 11.5 {cab0}" fill="none" stroke="#2B3038" '
            f'stroke-width="7" stroke-linecap="round"/>')
    d.add(f'<g class="hy">{bend}{beam}{carriages}</g>')

    # the invisible frame centres the fill box on the pen, so the plunge scales about it
    head = ('<rect x="-21" y="-30" width="42" height="60" fill="none"/>'
            + rect(-21, -30, 42, 46, 8, fill=METAL, stroke=METAL_EDGE, stroke_width=1.2)
            + f'<circle r="11" fill="#15171B" stroke="{METAL_EDGE}"/><circle r="6.5" fill="#060708"/>')
    vis("hpi", [(0, t_drop["ink"][0]), (t_drop["ink"][1], P)], True)
    vis("hpc", [coral_head], False)
    vis("hpl", [lime_head], False)
    head += f'<g class="hpi"><circle r="6.5" fill="{COLLAR}"/><circle r="3.4" fill="{PEN}"/></g>'
    head += f'<g class="hpc"><circle r="6" fill="{CORAL_CAP}"/></g>'
    head += f'<g class="hpl"><circle r="6" fill="{LIME}"/></g>'
    head += f'<g class="tip"><circle r="2.2" fill="{D_TEXT}"/></g>'
    d.add(f'<g class="hy"><g class="hx"><g class="pl fb">{head}</g></g></g>')

    # ---------------------------------------------------------------- report
    m = p.marks
    hold = (f0 - t_fin) / P
    print(f"  plotter: {len(p.ink)} strokes, {len(p.keys)} keys, plot {T:.2f}s (ink done {t_fin:.2f}s), loop {P:.2f}s, "
          f"finished sheet {hold * 100:.1f}% of the loop ({(f0 - T) / P * 100:.1f}% after park)")
    print(f"  phases: printed {m['printed']:.2f}s, dim {m['dim']:.2f}s, outline {m['outlined'] - m['dim']:.2f}s, "
          f"hatch {m['hatched'] - m['outlined']:.2f}s ({len(rows)} rows), cloud done {m['cloud']:.2f}s; "
          f"ink width {ix1 - ix0:.1f} px ({ix0:.1f} to {ix1:.1f}), dot right {dot_c[0] + r_dot:.1f}")
    build.plotter = p  # for checks
    build.loop = P
    save("hero.svg", d, themed=False)
    return d
