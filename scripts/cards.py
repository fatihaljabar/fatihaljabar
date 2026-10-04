"""Project cards built from real screenshots.

Each card embeds the project's own desktop and mobile captures (taken from a
local build of the repo, see scripts/shots/ and import_shots.py) as WebP and
reads them the way a person reads a page: a push, a glide that settles, a
pause to read, and in the end a smooth trip back to the top. Every viewport
gets its own rhythm, seeded by the card's slug, so a grid of cards never moves
in lockstep and the desktop and phone of one card drift against each other.

Scrolling is a critically damped spring: no overshoot anywhere, so a page
never shows anything above its own top or below its own end. A card that
needs several screens (pages under 900 css px) cuts between them like a page
navigation instead of gluing them into one fake long page.

The static frame (reduced motion) is the top of the first page, which is
also where every loop ends. No fake browser chrome, just the page and a hairline.
"""

from __future__ import annotations

import base64
import glob
import json
import math
import os
import random

from PIL import Image

from svgkit import Doc, num, rect, wrap
from theme import *  # noqa: F403

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.environ.get("SHOTS_DIR", os.path.join(HERE, "shots"))
LOGO_FILE = os.path.join(HERE, "data", "logos.json")

CW, CH = 600, 500
PAD = 26  # text inset
MX, MY, MW = 14, 14, 572  # media area
MB = 306  # media area bottom
MH = MB - MY
BLEED = 10  # both devices stand on the media edge and run 10 units past it

DW = 452  # desktop viewport on the card (1440 css px wide)
DH = DW * 900 / 1440
DX, DY = MX + 22, MB + BLEED - DH
PW = 124  # phone viewport (390 css px wide)
PH = PW * 844 / 390
PX, PY = MX + MW - PW - 22, MB + BLEED - PH

# Text block, bottom up: stack row, rule, three description lines, name.
NAME_SIZE, NAME_Y = 32, 349
DESC_SIZE, DESC_Y, DESC_LH, DESC_MAX = 19, 380, 24, 3
RULE_Y = 446
LOGO_SIZE, STACK_Y, STACK_SIZE = 18, 460, 16
PILL_SIZE, PILL_H = 14, 30

MIN_SCROLL = 48  # a page less than this much taller than its viewport stays still
FADE = 0.22  # a page change between screens of one flow

STATUS = {
    "prod": "In production",
    "demo": "Live demo",
    "repo": "Public repo",
    "private": "Private repo",
}


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------
def webp_data(path: str) -> tuple[str, int, int]:
    """Embed a WebP prepared by import_shots.py as it is."""
    w, h = Image.open(path).size
    with open(path, "rb") as fh:
        return "data:image/webp;base64," + base64.b64encode(fh.read()).decode(), w, h


def pages(sdir: str, stem: str) -> list[str]:
    single = os.path.join(sdir, f"{stem}.webp")
    if os.path.exists(single):
        return [single]
    return sorted(glob.glob(os.path.join(sdir, f"{stem}-*.webp")),
                  key=lambda p: int(p.rsplit("-", 1)[1].split(".")[0]))


# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------
def _pct(t: float, period: float) -> str:
    s = f"{max(0.0, min(100.0, t / period * 100)):.3f}".rstrip("0").rstrip(".")
    return (s or "0") + "%"


def glide(dist: float, points: int = 34) -> str:
    """Timing for one scroll move: the exact step response of a critically damped
    spring started from rest, x(u) = 1 - (1 + a u) e^(-a u) over the move's
    normalised time u. `a` is chosen so the page is within a quarter of a pixel of
    its stop when the move ends, so the last keyframe is an invisible snap and
    there is never any overshoot. For a move of T seconds the spring has
    stiffness (a/T)^2 and damping 2a/T per unit mass. Samples are denser near
    the start, where the curve bends hardest."""
    eps = min(0.05, 0.25 / max(dist, 1.0))
    a = 3.0
    while (1 + a) * math.exp(-a) > eps:
        a += 0.01
    stops = []
    for k in range(points + 1):
        u = (k / points) ** 1.6
        x = 1 - (1 + a * u) * math.exp(-a * u)
        if k == 0:
            stops.append("0")
        elif k == points:
            stops.append("1")
        else:
            stops.append(f"{x:.4f}".rstrip("0").rstrip(".") + f" {u * 100:.2f}".rstrip("0").rstrip(".") + "%")
    return f"animation-timing-function:{OUTQ};animation-timing-function:linear({','.join(stops)})"


