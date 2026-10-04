"""Project cards built from real screenshots.

Each card embeds the project's own desktop and mobile captures (taken from a
local build of the repo, see scripts/shots/) as WebP, and scrolls them like a
person flicking through the page: a quick move, a spring settle, a pause to
read. No fake browser chrome, just the page and a hairline.
"""

from __future__ import annotations

import base64
import io
import json
import os

from PIL import Image

from motion import HEAVY, Spring, spring_tf
from svgkit import Doc, num, rect, wrap
from theme import *  # noqa: F403

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.environ.get("SHOTS_DIR", os.path.join(HERE, "shots"))
LOGOS = json.load(open(os.path.join(HERE, "data", "logos.json")))

CW, CH = 600, 500
MX, MY, MW, MH = 14, 14, 572, 318  # media area
DW = 452  # desktop viewport width on the card (1440 css px)
DH = round(DW * 900 / 1440)
PW = 124  # phone viewport width (390 css px)
PH = round(PW * 844 / 390)
SCROLL = Spring(210, 26)  # a flick: fast, then the page settles with a small give

STATUS = {
    "prod": "In production",
    "demo": "Live demo",
    "repo": "Public repo",
    "private": "Private repo",
}


def webp_data(path: str, width: int, max_h: int | None = None, quality: int = 74) -> tuple[str, int]:
    im = Image.open(path)
    if path.endswith(".webp") and im.width == width and not max_h:
        # already prepared by import_shots.py: embed the bytes as they are
        with open(path, "rb") as fh:
            return "data:image/webp;base64," + base64.b64encode(fh.read()).decode(), im.height
    im = im.convert("RGB")
    if max_h and im.height > max_h:
        im = im.crop((0, 0, im.width, max_h))
    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode(), h


def logo(slug, name, x, y, s, d: Doc, color=TEXT) -> str:
    if slug:
        k = s / 24
        return f'<path transform="translate({num(x)} {num(y)}) scale({k:.4f})" d="{LOGOS[slug]["path"]}" fill="{color}"/>'
    letters = "".join(w[0] for w in name.replace(".", " ").split()[:2]).upper()
    return (rect(x, y, s, s, 4, fill="none", stroke=color, stroke_width=1.3)
            + d.text(letters[:2], x + s / 2, y + s / 2 + 3, 7.5, MONOB, fill=color, anchor="middle"))


def scroll_keyframes(name: str, content_h: float, view_h: float, period: float, offset: float) -> str:
    """Read, flick, read, flick... then a longer spring back to the top."""
    max_y = max(0.0, content_h - view_h)
    if max_y < 4:
        return ""
    stops = []
    y = 0.0
    step = view_h * 0.82
    while y < max_y - 2 and len(stops) < 5:
        y = min(max_y, y + step)
        stops.append(y)
    n = len(stops)
    hold = 1.6  # seconds spent reading each screen
    move = 0.55
    total = 1.2 + n * (move + hold) + 0.9
    period = max(period, total)
    t = 1.2
    kf = ["0%{transform:translateY(0)}",
          f"{t / period * 100:.2f}%{{transform:translateY(0);{spring_tf(SCROLL)}}}"]
    for i, y in enumerate(stops):
        t += move
        kf.append(f"{t / period * 100:.2f}%{{transform:translateY(-{y:.1f}px)}}")
        t += hold
        tf = spring_tf(HEAVY) if i == n - 1 else spring_tf(SCROLL)
        kf.append(f"{t / period * 100:.2f}%{{transform:translateY(-{y:.1f}px);{tf}}}")
    t += 0.9
    kf.append(f"{min(t / period * 100, 100):.2f}%,100%{{transform:translateY(0)}}")
    return (f"@keyframes {name}{{" + "".join(kf) + "}"
            f".{name}{{animation:{name} {period:.2f}s linear {-offset:.2f}s infinite}}")


