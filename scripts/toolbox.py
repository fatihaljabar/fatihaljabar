"""The full toolbox: every tool from the profile, grouped, as a grid of keycaps.

It replaces a wall of shields.io badges. Each key carries the tool's official
Simple Icons mark in the text colour, or no mark at all when the tool has none
(a borrowed logo is worse than none). The group heading runs in as the first
cell of its group, so a group of n tools fills n + 1 cells of the six-column grid.

The one moving part: now and then a single key is pressed and springs back
against its top stop, the same keystroke as the README's buttons. Every key
rests at the identity transform, so the static (reduced-motion) frame is the
grid at rest.
"""

from __future__ import annotations

import json
import os

from svgkit import Doc, num, rect
from theme import *  # noqa: F403

LOGOS = json.load(open(os.path.join(os.path.dirname(__file__), "data", "logos.json")))

# Exactly the tools of the old badge wall (README at d0ea1ad), names fixed.
# The slug is the tool's own Simple Icons mark; None when it has no official mark
# there (MySQL's mark is a wordmark that turns into a smudge at 22 px, so it is set
# in type too). Vue Router, Supabase Auth, Google Identity Services and Cloudflare R2
# are first-party products of the brand whose mark they carry.
GROUPS = [
    ("Languages", [("TypeScript", "typescript"), ("JavaScript", "javascript"), ("Python", "python"),
                   ("HTML5", "html5"), ("CSS", "css")]),
    ("Front-end", [("React", "react"), ("Next.js", "nextdotjs"), ("Tailwind CSS", "tailwindcss"),
                   ("Radix UI", "radixui"), ("shadcn/ui", "shadcnui"), ("Framer Motion", "framer"),
                   ("Zustand", None), ("TanStack Query", "tanstack"), ("Recharts", None), ("Vite", "vite"),
                   ("React Router", "reactrouter"), ("Vue.js", "vuedotjs"), ("Bootstrap", "bootstrap"),
                   ("Vue Router", "vuedotjs"), ("Lucide", "lucide"), ("React Icons", None), ("next-intl", None),
                   ("next-themes", None), ("jsPDF", None)]),
    ("Back-end", [("Node.js", "nodedotjs"), ("Express", "express"), ("Hono", "hono"), ("Prisma", "prisma"),
                  ("Drizzle ORM", "drizzle"), ("Auth.js", None), ("Zod", "zod"),
                  ("Google Identity", "google"), ("aws4fetch", None), ("Resend", "resend"),
                  ("JWT", "jsonwebtokens"), ("bcrypt", None), ("Supabase Auth", "supabase"), ("Midtrans", None),
                  ("API.co.id", None), ("React Email", None), ("Tesseract.js", None)]),
    ("Databases and infra", [("PostgreSQL", "postgresql"), ("MySQL", None), ("MariaDB", "mariadb"),
                             ("MongoDB", "mongodb"), ("Supabase", "supabase"), ("Vercel", "vercel"),
                             ("Cloudflare R2", "cloudflare"), ("Hostinger", "hostinger"), ("Netlify", "netlify"),
                             ("Docker", "docker")]),
    ("Machine learning", [("TensorFlow", "tensorflow"), ("Keras", "keras"), ("PyTorch", "pytorch"),
                          ("scikit-learn", "scikitlearn"), ("pandas", "pandas"), ("NumPy", "numpy"),
                          ("Streamlit", "streamlit"), ("Jupyter", "jupyter"), ("Hugging Face", "huggingface"),
                          ("NLTK", None), ("Sastrawi", None)]),
    ("Testing and tooling", [("Git", "git"), ("GitHub", "github"), ("Playwright", None), ("ESLint", "eslint"),
                             ("Biome", "biome"), ("Postman", "postman"), ("Figma", "figma"),
                             ("Claude Code", "claudecode"), ("Codex", None), ("Vitest", "vitest"),
                             ("GitHub Actions", "githubactions")]),
]
FULL_NAMES = {"Google Identity": "Google Identity Services"}

W = 1200
PAD_X, PAD_TOP = 24, 28
COLS, COL_GAP = 6, 8
CELL = (W - 2 * PAD_X - (COLS - 1) * COL_GAP) / COLS
CAP_H, SKIRT, ROW_GAP = 40, 3, 8
PITCH = CAP_H + SKIRT + ROW_GAP
GROUP_GAP = 18  # space above and below the hairline between groups
ICON, ICON_X, ICON_GAP, PAD_R = 22, 13, 10, 9
LABEL, HEAD = 17, 18

# Keycaps from the theme tokens: the cap is the lightest surface in light mode and a
# raised panel in dark mode; the skirt below it is the shadow side.
DARK = THEME == "dark"
FACE = PANEL2 if DARK else BG
FACE_EDGE = LINE2
BASE = BG if DARK else LINE
BASE_EDGE = LINE if DARK else LINE2

# The keystroke: one key at a time, every STEP seconds, cycling through these tools.
PRESSED = ["TypeScript", "Next.js", "PostgreSQL", "TensorFlow"]
STEP = 6.5
PERIOD = STEP * len(PRESSED)
RISE = "cubic-bezier(.33,.67,.67,1)"  # launched upward, decelerating
SMOOTH = "cubic-bezier(.45,0,.55,1)"


def _pct(t: float) -> str:
    s = f"{t / PERIOD * 100:.3f}".rstrip("0").rstrip(".")
    return (s or "0") + "%"


