"""Section headers (a vernier caliper measures each title), keycap buttons,
the odometer strip and the stamped footer.

Every asset here follows THEME like the rest of the build: the dark run writes
<name>.svg and THEME=light writes <name>-light.svg through theme.save().

All motion loops, because GitHub starts every SVG animation at page load and
most of these images sit below the fold. Every loop keeps its moving parts in
a nested pair of groups: the outer group plays the one-time intro, the inner
group plays the replay on a long period, and both rest at the identity
transform, so the static (reduced-motion) frame is always the end state.
"""

from __future__ import annotations

import json
import math
import os
import random

from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen

from motion import SETTLE, duration, spring_tf
from svgkit import Doc, Font, num, rect
from theme import *  # noqa: F403

HERE = os.path.dirname(os.path.abspath(__file__))
DARK = THEME == "dark"

# Easing shapes with a physical meaning, used by several parts below.
IMPACT = "cubic-bezier(.22,.6,.5,.9)"  # a hand flick: fast start, still moving at contact
RISE = "cubic-bezier(.33,.67,.67,1)"  # y = 2t - t^2: launched upward, decelerating to a stop
FALL = GRAVITY  # y = t^2: from rest, accelerating
SMOOTH = "cubic-bezier(.45,0,.55,1)"


# ---------------------------------------------------------------------------
# Keyframe helpers
# ---------------------------------------------------------------------------
def _pct(t: float, period: float) -> str:
    p = max(0.0, min(100.0, t / period * 100))
    s = f"{p:.3f}".rstrip("0").rstrip(".")
    return (s or "0") + "%"


def keyframes(name: str, period: float, frames: list[tuple[float, str, str | None]]) -> str:
    """frames: (time in s, declarations, timing) where timing is a CSS easing or a
    full declaration pair from motion.spring_tf. Times are converted to percentages."""
    out = []
    for t, decl, tf in frames:
        body = decl
        if tf:
            body += ";" + (tf if tf.startswith("animation-timing-function") else f"animation-timing-function:{tf}")
        out.append(f"{_pct(t, period)}{{{body}}}")
    return f"@keyframes {name}{{{''.join(out)}}}"


def bounce_frames(t: float, v_in: float, e: float, a: float, prop, min_h: float = 0.2):
    """A part hits a stop at time t with speed v_in (px/s) and rebounds away from it.
    Each rebound leaves at e times the arrival speed and is pulled back with a
    constant deceleration a (px/s^2), so it rises on y = 2t - t^2 and falls on y = t^2.
    Returns keyframes from the contact on and the time the part is at rest."""
    frames = []
    v = v_in * e
    while True:
        h = v * v / (2 * a)
        if h < min_h:
            break
        tu = v / a
        frames.append((t, prop(0), RISE))
        frames.append((t + tu, prop(h), FALL))
        t += 2 * tu
        v *= e
    frames.append((t, prop(0), None))
    return frames, t


