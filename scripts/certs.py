"""Certifications: six record sheets on a print line.

The six Dicoding Indonesia certificates hang the way a drafting room hangs fresh
prints: A5 sheets held by binder clips on two tensioned wires, four front-end
courses on the top wire, then back-end and career. Each sheet carries a title
block whose serial is the real credential ID.

Every 16 s a drafting pencil is drawn along the bottom edges of the top row,
left to right, then back along the bottom row, right to left. While it slides
across a sheet, kinetic friction pushes that sheet with a constant force, so a
sheet the pencil crosses slowly gets a longer push than one it crosses fast.
The pencil follows a minimum-jerk stroke, like a hand.

A sheet is a physical pendulum pinned where the clip handle rests on the wire.
It swings in its own plane, so it moves edge-on through the air and the loss
that matters is Coulomb friction where the handle rubs on the wire:

    theta'' = -wn^2 sin(theta) - 2 zeta_air wn theta' - tau_f sign(theta') + tau(t)

That gives a linear decay envelope and a real stop. Nothing ever touches a
neighbour, the wire below or the panel (checked at build time). At rest, which
is frame 0, the end of every swing and the reduced-motion frame, all six sheets
hang plumb and every line is readable.
"""

from __future__ import annotations

import math

from shapely.affinity import rotate as sh_rotate
from shapely.geometry import box

from theme import *  # noqa: F403
from ui import CAL

W, H = 1200, 690
PERIOD = 16.0
STEP = 0.025  # keyframe sampling, s

# A5 landscape at 1 px = 0.5966 mm, so 352 x 249 px is 210 x 148.6 mm
SW, SH = 352, 249
MM = 210.0 / SW
CENTRES = [212, 600, 988]
WIRES = [54, 374]
X_EYE_L, X_EYE_R = 96, 1180  # the eyes the wire is spliced to, left and right
HANG = 30  # pivot (handle bend on the wire) to the top edge of the sheet, px
SAG = 7.0  # largest wire dip under the three clips, px

# The courses with the topics the original README lists for them; the career
# course has none listed, so its sheet shows none.
CERTS = [
    ("NVP741O0WPR0", ["JavaScript Programming", "Basics"], ["OOP, functional programming, async"]),
    ("EYX4J9RROZDL", ["Front-End Web Development", "for Beginners"], ["DOM manipulation, events,", "web storage"]),
    ("EYX4J058OZDL", ["Front-End Web Development", "Fundamentals"], ["Web Components, module bundlers,", "async JS"]),
    ("N9ZOY1Y7DPG5", ["Becoming an Expert", "Front-End Web Developer"], ["PWA, accessibility,", "automation testing, CI/CD"]),
    ("2VX349OGVZYQ", ["Back-End Fundamentals", "with JavaScript"], ["RESTful APIs, Node.js, Hapi, AWS EC2"]),
    ("6RPNYN60QZ2M", ["Building a Career as", "a Software Developer"], []),
]
GROUP = ["Front-end"] * 4 + ["Back-end", "Career"]
CHIP = ["lime"] * 4 + ["#2A78D6", "#C8481F"]  # paper-safe sky and coral for the single sheets

DARK = THEME == "dark"
STEEL = CAL
CLIP = "#1A1C20"
CLIP_HI = "#3A3F48"
CLIP_EDGE = STEEL["edge"] if DARK else None
# In light mode the wall is pale, so the paper is lifted above it to stay the brightest surface.
SHEET = PAPER if DARK else "#FFFDF8"
EDGE = None if DARK else "#CBC4B4"
SHADOW_OP = 0.30 if DARK else 0.12
LIGHT_DY = 6  # one light from straight above, as on the keycaps and the footer stamp

# the pencil: hex body, wood cone, graphite point, end dipped in the page's lime
PENCIL_L = 260  # a sharpened drafting pencil, 155 mm by 7 mm at this scale
PENCIL_BODY = ("#3A3F48", "#2B2F36", "#22262C")  # top, middle, bottom facet
WOOD, WOOD_SIDE = "#D9BC8C", "#C4A577"
GRAPHITE = "#2A2B2E"


# ----------------------------------------------------------------------------- geometry
def wire_dips() -> list[float]:
    """Funicular polygon of three equal clip loads on the span between the eyes."""
    span = X_EYE_R - X_EYE_L

    def moment(x):  # simply supported span, unit loads at the clip positions
        m = 0.0
        for c in CENTRES:
            a = c - X_EYE_L
            xx = x - X_EYE_L
            m += ((span - a) * xx / span) if xx <= a else (a * (span - xx) / span)
        return m
    ms = [moment(c) for c in CENTRES]
    k = SAG / max(ms)
    return [m * k for m in ms]


