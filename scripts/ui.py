"""Section headers (a vernier caliper measures each title), buttons,
the odometer strip and the stamped footer."""

from __future__ import annotations

import math
import random

from motion import FIRM, HEAVY, SETTLE, SNAP, Spring, duration, linear_easing, spring_anim, spring_tf
from svgkit import Doc, num, rect
from theme import *  # noqa: F403

THEMES = {
    "dark": dict(fg=TEXT, muted=MUTED, metal="#2A2E35", edge="#424852", tick="#9BA0A8", num=DIM, lcd="#0E1012",
                 lcdfg=VOLT, blade="#343941"),
    "light": dict(fg="#15171B", muted="#62666E", metal="#D7DADF", edge="#A3A9B2", tick="#3B4048", num="#6B7079",
                  lcd="#1A1D21", lcdfg=VOLT, blade="#C6CAD0"),
}

SECTIONS = [
    ("work", "Featured projects"),
    ("stack", "Tech stack"),
    ("thesis", "Final thesis"),
    ("certs", "Certifications"),
    ("stats", "GitHub activity"),
]


# ---------------------------------------------------------------------------
# Caliper section header
# ---------------------------------------------------------------------------
def section_header(slug: str, title: str, theme: str) -> None:
    t = THEMES[theme]
    W, H = 1200, 168
    size = 70
    tx, base = 30, 142
    tw = DISP.width(title, size)
    measure = tw  # the jaws close on the exact advance width of the title
    d = Doc(W, H, title, f"Section header: {title}. A vernier caliper slides in and measures the title at {measure:.2f} px.")
    d.style(BASE_CSS)

    beam_y0, beam_y1 = 16, 44
    jaw_bottom = 158
    fixed_edge = tx - 4
    contact = tx + measure + 6
    open_x = 1062.0
    travel = open_x - contact
    s = FIRM
    dur = duration(s)
    delay = 0.35

    d.style(f"@keyframes slide{{from{{transform:translateX({num(travel)}px)}}to{{transform:translateX(0)}}}}"
            + spring_anim("slide", "slide", s, delay))
    # thumb roller turns as it rolls along the beam: angle = distance / radius
    r_roll = 7.0
    turn = travel / r_roll * 180 / math.pi
    d.style(f"@keyframes roll{{from{{transform:rotate({num(turn)}deg)}}to{{transform:rotate(0deg)}}}}"
            + spring_anim("roll", "roll", s, delay).replace(".roll{", ".roll{transform-box:fill-box;transform-origin:center;"))
    t_contact = delay + dur * 0.55
    d.style(f"@keyframes on{{from{{opacity:0}}to{{opacity:1}}}}@keyframes off{{from{{opacity:1}}to{{opacity:0}}}}"
            f".lcdv{{animation:on .12s linear {t_contact:.2f}s both}}.lcdd{{opacity:0;animation:off .12s linear {t_contact:.2f}s both}}"
            f"@keyframes hit{{0%{{opacity:0}}30%{{opacity:1}}100%{{opacity:0}}}}"
            f".hit{{opacity:0;animation:hit .5s ease-out {t_contact - 0.05:.2f}s both}}")
    d.style(f"@keyframes rise{{from{{transform:translateY(28px);opacity:0}}to{{transform:none;opacity:1}}}}"
            + spring_anim("ttl", "rise", SNAP, 0.05))

    # main scale (beam) with engraved graduations
    d.add(rect(2, beam_y0, W - 4, beam_y1 - beam_y0, 4, fill=t["metal"], stroke=t["edge"], stroke_width=1))
    ticks = []
    for i, x in enumerate(range(int(fixed_edge), W - 6, 6)):
        n = (x - int(fixed_edge)) // 6
        ln = 12 if n % 10 == 0 else 8 if n % 5 == 0 else 5
        ticks.append(f"M{x} {beam_y1}V{beam_y1 - ln}")
        if n % 10 == 0 and x < W - 30:
            d.add(d.text(str(n // 10), x + 3, beam_y0 + 11, 8.5, MONOB, fill=t["num"]))
    d.add(f'<path d="{"".join(ticks)}" stroke="{t["tick"]}" stroke-width="1"/>')

    # fixed jaw
    d.add(f'<path d="M2 {beam_y1} H{num(fixed_edge)} V{jaw_bottom - 26} L{num(fixed_edge - 10)} {jaw_bottom} H2 Z" '
          f'fill="{t["blade"]}" stroke="{t["edge"]}" stroke-width="1"/>')

    # title
    d.add(f'<g class="ttl">{d.text(title, tx, base, size, DISP, fill=t["fg"])}</g>')

    # contact flashes on both jaws
    for ex in (fixed_edge, contact):
        d.add(f'<g class="hit"><path d="M{num(ex)} {base - size * 0.72} V{base + 4}" stroke="{VOLT}" stroke-width="2"/></g>')

    # sliding jaw + housing + LCD + thumb roller
    hx = contact
    blade = (f'<path d="M{num(hx)} {beam_y1} H{num(hx + 18)} V{jaw_bottom} H{num(hx + 10)} L{num(hx)} {jaw_bottom - 26} Z" '
             f'fill="{t["blade"]}" stroke="{t["edge"]}" stroke-width="1"/>')
    housing = rect(hx - 4, beam_y0 - 8, 172, beam_y1 - beam_y0 + 22, 7, fill=t["metal"], stroke=t["edge"], stroke_width=1.2)
    # vernier scale on the housing
    vt = "".join(f"M{num(hx + 4 + i * 5.4)} {beam_y1 + 14}V{beam_y1 + 14 - (7 if i % 5 == 0 else 4)}" for i in range(11))
    housing += f'<path d="{vt}" stroke="{t["tick"]}" stroke-width="1"/>'
    lcd_x = hx + 64
    housing += rect(lcd_x, beam_y0 - 2, 96, 26, 4, fill=t["lcd"])
    val = f"{measure:7.2f}".replace(" ", "0")
    housing += f'<g class="lcdd">{d.text("----.--", lcd_x + 48, beam_y0 + 15.5, 13, MONOB, fill=DIM, anchor="middle")}</g>'
    housing += f'<g class="lcdv">{d.text(val, lcd_x + 48, beam_y0 + 15.5, 13, MONOB, fill=t["lcdfg"], anchor="middle")}</g>'
    housing += d.text("PX", lcd_x + 86, beam_y0 + 34, 7.5, MONOB, fill=t["num"], anchor="middle")
    roller = (f'<g transform="translate({num(hx + 36)} {beam_y1 + 9})"><g class="roll">'
              f'<circle r="{r_roll}" fill="{t["blade"]}" stroke="{t["edge"]}"/>'
              + "".join(f'<path d="M0 {-r_roll} V{-r_roll + 3}" stroke="{t["tick"]}" transform="rotate({a})"/>' for a in range(0, 360, 30))
              + "</g></g>")
    d.add(f'<g class="slide">{blade}{housing}{roller}</g>')
    save(f"section-{slug}-{theme}.svg", d)


# ---------------------------------------------------------------------------
# Buttons: flat keycaps that get pressed now and then, with a spring return
# ---------------------------------------------------------------------------
def icon(kind: str, x: float, y: float, color: str) -> str:
    if kind == "down":
        return (f'<path d="M{x} {y-6} V{y+6} M{x-5} {y+1} L{x} {y+6} L{x+5} {y+1}" fill="none" stroke="{color}" '
                f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    if kind == "ne":
        return arrow_ne(x - 5.5, y - 5.5, 11, color, 2)
    if kind == "linkedin":
        return (rect(x - 9, y - 9, 18, 18, 4, fill=color)
                + f'<rect x="{x-5.5}" y="{y-1.5}" width="2.6" height="7" fill="{INK}"/><circle cx="{x-4.2}" cy="{y-4.6}" r="1.5" fill="{INK}"/>'
                + f'<path d="M{x-1} {y+5.5} V{y-1.5} h2.4 v1.2 q1 -1.5 2.8 -1.5 q2.6 0 2.6 3 v4.3 h-2.6 v-3.8 q0 -1.4 -1.2 -1.4 q-1.4 0 -1.4 1.6 v3.6 Z" fill="{INK}"/>')
    if kind == "mail":
        return (rect(x - 9.5, y - 7, 19, 14, 3, fill="none", stroke=color, stroke_width=1.8)
                + f'<path d="M{x-8} {y-5} L{x} {y+1} L{x+8} {y-5}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="round"/>')
    if kind == "instagram":
        return (rect(x - 9, y - 9, 18, 18, 5.5, fill="none", stroke=color, stroke_width=1.8)
                + f'<circle cx="{x}" cy="{y}" r="4.2" fill="none" stroke="{color}" stroke-width="1.8"/>'
                + f'<circle cx="{x+4.8}" cy="{y-4.8}" r="1.2" fill="{color}"/>')
    if kind == "play":
        return f'<circle cx="{x}" cy="{y}" r="9" fill="{color}"/><path d="M{x-2.5} {y-4} L{x+4} {y} L{x-2.5} {y+4} Z" fill="{INK}"/>'
    if kind == "code":
        return (f'<path d="M{x-4} {y-6} L{x-9} {y} L{x-4} {y+6} M{x+4} {y-6} L{x+9} {y} L{x+4} {y+6}" fill="none" '
                f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    if kind == "paper":
        return (f'<path d="M{x-7} {y-9} H{x+3} L{x+7} {y-5} V{y+9} H{x-7} Z" fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="round"/>'
                + f'<path d="M{x-3.5} {y-1} H{x+3.5} M{x-3.5} {y+3} H{x+3.5}" stroke="{color}" stroke-width="1.6" stroke-linecap="round"/>')
    raise ValueError(kind)


def button(name: str, label: str, lead: str, trail: str, prefix: str | None = None, phase: float = 0.0) -> None:
    H = 48
    face_h = 42
    lw = MONOB.width(label, 13)
    pw = MONO.width(prefix, 13) + 8 if prefix else 0
    lead_w = 22 if lead else 0
    W = 18 + lead_w + (10 if lead else 0) + pw + lw + 14 + 14 + 16
    d = Doc(W, H, label, f"Button: {label}")
    period = 9.0
    p0 = phase / period * 100
    # one press per cycle: quick travel down, spring back up
    d.style(f"@keyframes press{{0%,{p0:.2f}%{{transform:translateY(0)}}"
            f"{p0 + 1.2:.2f}%{{transform:translateY(4px);animation-timing-function:linear}}"
            f"{p0 + 2.6:.2f}%{{transform:translateY(4px);{spring_tf(SNAP)}}}"
            f"{p0 + 9:.2f}%,100%{{transform:translateY(0)}}}}"
            f".press{{animation:press {period}s cubic-bezier(.5,0,.75,0) infinite}}")
    d.add(rect(1, 5, W - 2, face_h, face_h / 2, fill="#07080A", stroke=LINE, stroke_width=1))
    g = rect(1, 1, W - 2, face_h, face_h / 2, fill=PANEL2, stroke="#3A3F48", stroke_width=1.2)
    cy = 1 + face_h / 2
    x = 18
    if lead:
        g += icon(lead, x + 11, cy, VOLT)
        x += lead_w + 10
    if prefix:
        g += d.text(prefix, x, cy + 4.6, 13, MONO, fill=VOLT)
        x += pw
    g += d.text(label, x, cy + 4.6, 13, MONOB, fill=TEXT)
    x += lw + 14
    g += icon(trail, x + 7, cy, MUTED)
    d.add(f'<g class="press">{g}</g>')
    save(f"btn-{name}.svg", d)


# ---------------------------------------------------------------------------
# Odometer strip
# ---------------------------------------------------------------------------
def odometer() -> None:
    W, H = 1200, 188
    d = Doc(W, H, "3.63 GPA, 75% thesis accuracy, 3 apps live in production, 12 builds on this page",
            "Four counters roll into place: GPA 3.63 out of 4.00, thesis model accuracy 75 percent, "
            "3 apps live in production and 12 builds featured on this page.")
    d.style(BASE_CSS)
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))
    stats = [
        ("3.63", "/ 4.00", "GPA, Computer Science", VOLT, 3.63 / 4),
        ("75%", "", "Thesis model accuracy", SKY, 0.75),
        ("3", "apps", "Live in production", CORAL, 1.0),
        ("12", "builds", "Featured on this page", TEXT, 1.0),
    ]
    cw = W / 4
    size = 84
    L = 96
    top, base = 30, 112
    roll = Spring(170, 19, 1.4)  # heavy drum: one soft overshoot before it locks
    for ci, (val, unit, label, color, frac) in enumerate(stats):
        x0 = ci * cw + 36
        if ci:
            d.add(f'<line x1="{num(ci*cw)}" y1="30" x2="{num(ci*cw)}" y2="{H-30}" stroke="{LINE}"/>')
        d.defs.append(f'<clipPath id="o{ci}"><rect x="{num(x0-28)}" y="{top}" width="{num(cw-36)}" height="{base-top+18}"/></clipPath>')
        x = x0
        parts = []
        for di, ch in enumerate(val):
            w = DISP.width(ch, size)
            if ch.isdigit():
                rows = 10 + int(ch)
                col = "".join(d.text(str(k % 10), x + w / 2, base - (rows - k) * L, size, DISP, fill=TEXT, anchor="middle")
                              for k in range(rows + 1))
                delay = 0.3 + ci * 0.16 + di * 0.09
                d.style(f"@keyframes r{ci}{di}{{from{{transform:translateY({rows*L}px)}}to{{transform:translateY(0)}}}}"
                        + spring_anim(f"r{ci}{di}", f"r{ci}{di}", roll, delay))
                parts.append(f'<g class="r{ci}{di}">{col}</g>')
            else:
                parts.append(d.text(ch, x, base, size, DISP, fill=TEXT))
            x += w
        d.add(f'<g clip-path="url(#o{ci})">{"".join(parts)}</g>')
        if unit:
            d.add(d.text(unit, x + 8, base, 17, MONOB, fill=MUTED))
        bw = cw - 72
        d.add(rect(x0, 138, bw, 4, 2, fill=LINE))
        d.style(f"@keyframes g{ci}{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}"
                + spring_anim(f"g{ci}", f"g{ci}", FIRM, 0.7 + ci * 0.16).replace(f".g{ci}{{", f".g{ci}{{transform-box:fill-box;transform-origin:left center;"))
        d.add(f'<rect class="g{ci}" x="{num(x0)}" y="138" width="{num(bw*frac)}" height="4" rx="2" fill="{color}"/>')
        d.add(d.text(label, x0, 166, 14, SEMI, fill=MUTED))
    save("stats.svg", d)


# ---------------------------------------------------------------------------
# Footer: a rubber stamp marks the reply card
# ---------------------------------------------------------------------------
def footer() -> None:
    W, H = 1200, 380
    P = 7.0
    d = Doc(W, H, "Open to remote opportunities. Feel free to reach out.",
            "A closing panel: open to remote opportunities, feel free to reach out at fatihaljabar@gmail.com. "
            "A rubber stamp comes down on a reply card and leaves the mark 'Available for remote work'.")
    d.style(BASE_CSS)
    d.defs.append(f'<clipPath id="panel"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22"/></clipPath>')
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))
    d.add('<g clip-path="url(#panel)">')
    d.add(d.text("Open to remote", 46, 150, 88, DISP, fill=TEXT))
    d.add(d.text("opportunities.", 46, 240, 88, DISP, fill=VOLT))
    d.add(d.text("Feel free to reach out.", 50, 292, 22, SEMI, fill=MUTED))
    d.add(d.text("fatihaljabar@gmail.com", 50, 326, 16, MONO, fill=TEXT))

    # reply card
    cx, cy = 1000, 196
    card = rect(-150, -118, 300, 236, 6, fill=PAPER)
    card += d.text("REPLY CARD", -126, -84, 11, MONOB, fill=PENSOFT, ls=1.4)
    card += d.text("No. 2026", 126, -84, 11, MONOB, fill=PENSOFT, anchor="end")
    for i in range(5):
        y = -52 + i * 30
        card += f'<path d="M-126 {y}H126" stroke="{GRAPH2}" stroke-width="1"/>'
    card += d.text("to: you", -126, -60, 13, MONO, fill=PEN)
    card += d.text("re: a remote role", -126, -30, 13, MONO, fill=PEN)

    # stamp imprint with ink grain
    rnd = random.Random(21)
    grain = "".join(f'<circle cx="{rnd.uniform(-118,118):.1f}" cy="{rnd.uniform(-44,44):.1f}" r="{rnd.uniform(.6,2.1):.1f}" fill="#000"/>'
                    for _ in range(170))
    d.defs.append(f'<mask id="ink" maskUnits="userSpaceOnUse" x="-130" y="-60" width="260" height="120">'
                  f'<rect x="-130" y="-60" width="260" height="120" fill="#fff"/>{grain}</mask>')
    imprint = (rect(-112, -42, 224, 84, 8, fill="none", stroke=CORAL, stroke_width=3.5)
               + rect(-104, -34, 208, 68, 5, fill="none", stroke=CORAL, stroke_width=1.4)
               + d.text("AVAILABLE", 0, 6, 34, DISP, fill=CORAL, anchor="middle")
               + d.text("FOR REMOTE WORK", 0, 26, 11, MONOB, fill=CORAL, anchor="middle", ls=2))
    hit = 0.30
    d.style(f"@keyframes inkin{{from{{opacity:0}}to{{opacity:1}}}}"
            f".inkin{{animation:inkin .06s linear {hit * P:.2f}s both}}"
            f"@keyframes inkpulse{{0%,{hit*100:.1f}%{{opacity:.86}}{hit*100+1:.1f}%{{opacity:1}}{hit*100+14:.1f}%,100%{{opacity:.86}}}}"
            f".inkpulse{{animation:inkpulse {P}s linear infinite}}")
    card += (f'<g transform="translate(6 40) rotate(-7)"><g class="inkin"><g class="inkpulse" opacity=".86">'
             f'<g mask="url(#ink)">{imprint}</g></g></g></g>')
    d.style(f"@keyframes nudge{{0%,{hit*100:.1f}%{{transform:translateY(0)}}{hit*100+0.8:.1f}%{{transform:translateY(2px)}}"
            f"{hit*100+6:.1f}%,100%{{transform:translateY(0)}}}}.nudge{{animation:nudge {P}s ease-out infinite}}")
    d.add(f'<g transform="translate({cx} {cy}) rotate(3)"><g class="nudge">{card}</g></g>')

    # the stamp, seen from above: lifted it sits closer to the eye (bigger, shadow
    # further away), it drops under gravity, squashes on contact, springs back
    rest = "translate(150px,-150px) scale(1.16) rotate(8deg)"
    fall0 = (hit - 0.09) * 100
    d.style(f"@keyframes stamp{{"
            f"0%,{fall0:.2f}%{{transform:{rest};animation-timing-function:cubic-bezier(.55,0,1,.45)}}"
            f"{hit*100:.2f}%{{transform:none;animation-timing-function:linear}}"
            f"{hit*100+0.7:.2f}%{{transform:scale(.985)}}"
            f"{hit*100+4:.2f}%{{transform:none;{spring_tf(HEAVY)}}}"
            f"{hit*100+24:.2f}%,100%{{transform:{rest}}}}}"
            f".stamp{{transform:{rest};animation:stamp {P}s linear infinite}}"
            f"@keyframes shadow{{"
            f"0%,{fall0:.2f}%{{transform:translate(26px,30px);opacity:.42;animation-timing-function:cubic-bezier(.55,0,1,.45)}}"
            f"{hit*100:.2f}%{{transform:translate(3px,4px);opacity:.6;animation-timing-function:linear}}"
            f"{hit*100+4:.2f}%{{transform:translate(3px,4px);{spring_tf(HEAVY)}}}"
            f"{hit*100+24:.2f}%,100%{{transform:translate(26px,30px);opacity:.42}}}}"
            f".shadow{{transform:translate(26px,30px);opacity:.42;animation:shadow {P}s linear infinite}}")
    block = (rect(-124, -50, 248, 100, 14, fill="#2A2E35", stroke="#4A505B", stroke_width=1.4)
             + rect(-114, -40, 228, 80, 9, fill="none", stroke="#3A3F48", stroke_width=1)
             + '<circle r="34" fill="#353A43" stroke="#555C67" stroke-width="1.4"/>'
             + '<circle r="22" fill="#3E444E"/>'
             + '<path d="M-14 -10 a18 18 0 0 1 20 -8" fill="none" stroke="#6B7280" stroke-width="3" stroke-linecap="round"/>')
    shadow = rect(-124, -50, 248, 100, 14, fill="#000")
    d.add(f'<g transform="translate({cx + 6} {cy + 40}) rotate(-4)">'
          f'<g class="stamp"><g class="shadow">{shadow}</g>{block}</g></g>')
    d.add("</g>")
    save("footer.svg", d)


def build_all() -> None:
    for slug, title in SECTIONS:
        for theme in ("dark", "light"):
            section_header(slug, title, theme)
    for i, (name, label, prefix) in enumerate([("nav-work", "Projects", "01 "), ("nav-stack", "Stack", "02 "),
                                               ("nav-thesis", "Thesis", "03 "), ("nav-certs", "Certifications", "04 "),
                                               ("nav-stats", "Activity", "05 ")]):
        button(name, label, "", "down", prefix=prefix, phase=1.2 + i * 0.35)
    for i, (name, label, lead) in enumerate([("linkedin", "LinkedIn", "linkedin"), ("email", "Email", "mail"),
                                             ("instagram", "Instagram", "instagram")]):
        button(name, label, lead, "ne", phase=4.5 + i * 0.35)
    for i, (name, label, lead) in enumerate([("demo", "Live demo", "play"), ("source", "Source code", "code"),
                                             ("article", "Article", "paper")]):
        button(name, label, lead, "ne", phase=2.0 + i * 0.35)
    odometer()
    footer()
