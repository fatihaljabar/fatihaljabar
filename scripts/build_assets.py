"""Generates every animated SVG used by the profile README.

    pip install fonttools brotli
    python scripts/build_assets.py            # everything
    python scripts/build_assets.py hero stats # only some parts

Output goes to assets/. All motion is CSS (plus SMIL for two paths) inside
the SVG, so it plays in GitHub's image sandbox with no scripts and no
external requests.
"""

from __future__ import annotations

import sys

from theme import save

PARTS = {}


def part(fn):
    PARTS[fn.__name__] = fn
    return fn


@part
def hero():
    import hero as h
    save("hero.svg", h.build())


@part
def cards():
    import cards as c
    c.build_all()


@part
def ui():
    import ui as u
    u.build_all()


@part
def stack():
    import stack as s
    s.build()


@part
def stats():
    import charts as c
    c.build()


@part
def thesis():
    import thesis as t
    t.build()


def main() -> None:
    names = sys.argv[1:] or list(PARTS)
    for n in names:
        PARTS[n]()


if __name__ == "__main__":
    main()
