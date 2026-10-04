"""Certifications: six record sheets on a print line.

The six Dicoding Indonesia certificates hang the way a drafting room hangs fresh
prints: A5 sheets held by binder clips on two tensioned wires, filed in course
order. Each sheet carries a title block whose serial is the real credential ID.

Every 16 s a fingertip runs along each wire, left to right, and brushes the
bottom edge of each sheet. A sheet is a physical pendulum pinned where the clip
handle rests on the wire, so it swings in its own plane and dies out in air:

    theta'' = -wn^2 sin(theta) - 2 zeta wn theta' + tau(t)

wn comes from the sheet and clip geometry below, tau is a 40 ms half-sine push.
Nothing ever touches a neighbour (checked at build time), so nothing rebounds.
At rest, which is frame 0, the end of every swing and the reduced-motion frame,
all six sheets hang plumb and every line is readable.
"""

from __future__ import annotations

import math

from shapely.affinity import rotate as sh_rotate
from shapely.geometry import box

from theme import *  # noqa: F403
from ui import CAL

W, H = 1200, 690
PERIOD = 16.0

# A5 landscape at 1 px = 0.5966 mm, so 352 x 249 px is 210 x 148.6 mm
SW, SH = 352, 249
MM = 210.0 / SW
CENTRES = [212, 600, 988]
WIRES = [54, 374]
X_EYE_L, X_EYE_R = 96, 1180  # where each wire leaves the turnbuckle and the right eye
HANG = 30  # pivot (handle bend on the wire) to the top edge of the sheet, px

# Sheets in course order: the titles imply the front-end path, then back-end, then career.
CERTS = [
    ("NVP741O0WPR0", ["JavaScript Programming", "Basics"], ["OOP, functional programming, async"]),
    ("EYX4J9RROZDL", ["Front-End Web Development", "for Beginners"], ["DOM manipulation, events,", "web storage"]),
    ("EYX4J058OZDL", ["Front-End Web Development", "Fundamentals"], ["Web Components, module bundlers,", "async JS"]),
    ("N9ZOY1Y7DPG5", ["Becoming an Expert", "Front-End Web Developer"], ["PWA, accessibility,", "automation testing, CI/CD"]),
    ("2VX349OGVZYQ", ["Back-End Fundamentals", "with JavaScript"], ["RESTful APIs, Node.js, Hapi, AWS EC2"]),
    ("6RPNYN60QZ2M", ["Building a Career as", "a Software Developer"], ["Career paths, roles and the", "day-to-day of software work"]),
]
GROUP = ["Front-end path"] * 4 + ["Back-end", "Career"]
SQUARE_INK = {4: "#2A78D6", 5: "#C8481F"}  # paper-safe sky and coral for the two single sheets

# when the fingertip reaches each sheet: one hand speed along a wire, then a reach down to wire B
T_FIRST = 4.0
DELAYS = [0.0, 0.16, 0.32, 0.90, 1.06, 1.22]

DARK = THEME == "dark"
STEEL = CAL
CLIP = "#1A1C20"
CLIP_HI = "#3A3F48"
EDGE = None if DARK else "#D6D0C2"
SHADOW_OP = 0.24 if DARK else 0.08


# ----------------------------------------------------------------------------- physics
def natural_frequency() -> float:
    """Sheet of 250 g/m2 card plus a 25 mm binder clip, pinned HANG px above the sheet."""
    w, h = SW * MM / 1000, SH * MM / 1000  # m
    m_s = 0.250 * w * h  # kg
    m_c = 0.004
    a = HANG * MM / 1000
    d_s = a + h / 2
    d_c = a + 0.003
    inertia = m_s * ((w * w + h * h) / 12 + d_s * d_s) + m_c * d_c * d_c
    return math.sqrt(9.81 * (m_s * d_s + m_c * d_c) / inertia)


WN = natural_frequency()
ZETA = 0.15  # air drag on a flat card
PUSH = 0.04  # s, the fingertip's contact time
PEAK_DEG = 3.0


def swing(amp: float, t_end: float = 3.4, dt: float = 0.0005) -> list[tuple[float, float]]:
    """Angle in degrees after a half-sine push of peak amp rad/s^2, semi-implicit Euler."""
    th = om = 0.0
    out = []
    n = int(round(t_end / dt))
    for i in range(n + 1):
        t = i * dt
        out.append((t, math.degrees(th)))
        tau = amp * math.sin(math.pi * t / PUSH) if t <= PUSH else 0.0
        om += (-WN * WN * math.sin(th) - 2 * ZETA * WN * om + tau) * dt
        th += om * dt
    return out


