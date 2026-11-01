#!/usr/bin/env python3
"""Generate the animated spider SVGs used in README.md.

The spider's size depends on how many commits the repo has, so it literally
grows as the project grows. Run locally with `python scripts/generate_spider.py`
or let the GitHub Action do it on every push.

Usage:
    python scripts/generate_spider.py            # uses `git rev-list --count HEAD`
    python scripts/generate_spider.py --commits 300   # preview a given size
"""
import argparse
import math
import subprocess
from pathlib import Path

STAGES = [(0, "Spiderling"), (25, "Juvenile"), (100, "Subadult"), (250, "Adult"), (500, "Giant")]


def commit_count() -> int:
    try:
        out = subprocess.check_output(["git", "rev-list", "--count", "HEAD"], text=True)
        return max(1, int(out.strip()))
    except Exception:
        return 1


def stage_info(n):
    idx = 0
    for i, (threshold, _) in enumerate(STAGES):
        if n >= threshold:
            idx = i
    name = STAGES[idx][1]
    if idx + 1 < len(STAGES):
        lo, hi = STAGES[idx][0], STAGES[idx + 1][0]
        return name, (n - lo) / (hi - lo), hi
    return name, 1.0, None


def spider_scale(n):
    """Smooth growth: tiny spiderling -> big, but never absurd."""
    return 0.45 + 1.15 * (1 - math.exp(-n / 150))


# --------------------------------------------------------------------------
# The spider (top-down view, facing +x, centred on the origin)
# --------------------------------------------------------------------------
# (attach x, femur angle, bend of the lower segments)
LEGS = [(12, -48, 22), (7, -78, 12), (2, -108, -12), (-3, -140, -22)]
LEG_COLOR = "#6a4a33"


def _pt(x, y, ang, length):
    r = math.radians(ang)
    return x + length * math.cos(r), y + length * math.sin(r)


def _leg(ang, bend, delay, speed):
    p1 = _pt(0, 0, ang, 17)
    p2 = _pt(*p1, ang + bend, 22)
    p3 = _pt(*p2, ang + bend * 2.2, 13)
    f = lambda p: f"{p[0]:.1f},{p[1]:.1f}"
    return (
        f'<g><animateTransform attributeName="transform" type="rotate" '
        f'values="-10;10;-10" dur="{speed}s" begin="{delay}s" repeatCount="indefinite"/>'
        f'<path d="M0,0 L{f(p1)}" stroke="{LEG_COLOR}" stroke-width="2.6" stroke-linecap="round" fill="none"/>'
        f'<path d="M{f(p1)} L{f(p2)}" stroke="{LEG_COLOR}" stroke-width="1.8" stroke-linecap="round" fill="none"/>'
        f'<path d="M{f(p2)} L{f(p3)}" stroke="{LEG_COLOR}" stroke-width="1.1" stroke-linecap="round" fill="none"/>'
        f'<circle cx="{p1[0]:.1f}" cy="{p1[1]:.1f}" r="1.7" fill="#8a6a4a"/>'
        f'<circle cx="{p2[0]:.1f}" cy="{p2[1]:.1f}" r="1.3" fill="#8a6a4a"/></g>'
    )


def spider(uid, speed=0.6):
    half = speed / 2
    top, bottom = [], []
    for i, (ax, ang, bend) in enumerate(LEGS):
        d_top = -(i % 2) * half
        d_bot = -((i + 1) % 2) * half
        top.append(f'<g transform="translate({ax},-4)">{_leg(ang, bend, d_top, speed)}</g>')
        bottom.append(f'<g transform="translate({ax},-4)">{_leg(ang, bend, d_bot, speed)}</g>')
    legs = "".join(top) + '<g transform="scale(1,-1)">' + "".join(bottom) + "</g>"

    eyes_spec = [(18, -1.4, 1.3), (18, 1.4, 1.3), (17.5, -3.6, 0.9), (17.5, 3.6, 0.9),
                 (15, -4.6, 0.8), (15, 4.6, 0.8), (14, -1.8, 0.7), (14, 1.8, 0.7)]
    eyes = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#080605" stroke="#b8895f" stroke-width=".3"/>'
        for x, y, r in eyes_spec
    )
    glints = "".join(
        f'<circle cx="{x - .3}" cy="{y - .3}" r=".35" fill="#fff" opacity=".7"/>'
        for x, y, _ in eyes_spec[:2]
    )

    defs = (
        f'<radialGradient id="ab{uid}" cx="38%" cy="32%" r="80%">'
        f'<stop offset="0" stop-color="#7a5539"/><stop offset=".5" stop-color="#3a2619"/>'
        f'<stop offset="1" stop-color="#140c07"/></radialGradient>'
        f'<radialGradient id="ce{uid}" cx="45%" cy="35%" r="80%">'
        f'<stop offset="0" stop-color="#8a6140"/><stop offset=".6" stop-color="#46301f"/>'
        f'<stop offset="1" stop-color="#1a110b"/></radialGradient>'
    )

    body = f"""
<g>
  <animateTransform attributeName="transform" type="rotate" values="-2.5 -8 0;2.5 -8 0;-2.5 -8 0" dur="{speed * 2}s" repeatCount="indefinite"/>
  <ellipse cx="-22" cy="0" rx="18" ry="13" fill="url(#ab{uid})" stroke="#8a6a4a" stroke-width=".6" stroke-opacity=".8"/>
  <path d="M-36,0 Q-29,-4 -22,-3 Q-14,-2 -10,0 Q-14,2 -22,3 Q-29,4 -36,0Z" fill="#a67c52" opacity=".3"/>
  <path d="M-31,-5 L-25,0 L-31,5 M-24,-6 L-18,0 L-24,6 M-17,-5 L-12,0 L-17,5" stroke="#a67c52" stroke-width=".8" fill="none" opacity=".5" stroke-linecap="round"/>
  <ellipse cx="-26" cy="-6" rx="7" ry="3" transform="rotate(-20 -26 -6)" fill="#fff" opacity=".12"/>
</g>
<ellipse cx="-6" cy="0" rx="3.5" ry="3" fill="#2a1a10"/>
<ellipse cx="6" cy="0" rx="13" ry="9" fill="url(#ce{uid})" stroke="#8a6a4a" stroke-width=".6" stroke-opacity=".8"/>
<ellipse cx="3" cy="0" rx="4" ry="2.5" fill="#1a110b" opacity=".6"/>
<path d="M17,-3 L25,-4.5 M17,3 L25,4.5" stroke="{LEG_COLOR}" stroke-width="1.5" stroke-linecap="round"/>
<path d="M19.5,-1.6 q3,.4 3.6,2.6 M19.5,1.6 q3,-.4 3.6,-2.6" stroke="#2a1a10" stroke-width="1.2" fill="none" stroke-linecap="round"/>
{eyes}{glints}"""
    return defs, legs + body


