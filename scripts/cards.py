"""Project cards. Each card has a live 'stage' that acts out what the product does."""

from __future__ import annotations

import random

from svgkit import Doc, num, rect, wrap
from theme import *  # noqa: F403

CW, CH = 600, 464
SW, SH = 572, 262  # stage size, drawn at (14, 14)
PAPER = "#EEEBE3"


def kf(name: str, stops: list[tuple[float, str]]) -> str:
    """Keyframes helper: stops are (percent, declarations)."""
    body = "".join(f"{num(p)}%{{{decl}}}" for p, decl in stops)
    return f"@keyframes {name}{{{body}}}"


def chip_text(d: Doc, x, y, label, fg, bg, font=MONOB, size=11, h=22, padx=9, anchor="start", stroke=None):
    w = font.width(label, size) + padx * 2
    if anchor == "end":
        x -= w
    elif anchor == "middle":
        x -= w / 2
    extra = {"stroke": stroke, "stroke_width": 1.2} if stroke else {}
    return rect(x, y, w, h, 6, fill=bg, **extra) + d.text(label, x + padx, y + h / 2 + size * 0.36, size, font, fill=fg), w


def check(x, y, s, color, w=2.2):
    return (f'<path d="M{num(x)} {num(y+s*0.5)} L{num(x+s*0.38)} {num(y+s*0.86)} L{num(x+s)} {num(y+s*0.12)}" '
            f'fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')


def mini_cursor(color: str) -> str:
    return f'<path d="{CURSOR_PATH}" transform="scale(.8)" fill="{color}" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round"/>'


def tagged_cursor(d: Doc, color: str, label: str) -> str:
    tw = MONOB.width(label, 11)
    return (mini_cursor(color) + rect(12, 21, tw + 14, 20, 6, fill=color)
            + d.text(label, 19, 35, 11, MONOB, fill=INK))


# ---------------------------------------------------------------------------
# Stages (local coordinates: 0..572 x 0..262)
# ---------------------------------------------------------------------------
def stage_blockwave(d: Doc) -> None:
    a = 30
    w, h = a * 0.866, a * 0.5
    ox, oy = 176, 112
    pal = {
        "g": (VOLT, "#9DC214", "#7B980F"),
        "s": ("#454C57", "#2E333B", "#23272E"),
        "c": (CORAL, "#D9552F", "#B04322"),
        "k": (SKY, "#5EA2DA", "#4783B5"),
    }
    blocks = [(i, j, 0, "g") for i in range(4) for j in range(4)]
    blocks += [(0, 0, 1, "s"), (0, 0, 2, "s"), (0, 0, 3, "s"), (1, 0, 1, "s"), (0, 1, 1, "s"),
               (3, 3, 1, "k"), (2, 3, 1, "k"), (3, 2, 1, "k"), (3, 3, 2, "c")]
    blocks.sort(key=lambda b: (b[0] + b[1], b[2]))
    d.style(kf("vx", [(0, "transform:translateY(-300px);opacity:0"), (6, "transform:translateY(0);opacity:1"),
                      (8, "transform:translateY(-9px)"), (10, "transform:translateY(0)"),
                      (82, "transform:translateY(0);opacity:1"), (90, "transform:translateY(-40px);opacity:0"),
                      (100, "transform:translateY(-40px);opacity:0")])
            + f".vx{{animation:vx 9s cubic-bezier(.3,.7,.4,1) infinite backwards}}")
    for n, (i, j, k, kind) in enumerate(blocks):
        cx = ox + (i - j) * w
        cy = oy + (i + j) * h - k * a
        t, l, r = pal[kind]
        top = f"M{num(cx)} {num(cy-h)} L{num(cx+w)} {num(cy)} L{num(cx)} {num(cy+h)} L{num(cx-w)} {num(cy)} Z"
        left = f"M{num(cx-w)} {num(cy)} L{num(cx)} {num(cy+h)} L{num(cx)} {num(cy+h+a)} L{num(cx-w)} {num(cy+a)} Z"
        right = f"M{num(cx)} {num(cy+h)} L{num(cx+w)} {num(cy)} L{num(cx+w)} {num(cy+a)} L{num(cx)} {num(cy+h+a)} Z"
        d.add(f'<g class="vx" style="animation-delay:{n*0.07:.2f}s" stroke="{INK}" stroke-width=".8" stroke-linejoin="round">'
              f'<path d="{left}" fill="{l}"/><path d="{right}" fill="{r}"/><path d="{top}" fill="{t}"/></g>')

    # product panel
    px, py = 344, 46
    d.add(rect(px, py, 206, 196, 14, fill=PANEL2, stroke=LINE, stroke_width=1.2))
    # platform toggle
    d.add(rect(px + 12, py + 12, 182, 28, 8, fill=BG))
    d.style(kf("seg", [(0, "transform:translateX(0)"), (40, "transform:translateX(0)"), (46, "transform:translateX(91px)"),
                       (86, "transform:translateX(91px)"), (92, "transform:translateX(0)"), (100, "transform:translateX(0)")])
            + ".seg{animation:seg 9s cubic-bezier(.65,0,.35,1) infinite}")
    d.add(f'<g class="seg">{rect(px + 14, py + 14, 87, 24, 6, fill=VOLT)}</g>')
    d.style(kf("ink1", [(0, f"fill:{INK}"), (42, f"fill:{INK}"), (44, f"fill:{MUTED}"), (88, f"fill:{MUTED}"), (90, f"fill:{INK}")])
            + kf("ink2", [(0, f"fill:{MUTED}"), (42, f"fill:{MUTED}"), (44, f"fill:{INK}"), (88, f"fill:{INK}"), (90, f"fill:{MUTED}")])
            + ".i1{animation:ink1 9s steps(1) infinite}.i2{animation:ink2 9s steps(1) infinite}")
    d.add(d.text("Minecraft", px + 57, py + 30, 11, MONOB, anchor="middle", cls="i1", fill=INK))
    d.add(d.text("Roblox", px + 148, py + 30, 11, MONOB, anchor="middle", cls="i2", fill=MUTED))
    # thumbnail with a tiny voxel
    d.add(rect(px + 12, py + 50, 182, 66, 9, fill=BG))
    tx, ty, ta = px + 103, py + 70, 16
    tw, th = ta * 0.866, ta * 0.5
    d.add(f'<path d="M{num(tx-tw)} {num(ty)} L{num(tx)} {num(ty+th)} L{num(tx)} {num(ty+th+ta)} L{num(tx-tw)} {num(ty+ta)} Z" fill="#9DC214"/>'
          f'<path d="M{num(tx)} {num(ty+th)} L{num(tx+tw)} {num(ty)} L{num(tx+tw)} {num(ty+ta)} L{num(tx)} {num(ty+th+ta)} Z" fill="#7B980F"/>'
          f'<path d="M{num(tx)} {num(ty-th)} L{num(tx+tw)} {num(ty)} L{num(tx)} {num(ty+th)} L{num(tx-tw)} {num(ty)} Z" fill="{VOLT}"/>')
    d.add(rect(px + 12, py + 128, 120, 9, 4, fill="#2A2F37"), rect(px + 12, py + 144, 80, 9, 4, fill="#22262D"))
    # add to cart
    d.style(kf("press", [(0, "transform:scale(1)"), (30, "transform:scale(1)"), (32, "transform:scale(.9)"),
                         (35, "transform:scale(1)"), (100, "transform:scale(1)")])
            + ".press{animation:press 9s ease-out infinite}")
    d.add(f'<g class="fb press">{rect(px + 12, py + 160, 130, 26, 8, fill=VOLT)}'
          + d.text("Add to cart", px + 77, py + 177, 11, MONOB, fill=INK, anchor="middle") + "</g>")
    # cart + badge
    cx, cy = px + 172, py + 172
    d.add(f'<path d="M{cx-11} {cy-8} h3 l3 13 h13 l3 -9 h-17" fill="none" stroke="{TEXT}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>'
          f'<circle cx="{cx-1}" cy="{cy+9}" r="1.8" fill="{TEXT}"/><circle cx="{cx+8}" cy="{cy+9}" r="1.8" fill="{TEXT}"/>')
    d.style(kf("badge", [(0, "transform:scale(0)"), (32, "transform:scale(0)"), (36, "transform:scale(1.25)"),
                         (39, "transform:scale(1)"), (86, "transform:scale(1)"), (90, "transform:scale(0)"), (100, "transform:scale(0)")])
            + f".badge{{animation:badge 9s {SPRING} infinite}}")
    d.add(f'<g class="fb badge"><circle cx="{cx+12}" cy="{cy-11}" r="8" fill="{CORAL}"/>'
          + d.text("1", cx + 12, cy - 7, 11, MONOB, fill=INK, anchor="middle") + "</g>")
    # cursor clicking the button
    d.style(kf("bcur", [(0, "transform:translate(120px,90px);opacity:0"), (14, "transform:translate(120px,90px);opacity:1"),
                        (28, "transform:translate(0,0)"), (60, "transform:translate(0,0);opacity:1"),
                        (70, "transform:translate(60px,80px);opacity:0"), (100, "transform:translate(60px,80px);opacity:0")])
            + ".bcur{animation:bcur 9s cubic-bezier(.65,0,.35,1) infinite}")
    d.add(f'<g transform="translate({px+96} {py+176})"><g class="bcur">{mini_cursor(TEXT)}</g></g>')
    # toast
    d.style(kf("toast", [(0, "transform:translateY(60px);opacity:0"), (36, "transform:translateY(60px);opacity:0"),
                         (41, "transform:translateY(0);opacity:1"), (80, "transform:translateY(0);opacity:1"),
                         (86, "transform:translateY(60px);opacity:0"), (100, "transform:translateY(60px);opacity:0")])
            + f".toast{{animation:toast 9s {OUTQ} infinite}}")
    label = "Added to your library"
    tw2 = MONOB.width(label, 11) + 44
    d.add(f'<g class="toast">{rect(20, 214, tw2, 32, 10, fill=TEXT)}'
          f'<circle cx="38" cy="230" r="8" fill="{VOLT}"/>{check(33.5, 226, 9, INK, 2)}'
          + d.text(label, 54, 234, 11, MONOB, fill=INK) + "</g>")