def build_card(p: dict, index: int) -> None:
    slug = p["slug"]
    sdir = os.path.join(SHOTS, slug)
    notes = os.path.join(sdir, "notes.json")
    meta = json.load(open(notes)) if os.path.exists(notes) else {}
    bg = p.get("bg") or meta.get("background_hex") or PANEL2
    r, g, b = (int(bg[i:i + 2], 16) for i in (1, 3, 5))
    light = (0.2126 * r + 0.7152 * g + 0.0722 * b) > 140
    hair = 'stroke="#000" stroke-opacity=".14"' if light else 'stroke="#fff" stroke-opacity=".14"'

    d = Doc(CW, CH, f"{p['name']}: {p['desc']}",
            f"Project card for {p['name']}, showing real screenshots of the desktop and mobile layouts scrolling. "
            f"{p['desc']} Built with {', '.join(n for n, _ in p['stack'])}.")
    d.style(BASE_CSS)
    d.add(rect(0.75, 0.75, CW - 1.5, CH - 1.5, 18, fill=PANEL, stroke=LINE, stroke_width=1.5))

    # media area in the product's own page colour
    d.defs.append(f'<clipPath id="media"><rect x="{MX}" y="{MY}" width="{MW}" height="{MH}" rx="12"/></clipPath>')
    d.add(rect(MX, MY, MW, MH, 12, fill=bg))
    d.add('<g clip-path="url(#media)">')

    desktop = os.path.join(sdir, "desktop.webp")
    mobile = os.path.join(sdir, "mobile.webp")
    dx, dy = MX + 22, MY + 24
    if os.path.exists(desktop):
        src, h = webp_data(desktop, round(DW * 1.5))
        h_disp = h / 1.5
        d.defs.append(f'<clipPath id="dv"><rect x="{dx}" y="{dy}" width="{DW}" height="{DH}" rx="8"/></clipPath>')
        d.style(scroll_keyframes("ds", h_disp, DH, 12.0, index * 1.3))
        d.add(f'<g clip-path="url(#dv)"><g class="ds"><image x="{dx}" y="{dy}" width="{DW}" height="{num(h_disp)}" '
              f'preserveAspectRatio="none" xlink:href="{src}"/></g></g>')
        d.add(f'<rect x="{dx - 0.5}" y="{dy - 0.5}" width="{DW + 1}" height="{DH + 1}" rx="8.5" fill="none" {hair}/>')
    px, py = MX + MW - PW - 22, MY + MH - PH + 6
    if os.path.exists(mobile):
        src, h = webp_data(mobile, PW * 2)
        h_disp = h / 2
        d.defs.append(f'<clipPath id="pv"><rect x="{px}" y="{py}" width="{PW}" height="{PH}" rx="16"/></clipPath>')
        d.style(scroll_keyframes("ps", h_disp, PH, 10.0, index * 1.3 + 3.1))
        d.add(rect(px - 5, py - 5, PW + 10, PH + 10, 20, fill=bg))
        d.add(f'<g clip-path="url(#pv)"><g class="ps"><image x="{px}" y="{py}" width="{PW}" height="{num(h_disp)}" '
              f'preserveAspectRatio="none" xlink:href="{src}"/></g></g>')
        d.add(f'<rect x="{px}" y="{py}" width="{PW}" height="{PH}" rx="16" fill="none" {hair}/>')
    d.add("</g>")

    # text block
    d.add(d.text(p["name"], 26, 376, 28, DISP, fill=TEXT))
    status = STATUS[p["status"]]
    link = p["status"] != "private"
    sw = MONOB.width(status, 11) + (34 if link else 24)
    sx = CW - 26 - sw
    d.add(rect(sx, 356, sw, 26, 13, fill="none", stroke="#3A3F48", stroke_width=1.2))
    d.add(d.text(status, sx + 12, 373, 11, MONOB, fill=TEXT))
    if link:
        d.add(arrow_ne(sx + sw - 19, 364, 9, VOLT, 1.8))
    lines = wrap(BODY, p["desc"], 15.5, CW - 52)
    if len(lines) > 2:
        raise ValueError(f"{slug}: description wraps to {len(lines)} lines")
    for i, ln in enumerate(lines):
        d.add(d.text(ln, 26, 406 + i * 22, 15.5, BODY, fill=MUTED))
    # stack: logo + name, separated by space only
    x = 26
    y = 458
    d.add(f'<line x1="26" y1="{y - 14}" x2="{CW - 26}" y2="{y - 14}" stroke="{LINE}"/>')
    for name, slug_ in p["stack"]:
        w = 15 + 7 + SEMI.width(name, 13)
        if x + w > CW - 26:
            break
        d.add(logo(slug_, name, x, y + 3, 15, d, color=MUTED))
        d.add(d.text(name, x + 22, y + 15, 13, SEMI, fill=MUTED))
        x += w + 16
    save(f"card-{slug}.svg", d)


