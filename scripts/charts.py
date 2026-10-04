"""GitHub activity panel drawn from scripts/data/stats.json.

Chart rules followed: one y-axis, thin marks with 4 px rounded data ends,
hairline solid grid, 2 px surface gaps in the stacked bar, selective direct
labels, text in text colours (never the series colour), a legend whenever
there are two or more series, and categorical palettes that passed the
colour-vision validator for each surface.

Motion: data marks never overshoot. Columns rise out of a clip that ends at
the baseline and repository bars slide out of a clip that starts at their
axis, both on the critically damped SETTLE spring, so a bar only ever shows
part of its own value and its rounded data end stays round. After that first
reveal the bars stay still; only the 4-week average is wiped and redrawn by
its pen every LOOP seconds.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import os

from motion import SETTLE, duration, spring_tf
from svgkit import Doc, num, rect
from theme import *  # noqa: F403

DATA = os.path.join(os.path.dirname(__file__), "data", "stats.json")
PROFILE_REPO = "fatihaljabar"  # the README repository itself is not shown as work

# Validated categorical slots: blue, orange, aqua, yellow, magenta, plus a neutral "other".
CATS = {
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"],
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"],
}[THEME]
OTHER = {"dark": "#5B606A", "light": "#80848C"}[THEME]
AXIS = LINE2  # the zero line and the repository axis

LOOP = 14.0  # seconds between redraws of the 4-week average
DRAW = 2.0  # seconds the pen takes to draw the average
T_LINE = 1.5  # first draw starts once the columns have landed
S = duration(SETTLE)
TF = spring_tf(SETTLE)


def nice_ticks(vmax: float, n: int = 3) -> list[int]:
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

    W, H = 1200, 832
    d = Doc(W, H, "GitHub activity: commits per week, by repository and code by language",
            f"Commits per week over the last 52 weeks: {total} commits across {data['repos_scanned']} repositories, "
            f"{data['active_days']} active days, longest streak {data['longest_streak_days']} days. "
            f"{sum(1 for c in counts if not c)} of the 52 weeks have no commits in these repositories. "
            "Below: the repositories with the most commits, and lines of code by language.")
    d.style(BASE_CSS)
    # One timing class for every spring-driven mark; each element names its own keyframes and delay.
    d.style(f".sp{{animation-duration:{S}s;animation-fill-mode:both;{TF}}}")
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))

    def sp(name: str, delay: float) -> str:
        return f'class="sp" style="animation-name:{name};animation-delay:{delay:.3f}s"'

    # ---- header and KPI tiles -------------------------------------------------
    d.add(d.text("Commits per week", 40, 60, 26, SEMI, fill=TEXT))
    d.add(d.text(f"Last 52 weeks, {data['repos_scanned']} repositories, public and private. "
                 f"Snapshot {as_of.day} {as_of:%b %Y}.", 40, 90, 16, BODY, fill=MUTED))

    VS, LS, US = 34, 16, 18  # value, label and unit sizes
    kpis = [(fmt(total), "", "commits"), (str(data["active_days"]), "", "active days"),
            (str(data["longest_streak_days"]), "days", "longest streak")]
    widths = []
    for val, unit, lab in kpis:
        vw = DISP.width(val, VS) + (6 + SEMI.width(unit, US) if unit else 0)
        widths.append(max(vw, SEMI.width(lab, LS)))
    pad = 30  # clear space either side of a divider
    x = W - 40
    xs = []
    for w in reversed(widths):
        x -= w
        xs.append(x)
        x -= 2 * pad
    xs.reverse()
    d.style("@keyframes kp{from{transform:translateY(10px);opacity:0}to{transform:none;opacity:1}}")
    for i, ((val, unit, lab), kx) in enumerate(zip(kpis, xs)):
        if i:
            dx = kx - pad
            d.add(f'<line x1="{num(dx)}" y1="34" x2="{num(dx)}" y2="96" stroke="{LINE}"/>')
        g = d.text(val, kx, 68, VS, DISP, fill=TEXT)
        if unit:
            g += d.text(unit, kx + DISP.width(val, VS) + 6, 68, US, SEMI, fill=MUTED)
        g += d.text(lab, kx, 94, LS, SEMI, fill=MUTED)
        d.add(f'<g {sp("kp", 0.15 + i * 0.07)}>{g}</g>')

    # ---- weekly columns ---------------------------------------------------------
    px0, px1, py0, py1 = 88, 1160, 168, 400
    ticks = nice_ticks(max(counts))
    ymax = ticks[-1]

    def Y(v):
        return py1 - (py1 - py0) * v / ymax

    for tv in ticks:
        y = Y(tv)
        if tv:
            d.add(f'<line x1="{px0}" y1="{num(y)}" x2="{px1}" y2="{num(y)}" stroke="{GRID}" stroke-width="1"/>')
        d.add(d.text(str(tv), px0 - 14, y + 5, 15, MONO, fill=MUTED, anchor="end"))
    band = (px1 - px0) / len(counts)
    bw = min(14.0, band - 4)
    peak_i = max(range(len(counts)), key=lambda i: counts[i])

    d.defs.append(f'<clipPath id="base"><rect x="{px0}" y="{py0 - 40}" width="{px1 - px0}" height="{py1 - py0 + 40}"/></clipPath>')
    cols = []
    for i, c in enumerate(counts):
        if not c:
            continue
        x = px0 + i * band + (band - bw) / 2
        h = py1 - Y(c)
        d.style(f"@keyframes c{i}{{from{{transform:translateY({num(h + 1)}px)}}to{{transform:none}}}}")
        cols.append(f'<path {sp(f"c{i}", 0.3 + i * 0.014)} d="{bar_path(x, py1, bw, h)}" fill="{VOLT}"/>')
    d.add(f'<g clip-path="url(#base)">{"".join(cols)}</g>')

    # empty stretches: one neutral note over each run of 8 or more zero weeks
    runs, start = [], None
    for i, c in enumerate(counts + [1]):
        if c == 0 and start is None:
            start = i
        elif c and start is not None:
            if i - start >= 8:
                runs.append((start, i - 1))
            start = None
    for a, b in runs:
        x0 = px0 + a * band + 3
        x1 = px0 + (b + 1) * band - 3
        xm = (x0 + x1) / 2
        yb = py1 - 14
        d.add(f'<path d="M{num(x0)} {yb + 5}V{yb}H{num(x1)}V{yb + 5}" fill="none" stroke="{LINE2}" stroke-width="1.2"/>')
        d.add(d.text("No commits in", xm, yb - 32, 16, BODY, fill=MUTED, anchor="middle"))
        d.add(d.text("these repositories", xm, yb - 12, 16, BODY, fill=MUTED, anchor="middle"))

    d.add(f'<line x1="{px0}" y1="{py1}" x2="{px1}" y2="{py1}" stroke="{AXIS}" stroke-width="1"/>')

    # month labels at the first week of each month, years under January and the first week
    prev = None
    for i, w in enumerate(weeks):
        end = dt.date.fromisoformat(w["week"]) + dt.timedelta(days=6)  # label by the month the week ends in
        if end.month != prev:
            x = px0 + i * band + band / 2
            d.add(d.text(end.strftime("%b"), x, py1 + 26, 15, MONO, fill=MUTED, anchor="middle"))
            if end.month == 1 or i == 0:
                d.add(d.text(str(end.year), x, py1 + 46, 15, MONOB, fill=MUTED, anchor="middle"))
            prev = end.month

    # 4-week rolling average, drawn by a pen at constant speed, wiped and redrawn every LOOP s
    avg = [sum(counts[max(0, i - 3):i + 1]) / len(counts[max(0, i - 3):i + 1]) for i in range(len(counts))]
    pts = [(px0 + i * band + band / 2, Y(a)) for i, a in enumerate(avg)]
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total_len = sum(seg)

    def pc(t: float) -> str:  # seconds inside the loop to a keyframe percentage
        return f"{t / LOOP * 100:.3f}%"

    t_in, t_draw = 0.0, 0.22  # pen sets down at the start, then draws
    t_end = t_draw + DRAW
    t_wipe = LOOP - 1.35
    t_wiped = t_wipe + 0.7
    t_lift = t_wiped + 0.25
    # dasharray 1 2 on pathLength 1: offset 1.01 and -1.01 both sit in the gap, so the loop seam is invisible
    d.style("@keyframes avg{"
            f"0%,{pc(t_draw)}{{stroke-dashoffset:1;animation-timing-function:linear}}"
            f"{pc(t_end)},{pc(t_wipe)}{{stroke-dashoffset:0;animation-timing-function:cubic-bezier(.45,0,.55,1)}}"
            f"{pc(t_wiped)},100%{{stroke-dashoffset:-1.01}}}}"
            f".avg{{stroke-dasharray:1 2;stroke-dashoffset:0;animation:avg {LOOP}s linear {T_LINE}s infinite backwards}}")
    path = "M" + " L".join(f"{num(x)} {num(y)}" for x, y in pts)
    d.add(f'<path class="avg" pathLength="1" d="{path}" fill="none" stroke="{SKY}" stroke-width="2.2" '
          f'stroke-linejoin="round" stroke-linecap="round"/>')
    acc = 0.0
    kfs = [f"0%{{transform:translate({num(pts[0][0])}px,{num(pts[0][1])}px)}}"]
    for i, (x, y) in enumerate(pts):
        kfs.append(f"{pc(t_draw + DRAW * acc / total_len)}{{transform:translate({num(x)}px,{num(y)}px)}}")
        if i < len(seg):
            acc += seg[i]
    end_tf = f"translate({num(pts[-1][0])}px,{num(pts[-1][1])}px)"
    kfs.append(f"{pc(t_lift + 0.02)}{{transform:{end_tf}}}")
    kfs.append(f"{pc(t_lift + 0.03)},100%{{transform:translate({num(pts[0][0])}px,{num(pts[0][1])}px)}}")
    d.style("@keyframes pen{" + "".join(kfs) + "}"
            f".pen{{transform:{end_tf};animation:pen {LOOP}s linear {T_LINE}s infinite backwards}}"
            "@keyframes lift{"
            f"0%{{opacity:0;transform:scale(.4)}}{pc(t_draw)},{pc(t_wiped)}{{opacity:1;transform:none}}"
            f"{pc(t_lift)},100%{{opacity:0;transform:scale(.4)}}}}"
            f".nib{{animation:lift {LOOP}s {OUTQ} {T_LINE}s infinite backwards}}")
    d.add(f'<g class="pen"><g class="nib"><circle r="5.5" fill="{SKY}" stroke="{PANEL}" stroke-width="2"/></g></g>')

    # legend (two series), above the plot on the right
    lab2 = "4-week average"
    lx = px1 - SEMI.width(lab2, 16)
    d.add(d.text(lab2, lx, 134, 16, SEMI, fill=MUTED))
    d.add(f'<line x1="{num(lx - 34)}" y1="128.5" x2="{num(lx - 10)}" y2="128.5" stroke="{SKY}" stroke-width="2.2" stroke-linecap="round"/>')
    lab1 = "Weekly commits"
    lx1 = lx - 34 - 32 - SEMI.width(lab1, 16)
    d.add(rect(lx1 - 22, 122, 14, 14, 3, fill=VOLT))
    d.add(d.text(lab1, lx1, 134, 16, SEMI, fill=MUTED))

    # peak annotation
    pk = counts[peak_i]
    pxp = px0 + peak_i * band + band / 2
    pk_day = dt.date.fromisoformat(weeks[peak_i]["week"])
    note = f"{pk} commits, week of {pk_day.day} {pk_day:%b}"
    d.style("@keyframes fade{from{opacity:0}to{opacity:1}}.ann{animation:fade .35s linear 1.3s both}")
    d.add(f'<g class="ann"><path d="M{num(pxp - 11)} {num(Y(pk) - 5)}H{num(pxp - 28)}" stroke="{MUTED}" stroke-width="1.2"/>'
          + d.text(note, pxp - 36, Y(pk), 16, SEMI, fill=TEXT, anchor="end") + "</g>")

    # ---- commits by repository ----------------------------------------------------
    by = [r for r in data["by_repo"] if r["repo"] != PROFILE_REPO]
    top = by[:6]
    rest = by[6:]
    rows = [(r["repo"], r["commits"]) for r in top]
    if rest:
        rows.append((f"{len(rest)} more repositories", sum(r["commits"] for r in rest)))
    rx0, ry0, rx1 = 40, 520, 668
    d.add(d.text("Commits by repository", rx0, ry0, 20, SEMI, fill=TEXT))
    d.add(d.text("Last 52 weeks, this profile repository left out", rx0, ry0 + 26, 16, BODY, fill=MUTED))
    name_w = max(MONO.width(n, 16) for n, _ in rows)
    bar_x = rx0 + name_w + 16
    val_w = MONOB.width(str(max(c for _, c in rows)), 16) + 10
    bar_max = rx1 - bar_x - val_w
    vmax = max(c for _, c in rows)
    pitch = 28
    y_first = ry0 + 62
    d.defs.append(f'<clipPath id="rbar"><rect x="{num(bar_x)}" y="{y_first - 20}" width="{num(rx1 - bar_x)}" '
                  f'height="{pitch * len(rows) + 10}"/></clipPath>')
    hb = []
    for i, (name, c) in enumerate(rows):
        yc = y_first + i * pitch
        is_rest = i >= len(top)
        d.add(d.text(name, bar_x - 16, yc + 5.5, 16, MONO, fill=MUTED if is_rest else TEXT, anchor="end"))
        ln = bar_max * c / vmax
        dl = 0.55 + i * 0.06
        d.style(f"@keyframes r{i}{{from{{transform:translateX(-{num(ln + 1)}px)}}to{{transform:none}}}}")
        hb.append(f'<path {sp(f"r{i}", dl)} d="{hbar_path(bar_x, yc, ln, 14)}" fill="{OTHER if is_rest else VOLT}"/>')
        d.add(f'<g class="sp" style="animation-name:fade;animation-delay:{dl + S * 0.55:.3f}s">'
              + d.text(str(c), bar_x + ln + 8, yc + 5.5, 16, MONOB, fill=TEXT) + "</g>")
    d.add(f'<g clip-path="url(#rbar)">{"".join(hb)}</g>')
    d.add(f'<line x1="{num(bar_x)}" y1="{y_first - 15}" x2="{num(bar_x)}" y2="{y_first + (len(rows) - 1) * pitch + 15}" stroke="{AXIS}"/>')

    # ---- code by language (100% stacked bar) -----------------------------------------
    langs = data["languages"]
    main = langs[:5]
    other = sum(l["lines"] for l in langs[5:])
    segs = [(l["language"], l["lines"], CATS[i]) for i, l in enumerate(main)] + ([("Other", other, OTHER)] if other else [])
    tot = sum(n for _, n, _ in segs)
    lx0, ly0, lw = 724, 520, 436
    d.add(d.text("Code by language", lx0, ly0, 20, SEMI, fill=TEXT))
    d.add(d.text("Non-blank lines in each repository's current tree", lx0, ly0 + 26, 16, BODY, fill=MUTED))
    gap = 2
    usable = lw - gap * (len(segs) - 1)
    x = lx0
    by_ = ly0 + 44
    bh = 22
    shapes = ""
    for i, (name, n, col) in enumerate(segs):
        w = max(usable * n / tot, 3)
        shapes += rect(x, by_, w, bh, 4 if i in (0, len(segs) - 1) else 0, fill=col)
        x += w + gap
    # the bar stays put; a panel-coloured shutter slides off it to the right
    d.defs.append(f'<clipPath id="lbar"><rect x="{lx0}" y="{by_ - 1}" width="{lw}" height="{bh + 2}"/></clipPath>')
    d.style(f"@keyframes sh{{from{{transform:none}}to{{transform:translateX({lw + 2}px)}}}}"
            f".shut{{transform:translateX({lw + 2}px)}}")
    d.add(shapes + f'<g clip-path="url(#lbar)"><rect class="shut sp" style="animation-name:sh;animation-delay:.85s" '
          f'x="{lx0 - 1}" y="{by_ - 1}" width="{lw + 2}" height="{bh + 2}" fill="{PANEL}"/></g>')
    # legend with values: identity never relies on colour alone
    for i, (name, n, col) in enumerate(segs):
        cy = by_ + bh + 34 + i * pitch
        d.add(rect(lx0, cy - 12, 14, 14, 3, fill=col))
        d.add(d.text(name, lx0 + 24, cy, 16, SEMI, fill=TEXT))
        pct = n / tot * 100
        d.add(d.text(fmt(n), lx0 + lw - 84, cy, 16, MONO, fill=MUTED, anchor="end"))
        d.add(d.text(f"{pct:.1f}%", lx0 + lw, cy, 16, MONOB, fill=TEXT, anchor="end"))

    d.add(d.text("Source: git history of each repository, commits authored by fatihaljabar. Client demos often "
                 "ship as a few squashed commits.", 40, H - 32, 16, BODY, fill=MUTED))
    save("activity.svg", d)
