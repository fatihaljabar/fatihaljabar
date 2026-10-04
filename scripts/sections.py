"""Section headers, buttons, stats odometer, stack marquee, thesis and footer."""

from __future__ import annotations

import math
import random

from svgkit import Doc, num, rect
from theme import *  # noqa: F403

THEMES = {
    "dark": dict(fg=TEXT, muted=MUTED, line=LINE, accent=VOLT, chip=PANEL),
    "light": dict(fg="#15171B", muted="#6B6F77", line="#D9D6CF", accent="#4C6B00", chip="#ECE9E2"),
}


# ---------------------------------------------------------------------------
# Section headers (one dark and one light variant each, swapped with <picture>)
# ---------------------------------------------------------------------------
SECTIONS = [
    ("work", "01", "Featured", "projects", "12 builds · click a card to open it"),
    ("stack", "02", "Tech", "stack", "the toolbox, always moving"),
    ("thesis", "03", "Final", "thesis", "deep learning · Indonesian NLP"),
    ("certs", "04", "Certifications", "", "6 courses · Dicoding Indonesia"),
    ("stats", "05", "GitHub", "stats", "pulled live from the API"),
]


def section_header(slug, idx, word, serif, kicker, theme) -> None:
    t = THEMES[theme]
    W, H = 1200, 132
    d = Doc(W, H, f"{idx} {word}{serif}", f"Section {idx}: {word}{serif}. {kicker}.")
    d.style(BASE_CSS)
    d.style(f"""
@keyframes up{{from{{transform:translateY(90px)}}to{{transform:none}}}}
.up{{animation:up .9s {OUTQ} both}}
@keyframes draw{{from{{stroke-dashoffset:1}}to{{stroke-dashoffset:0}}}}
.rule{{stroke-dasharray:1;animation:draw 1.2s {INOUT} .5s both}}
@keyframes popin{{from{{transform:scale(0)}}to{{transform:scale(1)}}}}
.idx{{animation:popin .5s {SPRING} both}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
.kick{{animation:fade .6s linear .7s both}}
""")
    d.defs.append(f'<clipPath id="mask"><rect x="0" y="40" width="{W}" height="88"/></clipPath>')
    d.add(f'<g class="fb idx">{rect(2, 6, 52, 28, 8, fill=VOLT)}{d.text(idx, 28, 25.5, 14, MONOB, fill=INK, anchor="middle")}</g>')
    d.add(f'<g class="kick">{d.text(kicker.upper(), 68, 25, 12, MONOB, fill=t["muted"], ls=1)}</g>')
    size = 72
    serif_size = 82
    ww = DISP.width(word, size)
    g = d.text(word, 0, 112, size, DISP, fill=t["fg"], per_char="up", delay0=0.1, step=0.035)
    if serif:
        g += d.text(serif, ww + 10, 112, serif_size, SERIF, fill=t["accent"], per_char="up",
                    delay0=0.1 + len(word) * 0.035, step=0.035)
    d.add(f'<g clip-path="url(#mask)">{g}</g>')
    end = ww + (SERIF.width(serif, serif_size) + 10 if serif else 0) + 36
    d.add(f'<path class="rule" pathLength="1" d="M{num(end)} 100 H{W-2}" stroke="{t["line"]}" stroke-width="2"/>')
    span = W - 2 - end - 10
    d.style(f"@keyframes run{{0%{{transform:translateX(0);opacity:0}}8%{{opacity:1}}92%{{opacity:1}}100%{{transform:translateX({num(span)}px);opacity:0}}}}"
            f".run{{animation:run 5s {INOUT} 1.6s infinite both}}")
    d.add(f'<g transform="translate({num(end)} 96)"><rect class="run" width="10" height="8" rx="2" fill="{VOLT}"/></g>')
    save(f"section-{slug}-{theme}.svg", d)


# ---------------------------------------------------------------------------
# Buttons (navigation, contact and thesis links)
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