def stage_ottodot(d: Doc) -> None:
    D = 8
    d.add(d.text("Science Trial · capacity 4", 24, 66, 12, MONO, fill=DIM))
    sx, sy, s, gap = 131, 92, 64, 18
    for i in range(3):
        x = sx + i * (s + gap)
        d.add(rect(x, sy, s, s, 14, fill=PANEL2, stroke=LINE, stroke_width=1.2))
        d.add(f'<circle cx="{x+32}" cy="{sy+25}" r="9" fill="{MUTED}"/>'
              f'<path d="M{x+16} {sy+52} q16 -22 32 0" fill="{MUTED}"/>')
    x4 = sx + 3 * (s + gap)
    d.style(kf("seatp", [(0, "opacity:.35"), (50, "opacity:1"), (100, "opacity:.35")])
            + ".seatp{animation:seatp 1.2s ease-in-out infinite}")
    d.add(f'<rect class="seatp" x="{x4}" y="{sy}" width="{s}" height="{s}" rx="14" fill="none" stroke="{VOLT}" stroke-width="1.6" stroke-dasharray="6 5"/>')
    d.add(d.text("1 left", x4 + 32, sy + 37, 12, MONOB, fill=VOLT, anchor="middle"))
    # seat fills for parent B
    d.style(kf("won", [(0, "opacity:0"), (37, "opacity:0"), (40, "opacity:1"), (86, "opacity:1"), (92, "opacity:0"), (100, "opacity:0")])
            + f".won{{animation:won {D}s linear infinite}}")
    d.add(f'<g class="won">{rect(x4, sy, s, s, 14, fill=SKY)}'
          f'<circle cx="{x4+32}" cy="{sy+25}" r="9" fill="{INK}"/><path d="M{x4+16} {sy+52} q16 -22 32 0" fill="{INK}"/></g>')
    # capacity bar
    by = 206
    d.add(rect(sx, by, 310, 8, 4, fill=PANEL2))
    d.add(rect(sx, by, 310 * 0.75, 8, 4, fill=MUTED))
    d.style(kf("cap", [(0, "transform:scaleX(0)"), (38, "transform:scaleX(0)"), (43, "transform:scaleX(1)"),
                       (86, "transform:scaleX(1)"), (92, "transform:scaleX(0)"), (100, "transform:scaleX(0)")])
            + f".cap{{animation:cap {D}s {OUTQ} infinite;transform-box:fill-box;transform-origin:left center}}")
    d.add(f'<rect class="cap" x="{sx + 310*0.75 - 4}" y="{by}" width="{310*0.25 + 4}" height="8" rx="4" fill="{SKY}"/>')
    d.style(kf("c3", [(0, "opacity:1"), (39, "opacity:1"), (40, "opacity:0"), (91, "opacity:0"), (92, "opacity:1")])
            + kf("c4", [(0, "opacity:0"), (39, "opacity:0"), (40, "opacity:1"), (91, "opacity:1"), (92, "opacity:0")])
            + f".c3{{animation:c3 {D}s steps(1) infinite}}.c4{{animation:c4 {D}s steps(1) infinite}}")
    d.add(f'<g class="c3" opacity="0">{d.text("3/4 confirmed", sx + 310, by + 28, 12, MONO, fill=MUTED, anchor="end")}</g>')
    d.add(f'<g class="c4">{d.text("4/4 confirmed", sx + 310, by + 28, 12, MONOB, fill=SKY, anchor="end")}</g>')
    # row lock
    lx, ly = x4 + 32, sy - 4
    d.style(kf("lock", [(0, "transform:scale(0)"), (31, "transform:scale(0)"), (34, "transform:scale(1.15)"),
                        (36, "transform:scale(1)"), (60, "transform:scale(1)"), (64, "transform:scale(0)"), (100, "transform:scale(0)")])
            + f".lock{{animation:lock {D}s {SPRING} infinite}}")
    lock_lbl = "ROW LOCK · FOR UPDATE"
    lw = MONOB.width(lock_lbl, 10) + 34
    d.add(f'<g class="fb lock">{rect(lx - lw/2, ly - 26, lw, 22, 6, fill=VOLT)}'
          f'<rect x="{num(lx - lw/2 + 9)}" y="{ly-17}" width="10" height="8" rx="1.5" fill="{INK}"/>'
          f'<path d="M{num(lx - lw/2 + 11)} {ly-17} v-3 a3 3 0 0 1 6 0 v3" fill="none" stroke="{INK}" stroke-width="1.6"/>'
          + d.text(lock_lbl, lx - lw / 2 + 25, ly - 11, 10, MONOB, fill=INK) + "</g>")
    # racing cursors
    tA, tB = (x4 + 18, sy + 50), (x4 + 40, sy + 40)
    rA = (40 - tA[0], 112 - tA[1])
    sA, sB = (40, 300), (560, 300)
    oA = (sA[0] - tA[0], sA[1] - tA[1])
    oB = (sB[0] - tB[0], sB[1] - tB[1])
    d.style(kf("ra", [(0, f"transform:translate({oA[0]}px,{oA[1]}px);opacity:1"), (8, f"transform:translate({oA[0]}px,{oA[1]}px)"),
                      (35, "transform:translate(-6px,6px)"), (40, "transform:translate(-6px,6px)"),
                      (48, f"transform:translate({rA[0]}px,{rA[1]}px)"), (86, f"transform:translate({rA[0]}px,{rA[1]}px);opacity:1"),
                      (92, f"transform:translate({rA[0]}px,{rA[1]}px);opacity:0"), (100, f"transform:translate({oA[0]}px,{oA[1]}px);opacity:0")])
            + kf("rb", [(0, f"transform:translate({oB[0]}px,{oB[1]}px);opacity:1"), (8, f"transform:translate({oB[0]}px,{oB[1]}px)"),
                        (33, "transform:translate(0,0)"), (86, "transform:translate(0,0);opacity:1"),
                        (92, "transform:translate(0,0);opacity:0"), (100, f"transform:translate({oB[0]}px,{oB[1]}px);opacity:0")])
            + f".ra{{animation:ra {D}s {INOUT} infinite}}.rb{{animation:rb {D}s {INOUT} infinite}}")
    d.style(kf("tagA", [(0, "opacity:0"), (46, "opacity:0"), (50, "opacity:1"), (86, "opacity:1"), (90, "opacity:0"), (100, "opacity:0")])
            + kf("tagB", [(0, "opacity:0"), (40, "opacity:0"), (44, "opacity:1"), (86, "opacity:1"), (90, "opacity:0"), (100, "opacity:0")])
            + f".tagA{{animation:tagA {D}s linear infinite}}.tagB{{animation:tagB {D}s linear infinite}}")
    ua, wa = chip_text(d, 26, 0, "seat_unavailable", INK, CORAL)
    cb, wb = chip_text(d, 26, 0, "confirmed", INK, SKY)
    d.add(f'<g transform="translate({tA[0]} {tA[1]})"><g class="ra">{tagged_cursor(d, CORAL, "Parent A")}'
          f'<g class="tagA" transform="translate(0 46)">{ua}</g></g></g>')
    d.add(f'<g transform="translate({tB[0]} {tB[1]})"><g class="rb">{tagged_cursor(d, SKY, "Parent B")}'
          f'<g class="tagB" transform="translate(-6 44)">{cb}</g></g></g>')


