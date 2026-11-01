#!/usr/bin/env python3
"""Halloween contribution calendar: a spider crawls the grid and webs up every
cell that has commits (the animated replacement for the pacman/snake graphs).

Real data (needs a token, the Action provides one):
    GH_USER=your-name GITHUB_TOKEN=ghp_xxx python scripts/generate_contrib_web.py

Preview with fake data:
    python scripts/generate_contrib_web.py --demo
"""
import argparse
import json
import math
import os
import random
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_spider as gs  # reuse the spider drawing

# ---- layout ---------------------------------------------------------------
SIZE, STEP = 11, 14          # cell size / pitch
LEFT, RIGHT = 44, 26
GRID_TOP = 78
LOOP = 60                    # seconds for one full crawl
RESET = 0.985                # fraction of the loop at which cells un-web
PALETTE = ["#1d1833", "#4c2a85", "#8e44ad", "#ff7518", "#ffb347"]  # none -> most
WEBBED = "#7b74a0"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{totalContributions weeks{contributionDays{
contributionCount contributionLevel date weekday}}}}}}"""
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


# ---- data -----------------------------------------------------------------
def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "spider-contrib"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors") or not data.get("data", {}).get("user"):
        sys.exit(f"GitHub API error: {data.get('errors') or 'user not found'}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = []
    for w in cal["weeks"]:
        col = [None] * 7
        for d in w["contributionDays"]:
            col[d["weekday"]] = (d["contributionCount"], LEVELS[d["contributionLevel"]], d["date"])
        weeks.append(col)
    return cal["totalContributions"], weeks


def demo_data(seed=13):
    rnd = random.Random(seed)
    today = date.today()
    sunday_idx = (today.weekday() + 1) % 7
    start = today - timedelta(days=52 * 7 + sunday_idx)
    weeks, total, streak = [], 0, 0
    for w in range(53):
        col = [None] * 7
        for d in range(7):
            day = start + timedelta(days=w * 7 + d)
            if day > today:
                continue
            busy = 0.55 if d in (1, 2, 3, 4, 5) else 0.25
            streak = streak + 1 if rnd.random() < busy else 0
            n = 0 if streak == 0 else int(rnd.expovariate(1 / 3.5)) + 1
            lvl = 0 if n == 0 else 1 if n < 3 else 2 if n < 6 else 3 if n < 10 else 4
            col[d] = (n, lvl, day.isoformat())
            total += n
        weeks.append(col)
    return total, weeks


# ---- svg ------------------------------------------------------------------
def bat(delay, dur, y_shift, scale):
    path = (f"M -40 {40 + y_shift} C 200 {y_shift}, 400 {70 + y_shift}, 600 {25 + y_shift} "
            f"S 900 {50 + y_shift}, 1000 {15 + y_shift}")
    shape = ("M0,2 C-3,-4 -8,-6 -14,-3 C-11,-1 -10,2 -8,4 C-6,2 -3,2 0,6 "
             "C3,2 6,2 8,4 C10,2 11,-1 14,-3 C8,-6 3,-4 0,2 Z")
    return (f'<g><animateMotion dur="{dur}s" begin="{delay}s" repeatCount="indefinite" path="{path}"/>'
            f'<g transform="scale({scale})"><g><animateTransform attributeName="transform" type="scale" '
            f'values="1 1;1 .4;1 1" dur=".35s" repeatCount="indefinite"/>'
            f'<path d="{shape}" fill="#0a0612" stroke="#7a58b0" stroke-width=".7"/></g></g></g>')


def hanging(x, drop_min, drop_max, scale, dur, uid):
    defs, art = gs.spider(uid, speed=0.9)
    g = (f'<g transform="translate({x},{drop_min})">'
         f'<animateTransform attributeName="transform" type="translate" '
         f'values="{x},{drop_min};{x},{drop_max};{x},{drop_min}" dur="{dur}s" repeatCount="indefinite"/>'
         f'<line x1="0" y1="-120" x2="0" y2="0" stroke="#cfc8e6" stroke-opacity=".55" stroke-width=".8"/>'
         f'<g transform="rotate(90) scale({scale})">{art}</g></g>')
    return defs, g


def build(total, weeks, login):
    ncols = len(weeks)
    W = LEFT + ncols * STEP + RIGHT
    legend_y = GRID_TOP + 7 * STEP + 24
    H = legend_y + 24

    def cx(c): return LEFT + c * STEP + SIZE / 2
    def cy(r): return GRID_TOP + r * STEP + SIZE / 2

    # crawl path: serpentine through every column, entering from the left
    pts, seq = [(LEFT - 46, cy(0))], [None]
    for c in range(ncols):
        for r in (range(7) if c % 2 == 0 else range(6, -1, -1)):
            pts.append((cx(c), cy(r)))
            seq.append((c, r))
    pts.append((cx(ncols - 1) + 46, pts[-1][1]))
    seq.append(None)

    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    length = cum[-1]
    arrive = {s: cum[i] / length for i, s in enumerate(seq) if s}

    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    cells = []
    for c, col in enumerate(weeks):
        for r, d in enumerate(col):
            if d is None:
                continue
            count, lvl, _ = d
            x, y = LEFT + c * STEP, GRID_TOP + r * STEP
            fill = PALETTE[lvl]
            stroke = ' stroke="#ffd9a0" stroke-opacity=".5" stroke-width=".6"' if lvl == 4 else ""
            if lvl == 0:
                cells.append(f'<rect x="{x}" y="{y}" width="{SIZE}" height="{SIZE}" rx="2.5" fill="{fill}"/>')
            else:
                f = min(max(arrive[(c, r)], 0.002), RESET - 0.002)
                cells.append(
                    f'<rect x="{x}" y="{y}" width="{SIZE}" height="{SIZE}" rx="2.5" fill="{fill}"{stroke}>'
                    f'<animate attributeName="fill" calcMode="discrete" dur="{LOOP}s" repeatCount="indefinite" '
                    f'values="{fill};{WEBBED};{fill}" keyTimes="0;{f:.4f};{RESET}"/></rect>')

    # month + weekday labels
    labels, last_m, last_c = [], None, -9
    for c, col in enumerate(weeks):
        first = next((d for d in col if d), None)
        if not first:
            continue
        m = int(first[2][5:7])
        if m != last_m and c - last_c >= 3:
            name = date(2000, m, 1).strftime("%b")
            labels.append(f'<text x="{LEFT + c * STEP}" y="{GRID_TOP - 9}">{name}</text>')
            last_c = c
        last_m = m
    for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        labels.append(f'<text x="{LEFT - 8}" y="{GRID_TOP + r * STEP + 9}" text-anchor="end">{name}</text>')

    # stars
    rnd = random.Random(5)
    stars = []
    for _ in range(18):
        sx = rnd.uniform(20, W - 20)
        sy = rnd.choice([rnd.uniform(8, 46), rnd.uniform(legend_y + 6, H - 6)])
        stars.append(
            f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{rnd.choice([.7, .9, 1.2])}" fill="#fff4cf">'
            f'<animate attributeName="opacity" values=".15;.9;.15" dur="{rnd.uniform(2, 5):.1f}s" '
            f'begin="-{rnd.uniform(0, 4):.1f}s" repeatCount="indefinite"/></circle>')

    # legend
    lx = W - RIGHT - (5 * 16 + 70)
    legend = [f'<text x="{lx}" y="{legend_y + 9}" text-anchor="end" fill="#8b7fb0">Less</text>']
    for i, col in enumerate(PALETTE):
        legend.append(f'<rect x="{lx + 8 + i * 16}" y="{legend_y}" width="{SIZE}" height="{SIZE}" rx="2.5" fill="{col}"/>')
    legend.append(f'<text x="{lx + 8 + 5 * 16 + 4}" y="{legend_y + 9}" fill="#8b7fb0">More</text>')

    d_walk, walker = gs.crawler(path, 0.30, "w", LOOP)
    d_h1, hang1 = hanging(560, 30, 52, 0.34, 4.2, "h1")
    d_h2, hang2 = hanging(660, 22, 36, 0.24, 3.1, "h2")

    moon_x, moon_y = W - 120, 40
    login_x = escape(login)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Halloween contribution graph for {login_x}: {total} contributions, with a spider crawling over the grid and webbing up commits.">
<title>{login_x}'s web of commits - {total} contributions</title>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#140d24"/><stop offset="1" stop-color="#22123a"/></linearGradient>
<radialGradient id="moon" cx="38%" cy="35%" r="70%"><stop offset="0" stop-color="#fff6d6"/><stop offset="1" stop-color="#f0cf84"/></radialGradient>
{d_walk}{d_h1}{d_h2}
</defs>
<rect width="{W}" height="{H}" rx="14" fill="url(#bg)" stroke="#3a2a5c"/>
{''.join(stars)}
<circle cx="{moon_x}" cy="{moon_y}" r="28" fill="#ffd57a" opacity=".1"><animate attributeName="opacity" values=".06;.16;.06" dur="5s" repeatCount="indefinite"/></circle>
<circle cx="{moon_x}" cy="{moon_y}" r="17" fill="url(#moon)"/>
<circle cx="{moon_x - 5}" cy="{moon_y - 4}" r="3" fill="#e0c06f" opacity=".55"/>
<circle cx="{moon_x + 6}" cy="{moon_y + 5}" r="4" fill="#e0c06f" opacity=".45"/>
{gs.corner_web(0, 0, 1, 1, 90)}
{gs.corner_web(W, H, -1, -1, 100)}
<text x="24" y="36" font-family="{FONT}" font-size="16" font-weight="700" fill="#ffb347">{login_x}'s web of commits</text>
<g font-family="{FONT}" font-size="9.5" fill="#8b7fb0">{''.join(labels)}</g>
{''.join(cells)}
<path d="{path}" pathLength="1" fill="none" stroke="#e5defa" stroke-opacity=".4" stroke-width=".7" stroke-dasharray="1 1" stroke-dashoffset="1">
<animate attributeName="stroke-dashoffset" values="1;0;0" keyTimes="0;{RESET};1" dur="{LOOP}s" repeatCount="indefinite"/></path>
{walker}
{hang1}
{hang2}
{bat(0, 17, 0, 1.0)}
{bat(-9, 23, 8, 0.8)}
{bat(-15, 29, -4, 0.65)}
<g font-family="{FONT}" font-size="9.5">
<text x="{LEFT}" y="{legend_y + 9}" fill="#8b7fb0">{total} contributions in the last year - the spider is devouring them</text>
{''.join(legend)}
</g>
</svg>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", default=os.environ.get("GH_USER"))
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    ap.add_argument("--demo", action="store_true", help="use fake data instead of the GitHub API")
    ap.add_argument("--out", default="assets/spider-contributions.svg")
    a = ap.parse_args()

    if a.demo:
        total, weeks = demo_data()
        login = a.login or "you"
    else:
        if not (a.login and a.token):
            sys.exit("Need GH_USER and GITHUB_TOKEN (or pass --demo to preview).")
        total, weeks = fetch(a.login, a.token)
        login = a.login

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(total, weeks, login))
    print(f"wrote {out} ({total} contributions)")


if __name__ == "__main__":
    main()