def button(name: str, label: str, lead: str, trail: str, prefix: str | None = None, delay: float = 0.0) -> None:
    H = 44
    lw = MONOB.width(label, 13)
    pw = MONO.width(prefix, 13) + 8 if prefix else 0
    lead_w = 22 if lead else 0
    W = 18 + lead_w + (10 if lead else 0) + pw + lw + 14 + 14 + 16
    d = Doc(W, H, label, f"Button: {label}")
    d.style(f"""
@keyframes shine{{0%,70%{{transform:translateX(-80px)}}100%{{transform:translateX({num(W+80)}px)}}}}
.shine{{animation:shine 6s {INOUT} {delay:.2f}s infinite}}
.ar{{animation:nudge 2.4s ease-in-out {delay:.2f}s infinite}}
""")
    d.defs.append(f'<clipPath id="c"><rect x="1" y="1" width="{num(W-2)}" height="{H-2}" rx="{(H-2)/2}"/></clipPath>'
                  f'<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{TEXT}" stop-opacity="0"/>'
                  f'<stop offset=".5" stop-color="{TEXT}" stop-opacity=".12"/><stop offset="1" stop-color="{TEXT}" stop-opacity="0"/></linearGradient>')
    d.add(rect(1, 1, W - 2, H - 2, (H - 2) / 2, fill=PANEL, stroke=LINE, stroke_width=1.4))
    d.add(f'<g clip-path="url(#c)"><g class="shine"><rect x="0" y="0" width="60" height="{H}" fill="url(#g)" transform="skewX(-20)"/></g></g>')
    x = 18
    if lead:
        d.add(icon(lead, x + 11, H / 2, VOLT))
        x += lead_w + 10
    if prefix:
        d.add(d.text(prefix, x, H / 2 + 4.6, 13, MONO, fill=VOLT))
        x += pw
    d.add(d.text(label, x, H / 2 + 4.6, 13, MONOB, fill=TEXT))
    x += lw + 14
    dx, dy = ("0px", "3px") if trail == "down" else ("2px", "-2px")
    d.style(f"@keyframes nudge{{0%,60%,100%{{transform:translate(0,0)}}75%{{transform:translate({dx},{dy})}}}}")
    d.add(f'<g class="ar">{icon(trail, x + 7, H / 2, MUTED)}</g>')
    save(f"btn-{name}.svg", d)