def stage_tracker(d: Doc) -> None:
    D = 11
    d.add(d.text("pipeline · 11 stages · 14 fields", 24, 66, 12, MONO, fill=DIM))
    x0, x1, ty = 40, 532, 168
    n = 11
    step = (x1 - x0) / (n - 1)
    d.add(f'<line x1="{x0}" y1="{ty}" x2="{x1}" y2="{ty}" stroke="{LINE}" stroke-width="3" stroke-linecap="round"/>')

    def arrive(s):
        return s * 8

    # progress line
    stops = []
    for s in range(n):
        stops.append((arrive(s), f"transform:scaleX({s/(n-1):.3f})"))
        if s < n - 1:
            stops.append((arrive(s) + 6, f"transform:scaleX({s/(n-1):.3f})"))
    stops += [(92, "transform:scaleX(1)"), (97, "transform:scaleX(0)"), (100, "transform:scaleX(0)")]
    d.style(kf("prog", stops) + f".prog{{animation:prog {D}s {INOUT} infinite;transform-box:fill-box;transform-origin:left center}}")
    d.add(f'<rect class="prog" x="{x0}" y="{ty-1.5}" width="{x1-x0}" height="3" rx="1.5" fill="{VOLT}"/>')
    for s in range(n):
        x = x0 + s * step
        d.add(f'<circle cx="{num(x)}" cy="{ty}" r="7" fill="{PANEL2}" stroke="{LINE}" stroke-width="1.5"/>')
        d.add(d.text(f"{s+1:02d}", x, ty + 28, 10, MONO, fill=DIM, anchor="middle"))
        p = arrive(s)
        if s:
            d.style(kf(f"nd{s}", [(0, "transform:scale(0)"), (p - 0.5, "transform:scale(0)"), (p + 1.5, "transform:scale(1)"),
                                   (93, "transform:scale(1)"), (97, "transform:scale(0)"), (100, "transform:scale(0)")])
                    + f".nd{s}{{animation:nd{s} {D}s {SPRING} infinite}}")
        d.add(f'<circle class="fb nd{s}" cx="{num(x)}" cy="{ty}" r="7" fill="{VOLT}"/>')
    # moving application card
    stops = []
    for s in range(n):
        tx = s * step
        stops.append((arrive(s), f"transform:translateX({tx:.1f}px)"))
        if s < n - 1:
            stops.append((arrive(s) + 6, f"transform:translateX({tx:.1f}px)"))
    stops += [(92, f"transform:translateX({(n-1)*step:.1f}px);opacity:1"), (96, f"transform:translateX({(n-1)*step:.1f}px);opacity:0"),
              (99, "transform:translateX(0);opacity:0"), (100, "transform:translateX(0);opacity:1")]
    d.style(kf("card", stops) + f".appc{{animation:card {D}s {INOUT} infinite}}")
    cw, chh = 92, 58
    card = rect(-cw / 2, -chh - 20, cw, chh, 10, fill=PANEL2, stroke=VOLT, stroke_width=1.4)
    card += rect(-cw / 2 + 9, -chh - 11, 14, 14, 4, fill=VOLT)
    card += rect(-cw / 2 + 29, -chh - 9, 48, 5, 2.5, fill="#3A404A") + rect(-cw / 2 + 29, -chh - 0, 30, 5, 2.5, fill="#2A2F37")
    for k in range(14):
        cxk = -cw / 2 + 12 + (k % 7) * 11.3
        cyk = -chh + 24 + (k // 7) * 9
        card += f'<circle cx="{num(cxk)}" cy="{num(cyk)}" r="2.6" fill="{MUTED}"/>'
    card += f'<path d="M-6 -21 L0 -13 L6 -21" fill="{PANEL2}" stroke="{VOLT}" stroke-width="1.4" stroke-linejoin="round"/>'
    card += f'<rect x="-7" y="-23" width="14" height="3" fill="{PANEL2}"/>'
    d.add(f'<g transform="translate({x0} {ty})"><g class="appc">{card}</g></g>')
    # reminders
    for s, label, color in [(3, "Deadline reminder", CORAL), (6, "Interview reminder", SKY)]:
        p = arrive(s)
        d.style(kf(f"rem{s}", [(0, "opacity:0;transform:translateY(8px)"), (p, "opacity:0;transform:translateY(8px)"),
                                (p + 2, "opacity:1;transform:translateY(0)"), (p + 13, "opacity:1;transform:translateY(0)"),
                                (p + 16, "opacity:0;transform:translateY(0)"), (100, "opacity:0")])
                + f".rem{s}{{animation:rem{s} {D}s {OUTQ} infinite}}")
        x = x0 + s * step
        lw = MONOB.width(label, 11) + 40
        bx = min(max(x - lw / 2, 16), SW - 16 - lw)
        bell = (f'<path d="M{num(bx+13)} 222 a6 6 0 0 1 12 0 v5 l2 3 h-16 l2 -3 Z" fill="{INK}"/>'
                f'<circle cx="{num(bx+19)}" cy="232.5" r="2" fill="{INK}"/>')
        d.add(f'<g class="rem{s}">{rect(bx, 210, lw, 30, 9, fill=color)}{bell}'
              + d.text(label, bx + 32, 229, 11, MONOB, fill=INK) + "</g>")
    # offer
    d.style(kf("fin", [(0, "transform:scale(0)"), (80, "transform:scale(0)"), (83, "transform:scale(1.2)"), (85, "transform:scale(1)"),
                       (93, "transform:scale(1)"), (96, "transform:scale(0)"), (100, "transform:scale(0)")])
            + f".fin{{animation:fin {D}s {SPRING} infinite}}")
    d.add(f'<g class="fb fin"><circle cx="{x1}" cy="{ty}" r="13" fill="{VOLT}"/>{check(x1-6, ty-6, 12, INK, 2.4)}</g>')


def stage_splitbill(d: Doc) -> None:
    D = 9
    rx, ry, rw, rh = 44, 34, 184, 210
    zig = "".join(f" L{num(rx + rw - i*11.5 - 5.75)} {ry+rh+6} L{num(rx + rw - (i+1)*11.5)} {ry+rh}" for i in range(16))
    d.add(f'<path d="M{rx} {ry} H{rx+rw} V{ry+rh}{zig} Z" fill="{PAPER}"/>')
    d.add(rect(rx + 14, ry + 14, 70, 9, 3, fill="#2B2F36"), rect(rx + 14, ry + 30, 110, 5, 2, fill="#B9B6AE"))
    rows = [(0.62, "35.000"), (0.48, "42.000"), (0.70, "18.000"), (0.40, "30.000")]
    for i, (wfrac, price) in enumerate(rows):
        y = ry + 56 + i * 24
        d.add(rect(rx + 14, y, 90 * wfrac + 20, 7, 3, fill="#8E8B84"))
        d.add(d.text(price, rx + rw - 14, y + 8, 11, MONOB, fill="#2B2F36", anchor="end"))
    d.add(f'<line x1="{rx+14}" y1="{ry+156}" x2="{rx+rw-14}" y2="{ry+156}" stroke="#8E8B84" stroke-dasharray="3 3"/>')
    d.add(d.text("TOTAL", rx + 14, ry + 180, 11, MONOB, fill="#2B2F36"))
    d.add(d.text("Rp 125.000", rx + rw - 14, ry + 181, 14, MONOB, fill=INK, anchor="end"))
    # OCR boxes
    for i in range(5):
        y = ry + 50 + i * 24 if i < 4 else ry + 165
        h = 19 if i < 4 else 22
        p = 6 + i * 6.5 if i < 4 else 34
        d.style(kf(f"ocr{i}", [(0, "opacity:0"), (p, "opacity:0"), (p + 1, "opacity:1"), (86, "opacity:1"), (90, "opacity:0"), (100, "opacity:0")])
                + f".ocr{i}{{animation:ocr{i} {D}s linear infinite}}")
        x = rx + rw - 66 if i < 4 else rx + rw - 106
        w = 58 if i < 4 else 98
        d.add(f'<rect class="ocr{i}" x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{VOLT}" fill-opacity=".18" stroke="{VOLT}" stroke-width="1.4"/>')
    # scanning laser
    d.style(kf("scan", [(0, "transform:translateY(0);opacity:0"), (3, "opacity:1"), (36, "transform:translateY(200px);opacity:1"),
                        (40, "transform:translateY(200px);opacity:0"), (100, "transform:translateY(200px);opacity:0")])
            + f".scan{{animation:scan {D}s linear infinite}}")
    d.add(f'<g class="scan"><rect x="{rx-8}" y="{ry+2}" width="{rw+16}" height="22" fill="{VOLT}" opacity=".14"/>'
          f'<rect x="{rx-8}" y="{ry+22}" width="{rw+16}" height="2.5" rx="1" fill="{VOLT}"/></g>')
    # split
    d.add(d.text("in-browser OCR, then split 3 ways", 268, 66, 12, MONO, fill=DIM))
    people = [("A", VOLT, "41.667"), ("B", CORAL, "41.667"), ("C", SKY, "41.666")]
    for i, (who, col, amt) in enumerate(people):
        y = 88 + i * 46
        p = 42 + i * 5
        d.style(kf(f"pp{i}", [(0, "opacity:0;transform:translateX(30px)"), (p, "opacity:0;transform:translateX(30px)"),
                               (p + 4, "opacity:1;transform:translateX(0)"), (86, "opacity:1;transform:translateX(0)"),
                               (90, "opacity:0;transform:translateX(0)"), (100, "opacity:0")])
                + f".pp{i}{{animation:pp{i} {D}s {OUTQ} infinite}}")
        d.style(kf(f"ln{i}", [(0, "stroke-dashoffset:1"), (p - 3, "stroke-dashoffset:1"), (p + 1, "stroke-dashoffset:0"),
                               (86, "stroke-dashoffset:0;opacity:1"), (90, "opacity:0"), (100, "opacity:0;stroke-dashoffset:1")])
                + f".ln{i}{{animation:ln{i} {D}s {INOUT} infinite;stroke-dasharray:1}}")
        d.add(f'<path class="ln{i}" pathLength="1" d="M{rx+rw+4} {ry+176} C 258 {ry+176}, 248 {y+16}, 280 {y+16}" fill="none" stroke="{col}" stroke-width="1.5"/>')
        g = rect(282, y, 266, 34, 10, fill=PANEL2, stroke=LINE, stroke_width=1.2)
        g += f'<circle cx="300" cy="{y+17}" r="10" fill="{col}"/>' + d.text(who, 300, y + 21, 11, MONOB, fill=INK, anchor="middle")
        g += d.text("pays", 320, y + 21.5, 12, MONO, fill=MUTED)
        g += d.text(f"Rp {amt}", 536, y + 22.5, 16, MONOB, fill=TEXT, anchor="end")
        d.add(f'<g class="pp{i}">{g}</g>')
    d.style(kf("sum", [(0, "opacity:0;transform:scale(.6)"), (60, "opacity:0;transform:scale(.6)"), (64, "opacity:1;transform:scale(1)"),
                       (86, "opacity:1;transform:scale(1)"), (90, "opacity:0"), (100, "opacity:0")])
            + f".sum{{animation:sum {D}s {SPRING} infinite}}")
    s_lbl = "= Rp 125.000 · not one rupiah lost"
    sw = MONOB.width(s_lbl, 11) + 20
    d.add(f'<g class="fb sum">{rect(548 - sw, 228, sw, 24, 7, fill=VOLT)}' + d.text(s_lbl, 558 - sw, 244, 11, MONOB, fill=INK) + "</g>")


def stage_nusaride(d: Doc) -> None:
    D = 9
    # skyline (two copies for a seamless loop)
    sky = ""
    rnd = random.Random(7)
    x = 0
    while x < SW:
        bw = rnd.randint(26, 54)
        bh = rnd.randint(18, 58)
        sky += rect(x, 196 - bh, bw - 4, bh, 3, fill="#171A1F")
        x += bw
    d.style("@keyframes city{from{transform:translateX(0)}to{transform:translateX(-572px)}}.city{animation:city 22s linear infinite}")
    d.add(f'<g class="city">{sky}<g transform="translate({SW} 0)">{sky}</g></g>')
    # road
    d.add(rect(0, 196, SW, 66, 0, fill="#14171B"))
    d.add(f'<line x1="0" y1="196" x2="{SW}" y2="196" stroke="{LINE}"/>')
    d.style("@keyframes lane{from{transform:translateX(0)}to{transform:translateX(-48px)}}.lane{animation:lane .6s linear infinite}")
    d.add(f'<g class="lane">' + "".join(rect(i * 48, 232, 26, 3, 1.5, fill="#3A404A") for i in range(14)) + "</g>")
    # van
    d.style("@keyframes bump{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}.bump{animation:bump .45s ease-in-out infinite}"
            "@keyframes spin{to{transform:rotate(360deg)}}.spin{animation:spin .5s linear infinite;transform-box:fill-box;transform-origin:center}")
    vx, vy = 70, 166
    van = (f'<path d="M{vx} {vy+34} V{vy+8} Q{vx} {vy} {vx+8} {vy} H{vx+92} Q{vx+104} {vy} {vx+112} {vy+12} L{vx+128} {vy+24} '
           f'Q{vx+132} {vy+27} {vx+132} {vy+32} V{vy+34} Q{vx+132} {vy+40} {vx+126} {vy+40} H{vx+6} Q{vx} {vy+40} {vx} {vy+34} Z" fill="{VOLT}"/>'
           + rect(vx + 10, vy + 7, 24, 15, 3, fill=INK) + rect(vx + 40, vy + 7, 24, 15, 3, fill=INK) + rect(vx + 70, vy + 7, 24, 15, 3, fill=INK)
           + f'<path d="M{vx+100} {vy+7} H{vx+106} L{vx+118} {vy+22} H{vx+100} Z" fill="{INK}"/>'
           + rect(vx + 124, vy + 28, 8, 4, 1, fill=PAPER))
    wheels = "".join(f'<g transform="translate({vx+cx} {vy+40})"><circle r="10" fill="{INK}"/>'
                     f'<circle class="spin" r="6" fill="none" stroke="{MUTED}" stroke-width="2" stroke-dasharray="4 3"/></g>' for cx in (26, 104))
    d.add(f'<g class="bump">{van}</g>{wheels}')
    # availability grid
    d.add(d.text("availability · per unit", 24, 66, 12, MONO, fill=DIM))
    days = "MTWTFSS"
    gx, gy = 80, 78
    for c, dd in enumerate(days):
        d.add(d.text(dd, gx + c * 26 + 11, gy + 10, 10, MONO, fill=DIM, anchor="middle"))
    units = ["Car", "Hiace", "Bus"]
    booked = {1: [2, 3, 4], 0: [0, 1], 2: [5]}
    for r, u in enumerate(units):
        y = gy + 18 + r * 22
        d.add(d.text(u, gx - 10, y + 12, 11, MONO, fill=MUTED, anchor="end"))
        for c in range(7):
            x = gx + c * 26
            d.add(rect(x, y, 22, 16, 4, fill=PANEL2, stroke=LINE, stroke_width=1))
            if c in booked.get(r, []):
                order = (0 if r == 1 else 1 if r == 0 else 2) * 3 + booked[r].index(c)
                p = 10 + order * 3
                col = CORAL if r == 1 else MUTED
                d.style(kf(f"bk{r}{c}", [(0, "transform:scale(0)"), (p, "transform:scale(0)"), (p + 2, "transform:scale(1)"),
                                         (88, "transform:scale(1)"), (92, "transform:scale(0)"), (100, "transform:scale(0)")])
                        + f".bk{r}{c}{{animation:bk{r}{c} {D}s {SPRING} infinite}}")
                d.add(f'<rect class="fb bk{r}{c}" x="{x}" y="{y}" width="22" height="16" rx="4" fill="{col}"/>')
            else:
                d.add(f'<circle cx="{x+11}" cy="{y+8}" r="2.2" fill="{VOLT}" opacity=".7"/>')
    # ID / EN toggle
    tx, ty = 318, 52
    d.add(rect(tx, ty, 92, 30, 9, fill=PANEL2, stroke=LINE, stroke_width=1))
    d.style(kf("lang", [(0, "transform:translateX(0)"), (45, "transform:translateX(0)"), (50, "transform:translateX(44px)"),
                        (88, "transform:translateX(44px)"), (93, "transform:translateX(0)"), (100, "transform:translateX(0)")])
            + f".lang{{animation:lang {D}s {INOUT} infinite}}")
    d.add(f'<g class="lang">{rect(tx + 3, ty + 3, 42, 24, 7, fill=VOLT)}</g>')
    d.add(d.text("ID", tx + 24, ty + 19.5, 11, MONOB, fill=TEXT, anchor="middle", style="mix-blend-mode:difference"))
    d.add(d.text("EN", tx + 68, ty + 19.5, 11, MONOB, fill=TEXT, anchor="middle", style="mix-blend-mode:difference"))
    # PDF invoice
    px, py = 446, 44
    d.style(kf("pdf", [(0, "transform:translateY(-150px) rotate(-14deg)"), (30, "transform:translateY(-150px) rotate(-14deg)"),
                       (38, "transform:translateY(0) rotate(4deg)"), (41, "transform:translateY(0) rotate(3deg)"),
                       (86, "transform:translateY(0) rotate(3deg)"), (94, "transform:translateY(-150px) rotate(-6deg)"),
                       (100, "transform:translateY(-150px) rotate(-14deg)")])
            + f".pdf{{animation:pdf {D}s {OUTQ} infinite;transform-box:fill-box;transform-origin:center}}")
    doc = rect(px, py, 96, 122, 6, fill=PAPER)
    doc += rect(px + 10, py + 12, 34, 14, 3, fill=CORAL) + d.text("PDF", px + 27, py + 23, 10, MONOB, fill=INK, anchor="middle")
    doc += d.text("INVOICE", px + 10, py + 44, 10, MONOB, fill=INK)
    for k in range(4):
        doc += rect(px + 10, py + 54 + k * 12, 76 - (k % 2) * 22, 5, 2, fill="#B9B6AE")
    doc += rect(px + 10, py + 104, 40, 7, 2, fill=INK)
    d.add(f'<g class="pdf">{doc}</g>')


def stage_vetready(d: Doc) -> None:
    D = 10
    # CBT panel
    px, py, pw, ph = 24, 50, 276, 196
    d.add(rect(px, py, pw, ph, 14, fill=PANEL2, stroke=LINE, stroke_width=1.2))
    d.add(d.text("CBT simulation", px + 16, py + 28, 13, MONOB, fill=TEXT))
    d.add(d.text("8 questions · timed", px + 16, py + 46, 11, MONO, fill=DIM))
    cx, cy, r = px + pw - 32, py + 32, 15
    circ = 2 * 3.14159 * r
    d.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}" stroke-width="4"/>')
    d.style(kf("timer", [(0, "stroke-dashoffset:0"), (96, f"stroke-dashoffset:{circ:.1f}"), (100, "stroke-dashoffset:0")])
            + f".timer{{animation:timer {D}s linear infinite}}")
    d.add(f'<circle class="timer" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{VOLT}" stroke-width="4" stroke-linecap="round" '
          f'stroke-dasharray="{circ:.1f}" transform="rotate(-90 {cx} {cy})"/>')
    for i in range(8):
        col, row = i % 4, i // 4
        x = px + 16 + col * 62
        y = py + 72 + row * 52
        d.add(rect(x, y, 54, 42, 9, fill=BG, stroke=LINE, stroke_width=1))
        p = 6 + i * 8
        flagged = i == 4
        color = CORAL if flagged else VOLT
        d.style(kf(f"q{i}", [(0, "transform:scale(0)"), (p, "transform:scale(0)"), (p + 2, "transform:scale(1.1)"), (p + 3, "transform:scale(1)"),
                              (90, "transform:scale(1)"), (94, "transform:scale(0)"), (100, "transform:scale(0)")])
                + f".q{i}{{animation:q{i} {D}s {SPRING} infinite}}")
        d.add(f'<rect class="fb q{i}" x="{x}" y="{y}" width="54" height="42" rx="9" fill="{color}"/>')
        d.add(d.text(str(i + 1), x + 27, y + 26, 14, MONOB, fill=MUTED, anchor="middle"))
        d.add(f'<g class="fb q{i}">' + d.text(str(i + 1), x + 27, y + 26, 14, MONOB, fill=INK, anchor="middle") + "</g>")
        if flagged:
            d.add(f'<g class="fb q{i}"><path d="M{x+41} {y+8} v14 M{x+41} {y+9} h8 l-2.5 3.5 l2.5 3.5 h-8" fill="{INK}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/></g>')
    # OSCE monitor
    mx, my, mw, mh = 314, 50, 236, 196
    d.add(rect(mx, my, mw, mh, 14, fill=PANEL2, stroke=LINE, stroke_width=1.2))
    d.add(d.text("OSCE clinical case", mx + 16, my + 28, 13, MONOB, fill=TEXT))
    d.style("@keyframes beat{0%,100%{transform:scale(1)}15%{transform:scale(1.4)}30%{transform:scale(1)}}.beat{animation:beat 1s ease-out infinite}")
    d.add(f'<circle class="fb beat" cx="{mx+mw-24}" cy="{my+24}" r="5" fill="{CORAL}"/>')
    d.add(f'<clipPath id="ecg"><rect x="{mx+12}" y="{my+40}" width="{mw-24}" height="80" rx="8"/></clipPath>')
    d.add(rect(mx + 12, my + 40, mw - 24, 80, 8, fill=BG))
    seg = "l18 0 l6 -6 l6 6 l8 0 l5 10 l7 -44 l7 50 l6 -16 l10 0 l7 -8 l7 8 l23 0"
    period = 110
    pts = "M0 0 " + " ".join([seg] * 8)
    d.style(f"@keyframes ecgm{{from{{transform:translateX(0)}}to{{transform:translateX(-{period}px)}}}}.ecgm{{animation:ecgm 1.1s linear infinite}}")
    d.add(f'<g clip-path="url(#ecg)"><g transform="translate({mx+12} {my+86})"><g class="ecgm">'
          f'<path d="{pts}" fill="none" stroke="{VOLT}" stroke-width="2" stroke-linejoin="round"/></g></g></g>')
    steps = ["anamnesis", "exam", "decision"]
    sx = mx + 12
    for i, st in enumerate(steps):
        w = MONOB.width(st, 10) + 16
        p = 20 + i * 22
        d.add(rect(sx, my + 134, w, 22, 6, fill=BG, stroke=LINE, stroke_width=1))
        d.add(d.text(st, sx + 8, my + 149, 10, MONOB, fill=DIM))
        d.style(kf(f"os{i}", [(0, "opacity:0"), (p, "opacity:0"), (p + 2, "opacity:1"), (90, "opacity:1"), (94, "opacity:0"), (100, "opacity:0")])
                + f".os{i}{{animation:os{i} {D}s linear infinite}}")
        d.add(f'<g class="os{i}">{rect(sx, my + 134, w, 22, 6, fill=SKY)}{d.text(st, sx + 8, my + 149, 10, MONOB, fill=INK)}</g>')
        sx += w + 6
    d.style(kf("res", [(0, "opacity:0;transform:translateY(6px)"), (78, "opacity:0;transform:translateY(6px)"),
                       (82, "opacity:1;transform:translateY(0)"), (92, "opacity:1"), (95, "opacity:0"), (100, "opacity:0")])
            + f".res{{animation:res {D}s {OUTQ} infinite}}")
    d.add(f'<g class="res">{check(mx+14, my+168, 11, VOLT)}' + d.text("result summary ready", mx + 34, my + 178, 11, MONO, fill=TEXT) + "</g>")