def scroll_css(cls: str, content_h: float, view_h: float, rng: random.Random) -> str:
    """Read, push, read, push... then glide back to the top. Steps are 0.62 to 0.92
    of the viewport, holds 1.2 to 2.4 s, each move 0.35 s + 0.9 ms per unit of travel."""
    max_y = content_h - view_h
    if max_y < MIN_SCROLL:
        return ""
    n = max(1, min(6, round(max_y / (0.77 * view_h))))
    weights = [rng.uniform(0.62, 0.92) for _ in range(n)]
    stops, y = [], 0.0
    for w in weights:
        y += w / sum(weights) * max_y
        stops.append(y)
    stops[-1] = max_y

    frames: list[tuple[float, float, str | None]] = []  # (time, y, timing of the segment that starts here)
    t, y = rng.uniform(1.2, 2.4), 0.0
    frames.append((0.0, 0.0, None))
    for s in stops:
        move = 0.35 + 0.0009 * (s - y)
        frames.append((t, y, glide(s - y)))
        t += move
        y = s
        frames.append((t, y, None))
        t += rng.uniform(1.2, 2.4)
    move = 0.35 + 0.0009 * max_y  # the trip home: same spring, longer travel
    frames.append((t, y, glide(max_y)))
    t += move
    frames.append((t, 0.0, None))
    period = t
    offset = rng.uniform(0, 6)

    kf = []
    for ft, fy, tf in frames:
        body = f"transform:translateY({-fy:.2f}px)" if fy else "transform:translateY(0)"
        kf.append(f"{_pct(ft, period)}{{{body}{';' + tf if tf else ''}}}")
    return (f"@keyframes {cls}{{{''.join(kf)}}}"
            f".{cls}{{transform:translateY(0);animation:{cls} {period:.3f}s linear {-offset:.3f}s infinite}}")


def page_css(cls: str, n: int, rng: random.Random) -> list[str]:
    """Screens of one flow shown in order, like following links: each page holds
    2.4 to 3.6 s, the next one cuts in with a short dissolve, and the last one
    dissolves back to the first. Pages 2..n sit on top of page 1; their static
    opacity is 0, so the static frame is page 1."""
    holds = [rng.uniform(2.4, 3.6) for _ in range(n)]
    starts = [0.0]
    for i in range(1, n):
        starts.append(starts[-1] + holds[i - 1] + (FADE if i > 1 else 0.0))
    period = starts[-1] + FADE + holds[-1] + FADE
    offset = rng.uniform(0, 6)
    tf = f"animation-timing-function:{INOUT}"
    rules = []
    for i in range(1, n):
        name = f"{cls}{i}"
        a, b = starts[i], starts[i] + FADE
        kf = [f"0%{{opacity:0}}", f"{_pct(a, period)}{{opacity:0;{tf}}}", f"{_pct(b, period)}{{opacity:1}}"]
        if i < n - 1:
            # hidden under the next page once that one is fully in
            off = starts[i + 1] + FADE
            kf += [f"{_pct(off, period)}{{opacity:1;animation-timing-function:steps(1,end)}}",
                   f"{_pct(off + 0.001, period)},100%{{opacity:0}}"]
        else:
            kf += [f"{_pct(period - FADE, period)}{{opacity:1;{tf}}}", "100%{opacity:0}"]
        rules.append(f"@keyframes {name}{{{''.join(kf)}}}"
                     f".{name}{{opacity:0;animation:{name} {period:.3f}s linear {-offset:.3f}s infinite}}")
    return rules


