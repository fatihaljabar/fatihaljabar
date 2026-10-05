"""Generates every animated SVG used by the profile README.

    pip install fonttools brotli
    python scripts/build_assets.py            # everything
    python scripts/build_assets.py hero stats # only some parts
    THEME=light python scripts/build_assets.py # the -light twins
    python scripts/build_assets.py readme     # README.md from the same data

Output goes to assets/. All motion is CSS (plus SMIL for two paths) inside
the SVG, so it plays in GitHub's image sandbox with no scripts and no
external requests.
"""

from __future__ import annotations

import os
import sys

from theme import save

PARTS = {}


def part(fn):
    PARTS[fn.__name__] = fn
    return fn


@part
def hero():
    import hero as h
    h.build()  # saves itself; the machine has a single file for both themes


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
def toolbox():
    import toolbox as t
    t.build()


@part
def stats():
    import charts as c
    c.build()


@part
def thesis():
    import thesis as t
    t.build()


@part
def certs():
    import certs as c
    c.build()


@part
def readme():
    import runpy
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_readme.py"))


def main() -> None:
    names = sys.argv[1:] or list(PARTS)
    for n in names:
        PARTS[n]()


if __name__ == "__main__":
    main()
