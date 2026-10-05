"""Thesis panel: real tweets from the dataset pass, one at a time, through the
Indonesian preprocessing steps and the CNN + BiLSTM + attention model; the
result column compares the test accuracy of the four trained models.

Facts (project-ta, model_outputs_epoch_150/run_summary.pkl and dataset.csv):
26,852 tweets about electric vehicles, Jan 2023 to Aug 2025, labels Netral
11,788, Negatif 8,370, Positif 6,694. Test accuracy CNN 72.2%, LSTM 43.9%,
BiLSTM 73.5%, CNN + BiLSTM with attention 75.9%, macro F1 0.76.

One clock drives the pipeline. Every CYCLE seconds the tweet in the reading
slot is processed: the connector flashes, the four preprocessing chips light
in order, the Conv1D kernel steps across the tokens (stride 1), the forward
LSTM nodes and the attention columns light exactly when the kernel passes
them, then the kernel returns on a critically damped spring while the
backward LSTM nodes light as it goes by. The feed then advances one tweet.
The static frame (reduced motion) is the rest state of that cycle.
"""

from __future__ import annotations

import math

from motion import SETTLE, duration, response, spring_tf
from svgkit import Doc, num, rect, wrap
from theme import *  # noqa: F403

# Six real rows of the dataset's clean_text column (no mentions, no links), two per label.
TWEETS = [
    ("Negatif", "Apr 2024", "menunggu drama kehabisan daya kemacetan arus mudik"),
    ("Positif", "Jul 2025", "langkah bikin konsumen percaya nyaman beralih"),
    ("Netral", "Nov 2023", "tersedia stasiun pengisian ulang daya rest area"),
    ("Negatif", "May 2025", "ambil utang beli bikin cepat miskin"),
    ("Positif", "Nov 2024", "kehadiran indonesia trend ramah lingkungan efisien"),
    ("Netral", "Dec 2023", "tidak bikin atapnya pakai solar panel"),
]
MODELS = [("CNN", 72.2), ("LSTM", 43.9), ("BiLSTM", 73.5), ("CNN + BiLSTM", 75.9)]
AX_LO, AX_HI = 40.0, 80.0
NEUTRAL_BAR = {"dark": "#5B606A", "light": "#80848C"}[THEME]

CYCLE = 5.0  # seconds per tweet
G = 0.6  # the first cycle starts after the result bars have landed
S = duration(SETTLE)
TF = spring_tf(SETTLE)

# cycle-relative timings (seconds)
T_LINK = 0.15  # feed to pipeline connector flashes
T_CHIP = 0.35  # first chip lights, then one every CHIP_DT
CHIP_DT = 0.22
T_K0 = 1.45  # kernel starts stepping
K_DT = 0.1  # one stride per K_DT
T_RET = 3.2  # kernel returns
T_OUT = T_RET + S * 0.6  # pipeline to result connector flashes
T_FEED = CYCLE - S - 0.15  # the feed advances one tweet


def pc(t: float, period: float = CYCLE) -> str:
    return f"{max(0.0, min(100.0, t / period * 100)):.3f}%"


def hbar_path(x, yc, length, t, r=4.0) -> str:
    r = min(r, t / 2, length)
    y0, y1 = yc - t / 2, yc + t / 2
    return (f"M{num(x)} {num(y0)}H{num(x + length - r)}Q{num(x + length)} {num(y0)} {num(x + length)} {num(y0 + r)}"
            f"V{num(y1 - r)}Q{num(x + length)} {num(y1)} {num(x + length - r)} {num(y1)}H{num(x)}Z")


def pulse(name: str, t_on: float, hold: float, decay: float, rise: float = 0.06) -> str:
    """Opacity 0, up to 1 at t_on, held for `hold`, back to 0 over `decay`; one cycle."""
    return (f"@keyframes {name}{{0%,{pc(t_on)}{{opacity:0}}{pc(t_on + rise)},{pc(t_on + rise + hold)}"
            f"{{opacity:1;animation-timing-function:cubic-bezier(.3,0,.6,1)}}{pc(t_on + rise + hold + decay)},100%{{opacity:0}}}}")