# ---------------------------------------------------------------------------
# Stats odometer
# ---------------------------------------------------------------------------
def odometer() -> None:
    W, H = 1200, 196
    d = Doc(W, H, "3.63 GPA, 75% thesis accuracy, 3 apps live in production, 12 builds on this page",
            "Four numbers roll into place like an odometer: GPA 3.63 out of 4.00, thesis model accuracy 75 percent, "
            "3 apps live in production and 12 builds featured on this page.")
    d.defs.append(dots_pattern("dots", 22))
    d.style(BASE_CSS)
    d.style(f"""
@keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
.grow{{animation:grow 1.6s {OUTQ} both;transform-box:fill-box;transform-origin:left center}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.blink{{animation:blink 1.4s ease-in-out infinite}}
""")
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))
    d.add(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22" fill="url(#dots)" opacity=".6"/>')
    stats = [
        ("3.63", "/ 4.00", "GPA · COMPUTER SCIENCE", VOLT),
        ("75%", "", "THESIS MODEL ACCURACY", SKY),
        ("3", "apps", "LIVE IN PRODUCTION", CORAL),
        ("12", "builds", "FEATURED ON THIS PAGE", TEXT),
    ]
    cw = W / 4
    size = 84
    L = 96  # digit line height
    top, base = 34, 116
    for ci, (val, unit, label, color) in enumerate(stats):
        x0 = ci * cw + 36
        if ci:
            d.add(f'<line x1="{num(ci*cw)}" y1="30" x2="{num(ci*cw)}" y2="{H-30}" stroke="{LINE}"/>')
        d.defs.append(f'<clipPath id="o{ci}"><rect x="{num(x0-28)}" y="{top}" width="{num(cw-36)}" height="{base-top+18}"/></clipPath>')
        x = x0
        parts = []
        for di, ch in enumerate(val):
            w = DISP.width(ch, size)
            if ch.isdigit():
                t = int(ch)
                rows = 10 + t
                # digit k sits at baseline - (rows - k) * L, so k == rows (the target) sits on the baseline
                col = "".join(d.text(str(k % 10), x + w / 2, base - (rows - k) * L, size, DISP, fill=TEXT, anchor="middle")
                              for k in range(rows + 1))
                delay = 0.3 + ci * 0.18 + di * 0.1
                d.style(f"@keyframes r{ci}{di}{{from{{transform:translateY({rows*L}px)}}to{{transform:translateY(0)}}}}"
                        f".r{ci}{di}{{animation:r{ci}{di} 2.4s {OUTQ} {delay:.2f}s both}}")
                parts.append(f'<g class="r{ci}{di}">{col}</g>')
            else:
                parts.append(d.text(ch, x, base, size, DISP, fill=TEXT))
            x += w
        d.add(f'<g clip-path="url(#o{ci})">{"".join(parts)}</g>')
        if unit:
            d.add(d.text(unit, x + 8, base, 30, SERIF, fill=color))
        d.add(rect(x0, 142, cw - 72, 3, 1.5, fill=LINE))
        d.add(f'<rect class="grow" style="animation-delay:{0.6 + ci*0.18:.2f}s" x="{num(x0)}" y="142" width="{num((cw-72)*[0.9075,0.75,1,1][ci])}" height="3" rx="1.5" fill="{color}"/>')
        d.add(d.text(label, x0, 170, 12, MONOB, fill=MUTED, ls=0.8))
        if ci == 2:
            lx = x0 + MONOB.width(label, 12) + 0.8 * len(label) + 10
            d.add(f'<circle class="blink" cx="{num(lx)}" cy="165.5" r="4" fill="{CORAL}"/>')
    save("stats.svg", d)


# ---------------------------------------------------------------------------
# Stack marquee
# ---------------------------------------------------------------------------
STACK_ROWS = [
    ("FRONT-END", VOLT, ["TypeScript", "React", "Next.js", "Vue.js", "Tailwind CSS", "Framer Motion", "TanStack Query",
                         "Zustand", "Radix UI", "shadcn/ui", "Recharts", "Vite", "React Router", "next-intl", "JavaScript", "HTML5", "CSS3"]),
    ("BACK-END & DATA", CORAL, ["Node.js", "Express", "Hono", "Prisma", "Drizzle ORM", "PostgreSQL", "MariaDB", "MySQL", "Supabase",
                                "MongoDB", "Auth.js", "Zod", "Cloudflare R2", "Resend", "Midtrans", "Docker", "Vercel", "Netlify"]),
    ("ML & TOOLING", SKY, ["Python", "TensorFlow", "Keras", "PyTorch", "scikit-learn", "pandas", "Streamlit", "HuggingFace",
                           "Sastrawi", "Playwright", "Vitest", "GitHub Actions", "Biome", "ESLint", "Figma", "Claude Code", "Codex"]),
]


def marquee() -> None:
    W, H = 1200, 300
    d = Doc(W, H, "Tech stack marquee", "Three rows of technologies scroll sideways: front-end, back-end and data, machine learning and tooling.")
    d.style(BASE_CSS)
    d.defs.append(f'<clipPath id="panel"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22"/></clipPath>')
    d.defs.append(f'<linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="{PANEL}"/><stop offset=".72" stop-color="{PANEL}"/>'
                  f'<stop offset="1" stop-color="{PANEL}" stop-opacity="0"/></linearGradient>'
                  f'<linearGradient id="fadeR" x1="0" x2="1"><stop offset="0" stop-color="{PANEL}" stop-opacity="0"/><stop offset="1" stop-color="{PANEL}"/></linearGradient>')
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))
    d.add('<g clip-path="url(#panel)">')
    ys = [42, 124, 206]
    for ri, (label, color, items) in enumerate(STACK_ROWS):
        x = 0
        chips = ""
        for it in items:
            tw = SEMI.width(it, 19)
            w = tw + 50
            chips += rect(x, 0, w, 52, 14, fill=PANEL2, stroke=LINE, stroke_width=1.2)
            chips += f'<circle cx="{num(x+20)}" cy="26" r="5" fill="{color}"/>'
            chips += d.text(it, x + 34, 32.5, 19, SEMI, fill=TEXT)
            x += w + 12
        row_w = x
        dur = row_w / 38
        direction = "normal" if ri != 1 else "reverse"
        d.style(f"@keyframes mq{ri}{{from{{transform:translateX(0)}}to{{transform:translateX(-{num(row_w)}px)}}}}"
                f".mq{ri}{{animation:mq{ri} {dur:.1f}s linear infinite {direction}}}")
        d.add(f'<g transform="translate(0 {ys[ri]})"><g class="mq{ri}">{chips}<g transform="translate({num(row_w)} 0)">{chips}</g></g></g>')
    d.add(f'<rect x="0" y="0" width="250" height="{H}" fill="url(#fadeL)"/>')
    d.add(f'<rect x="{W-140}" y="0" width="140" height="{H}" fill="url(#fadeR)"/>')
    for ri, (label, color, items) in enumerate(STACK_ROWS):
        y = ys[ri]
        d.add(rect(28, y + 14, 4, 24, 2, fill=color))
        d.add(d.text(label, 44, y + 25, 12, MONOB, fill=TEXT, ls=0.8))
        d.add(d.text(f"{len(items)} tools", 44, y + 42, 11, MONO, fill=DIM))
    d.add("</g>")
    save("stack.svg", d)


