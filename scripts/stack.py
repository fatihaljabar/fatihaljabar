"""Tech stack as three conveyor belts carrying real logos.

Belt speed v drives everything: the tags, the cleats on the top run, the
return run underneath (opposite direction) and the rollers, which turn at
omega = v / r so the belt never slips.
"""

from __future__ import annotations

import json
import math
import os

from svgkit import Doc, num, rect
from theme import *  # noqa: F403

LOGOS = json.load(open(os.path.join(os.path.dirname(__file__), "data", "logos.json")))

ROWS = [
    ("Front-end", 40.0, [("TypeScript", "typescript"), ("React", "react"), ("Next.js", "nextdotjs"), ("Vue.js", "vuedotjs"),
                         ("Tailwind CSS", "tailwindcss"), ("Framer Motion", "framer"), ("TanStack Query", "reactquery"),
                         ("Zustand", None), ("Radix UI", "radixui"), ("shadcn/ui", "shadcnui"), ("Vite", "vite"),
                         ("React Router", "reactrouter"), ("Recharts", None), ("JavaScript", "javascript"), ("HTML5", "html5"),
                         ("CSS", "css")]),
    ("Back-end and data", -32.0, [("Node.js", "nodedotjs"), ("Express", "express"), ("Hono", "hono"), ("Prisma", "prisma"),
                                  ("Drizzle ORM", "drizzle"), ("PostgreSQL", "postgresql"), ("MariaDB", "mariadb"), ("MySQL", "mysql"),
                                  ("Supabase", "supabase"), ("MongoDB", "mongodb"), ("Zod", "zod"), ("Cloudflare R2", "cloudflare"),
                                  ("Resend", "resend"), ("JWT", "jsonwebtokens"), ("Docker", "docker"), ("Vercel", "vercel"),
                                  ("Netlify", "netlify")]),
    ("Machine learning and tooling", 46.0, [("Python", "python"), ("TensorFlow", "tensorflow"), ("Keras", "keras"), ("PyTorch", "pytorch"),
                                            ("scikit-learn", "scikitlearn"), ("pandas", "pandas"), ("NumPy", "numpy"), ("Streamlit", "streamlit"),
                                            ("Hugging Face", "huggingface"), ("Jupyter", "jupyter"), ("Playwright", None), ("Vitest", "vitest"),
                                            ("GitHub Actions", "githubactions"), ("Biome", "biome"), ("ESLint", "eslint"), ("Figma", "figma"),
                                            ("Claude Code", "claude"), ("Git", "git")]),
]

X0, X1 = 58, 1142  # roller centres
R = 17
ROW_H = 140
TOP = 66


def logo(slug: str | None, name: str, x: float, y: float, s: float, d: Doc) -> str:
    """Simple Icons are drawn on a 24 x 24 grid."""
    if slug:
        k = s / 24
        return f'<path transform="translate({num(x)} {num(y)}) scale({k:.4f})" d="{LOGOS[slug]["path"]}" fill="{TEXT}"/>'
    letters = "".join(w[0] for w in name.split()[:2]).upper() if " " in name else name[:2].upper()
    return (rect(x, y, s, s, 4, fill="none", stroke=TEXT, stroke_width=1.4)
            + d.text(letters, x + s / 2, y + s / 2 + 3.2, 8.5, MONOB, fill=TEXT, anchor="middle"))


