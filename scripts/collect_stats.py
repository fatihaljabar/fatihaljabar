"""Collects the numbers behind assets/stats.svg from local clones.

    python scripts/collect_stats.py --as-of 2026-10-04 ../application-tracker ../splitbill ...

Counts only commits authored by Fatih (by email), buckets them into the 52
ISO weeks that end on --as-of, and measures lines of code per language in each
repository's current tree. Writes scripts/data/stats.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "stats.json")

AUTHOR_EMAILS = {
    "fatihaljabar@gmail.com",
    "130438727+fatihaljabar@users.noreply.github.com",
}

LANGS = {
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".vue": "Vue", ".py": "Python", ".css": "CSS", ".scss": "CSS",
    ".html": "HTML", ".sql": "SQL", ".dart": "Dart",
}
SKIP_PARTS = ("node_modules/", "dist/", "build/", ".next/", "vendor/", "public/", "migrations/", "drizzle/meta/")
SKIP_SUFFIX = (".min.js", ".min.css", ".d.ts")


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def week_start(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", required=True)
    ap.add_argument("--languages-exclude", nargs="*", default=["fatihaljabar"])
    ap.add_argument("repos", nargs="+")
    a = ap.parse_args()

    as_of = dt.date.fromisoformat(a.as_of)
    last_week = week_start(as_of)
    weeks = [last_week - dt.timedelta(weeks=52 - 1 - i) for i in range(52)]
    first_day = weeks[0]

    per_week: Counter = Counter()
    per_month: Counter = Counter()
    per_repo: Counter = Counter()
    days: set[dt.date] = set()
    all_time = 0
    loc: Counter = Counter()

    for path in a.repos:
        name = os.path.basename(os.path.abspath(path))
        log = git(path, "log", "--all", "--no-merges", "--format=%H|%ae|%ad", "--date=short")
        seen = set()
        for line in log.splitlines():
            sha, email, date = line.split("|")
            if sha in seen or email.lower() not in AUTHOR_EMAILS:
                continue
            seen.add(sha)
            all_time += 1
            day = dt.date.fromisoformat(date)
            if first_day <= day <= as_of:
                per_week[week_start(day)] += 1
                per_month[day.strftime("%Y-%m")] += 1
                per_repo[name] += 1
                days.add(day)
        if name in a.languages_exclude:
            continue
        for f in git(path, "ls-files").splitlines():
            if any(p in f for p in SKIP_PARTS) or f.endswith(SKIP_SUFFIX):
                continue
            ext = os.path.splitext(f)[1].lower()
            full = os.path.join(path, f)
            if not os.path.isfile(full):
                continue
            if ext == ".ipynb":
                # notebooks count as Python: only the code cells, not outputs
                with open(full, encoding="utf-8") as fh:
                    cells = json.load(fh).get("cells", [])
                loc["Python"] += sum(1 for c in cells if c.get("cell_type") == "code"
                                     for ln in "".join(c.get("source", [])).splitlines() if ln.strip())
                continue
            lang = LANGS.get(ext)
            if not lang:
                continue
            with open(full, "rb") as fh:
                loc[lang] += sum(1 for ln in fh if ln.strip())

    # longest run of consecutive days with at least one commit
    streak = best = 0
    prev = None
    for day in sorted(days):
        streak = streak + 1 if prev and (day - prev).days == 1 else 1
        best = max(best, streak)
        prev = day

    data = {
        "as_of": as_of.isoformat(),
        "repos_scanned": len(a.repos),
        "commits_all_time": all_time,
        "weeks": [{"week": w.isoformat(), "commits": per_week.get(w, 0)} for w in weeks],
        "months": [{"month": m, "commits": per_month[m]} for m in sorted(per_month)],
        "by_repo": [{"repo": r, "commits": c} for r, c in per_repo.most_common()],
        "languages": [{"language": l, "lines": n} for l, n in loc.most_common()],
        "active_days": len(days),
        "longest_streak_days": best,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(data, fh, indent=2)
    total = sum(w["commits"] for w in data["weeks"])
    print(f"{total} commits in the last 52 weeks, {len(days)} active days, streak {best}, {all_time} all time")
    print("by repo:", data["by_repo"][:10])
    print("languages:", data["languages"])


if __name__ == "__main__":
    main()