# ---------------------------------------------------------------------------
# Card
# ---------------------------------------------------------------------------
def luminance(hex_: str) -> float:
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def viewport(d: Doc, slug: str, which: str, files: list[str], x: float, y: float, w: float, h: float,
             rx: float, hair: str) -> None:
    """One device viewport: a clip, the page image(s) and their motion, a hairline."""
    view_h = MB - y  # the part above the media edge is what a reader can see
    rng = random.Random(f"{slug}:{which}")
    cid = f"{which}v"
    d.defs.append(f'<clipPath id="{cid}"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" '
                  f'rx="{num(rx)}"/></clipPath>')
    imgs = []
    for f in files:
        src, iw, ih = webp_data(f)
        imgs.append((src, ih * w / iw))
    heights = [hh for _, hh in imgs]
    d.add(f'<g clip-path="url(#{cid})">')
    if len(files) == 1:
        css = scroll_css(f"{which}s", heights[0], view_h, rng)
        cls = f' class="{which}s"' if css else ""
        if css:
            d.style(css)
        d.add(f'<g{cls}><image x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(heights[0])}" '
              f'preserveAspectRatio="none" xlink:href="{imgs[0][0]}"/></g>')
    else:
        for i, hh in enumerate(heights):
            if hh - view_h >= MIN_SCROLL:
                raise ValueError(f"{slug}: page {i + 1} of a sequence is taller than its viewport; use one page")
        for rule in page_css(f"{which}p", len(files), rng):
            d.style(rule)
        for i, (src, hh) in enumerate(imgs):
            cls = f' class="{which}p{i}"' if i else ""
            d.add(f'<image{cls} x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(hh)}" '
                  f'preserveAspectRatio="none" xlink:href="{src}"/>')
    d.add("</g>")
    d.add(f'<rect x="{num(x - 0.5)}" y="{num(y - 0.5)}" width="{num(w + 1)}" height="{num(h + 1)}" '
          f'rx="{num(rx + 0.5)}" fill="none" {hair}/>')


def stack_row(d: Doc, items: list[tuple[str, str | None]], logos: dict, slug: str) -> None:
    """Tool logos (only official Simple Icons marks from logos.json) and names. A tool
    without a mark is set as its name alone; nothing is invented to fill the gap."""
    cy = STACK_Y + LOGO_SIZE / 2
    base = cy + SEMI.cap * STACK_SIZE / SEMI.upm / 2
    x = PAD
    parts = []
    for name, key in items:
        if key and key in logos:
            k = LOGO_SIZE / 24
            parts.append(f'<path transform="translate({num(x)} {num(STACK_Y)}) scale({k:.4f})" '
                         f'd="{logos[key]["path"]}" fill="{MUTED}"/>')
            x += LOGO_SIZE + 7
        parts.append(d.text(name, x, base, STACK_SIZE, SEMI, fill=MUTED))
        x += SEMI.width(name, STACK_SIZE) + 20
    if x - 20 > CW - PAD:
        raise ValueError(f"{slug}: stack row is {x - 20 - PAD:.0f} wide, the card has {CW - 2 * PAD}")
    d.add(*parts)