def stage_ramatama(d: Doc) -> None:
    D = 10
    nodes = [("Quotation", 78, 152), ("Booking", 184, 112), ("Invoice", 290, 152), ("Payment", 396, 112), ("Receipt", 500, 152)]
    path = f"M{nodes[0][1]} {nodes[0][2]}"
    for (_, x0, y0), (_, x1, y1) in zip(nodes, nodes[1:]):
        mxp = (x0 + x1) / 2
        path += f" C{num(mxp)} {y0} {num(mxp)} {y1} {x1} {y1}"
    d.add(f'<path d="{path}" fill="none" stroke="{LINE}" stroke-width="2" stroke-dasharray="2 6" stroke-linecap="round"/>')
    # flight arc
    arc = "M70 92 Q 300 -10 540 78"
    d.add(f'<path d="{arc}" fill="none" stroke="#2A2F37" stroke-width="1.5" stroke-dasharray="3 6"/>')
    plane = (f'<path d="M-9 -1.5 L3 -1.5 L8 -7 L10.5 -7 L7.5 -1.5 L12 -1.5 Q14 0 12 1.5 L7.5 1.5 L10.5 7 L8 7 L3 1.5 L-9 1.5 Z" '
             f'fill="{SKY}"/>')
    d.add(f'<g>{plane}<animateMotion dur="7s" repeatCount="indefinite" rotate="auto" path="{arc}" '
          f'keyPoints="0;1;1" keyTimes="0;.85;1" calcMode="linear"/></g>')
    # node pills and token
    n = len(nodes)
    seg = 70 / (n - 1)
    kp, kt = [], []
    for i in range(n):
        t_arrive = 4 + i * seg
        kp += [i / (n - 1), i / (n - 1)]
        kt += [t_arrive, t_arrive + seg * 0.45 if i < n - 1 else 92]
    kp = [0] + kp + [1]
    kt = [0] + kt + [100]
    # The cubic segments have similar lengths, so equal keyPoints spacing is close enough.
    d.add(f'<g><circle r="12" fill="{VOLT}" opacity=".2"/><circle r="6" fill="{VOLT}"/>'
          f'<animateMotion dur="{D}s" repeatCount="indefinite" calcMode="spline" path="{path}" '
          f'keyPoints="{";".join(num(p) for p in kp)}" keyTimes="{";".join(num(t/100) for t in kt)}" '
          f'keySplines="{";".join([".65 0 .35 1"] * (len(kt) - 1))}"/></g>')
    for i, (label, x, y) in enumerate(nodes):
        w = MONOB.width(label, 12) + 26
        p = 4 + i * seg
        d.add(rect(x - w / 2, y + 16, w, 28, 8, fill=PANEL2, stroke=LINE, stroke_width=1.2))
        d.add(d.text(label, x, y + 34.5, 12, MONOB, fill=MUTED, anchor="middle"))
        d.style(kf(f"nd{i}", [(0, "opacity:0"), (max(p - 0.5, 0), "opacity:0"), (p + 1, "opacity:1"), (92, "opacity:1"), (96, "opacity:0"), (100, "opacity:0")])
                + f".nd{i}{{animation:nd{i} {D}s linear infinite}}")
        d.add(f'<g class="nd{i}">{rect(x - w/2, y + 16, w, 28, 8, fill=VOLT)}{d.text(label, x, y + 34.5, 12, MONOB, fill=INK, anchor="middle")}</g>')
        d.add(f'<circle cx="{x}" cy="{y}" r="4" fill="{TEXT}"/>')
    # currency cycler + roles
    d.add(rect(24, 220, 186, 28, 8, fill=PANEL2, stroke=LINE, stroke_width=1))
    d.add(d.text("display", 36, 238, 11, MONO, fill=DIM))
    for i, cur in enumerate(["IDR", "USD", "SGD"]):
        a0 = i * 33.3
        stops = [(0, "opacity:0;transform:translateY(8px)")] if i else [(0, "opacity:1;transform:translateY(0)")]
        stops += [(a0 + 0.01, "opacity:0;transform:translateY(8px)") if i else (0.01, "opacity:1;transform:translateY(0)"),
                  (a0 + 2, "opacity:1;transform:translateY(0)"), (a0 + 31, "opacity:1;transform:translateY(0)"),
                  (a0 + 33, "opacity:0;transform:translateY(-8px)"), (100, "opacity:0;transform:translateY(-8px)")]
        d.style(kf(f"cur{i}", stops) + f".cur{i}{{animation:cur{i} 6s {OUTQ} infinite}}")
        d.add(f'<g class="cur{i}">{d.text(cur, 92, 238.5, 12, MONOB, fill=VOLT)}</g>')
    d.add(d.text("· AR / AP", 126, 238, 11, MONO, fill=MUTED))
    rb, rw2 = chip_text(d, 548, 222, "role-based access", MUTED, PANEL2, anchor="end", stroke=LINE, h=26)
    d.add(rb)


