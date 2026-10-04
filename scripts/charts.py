"""GitHub activity panel drawn from scripts/data/stats.json.

Chart rules followed: one y-axis, thin marks with 4 px rounded data ends,
hairline solid grid, 2 px surface gaps in the stacked bar, selective direct
labels, text in text colours (never the series colour), a legend whenever
there are two or more series, and a categorical palette that passed the
colour-vision validator for the dark surface.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import os

from motion import FIRM, SNAP, linear_easing, spring_anim
from svgkit import Doc, num, rect
from theme import *  # noqa: F403

DATA = os.path.join(os.path.dirname(__file__), "data", "stats.json")
GRID = "#1F2328"
# validated categorical slots (dark surface): blue, orange, aqua, yellow, magenta + neutral "other"
CATS = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"]
OTHER = "#5B606A"


def nice_ticks(vmax: float, n: int = 4) -> list[int]:
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw), default=10 * mag)
    top = math.ceil(vmax / step) * step
    return [int(round(i * step)) for i in range(int(round(top / step)) + 1)]


def bar_path(x, y_base, w, h, r=4.0) -> str:
    """Column with a rounded data end and a square foot on the baseline."""
    r = min(r, w / 2, h)
    top = y_base - h
    return (f"M{num(x)} {num(y_base)}V{num(top + r)}Q{num(x)} {num(top)} {num(x + r)} {num(top)}"
            f"H{num(x + w - r)}Q{num(x + w)} {num(top)} {num(x + w)} {num(top + r)}V{num(y_base)}Z")


def hbar_path(x, yc, length, t, r=4.0) -> str:
    r = min(r, t / 2, length)
    y0, y1 = yc - t / 2, yc + t / 2
    return (f"M{num(x)} {num(y0)}H{num(x + length - r)}Q{num(x + length)} {num(y0)} {num(x + length)} {num(y0 + r)}"
            f"V{num(y1 - r)}Q{num(x + length)} {num(y1)} {num(x + length - r)} {num(y1)}H{num(x)}Z")


def fmt(n: int) -> str:
    return f"{n:,}"


def build() -> None:
    data = json.load(open(DATA))
    weeks = data["weeks"]
    counts = [w["commits"] for w in weeks]
    total = sum(counts)
    as_of = dt.date.fromisoformat(data["as_of"])
    repos_active = len(data["by_repo"])

    W, H = 1200, 724
    d = Doc(W, H, "GitHub activity: commits per week, by repository and code by language",
            f"Commits per week over the last 52 weeks: {total} commits across {data['repos_scanned']} repositories, "
            f"{data['active_days']} active days, longest streak {data['longest_streak_days']} days. "
            "Most commits by repository and lines of code by language are shown below the weekly chart.")
    d.style(BASE_CSS)
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))

    # ---- header + KPI tiles
    d.add(d.text("Commits per week", 40, 58, 22, SEMI, fill=TEXT))
    d.add(d.text(f"Last 52 weeks, {data['repos_scanned']} repositories, public and private. "
                 f"Snapshot {as_of.day} {as_of:%b %Y}.", 40, 84, 14, BODY, fill=MUTED))
    kpis = [(fmt(total), "commits"), (str(data["active_days"]), "active days"),
            (str(data["longest_streak_days"]), "day longest streak"), (str(repos_active), "repos with commits")]
    kx = 652
    for i, (val, lab) in enumerate(kpis):
        x = kx + i * 128
        if i:
            d.add(f'<line x1="{x - 18}" y1="38" x2="{x - 18}" y2="92" stroke="{LINE}"/>')
        d.style(f"@keyframes kp{{from{{transform:translateY(14px);opacity:0}}to{{transform:none;opacity:1}}}}"
                + spring_anim(f"kp{i}", "kp", SNAP, 0.15 + i * 0.07))
        d.add(f'<g class="kp{i}">{d.text(val, x, 70, 30, DISP, fill=TEXT)}{d.text(lab, x, 90, 12.5, SEMI, fill=MUTED)}</g>')

    # ---- weekly columns
    px0, px1, py0, py1 = 84, 1160, 150, 384
    ticks = nice_ticks(max(counts))
    ymax = ticks[-1]

    def Y(v):
        return py1 - (py1 - py0) * v / ymax

    for tv in ticks:
        y = Y(tv)
        d.add(f'<line x1="{px0}" y1="{num(y)}" x2="{px1}" y2="{num(y)}" stroke="{GRID if tv else "#3A3F48"}" stroke-width="1"/>')
        d.add(d.text(str(tv), px0 - 12, y + 4, 11, MONO, fill=DIM, anchor="end"))
    band = (px1 - px0) / len(counts)
    bw = min(14.0, band - 4)
    peak_i = max(range(len(counts)), key=lambda i: counts[i])
    for i, c in enumerate(counts):
        if not c:
            continue
        x = px0 + i * band + (band - bw) / 2
        h = py1 - Y(c)
        d.style(f"@keyframes cb{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}"
                + spring_anim(f"b{i}", "cb", SNAP, 0.35 + i * 0.016).replace(f".b{i}{{", f".b{i}{{transform-box:fill-box;transform-origin:center bottom;"))
        d.add(f'<path class="b{i}" d="{bar_path(x, py1, bw, h)}" fill="{VOLT}"/>')

    # month labels at the first week of each month
    prev = None
    for i, w in enumerate(weeks):
        day = dt.date.fromisoformat(w["week"])
        m = (day + dt.timedelta(days=6)).month  # label by the month the week ends in
        if m != prev:
            x = px0 + i * band + band / 2
            label = (day + dt.timedelta(days=6)).strftime("%b")
            d.add(d.text(label, x, py1 + 22, 11, MONO, fill=DIM, anchor="middle"))
            if label == "Jan" or i == 0:
                d.add(d.text(str((day + dt.timedelta(days=6)).year), x, py1 + 38, 10, MONOB, fill=DIM, anchor="middle"))
            prev = m

    # 4-week rolling average: drawn by a pen that travels along it at constant speed
    avg = [sum(counts[max(0, i - 3):i + 1]) / len(counts[max(0, i - 3):i + 1]) for i in range(len(counts))]
    pts = [(px0 + i * band + band / 2, Y(a)) for i, a in enumerate(avg)]
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total_len = sum(seg)
    t0, tdur = 1.45, 2.0
    d.style(f"@keyframes line{{from{{stroke-dashoffset:1}}to{{stroke-dashoffset:0}}}}"
            f".avg{{stroke-dasharray:1 1;animation:line {tdur}s linear {t0}s both}}")
    path = "M" + " L".join(f"{num(x)} {num(y)}" for x, y in pts)
    d.add(f'<path class="avg" pathLength="1" d="{path}" fill="none" stroke="{SKY}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    acc = 0.0
    kfs = []
    for i, (x, y) in enumerate(pts):
        kfs.append(f"{acc / total_len * 100:.2f}%{{transform:translate({num(x)}px,{num(y)}px)}}")
        if i < len(seg):
            acc += seg[i]
    d.style("@keyframes pen{" + "".join(kfs) + "}"
            f".pen{{transform:translate({num(pts[-1][0])}px,{num(pts[-1][1])}px);animation:pen {tdur}s linear {t0}s both}}")
    d.add(f'<g class="pen"><circle r="5" fill="{SKY}" stroke="{PANEL}" stroke-width="2"/></g>')

    # legend (two series), top right of the plot
    lx = px1 - 300
    d.add(rect(lx, py0 - 30, 12, 12, 3, fill=VOLT))
    d.add(d.text("Weekly commits", lx + 20, py0 - 20, 12, SEMI, fill=MUTED))
    d.add(f'<line x1="{lx + 146}" y1="{py0 - 24}" x2="{lx + 166}" y2="{py0 - 24}" stroke="{SKY}" stroke-width="2" stroke-linecap="round"/>')
    d.add(d.text("4-week average", lx + 174, py0 - 20, 12, SEMI, fill=MUTED))

    # peak annotation
    pk = counts[peak_i]
    pxp = px0 + peak_i * band + band / 2
    pk_day = dt.date.fromisoformat(weeks[peak_i]["week"])
    note = f"{pk} commits, week of {pk_day.day} {pk_day:%b}"
    d.style(f"@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}.ann{{animation:fade .4s linear 1.4s both}}")
    d.add(f'<g class="ann"><path d="M{num(pxp - 10)} {num(Y(pk) - 4)}H{num(pxp - 26)}" stroke="{MUTED}" stroke-width="1"/>'
          + d.text(note, pxp - 32, Y(pk), 12.5, SEMI, fill=TEXT, anchor="end") + "</g>")

    # ---- commits by repository
    by = data["by_repo"]
    top = by[:6]
    rest = sum(r["commits"] for r in by[6:])
    rows = [(r["repo"], r["commits"]) for r in top] + ([(f"{len(by) - 6} more repos", rest)] if rest else [])
    rx0, ry0 = 40, 474
    d.add(d.text("Commits by repository", rx0, ry0, 15, SEMI, fill=TEXT))
    d.add(d.text("last 52 weeks", rx0 + SEMI.width("Commits by repository", 15) + 10, ry0, 12, MONO, fill=DIM))
    name_w = 262
    bar_x = rx0 + name_w
    bar_max = 520 - name_w - 40
    vmax = max(c for _, c in rows)
    for i, (name, c) in enumerate(rows):
        yc = ry0 + 28 + i * 25
        d.add(d.text(name, bar_x - 12, yc + 4, 12, MONO, fill=TEXT if i < len(top) else MUTED, anchor="end"))
        ln = bar_max * c / vmax
        col = VOLT if i < len(top) else OTHER
        d.style(f"@keyframes hb{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}"
                + spring_anim(f"h{i}", "hb", FIRM, 0.6 + i * 0.06).replace(f".h{i}{{", f".h{i}{{transform-box:fill-box;transform-origin:left center;"))
        d.add(f'<path class="h{i}" d="{hbar_path(bar_x, yc, ln, 12)}" fill="{col}"/>')
        d.add(d.text(str(c), bar_x + ln + 8, yc + 4, 12, MONOB, fill=TEXT))
    d.add(f'<line x1="{bar_x}" y1="{ry0 + 14}" x2="{bar_x}" y2="{ry0 + 28 + (len(rows) - 1) * 25 + 10}" stroke="#3A3F48"/>')

    # ---- code by language (100% stacked bar)
    langs = data["languages"]
    main = langs[:5]
    other = sum(l["lines"] for l in langs[5:])
    segs = [(l["language"], l["lines"], CATS[i]) for i, l in enumerate(main)] + ([("Other", other, OTHER)] if other else [])
    tot = sum(n for _, n, _ in segs)
    lx0, ly0, lw = 620, 474, 540
    d.add(d.text("Code by language", lx0, ly0, 15, SEMI, fill=TEXT))
    d.add(d.text("non-blank lines in each repo's current tree", lx0 + SEMI.width("Code by language", 15) + 10, ly0, 12, MONO, fill=DIM))
    gap = 2
    usable = lw - gap * (len(segs) - 1)
    x = lx0
    for i, (name, n, col) in enumerate(segs):
        w = max(usable * n / tot, 3)
        shape = rect(x, ly0 + 20, w, 22, 4 if i in (0, len(segs) - 1) else 0, fill=col)
        d.style(f"@keyframes sg{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}"
                + spring_anim(f"s{i}", "sg", FIRM, 0.9 + i * 0.08).replace(f".s{i}{{", f".s{i}{{transform-box:fill-box;transform-origin:left center;"))
        d.add(f'<g class="s{i}">{shape}</g>')
        x += w + gap
    # legend with values: identity never relies on colour alone
    for i, (name, n, col) in enumerate(segs):
        cx = lx0 + (i % 2) * 270
        cy = ly0 + 70 + (i // 2) * 26
        d.add(rect(cx, cy - 10, 12, 12, 3, fill=col))
        d.add(d.text(name, cx + 20, cy, 13, SEMI, fill=TEXT))
        pct = n / tot * 100
        d.add(d.text(fmt(n), cx + 196, cy, 12, MONO, fill=MUTED, anchor="end"))
        d.add(d.text(f"{pct:.1f}%", cx + 250, cy, 12, MONOB, fill=TEXT, anchor="end"))

    d.add(d.text("Source: git history of each repository, commits authored by fatihaljabar. Client demos often "
                 "ship as a few squashed commits.", 40, H - 24, 11, MONO, fill=DIM))
    save("activity.svg", d)
