"""Build GitHub profile metrics from public GitHub API fields only.

The script never edits README.md. It writes three SVGs under assets/.
Uses Python's standard library, and fails without replacing existing images
when the API is inaccessible or returns an incomplete payload.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
import json
import os

USER = "Adil307"
OUT = Path(__file__).resolve().parent.parent / "assets"
BG = "#101827"
FG = "#f2f6ff"
MUTED = "#9eb0ce"
CYAN = "#65dbe5"
VIOLET = "#a994ff"
BLUE = "#73abfa"


def fetch(path: str):
    headers = {
        "User-Agent": "Adil307-profile-stats",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    request = Request("https://api.github.com/" + path, headers=headers)
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def svg_root(width: int, height: int, label: str):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">',
        f'<rect width="{width}" height="{height}" rx="16" fill="{BG}"/>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="15" fill="none" stroke="#344666"/>',
    ]


def label(x: int, y: int, message: object, *, size=18, color=MUTED, weight="400", anchor="start") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" '
        f'fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(message))}</text>'
    )


def render_stats(public, originals, profile, stamp):
    stats = [
        ("PUBLIC REPOS", len(public)),
        ("FOLLOWERS", int(profile["followers"])),
        ("STARS · NON-FORK", sum(int(r.get("stargazers_count") or 0) for r in originals)),
    ]
    s = svg_root(1120, 250, "Public GitHub profile counts")
    s += [label(34, 43, "GITHUB / PUBLIC METRICS", size=20, color=CYAN, weight="700")]
    for i, (name, value) in enumerate(stats):
        x = 34 + i * 355
        s += [f'<rect x="{x}" y="65" width="335" height="122" rx="10" fill="#1b2942" stroke="#344666"/>']
        s += [label(x+20, 94, name, size=15, color=MUTED, weight="700"), label(x+20, 160, value, size=50, color=FG, weight="700")]
    s += [label(34, 224, f"Updated {stamp} · Public repositories only · Stars exclude forks", size=16)]
    return "".join(s) + "</svg>"


def render_languages(originals):
    langs = Counter(r.get("language") for r in originals if r.get("language"))
    top = langs.most_common(5)
    s = svg_root(550, 280, "Primary language counts across original public repositories")
    s += [label(24, 42, "TOP LANGUAGES BY REPO", size=18, color=CYAN, weight="700")]
    if not top:
        s += [label(25, 138, "No repository language data", size=23, color=FG)]
    else:
        highest = max(count for _, count in top)
        for i, (name, count) in enumerate(top):
            y = 83 + i * 37
            barw = int(260 * count / highest)
            s += [label(25, y, str(name)[:15], size=16, color=FG),
                  f'<rect x="207" y="{y-17}" width="264" height="17" rx="5" fill="#1d2b43"/>',
                  f'<rect x="207" y="{y-17}" width="{barw}" height="17" rx="5" fill="{[CYAN,VIOLET,BLUE,"#67cba8","#e8b97b"][i]}"/>',
                  label(492, y-2, count, size=15, color=FG)]
    s += [label(24, 261, "One primary language per non-fork repository", size=13)]
    return "".join(s) + "</svg>"


def months_back(now, n=6):
    keys = []
    for delta in reversed(range(n)):
        year = now.year
        month = now.month - delta
        while month < 1:
            year -= 1
            month += 12
        keys.append(f"{year:04}-{month:02}")
    return keys


def render_recent(originals, now):
    months = months_back(now)
    counts = Counter(str(r.get("pushed_at") or "")[:7] for r in originals)
    numbers = [counts.get(key, 0) for key in months]
    maximum = max(1, *numbers)
    s = svg_root(550, 280, "Months when public original repositories were last pushed")
    s += [label(24, 42, "LATEST REPO UPDATES / 6 MONTHS", size=18, color=CYAN, weight="700")]
    s += [f'<path d="M42 215H518" stroke="#48607c"/>']
    for i, (month, count) in enumerate(zip(months, numbers)):
        x = 54 + i * 80
        height = int(125 * count / maximum)
        s += [f'<rect x="{x}" y="{215-height}" width="49" height="{height}" rx="4" fill="{CYAN if i==5 else VIOLET}"/>',
              label(x+24, 207-height, count, size=17, color=FG, weight="700", anchor="middle"),
              label(x+24, 240, month[5:], size=14, anchor="middle")]
    s += [label(24, 264, "Counts repos by last push, not total commits", size=13)]
    return "".join(s) + "</svg>"


def main():
    profile = fetch(f"users/{USER}")
    if not isinstance(profile, dict) or "followers" not in profile:
        raise RuntimeError("Invalid GitHub user response")
    repositories = []
    for page in range(1, 51):
        batch = fetch(f"users/{USER}/repos?type=owner&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise RuntimeError("Invalid GitHub repos response")
        repositories.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise RuntimeError("Pagination exceeded; previous SVGs preserved")
    public = [r for r in repositories if not r.get("private", False)]
    originals = [r for r in public if not r.get("fork", False)]
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    output = {
        "stats-live.svg": render_stats(public, originals, profile, stamp),
        "languages-live.svg": render_languages(originals),
        "activity-live.svg": render_recent(originals, now),
    }
    # API requests and rendering all finish before any disk writes.
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, content in output.items():
        (OUT / filename).write_text(content, encoding="utf-8")
    print(f"Refreshed {len(public)} public repositories, {len(originals)} original repos")


if __name__ == "__main__":
    main()
