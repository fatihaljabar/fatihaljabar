"""Tech stack as three conveyor belts carrying real logos.

One belt speed v drives a whole row: the tags ride the top run at v, the cleat
marks on the top run move with them, the return run underneath moves the other
way, and both rollers turn at omega = v / R so the belt never slips.

Tags come in through a hard clip at the tail end of the belt. At the head end
they tip over the drive roller like real parcels: once a tag's centre of mass
passes the roller's top tangent point it pivots about the roller centre, a
quarter turn over pi*R/2 of belt travel (the same omega as the roller), and
leaves through the clip at the end of the belt.

Every belt carries eight headline tools, few enough that all of them sit fully
on the belt in the rest frame, which is also the static (reduced-motion) frame
and the first frame at page load. The full list lives in toolbox.svg.
"""

from __future__ import annotations

import json
import math
import os

from svgkit import Doc, num, rect
from theme import *  # noqa: F403

LOGOS = json.load(open(os.path.join(os.path.dirname(__file__), "data", "logos.json")))

# (heading, belt speed in px/s, [(label, Simple Icons slug or None)])
# None means the tool has no official mark (or only a wordmark): a text-only tag.
ROWS = [
    ("Front-end", 40.0, [("TypeScript", "typescript"), ("React", "react"), ("Next.js", "nextdotjs"),
                         ("Vue.js", "vuedotjs"), ("Tailwind CSS", "tailwindcss"), ("Framer Motion", "framer"),
                         ("TanStack Query", "tanstack"), ("Vite", "vite")]),
    ("Back-end and data", 34.0, [("Node.js", "nodedotjs"), ("Express", "express"), ("Hono", "hono"),
                                 ("Prisma", "prisma"), ("Drizzle ORM", "drizzle"), ("PostgreSQL", "postgresql"),
                                 ("Supabase", "supabase"), ("Docker", "docker")]),
    ("Machine learning and tooling", 44.0, [("Python", "python"), ("TensorFlow", "tensorflow"),
                                            ("PyTorch", "pytorch"), ("scikit-learn", "scikitlearn"),
                                            ("pandas", "pandas"), ("Streamlit", "streamlit"), ("Vitest", "vitest"),
                                            ("GitHub Actions", "githubactions")]),
]

W = 1200
X0, X1 = 52, 1148  # roller centres: X0 tail, X1 head (drive)
R = 17  # belt radius around a roller (outer surface at R + 0.7)
CL, CR = X0 - R, X1 + R  # hard clip lines at the ends of the belt
REST_X = CL + 5  # left edge of the first tag in the rest frame, and of the heading
ROW_H = 140
BELT0 = 106  # top surface of the first belt

TAG_H = 40
TAG_GAP = 8
PAD_L, ICON, ICON_GAP, PAD_R = 12, 20, 9, 12
LABEL = 17
LIFT = 1.3  # belt stroke half width plus tag stroke half width: the tag rests on the rubber
TIP = math.pi * R / 2  # belt travel during the quarter turn over the drive roller

# Belt and rollers are rubber and metal: the same dark parts in both themes.
RUBBER, RUBBER_EDGE = "#15181C", "#30353D"
CLEAT, CLEAT_RET = "#3D434C", "#2A2F36"
ROLL, ROLL_EDGE, SPOKE, HUB = "#1E2228", "#3A3F48", "#4A505B", "#2F343C"


def tag_width(name: str, slug: str | None) -> float:
    tw = SEMI.width(name, LABEL)
    return (PAD_L + ICON + ICON_GAP + tw + PAD_R) if slug else (PAD_L + tw + PAD_R)


def tag(d: Doc, name: str, slug: str | None, y_bottom: float) -> str:
    """A tag drawn with its left edge at x = 0 and its bottom edge at y_bottom."""
    w = tag_width(name, slug)
    y = y_bottom - TAG_H
    out = rect(0, y, w, TAG_H, 9, fill=PANEL2, stroke=LINE2, stroke_width=1.2)
    x = PAD_L
    if slug:
        k = ICON / 24
        out += (f'<path transform="translate({num(x)} {num(y + (TAG_H - ICON) / 2)}) scale({k:.4f})" '
                f'd="{LOGOS[slug]["path"]}" fill="{TEXT}"/>')
        x += ICON + ICON_GAP
    out += d.text(name, x, y + TAG_H / 2 + 6, LABEL, SEMI, fill=TEXT)
    return out


def pct(v: float) -> str:
    s = f"{v * 100:.3f}".rstrip("0").rstrip(".")
    return (s or "0") + "%"