def calibrated() -> list[tuple[float, float]]:
    """Scale the push so the first peak is exactly PEAK_DEG."""
    probe = swing(10.0)
    k = PEAK_DEG / max(a for _, a in probe)
    return swing(10.0 * k)


TRACE = calibrated()


def settle_time(trace, tol_px: float = 0.2) -> float:
    """First time after which the bottom corner never leaves plumb by more than tol_px."""
    reach = math.hypot(SW / 2, HANG + SH)
    last = 0.0
    for t, a in trace:
        if abs(math.radians(a)) * reach > tol_px:
            last = t
    return last


T_SETTLE = settle_time(TRACE)


def angle_at(t_local: float) -> float:
    """Angle of a sheet whose push starts at local time 0 (linear between samples)."""
    if t_local <= 0 or t_local >= T_SETTLE:
        return 0.0
    dt = TRACE[1][0]
    i = int(t_local / dt)
    (t0, a0), (t1, a1) = TRACE[i], TRACE[min(i + 1, len(TRACE) - 1)]
    return a0 + (a1 - a0) * (t_local - t0) / dt if t1 > t0 else a0


def keyframes() -> str:
    """One shared 16 s clock; each sheet runs it with its own delay."""
    step = 0.02
    stops = [f"0%,{T_FIRST / PERIOD * 100:.3f}%{{transform:rotate(0deg)}}"]
    n = int(math.ceil(T_SETTLE / step))
    for i in range(1, n + 1):
        t = min(i * step, T_SETTLE)
        a = angle_at(t) if t < T_SETTLE else 0.0
        stops.append(f"{(T_FIRST + t) / PERIOD * 100:.3f}%{{transform:rotate({-a:.3f}deg)}}")
    stops.append("100%{transform:rotate(0deg)}")
    css = "@keyframes sw{" + "".join(stops) + "}"
    css += f".sw{{animation:sw {PERIOD}s linear infinite}}"
    css += "".join(f".d{i}{{animation-delay:{d}s}}" for i, d in enumerate(DELAYS) if d)
    return css


# ----------------------------------------------------------------------------- geometry
def wire_dips() -> list[float]:
    """Funicular polygon of three equal clip loads; the largest dip is 2.0 px."""
    span = X_EYE_R - X_EYE_L

    def moment(x):  # simply supported span, unit loads at the clip positions
        m = 0.0
        for c in CENTRES:
            a, b = c - X_EYE_L, X_EYE_R - c
            xx = x - X_EYE_L
            m += (b * xx / span) if xx <= a else (a * (span - xx) / span)
        return m
    ms = [moment(c) for c in CENTRES]
    k = 2.0 / max(ms)
    return [m * k for m in ms]


DIPS = wire_dips()