# ---------------------------------------------------------------------------
# Thesis
# ---------------------------------------------------------------------------
def thesis() -> None:
    W, H = 1200, 470
    D = 10
    d = Doc(W, H, "Sentiment analysis pipeline: tweets, preprocessing, CNN + BiLSTM + Attention, 75% accuracy",
            "Indonesian tweets about electric vehicles stream in, pass through cleaning, case folding, Sastrawi stemming and "
            "quantile labeling, then through Conv1D, BiLSTM and attention layers. Four models are compared and the "
            "CNN + BiLSTM + Attention hybrid wins with 75 percent accuracy and 0.76 macro F1.")
    d.defs.append(dots_pattern("dots", 22))
    d.style(BASE_CSS)
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))
    d.add(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22" fill="url(#dots)" opacity=".7"/>')

    def colhead(x, n, title, sub):
        d.add(rect(x, 34, 40, 24, 6, fill=VOLT) + d.text(n, x + 20, 50.5, 12, MONOB, fill=INK, anchor="middle"))
        d.add(d.text(title, x + 52, 51, 15, MONOB, fill=TEXT))
        d.add(d.text(sub, x, 82, 12, MONO, fill=DIM))

    # --- column A: tweet stream
    ax, aw = 36, 290
    colhead(ax, "01", "DATA", "Indonesian tweets · Jan 2023 to Aug 2025")
    d.defs.append(f'<clipPath id="feed"><rect x="{ax}" y="98" width="{aw}" height="336" rx="14"/></clipPath>')
    d.add(rect(ax, 98, aw, 336, 14, fill=BG, stroke=LINE, stroke_width=1.2))
    rnd = random.Random(5)
    feed = ""
    n = 8
    gap = 62
    tints = [VOLT, CORAL, SKY, MUTED]
    for i in range(n):
        y = i * gap
        c = tints[i % 4]
        feed += rect(ax + 14, y, aw - 28, 50, 12, fill=PANEL2, stroke=LINE, stroke_width=1)
        feed += f'<circle cx="{ax+36}" cy="{y+25}" r="11" fill="{c}" opacity=".9"/>'
        feed += rect(ax + 56, y + 13, 60 + rnd.randint(0, 60), 7, 3.5, fill="#4A505B")
        feed += rect(ax + 56, y + 29, 100 + rnd.randint(0, 90), 7, 3.5, fill="#2E333B")
        feed += f'<path d="M{ax+aw-38} {y+18} l5 6 l-5 6" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" opacity=".7"/>'
    loop = n * gap
    d.style(f"@keyframes feed{{from{{transform:translateY(0)}}to{{transform:translateY(-{loop}px)}}}}.feed{{animation:feed 14s linear infinite}}")
    d.add(f'<g clip-path="url(#feed)"><g transform="translate(0 110)"><g class="feed">{feed}<g transform="translate(0 {loop})">{feed}</g></g></g></g>')
    d.defs.append(f'<linearGradient id="vfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset=".18" stop-color="{BG}" stop-opacity="0"/>'
                  f'<stop offset=".82" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient>')
    d.add(f'<rect x="{ax+1}" y="99" width="{aw-2}" height="334" rx="14" fill="url(#vfade)"/>')

    # flow connectors
    d.style("@keyframes flow{from{stroke-dashoffset:24}to{stroke-dashoffset:0}}.flow{animation:flow .8s linear infinite}")
    for x0, x1 in [(ax + aw + 8, 364), (830, 862)]:
        d.add(f'<path class="flow" d="M{x0} 266 H{x1}" stroke="{VOLT}" stroke-width="2" stroke-dasharray="6 6" stroke-linecap="round"/>')
        d.add(f'<path d="M{x1-6} 260 L{x1} 266 L{x1-6} 272" fill="none" stroke="{VOLT}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')

    # --- column B: preprocess + model
    bx, bw = 372, 450
    colhead(bx, "02", "PREPROCESS + MODEL", "clean, fold, stem, label, then learn")
    steps = ["clean", "case fold", "Sastrawi stem", "quantile label"]
    sx = bx
    pos = []
    for st in steps:
        w = MONOB.width(st, 12) + 22
        pos.append((sx, w))
        sx += w + 14
    total_w = sx - bx - 14
    scale_x = bw / total_w
    sx = bx
    for i, (st, (_, w)) in enumerate(zip(steps, pos)):
        w2 = w * scale_x
        d.add(rect(sx, 98, w2, 32, 9, fill=BG, stroke=LINE, stroke_width=1.2))
        d.add(d.text(st, sx + w2 / 2, 118.5, 12, MONOB, fill=MUTED, anchor="middle"))
        p = 5 + i * 9
        d.style(f"@keyframes pp{i}{{0%,{p}%{{opacity:0}}{p+2}%,88%{{opacity:1}}94%,100%{{opacity:0}}}}.pp{i}{{animation:pp{i} {D}s linear infinite}}")
        d.add(f'<g class="pp{i}">{rect(sx, 98, w2, 32, 9, fill=VOLT)}{d.text(st, sx + w2/2, 118.5, 12, MONOB, fill=INK, anchor="middle")}</g>')
        if i < len(steps) - 1:
            d.add(arrow_right(sx + w2 + 2, 114, 9, DIM, 1.6))
        sx += w2 + 14 * scale_x

    # Conv1D: token cells with a sliding kernel
    cy = 160
    d.add(d.text("Conv1D", bx, cy + 4, 12, MONOB, fill=TEXT))
    cells = 16
    cwid = (bw - 90) / cells
    for i in range(cells):
        shade = ["#22262D", "#2B3038", "#343A44"][(i * 7) % 3]
        d.add(rect(bx + 90 + i * cwid, cy - 12, cwid - 3, 22, 4, fill=shade))
    kw = cwid * 3
    d.style(f"@keyframes kern{{0%{{transform:translateX(0)}}100%{{transform:translateX({num(cwid*(cells-3))}px)}}}}"
            f".kern{{animation:kern 3s steps({cells-3}) infinite alternate}}")
    d.add(f'<g class="kern"><rect x="{num(bx+88)}" y="{cy-15}" width="{num(kw+1)}" height="28" rx="6" fill="{VOLT}" fill-opacity=".16" stroke="{VOLT}" stroke-width="2"/></g>')

    # BiLSTM: forward and backward pulses
    ly = 232
    d.add(d.text("BiLSTM", bx, ly + 4, 12, MONOB, fill=TEXT))
    nodes = 7
    nx0 = bx + 106
    step = (bw - 120) / (nodes - 1)
    for row, (yy, col, dirn) in enumerate([(ly - 14, VOLT, 1), (ly + 22, CORAL, -1)]):
        d.add(f'<line x1="{nx0}" y1="{yy}" x2="{num(nx0 + step*(nodes-1))}" y2="{yy}" stroke="{LINE}" stroke-width="2"/>')
        for i in range(nodes):
            d.add(f'<circle cx="{num(nx0 + i*step)}" cy="{yy}" r="9" fill="{PANEL2}" stroke="{LINE}" stroke-width="1.5"/>')
            delay = (i if dirn > 0 else nodes - 1 - i) * 0.22
            d.style(f"@keyframes ls{row}{{0%{{opacity:0;transform:scale(.4)}}12%{{opacity:1;transform:scale(1)}}40%,100%{{opacity:0;transform:scale(.6)}}}}"
                    f".ls{row}{{animation:ls{row} 1.54s ease-out infinite}}")
            d.add(f'<circle class="fb ls{row}" style="animation-delay:{delay:.2f}s" cx="{num(nx0 + i*step)}" cy="{yy}" r="9" fill="{col}"/>')
        ax2 = nx0 + step * (nodes - 1) + 16 if dirn > 0 else nx0 - 16
        d.add(arrow_right(ax2, yy, 8, col, 2) if dirn > 0 else
              f'<path d="M{num(ax2)} {yy} l-8 0 M{num(ax2-5)} {yy-3} L{num(ax2-8)} {yy} L{num(ax2-5)} {yy+3}" fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    d.add(d.text("fwd", nx0 - 62, ly - 10, 10, MONO, fill=VOLT))
    d.add(d.text("bwd", nx0 - 62, ly + 26, 10, MONO, fill=CORAL))

    # Attention heatmap
    hy = 300
    d.add(d.text("Attention", bx, hy + 16, 12, MONOB, fill=TEXT))
    rows_, cols_ = 4, 16
    hw = (bw - 90) / cols_
    rh = 112 / rows_ - 4
    rnd2 = random.Random(9)
    for r in range(rows_):
        for c in range(cols_):
            base_o = 0.08 + 0.85 * math.exp(-((c - 9 - r) ** 2) / 6)
            dur = 1.6 + rnd2.random() * 2.2
            delay = -rnd2.random() * 3
            d.add(f'<rect class="hm" style="animation-duration:{dur:.2f}s;animation-delay:{delay:.2f}s" x="{num(bx + 90 + c*hw)}" y="{num(hy + r*(rh+4))}" '
                  f'width="{num(hw-3)}" height="{num(rh)}" rx="3" fill="{SKY}" opacity="{base_o:.2f}"/>')
    d.style("@keyframes hm{0%,100%{fill-opacity:1}50%{fill-opacity:.35}}.hm{animation:hm 2s ease-in-out infinite}")
    d.add(d.text("softmax weights over tokens", bx + 90, hy + 132, 11, MONO, fill=DIM))

    # --- column C: model shoot-out
    cx0, cwid2 = 870, 294
    colhead(cx0, "03", "RESULT", "4 architectures compared")
    models = ["CNN", "LSTM", "BiLSTM", "CNN + BiLSTM + Attention"]
    for i, m in enumerate(models):
        y = 98 + i * 44
        d.add(rect(cx0, y, cwid2, 36, 10, fill=BG, stroke=LINE, stroke_width=1.2))
        d.add(d.text(m, cx0 + 16, y + 23, 13, MONOB, fill=MUTED))
    # scanning highlight that settles on the hybrid
    stops = "0%{transform:translateY(0);opacity:0}4%{opacity:1}"
    for i in range(4):
        stops += f"{8 + i*12}%{{transform:translateY({i*44}px)}}"
    stops += "60%,90%{transform:translateY(132px);opacity:1}96%,100%{transform:translateY(132px);opacity:0}"
    d.style(f"@keyframes scan{{{stops}}}.scan{{animation:scan {D}s {INOUT} infinite}}")
    d.add(f'<g class="scan"><rect x="{cx0-2}" y="96" width="{cwid2+4}" height="40" rx="11" fill="none" stroke="{VOLT}" stroke-width="2"/></g>')
    d.style(f"@keyframes win{{0%,46%{{opacity:0}}50%,90%{{opacity:1}}96%,100%{{opacity:0}}}}.win{{animation:win {D}s linear infinite}}")
    wy = 98 + 3 * 44
    d.add(f'<g class="win">{rect(cx0, wy, cwid2, 36, 10, fill=VOLT)}{d.text(models[3], cx0 + 16, wy + 23, 13, MONOB, fill=INK)}'
          + rect(cx0 + cwid2 - 52, wy + 9, 40, 18, 5, fill=INK) + d.text("WIN", cx0 + cwid2 - 32, wy + 22, 10, MONOB, fill=VOLT, anchor="middle") + "</g>")
    # big number
    d.add(d.text("75%", cx0 - 4, 368, 84, DISP, fill=TEXT))
    d.add(d.text("accuracy", cx0 + DISP.width("75%", 84) + 4, 368, 32, SERIF, fill=VOLT))
    d.add(d.text("0.76 macro F1 · deployed on Streamlit", cx0, 404, 12, MONO, fill=MUTED))
    d.style(f"@keyframes bar{{0%,50%{{transform:scaleX(0)}}62%,92%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}}}"
            f".bar{{animation:bar {D}s {OUTQ} infinite;transform-box:fill-box;transform-origin:left center}}")
    d.add(rect(cx0, 422, cwid2, 6, 3, fill=LINE))
    d.add(f'<rect class="bar" x="{cx0}" y="422" width="{num(cwid2*0.75)}" height="6" rx="3" fill="{VOLT}"/>')
    save("thesis.svg", d)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def footer() -> None:
    W, H = 1200, 380
    D = 8
    d = Doc(W, H, "Open to remote opportunities: feel free to reach out.",
            "A closing panel: open to remote opportunities, feel free to reach out. A cursor named You clicks a Say hello "
            "button and a burst of confetti pops out.")
    d.defs.append(dots_pattern("dots", 24))
    d.style(BASE_CSS)
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=BG, stroke=LINE, stroke_width=1.5))
    d.add(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22" fill="url(#dots)"/>')
    d.style("@keyframes pulse{0%{transform:scale(1);opacity:.7}100%{transform:scale(3.2);opacity:0}}.pulse{animation:pulse 1.8s ease-out infinite}")
    d.add(f'<circle cx="54" cy="66" r="5" fill="{VOLT}"/><circle class="fb pulse" cx="54" cy="66" r="5" fill="{VOLT}"/>')
    d.add(d.text("STATUS · AVAILABLE FOR REMOTE WORK", 70, 70.5, 13, MONOB, fill=VOLT, ls=1))
    d.add(d.text("Open to remote", 44, 172, 92, DISP, fill=TEXT))
    d.add(d.text("opportunities.", 46, 262, 104, SERIF, fill=VOLT))
    d.add(d.text("feel free to reach out · fatihaljabar@gmail.com", 48, 326, 15, MONO, fill=MUTED))
    # button
    bx, by, bw, bh = 862, 196, 268, 76
    d.style(f"@keyframes press{{0%,34%{{transform:scale(1)}}37%{{transform:scale(.92)}}42%,100%{{transform:scale(1)}}}}.press{{animation:press {D}s ease-out infinite}}")
    d.add(f'<g class="fb press">{rect(bx, by, bw, bh, 22, fill=VOLT)}'
          + d.text("Say hello", bx + 34, by + 47, 28, DISP, fill=INK)
          + arrow_ne(bx + bw - 58, by + 26, 22, INK, 3) + "</g>")
    # confetti
    rnd = random.Random(4)
    cx, cy = bx + bw / 2, by + bh / 2
    pieces = ""
    styles = ""
    colors = [VOLT, CORAL, SKY, TEXT]
    for i in range(22):
        ang = -math.pi / 2 + (rnd.random() - 0.5) * math.pi * 1.6
        dist = 120 + rnd.random() * 120
        dx, dy = math.cos(ang) * dist, math.sin(ang) * dist
        rot = rnd.randint(-360, 360)
        col = colors[i % 4]
        shape = (f'<rect x="-5" y="-3" width="10" height="6" rx="1.5" fill="{col}"/>' if i % 3 else f'<circle r="4.5" fill="{col}"/>')
        styles += (f"@keyframes cf{i}{{0%,36%{{transform:translate(0,0) rotate(0);opacity:0}}37%{{opacity:1}}"
                   f"62%{{transform:translate({dx:.0f}px,{dy+70:.0f}px) rotate({rot}deg);opacity:1}}72%,100%{{transform:translate({dx*1.05:.0f}px,{dy+130:.0f}px) rotate({rot*1.3:.0f}deg);opacity:0}}}}"
                   f".cf{i}{{animation:cf{i} {D}s cubic-bezier(.2,.8,.4,1) infinite}}")
        pieces += f'<g class="cf{i}">{shape}</g>'
    d.style(styles)
    d.add(f'<g transform="translate({num(cx)} {num(cy)})">{pieces}</g>')
    # visitor cursor
    tx, ty = bx + bw * 0.62, by + bh * 0.58
    d.style(f"@keyframes you{{0%,8%{{transform:translate(260px,200px)}}30%,52%{{transform:translate(0,0)}}74%,100%{{transform:translate(260px,200px)}}}}"
            f".you{{animation:you {D}s {INOUT} infinite}}")
    d.add(f'<g transform="translate({num(tx)} {num(ty)})"><g class="you">{cursor(d, CORAL, "You")}</g></g>')
    d.add(d.text("hand-written SVG + CSS · no JavaScript", W - 40, H - 30, 11, MONO, fill=DIM, anchor="end"))
    save("footer.svg", d)


def build_all() -> None:
    for slug, idx, word, serif, kicker in SECTIONS:
        for theme in ("dark", "light"):
            section_header(slug, idx, word, serif, kicker, theme)
    for i, (name, label, prefix) in enumerate([("nav-work", "Projects", "01 "), ("nav-stack", "Stack", "02 "),
                                               ("nav-thesis", "Thesis", "03 "), ("nav-certs", "Certifications", "04 "),
                                               ("nav-stats", "Stats", "05 ")]):
        button(name, label, "", "down", prefix=prefix, delay=i * 0.35)
    for i, (name, label, lead) in enumerate([("linkedin", "LinkedIn", "linkedin"), ("email", "Email", "mail"),
                                             ("instagram", "Instagram", "instagram")]):
        button(name, label, lead, "ne", delay=1.5 + i * 0.35)
    for i, (name, label, lead) in enumerate([("demo", "Live demo", "play"), ("source", "Source code", "code"),
                                             ("article", "Article", "paper")]):
        button(name, label, lead, "ne", delay=i * 0.35)
    odometer()
    marquee()
    thesis()
    footer()