def build() -> None:
    W = 1200
    H = TOP + ROW_H * len(ROWS) - 18
    d = Doc(W, H, "Tech stack on three conveyor belts",
            "Three conveyor belts carry technology logos: front-end, back-end and data, machine learning and tooling. "
            + " ".join(f"{label}: {', '.join(n for n, _ in items)}." for label, _, items in ROWS))
    d.style(BASE_CSS)
    d.defs.append(f'<clipPath id="panel"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22"/></clipPath>')
    d.defs.append('<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".035" stop-color="#fff"/><stop offset=".965" stop-color="#fff"/>'
                  '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    d.defs.append(f'<mask id="ends" maskUnits="userSpaceOnUse" x="{X0}" y="0" width="{X1-X0}" height="{H}">'
                  f'<rect x="{X0}" y="0" width="{X1-X0}" height="{H}" fill="url(#edge)"/></mask>')
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))
    d.add('<g clip-path="url(#panel)">')

    for ri, (label, v, items) in enumerate(ROWS):
        belt = TOP + 52 + ri * ROW_H  # top surface of the belt
        y_label = belt - 60
        d.add(d.text(label, X0 - 14, y_label, 15, SEMI, fill=TEXT))
        d.add(d.text(f"{len(items)}", X0 - 14 + SEMI.width(label, 15) + 10, y_label, 12, MONO, fill=DIM))

        # belt body and rollers
        d.add(rect(X0 - R, belt, X1 - X0 + 2 * R, 2 * R, R, fill="#15181C", stroke="#30353D", stroke_width=1.4))
        period = 28.0
        cleats = "".join(f"M{num(X0 + i * period)} {belt + 1.5}v4" for i in range(-1, int((X1 - X0) / period) + 3))
        ret = "".join(f"M{num(X0 + i * period)} {belt + 2 * R - 5.5}v4" for i in range(-1, int((X1 - X0) / period) + 3))
        t_cleat = period / abs(v)
        sgn = "-" if v > 0 else ""
        d.style(f"@keyframes c{ri}{{from{{transform:translateX(0)}}to{{transform:translateX({sgn}{period}px)}}}}"
                f"@keyframes cr{ri}{{from{{transform:translateX(0)}}to{{transform:translateX({'' if v > 0 else '-'}{period}px)}}}}"
                f".c{ri}{{animation:c{ri} {t_cleat:.3f}s linear infinite}}.cr{ri}{{animation:cr{ri} {t_cleat:.3f}s linear infinite}}")
        d.add(f'<g mask="url(#ends)"><g class="c{ri}"><path d="{cleats}" stroke="#3D434C" stroke-width="2"/></g>'
              f'<g class="cr{ri}"><path d="{ret}" stroke="#2A2F36" stroke-width="2"/></g></g>')
        omega = abs(v) / R * 180 / math.pi  # deg per second
        turn = -360 if v > 0 else 360  # top run moving left turns the rollers anticlockwise
        d.style(f"@keyframes rot{ri}{{to{{transform:rotate({turn}deg)}}}}"
                f".rot{ri}{{transform-box:fill-box;transform-origin:center;animation:rot{ri} {360/omega:.3f}s linear infinite}}")
        for cx in (X0, X1):
            spokes = "".join(f'<path d="M0 0L0 {-R + 5}" stroke="#4A505B" stroke-width="2" transform="rotate({a})"/>' for a in (0, 90, 180, 270))
            d.add(f'<g transform="translate({cx} {belt + R})"><circle r="{R - 1.5}" fill="#1E2228" stroke="#3A3F48" stroke-width="1.2"/>'
                  f'<g class="rot{ri}"><circle r="{R - 1.5}" fill="none"/>{spokes}</g>'
                  f'<circle r="4.5" fill="#2F343C" stroke="#4A505B"/></g>')

        # tags riding on the top run
        x = 0.0
        tags = ""
        for name, slug in items:
            tw = SEMI.width(name, 16)
            w = tw + 58
            tags += rect(x, 0, w, 40, 10, fill=PANEL2, stroke="#30353D", stroke_width=1.2)
            tags += logo(slug, name, x + 14, 10, 20, d)
            tags += d.text(name, x + 44, 25.5, 16, SEMI, fill=TEXT)
            x += w + 12
        row_w = x
        copies = math.ceil((X1 - X0) / row_w) + 1
        d.defs.append(f'<g id="row{ri}">{tags}</g>')
        body = "".join(f'<use xlink:href="#row{ri}" x="{num(i * row_w)}"/>' for i in range(copies + 1))
        dur = row_w / abs(v)
        if v > 0:
            kf = f"from{{transform:translateX(0)}}to{{transform:translateX(-{num(row_w)}px)}}"
        else:
            kf = f"from{{transform:translateX(-{num(row_w)}px)}}to{{transform:translateX(0)}}"
        d.style(f"@keyframes t{ri}{{{kf}}}.t{ri}{{animation:t{ri} {dur:.2f}s linear infinite}}")
        d.add(f'<g mask="url(#ends)"><g transform="translate({X0 - 20} {belt - 42})"><g class="t{ri}">{body}</g></g></g>')

    d.add("</g>")
    save("stack.svg", d)