DIPS = wire_dips()


def pivots() -> list[tuple[float, float]]:
    return [(CENTRES[i % 3], WIRES[i // 3] + DIPS[i % 3]) for i in range(6)]


def bottom(i: int) -> float:
    return pivots()[i][1] + HANG + SH


# ----------------------------------------------------------------------------- the pencil stroke
T_A = 4.0          # stroke along the top row starts
D_STROKE = 1.05    # s per row
D_DROP = 0.28      # s to move down to the bottom row, out of sight at the right
X_OFF_L = -12.0               # tip x with the whole pencil left of the panel
X_OFF_R = W + PENCIL_L + 12.0  # tip x with the whole pencil right of the panel
Y_ROW = [sum(bottom(r * 3 + k) for k in range(3)) / 3 - 4 for r in (0, 1)]  # pencil axis, over the bottom margin


def min_jerk(s: float) -> float:
    s = min(1.0, max(0.0, s))
    return s * s * s * (10 - 15 * s + 6 * s * s)


def pencil_at(t: float) -> tuple[float, float]:
    """Tip position at loop time t."""
    t_b0 = T_A + D_STROKE + D_DROP
    if t < T_A:
        return X_OFF_L, Y_ROW[0]
    if t < T_A + D_STROKE:
        return X_OFF_L + (X_OFF_R - X_OFF_L) * min_jerk((t - T_A) / D_STROKE), Y_ROW[0]
    if t < t_b0:
        u = min_jerk((t - T_A - D_STROKE) / D_DROP)
        return X_OFF_R, Y_ROW[0] + (Y_ROW[1] - Y_ROW[0]) * u
    if t < t_b0 + D_STROKE:
        return X_OFF_R + (X_OFF_L - X_OFF_R) * min_jerk((t - t_b0) / D_STROKE), Y_ROW[1]
    return X_OFF_L, Y_ROW[1]


def contact(i: int) -> tuple[float, float, int]:
    """When the pencil lies across sheet i (start, end) and which way it drags it."""
    c = CENTRES[i % 3]
    lo, hi = c - SW / 2, c + SW / 2 + PENCIL_L  # tip range with any overlap
    row = i // 3
    t0 = T_A if row == 0 else T_A + D_STROKE + D_DROP
    times = [t0 + k * 0.0005 for k in range(int(D_STROKE / 0.0005) + 1)]
    inside = [t for t in times if lo < pencil_at(t)[0] < hi]
    return inside[0], inside[-1], (1 if row == 0 else -1)


# ----------------------------------------------------------------------------- physics
def sheet_constants() -> tuple[float, float]:
    """Natural frequency and Coulomb pivot torque per unit inertia, from real parts.

    Sheet: 250 g/m2 card, 210 x 148.6 mm. Clip: 25 mm binder clip, 4 g, its mass
    centre 3 mm below the sheet top. Pivot: HANG px above the sheet top. Friction:
    steel handle on a 1 mm steel wire, mu 0.3, acting at the wire radius."""
    w, h = SW * MM / 1000, SH * MM / 1000
    m_s, m_c = 0.250 * w * h, 0.004
    a = HANG * MM / 1000
    d_s, d_c = a + h / 2, a + 0.003
    inertia = m_s * ((w * w + h * h) / 12 + d_s * d_s) + m_c * d_c * d_c
    wn = math.sqrt(9.81 * (m_s * d_s + m_c * d_c) / inertia)
    tau_f = 0.3 * (m_s + m_c) * 9.81 * 0.0005 / inertia
    return wn, tau_f


WN, TAU_F = sheet_constants()
ZETA_AIR = 0.01  # edge-on skin friction, small
PEAK_DEG = 3.0
EASE_OUT = 0.4  # s to take the last stuck hundredth of a degree back to plumb


def simulate(push: float, t_on: float, sign: int, dt: float = 0.0005) -> list[tuple[float, float]]:
    """Angle in degrees from the start of contact; constant friction push for t_on s."""
    th = om = 0.0
    out = [(0.0, 0.0)]
    t = 0.0
    while True:
        tau = sign * push if t < t_on else 0.0
        restoring = -WN * WN * math.sin(th) - 2 * ZETA_AIR * WN * om + tau
        if om == 0.0 and abs(restoring) <= TAU_F:
            acc = 0.0  # static friction holds it
        else:
            fric = -TAU_F * math.copysign(1.0, om if om != 0.0 else restoring)
            acc = restoring + fric
        om_new = om + acc * dt
        if om != 0.0 and om_new * om < 0 and t >= t_on:
            om_new = 0.0  # reversing: it sticks for this step, and the stick test decides next step
        om = om_new
        th += om * dt
        t += dt
        out.append((t, math.degrees(th)))
        if t > t_on and om == 0.0 and abs(-WN * WN * math.sin(th)) <= TAU_F:
            break
        assert t < 12, "never stopped"
    # take the stuck angle back to plumb (it is a fraction of a pixel at the corner)
    stuck = out[-1][1]
    reach = math.hypot(SW / 2, HANG + SH)
    assert abs(math.radians(stuck)) * reach < 1.0, stuck
    t_end = out[-1][0]
    n = int(EASE_OUT / dt)
    for k in range(1, n + 1):
        out.append((t_end + k * dt, stuck * (1 - min_jerk(k / n))))
    return out


CONTACTS = [contact(i) for i in range(6)]


def traces() -> list[list[tuple[float, float]]]:
    """One push force for all six sheets, set so the largest swing is PEAK_DEG.

    Pivot friction makes the response nonlinear in the push, so the force is found
    by bisection rather than by scaling."""
    def run(k):
        return [simulate(k, t1 - t0, s) for t0, t1, s in CONTACTS]

    def peak(trs):
        return max(max(abs(a) for _, a in tr) for tr in trs)
    lo, hi = TAU_F, 2 * TAU_F
    while peak(run(hi)) < PEAK_DEG:  # bracket the force from below, never into a wild swing
        lo, hi = hi, hi * 1.5
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if peak(run(mid)) < PEAK_DEG else (lo, mid)
    trs = run((lo + hi) / 2)
    assert abs(peak(trs) - PEAK_DEG) < 0.01, peak(trs)
    return trs


TRACES = traces()


def angle_at(i: int, t: float) -> float:
    """Angle of sheet i at loop time t (linear between simulation samples)."""
    t0 = CONTACTS[i][0]
    tr = TRACES[i]
    u = t - t0
    if u <= 0 or u >= tr[-1][0]:
        return 0.0
    dt = tr[1][0]
    j = int(u / dt)
    (ta, a0), (_, a1) = tr[j], tr[min(j + 1, len(tr) - 1)]
    return a0 + (a1 - a0) * (u - ta) / dt


def pct(t: float) -> str:
    return f"{t / PERIOD * 100:.3f}%"


def deg(a: float) -> str:
    v = round(-a, 3) + 0.0  # SVG rotate is clockwise; +0.0 drops the sign of a zero
    return f"rotate({v:g}deg)"


def keyframes() -> str:
    css = []
    for i in range(6):
        t0 = CONTACTS[i][0]
        t_end = t0 + TRACES[i][-1][0]
        assert t_end < PERIOD + T_A - 1.0, ("sheet still moving at the next stroke", i, t_end)
        stops = [f"0%,{pct(t0)}{{transform:rotate(0deg)}}"]
        n = int(math.ceil((t_end - t0) / STEP))
        for k in range(1, n):
            t = t0 + k * STEP
            stops.append(f"{pct(t)}{{transform:{deg(angle_at(i, t))}}}")
        stops.append(f"{pct(t_end)},100%{{transform:rotate(0deg)}}")
        css.append(f"@keyframes s{i}{{{''.join(stops)}}}.s{i}{{animation:s{i} {PERIOD}s linear infinite}}")
    # the pencil, sampled on the same clock
    t_stop = T_A + 2 * D_STROKE + D_DROP
    stops = []
    t = T_A
    while t < t_stop + STEP:
        x, y = pencil_at(min(t, t_stop))
        stops.append(f"{pct(min(t, t_stop))}{{transform:translate({num(x)}px,{num(y)}px)}}")
        t += STEP
    x0, y0 = pencil_at(0)
    css.append("@keyframes pc{0%," + stops[0].split("{", 1)[0].split(",")[-1] + "{transform:translate("
               f"{num(x0)}px,{num(y0)}px)}}" + "".join(stops[1:]) + "100%{transform:translate("
               f"{num(X_OFF_L)}px,{num(Y_ROW[0])}px)}}}}.pc{{animation:pc {PERIOD}s linear infinite}}")
    return "".join(css)


def check_clearances() -> None:
    """Sample the whole loop: neighbours, the wire below and every panel edge stay clear."""
    pv = pivots()
    worst_gap, worst_low, worst_side = 1e9, 0.0, 1e9
    for k in range(int(PERIOD / 0.01)):
        t = k * 0.01
        polys = []
        for i, (px, py) in enumerate(pv):
            sheet = box(px - SW / 2, py + HANG, px + SW / 2, py + HANG + SH)
            polys.append(sh_rotate(sheet, -angle_at(i, t), origin=(px, py)))
        for row in (0, 1):
            for j in range(2):
                worst_gap = min(worst_gap, polys[row * 3 + j].distance(polys[row * 3 + j + 1]))
        for i, p in enumerate(polys):
            x0, _, x1, y1 = p.bounds
            worst_side = min(worst_side, x0 - 2, W - (x1 + 2))  # the soft shadow spreads 2 px
            if i < 3:
                worst_low = max(worst_low, y1)
            else:
                assert y1 + LIGHT_DY + 2 < H - 12, ("panel bottom", t, i)
    assert worst_gap > 6, worst_gap
    assert worst_low < WIRES[1] - 20, worst_low  # top-row sheets never reach the lower wire
    assert worst_side > 16, worst_side
    peaks = [max(abs(a) for _, a in tr) for tr in TRACES]
    stops = [CONTACTS[i][0] + TRACES[i][-1][0] for i in range(6)]
    print(f"  certs: wn {WN:.2f} rad/s (T {2 * math.pi / WN:.3f} s), pivot friction {TAU_F:.3f} rad/s2; "
          f"pushes {', '.join(f'{c[1] - c[0]:.2f}' for c in CONTACTS)} s; "
          f"peaks {', '.join(f'{p:.2f}' for p in peaks)} deg; all still at {max(stops):.2f} s; "
          f"closest neighbours {worst_gap:.1f} px, top row reaches y {worst_low:.1f}, side margin {worst_side:.1f} px")


# ----------------------------------------------------------------------------- drawing
def hardware(y: float, mono: str | None = None) -> str:
    """Wall plates, eye rings, a turnbuckle on the left, doubled splices into ferrules.

    With mono set, everything is drawn in that one colour (the shadow pass)."""
    c = {k: (mono or v) for k, v in STEEL.items()}
    s = ""
    for x0 in (8, 1185):  # wall plates
        s += rect(x0, y - 13, 7, 26, 1.5, fill=c["beam"], stroke=c["edge"], stroke_width=1)
    # left: anchor ring linked through its plate, turnbuckle, eye, splice
    s += f'<circle cx="19" cy="{y}" r="5" fill="none" stroke="{c["knurl"]}" stroke-width="2"/>'
    s += f'<path d="M24 {y}H34M76 {y}H91.5" stroke="{c["tick"]}" stroke-width="2"/>'
    s += rect(34, y - 7, 8, 14, 1.5, fill=c["body"], stroke=c["edge"], stroke_width=1)
    s += rect(68, y - 7, 8, 14, 1.5, fill=c["body"], stroke=c["edge"], stroke_width=1)
    s += f'<path d="M42 {y - 5}H68M42 {y + 5}H68" stroke="{c["knurl"]}" stroke-width="2.2"/>'
    s += f'<path d="M42 {y}H68" stroke="{c["tick"]}" stroke-width="1.4"/>'
    threads = "".join(f"M{x} {y - 2.2}V{y + 2.2}" for x in (46, 49, 52, 58, 61, 64))
    s += f'<path d="{threads}" stroke="{c["edge"]}" stroke-width="1"/>'
    s += f'<circle cx="{X_EYE_L}" cy="{y}" r="4.5" fill="none" stroke="{c["knurl"]}" stroke-width="2"/>'
    # the wire turns back through the eye: two strands into the crimp ferrule
    s += f'<path d="M100.5 {y - 0.9}H110M100.5 {y + 0.9}H110M1160 {y - 0.9}H1175.5M1160 {y + 0.9}H1175.5" ' \
         f'stroke="{c["tick"]}" stroke-width="1.2"/>'
    s += rect(108, y - 3, 12, 6, 1.2, fill=c["body"], stroke=c["edge"], stroke_width=1)
    s += rect(1150, y - 3, 12, 6, 1.2, fill=c["body"], stroke=c["edge"], stroke_width=1)
    s += f'<circle cx="{X_EYE_R}" cy="{y}" r="4.5" fill="none" stroke="{c["knurl"]}" stroke-width="2"/>'
    s += f'<circle cx="1186" cy="{y}" r="2.6" fill="{c["edge"]}"/>'  # the pin through the right plate
    return s


def wire_path(y: float) -> str:
    pts = [(120, y)] + [(cx, y + dip) for cx, dip in zip(CENTRES, DIPS)] + [(1150, y)]
    return "M" + "L".join(f"{num(x)} {num(yy)}" for x, yy in pts)


def clip(mono: str | None = None) -> str:
    """A 25 mm binder clip in front view; local origin is the pivot on the wire.

    The two wire handles are folded up together, so in front view they read as one
    loop whose arms leave the rolled top edge of the body and narrow to a bend that
    rests on the wire."""
    top = HANG
    by0, by1 = top - 5, top + 10  # the body grips the top 10 px of the sheet
    wire_c = mono or STEEL["knurl"]
    arm = f"M-17 {by0 + 1}L-7.5 3.2Q-7 -1.9 0 -1.9Q7 -1.9 7.5 3.2L17 {by0 + 1}"
    s = f'<path d="{arm}" fill="none" stroke="{wire_c}" stroke-width="1.8" stroke-linejoin="round" ' \
        f'stroke-linecap="round"/>'
    body = (f"M-24 {by0 + 2}Q-24 {by0} -22 {by0}H22Q24 {by0} 24 {by0 + 2}V{by1 - 1.5}Q24 {by1} 22.5 {by1}"
            f"H-22.5Q-24 {by1} -24 {by1 - 1.5}Z")
    if mono:
        return s + f'<path d="{body}" fill="{mono}"/>'
    edge = f' stroke="{CLIP_EDGE}" stroke-width="1"' if CLIP_EDGE else ""
    s += f'<path d="{body}" fill="{CLIP}"{edge}/>'
    # the rolled edge the handle ends pivot in, and the lip of the jaw
    s += f'<path d="M-22 {by0 + 1.6}H22" stroke="{CLIP_HI}" stroke-width="1.6"/>'
    s += f'<path d="M-17 {by0 + 1.6}h0.01M17 {by0 + 1.6}h0.01" stroke="{STEEL["knurl"]}" stroke-width="3.2" ' \
         f'stroke-linecap="round"/>'
    s += f'<path d="M-24 {by1 - 2.5}H24" stroke="{CLIP_HI}" stroke-width="0.8"/>'
    return s


def credential(d: Doc, cred: str, x_end: float, base: float, size: float) -> str:
    """The ID in mono, with a dot in every zero so 0 and O stay apart (the IDs mix both)."""
    s = d.text(cred, x_end, base, size, MONOB, fill=PEN, anchor="end")
    adv = MONOB.width("0", size)
    x0 = x_end - MONOB.width(cred, size)
    cap = MONOB.cap * size / MONOB.upm
    for k, ch in enumerate(cred):
        if ch == "0":
            s += f'<ellipse cx="{num(x0 + adv * (k + 0.5))}" cy="{num(base - cap / 2)}" rx="1.5" ry="2.4" fill="{PEN}"/>'
    return s


def sheet(d: Doc, i: int) -> str:
    """The record sheet in pivot coordinates: origin on the wire, sheet top at y=HANG."""
    cred, title, topics = CERTS[i]
    x0, y0 = -SW / 2, HANG

    def L(v):
        return x0 + v

    def T(v):
        return y0 + v
    s = rect(x0, y0, SW, SH, 2, fill=SHEET, stroke=EDGE or "none", stroke_width=1)
    # graph paper above the title block, the same 12 px grid as the hero sheet
    grid = "".join(f"M{num(L(x))} {num(T(8))}V{num(T(184))}" for x in range(20, SW - 8, 12))
    grid += "".join(f"M{num(L(8))} {num(T(y))}H{num(L(SW - 8))}" for y in range(20, 184, 12))
    s += f'<path d="{grid}" stroke="{GRAPH}" stroke-width="0.8"/>'
    s += rect(L(8), T(8), SW - 16, SH - 16, 0, fill="none", stroke=PENSOFT, stroke_width=1)

    # header: filing number, then the group as set text with one colour chip on the baseline
    s += d.text(f"{i + 1:02d}", L(22), T(44), 18, MONOB, fill=PEN)
    s += d.text(GROUP[i], L(308), T(44), 16, MONO, fill=PENSOFT, anchor="end")
    chip = LIME if CHIP[i] == "lime" else CHIP[i]
    s += rect(L(318.6), T(32.6), 10.8, 10.8, 1.5, fill=chip, stroke=PEN, stroke_width=1.2)

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
    s += credential(d, cred, L(330), T(233), 17)
    return s + clip()


def sheet_shadow(i: int) -> str:
    """Soft two-layer shadow of the sheet and its clip, in the sheet's own pivot frame."""
    s = f'<g opacity="{SHADOW_OP / 2}">{rect(-SW / 2 - 2, HANG - 2, SW + 4, SH + 4, 4, fill="#000")}</g>'
    s += f'<g opacity="{SHADOW_OP / 2}">{rect(-SW / 2, HANG, SW, SH, 2, fill="#000")}{clip("#000")}</g>'
    return s


def pencil() -> str:
    """Drafting pencil lying horizontal, point to the right; local origin at the point."""
    top, mid, bot = PENCIL_BODY
    b0, b1 = -PENCIL_L + 8, -30  # hex body
    s = ""
    s += rect(b0, -6, b1 - b0, 4, 0, fill=top)
    s += rect(b0, -2, b1 - b0, 4, 0, fill=mid)
    s += rect(b0, 2, b1 - b0, 4, 0, fill=bot)
    s += rect(-PENCIL_L, -6, 9, 12, 1.5, fill=LIME)  # the dipped end
    s += f'<path d="M{b0} -6V6" stroke="#000" stroke-opacity=".25" stroke-width="1"/>'
    # sharpened wood cone with its scalloped edge, then the graphite point
    s += f'<path d="M-30 -6Q-27 -4 -30 -2Q-27 0 -30 2Q-27 4 -30 6L-9 1.9V-1.9Z" fill="{WOOD}"/>'
    s += f'<path d="M-30 2Q-27 4 -30 6L-9 1.9V0Z" fill="{WOOD_SIDE}"/>'
    s += f'<path d="M-9 -1.9L0 0L-9 1.9Z" fill="{GRAPHITE}"/>'
    return s


def build() -> None:
    check_clearances()
    titles = [" ".join(t) for _, t, _ in CERTS]

    def covers(i):
        return f", covering {' '.join(CERTS[i][2])}" if CERTS[i][2] else ""
    desc = ("Six certificates from Dicoding Indonesia hang from binder clips on two wires: four front-end "
            "courses on the top wire, then back-end and career. "
            + " ".join(f"{i + 1:02d}: {titles[i]}{covers(i)}, credential {CERTS[i][0]}." for i in range(6))
            + " Every 16 seconds a drafting pencil is drawn along the bottom edges of each row and the sheets "
              "swing like pendulums, then hang still.")
    d = Doc(W, H, "Certifications: six Dicoding Indonesia certificates on a print line", desc)
    d.style(keyframes())
    d.defs.append(f'<clipPath id="panel"><rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="21"/></clipPath>')
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))

    pv = pivots()
    # shadow pass, light from straight above: hardware, wires, then each sheet with its clip
    sh = ""
    for y in WIRES:
        sh += f'<g transform="translate(0 {LIGHT_DY})">{hardware(y, "#000")}' \
              f'<path d="{wire_path(y)}" fill="none" stroke="#000" stroke-width="1.6"/></g>'
    d.add(f'<g opacity="{SHADOW_OP}">{sh}</g>')
    for i, (px, py) in enumerate(pv):
        d.add(f'<g transform="translate({num(px)} {num(py + LIGHT_DY)})"><g class="s{i}">{sheet_shadow(i)}</g></g>')

    for y in WIRES:
        d.add(hardware(y))
        d.add(f'<path d="{wire_path(y)}" fill="none" stroke="{STEEL["tick"]}" stroke-width="1.6" '
              f'stroke-linejoin="round"/>')
    for i, (px, py) in enumerate(pv):
        d.add(f'<g transform="translate({num(px)} {num(py)})"><g class="s{i}">{sheet(d, i)}</g></g>')

    # the pencil and its shadow on the paper, out of sight whenever it is not stroking
    x0, y0 = pencil_at(0)
    d.add(f'<g clip-path="url(#panel)"><g class="pc" transform="translate({num(x0)} {num(y0)})">'
          f'<g transform="translate(0 4)" opacity="{SHADOW_OP}">'
          f'<path d="M{-PENCIL_L} -6H-30L0 0L-30 6H{-PENCIL_L}Z" fill="#000"/></g>{pencil()}</g></g>')

    save("certs.svg", d)
