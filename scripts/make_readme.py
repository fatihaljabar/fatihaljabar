"""Writes README.md from the same data the assets are built from.

    python scripts/make_readme.py

Project cards come from cards.PROJECTS, the stack from stack.ROWS, the toolbox
from toolbox.GROUPS, the certificates from certs.CERTS and the activity numbers
from scripts/data/stats.json, so the page and its drawings never disagree.
"""

import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import cards  # noqa: E402
import certs as cert_sheets  # noqa: E402
import toolbox  # noqa: E402

tool_names = [n for _, items in toolbox.GROUPS for n, _ in items]
with open(os.path.join(HERE, "data", "stats.json"), encoding="utf-8") as f:
    data = json.load(f)
import stack  # noqa: E402
STACK_ALT = "Tech stack on three conveyor belts. " + " ".join(f"{label}: {', '.join(n for n, _ in items)}." for label, _, items in stack.ROWS)


def pic(name, alt, width=None, height=None):
    size = (f' width="{width}"' if width else "") + (f' height="{height}"' if height else "")
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}.svg">'
            f'<source media="(prefers-color-scheme: light)" srcset="assets/{name}-light.svg">'
            f'<img src="assets/{name}.svg"{size} alt="{alt}"></picture>')


def heading(anchor, name, alt):
    return f'<a name="{anchor}"></a>\n<h3><a href="#{anchor}">{pic("section-" + name, alt, "100%")}</a></h3>'


SPEC = {
    "blockwave": ("Blockwave Studios", None,
                  "Digital asset marketplace for Minecraft and Roblox creators. I designed and built it solo, from the client's spec to an approved, fully interactive demo: storefront, customer library and an admin console with analytics, coupons and order states. The production build (Next.js 15, NestJS, PostgreSQL, PayPal, Cloudflare R2) is in progress.",
                  "React 19, Vite, React Router, Tailwind v4, Framer Motion, Recharts",
                  [("Live demo", "https://blockwavestudio-demo.vercel.app")]),
    "ottodot": ("Ottodot Trial Booking", "ottodot-trial-booking",
                "Full-stack take-home: trial classes hold exactly four confirmed students. One PostgreSQL transaction with a class-row lock guards every path to a confirmed seat, idempotency keys make retries safe, and 34 automated tests cover it, including a genuinely concurrent last-seat race.",
                "Next.js, TypeScript, PostgreSQL, Prisma, Zod, Vitest",
                [("Repo", "https://github.com/fatihaljabar/ottodot-trial-booking")]),
    "tracker": ("Tracking Lamaran", "application-tracker",
                "Job-hunt companion: an 11-stage pipeline, 14 fields per application, deadline and interview reminders, document uploads and stats.",
                "React, Vite, Express, Drizzle (MariaDB), Cloudflare R2, Resend",
                [("Live", "https://trackinglamaran.site"), ("Repo", "https://github.com/fatihaljabar/application-tracker")]),
    "splitbill": ("SplitBills", "splitbill",
                  "Bill splitting with in-browser OCR receipt scanning, item or percentage splits with exact-rupiah rounding, a private mode where each person sees only their own share, and short links that expire after 24 hours.",
                  "Vue 3, TypeScript, Hono, Drizzle (MySQL), Tesseract.js",
                  [("Live", "https://splitbills.site"), ("Repo", "https://github.com/fatihaljabar/splitbill")]),
    "nusaride": ("NusaRide", None,
                 "Front-end demo for car, Hiace, Elf and bus rentals: self-drive, chauffeur and airport-transfer booking, per-unit availability, admin CRUD for fleet, drivers and payments, PDF invoices and reports, Indonesian and English, light and dark.",
                 "React 19, TypeScript, Vite 7, React Router, Tailwind v4, Framer Motion, jsPDF",
                 [("Live demo", "https://rentcar-demo-blue.vercel.app")]),
    "vetready": ("VetReady", None,
                 "Interactive demo for a veterinary exam prep platform: timed CBT simulation with flags and answer review, guided OSCE clinical cases, checkout with simulated payments, a participant dashboard and an admin portal.",
                 "React 19, TypeScript, Vite 7, Tailwind 4, Framer Motion",
                 [("Live demo", "https://vetready-demo.vercel.app")]),
    "ramatama": ("Ramatama Tours", None,
                 "Travel agency management demo where quotation, booking, invoice, payment and receipt share one connected data model, with AR and AP, supplier bookings, itineraries, role-based access, multi-currency display and CSV export.",
                 "React, TypeScript, Vite, React Router, Tailwind, Framer Motion",
                 [("Live demo", "https://tours-agent-demo.vercel.app")]),
    "formkey": ("Formkey", None,
                "Storefront demo for artisan keycaps: catalog with search and sorting, bag and checkout, a PayPal payment simulator, a confirmation email preview, and an admin for products, categories and orders.",
                "React, TypeScript, Vite, Tailwind, Framer Motion, Playwright",
                [("Live demo", "https://catalog-order-demo.vercel.app")]),
    "eventsport": ("ISDN Event Management", None,
                   "Event management console for ISDN sports competitions: bracket generator, sport-specific live scoring (combat, race, judged and more), drag-and-drop scheduling with conflict detection, and QR check-in. Still in active development for the client.",
                   "React, Vite, React Router, Framer Motion",
                   [("Live demo", "https://event-sport-demo.netlify.app")]),
    "portfolio": ("Portfolio", "portfolio",
                  "My own site and self-service CMS: English and Indonesian, dark mode, an admin dashboard for content, and a full security audit of the codebase.",
                  "Next.js, TypeScript, Prisma, Supabase, next-intl",
                  [("Live", "https://fatihaljabar.com"), ("Repo", "https://github.com/fatihaljabar/portfolio")]),
    "samspos": ("POS", None,
                'POS and inventory prototype for a bakery client, built with <a href="https://github.com/aliefadam">Alief Adam</a>: checkout, purchasing, production, stock across branches and audit logs.',
                "Next.js, TypeScript, Tailwind",
                [("Live demo", "https://sams-pos-demo.netlify.app")]),
    "fadlan": ("Fadlan Creator", None,
               "Cinematic portfolio for a videographer and filmmaker: five category galleries with their own routes, a demo video modal, skeleton loading states and reduced-motion support.",
               "React, Vite, React Router, Tailwind",
               [("Live demo", "https://fadlanportfolio-demo.vercel.app")]),
}