def stage_formkey(d: Doc) -> None:
    D = 8
    kx, ky = 56, 176
    d.add(rect(kx - 18, ky - 12, 460, 86, 16, fill=PANEL2, stroke=LINE, stroke_width=1.2))
    slot = 3
    for i in range(6):
        x = kx + i * 72
        d.style(kf(f"key{i}", [(0, "transform:translateY(0)"), (30 + i * 2, "transform:translateY(0)"), (32 + i * 2, "transform:translateY(5px)"),
                                (35 + i * 2, "transform:translateY(0)"), (100, "transform:translateY(0)")])
                + f".key{i}{{animation:key{i} {D}s ease-out infinite}}")
        if i == slot:
            d.add(rect(x + 8, ky + 4, 48, 50, 8, fill=BG))
            d.add(f'<path d="M{x+32} {ky+18} v22 M{x+21} {ky+29} h22" stroke="{MUTED}" stroke-width="4" stroke-linecap="round"/>')
            continue
        d.add(f'<g class="key{i}">{rect(x, ky, 64, 56, 10, fill="#2A2F37")}{rect(x + 7, ky + 4, 50, 38, 8, fill="#363C46")}</g>')
    # artisan keycap
    ax = kx + slot * 72
    art = rect(ax, ky, 64, 56, 10, fill="#C2512B") + rect(ax + 7, ky + 4, 50, 38, 8, fill=CORAL)
    art += f'<circle cx="{ax+42}" cy="{ky+15}" r="5" fill="{VOLT}"/>'
    art += f'<path d="M{ax+11} {ky+38} L{ax+24} {ky+20} L{ax+31} {ky+29} L{ax+37} {ky+23} L{ax+52} {ky+38} Z" fill="{INK}" opacity=".85"/>'
    d.style(kf("art", [(0, "transform:translateY(-230px) rotate(-12deg)"), (12, "transform:translateY(-230px) rotate(-12deg)"),
                       (26, "transform:translateY(6px) rotate(0)"), (29, "transform:translateY(-4px)"), (31, "transform:translateY(0)"),
                       (86, "transform:translateY(0)"), (96, "transform:translateY(-230px) rotate(10deg)"), (100, "transform:translateY(-230px) rotate(-12deg)")])
            + f".art{{animation:art {D}s cubic-bezier(.3,.7,.4,1) infinite;transform-box:fill-box;transform-origin:center}}")
    d.add(f'<g class="art">{art}</g>')
    d.style(kf("spark", [(0, "transform:scale(0);opacity:0"), (27, "transform:scale(0);opacity:1"), (36, "transform:scale(1.6);opacity:0"), (100, "opacity:0")])
            + f".spark{{animation:spark {D}s ease-out infinite}}")
    d.add(f'<g transform="translate({ax+32} {ky+28})"><circle class="fb spark" r="40" fill="none" stroke="{VOLT}" stroke-width="2"/></g>')
    # bag + payment status
    d.add(d.text("small keys, extraordinary character", 24, 66, 12, MONO, fill=DIM))
    bx, by = 500, 92
    d.add(f'<path d="M{bx-16} {by-6} h32 l-3 34 h-26 Z" fill="none" stroke="{TEXT}" stroke-width="2" stroke-linejoin="round"/>'
          f'<path d="M{bx-7} {by-6} v-4 a7 7 0 0 1 14 0 v4" fill="none" stroke="{TEXT}" stroke-width="2"/>')
    d.style(kf("bb", [(0, "transform:scale(0)"), (33, "transform:scale(0)"), (37, "transform:scale(1.25)"), (40, "transform:scale(1)"),
                      (88, "transform:scale(1)"), (92, "transform:scale(0)"), (100, "transform:scale(0)")])
            + f".bb{{animation:bb {D}s {SPRING} infinite}}")
    d.add(f'<g class="fb bb"><circle cx="{bx+16}" cy="{by-8}" r="9" fill="{VOLT}"/>{d.text("1", bx+16, by-4, 11, MONOB, fill=INK, anchor="middle")}</g>')
    d.add(d.text("PayPal simulator", 24, 102, 11, MONO, fill=DIM))
    pend, pw = chip_text(d, 150, 87, "pending", CORAL, BG, stroke=CORAL, h=22)
    paid, _ = chip_text(d, 150, 87, "paid", INK, VOLT, h=22)
    d.style(kf("st1", [(0, "opacity:1"), (55, "opacity:1"), (56, "opacity:0"), (91, "opacity:0"), (92, "opacity:1")])
            + kf("st2", [(0, "opacity:0"), (55, "opacity:0"), (56, "opacity:1"), (91, "opacity:1"), (92, "opacity:0")])
            + f".st1{{animation:st1 {D}s steps(1) infinite}}.st2{{animation:st2 {D}s steps(1) infinite}}")
    d.add(f'<g class="st1">{pend}</g><g class="st2">{paid}</g>')