def build() -> None:
    W, H = 1200, 560
    d = Doc(W, H, "Sentiment analysis pipeline: real tweets, preprocessing, CNN + BiLSTM with attention, 75.9% accuracy",
            "Six real tweets from the 26,852 tweet dataset (Indonesian, about electric vehicles, Jan 2023 to Aug 2025) "
            "pass one at a time through cleaning, case folding, Sastrawi stemming and quantile labeling, then through "
            "Conv1D, BiLSTM and attention layers. Test accuracy: CNN 72.2%, LSTM 43.9%, BiLSTM 73.5%, "
            "CNN + BiLSTM with attention 75.9%, macro F1 0.76.")
    d.style(BASE_CSS)
    d.style(f".sp{{animation-duration:{S}s;animation-fill-mode:both;{TF}}}"
            f".cy{{animation-duration:{CYCLE}s;animation-delay:{G}s;animation-iteration-count:infinite;"
            "animation-timing-function:linear;animation-fill-mode:backwards}")
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))

    ax, aw = 36, 296
    bx, bw = 376, 452
    cx, cw = 872, 292
    top = 112

    def head(x, title, sub):
        d.add(d.text(title, x, 60, 22, SEMI, fill=TEXT))
        d.add(d.text(sub, x, 88, 16, BODY, fill=MUTED))

    head(ax, "Data", "26,852 tweets, Jan 2023 to Aug 2025")
    head(bx, "Pipeline and model", "Preprocessing, then the CNN + BiLSTM hybrid")
    head(cx, "Result", "Test accuracy of the four models")

    # ---- column A: the tweet feed ------------------------------------------------------------
    win_h = H - 32 - top
    card_w, card_h, gap = aw - 20, 96, 10
    pitch = card_h + gap
    d.defs.append(f'<clipPath id="feed"><rect x="{ax + 1}" y="{top + 1}" width="{aw - 2}" height="{win_h - 2}" rx="13"/></clipPath>')
    d.add(rect(ax, top, aw, win_h, 14, fill=BG, stroke=LINE, stroke_width=1.2))

    def card(y: float, label: str, when: str, text: str) -> str:
        x = ax + 10
        out = rect(x, y, card_w, card_h, 12, fill=PANEL2, stroke=LINE, stroke_width=1)
        out += d.text(label, x + 16, y + 28, 16, SEMI, fill=MUTED)
        out += d.text(when, x + card_w - 16, y + 28, 16, MONO, fill=MUTED, anchor="end")
        for j, line in enumerate(wrap(BODY, text, 17, card_w - 32)[:2]):
            out += d.text(line, x + 16, y + 56 + j * 23, 17, BODY, fill=TEXT)
        return out

    n = len(TWEETS)
    assert n * pitch >= win_h, "two copies of the set must cover the window at every scroll offset"
    d.defs.append('<g id="set">' + "".join(card(top + 10 + i * pitch, *t) for i, t in enumerate(TWEETS)) + "</g>")
    cards = f'<use xlink:href="#set"/><use xlink:href="#set" y="{n * pitch}"/>'
    loop = n * CYCLE
    kf = ["0%{transform:none}"]
    for k in range(n):
        t0 = k * CYCLE + T_FEED
        kf.append(f"{pc(t0, loop)}{{transform:translateY(-{num(k * pitch)}px);{TF}}}")
        kf.append(f"{pc(t0 + S, loop)}{{transform:translateY(-{num((k + 1) * pitch)}px)}}")
    kf.append(f"100%{{transform:translateY(-{num(n * pitch)}px)}}")
    d.style("@keyframes feed{" + "".join(kf) + "}"
            f".feed{{animation:feed {loop}s linear {G}s infinite backwards}}")
    d.add(f'<g clip-path="url(#feed)"><g class="feed">{cards}</g></g>')
    # the reading slot: the tweet inside it is the one the pipeline is processing
    slot_y = top + 10
    d.add(rect(ax + 6, slot_y - 4, aw - 12, card_h + 8, 15, fill="none", stroke=VOLT, stroke_width=2))

    # ---- connectors ---------------------------------------------------------------------------
    def connector(x0, x1, y, t_on, name):
        line = (f'M{num(x0)} {num(y)}H{num(x1)}M{num(x1 - 6)} {num(y - 6)}L{num(x1)} {num(y)}L{num(x1 - 6)} {num(y + 6)}')
        d.add(f'<path d="{line}" fill="none" stroke="{LINE2}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
        d.style(pulse(name, t_on, 0.25, 0.5))
        d.add(f'<path class="cy" style="animation-name:{name}" opacity="0" d="{line}" fill="none" stroke="{VOLT}" '
              f'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>')

    slot_c = slot_y + card_h / 2
    connector(ax + aw + 8, bx - 8, slot_c, T_LINK, "lk0")

    # ---- column B: preprocessing chips -------------------------------------------------------------
    steps = ["clean", "case fold", "Sastrawi stem", "quantile label"]
    padx = 11
    ws = [SEMI.width(s, 16) + 2 * padx for s in steps]
    sgap = (bw - sum(ws)) / (len(steps) - 1)
    chip_h = 34
    cy0 = slot_c - chip_h / 2
    x = bx
    for i, (st, w) in enumerate(zip(steps, ws)):
        d.add(rect(x, cy0, w, chip_h, 9, fill=BG, stroke=LINE2, stroke_width=1.2))
        d.add(d.text(st, x + w / 2, cy0 + 22.5, 16, SEMI, fill=MUTED, anchor="middle"))
        d.style(pulse(f"ch{i}", T_CHIP + i * CHIP_DT, 0.28, 0.35))
        d.add(f'<g class="cy" style="animation-name:ch{i}" opacity="0">'
              + rect(x, cy0, w, chip_h, 9, fill=LIME, stroke=VOLT, stroke_width=1.2)
              + d.text(st, x + w / 2, cy0 + 22.5, 16, SEMI, fill=INK, anchor="middle") + "</g>")
        if i < len(steps) - 1:  # the rail the connector continues on
            d.add(f'<line x1="{num(x + w + 2)}" y1="{num(slot_c)}" x2="{num(x + w + sgap - 2)}" y2="{num(slot_c)}" '
                  f'stroke="{LINE2}" stroke-width="2" stroke-linecap="round"/>')
        x += w + sgap

    # ---- Conv1D: token cells and a kernel that steps with stride 1 -----------------------------------
    lab_w = 100
    gx0 = bx + lab_w
    cells = 16
    cwid = (bw - lab_w) / cells
    conv_y = slot_c + 76
    d.add(d.text("Conv1D", bx, conv_y + 6, 16, SEMI, fill=TEXT))
    shades = [PANEL2, LINE, LINE2]
    for i in range(cells):
        d.add(rect(gx0 + i * cwid, conv_y - 12, cwid - 3, 24, 4, fill=shades[(i * 7 + 1) % 3]))
    kpos = cells - 3
    kx = cwid * kpos
    d.style("@keyframes kern{"
            f"0%,{pc(T_K0)}{{transform:none;animation-timing-function:steps({kpos},end)}}"
            f"{pc(T_K0 + kpos * K_DT)},{pc(T_RET)}{{transform:translateX({num(kx)}px);{TF}}}"
            f"{pc(T_RET + S)},100%{{transform:none}}}}")
    d.add(f'<g class="cy" style="animation-name:kern"><rect x="{num(gx0 - 3)}" y="{conv_y - 16}" width="{num(3 * cwid + 3)}" '
          f'height="32" rx="7" fill="{VOLT}" fill-opacity=".14" stroke="{VOLT}" stroke-width="2"/></g>')

    def kernel_center_fwd(p: int) -> float:
        return gx0 + (p + 1.5) * cwid - 1.5

    # return trip: kernel position along the SETTLE step response
    _, xs = response(SETTLE)

    def t_back(xc: float) -> float:
        """Seconds after T_RET at which the returning kernel's centre passes x = xc."""
        start, end = kernel_center_fwd(kpos), kernel_center_fwd(0)
        if xc >= start:
            return 0.0
        frac = (start - xc) / (start - end)
        for i, v in enumerate(xs):
            if v >= frac:
                return i * 0.001
        return S

    # ---- BiLSTM: forward nodes light as the kernel passes, backward nodes as it returns ------------------
    nodes = 7
    nx0 = gx0 + 11
    nstep = (bw - lab_w - 22) / (nodes - 1)
    ly = conv_y + 78
    rows = [(ly - 19, VOLT, 1), (ly + 19, CORAL, -1)]
    d.add(d.text("BiLSTM", bx, ly + 6, 16, SEMI, fill=TEXT))
    for row, (yy, col, dirn) in enumerate(rows):
        d.add(f'<line x1="{num(nx0)}" y1="{yy}" x2="{num(nx0 + nstep * (nodes - 1))}" y2="{yy}" stroke="{LINE2}" stroke-width="2"/>')
        for i in range(nodes):
            xn = nx0 + i * nstep
            d.add(f'<circle cx="{num(xn)}" cy="{yy}" r="9" fill="{PANEL2}" stroke="{LINE2}" stroke-width="1.5"/>')
            if dirn > 0:
                p = min(kpos, max(0, math.ceil((xn - gx0) / cwid - 1.5)))
                t_on = T_K0 + p * K_DT
            else:
                t_on = T_RET + t_back(xn)
            name = f"n{row}{i}"
            d.style(pulse(name, t_on, 0.12, 0.55, rise=0.04))
            d.add(f'<circle class="cy" style="animation-name:{name}" opacity="0" cx="{num(xn)}" cy="{yy}" r="9" fill="{col}"/>')
        if dirn > 0:
            d.add(arrow_right(nx0 + nstep * (nodes - 1) + 17, yy, 8, col, 2))
        else:
            ax2 = nx0 - 17
            d.add(f'<path d="M{num(ax2)} {yy}h-8M{num(ax2 - 5)} {yy - 3}L{num(ax2 - 8)} {yy}L{num(ax2 - 5)} {yy + 3}" fill="none" '
                  f'stroke="{col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')

    # ---- attention: a diagonal of weights; each column brightens while the kernel covers it --------------
    hy = ly + 62
    hrows, hgap = 4, 4
    rh = 20
    d.add(d.text("Attention", bx, hy + 15, 16, SEMI, fill=TEXT))
    for c in range(cells):
        on = T_K0 + max(0, c - 2) * K_DT
        off = T_RET if c >= kpos else T_K0 + (c + 1) * K_DT  # the kernel parks over the last three columns
        over = ""
        for r in range(hrows):
            w = 0.07 + 0.83 * math.exp(-((c - 8 - r) ** 2) / 5)
            xr = gx0 + c * cwid
            yr = hy + r * (rh + hgap)
            d.add(rect(xr, yr, cwid - 3, rh, 3, fill=SKY, fill_opacity=f"{w:.2f}"))
            peak = min(1.0, w * 1.45 + 0.22)
            a = (peak - w) / (1 - w)  # overlay alpha that composites the base up to the peak
            over += rect(xr, yr, cwid - 3, rh, 3, fill=SKY, fill_opacity=f"{a:.2f}")
        d.style(pulse(f"hc{c}", on, off - on - 0.06, 0.45))
        d.add(f'<g class="cy" style="animation-name:hc{c}" opacity="0">{over}</g>')
    d.add(d.text("Softmax weights over tokens", gx0, hy + hrows * (rh + hgap) + 22, 16, BODY, fill=MUTED))

    # ---- column C: result ---------------------------------------------------------------------------
    best = max(MODELS, key=lambda m: m[1])
    big = f"{best[1]:.1f}%"
    d.add(d.text(big, cx - 3, top + 58, 64, DISP, fill=TEXT))
    d.add(d.text("accuracy", cx + DISP.width(big, 64) + 8, top + 58, 20, SEMI, fill=MUTED))
    d.add(d.text("macro F1 0.76", cx, top + 90, 16, MONO, fill=MUTED))

    val_w = MONOB.width("75.9%", 16) + 10
    span = cw - val_w
    X = lambda v: cx + span * (v - AX_LO) / (AX_HI - AX_LO)  # noqa: E731
    r0 = top + 150
    rp = 52
    tick_y0, tick_y1 = r0 - 22, r0 + (len(MODELS) - 1) * rp + 22
    # axis: a baseline at 40% and a scale under the rows, no gridlines behind the value labels
    d.add(f'<line x1="{num(X(AX_LO))}" y1="{tick_y0}" x2="{num(X(AX_LO))}" y2="{tick_y1}" stroke="{LINE2}" stroke-width="1.2"/>')
    d.add(f'<line x1="{num(X(AX_LO))}" y1="{tick_y1}" x2="{num(X(AX_HI))}" y2="{tick_y1}" stroke="{LINE2}" stroke-width="1.2"/>')
    for tv in (40, 50, 60, 70, 80):
        xt = X(tv)
        major = tv % 20 == 0
        d.add(f'<line x1="{num(xt)}" y1="{tick_y1}" x2="{num(xt)}" y2="{tick_y1 + (6 if major else 4)}" stroke="{LINE2}" stroke-width="1.2"/>')
        if major:
            d.add(d.text(f"{tv}%", xt, tick_y1 + 26, 16, MONO, fill=MUTED, anchor="middle" if tv > AX_LO else "start"))
    d.defs.append(f'<clipPath id="acc"><rect x="{num(cx)}" y="{tick_y0}" width="{num(cw)}" height="{tick_y1 - tick_y0}"/></clipPath>')
    bars = ""
    hybrid_y = r0
    d.style("@keyframes fade{from{opacity:0}to{opacity:1}}")
    for i, (m, v) in enumerate(MODELS):
        yb = r0 + i * rp
        win = m == best[0]
        if win:
            hybrid_y = yb + 6
        d.add(d.text(m, cx, yb - 4, 16, SEMI, fill=TEXT if win else MUTED))
        ln = X(v) - cx
        dl = 0.25 + i * 0.08
        d.style(f"@keyframes ab{i}{{from{{transform:translateX(-{num(ln + 1)}px)}}to{{transform:none}}}}")
        bars += (f'<path class="sp" style="animation-name:ab{i};animation-delay:{dl:.2f}s" '
                 f'd="{hbar_path(cx, yb + 12, ln, 14)}" fill="{VOLT if win else NEUTRAL_BAR}"/>')
        d.add(f'<g class="sp" style="animation-name:fade;animation-delay:{dl + S * 0.6:.2f}s">'
              + d.text(f"{v:.1f}%", X(v) + 8, yb + 17.5, 16, MONOB if win else MONO, fill=TEXT if win else MUTED) + "</g>")
    d.add(f'<g clip-path="url(#acc)">{bars}</g>')

    # pipeline output into the result, level with the hybrid's bar
    connector(bx + bw + 8, cx - 8, hybrid_y + 6, T_OUT, "lk1")
    save("thesis.svg", d)