def press_css() -> str:
    """The finger drives the cap down onto the skirt (a hard stop: it lands there
    and goes no further), holds it for 130 ms and lets go. The switch spring throws
    the cap up against its top stop; it rebounds 0.6 px and is at rest 110 ms after
    the hit. Each pressed key runs the same keyframes, STEP seconds apart."""
    at, depth = 0.8, SKIRT

    def y(v: float) -> str:
        return f"transform:translateY({num(v)}px)"

    t_hit = at + 0.07 + 0.13 + 0.07
    frames = [
        (0, y(0), None),
        (at, y(0), "cubic-bezier(.5,0,.75,0)"),
        (at + 0.07, y(depth), None),
        (at + 0.20, y(depth), "cubic-bezier(.36,0,.6,.37)"),
        (t_hit, y(0), RISE),
        (t_hit + 0.035, y(0.6), SMOOTH),
        (t_hit + 0.11, y(0), None),
        (PERIOD, y(0), None),
    ]
    body = "".join(f"{_pct(t)}{{{decl}" + (f";animation-timing-function:{tf}" if tf else "") + "}"
                   for t, decl, tf in frames)
    css = f"@keyframes press{{{body}}}.press{{animation:press {PERIOD}s linear infinite}}"
    css += "".join(f".p{i}{{animation-delay:{num(i * STEP)}s}}" for i in range(len(PRESSED)))
    return css


def ordered(items):
    """Tools with a mark first, then the ones set in type; each in the README's order."""
    return [t for t in items if t[1]] + [t for t in items if not t[1]]


def build() -> None:
    # ---- lay out the cells: heading cell first, then the tools, six to a row
    cells = []  # (group index, row within the whole grid, column, payload)
    row = 0
    for gi, (head, items) in enumerate(GROUPS):
        seq = [("head", head)] + [("tool", t) for t in ordered(items)]
        for k, c in enumerate(seq):
            cells.append((gi, row + k // COLS, k % COLS, c))
        row += (len(seq) + COLS - 1) // COLS
    n_tools = sum(len(items) for _, items in GROUPS)

    def row_y(gi: int, r: int) -> float:
        return PAD_TOP + r * PITCH + gi * (2 * GROUP_GAP + 1 - ROW_GAP)

    last_gi, last_r = cells[-1][0], cells[-1][1]
    grid_bottom = row_y(last_gi, last_r) + CAP_H + SKIRT
    H = grid_bottom + GROUP_GAP + 1 + GROUP_GAP + 16 + 26

    d = Doc(W, H, f"Toolbox: {n_tools} tools in six groups",
            f"{n_tools} tools. " + " ".join(
                f"{head}: {', '.join(FULL_NAMES.get(n, n) for n, _ in items)}." for head, items in GROUPS))
    d.style(BASE_CSS)
    d.style(press_css())
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))

    used = sorted({slug for _, items in GROUPS for _, slug in items if slug})
    for slug in used:
        d.defs.append(f'<path id="i-{slug}" d="{LOGOS[slug]["path"]}"/>')

    def hairline(y: float) -> str:
        return f'<path d="M{PAD_X} {num(y)}H{W - PAD_X}" stroke="{LINE}" stroke-width="1"/>'

    for gi in range(1, len(GROUPS)):
        first_r = min(r for g, r, _, _ in cells if g == gi)
        d.add(hairline(row_y(gi, first_r) - GROUP_GAP - 0.5))

    k_icon = ICON / 24
    pressed_i = 0
    for gi, r, c, (kind, payload) in cells:
        x = PAD_X + c * (CELL + COL_GAP)
        y = row_y(gi, r)
        base_line = y + CAP_H / 2 + 6
        if kind == "head":
            d.add(d.text(payload, x, base_line, HEAD, SEMI, fill=TEXT))
            continue
        name, slug = payload
        cap = rect(x, y, CELL, CAP_H, 9, fill=FACE, stroke=FACE_EDGE, stroke_width=1.2)
        lx = x + ICON_X
        if slug:
            cap += (f'<use xlink:href="#i-{slug}" fill="{TEXT}" transform="translate({num(lx)} '
                    f'{num(y + (CAP_H - ICON) / 2)}) scale({k_icon:.4f})"/>')
            lx += ICON + ICON_GAP
        assert lx + SEMI.width(name, LABEL) <= x + CELL - PAD_R, name
        cap += d.text(name, lx, base_line, LABEL, SEMI, fill=TEXT)
        skirt = rect(x, y + SKIRT, CELL, CAP_H, 9, fill=BASE, stroke=BASE_EDGE, stroke_width=1)
        if name in PRESSED:
            cap = f'<g class="press p{PRESSED.index(name)}">{cap}</g>'
            pressed_i += 1
        d.add(skirt + cap)
    assert pressed_i == len(PRESSED)

    y_rule = grid_bottom + GROUP_GAP
    d.add(hairline(y_rule + 0.5))
    d.add(d.text(f"{n_tools} tools. Logos are the official marks from Simple Icons; a tool without one is set in type.",
                 PAD_X, y_rule + 1 + GROUP_GAP + 13, 16, BODY, fill=MUTED))

    save("toolbox.svg", d)
    print(f"toolbox: {n_tools} tools, {len(used)} distinct marks, "
          f"{sum(1 for _, it in GROUPS for _, s in it if not s)} set in type")