rows = []
cells = []
for i, p in enumerate(cards.PROJECTS, 1):
    name, repo, what, stack, links = SPEC[p["slug"]]
    name = name or p["name"]
    sub = f'<br><sub><a href="https://github.com/fatihaljabar/{repo}">{repo}</a></sub>' if repo else "<br><sub>private repo</sub>"
    link = " / ".join(f'<a href="{u}">{t}</a>' for t, u in links) or "Private"
    rows.append(f"| {i:02d} | **{name}**{sub} | {what} | {stack} | {link} |")
    cells.append(f'  <a href="{p["href"]}">{pic("card-" + p["slug"], p["name"] + ": " + p["desc"], "49%")}</a>')
spec = "| # | Project | What it does | Stack | Links |\n|---|---|---|---|---|\n" + "\n".join(rows)
card_html = "\n".join(cells)

_kinds = [p["status"] for p in cards.PROJECTS]
_prod, _demo = _kinds.count("prod"), _kinds.count("demo")
stats_alt_head = (f"{_prod + _demo} of the {len(_kinds)} builds on this page are live: "
                  f"{_prod} in production and {_demo} demo{'' if _demo == 1 else 's'}. Thesis model accuracy 75.9 percent. ")

CERT_URL = "https://www.dicoding.com/certificates/"
cert_items = [(cred, " ".join(title), " ".join(topics)) for cred, title, topics in cert_sheets.CERTS]
cert_alt = ("Six Dicoding Indonesia certificates clipped to two wires, each showing its course and credential ID. "
            "The courses are linked below.")
cert_links = ", ".join(f'<a href="{CERT_URL}{c}">{t}</a>' for c, t, _ in cert_items[:-1])
cert_links += f' and <a href="{CERT_URL}{cert_items[-1][0]}">{cert_items[-1][1]}</a>'
cert_rows = "\n".join(f'| {i + 1:02d} | {t} | {w} | <a href="{CERT_URL}{c}"><code>{c}</code></a> |'
                      for i, (c, t, w) in enumerate(cert_items))