# ---------------------------------------------------------------------------
# Glyph geometry: the ink, not the advance width
# ---------------------------------------------------------------------------
class _FlatPen(BasePen):
    """Flattens an outline into points so we can ask where the ink actually is."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.pts: list[tuple[float, float]] = []
        self._cur = (0.0, 0.0)

    def _moveTo(self, p):
        self._cur = p
        self.pts.append(p)

    def _lineTo(self, p):
        self._cur = p
        self.pts.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._cur
        for i in range(1, 49):
            t = i / 48
            m = 1 - t
            self.pts.append((m ** 3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t ** 3 * p3[0],
                             m ** 3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t ** 3 * p3[1]))
        self._cur = p3

    def _qCurveToOne(self, p1, p2):
        p0 = self._cur
        for i in range(1, 49):
            t = i / 48
            m = 1 - t
            self.pts.append((m * m * p0[0] + 2 * m * t * p1[0] + t * t * p2[0],
                             m * m * p0[1] + 2 * m * t * p1[1] + t * t * p2[1]))
        self._cur = p2


def ink_points(font: Font, s: str, size: float, x: float, base: float) -> list[list[tuple[float, float]]]:
    """Outline points per glyph in canvas coordinates (y down)."""
    k = size / font.upm
    glyphs, _ = font.layout(s, size)
    out = []
    for ch, name, gx in glyphs:
        pen = _FlatPen(font.glyphs)
        font.glyphs[name].draw(pen)
        out.append([(x + gx + px * k, base - py * k) for px, py in pen.pts])
    return out


def ink_x_bounds(font: Font, s: str, size: float) -> tuple[float, float]:
    """Exact horizontal ink extent at x=0 from the curve extrema (BoundsPen),
    including kerning offsets."""
    k = size / font.upm
    glyphs, _ = font.layout(s, size)
    x0, x1 = math.inf, -math.inf
    for ch, name, gx in glyphs:
        bp = BoundsPen(font.glyphs)
        font.glyphs[name].draw(bp)
        if bp.bounds is None:
            continue
        xmin, _, xmax, _ = bp.bounds
        x0 = min(x0, gx + xmin * k)
        x1 = max(x1, gx + xmax * k)
    return x0, x1


# ---------------------------------------------------------------------------
# Caliper section header
# ---------------------------------------------------------------------------
SECTIONS = [
    ("work", "Featured projects"),
    ("stack", "Tech stack"),
    ("thesis", "Thesis"),
    ("certs", "Certifications"),
    ("stats", "GitHub activity"),
]

# The instrument is brushed steel: graphite in the dark build, pale steel in the
# light one. The LCD is a physical display and stays dark with lime segments.
CAL = {
    "dark": dict(beam="#2A2E35", edge="#474D58", tick="#A3A8B0", blade="#353A43", body="#31363F",
                 slot="#15171B", knurl="#8D939C", hub="#5B616B", lcd="#0D0F11", lcdedge="#535A65"),
    "light": dict(beam="#DADDE1", edge="#9EA4AD", tick="#3B4048", blade="#CBCFD5", body="#C9CDD3",
                  slot="#8E949D", knurl="#4A5058", hub="#7B818A", lcd="#1A1D21", lcdedge="#6E747D"),
}[THEME]

CAL_PERIOD = 16.0


def section_header(slug: str, title: str) -> None:
    c = CAL
    W, H = 1200, 168
    size, base = 70, 142
    X0 = 34.0  # the fixed jaw face, identical on every header
    ix0, ix1 = ink_x_bounds(DISP, title, size)
    tx = X0 - ix0
    x0, x1 = X0, tx + ix1  # jaw faces sit exactly on the ink
    measure = x1 - x0
    reading = f"{measure:.2f}"

    # where the extremes touch the faces (y ranges), for the contact flash
    glyph_pts = ink_points(DISP, title, size, tx, base)
    pts = [p for g in glyph_pts for p in g]
    near0 = [y for x, y in pts if x < x0 + 0.6]
    near1 = [y for x, y in pts if x > x1 - 0.6]

    d = Doc(W, H, title, f"Section header: {title}. A vernier caliper closes on the title and reads its ink width, "
                         f"{reading} px.")
    d.style(BASE_CSS)

    by0, by1 = 16, 44  # beam
    tip = 156  # jaw tips
    open_x = 1000.0
    travel = open_x - x1
    r_roll = 9.0

    # ---- intro: a hand flicks the slider shut, it hits the part and rebounds outward
    t0 = 0.35
    # peak speed of IMPACT is 2.727 x average; keep it at 2900 px/s or below
    t_slide = 2.7273 * travel / 2900
    v_hit = 0.2 * travel / t_slide  # IMPACT ends with slope 0.2
    a_thumb = 1250.0  # the thumb keeps pushing toward the part
    intro_end = t0 + t_slide + 0.4

    def tx_(v):
        return f"transform:translateX({num(v)}px)"

    def rot_(v):
        return f"transform:rotate({-v / r_roll * 180 / math.pi:.2f}deg)"

    def intro(prop):
        bf, _ = bounce_frames(t_slide, v_hit, 0.47, a_thumb, prop)
        frames = [(0, prop(travel), IMPACT)] + bf
        return frames

    t_contact_a = t0 + t_slide
    ia = intro(tx_)
    span_a = ia[-1][0]
    d.style(keyframes("sa", span_a, ia) + f".sa{{animation:sa {span_a:.3f}s linear {t0}s both}}")
    d.style(keyframes("ra", span_a, intro(rot_)) + f".ra{{animation:ra {span_a:.3f}s linear {t0}s both}}")

    # ---- loop: hold, back off 60 px, re-close with a lighter flick
    P = CAL_PERIOD
    back, t_back, t_reclose = 60.0, 13.6, 14.4
    t_close = 0.16
    v_hit_b = 0.2 * back / t_close

    def loop(prop):
        bf, _ = bounce_frames(t_reclose + t_close, v_hit_b, 0.5, a_thumb, prop, min_h=0.3)
        return ([(0, prop(0), None), (t_back, prop(0), SMOOTH), (t_back + 0.5, prop(back), None),
                 (t_reclose, prop(back), IMPACT)] + bf + [(P, prop(0), None)])

    t_contact_b = t_reclose + t_close
    d.style(keyframes("sb", P, loop(tx_)) + f".sb{{animation:sb {P}s linear infinite}}")
    d.style(keyframes("rb", P, loop(rot_)) + f".rb{{animation:rb {P}s linear infinite}}")
    d.style(".ra,.rb{transform-box:fill-box;transform-origin:center}")

    # LCD: value appears at the exact contact, returns to dashes while the jaw backs off
    d.style(f"@keyframes va{{from{{opacity:0}}to{{opacity:1}}}}.va{{animation:va 1ms linear {t_contact_a:.3f}s both}}"
            + keyframes("vb", P, [(0, "opacity:1", None), (t_back, "opacity:0", None),
                                  (t_contact_b, "opacity:1", None), (P, "opacity:1", None)])
            + f".vb{{animation:vb {P}s step-end infinite}}")
    # contact flash on both faces, also on the exact contact
    d.style(f"@keyframes ha{{from{{opacity:1}}to{{opacity:0}}}}"
            f".ha{{opacity:0;animation:ha .5s cubic-bezier(.3,0,.6,1) {t_contact_a:.3f}s forwards}}"
            + keyframes("hb", P, [(0, "opacity:0", None), (t_contact_b, "opacity:0", None),
                                  (t_contact_b + 0.001, "opacity:1", "cubic-bezier(.3,0,.6,1)"),
                                  (t_contact_b + 0.5, "opacity:0", None), (P, "opacity:0", None)])
            + f".hb{{opacity:0;animation:hb {P}s linear infinite}}")

    # ---- beam with main scale: zero at the fixed face, 5 px divisions
    d.add(rect(2, by0, W - 4, by1 - by0, 3, fill=c["beam"], stroke=c["edge"], stroke_width=1))
    ticks = []
    n = 0
    while X0 + n * 5 <= W - 8:
        x = X0 + n * 5
        ln = 11 if n % 10 == 0 else 7.5 if n % 5 == 0 else 4.5
        ticks.append(f"M{num(x)} {by1}V{num(by1 - ln)}")
        n += 1
    d.add(f'<path d="{"".join(ticks)}" stroke="{c["tick"]}" stroke-width="1"/>')

    # fixed jaw: flat face on x0 down to the tip, tapered back
    d.add(f'<path d="M2.5 {by1} H{num(x0 - 0.5)} V{tip} L2.5 {tip - 40} Z" fill="{c["blade"]}" '
          f'stroke="{c["edge"]}" stroke-width="1" stroke-linejoin="round"/>')

    # the object being measured
    d.add(d.text(title, tx, base, size, DISP, fill=TEXT))

    def flash(x, ys, cls, side):
        y0, y1 = min(ys) - 7, max(ys) + 7
        xx = x - 1.5 if side < 0 else x + 1.5
        return (f'<g class="{cls}"><path d="M{num(xx)} {num(y0)}V{num(y1)}" stroke="{VOLT}" stroke-width="3" '
                f'stroke-linecap="round"/></g>')

    d.add(flash(x0, near0, "ha", -1), flash(x0, near0, "hb", -1))

    # ---- the slider, drawn at the closed position (hx = moving face)
    hx = x1
    HW = 196
    blade = (f'<path d="M{num(hx + 0.5)} {by1} H{num(hx + 18)} V{tip - 40} L{num(hx + 0.5)} {tip} Z" '
             f'fill="{c["blade"]}" stroke="{c["edge"]}" stroke-width="1" stroke-linejoin="round"/>')
    # housing wraps the beam; a notch on the left exposes the main scale above the vernier plate
    nx = hx + 58
    housing = (f'<path d="M{num(hx + 0.5)} 6.5 H{num(hx + HW - 6)} q6 0 6 6 V52 q0 6 -6 6 H{num(hx + 0.5)} '
               f'V{by1} H{num(nx)} V30 H{num(hx + 0.5)} Z" fill="{c["body"]}" stroke="{c["edge"]}" '
               f'stroke-width="1" stroke-linejoin="round"/>')
    # vernier: 10 divisions over 9 main divisions (least count 0.5 px), zero on the jaw face
    vt = "".join(f"M{num(hx + i * 4.5)} {by1}V{by1 + (8 if i % 5 == 0 else 5)}" for i in range(11))
    housing += f'<path d="{vt}" stroke="{c["tick"]}" stroke-width="1"/>'
    # LCD
    lx, ly, lw, lh = hx + 98, 12, 90, 28
    housing += rect(lx, ly, lw, lh, 4, fill=c["lcd"], stroke=c["lcdedge"], stroke_width=1)
    dig = 18
    dbase = ly + lh / 2 + MONOB.cap * dig / MONOB.upm / 2
    housing += d.text("---.--", lx + lw / 2, dbase, dig, MONOB, fill=LIME, anchor="middle")
    housing += (f'<g class="va"><g class="vb">{rect(lx + 3, ly + 3, lw - 6, lh - 6, 2, fill=c["lcd"])}'
                f'{d.text(reading, lx + lw / 2, dbase, dig, MONOB, fill=LIME, anchor="middle")}</g></g>')
    # thumb roller under the beam, rolling on its lower face
    rx, ry = hx + 76, by1 + r_roll
    housing += rect(rx - r_roll - 3, by1, 2 * r_roll + 6, 14, 2, fill=c["slot"])
    roller = (f'<g transform="translate({num(rx)} {num(ry)})"><g class="ra"><g class="rb">'
              f'<circle r="{num(r_roll - 1)}" fill="{c["blade"]}"/>'
              f'<circle r="{num(r_roll - 1.2)}" fill="none" stroke="{c["knurl"]}" stroke-width="2.4" '
              f'pathLength="48" stroke-dasharray="1 1"/>'
              f'<circle r="2.6" fill="{c["hub"]}"/></g></g></g>')
    d.add(f'<g class="sa"><g class="sb">{blade}{housing}{roller}'
          f'{flash(hx, near1, "ha", 1)}{flash(hx, near1, "hb", 1)}</g></g>')
    save(f"section-{slug}.svg", d)


# ---------------------------------------------------------------------------
# Buttons: keycaps that get pressed now and then and return against a stop
# ---------------------------------------------------------------------------
KEY = {
    "dark": dict(face=PANEL2, stroke=LINE2, base="#07080A", base_stroke=LINE),
    "light": dict(face="#FBFAF7", stroke="#BDB6A8", base="#D3CCBE", base_stroke="#ADA595"),
}[THEME]


def icon(kind: str, x: float, y: float, color: str, knock: str) -> str:
    if kind == "down":
        return (f'<path d="M{x} {y-6} V{y+6} M{x-5} {y+1} L{x} {y+6} L{x+5} {y+1}" fill="none" stroke="{color}" '
                f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    if kind == "ne":
        return arrow_ne(x - 5.5, y - 5.5, 11, color, 2)
    if kind == "linkedin":
        return (rect(x - 9, y - 9, 18, 18, 4, fill=color)
                + f'<rect x="{x-5.5}" y="{y-1.5}" width="2.6" height="7" fill="{knock}"/>'
                + f'<circle cx="{x-4.2}" cy="{y-4.6}" r="1.5" fill="{knock}"/>'
                + f'<path d="M{x-1} {y+5.5} V{y-1.5} h2.4 v1.2 q1 -1.5 2.8 -1.5 q2.6 0 2.6 3 v4.3 h-2.6 v-3.8 '
                  f'q0 -1.4 -1.2 -1.4 q-1.4 0 -1.4 1.6 v3.6 Z" fill="{knock}"/>')
    if kind == "mail":
        return (rect(x - 9.5, y - 7, 19, 14, 3, fill="none", stroke=color, stroke_width=1.8)
                + f'<path d="M{x-8} {y-5} L{x} {y+1} L{x+8} {y-5}" fill="none" stroke="{color}" stroke-width="1.8" '
                  f'stroke-linejoin="round"/>')
    if kind == "instagram":
        return (rect(x - 9, y - 9, 18, 18, 5.5, fill="none", stroke=color, stroke_width=1.8)
                + f'<circle cx="{x}" cy="{y}" r="4.2" fill="none" stroke="{color}" stroke-width="1.8"/>'
                + f'<circle cx="{x+4.8}" cy="{y-4.8}" r="1.2" fill="{color}"/>')
    if kind == "play":
        return (f'<circle cx="{x}" cy="{y}" r="9" fill="{color}"/>'
                f'<path d="M{x-2.5} {y-4} L{x+4} {y} L{x-2.5} {y+4} Z" fill="{knock}"/>')
    if kind == "code":
        return (f'<path d="M{x-4} {y-6} L{x-9} {y} L{x-4} {y+6} M{x+4} {y-6} L{x+9} {y} L{x+4} {y+6}" fill="none" '
                f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    if kind == "paper":
        return (f'<path d="M{x-7} {y-9} H{x+3} L{x+7} {y-5} V{y+9} H{x-7} Z" fill="none" stroke="{color}" '
                f'stroke-width="1.8" stroke-linejoin="round"/>'
                + f'<path d="M{x-3.5} {y-1} H{x+3.5} M{x-3.5} {y+3} H{x+3.5}" stroke="{color}" stroke-width="1.6" '
                  f'stroke-linecap="round"/>')
    raise ValueError(kind)


def press_keyframes(period: float, at: float, depth: float = 4.0) -> str:
    """One keystroke per period: the finger drives the cap down, holds it on the
    bottom, lets go; the spring throws it up against the top stop in 70 ms, it
    rebounds 0.8 px and is back at rest 110 ms after the hit."""
    def y(v):
        return f"transform:translateY({num(v)}px)"
    t_hit = at + 0.07 + 0.13 + 0.07
    frames = [
        (0, y(0), None),
        (at, y(0), "cubic-bezier(.5,0,.75,0)"),  # finger accelerates the cap down
        (at + 0.07, y(depth), None),  # bottomed out
        (at + 0.20, y(depth), "cubic-bezier(.36,0,.6,.37)"),  # released: spring force falls as it extends
        (t_hit, y(0), RISE),  # hits the top stop at speed
        (t_hit + 0.035, y(0.8), SMOOTH),  # rebound
        (t_hit + 0.11, y(0), None),  # settled
        (period, y(0), None),
    ]
    return keyframes("press", period, frames)


def button(name: str, label: str, lead: str, trail: str, period: float, at: float, prefix: str | None = None) -> None:
    H = 48
    face_h = 42
    k = KEY
    lw = MONOB.width(label, 13)
    pw = MONO.width(prefix, 13) + 8 if prefix else 0
    lead_w = 22 if lead else 0
    W = 18 + lead_w + (10 if lead else 0) + pw + lw + 14 + 14 + 16
    d = Doc(W, H, label, f"Button: {label}")
    d.style(press_keyframes(period, at) + f".press{{animation:press {period}s linear infinite}}")
    # the skirt under the cap: visible as a darker edge until the cap is pressed down onto it
    d.add(rect(1, 5, W - 2, face_h, face_h / 2, fill=k["base"], stroke=k["base_stroke"], stroke_width=1))
    g = rect(1, 1, W - 2, face_h, face_h / 2, fill=k["face"], stroke=k["stroke"], stroke_width=1.2)
    cy = 1 + face_h / 2
    x = 18
    if lead:
        g += icon(lead, x + 11, cy, VOLT, k["face"])
        x += lead_w + 10
    if prefix:
        g += d.text(prefix, x, cy + 4.6, 13, MONO, fill=VOLT_TEXT)
        x += pw
    g += d.text(label, x, cy + 4.6, 13, MONOB, fill=TEXT)
    x += lw + 14
    g += icon(trail, x + 7, cy, MUTED, k["face"])
    d.add(f'<g class="press">{g}</g>')
    save(f"btn-{name}.svg", d)


# ---------------------------------------------------------------------------
# Odometer strip: four counters, each on a real scale
# ---------------------------------------------------------------------------
ODO_PERIOD = 18.0
DRUM_VPEAK = 2400.0  # px/s; keeps the drum under half a digit per 60 Hz frame
SETTLE_T = duration(SETTLE)
SETTLE_VK = 4.08  # peak speed of the SETTLE step response, in travel per natural duration


def detent_frames(t: float, frm: float, to: float, over: float, prop):
    """motion.detent_keyframes as a segment of a longer timeline: a critically damped
    approach, a fixed overshoot in px past the detent and a short return."""
    travel = abs(to - frm)
    ta = max(0.45, SETTLE_VK * travel / DRUM_VPEAK)
    D = ta / 0.82
    s = 1 if to >= frm else -1
    return [(t, prop(frm), spring_tf(SETTLE)),
            (t + 0.82 * D, prop(to + s * over), "cubic-bezier(.3,0,.3,1)"),
            (t + 0.92 * D, prop(to - s * over * 0.2), None),
            (t + D, prop(to), None)], t + D


def odometer() -> None:
    W, H = 1200, 232
    with open(os.path.join(HERE, "data", "stats.json"), encoding="utf-8") as f:
        data = json.load(f)
    weeks = [w["commits"] for w in data["weeks"]]
    commits = sum(weeks)
    first = data["weeks"][0]["week"]
    last = data["weeks"][-1]["week"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def mlabel(iso):
        y, m, _ = iso.split("-")
        return f"{months[int(m) - 1]} {y}"

    models = [("LSTM", 43.9), ("CNN", 72.2), ("BiLSTM", 73.5), ("CNN + BiLSTM", 75.9)]
    d = Doc(W, H, f"GPA 3.63 of 4.00, thesis accuracy 75.9%, 3 of 12 builds in production, {commits} commits in 52 weeks",
            f"Four counters. GPA 3.63 on a 0 to 4.00 scale. Thesis accuracy 75.9% for the CNN + BiLSTM hybrid, "
            f"against BiLSTM 73.5%, CNN 72.2% and LSTM 43.9%. 3 of the 12 builds on this page are in production. "
            f"{commits} commits in the last 52 weeks.")
    d.style(BASE_CSS)
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))

    widths = [292, 316, 292, 300]  # the accuracy tile carries the longest label and the densest scale
    lefts = [sum(widths[:i]) for i in range(4)]
    pad = 36
    size = 72
    L = 86  # drum row pitch
    base = 94
    cap = DISP.cap * size / DISP.upm
    rule_y = 140
    ann_y = 168
    lab_y = 202
    grad = DIM  # graduations and empty slots: strokes, never text

    tiles = [
        ("3.63", "/ 4.00", "GPA, computer science"),
        ("75.9", "%", "Thesis accuracy, CNN + BiLSTM"),
        ("3", "of 12", "Builds in production"),
        (str(commits), "", "Commits, last 52 weeks"),
    ]
    css = []
    for ci, (val, unit, label) in enumerate(tiles):
        x0 = lefts[ci] + pad
        cw = widths[ci] - 2 * pad
        if ci:
            d.add(f'<line x1="{num(lefts[ci])}" y1="30" x2="{num(lefts[ci])}" y2="{H - 30}" stroke="{LINE}"/>')
        # -- the counter
        x = x0
        drums = []
        di = 0
        for ch in val:
            w = DISP.width(ch, size)
            if ch.isdigit():
                dg = int(ch)
                rows = "".join(d.text(str(k % 10), x + w / 2, base + (k - dg) * L, size, DISP, fill=TEXT,
                                      anchor="middle") for k in range(0, dg + 12))
                name = f"d{ci}{di}"

                def ty(v):
                    return f"transform:translateY({num(v)}px)"
                t_in = 0.5 + ci * 0.18 + di * 0.07
                fa, ea = detent_frames(0, dg * L, 0, 7, ty)
                css.append(keyframes(f"{name}a", ea, fa) + f".{name}a{{animation:{name}a {ea:.3f}s linear {t_in:.2f}s both}}")
                t_spin = 15.2 + ci * 0.18 + di * 0.07
                fb, eb = detent_frames(t_spin, 0, -10 * L, 7, ty)
                assert eb < ODO_PERIOD - 0.05, eb
                fb = [(0, ty(0), None)] + fb + [(ODO_PERIOD, ty(-10 * L), None)]
                css.append(keyframes(f"{name}b", ODO_PERIOD, fb) + f".{name}b{{animation:{name}b {ODO_PERIOD}s linear infinite}}")
                drums.append(f'<g class="{name}a"><g class="{name}b">{rows}</g></g>')
                di += 1
            else:
                drums.append(d.text(ch, x, base, size, DISP, fill=TEXT))
            x += w
        # the slot is exactly the figure height plus the detent travel, so a rolling drum
        # never spills into the labels around it
        d.defs.append(f'<clipPath id="w{ci}"><rect x="{num(x0 - 8)}" y="{num(base - cap - 8)}" '
                      f'width="{num(x - x0 + 16)}" height="{num(cap + 16)}"/></clipPath>')
        d.add(f'<g clip-path="url(#w{ci})">{"".join(drums)}</g>')
        if unit == "%":
            d.add(d.text("%", x + 3, base, 46, DISP, fill=TEXT))
        elif unit:
            d.add(d.text(unit, x + 10, base, 18, MONOB, fill=MUTED))
        d.add(d.text(label, x0, lab_y, 17, SEMI, fill=MUTED))

        # -- the scale: a rule, graduations below it, data marks standing on it
        def rule():
            return f'<path d="M{num(x0)} {rule_y}H{num(x0 + cw)}" stroke="{LINE2}" stroke-width="2"/>'

        def grads(xs):
            return f'<path d="{"".join(f"M{num(v)} {rule_y + 1}v6" for v in xs)}" stroke="{grad}" stroke-width="1.5"/>'

        def mark(x, h, color, w):
            return f'<path d="M{num(x)} {rule_y - 1}V{num(rule_y - h)}" stroke="{color}" stroke-width="{w}"/>'

        if ci == 0:  # GPA on a 0 to 4.00 rule, graduated every 1.00
            sx = lambda v: x0 + v / 4 * cw  # noqa: E731
            g = rule() + grads([sx(i) for i in range(5)]) + mark(sx(3.63), 16, VOLT, 4)
            for i in range(5):
                anchor = "start" if i == 0 else "end" if i == 4 else "middle"
                g += d.text(str(i), sx(i) + (-1 if i == 0 else 1 if i == 4 else 0), ann_y, 16, MONO, fill=MUTED,
                            anchor=anchor)
            d.add(g)
        elif ci == 1:  # accuracy on 40 to 80%, one mark per model, the hybrid lit
            sx = lambda v: x0 + (v - 40) / 40 * cw  # noqa: E731
            g = rule() + grads([sx(v) for v in (40, 50, 60, 70, 80)])
            for nm, v in models:
                lit = nm == "CNN + BiLSTM"
                g += mark(sx(v), 16 if lit else 10, VOLT if lit else MUTED, 4 if lit else 2)
            g += d.text("LSTM", sx(43.9) - 9, rule_y - 21, 16, MONO, fill=MUTED)
            g += d.text("CNN, BiLSTM", sx(73.5) + 1, rule_y - 21, 16, MONO, fill=MUTED, anchor="end")
            g += d.text("40", x0 - 1, ann_y, 16, MONO, fill=MUTED)
            g += d.text("60", sx(60), ann_y, 16, MONO, fill=MUTED, anchor="middle")
            g += d.text("80%", x0 + cw + 1, ann_y, 16, MONO, fill=MUTED, anchor="end")
            d.add(g)
        elif ci == 2:  # 3 of 12 builds in production
            n, live = 12, 3
            gap = 5
            s = (cw - gap * (n - 1)) / n
            g = ""
            for i in range(n):
                xx = x0 + i * (s + gap)
                if i < live:
                    g += rect(xx, rule_y - s + 1, s, s, 2, fill=VOLT)
                else:
                    g += rect(xx + 0.75, rule_y - s + 1.75, s - 1.5, s - 1.5, 1.6, fill="none", stroke=grad,
                              stroke_width=1.5)
            g += d.text("1", x0 + s / 2, ann_y, 16, MONO, fill=MUTED, anchor="middle")
            g += d.text("12", x0 + cw - s / 2, ann_y, 16, MONO, fill=MUTED, anchor="middle")
            d.add(g)
        else:  # commits per week, 52 columns standing on the rule
            n = len(weeks)
            step = cw / n
            bw = max(1.5, step - 1.4)
            top = max(weeks)
            hmax = 34
            bars = []
            for i, v in enumerate(weeks):
                if v <= 0:
                    continue
                h = max(1.5, v / top * hmax)
                bars.append(f"M{num(x0 + i * step + bw / 2)} {rule_y - 1}v{num(-h)}")
            g = rule() + f'<path d="{"".join(bars)}" stroke="{VOLT}" stroke-width="{num(bw)}"/>'
            g += d.text(mlabel(first), x0 - 1, ann_y, 16, MONO, fill=MUTED)
            g += d.text(mlabel(last), x0 + cw + 1, ann_y, 16, MONO, fill=MUTED, anchor="end")
            d.add(g)
    d.style("".join(css))
    save("stats.svg", d)


# ---------------------------------------------------------------------------
# Footer: a rubber stamp marks a reply card, then a fresh card is laid down
# ---------------------------------------------------------------------------
STAMP_INK = "#C8481F"  # red stamp ink on paper, the same paper in both themes
WOOD = "#8E5D3A"
WOOD_HI = "#A9744C"
WOOD_DK = "#6E4529"
RUBBER = "#2B2624"


def skip_ink_underline(font: Font, s: str, size: float, x: float, base: float, uy: float, uw: float, gap: float):
    """Underline segments that break around descenders, like text-decoration-skip-ink."""
    width = font.width(s, size)
    cuts = []
    for g in ink_points(font, s, size, x, base):
        xs = [px for px, py in g if uy - uw / 2 - gap <= py <= uy + uw / 2 + gap]
        if xs:
            cuts.append((min(xs) - gap, max(xs) + gap))
    cuts.sort()
    segs, cur = [], x
    for a, b in cuts:
        if a > cur:
            segs.append((cur, a))
        cur = max(cur, b)
    if cur < x + width:
        segs.append((cur, x + width))
    return segs


def footer() -> None:
    W, H = 1200, 380
    P = 9.0
    email = "fatihaljabar@gmail.com"
    d = Doc(W, H, f"Open to remote opportunities. Email me at {email}.",
            f"A closing panel: open to remote opportunities, email me at {email}. A rubber stamp drops onto a "
            "reply card and marks it Available; a fresh card is laid down for the next one.")
    d.style(BASE_CSS)
    d.defs.append(f'<clipPath id="panel"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22"/></clipPath>')
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))
    d.add('<g clip-path="url(#panel)">')
    d.add(d.text("Open to remote", 48, 126, 88, DISP, fill=TEXT))
    d.add(d.text("opportunities.", 48, 212, 88, DISP, fill=VOLT if DARK else VOLT_TEXT))
    d.add(d.text("Email me.", 50, 272, 20, BODY, fill=MUTED))
    eb = 316
    d.add(d.text(email, 50, eb, 34, SEMI, fill=TEXT))
    uy = eb + 7
    for a, b in skip_ink_underline(SEMI, email, 34, 50, eb, uy, 2, 2.5):
        d.add(f'<path d="M{num(a)} {num(uy)}H{num(b)}" stroke="{VOLT}" stroke-width="2"/>')

    # ---- timeline (s)
    t_ant = 1.02  # anticipation: a short rise before the strike (seen in the shadow)
    t_shadow = t_ant - 0.22  # the stamp is brought over the card, still above the frame
    t_fall = t_ant + 0.12
    t_hit = t_fall + 0.22  # free fall from rest, y = t^2
    t_lift = t_hit + 0.045 + 0.09  # 45 ms squash, a short dwell, then lift
    t_gone = t_lift + 0.55
    t_out = P * 0.85  # the stamped card is pulled out of the panel
    t_swap = t_out + 0.42
    t_in = t_swap + 0.02  # a fresh card slides in from the right
    t_set = t_in + SETTLE_T

    # ---- reply card
    cx, cy = 1000, 196
    card = (rect(-150 + 3, -118 + 5, 300, 236, 6, fill="#000", opacity=".22" if DARK else ".07")
            + rect(-150, -118, 300, 236, 6, fill=PAPER, stroke="none" if DARK else "#D6D0C2", stroke_width=1))
    card += d.text("Reply card", -126, -78, 18, SEMI, fill=PENSOFT)
    card += f'<path d="M-126 -64H126" stroke="{PENSOFT}" stroke-width="1.5"/>'
    for i in range(5):
        y = -30 + i * 30
        card += f'<path d="M-126 {y}H126" stroke="{GRAPH2}" stroke-width="1"/>'

    # imprint with ink grain; axis-aligned on screen like the stamp that makes it
    ih = 60  # imprint height
    rnd = random.Random(21)
    grain = "".join(f'<circle cx="{rnd.uniform(-118,118):.1f}" cy="{rnd.uniform(-32,32):.1f}" '
                    f'r="{rnd.uniform(.6,1.9):.1f}" fill="#000"/>' for _ in range(140))
    d.defs.append(f'<mask id="ink" maskUnits="userSpaceOnUse" x="-130" y="-45" width="260" height="90">'
                  f'<rect x="-130" y="-45" width="260" height="90" fill="#fff"/>{grain}</mask>')
    imprint = (rect(-112, -ih / 2, 224, ih, 7, fill="none", stroke=STAMP_INK, stroke_width=3.5)
               + rect(-104, -ih / 2 + 8, 208, ih - 16, 4, fill="none", stroke=STAMP_INK, stroke_width=1.4)
               + d.text("AVAILABLE", 0, DISP.cap * 34 / DISP.upm / 2, 34, DISP, fill=STAMP_INK, anchor="middle"))
    iy = 40  # imprint centre in card space
    d.style(keyframes("ink", P, [(0, "opacity:0", None), (t_hit, "opacity:1", None), (t_swap, "opacity:0", None),
                                 (P, "opacity:0", None)])
            + f".ink{{opacity:.9;animation:ink {P}s step-end infinite}}")
    card += (f'<g transform="translate(0 {iy}) rotate(-3)"><g class="ink" opacity=".9">'
             f'<g mask="url(#ink)">{imprint}</g></g></g>')

    def tf(x, y, r):
        return f"transform:translate({num(x)}px,{num(y)}px) rotate({num(r)}deg)"
    d.style(keyframes("card", P, [
        (0, tf(0, 0, 0), None),
        (t_out, tf(0, 0, 0), "cubic-bezier(.5,0,.9,.4)"),
        (t_swap, tf(-30, 330, 7), None),
        (t_swap + 0.001, tf(380, -8, 4), None),
        (t_in, tf(380, -8, 4), spring_tf(SETTLE)),
        (t_set, tf(0, 0, 0), None),
        (P, tf(0, 0, 0), None),
    ]) + f".card{{animation:card {P}s linear infinite}}")
    d.add(f'<g transform="translate({cx} {cy}) rotate(3)"><g class="card">{card}</g></g>')

    # ---- the stamp in side elevation: turned wooden handle, metal ferrule, wooden mount, rubber.
    # We look down at the desk from the front, so the footprint lies behind the front edge of
    # the rubber: the rubber lands on the imprint's lower edge and the mount hides the rest.
    ix = cx - iy * math.sin(math.radians(3))
    iyc = cy + iy * math.cos(math.radians(3))
    sx, sy = ix, iyc + ih / 2 + 3.5  # stamp origin: bottom centre of the rubber
    mount = 64  # mount height; rubber + mount cover the imprint with margin to spare
    top = -8 - mount
    hb = top - 12  # handle base, above the ferrule
    assert 8 + mount > ih + 3.5 + 1.75 + 2, "the stamp body must hide the imprint at contact"
    stamp = (
        # handle: a turned knob, 60 wide and 70 tall
        f'<path d="M-13 {hb} V{hb - 22} C-13 {hb - 28} -30 {hb - 31} -30 {hb - 45} C-30 {hb - 61} -16 {hb - 70} 0 {hb - 70} '
        f'C16 {hb - 70} 30 {hb - 61} 30 {hb - 45} C30 {hb - 31} 13 {hb - 28} 13 {hb - 22} V{hb} Z" fill="{WOOD}"/>'
        f'<path d="M-22 {hb - 50} C-21 {hb - 59} -13 {hb - 65} -4 {hb - 66}" fill="none" stroke="{WOOD_HI}" '
        'stroke-width="4" stroke-linecap="round"/>'
        f'<path d="M7 {hb - 22} V{hb - 3}" stroke="{WOOD_DK}" stroke-width="4" stroke-linecap="round"/>'
        # ferrule
        + rect(-19, hb - 1, 38, 13, 2, fill=METAL, stroke=METAL_EDGE, stroke_width=1)
        + f'<path d="M-18 {hb + 5.5}H18" stroke="{METAL_EDGE}" stroke-width="1"/>'
        # mount: a block of wood with a little grain, and the rubber die under it
        + rect(-124, top, 248, mount + 2, 4, fill=WOOD)
        + f'<path d="M-121 {top + 2.5}H121" stroke="{WOOD_HI}" stroke-width="2" stroke-linecap="round"/>'
        + f'<path d="M-96 {top + 22} C-40 {top + 18} 10 {top + 27} 70 {top + 21} M-60 {top + 40} C0 {top + 36} 40 {top + 44} 104 {top + 38}" '
          f'fill="none" stroke="{WOOD_DK}" stroke-width="1.5" stroke-linecap="round" opacity=".55"/>'
        + f'<path d="M-124 -10.5H124" stroke="{WOOD_DK}" stroke-width="3"/>'
        + rect(-116, -9, 232, 9, 1.5, fill=RUBBER)
        + f'<path d="M-116 -1H116" stroke="{STAMP_INK}" stroke-width="2"/>'
    )
    park = -(sy + 4)  # rubber fully above the panel
    ant = park - 14

    def st(y, sy_=1.0):
        return f"transform:translateY({num(y)}px) scaleY({sy_})"
    d.style(keyframes("stamp", P, [
        (0, st(park), None),
        (t_ant, st(park), "cubic-bezier(.2,.6,.4,1)"),
        (t_fall, st(ant), FALL),
        (t_hit, st(0), "cubic-bezier(.2,.7,.4,1)"),
        (t_hit + 0.015, st(0, 0.98), "cubic-bezier(.3,0,.4,1)"),  # rubber and wood take the blow
        (t_hit + 0.045, st(0), None),
        (t_lift, st(0), "cubic-bezier(.3,0,.2,1)"),  # a hand lifts it, no spring
        (t_gone, st(park), None),
        (P, st(park), None),
    ]) + f".stamp{{transform:translateY({num(park)}px);transform-box:fill-box;transform-origin:50% 100%;"
         f"animation:stamp {P}s linear infinite}}")

    # its shadow on the card: faint and wide while high, tight and dark at contact
    def sh(o, s):
        return f"opacity:{o};transform:scale({s},1)"
    d.style(keyframes("shadow", P, [
        (0, sh(0, 1.2), None),
        (t_shadow, sh(0, 1.2), "ease-out"),
        (t_ant, sh(0.07, 1.14), "ease-out"),
        (t_fall, sh(0.055, 1.18), FALL),
        (t_hit, sh(0.2, 1.0), None),
        (t_lift, sh(0.2, 1.0), "cubic-bezier(.3,0,.2,1)"),
        (t_gone, sh(0, 1.2), None),
        (P, sh(0, 1.2), None),
    ]) + f".shadow{{opacity:0;transform-box:fill-box;transform-origin:center;animation:shadow {P}s linear infinite}}")
    d.add(f'<g transform="translate({num(sx)} {num(sy)})"><g class="shadow">'
          f'<ellipse cx="0" cy="-2" rx="126" ry="6" fill="#000"/></g></g>')
    d.add(f'<g transform="translate({num(sx)} {num(sy)})"><g class="stamp">{stamp}</g></g>')
    d.add("</g>")
    save("footer.svg", d)


# ---------------------------------------------------------------------------
NAV = [("nav-work", "Projects", "01 ", 8.3, 1.6), ("nav-stack", "Stack", "02 ", 9.1, 3.4),
       ("nav-thesis", "Thesis", "03 ", 9.7, 0.9), ("nav-certs", "Certifications", "04 ", 10.4, 2.5),
       ("nav-stats", "Activity", "05 ", 11.3, 4.2)]
SOCIAL = [("linkedin", "LinkedIn", "linkedin", 7.7, 2.2), ("email", "Email", "mail", 8.9, 4.6),
          ("instagram", "Instagram", "instagram", 10.1, 1.1)]
THESIS = [("demo", "Live demo", "play", 8.6, 1.4), ("source", "Source code", "code", 9.4, 3.7),
          ("article", "Article", "paper", 10.8, 2.6)]


def build_all() -> None:
    for slug, title in SECTIONS:
        section_header(slug, title)
    for name, label, prefix, period, at in NAV:
        button(name, label, "", "down", period, at, prefix=prefix)
    for name, label, lead, period, at in SOCIAL + THESIS:
        button(name, label, lead, "ne", period, at)
    odometer()
    footer()
