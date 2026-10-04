"""Thesis panel: tweets flow through the Indonesian NLP pipeline into the
CNN + BiLSTM + Attention model, which wins the four-model comparison."""

from __future__ import annotations

import math
import random

from svgkit import Doc, num, rect
from theme import *  # noqa: F403


def build() -> None:
    W, H = 1200, 470
    D = 10
    d = Doc(W, H, "Sentiment analysis pipeline: tweets, preprocessing, CNN + BiLSTM + Attention, 75% accuracy",
            "Indonesian tweets about electric vehicles stream in, pass through cleaning, case folding, Sastrawi stemming and "
            "quantile labeling, then through Conv1D, BiLSTM and attention layers. Four models are compared and the "
            "CNN + BiLSTM + Attention hybrid wins with 75 percent accuracy and 0.76 macro F1.")
    d.style(BASE_CSS)
    d.add(rect(0.75, 0.75, W - 1.5, H - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))

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
        feed += rect(ax + 26, y + 15, 20, 20, 5, fill="#3A404A")
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
    d.add(d.text("accuracy", cx0 + DISP.width("75%", 84) + 10, 368, 22, SEMI, fill=MUTED))
    d.add(d.text("0.76 macro F1 · deployed on Streamlit", cx0, 404, 12, MONO, fill=MUTED))
    d.style(f"@keyframes bar{{0%,50%{{transform:scaleX(0)}}62%,92%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}}}"
            f".bar{{animation:bar {D}s {OUTQ} infinite;transform-box:fill-box;transform-origin:left center}}")
    d.add(rect(cx0, 422, cwid2, 6, 3, fill=LINE))
    d.add(f'<rect class="bar" x="{cx0}" y="422" width="{num(cwid2*0.75)}" height="6" rx="3" fill="{VOLT}"/>')
    save("thesis.svg", d)