def build_card(p: dict, logos: dict) -> None:
    slug = p["slug"]
    sdir = os.path.join(SHOTS, slug)
    notes = os.path.join(sdir, "notes.json")
    meta = json.load(open(notes)) if os.path.exists(notes) else {}
    bg = p.get("bg") or meta.get("background_hex") or PANEL2
    light_page = luminance(bg) > 140
    hair = 'stroke="#000" stroke-opacity=".14"' if light_page else 'stroke="#fff" stroke-opacity=".16"'

    stack_names = ", ".join(n for n, _ in p["stack"])
    d = Doc(CW, CH, f"{p['name']}: {p['desc']}",
            f"Project card for {p['name']}, showing real screenshots of the desktop and mobile layouts. "
            f"{p['desc']} Built with {stack_names}.")
    d.add(rect(0.75, 0.75, CW - 1.5, CH - 1.5, 18, fill=PANEL, stroke=LINE, stroke_width=1.5))

    # media area in the product's own page colour, both devices standing on its bottom edge
    d.defs.append(f'<clipPath id="media"><rect x="{MX}" y="{MY}" width="{MW}" height="{MH}" rx="12"/></clipPath>')
    d.add(rect(MX, MY, MW, MH, 12, fill=bg))
    d.add('<g clip-path="url(#media)">')
    desk = pages(sdir, "desktop")
    if desk:
        viewport(d, slug, "d", desk, DX, DY, DW, DH, 8, hair)
    mob = pages(sdir, "mobile")
    if mob:
        d.add(rect(PX - 5, PY - 5, PW + 10, PH + 10, 20, fill=bg))
        viewport(d, slug, "p", mob, PX, PY, PW, PH, 16, hair)
    d.add("</g>")
    d.add(rect(MX + 0.5, MY + 0.5, MW - 1, MH - 1, 11.5, fill="none", stroke=LINE, stroke_width=1))

    # name and status
    status = STATUS[p["status"]]
    link = p["status"] != "private"
    tw = MONOB.width(status, PILL_SIZE)
    sw = tw + (48 if link else 30)
    sx = CW - PAD - sw
    cap_mid = NAME_Y - DISP.cap * NAME_SIZE / DISP.upm / 2
    sy = cap_mid - PILL_H / 2
    name_w = DISP.width(p["name"], NAME_SIZE)
    if PAD + name_w > sx - 16:
        raise ValueError(f"{slug}: name runs into the status pill")
    d.add(d.text(p["name"], PAD, NAME_Y, NAME_SIZE, DISP, fill=TEXT))
    d.add(rect(sx, sy, sw, PILL_H, PILL_H / 2, fill="none", stroke=LINE2, stroke_width=1.2))
    d.add(d.text(status, sx + 15, cap_mid + MONOB.cap * PILL_SIZE / MONOB.upm / 2, PILL_SIZE, MONOB, fill=TEXT))
    if link:
        d.add(arrow_ne(sx + sw - 24, cap_mid - 4.5, 9, VOLT, 1.9))

    # description
    lines = wrap(BODY, p["desc"], DESC_SIZE, CW - 2 * PAD)
    if len(lines) > DESC_MAX:
        raise ValueError(f"{slug}: description wraps to {len(lines)} lines")
    for i, ln in enumerate(lines):
        d.add(d.text(ln, PAD, DESC_Y + i * DESC_LH, DESC_SIZE, BODY, fill=MUTED))

    d.add(f'<line x1="{PAD}" y1="{RULE_Y}" x2="{CW - PAD}" y2="{RULE_Y}" stroke="{LINE}"/>')
    stack_row(d, p["stack"], logos, slug)
    save(f"card-{slug}.svg", d)