def build() -> None:
    H = BELT0 + ROW_H * (len(ROWS) - 1) + 2 * R + 36
    d = Doc(W, H, "Tech stack on three conveyor belts",
            "Three conveyor belts carry the headline tools, eight per belt; the toolbox lists every tool. "
            + " ".join(f"{label}: {', '.join(n for n, _ in items)}." for label, _, items in ROWS))
    d.style(BASE_CSS)
    d.defs.append(f'<clipPath id="run"><rect x="{CL}" y="0" width="{CR - CL}" height="{H}"/></clipPath>')
    d.defs.append(f'<clipPath id="flat"><rect x="{X0}" y="0" width="{X1 - X0}" height="{H}"/></clipPath>')
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))

    for ri, (label, v, items) in enumerate(ROWS):
        belt = BELT0 + ri * ROW_H  # top surface of the belt
        cy = belt + R  # roller centres
        d.add(d.text(label, REST_X, belt - TAG_H - LIFT - 16, 18, SEMI, fill=TEXT))

        # ---- belt, cleats and rollers (top run moves right at v, return run left)
        d.add(rect(X0 - R, belt, X1 - X0 + 2 * R, 2 * R, R, fill=RUBBER, stroke=RUBBER_EDGE, stroke_width=1.4))
        period = 28.0
        n = int((X1 - X0) / period) + 3
        top = "".join(f"M{num(X0 + i * period)} {num(belt + 1.5)}v4" for i in range(-1, n))
        ret = "".join(f"M{num(X0 + i * period)} {num(belt + 2 * R - 5.5)}v4" for i in range(-1, n))
        t_cleat = period / v
        d.style(f"@keyframes c{ri}{{from{{transform:translateX(-{num(period)}px)}}to{{transform:translateX(0)}}}}"
                f"@keyframes cr{ri}{{from{{transform:translateX(0)}}to{{transform:translateX(-{num(period)}px)}}}}"
                f".c{ri}{{animation:c{ri} {t_cleat:.4f}s linear infinite}}"
                f".cr{ri}{{animation:cr{ri} {t_cleat:.4f}s linear infinite}}")
        d.add(f'<g clip-path="url(#flat)"><g class="c{ri}"><path d="{top}" stroke="{CLEAT}" stroke-width="2"/></g>'
              f'<g class="cr{ri}"><path d="{ret}" stroke="{CLEAT_RET}" stroke-width="2"/></g></g>')
        omega = v / R * 180 / math.pi  # deg/s, clockwise: the top run moves right
        d.style(f"@keyframes rot{ri}{{to{{transform:rotate(360deg)}}}}"
                f".rot{ri}{{transform-box:fill-box;transform-origin:center;"
                f"animation:rot{ri} {360 / omega:.4f}s linear infinite}}")
        for cx in (X0, X1):
            spokes = "".join(f'<path d="M0 0L0 {-R + 5}" stroke="{SPOKE}" stroke-width="2" transform="rotate({a})"/>'
                             for a in (0, 90, 180, 270))
            d.add(f'<g transform="translate({cx} {cy})"><circle r="{R - 1.5}" fill="{ROLL}" stroke="{ROLL_EDGE}" '
                  f'stroke-width="1.2"/><g class="rot{ri}"><circle r="{R - 1.5}" fill="none"/>{spokes}</g>'
                  f'<circle r="4.5" fill="{HUB}" stroke="{SPOKE}"/></g>')

        # ---- tags
        # One lap of the belt loop is long enough that every tag travels from fully
        # hidden at the tail clip to the end of its quarter turn before it comes round
        # again. While the belt runs, that slack is shared out as equal gaps. The rest
        # frame (static and reduced-motion) packs the same tags TAG_GAP apart from the
        # tail end so the whole row is on the belt at once.
        widths = [tag_width(nm, sl) for nm, sl in items]
        rest_w = sum(widths) + TAG_GAP * (len(items) - 1)
        assert REST_X + rest_w <= CR - 4, (label, rest_w)
        lap = max((X1 - CL) + w / 2 + TIP for w in widths) + 4
        gap = (lap - sum(widths)) / len(items)
        assert gap >= TAG_GAP, (label, gap)
        dur = lap / v
        x_rest = REST_X
        x_run = REST_X  # where the tag is at t = 0 when the belt runs
        tags = []
        for ti, ((name, slug), w) in enumerate(zip(items, widths)):
            assert x_rest + w / 2 < X1, name  # at rest the centre of mass is on the flat run
            x_in = CL - w - X1  # entry: right edge on the tail clip (pivot frame)
            x_tip = -w / 2  # centre over the drive roller's top tangent point
            pa = (x_tip - x_in) / lap
            pb = pa + TIP / lap
            phase = ((x_run - X1 - x_in) / lap) % 1.0
            cls = f"g{ri}{ti}"
            d.style(f"@keyframes {cls}{{0%{{transform:rotate(0deg) translateX({num(x_in)}px)}}"
                    f"{pct(pa)}{{transform:rotate(0deg) translateX({num(x_tip)}px)}}"
                    f"{pct(pb)},100%{{transform:rotate(90deg) translateX({num(x_tip)}px)}}}}"
                    f".{cls}{{animation:{cls} {dur:.3f}s linear -{phase * dur:.3f}s infinite}}")
            # The pivot frame sits on the drive roller centre. The rest position is the
            # transform attribute, which the CSS animation overrides while it runs.
            tags.append(f'<g class="{cls}" transform="translate({num(x_rest - X1)} 0)">'
                        f'{tag(d, name, slug, -(R + LIFT))}</g>')
            x_rest += w + TAG_GAP
            x_run += w + gap
        d.add(f'<g clip-path="url(#run)"><g transform="translate({X1} {cy})">{"".join(tags)}</g></g>')

    save("stack.svg", d)
