"""Generates every animated SVG used by the profile README.

    pip install fonttools brotli
    python scripts/build_assets.py

Output goes to assets/. All motion is pure CSS inside the SVG, so it plays in
GitHub's image sandbox with no scripts and no external requests.
"""

from __future__ import annotations

import os
import math

from svgkit import Doc, num, rect, wrap
from theme import *  # noqa: F403
import cards
import sections


# ---------------------------------------------------------------------------
# HERO: a design-tool canvas where the profile builds itself while two
# multiplayer cursors (me and the visitor) play with it.
# ---------------------------------------------------------------------------
def hero() -> None:
    W, H = 1200, 640
    d = Doc(W, H, "Fatih, front-end leaning full-stack developer",
            "An animated design canvas: the name Fatih drops in letter by letter, a selection frame "
            "snaps around it, stickers show 3 apps live in production, 75 percent thesis accuracy "
            "and a 3.63 GPA, while two cursors named Fatih and You move around the canvas.")
    d.defs.append(dots_pattern())
    d.style(BASE_CSS)
    d.style(f"""
@keyframes drop{{0%{{transform:translateY(-300px);opacity:0}}55%{{transform:translateY(16px);opacity:1}}75%{{transform:translateY(-7px)}}90%{{transform:translateY(2px)}}100%{{transform:translateY(0)}}}}
.ch{{animation:drop 1s cubic-bezier(.3,.6,.4,1) both}}
@keyframes pop{{0%{{transform:scale(0);opacity:0}}100%{{transform:scale(1);opacity:1}}}}
.dotpop{{animation:pop .5s {SPRING} 1.25s both}}
@keyframes type{{from{{opacity:0}}to{{opacity:1}}}}
.ty{{animation:type .01s linear both}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
.caret{{animation:blink 1s steps(1) infinite}}
@keyframes draw{{from{{stroke-dashoffset:1}}to{{stroke-dashoffset:0}}}}
.frame{{stroke-dasharray:1;animation:draw .7s {INOUT} 1.35s both}}
.handle{{animation:pop .35s {SPRING} both}}
.dim{{animation:pop .45s {SPRING} 1.95s both}}
.flab{{animation:type .3s linear 1.35s both}}
@keyframes rise{{from{{opacity:0;transform:translateY(22px)}}to{{opacity:1;transform:none}}}}
.r1{{animation:rise .8s {OUTQ} 1.55s both}}
.r2{{animation:rise .8s {OUTQ} 1.7s both}}
.chip{{animation:rise .6s {OUTQ} both}}
@keyframes stick{{0%{{opacity:0;transform:translateY(-70px) rotate(-10deg) scale(1.12)}}65%{{opacity:1;transform:translateY(6px) rotate(2deg) scale(.98)}}100%{{transform:none}}}}
.stick{{animation:stick .9s {OUTQ} both}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-9px)}}}}
.float{{animation:float 6s ease-in-out infinite}}
@keyframes fin{{from{{transform:translate(-420px,360px)}}to{{transform:none}}}}
.fin{{animation:fin 1.1s {OUTQ} .8s both}}
@keyframes fwander{{
 0%{{transform:translate(0,0)}}
 8%{{transform:translate(0,0)}}
 16%,24%{{transform:translate(22px,12px)}}
 38%,52%{{transform:translate(318px,-150px)}}
 66%,80%{{transform:translate(120px,170px)}}
 100%{{transform:translate(0,0)}}}}
.fw{{animation:fwander 14s {INOUT} 2s infinite}}
@keyframes guides{{0%,9%{{opacity:0}}12%,24%{{opacity:1}}28%,100%{{opacity:0}}}}
.guide{{animation:guides 14s linear 2s infinite;opacity:0}}
@keyframes ywander{{
 0%,14%{{transform:translate(320px,300px)}}
 30%,48%{{transform:translate(0,0)}}
 64%,80%{{transform:translate(-140px,330px)}}
 96%,100%{{transform:translate(320px,300px)}}}}
.yw{{animation:ywander 12s {INOUT} 2.6s infinite;transform:translate(320px,300px)}}
@keyframes yclick{{0%,31%{{transform:scale(1)}}33%{{transform:scale(.8)}}36%,100%{{transform:scale(1)}}}}
.yc{{animation:yclick 12s linear 2.6s infinite}}
@keyframes ripple{{0%,32%{{transform:scale(.2);opacity:0}}33%{{opacity:.9;transform:scale(.3)}}44%,100%{{transform:scale(2.6);opacity:0}}}}
.ripple{{animation:ripple 12s ease-out 2.6s infinite;opacity:0}}
@keyframes pon{{0%,32%{{opacity:0}}34%,56%{{opacity:1}}60%,100%{{opacity:0}}}}
.pon{{animation:pon 12s linear 2.6s infinite;opacity:0}}
@keyframes here{{0%,18%{{opacity:0}}24%,90%{{opacity:1}}96%,100%{{opacity:0}}}}
.here{{animation:here 12s linear 2.6s infinite;opacity:0}}
@keyframes alone{{0%,18%{{opacity:1}}24%,90%{{opacity:0}}96%,100%{{opacity:1}}}}
.alone{{animation:alone 12s linear 2.6s infinite}}
@keyframes lift{{0%,62%{{transform:none}}67%,80%{{transform:translateY(-14px) rotate(-3deg) scale(1.04)}}86%,100%{{transform:none}}}}
.lift{{animation:lift 12s {INOUT} 2.6s infinite}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(4px)}}}}
.bob{{animation:bob 1.6s ease-in-out infinite}}
@keyframes pulse{{0%{{transform:scale(1);opacity:.7}}100%{{transform:scale(3.2);opacity:0}}}}
.pulse{{animation:pulse 1.8s ease-out infinite}}
""")

    # canvas
    d.add(rect(0, 0, W, H, 22, fill=BG))
    d.add(f'<rect x="0" y="56" width="{W}" height="{H-96}" fill="url(#dots)"/>')

    # ---- toolbar (moved above the canvas content later so falling letters slide under it)
    tb_start = len(d.body)
    d.add(f'<path d="M0 22 Q0 0 22 0 L{W-22} 0 Q{W} 0 {W} 22 L{W} 56 L0 56 Z" fill="{PANEL}"/>')
    d.add(f'<line x1="0" y1="56" x2="{W}" y2="56" stroke="{LINE}"/>')
    d.add(rect(20, 14, 28, 28, 7, fill=VOLT))
    d.add(d.text("F", 34, 34, 18, DISP, fill=INK, anchor="middle"))
    d.add(d.text("fatihaljabar", 62, 33, 14, MONO, fill=TEXT))
    d.add(d.text("/ readme.canvas", 62 + MONO.width("fatihaljabar ", 14), 33, 14, MONO, fill=DIM))

    # tools
    tx = 520
    icons = [
        f'<path d="M{tx+11} {16+0} l0 15 l4 -3.6 l3 6.3 l2.6 -1.2 l-2.9 -6.1 l5.2 0 Z" transform="translate(0 4)" fill="{MUTED}"/>',
        None,
        f'<rect x="{tx+2*38+9}" y="19" width="16" height="16" rx="2" fill="none" stroke="{MUTED}" stroke-width="1.8"/>',
        "T",
        f'<path d="M{tx+4*38+9} 35 L{tx+4*38+21} 21 L{tx+4*38+25} 25 L{tx+4*38+13} 37 Z M{tx+4*38+9} 35 l0 2 l2 0" fill="none" stroke="{MUTED}" stroke-width="1.8" stroke-linejoin="round"/>',
    ]
    for i, ic in enumerate(icons):
        x = tx + i * 38
        if i == 1:
            d.add(rect(x, 10, 34, 36, 8, fill=VOLT))
            d.add(
                f'<path d="M{x+12} 15 L{x+12} 41 M{x+22} 15 L{x+22} 41 M{x+6} 21 L{x+28} 21 M{x+6} 35 L{x+28} 35" '
                f'stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
            )
        elif ic == "T":
            d.add(d.text("T", x + 17, 34, 19, SEMI, fill=MUTED, anchor="middle"))
        else:
            d.add(ic)

    # viewers
    vx = 930
    d.add(f'<g class="here"><circle cx="{vx+20}" cy="28" r="13" fill="{CORAL}" stroke="{PANEL}" stroke-width="3"/>'
          + d.text("Y", vx + 20, 33, 13, MONOB, fill=INK, anchor="middle") + "</g>")
    d.add(f'<circle cx="{vx}" cy="28" r="13" fill="{VOLT}" stroke="{PANEL}" stroke-width="3"/>')
    d.add(d.text("F", vx, 33, 13, MONOB, fill=INK, anchor="middle"))
    d.add(f'<g class="alone">{d.text("1 here", vx + 44, 33, 13, MONO, fill=DIM)}</g>')
    d.add(f'<g class="here">{d.text("2 here", vx + 44, 33, 13, MONO, fill=MUTED)}</g>')

    # "open to remote" pill (target of the visitor's click)
    plabel = "Open to remote"
    pw = MONOB.width(plabel, 13) + 40
    px = W - 20 - pw
    d.add(rect(px, 13, pw, 30, 15, fill="none", stroke=VOLT, stroke_width=1.4))
    d.add(f'<circle cx="{px+16}" cy="28" r="4" fill="{VOLT}"/>')
    d.add(d.text(plabel, px + 28, 32.5, 13, MONOB, fill=VOLT))
    d.add(f'<g class="pon">' + rect(px, 13, pw, 30, 15, fill=VOLT)
          + f'<circle cx="{px+16}" cy="28" r="4" fill="{INK}"/>'
          + d.text(plabel, px + 28, 32.5, 13, MONOB, fill=INK) + "</g>")
    click_x, click_y = px + pw * 0.55, 30

    tb_end = len(d.body)

    # ---- canvas content
    d.add(d.text("About / Hero", 64, 96, 13, MONO, fill=DIM, cls="flab"))

    hi = "HI, I'M"
    d.add(d.text(hi, 66, 150, 20, MONOB, fill=VOLT, per_char="ty", delay0=0.15, step=0.07))
    cx_ = 66 + MONOB.width(hi, 20) + 6
    d.add(rect(cx_, 134, 11, 20, 0, fill=VOLT, cls="caret"))

    size = 216
    base = 340
    name = "Fatih"
    nx = 56
    d.add(d.text(name, nx, base, size, DISP, fill=TEXT, per_char="ch", delay0=0.3, step=0.09))
    nw = DISP.width(name, size)
    dot_r = 17
    dcx = nx + nw + 14 + dot_r
    d.add(f'<circle class="fb dotpop" cx="{num(dcx)}" cy="{base - dot_r}" r="{dot_r}" fill="{VOLT}"/>')

    # selection frame
    fx0, fy0 = nx - 12, base - 0.76 * size - 14
    fx1, fy1 = dcx + dot_r + 14, base + 16
    fw, fh = fx1 - fx0, fy1 - fy0
    d.add(f'<path class="frame" pathLength="1" d="M{num(fx0)} {num(fy0)} H{num(fx1)} V{num(fy1)} H{num(fx0)} Z" '
          f'fill="none" stroke="{VOLT}" stroke-width="1.6"/>')
    for i, (hx, hy) in enumerate([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)]):
        d.add(f'<rect class="fb handle" style="animation-delay:{1.7 + i*0.06:.2f}s" x="{num(hx-5)}" y="{num(hy-5)}" '
              f'width="10" height="10" fill="{TEXT}" stroke="{VOLT}" stroke-width="1.6"/>')
    dim = f"{round(fw)} × {round(fh)}"
    dw = MONOB.width(dim, 12) + 16
    d.add(f'<g class="fb dim">' + rect((fx0 + fx1) / 2 - dw / 2, fy1 + 12, dw, 22, 5, fill=VOLT)
          + d.text(dim, (fx0 + fx1) / 2, fy1 + 27, 12, MONOB, fill=INK, anchor="middle") + "</g>")

    # smart guides that flash while the cursor drags the corner
    d.add(f'<g class="guide" stroke="{CORAL}" stroke-width="1" stroke-dasharray="4 4">'
          f'<line x1="{num(fx1+22)}" y1="70" x2="{num(fx1+22)}" y2="590"/>'
          f'<line x1="24" y1="{num(fy1+12)}" x2="1176" y2="{num(fy1+12)}"/></g>')

    # subtitle
    d.add(f'<g class="r1">' + d.text("interfaces that feel fast and obvious,", 60, 432, 46, SERIF, fill=TEXT) + "</g>")
    d.add(f'<g class="r2">' + d.text("with a backend behind them that stays out of the way.", 62, 474, 24, BODY, fill=MUTED) + "</g>")

    # chips
    cx = 60
    for i, (label, dotc) in enumerate([("React · Next.js · TypeScript", VOLT), ("Vue on the side", SKY), ("Based in Indonesia", CORAL)]):
        g, w = pill(d, cx, 512, label, size=14, dot=dotc, cls="chip", style=f"animation-delay:{2.0 + i*0.1:.2f}s")
        d.add(g)
        cx += w + 10

    # stickers
    def sticker(cx, cy, rot, delay, phase, w, h, fill, stroke, inner, lift=False):
        content = rect(-w / 2, -h / 2, w, h, 16, fill=fill, **({"stroke": stroke, "stroke_width": 1.4} if stroke else {}))
        content += inner
        lifted = f'<g class="fb lift">{content}</g>' if lift else content
        return (f'<g transform="translate({cx} {cy}) rotate({rot})"><g class="fb stick" style="animation-delay:{delay}s">'
                f'<g class="float" style="animation-delay:{phase}s">{lifted}</g></g></g>')

    a_inner = (d.text("LIVE IN PRODUCTION", -134, -42, 13, MONOB, fill=INK)
               + f'<circle cx="128" cy="-47" r="5" fill="{INK}"/>'
               + f'<circle class="fb pulse" cx="128" cy="-47" r="5" fill="{INK}"/>'
               + d.text("3 apps", -136, 22, 66, DISP, fill=INK)
               + d.text("trackinglamaran.site · splitbills.site", -134, 48, 12, MONO, fill=INK)
               + d.text("fatihaljabar.com", -134, 66, 12, MONO, fill=INK))
    d.add(sticker(960, 196, -5, 1.55, 0, 300, 160, VOLT, None, a_inner))

    b_inner = (d.text("THESIS · CNN + BiLSTM", -128, -30, 13, MONOB, fill=MUTED)
               + d.text("75%", -130, 36, 64, DISP, fill=TEXT)
               + d.text("accuracy,", 44, 12, 26, SERIF, fill=SKY)
               + d.text("0.76 F1", 44, 38, 26, SERIF, fill=SKY))
    d.add(sticker(1024, 372, 4, 1.75, -2, 292, 130, PANEL2, LINE, b_inner, lift=True))

    c_inner = (d.text("GPA", -104, -12, 13, MONOB, fill=INK)
               + d.text("3.63", -106, 30, 46, DISP, fill=INK)
               + d.text("/ 4.00", 6, 30, 22, MONOB, fill=INK))
    d.add(sticker(904, 520, -3, 1.95, -4, 228, 96, CORAL, None, c_inner))

    toolbar = d.body[tb_start:tb_end]
    del d.body[tb_start:tb_end]
    d.body.extend(toolbar)

    # ---- status bar
    d.add(f'<path d="M0 600 L{W} 600 L{W} {H-22} Q{W} {H} {W-22} {H} L22 {H} Q0 {H} 0 {H-22} Z" fill="{PANEL}"/>')
    d.add(f'<line x1="0" y1="600" x2="{W}" y2="600" stroke="{LINE}"/>')
    d.add(f'<circle cx="30" cy="620" r="4.5" fill="{VOLT}"/><circle class="fb pulse" cx="30" cy="620" r="4.5" fill="{VOLT}"/>')
    d.add(d.text("Available for remote front-end and full-stack roles", 44, 624.5, 13, MONO, fill=TEXT))
    d.add(d.text("scroll to explore", W - 50, 624.5, 13, MONO, fill=MUTED, anchor="end"))
    d.add(f'<g class="bob">' + d.text("↓", W - 30, 625, 15, MONOB, fill=VOLT, anchor="middle") + "</g>")


    # ---- cursors
    hx, hy = fx1, fy1
    d.add(f'<g transform="translate({num(hx)} {num(hy)})"><g class="fin"><g class="fw">{cursor(d, VOLT, "Fatih")}</g></g></g>')
    d.add(f'<g transform="translate({num(click_x)} {num(click_y)})"><circle class="fb ripple" r="14" fill="none" stroke="{CORAL}" stroke-width="2"/></g>')
    d.add(f'<g transform="translate({num(click_x)} {num(click_y)})"><g class="yw"><g class="ft yc">{cursor(d, CORAL, "You")}</g></g></g>')


    save("hero.svg", d)


def main() -> None:
    hero()
    cards.build_all()
    sections.build_all()


if __name__ == "__main__":
    main()