# Product names as the products call themselves; repo names live in the README spec sheet.
PROJECTS = [
    dict(slug="blockwave", name="Blockwave Studios", status="demo", href="https://blockwavestudio-demo.vercel.app",
         desc="Minecraft and Roblox asset marketplace. Designed and built solo, from the spec to a client-approved demo.",
         stack=[("React 19", "react"), ("Vite", "vite"), ("Tailwind v4", "tailwindcss"), ("Recharts", None)]),
    dict(slug="ottodot", name="Ottodot Trial Booking", status="repo", href="https://github.com/fatihaljabar/ottodot-trial-booking",
         desc="Two parents, one seat left: row-locked Postgres transactions, idempotent payments and 34 tests, one of them a real race.",
         stack=[("Next.js", "nextdotjs"), ("PostgreSQL", "postgresql"), ("Prisma", "prisma"), ("Zod", "zod"), ("Vitest", "vitest")]),
    dict(slug="tracker", name="Tracking Lamaran", status="prod", href="https://trackinglamaran.site",
         desc="Job-hunt tracker with an 11-stage pipeline, 14 fields per application, deadline and interview reminders, and stats.",
         stack=[("React", "react"), ("Express", "express"), ("Drizzle", "drizzle"), ("Cloudflare R2", "cloudflare"), ("Resend", "resend")]),
    dict(slug="splitbill", name="SplitBills", status="prod", href="https://splitbills.site",
         desc="Scan a receipt in the browser, split it by item or percentage, and every rupiah adds up. A shared bill and its link expire after 24 hours.",
         stack=[("Vue 3", "vuedotjs"), ("TypeScript", "typescript"), ("Hono", "hono"), ("Drizzle", "drizzle"), ("Tesseract.js", None)]),
    dict(slug="nusaride", name="NusaRide", status="demo", href="https://rentcar-demo-blue.vercel.app",
         desc="Frontend demo for car, Hiace and bus rentals: per-unit availability, a fleet admin, PDF invoices, two languages and two themes.",
         stack=[("React 19", "react"), ("React Router", "reactrouter"), ("Tailwind v4", "tailwindcss"), ("jsPDF", None)]),
    dict(slug="vetready", name="VetReady", status="demo", href="https://vetready-demo.vercel.app",
         desc="Vet exam prep with a timed CBT simulation, guided OSCE cases, checkout, and portals for participants and admins.",
         stack=[("React 19", "react"), ("TypeScript", "typescript"), ("Tailwind", "tailwindcss"), ("Framer Motion", "framer")]),
    dict(slug="ramatama", name="Ramatama Tours", status="demo", href="https://tours-agent-demo.vercel.app",
         desc="Travel agency suite where a quotation becomes a booking, an invoice and a receipt, with AR, AP and role-based access.",
         stack=[("React", "react"), ("React Router", "reactrouter"), ("Tailwind", "tailwindcss"), ("Framer Motion", "framer")]),
    dict(slug="formkey", name="Formkey", status="demo", href="https://catalog-order-demo.vercel.app",
         desc="Storefront for artisan keycaps: catalog, bag, checkout, a PayPal payment simulator and an admin for orders.",
         stack=[("React", "react"), ("Tailwind", "tailwindcss"), ("Framer Motion", "framer"), ("Playwright", None)]),
    dict(slug="eventsport", name="ISDN Event Management", status="demo", href="https://event-sport-demo.netlify.app",
         desc="Console for sports competitions: bracket generator, live scoring per sport, drag-and-drop scheduling and QR codes for every participant.",
         stack=[("React", "react"), ("Vite", "vite"), ("React Router", "reactrouter"), ("Framer Motion", "framer")]),
    dict(slug="portfolio", name="Portfolio", status="prod", href="https://fatihaljabar.com",
         desc="My own site and CMS: English and Indonesian, dark mode, an admin dashboard for content, and a full security audit.",
         stack=[("Next.js", "nextdotjs"), ("TypeScript", "typescript"), ("Prisma", "prisma"), ("Supabase", "supabase")]),
    dict(slug="samspos", name="POS", status="demo", href="https://sams-pos-demo.netlify.app",
         desc="POS and inventory for a bakery with three branches, built with Alief Adam: checkout, purchasing, production, stock and an audit log.",
         stack=[("Next.js", "nextdotjs"), ("TypeScript", "typescript"), ("Tailwind", "tailwindcss")]),
    dict(slug="fadlan", name="Fadlan Creator", status="demo", href="https://fadlanportfolio-demo.vercel.app",
         desc="Portfolio for a filmmaker: five galleries with their own routes, a video modal, skeleton loading and reduced motion.",
         stack=[("React", "react"), ("Vite", "vite"), ("React Router", "reactrouter"), ("Tailwind", "tailwindcss")]),
]


def build_all(only: list[str] | None = None) -> None:
    logos = json.load(open(LOGO_FILE))  # read at build time: other parts may add marks
    for p in PROJECTS:
        if only and p["slug"] not in only:
            continue
        if not os.path.isdir(os.path.join(SHOTS, p["slug"])):
            print(f"  skip {p['slug']}: no screenshots in {SHOTS}")
            continue
        build_card(p, logos)