def stage_event(d: Doc) -> None:
    D = 9
    rnd = random.Random(3)
    slot_w, slot_h = 74, 18
    cols = [26, 140, 254, 368]
    ys = [56 + i * 25 for i in range(8)]
    rounds = [ys]
    for r in range(3):
        prev = rounds[-1]
        rounds.append([(prev[2 * i] + prev[2 * i + 1]) / 2 for i in range(len(prev) // 2)])
    picks = [[0, 1, 0, 1], [1, 0], [0]]  # which of each pair advances
    for r, ylist in enumerate(rounds):
        for i, y in enumerate(ylist):
            x = cols[r]
            d.add(rect(x, y, slot_w, slot_h, 5, fill=PANEL2, stroke=LINE, stroke_width=1))
            if r == 0:
                d.add(d.text(f"{i+1}", x + 9, y + 13, 10, MONOB, fill=DIM))
                d.add(rect(x + 22, y + 7, 26 + rnd.randint(0, 20), 4, 2, fill="#3A404A"))
    # connectors + winners
    for r in range(3):
        src = rounds[r]
        dst = rounds[r + 1]
        p = 12 + r * 22
        for j, y2 in enumerate(dst):
            a, b = src[2 * j] + slot_h / 2, src[2 * j + 1] + slot_h / 2
            x0 = cols[r] + slot_w
            xm = x0 + 20
            x2 = cols[r + 1]
            d.add(f'<path d="M{x0} {a} H{xm} V{b} H{x0} M{xm} {y2+slot_h/2} H{x2}" fill="none" stroke="{LINE}" stroke-width="1.4"/>')
            wy = src[2 * j + picks[r][j]] + slot_h / 2
            d.style(kf(f"w{r}{j}", [(0, "stroke-dashoffset:1"), (p, "stroke-dashoffset:1"), (p + 8, "stroke-dashoffset:0"),
                                    (90, "stroke-dashoffset:0;opacity:1"), (94, "opacity:0"), (100, "opacity:0;stroke-dashoffset:1")])
                    + f".w{r}{j}{{animation:w{r}{j} {D}s {INOUT} infinite;stroke-dasharray:1}}")
            d.add(f'<path class="w{r}{j}" pathLength="1" d="M{x0} {wy} H{xm} V{y2+slot_h/2} H{x2}" fill="none" stroke="{VOLT}" stroke-width="2"/>')
            d.style(kf(f"f{r}{j}", [(0, "opacity:0"), (p + 7, "opacity:0"), (p + 9, "opacity:1"), (90, "opacity:1"), (94, "opacity:0"), (100, "opacity:0")])
                    + f".f{r}{j}{{animation:f{r}{j} {D}s linear infinite}}")
            col = VOLT if r == 2 else "#3A404A"
            d.add(f'<rect class="f{r}{j}" x="{cols[r+1]}" y="{y2}" width="{slot_w}" height="{slot_h}" rx="5" fill="{col}"/>')
            if r < 2:
                d.add(f'<rect class="f{r}{j}" x="{cols[r+1]+22}" y="{y2+7}" width="{30 + (j*7)%14}" height="4" rx="2" fill="{MUTED}"/>')
    fy = rounds[3][0]
    d.style(kf("crown", [(0, "transform:scale(0) rotate(-30deg)"), (64, "transform:scale(0) rotate(-30deg)"), (68, "transform:scale(1.2) rotate(0)"),
                         (70, "transform:scale(1)"), (90, "transform:scale(1)"), (94, "transform:scale(0)"), (100, "transform:scale(0)")])
            + f".crown{{animation:crown {D}s {SPRING} infinite}}")
    d.add(f'<g class="fb crown"><path d="M{cols[3]+24} {fy+13} l4 -9 l5 6 l4 -8 l4 8 l5 -6 l4 9 Z" fill="{INK}"/></g>')
    # live score card
    lx, ly = 466, 52
    d.add(rect(lx, ly, 86, 74, 12, fill=PANEL2, stroke=LINE, stroke_width=1.2))
    d.style("@keyframes live{0%,100%{opacity:1}50%{opacity:.25}}.live{animation:live 1s ease-in-out infinite}")
    d.add(f'<circle class="live" cx="{lx+14}" cy="{ly+16}" r="4" fill="{CORAL}"/>')
    d.add(d.text("LIVE", lx + 24, ly + 20, 10, MONOB, fill=CORAL))
    d.style(kf("s1", [(0, "opacity:1"), (47, "opacity:1"), (48, "opacity:0"), (94, "opacity:0"), (95, "opacity:1")])
            + kf("s2", [(0, "opacity:0"), (47, "opacity:0"), (48, "opacity:1"), (94, "opacity:1"), (95, "opacity:0")])
            + f".s1{{animation:s1 {D}s steps(1) infinite}}.s2{{animation:s2 {D}s steps(1) infinite}}")
    d.add(f'<g class="s1">{d.text("2:1", lx + 43, ly + 58, 28, DISP, fill=TEXT, anchor="middle")}</g>')
    d.add(f'<g class="s2">{d.text("3:1", lx + 43, ly + 58, 28, DISP, fill=VOLT, anchor="middle")}</g>')
    # QR check-in
    qx, qy, q = 470, 144, 78
    d.add(rect(qx - 4, qy - 4, q + 8, q + 8, 10, fill=PAPER))
    cells = 13
    cs = q / cells
    qr = ""
    rq = random.Random(11)
    for i in range(cells):
        for j in range(cells):
            finder = (i < 4 and j < 4) or (i < 4 and j > cells - 5) or (i > cells - 5 and j < 4)
            if finder:
                continue
            if rq.random() < 0.48:
                qr += f'<rect x="{num(qx + i*cs)}" y="{num(qy + j*cs)}" width="{num(cs)}" height="{num(cs)}" fill="{INK}"/>'
    for fx, fy2 in [(0, 0), (cells - 4, 0), (0, cells - 4)]:
        x, y = qx + fx * cs, qy + fy2 * cs
        qr += f'<rect x="{num(x+cs*0.5)}" y="{num(y+cs*0.5)}" width="{num(cs*3)}" height="{num(cs*3)}" fill="none" stroke="{INK}" stroke-width="{num(cs)}"/>'
        qr += f'<rect x="{num(x+cs*1.5)}" y="{num(y+cs*1.5)}" width="{num(cs)}" height="{num(cs)}" fill="{INK}"/>'
    d.add(qr)
    d.style(kf("qs", [(0, "transform:translateY(0)"), (50, f"transform:translateY({q}px)"), (100, "transform:translateY(0)")])
            + ".qs{animation:qs 2.4s ease-in-out infinite}")
    d.add(f'<g class="qs"><rect x="{qx-8}" y="{qy-1}" width="{q+16}" height="3" rx="1.5" fill="{VOLT}"/></g>')
    d.style(kf("ok", [(0, "opacity:0"), (72, "opacity:0"), (75, "opacity:1"), (92, "opacity:1"), (95, "opacity:0"), (100, "opacity:0")])
            + f".ok{{animation:ok {D}s linear infinite}}")
    okc, okw = chip_text(d, qx + q / 2, qy + q - 14, "checked in", INK, VOLT, anchor="middle", h=22)
    d.add(f'<g class="ok">{okc}</g>')


def stage_portfolio(d: Doc) -> None:
    D = 10
    wx, wy, ww, wh = 36, 44, 500, 204
    light = "#F4F2ED"
    d.add(f'<clipPath id="win"><rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="14"/></clipPath>')

    def layer(dark: bool) -> str:
        bg = BG if dark else light
        fg = TEXT if dark else "#15171B"
        mu = MUTED if dark else "#6B6F77"
        ln = LINE if dark else "#DCD9D2"
        o = rect(wx, wy, ww, wh, 14, fill=bg)
        o += rect(wx, wy, ww, 38, 0, fill=PANEL if dark else "#E9E6DF")
        o += "".join(f'<circle cx="{wx+20+i*16}" cy="{wy+19}" r="5" fill="{c}"/>' for i, c in enumerate([CORAL, "#F2C14E", VOLT]))
        o += rect(wx + 160, wy + 9, 180, 20, 10, fill=bg, stroke=ln, stroke_width=1)
        o += d.text("fatihaljabar.com", wx + 250, wy + 23, 11, MONO, fill=mu, anchor="middle")
        return o, fg, mu

    def head(txt, fg, mu, lang_label):
        o = d.text(txt, wx + 28, wy + 104, 34, DISP, fill=fg)
        o += d.text(lang_label, wx + 30, wy + 72, 11, MONOB, fill=VOLT if fg == TEXT else "#5C7A00")
        o += rect(wx + 30, wy + 124, 260, 8, 4, fill=mu, opacity=".35") + rect(wx + 30, wy + 140, 190, 8, 4, fill=mu, opacity=".25")
        o += rect(wx + 30, wy + 162, 104, 26, 8, fill=fg) + d.text("View work", wx + 82, wy + 179, 11, MONOB, fill=BG if fg == TEXT else light, anchor="middle")
        return o

    # 4 states: dark EN, dark ID, light ID, light EN
    states = [(True, "Hello, I'm Fatih.", "EN"), (True, "Halo, saya Fatih.", "ID"), (False, "Halo, saya Fatih.", "ID"), (False, "Hello, I'm Fatih.", "EN")]
    for i, (dark, txt, lang) in enumerate(states):
        base, fg, mu = layer(dark)
        a0, a1 = i * 25, (i + 1) * 25
        if i == 0:
            stops = [(0, "opacity:1"), (a1 - 0.01, "opacity:1"), (a1, "opacity:0"), (99.99, "opacity:0"), (100, "opacity:1")]
        else:
            stops = [(0, "opacity:0"), (a0 - 0.01, "opacity:0"), (a0, "opacity:1"), (a1 - 0.01, "opacity:1"), (a1, "opacity:0"), (100, "opacity:0")]
            if i == 3:
                stops = [(0, "opacity:0"), (a0 - 0.01, "opacity:0"), (a0, "opacity:1"), (99.99, "opacity:1"), (100, "opacity:0")]
        d.style(kf(f"st{i}", stops) + f".st{i}{{animation:st{i} {D}s steps(1) infinite}}")
        d.add(f'<g class="st{i}" clip-path="url(#win)">{base}{head(txt, fg, mu, lang)}</g>')
    # toggles (on top of all layers)
    tx, ty = wx + ww - 150, wy + 54
    d.add(rect(tx, ty, 64, 26, 13, fill=PANEL2, stroke=LINE, stroke_width=1))
    d.style(kf("lg", [(0, "transform:translateX(0)"), (22, "transform:translateX(0)"), (25, "transform:translateX(30px)"),
                      (72, "transform:translateX(30px)"), (75, "transform:translateX(0)"), (100, "transform:translateX(0)")])
            + f".lg{{animation:lg {D}s {INOUT} infinite}}")
    d.add(f'<g class="lg">{rect(tx + 3, ty + 3, 28, 20, 10, fill=VOLT)}</g>')
    d.add(d.text("EN", tx + 17, ty + 17, 9, MONOB, fill=TEXT, anchor="middle", style="mix-blend-mode:difference"))
    d.add(d.text("ID", tx + 47, ty + 17, 9, MONOB, fill=TEXT, anchor="middle", style="mix-blend-mode:difference"))
    sx = tx + 76
    d.add(rect(sx, ty, 52, 26, 13, fill=PANEL2, stroke=LINE, stroke_width=1))
    d.style(kf("th", [(0, "transform:translateX(0)"), (47, "transform:translateX(0)"), (50, "transform:translateX(26px)"),
                      (97, "transform:translateX(26px)"), (100, "transform:translateX(0)")])
            + f".th{{animation:th {D}s {INOUT} infinite}}")
    knob = (f'<circle cx="{sx+13}" cy="{ty+13}" r="9" fill="{TEXT}"/>'
            f'<circle cx="{sx+17}" cy="{ty+10}" r="7" fill="{PANEL2}"/>')
    d.add(f'<g class="th">{knob}</g>')
    # audit badge
    lab = "security audit · passed"
    w = MONOB.width(lab, 10) + 34
    d.add(rect(wx + ww - w - 14, wy + wh - 38, w, 24, 7, fill=PANEL2, stroke=LINE, stroke_width=1))
    d.add(f'<path d="M{wx+ww-w-1} {wy+wh-32} l6 -2 l6 2 v5 q0 5 -6 8 q-6 -3 -6 -8 Z" fill="{VOLT}"/>')
    d.add(d.text(lab, wx + ww - w + 18, wy + wh - 22, 10, MONOB, fill=TEXT))


def stage_fadlan(d: Doc) -> None:
    cats = [("Commercial", CORAL), ("Event", VOLT), ("Social Media", SKY), ("Short Film", "#B59CFF"), ("Music Video", "#F2C14E")]
    fw, fh, gap = 150, 112, 14
    strip_w = len(cats) * (fw + gap)
    frames = ""
    for i, (name, col) in enumerate(cats):
        x = i * (fw + gap)
        frames += rect(x, 0, fw, fh, 6, fill="#16191E")
        frames += f'<circle cx="{x+fw*0.7}" cy="{fh*0.38}" r="{18 + i*3}" fill="{col}" opacity=".85"/>'
        frames += f'<path d="M{x} {fh} L{x+fw*0.35} {fh*0.52} L{x+fw*0.6} {fh*0.78} L{x+fw*0.78} {fh*0.62} L{x+fw} {fh} Z" fill="#0B0C0E" opacity=".75"/>'
        frames += d.text(name, x + 10, fh - 10, 11, MONOB, fill=TEXT)
    holes = "".join(rect(i * 22 + 4, 0, 12, 7, 2, fill=BG) for i in range(int(strip_w * 2 / 22) + 2))
    d.style(f"@keyframes reel{{from{{transform:translateX(0)}}to{{transform:translateX(-{strip_w}px)}}}}.reel{{animation:reel 16s linear infinite}}")
    d.add(rect(0, 50, SW, 160, 0, fill="#1F2329"))
    d.add(f'<g transform="translate(0 74)"><g class="reel">{frames}<g transform="translate({strip_w} 0)">{frames}</g></g></g>')
    d.add(f'<g transform="translate(0 56)"><g class="reel">{holes}</g></g>')
    d.add(f'<g transform="translate(0 195)"><g class="reel">{holes}</g></g>')
    # letterbox
    d.add(rect(0, 0, SW, 46, 0, fill=INK), rect(0, 214, SW, 48, 0, fill=INK))
    d.style("@keyframes rec{0%,100%{opacity:1}50%{opacity:.15}}.rec{animation:rec 1.2s steps(1) infinite}")
    d.add(f'<circle class="rec" cx="28" cy="238" r="5" fill="{CORAL}"/>')
    d.add(d.text("REC", 40, 242, 11, MONOB, fill=CORAL))
    d.add(d.text("00:01:24:12 · 24 fps", 74, 242, 11, MONO, fill=MUTED))
    # play button
    d.style("@keyframes ring{0%{transform:scale(1);opacity:.8}100%{transform:scale(1.9);opacity:0}}.ring{animation:ring 1.8s ease-out infinite}")
    cx, cy = SW / 2, 130
    d.add(f'<circle class="fb ring" cx="{cx}" cy="{cy}" r="26" fill="none" stroke="{TEXT}" stroke-width="2"/>')
    d.add(f'<circle cx="{cx}" cy="{cy}" r="26" fill="{TEXT}"/><path d="M{cx-7} {cy-11} L{cx+12} {cy} L{cx-7} {cy+11} Z" fill="{INK}"/>')
    # waveform
    d.style("@keyframes wv{0%,100%{transform:scaleY(.3)}50%{transform:scaleY(1)}}.wv{animation:wv .9s ease-in-out infinite;transform-box:fill-box;transform-origin:center}")
    bars = ""
    for i in range(24):
        h = 6 + (i * 37 % 13)
        bars += f'<rect class="wv" style="animation-delay:-{(i*0.13)%0.9:.2f}s" x="{SW-150+i*5.5}" y="{238-h/2}" width="3" height="{h}" rx="1.5" fill="{VOLT}"/>'
    d.add(bars)


def stage_pos(d: Doc) -> None:
    D = 9
    d.add(d.text("checkout · branch A", 24, 66, 12, MONO, fill=DIM))
    gx, gy = 24, 80
    taps = [0, 4, 2]
    for i in range(6):
        x = gx + (i % 3) * 70
        y = gy + (i // 3) * 62
        d.add(rect(x, y, 62, 54, 10, fill=PANEL2, stroke=LINE, stroke_width=1.2))
        d.add(f'<ellipse cx="{x+31}" cy="{y+24}" rx="17" ry="10" fill="#C99A5B"/>'
              f'<path d="M{x+22} {y+20} l4 6 M{x+30} {y+18} l4 7 M{x+38} {y+20} l3 5" stroke="#8A6435" stroke-width="2" stroke-linecap="round"/>')
        d.add(rect(x + 14, y + 40, 34, 5, 2.5, fill="#3A404A"))
        if i in taps:
            k = taps.index(i)
            p = 12 + k * 14
            d.style(kf(f"tp{i}", [(0, "transform:scale(1)"), (p, "transform:scale(1)"), (p + 1.5, "transform:scale(.9)"), (p + 4, "transform:scale(1)"), (100, "transform:scale(1)")])
                    + f".tp{i}{{animation:tp{i} {D}s ease-out infinite}}"
                    + kf(f"rp{i}", [(0, "transform:scale(0);opacity:0"), (p, "transform:scale(.2);opacity:.9"), (p + 6, "transform:scale(1.3);opacity:0"), (100, "opacity:0")])
                    + f".rp{i}{{animation:rp{i} {D}s ease-out infinite}}")
            d.add(f'<rect class="fb tp{i}" x="{x}" y="{y}" width="62" height="54" rx="10" fill="none" stroke="{VOLT}" stroke-width="1.6"/>')
            d.add(f'<g transform="translate({x+31} {y+27})"><circle class="fb rp{i}" r="30" fill="{VOLT}" opacity="0"/></g>')
    # tapping cursor
    pos = [(gx + (i % 3) * 70 + 34, gy + (i // 3) * 62 + 30) for i in taps]
    stops = [(0, f"transform:translate({pos[0][0]+80}px,{pos[0][1]+90}px);opacity:0"), (5, f"opacity:1;transform:translate({pos[0][0]+40}px,{pos[0][1]+50}px)")]
    for k, (x, y) in enumerate(pos):
        p = 12 + k * 14
        stops += [(p - 2, f"transform:translate({x}px,{y}px)"), (p + 3, f"transform:translate({x}px,{y}px)")]
    stops += [(70, f"transform:translate({pos[-1][0]}px,{pos[-1][1]}px);opacity:1"), (80, f"transform:translate({pos[-1][0]+60}px,{pos[-1][1]+80}px);opacity:0"),
              (100, f"transform:translate({pos[0][0]+80}px,{pos[0][1]+90}px);opacity:0")]
    d.style(kf("pc", stops) + f".pc{{animation:pc {D}s {INOUT} infinite}}")
    d.add(f'<g class="pc">{mini_cursor(TEXT)}</g>')
    # printer + receipt
    rx = 262
    d.add(rect(rx - 10, 50, 150, 22, 8, fill=PANEL2, stroke=LINE, stroke_width=1.2))
    d.add(rect(rx, 64, 130, 4, 2, fill=INK))
    d.add(f'<clipPath id="paper"><rect x="{rx}" y="66" width="130" height="190"/></clipPath>')
    rec = rect(rx + 6, 0, 118, 150, 0, fill=PAPER)
    for k in range(3):
        rec += rect(rx + 16, 16 + k * 18, 56, 6, 3, fill="#8E8B84") + rect(rx + 92, 16 + k * 18, 22, 6, 3, fill="#2B2F36")
    rec += f'<line x1="{rx+16}" y1="78" x2="{rx+114}" y2="78" stroke="#8E8B84" stroke-dasharray="3 3"/>'
    rec += d.text("TOTAL", rx + 16, 98, 10, MONOB, fill=INK) + rect(rx + 80, 90, 34, 9, 3, fill=INK)
    rec += "".join(rect(rx + 16 + k * 7, 116, 4 if k % 3 else 2, 18, 0, fill=INK) for k in range(14))
    d.style(kf("print", [(0, "transform:translateY(-150px)"), (42, "transform:translateY(-150px)"), (58, "transform:translateY(68px)"),
                         (88, "transform:translateY(68px)"), (94, "transform:translateY(260px)"), (100, "transform:translateY(260px)")])
            + f".print{{animation:print {D}s cubic-bezier(.4,0,.6,1) infinite}}")
    d.add(f'<g clip-path="url(#paper)"><g class="print">{rec}</g></g>')
    # branch stock
    bx = 430
    d.add(d.text("stock", bx, 66, 12, MONO, fill=DIM))
    for i, (b, lvl) in enumerate([("A", 0.82), ("B", 0.6), ("C", 0.7)]):
        y = 82 + i * 34
        d.add(d.text(f"Branch {b}", bx, y + 10, 10, MONO, fill=MUTED))
        d.add(rect(bx, y + 16, 118, 6, 3, fill=PANEL2))
        if i == 0:
            d.style(kf("stk", [(0, f"transform:scaleX({lvl})"), (12, f"transform:scaleX({lvl})"), (14, f"transform:scaleX({lvl-0.08})"),
                               (26, f"transform:scaleX({lvl-0.08})"), (28, f"transform:scaleX({lvl-0.16})"), (40, f"transform:scaleX({lvl-0.16})"),
                               (42, f"transform:scaleX({lvl-0.24})"), (90, f"transform:scaleX({lvl-0.24})"), (96, f"transform:scaleX({lvl})"), (100, f"transform:scaleX({lvl})")])
                    + f".stk{{animation:stk {D}s {OUTQ} infinite;transform-box:fill-box;transform-origin:left center}}")
            d.add(f'<rect class="stk" x="{bx}" y="{y+16}" width="118" height="6" rx="3" fill="{VOLT}" style="transform:scaleX({lvl})"/>')
        else:
            d.add(rect(bx, y + 16, 118 * lvl, 6, 3, fill="#3A404A"))
    # audit log
    d.add(d.text("audit log", bx, 196, 12, MONO, fill=DIM))
    for k, line in enumerate(["sale · branch A", "stock −3 · A"]):
        p = 46 + k * 8
        d.style(kf(f"al{k}", [(0, "opacity:0;transform:translateX(-8px)"), (p, "opacity:0;transform:translateX(-8px)"), (p + 3, "opacity:1;transform:translateX(0)"),
                               (90, "opacity:1"), (94, "opacity:0"), (100, "opacity:0")])
                + f".al{k}{{animation:al{k} {D}s {OUTQ} infinite}}")
        d.add(f'<g class="al{k}"><circle cx="{bx+4}" cy="{213 + k*20}" r="3" fill="{VOLT if k == 0 else CORAL}"/>'
              + d.text(line, bx + 14, 217 + k * 20, 10, MONO, fill=TEXT) + "</g>")


# ---------------------------------------------------------------------------
# Card shell
# ---------------------------------------------------------------------------
STATUS = {
    "prod": ("IN PRODUCTION", VOLT, True),
    "demo": ("LIVE DEMO", VOLT, False),
    "repo": ("PUBLIC REPO", SKY, False),
    "private": ("PRIVATE", MUTED, False),
}

PROJECTS = [
    dict(slug="blockwave", name="Blockwave Studios", kicker="CLIENT BUILD · DIGITAL MARKETPLACE", status="demo",
         desc="Minecraft and Roblox asset marketplace. Designed and built solo, from spec to a client-approved demo. Production build underway.",
         stack=["React 19", "Vite", "Tailwind v4", "Framer Motion", "Recharts"], stage=stage_blockwave),
    dict(slug="ottodot", name="Ottodot Trial Booking", kicker="TAKE-HOME · FULL-STACK RELIABILITY", status="repo",
         desc="Two parents, one last seat. Row-locked Postgres transactions, idempotent mock payments, 34 tests incl. a true concurrency race.",
         stack=["Next.js", "PostgreSQL", "Prisma", "Zod", "Vitest"], stage=stage_ottodot),
    dict(slug="tracker", name="application-tracker", kicker="PRODUCT · TRACKINGLAMARAN.SITE", status="prod",
         desc="Job-hunt companion: 11-stage pipeline, 14-field tracking, deadline and interview reminders, document uploads, stats.",
         stack=["React", "Express", "Drizzle", "Cloudflare R2", "Resend"], stage=stage_tracker),
    dict(slug="splitbill", name="splitbill", kicker="PRODUCT · SPLITBILLS.SITE", status="prod",
         desc="In-browser OCR receipt scanning, item or percentage splits with exact-rupiah rounding, privacy-first short links.",
         stack=["Vue 3", "TypeScript", "Hono", "Drizzle", "Tesseract.js"], stage=stage_splitbill),
    dict(slug="nusaride", name="NusaRide", kicker="CLIENT DEMO · RENTAL AND FLEET OPS", status="demo",
         desc="Car, Hiace and bus rentals: booking flow, per-unit availability, fleet CRUD, PDF invoices, ID and EN, dark mode.",
         stack=["React 19", "React Router", "Tailwind v4", "Framer Motion", "jsPDF"], stage=stage_nusaride),
    dict(slug="vetready", name="VetReady", kicker="CLIENT DEMO · EXAM PREPARATION", status="demo",
         desc="Veterinary exam prep: timed CBT simulation, guided OSCE clinical cases, checkout, participant and admin portals.",
         stack=["React 19", "TypeScript", "Vite 7", "Tailwind 4", "Framer Motion"], stage=stage_vetready),
    dict(slug="ramatama", name="Ramatama Tours", kicker="CLIENT DEMO · TRAVEL AGENCY SUITE", status="demo",
         desc="Quotation to booking to invoice to receipt in one connected flow, with AR and AP, role-based access, multi-currency.",
         stack=["React", "React Router", "Tailwind", "Framer Motion"], stage=stage_ramatama),
    dict(slug="formkey", name="Formkey", kicker="CLIENT DEMO · E-COMMERCE", status="demo",
         desc="Artisan keycap storefront: catalog, bag, checkout, PayPal payment simulator, plus an order and product admin.",
         stack=["React", "Tailwind", "Framer Motion", "Playwright"], stage=stage_formkey),
    dict(slug="eventsport", name="event-sport-demo", kicker="CLIENT BUILD · SPORTS EVENTS", status="demo",
         desc="ISDN event platform: bracket generator, sport-specific live scoring, drag-and-drop scheduling, QR check-in.",
         stack=["React", "Vite", "React Router", "Framer Motion"], stage=stage_event),
    dict(slug="portfolio", name="portfolio", kicker="PRODUCT · FATIHALJABAR.COM", status="prod",
         desc="Self-service CMS: bilingual EN and ID, dark mode, admin dashboard for content, whole-codebase security audit.",
         stack=["Next.js", "TypeScript", "Prisma", "Supabase", "next-intl"], stage=stage_portfolio),
    dict(slug="fadlan", name="Fadlan Creator", kicker="CLIENT DEMO · FILMMAKER PORTFOLIO", status="demo",
         desc="Cinematic portfolio for a videographer: five category galleries, video modal, skeleton states, reduced-motion support.",
         stack=["React", "Vite", "React Router", "Tailwind"], stage=stage_fadlan),
    dict(slug="samspos", name="sams-pos-demo", kicker="CLIENT PROTOTYPE · BAKERY POS", status="private",
         desc="POS and inventory for a bakery client: checkout, purchasing, production, multi-branch stock, audit logs.",
         stack=["Next.js", "TypeScript", "Tailwind"], stage=stage_pos),
]


def build_card(idx: int, p: dict) -> None:
    total = len(PROJECTS)
    d = Doc(CW, CH, f"{p['name']}: {p['desc']}", f"Animated project card for {p['name']}. {p['desc']} Stack: {', '.join(p['stack'])}.")
    d.defs.append(dots_pattern("dots", 22))
    d.defs.append(f'<clipPath id="stage"><rect x="0" y="0" width="{SW}" height="{SH}" rx="14"/></clipPath>')
    d.style(BASE_CSS)
    d.style("@keyframes nudge{0%,70%,100%{transform:translate(0,0)}80%{transform:translate(3px,-3px)}90%{transform:translate(0,0)}}"
            ".nudge{animation:nudge 3s ease-in-out infinite}"
            "@keyframes spulse{0%{transform:scale(1);opacity:.7}100%{transform:scale(3);opacity:0}}"
            ".spulse{animation:spulse 1.8s ease-out infinite;transform-box:fill-box;transform-origin:center}")
    d.add(rect(0.75, 0.75, CW - 1.5, CH - 1.5, 22, fill=PANEL, stroke=LINE, stroke_width=1.5))
    d.add(f'<g transform="translate(14 14)"><g clip-path="url(#stage)">')
    d.add(rect(0, 0, SW, SH, 0, fill=BG), f'<rect width="{SW}" height="{SH}" fill="url(#dots)"/>')
    p["stage"](d)
    d.add("</g>")
    d.add(f'<rect x="0.5" y="0.5" width="{SW-1}" height="{SH-1}" rx="14" fill="none" stroke="{LINE}"/>')
    # overlays
    idx_s = f"{idx:02d}"
    iw = MONOB.width(idx_s, 12) + MONO.width(f"/{total}", 12) + 20
    d.add(rect(10, 10, iw, 24, 7, fill=PANEL, stroke=LINE, stroke_width=1))
    d.add(d.text(idx_s, 20, 26.5, 12, MONOB, fill=VOLT))
    d.add(d.text(f"/{total}", 20 + MONOB.width(idx_s, 12) + 1, 26.5, 12, MONO, fill=DIM))
    label, color, pulse = STATUS[p["status"]]
    sw = MONOB.width(label, 11) + 34
    sx = SW - 10 - sw
    d.add(rect(sx, 10, sw, 24, 7, fill=PANEL, stroke=LINE, stroke_width=1))
    d.add(f'<circle cx="{sx+13}" cy="22" r="4" fill="{color}"/>')
    if pulse:
        d.add(f'<circle class="spulse" cx="{sx+13}" cy="22" r="4" fill="{color}"/>')
    d.add(d.text(label, sx + 24, 26, 11, MONOB, fill=TEXT))
    d.add("</g>")
    # info block
    d.add(d.text(p["kicker"], 28, 306, 11, MONOB, fill=VOLT, ls=0.8))
    d.add(d.text(p["name"], 26, 342, 32, DISP, fill=TEXT))
    d.add(f'<circle cx="{CW-48}" cy="322" r="20" fill="none" stroke="{LINE}" stroke-width="1.4"/>')
    d.add(f'<g class="nudge">{arrow_ne(CW-55, 315, 14, TEXT, 2)}</g>')
    lines = wrap(BODY, p["desc"], 17, CW - 56)
    if len(lines) > 2:
        raise ValueError(f"{p['slug']}: description wraps to {len(lines)} lines: {lines}")
    for i, ln in enumerate(lines):
        d.add(d.text(ln, 28, 374 + i * 23, 17, BODY, fill=MUTED))
    x = 28
    for s in p["stack"]:
        g, w = pill(d, x, 418, s, font=MONO, size=12, fg=TEXT, stroke=LINE, padx=11, h=26)
        if x + w > CW - 24:
            raise ValueError(f"{p['slug']}: stack chips overflow")
        d.add(g)
        x += w + 7
    save(f"card-{p['slug']}.svg", d)


def build_all() -> None:
    for i, p in enumerate(PROJECTS, 1):
        build_card(i, p)