def pivots() -> list[tuple[float, float]]:
    return [(CENTRES[i % 3], WIRES[i // 3] + DIPS[i % 3]) for i in range(6)]


def check_clearances() -> None:
    """Sample the whole loop; adjacent sheets, the wire below and the panel stay clear."""
    pv = pivots()
    worst_gap, worst_low = 1e9, 0.0
    for k in range(0, int(PERIOD / 0.01)):
        t = k * 0.01
        polys = []
        for i, (px, py) in enumerate(pv):
            a = -angle_at(t - T_FIRST - DELAYS[i])
            sheet = box(px - SW / 2, py + HANG, px + SW / 2, py + HANG + SH)
            polys.append(sh_rotate(sheet, a, origin=(px, py)))
        for row in (0, 1):
            for j in range(2):
                gap = polys[row * 3 + j].distance(polys[row * 3 + j + 1])
                worst_gap = min(worst_gap, gap)
        for i in range(3):
            worst_low = max(worst_low, polys[i].bounds[3])
        for i in range(3, 6):
            assert polys[i].bounds[3] < H - 16, ("panel", t, i)
    assert worst_gap > 6, worst_gap
    assert worst_low < WIRES[1] - 20, worst_low  # wire A sheets never reach wire B's clips
    print(f"  certs: wn {WN:.2f} rad/s, T {2 * math.pi / WN:.3f} s, settles in {T_SETTLE:.2f} s, "
          f"closest neighbours {worst_gap:.1f} px, wire A sheets reach y {worst_low:.1f}")


# ----------------------------------------------------------------------------- drawing
def hardware(y: float) -> str:
    """Wall plates, eye rings, a turnbuckle on the left and a ferrule at each end."""
    c = STEEL
    s = ""
    # left: plate, eye, turnbuckle, eye, ferrule
    s += rect(8, y - 13, 7, 26, 1.5, fill=c["beam"], stroke=c["edge"], stroke_width=1)
    s += f'<circle cx="24" cy="{y}" r="5" fill="none" stroke="{c["knurl"]}" stroke-width="2"/>'
    s += f'<path d="M29 {y}H34M76 {y}H91" stroke="{c["tick"]}" stroke-width="2"/>'
    s += rect(34, y - 7, 8, 14, 1.5, fill=c["body"], stroke=c["edge"], stroke_width=1)
    s += rect(68, y - 7, 8, 14, 1.5, fill=c["body"], stroke=c["edge"], stroke_width=1)
    s += f'<path d="M42 {y - 5}H68M42 {y + 5}H68" stroke="{c["knurl"]}" stroke-width="2.2"/>'
    threads = "".join(f"M{x} {y - 2.2}V{y + 2.2}" for x in (46, 49, 52, 58, 61, 64))
    s += f'<path d="M42 {y}H68" stroke="{c["tick"]}" stroke-width="1.4"/>'
    s += f'<path d="{threads}" stroke="{c["edge"]}" stroke-width="1"/>'
    s += f'<circle cx="{X_EYE_L}" cy="{y}" r="4.5" fill="none" stroke="{c["knurl"]}" stroke-width="2"/>'
    s += rect(102, y - 3, 12, 6, 1.2, fill=c["body"], stroke=c["edge"], stroke_width=1)
    # right: ferrule, eye, plate
    s += rect(1162, y - 3, 12, 6, 1.2, fill=c["body"], stroke=c["edge"], stroke_width=1)
    s += f'<circle cx="{X_EYE_R}" cy="{y}" r="4.5" fill="none" stroke="{c["knurl"]}" stroke-width="2"/>'
    s += rect(1185, y - 13, 7, 26, 1.5, fill=c["beam"], stroke=c["edge"], stroke_width=1)
    return s


def wire_path(y: float, dx: float = 0, dy: float = 0) -> str:
    pts = [(X_EYE_L + 4.5, y)] + [(c, y + dip) for c, dip in zip(CENTRES, DIPS)] + [(X_EYE_R - 4.5, y)]
    return "M" + "L".join(f"{num(x + dx)} {num(yy + dy)}" for x, yy in pts)


def clip() -> str:
    """A 25 mm binder clip in front view; local origin is the pivot on the wire.

    The two wire handles are folded up together, so in front view they read as one
    loop whose arms leave the rolled top edge of the body and narrow to a bend that
    rests on the wire."""
    top = HANG  # sheet top
    by0, by1 = top - 5, top + 10  # the body grips the top 10 px of the sheet
    arm = f'M-17 {by0 + 1}L-7.5 3.2Q-7 -1.9 0 -1.9Q7 -1.9 7.5 3.2L17 {by0 + 1}'
    s = f'<path d="{arm}" fill="none" stroke="{STEEL["knurl"]}" stroke-width="1.8" stroke-linejoin="round" ' \
        f'stroke-linecap="round"/>'
    s += f'<path d="M-24 {by0 + 2}Q-24 {by0} -22 {by0}H22Q24 {by0} 24 {by0 + 2}V{by1 - 1.5}Q24 {by1} 22.5 {by1}' \
         f'H-22.5Q-24 {by1} -24 {by1 - 1.5}Z" fill="{CLIP}"/>'
    # the rolled edge that the handle ends pivot in, and the lip of the jaw
    s += f'<path d="M-22 {by0 + 1.6}H22" stroke="{CLIP_HI}" stroke-width="1.6"/>'
    s += f'<path d="M-17 {by0 + 1.6}h0.01M17 {by0 + 1.6}h0.01" stroke="{STEEL["knurl"]}" stroke-width="3.2" ' \
         f'stroke-linecap="round"/>'
    s += f'<path d="M-24 {by1 - 2.5}H24" stroke="{CLIP_HI}" stroke-width="0.8"/>'
    return s


def sheet(d: Doc, i: int) -> str:
    """The record sheet in pivot coordinates: origin on the wire, sheet top at y=HANG."""
    cred, title, topics = CERTS[i]
    x0, y0 = -SW / 2, HANG
    L = lambda v: x0 + v  # noqa: E731
    T = lambda v: y0 + v  # noqa: E731
    s = rect(x0, y0, SW, SH, 2, fill=PAPER, stroke=EDGE or "none", stroke_width=1)
    # graph paper above the title block, the same 12 px grid as the hero sheet
    grid = "".join(f"M{num(L(x))} {num(T(8))}V{num(T(184))}" for x in range(20, SW - 8, 12))
    grid += "".join(f"M{num(L(8))} {num(T(y))}H{num(L(SW - 8))}" for y in range(20, 184, 12))
    s += f'<path d="{grid}" stroke="{GRAPH}" stroke-width="0.8"/>'
    s += rect(L(8), T(8), SW - 16, SH - 16, 0, fill="none", stroke=PENSOFT, stroke_width=1)

    # header: filing number, group and position on the path
    s += d.text(f"{i + 1:02d}", L(22), T(44), 18, MONOB, fill=PEN)
    if i < 4:
        sq_x = [267, 284, 301, 318]
        s += d.text(GROUP[i], L(257), T(44), 16, MONO, fill=PENSOFT, anchor="end")
        for k, sx in enumerate(sq_x):
            if k == i:
                s += rect(L(sx), T(33), 12, 12, 1.5, fill=LIME, stroke=PEN, stroke_width=1.2)
            else:
                s += rect(L(sx) + 0.6, T(33) + 0.6, 10.8, 10.8, 1.2, fill="none", stroke=PENSOFT, stroke_width=1.2)
    else:
        s += d.text(GROUP[i], L(310), T(44), 16, MONO, fill=PENSOFT, anchor="end")
        s += rect(L(318), T(33), 12, 12, 1.5, fill=SQUARE_INK[i], stroke=PEN, stroke_width=1.2)

    for k, ln in enumerate(title):
        assert SEMI.width(ln, 22) <= 308, ln
        s += d.text(ln, L(22), T(86 + 27 * k), 22, SEMI, fill=PEN)
    for k, ln in enumerate(topics):
        assert BODY.width(ln, 17) <= 308, ln
        s += d.text(ln, L(22), T(146 + 22 * k), 17, BODY, fill=PENSOFT)

    # title block: issuer and the credential, which is the sheet's serial
    s += f'<path d="M{num(L(8))} {num(T(184))}H{num(L(SW - 8))}" stroke="{PEN}" stroke-width="1.2"/>'
    s += f'<path d="M{num(L(8))} {num(T(212.5))}H{num(L(SW - 8))}" stroke="{GRAPH2}" stroke-width="1"/>'
    s += d.text("Issued by", L(22), T(204), 16, MONO, fill=PENSOFT)
    s += d.text("Dicoding Indonesia", L(330), T(204), 16, SEMI, fill=PEN, anchor="end")
    s += d.text("Credential", L(22), T(233), 16, MONO, fill=PENSOFT)
    s += d.text(cred, L(330), T(233), 17, MONOB, fill=PEN, anchor="end")
    return s + clip()


def build() -> None:
    check_clearances()
    titles = [" ".join(t) for _, t, _ in CERTS]
    desc = ("Six certificates from Dicoding Indonesia hang from binder clips on two wires, filed in course order. "
            + " ".join(f"{i + 1:02d}: {titles[i]}, covering {' '.join(CERTS[i][2])}, credential {CERTS[i][0]}."
                       for i in range(6))
            + " Every 16 seconds a fingertip runs along each wire and the sheets swing like pendulums, "
              "then hang still.")
    d = Doc(W, H, "Certifications: six Dicoding Indonesia certificates on a print line", desc)
    d.style(keyframes())
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))

    pv = pivots()
    # shadows first: the wires' and each sheet's, the sheet shadow swinging with its sheet
    shadow = "#000"
    for y in WIRES:
        d.add(f'<path d="{wire_path(y, 4, 6)}" fill="none" stroke="{shadow}" stroke-opacity="{SHADOW_OP}" '
              f'stroke-width="1.6"/>')
    for i, (px, py) in enumerate(pv):
        cls = f"sw d{i}" if DELAYS[i] else "sw"
        d.add(f'<g transform="translate({num(px + 4)} {num(py + 6)})"><g class="{cls}">'
              f'{rect(-SW / 2, HANG, SW, SH, 2, fill=shadow, fill_opacity=SHADOW_OP)}</g></g>')

    for y in WIRES:
        d.add(hardware(y))
        d.add(f'<path d="{wire_path(y)}" fill="none" stroke="{STEEL["tick"]}" stroke-width="1.6" '
              f'stroke-linejoin="round"/>')

    for i, (px, py) in enumerate(pv):
        cls = f"sw d{i}" if DELAYS[i] else "sw"
        d.add(f'<g transform="translate({num(px)} {num(py)})"><g class="{cls}">{sheet(d, i)}</g></g>')

    save("certs.svg", d)