PROJECTS = [
    dict(slug="blockwave", name="Blockwave Studios", status="demo", href="https://blockwavestudio-demo.vercel.app",
         desc="Minecraft and Roblox asset marketplace. Designed and built solo, from the spec to a client-approved demo.",
         stack=[("React 19", "react"), ("Vite", "vite"), ("Tailwind v4", "tailwindcss"), ("Recharts", None)]),
    dict(slug="ottodot", name="Ottodot Trial Booking", status="repo", href="https://github.com/fatihaljabar/ottodot-trial-booking",
         desc="Two parents, one seat left. Row-locked Postgres transactions, idempotent payments, 34 tests including a real race.",
         stack=[("Next.js", "nextdotjs"), ("PostgreSQL", "postgresql"), ("Prisma", "prisma"), ("Zod", "zod"), ("Vitest", "vitest")]),
    dict(slug="tracker", name="application-tracker", status="prod", href="https://trackinglamaran.site",
         desc="Job-hunt companion: an 11-stage pipeline, 14 fields per application, deadline and interview reminders, stats.",
         stack=[("React", "react"), ("Express", "express"), ("Drizzle", "drizzle"), ("Cloudflare R2", "cloudflare"), ("Resend", "resend")]),
    dict(slug="splitbill", name="splitbill", status="prod", href="https://splitbills.site",
         desc="Scan a receipt in the browser, split it by item or percentage, and every rupiah still adds up. Short links stay private.",
         stack=[("Vue 3", "vuedotjs"), ("TypeScript", "typescript"), ("Hono", "hono"), ("Drizzle", "drizzle"), ("Tesseract.js", None)]),
    dict(slug="nusaride", name="NusaRide", status="demo", href="https://rentcar-demo-blue.vercel.app",
         desc="Car, Hiace and bus rentals with per-unit availability, a fleet admin, PDF invoices, two languages and two themes.",
         stack=[("React 19", "react"), ("React Router", "reactrouter"), ("Tailwind v4", "tailwindcss"), ("jsPDF", None)]),
    dict(slug="vetready", name="VetReady", status="demo", href="https://vetready-demo.vercel.app",
         desc="Vet exam prep with a timed CBT simulation, guided OSCE cases, checkout, and portals for participants and admins.",
         stack=[("React 19", "react"), ("TypeScript", "typescript"), ("Vite", "vite"), ("Tailwind", "tailwindcss"), ("Framer Motion", "framer")]),
    dict(slug="ramatama", name="Ramatama Tours", status="demo", href="https://tours-agent-demo.vercel.app",
         desc="Travel agency suite where a quotation becomes a booking, an invoice and a receipt, with AR, AP and role-based access.",
         stack=[("React", "react"), ("React Router", "reactrouter"), ("Tailwind", "tailwindcss"), ("Framer Motion", "framer")]),
    dict(slug="formkey", name="Formkey", status="demo", href="https://catalog-order-demo.vercel.app",
         desc="Storefront for artisan keycaps: catalog, bag, checkout, a PayPal payment simulator and an admin for orders.",
         stack=[("React", "react"), ("Tailwind", "tailwindcss"), ("Framer Motion", "framer"), ("Playwright", None)]),
    dict(slug="eventsport", name="event-sport-demo", status="demo", href="https://event-sport-demo.netlify.app",
         desc="Sports event platform for ISDN: bracket generator, sport-specific live scoring, drag-and-drop scheduling, QR check-in.",
         stack=[("React", "react"), ("Vite", "vite"), ("React Router", "reactrouter"), ("Framer Motion", "framer")]),
    dict(slug="portfolio", name="portfolio", status="prod", href="https://fatihaljabar.com",
         desc="My own site and CMS: English and Indonesian, dark mode, an admin dashboard for content, and a full security audit.",
         stack=[("Next.js", "nextdotjs"), ("TypeScript", "typescript"), ("Prisma", "prisma"), ("Supabase", "supabase")]),
    dict(slug="fadlan", name="Fadlan Creator", status="demo", href="https://fadlanportfolio-demo.vercel.app",
         desc="Portfolio for a filmmaker: five galleries with their own routes, a video modal, skeleton loading and reduced motion.",
         stack=[("React", "react"), ("Vite", "vite"), ("React Router", "reactrouter"), ("Tailwind", "tailwindcss")]),
    dict(slug="samspos", name="sams-pos-demo", status="private", href="#spec-sheet",
         desc="POS and inventory for a bakery: checkout, purchasing, production, stock across branches and an audit log.",
         stack=[("Next.js", "nextdotjs"), ("TypeScript", "typescript"), ("Tailwind", "tailwindcss")]),
]


def build_all(only: list[str] | None = None) -> None:
    for i, p in enumerate(PROJECTS):
        if only and p["slug"] not in only:
            continue
        if not os.path.isdir(os.path.join(SHOTS, p["slug"])):
            print(f"  skip {p['slug']}: no screenshots in {SHOTS}")
            continue
        build_card(p, i)