# --------------------------------------------------------------------------
# Decorations
# --------------------------------------------------------------------------
def corner_web(x, y, flip_x=1, flip_y=1, size=130):
    pts = []
    spokes = 6
    out = []
    for i in range(spokes + 1):
        a = math.radians(90 * i / spokes)
        out.append(f"M{x},{y} L{x + flip_x * size * math.cos(a):.1f},{y + flip_y * size * math.sin(a):.1f}")
    arcs = []
    for r in (30, 55, 80, 105, size):
        prev = None
        for i in range(spokes + 1):
            a = math.radians(90 * i / spokes)
            p = (x + flip_x * r * math.cos(a), y + flip_y * r * math.sin(a))
            if prev:
                cx = (prev[0] + p[0]) / 2 - (prev[0] + p[0] - 2 * x) * 0.07
                cy = (prev[1] + p[1]) / 2 - (prev[1] + p[1] - 2 * y) * 0.07
                arcs.append(f"M{prev[0]:.1f},{prev[1]:.1f} Q{cx:.1f},{cy:.1f} {p[0]:.1f},{p[1]:.1f}")
            prev = p
    return (f'<path d="{" ".join(out)} {" ".join(arcs)}" stroke="#8b949e" stroke-opacity=".35" '
            f'stroke-width=".8" fill="none"/>')


def wave_path(amp, period, phase, y0, reverse=False, x_from=-100, x_to=1000, step=10):
    xs = list(range(x_from, x_to + 1, step))
    if reverse:
        xs.reverse()
    pts = [f"{x},{y0 + amp * math.sin(x / period + phase):.1f}" for x in xs]
    return "M" + " L".join(pts)


def crawler(path, scale, uid, dur, delay=0):
    defs, art = spider(uid)
    return defs, (
        f'<g><animateMotion dur="{dur}s" begin="{delay}s" repeatCount="indefinite" rotate="auto" path="{path}"/>'
        f'<g transform="scale({scale:.3f})">{art}</g></g>'
    )


# --------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------
def banner(n):
    name, prog, nxt = stage_info(n)
    scale = spider_scale(n) * 1.25
    path = "M -90 175 C 90 40, 230 215, 400 125 S 650 30, 780 145 S 930 200, 1010 120"
    defs, walker = crawler(path, scale, "b", 24)
    nxt_txt = f"next molt at {nxt} commits" if nxt else "fully grown"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240" viewBox="0 0 900 240" role="img" aria-label="A spider crawling across the banner. Stage: {name}, {n} commits.">
<title>{name} - {n} commits</title>
<defs>{defs}</defs>
{corner_web(0, 0, 1, 1)}
{corner_web(900, 0, -1, 1)}
<path d="{path}" stroke="#8b949e" stroke-opacity=".45" stroke-width="1" stroke-dasharray="2 5" fill="none"/>
{walker}
<g font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="12" fill="#8b949e">
  <text x="24" y="206">stage: {name} - {n} commits</text>
  <rect x="24" y="214" width="180" height="5" rx="2.5" fill="#8b949e" opacity=".25"/>
  <rect x="24" y="214" width="{180 * prog:.1f}" height="5" rx="2.5" fill="#a67c52"/>
  <text x="24" y="234" font-size="10" opacity=".8">{nxt_txt}</text>
</g>
</svg>
"""


def divider(n, i, reverse, dur, delay):
    scale = spider_scale(n) * 0.62
    path = wave_path(amp=14 + 4 * i, period=60 + 25 * i, phase=i * 1.7, y0=40, reverse=reverse)
    defs, walker = crawler(path, scale, f"d{i}", dur, delay)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="80" viewBox="0 0 900 80" role="img" aria-label="A spider crawling along a silk thread">
<defs>{defs}</defs>
<path d="{path}" stroke="#8b949e" stroke-opacity=".45" stroke-width="1" stroke-dasharray="2 5" fill="none"/>
{walker}
</svg>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commits", type=int, help="override the commit count (for previews)")
    ap.add_argument("--out", default="assets")
    args = ap.parse_args()

    n = args.commits or commit_count()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    (out / "spider-banner.svg").write_text(banner(n))
    (out / "spider-divider-1.svg").write_text(divider(n, 0, False, 16, 0))
    (out / "spider-divider-2.svg").write_text(divider(n, 1, True, 19, -6))
    (out / "spider-divider-3.svg").write_text(divider(n, 2, False, 14, -3))

    name, _, _ = stage_info(n)
    print(f"{n} commits -> {name} (scale {spider_scale(n):.2f})")


if __name__ == "__main__":
    main()