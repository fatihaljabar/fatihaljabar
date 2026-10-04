"""Real spring physics for CSS.

A damped spring is simulated numerically (semi-implicit Euler, 1 ms steps) and
its unit step response is sampled into a CSS linear() easing. Browsers without
linear() keep the cubic-bezier fallback declared first.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Spring:
    stiffness: float  # N/m
    damping: float  # N*s/m
    mass: float = 1.0

    @property
    def zeta(self) -> float:
        return self.damping / (2 * (self.stiffness * self.mass) ** 0.5)


# Tuned presets: high stiffness so things arrive fast, damping picked per weight.
SNAP = Spring(560, 32)  # light UI parts, ~5% overshoot
FIRM = Spring(420, 30)  # jaws, sliders, ~3% overshoot
HEAVY = Spring(260, 24, 1.6)  # gantry, stamp: visible inertia, one soft rebound
SETTLE = Spring(380, 39)  # critically damped, no overshoot


_cache: dict[Spring, tuple[float, list[float]]] = {}


def response(s: Spring, tol: float = 0.0008) -> tuple[float, list[float]]:
    if s in _cache:
        return _cache[s]
    dt = 0.001
    x, v, t = 0.0, 0.0, 0.0
    xs = [0.0]
    calm = 0.0
    while t < 4:
        a = (-s.stiffness * (x - 1) - s.damping * v) / s.mass
        v += a * dt
        x += v * dt
        t += dt
        xs.append(x)
        calm = calm + dt if abs(x - 1) < tol and abs(v) < tol * 10 else 0.0
        if calm > 0.04:
            break
    _cache[s] = (t, xs)
    return t, xs


def duration(s: Spring) -> float:
    return round(response(s)[0], 3)


def linear_easing(s: Spring, points: int = 40) -> str:
    _, xs = response(s)
    n = len(xs) - 1
    vals = [xs[round(i * n / (points - 1))] for i in range(points)]
    vals[0], vals[-1] = 0.0, 1.0
    return "linear(" + ",".join(f"{v:.3f}".rstrip("0").rstrip(".") or "0" for v in vals) + ")"


FALLBACK = {
    SNAP: "cubic-bezier(.34,1.4,.64,1)",
    FIRM: "cubic-bezier(.3,1.15,.5,1)",
    HEAVY: "cubic-bezier(.3,1.25,.45,1)",
    SETTLE: "cubic-bezier(.16,1,.3,1)",
}


def spring_anim(cls: str, name: str, s: Spring, delay: float = 0.0, extra: str = "both") -> str:
    """CSS rule running keyframes `name` once with a physical spring easing."""
    return (f".{cls}{{animation:{name} {duration(s)}s {FALLBACK.get(s, 'ease-out')} {delay:.3f}s {extra};"
            f"animation-timing-function:{linear_easing(s)}}}")


def spring_tf(s: Spring) -> str:
    """Per-keyframe timing declarations (fallback first, then linear())."""
    return f"animation-timing-function:{FALLBACK.get(s, 'ease-out')};animation-timing-function:{linear_easing(s)}"


def detent_keyframes(name: str, prop, frm: float, to: float, overshoot_px: float, settle: Spring = SETTLE) -> str:
    """Move from `frm` to `to` and stop like a mechanism hitting a detent: a critically
    damped approach, a fixed overshoot in pixels (never a percentage of the travel),
    and a short return. `prop(v)` renders the CSS declaration for value v."""
    sign = 1 if to >= frm else -1
    return (f"@keyframes {name}{{0%{{{prop(frm)};{spring_tf(settle)}}}"
            f"82%{{{prop(to + sign * overshoot_px)};animation-timing-function:cubic-bezier(.3,0,.3,1)}}"
            f"92%{{{prop(to - sign * overshoot_px * 0.2)}}}100%{{{prop(to)}}}}}")