months = {m["month"]: m["commits"] for m in data["months"]}
first = dt.date.fromisoformat(data["weeks"][0]["week"])
last = dt.date.fromisoformat(data["as_of"])
mrows = []
y, m = first.year, first.month
while (y, m) <= (last.year, last.month):
    mrows.append(f"| {dt.date(y, m, 1):%b %Y} | {months.get(f'{y}-{m:02d}', 0)} |")
    m += 1
    if m == 13:
        y, m = y + 1, 1
month_table = "| Month | Commits |\n|---|---:|\n" + "\n".join(mrows)
repo_table = "| Repository | Commits |\n|---|---:|\n" + "\n".join(f"| {r['repo']} | {r['commits']} |" for r in data["by_repo"])
tot = sum(l["lines"] for l in data["languages"])
lang_table = "| Language | Lines | Share |\n|---|---:|---:|\n" + "\n".join(
    f"| {l['language']} | {l['lines']:,} | {l['lines'] / tot * 100:.1f}% |" for l in data["languages"])
week_total = sum(w["commits"] for w in data["weeks"])
stats_alt = stats_alt_head + str(week_total) + " commits in the last 52 weeks."

readme = f'''<a name="top"></a>

<p align="center">
  <a href="https://fatihaljabar.com"><img src="assets/hero.svg" width="100%" alt="A pen plotter drafts the name Fatih on a sheet that reads: 'Interfaces that feel fast and obvious, with a backend behind them that stays out of the way.' Title block: Fatih Al Jabar, Front-End & Full-Stack Developer, Indonesia, UTC+7, open to remote work. Links to fatihaljabar.com."></a>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/fatihaljabar">{pic("btn-linkedin", "LinkedIn", height=48)}</a>
  <a href="mailto:fatihaljabar@gmail.com">{pic("btn-email", "Email", height=48)}</a>
  <a href="https://www.instagram.com/fatihaljabar">{pic("btn-instagram", "Instagram", height=48)}</a>
</p>

<p align="center">
  <a href="#projects">{pic("btn-nav-work", "01 Projects", height=44)}</a>
  <a href="#stack">{pic("btn-nav-stack", "02 Stack", height=44)}</a>
  <a href="#thesis">{pic("btn-nav-thesis", "03 Thesis", height=44)}</a>
  <a href="#certifications">{pic("btn-nav-certs", "04 Certifications", height=44)}</a>
  <a href="#activity">{pic("btn-nav-stats", "05 Activity", height=44)}</a>
</p>

<p align="center">
  <a href="#activity">{pic("stats", stats_alt, "100%")}</a>
</p>

I'm Fatih Al Jabar, a **Front-End & Full-Stack Developer** in Indonesia (UTC+7), and I take on freelance client projects. Send me your spec and I'll turn it into **a demo you can click through before any backend exists**, so you can try every screen and ask for changes while they're still easy to make. Once you approve it, I build the production version from it.

A Minecraft and Roblox asset marketplace, a travel agency suite, a vet exam platform and a sports event console all started that way. The marketplace is in its production build now.

My main stack is **React, Next.js and TypeScript**, with Node.js and PostgreSQL, MySQL or Supabase behind it, and Vue when a project calls for it. Three of my own apps run in production: a job-application tracker at [trackinglamaran.site](https://trackinglamaran.site), a bill splitter with in-browser receipt OCR at [splitbills.site](https://splitbills.site), and the site and CMS behind [fatihaljabar.com](https://fatihaljabar.com). I've also built an e-commerce platform with live payments, and with [Alief Adam](https://github.com/aliefadam) a POS for a bakery client.

If you have a spec that needs a first version, email me at [fatihaljabar@gmail.com](mailto:fatihaljabar@gmail.com) and tell me what you're building. I'll reply with how I'd approach it. The same address works if you're hiring for a front-end or full-stack role.

<br>

{heading("projects", "work", "Featured projects")}

<p align="center">
{card_html}
</p>

<a name="spec-sheet"></a>

<details>
<summary><b>Open the spec sheet</b>: every project with the full description, stack and links</summary>
<br>

{spec}

</details>

<br>

{heading("stack", "stack", "Tech stack")}

<p align="center">
  <a href="#stack">{pic("stack", STACK_ALT, "100%")}</a>
</p>

<details>
<summary><b>Open the full toolbox</b> ({len(tool_names)} tools, grouped)</summary>
<br>

<p align="center">{pic("toolbox", "Full toolbox: " + ", ".join(tool_names) + ".", "100%")}</p>

</details>

<br>

{heading("thesis", "thesis", "Thesis")}

<p align="center">
  <a href="https://github.com/fatihaljabar/project-TA">{pic("thesis", "Thesis pipeline: real Indonesian tweets about electric vehicles flow through cleaning, case folding, Sastrawi stemming and quantile labeling into Conv1D, BiLSTM and attention layers. Test accuracy: CNN 72.2 percent, LSTM 43.9 percent, BiLSTM 73.5 percent, CNN + BiLSTM hybrid 75.9 percent with macro F1 0.76.", "100%")}</a>
</p>

**Sentiment Analysis on Online Reviews of Electric Vehicles Using Deep Learning**

For my Computer Science degree at Universitas 17 Agustus 1945 Surabaya, I compared four architectures (CNN, LSTM, BiLSTM, and a CNN + BiLSTM hybrid with attention) on 26,852 Indonesian tweets collected from January 2023 to August 2025, and built the whole Indonesian NLP pipeline myself: text cleaning, case folding, Sastrawi stemming and lexicon-based quantile labeling. The hybrid won with **75.9% accuracy and 0.76 macro F1**. The repository has the notebook, the trained weights for all four models and a Streamlit app for trying sentiment predictions on your own text.

<p>
  <a href="https://project-ta-fatih.streamlit.app">{pic("btn-demo", "Live demo", height=44)}</a>
  <a href="https://github.com/fatihaljabar/project-TA">{pic("btn-source", "Source code", height=44)}</a>
  <a href="https://doi.org/10.36040/jati.v10i1.17094">{pic("btn-article", "Article", height=44)}</a>
</p>

<br>

{heading("certifications", "certs", "Certifications")}

<p align="center">
  <a href="#certifications">{pic("certs", cert_alt, "100%")}</a>
</p>

All six are from **Dicoding Indonesia**, and each link opens the credential on dicoding.com: {cert_links}.

<details>
<summary><b>The certificates as text</b></summary>
<br>

| # | Course | What it covers | Credential |
|---|---|---|---|
{cert_rows}

</details>

<br>

{heading("activity", "stats", "GitHub activity")}

<p align="center">
  <a href="#activity">{pic("activity", "Commits per week over the last 52 weeks with a 4-week average, commits by repository, and lines of code by language.", "100%")}</a>
</p>

<details>
<summary><b>The numbers behind the chart</b></summary>
<br>

Counted from the git history of {data["repos_scanned"]} repositories, public and private, as of {last.day} {last:%B %Y}: {week_total} commits in the last 52 weeks over {data["active_days"]} active days, longest streak {data["longest_streak_days"]} days.

{month_table}

{repo_table}

{lang_table}

</details>

<br>

<p align="center">
  <a href="mailto:fatihaljabar@gmail.com">{pic("footer", "Open to remote opportunities. Email me at fatihaljabar@gmail.com.", "100%")}</a>
</p>

<p align="center">
  <img src="https://komarev.com/ghpvc/?username=fatihaljabar&style=flat-square&color=C9F31D&label=profile+views" alt="Profile views"/>
  <br>
  <sub><a href="#top">Back to top</a>. Every drawing on this page is plain SVG and CSS, by <a href="https://github.com/fatihaljabar">fatihaljabar</a>.</sub>
</p>
'''
for bad in ("—", "–", "·", "•"):
    assert bad not in readme, f"banned glyph {bad!r} in README"
with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)
print("README written,", len(readme), "chars,", len(tool_names), "tools,", len(cert_items), "certs")
