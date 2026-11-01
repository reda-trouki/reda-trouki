#!/usr/bin/env python3
"""Animated 'About me' card: a spooky terminal that types out your intro,
next to floating stack pills. Edit the CONFIG block and re-run:

    python scripts/generate_about_card.py
"""
import random
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_spider as gs

# ---- CONFIG: edit me ---------------------------------------------------------
NAME = "Reda Trouki"
ROLE = "Full Stack Developer"
ABOUT = "Turning ideas into web and mobile apps from Morocco."
FOCUS = "Full Stack Development"
LEARNING = ["Angular", "React-Native", "Docker"]
ASK_ME = "Web dev / App dev / Tech"
FORTUNE = ['"There are two ways to write error-free programs;', 'only the third one works"']
STACK = [
    ("Front-end", ["React", "Vue", "Angular", "Tailwind", "Bootstrap", "Chakra UI"]),
    ("Back-end", ["Node", "Express", "Spring Boot", "Flask", "Laravel"]),
    ("Mobile", ["React Native"]),
    ("Databases", ["MongoDB", "MySQL", "PostgreSQL"]),
    ("Extras", ["GraphQL", "Redux", "Prisma"]),
]
LEARNING_PILLS = ["Angular", "React Native", "Docker"]
# -----------------------------------------------------------------------------

W = 900
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
ORANGE, GOLD, CMD, OUT, MUTED = "#ff7518", "#ffb347", "#e5defa", "#b9a6e6", "#8b7fb0"
FS, CW = 13, 7.8          # font size / approx monospace char width
LINE_H = 20
TERM_X, TERM_W = 20, 520
COL_X = 566
COL_W = W - COL_X - 24


def terminal_lines():
    P = ("$ ", ORANGE)
    return [
        ("cmd", [P, ("whoami", CMD)]),
        ("out", [(NAME, GOLD), (" - " + ROLE, OUT)]),
        ("cmd", [P, ("cat about.txt", CMD)]),
        ("out", [(ABOUT, OUT)]),
        ("cmd", [P, ("echo $FOCUS", CMD)]),
        ("out", [(FOCUS, GOLD)]),
        ("cmd", [P, ("ls learning/", CMD)]),
        ("out", [("  ".join(LEARNING), GOLD)]),
        ("cmd", [P, ("ask --me-about", CMD)]),
        ("out", [(ASK_ME, OUT)]),
        ("cmd", [P, ("fortune", CMD)]),
        ("out", [(FORTUNE[0], OUT)]),
        ("out", [(FORTUNE[1], OUT)]),
        ("prompt", [P]),
    ]


def pill(x, y, text, learning, rnd):
    w = len(text) * 7.0 + 20
    if learning:
        fill, stroke, tcol = "#3a1c08", ORANGE, "#ffd9a0"
    else:
        fill, stroke, tcol = "#231445", "#5b3a99", CMD
    dur, delay = rnd.uniform(2.6, 4.2), rnd.uniform(0, 3)
    return w, (
        f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -2.5;0 0" '
        f'dur="{dur:.1f}s" begin="-{delay:.1f}s" repeatCount="indefinite"/>'
        f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="22" rx="11" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
        f'<text x="{x + w / 2:.1f}" y="{y + 15}" text-anchor="middle" font-size="11.5" fill="{tcol}">{escape(text)}</text></g>'
    )


def build():
    rnd = random.Random(21)
    lines = terminal_lines()

    # ---- chips column (also tells us how tall the card must be)
    chips, y = [], 62
    groups = [(label, items, False) for label, items in STACK] + [("Learning", LEARNING_PILLS, True)]
    for label, items, learning in groups:
        chips.append(f'<text x="{COL_X}" y="{y}" font-size="10.5" fill="{MUTED}">{escape(label.upper())}</text>')
        px, py = COL_X, y + 5
        for item in items:
            w = len(item) * 7.0 + 20
            if px + w > COL_X + COL_W:
                px, py = COL_X, py + 26
            _, svg = pill(px, py, item, learning, rnd)
            chips.append(svg)
            px += w + 8
        y = py + 22 + 18
    chips_bottom = y - 18

    term_text_y0 = 24 + 34 + 20
    term_bottom = term_text_y0 + (len(lines) - 1) * LINE_H + 16
    H = int(max(chips_bottom, term_bottom) + 24)

    # ---- typing timeline
    t, timing = 0.6, []
    for kind, segs in lines:
        n = sum(len(s) for s, _ in segs)
        dt = {"cmd": 0.07, "out": 0.018, "prompt": 0.05}[kind]
        timing.append((t, dt, n))
        t += n * dt + (0.45 if kind == "cmd" else 0.35)
    t_last = timing[-1][0] + timing[-1][2] * timing[-1][1]
    T = t_last + 7

    clips, texts = [], []
    tx = TERM_X + 18
    for i, ((kind, segs), (ts, dt, n)) in enumerate(zip(lines, timing)):
        ty = term_text_y0 + i * LINE_H
        values = ["0"] + [f"{k * CW:.1f}" for k in range(1, n + 1)]
        values[-1] = "2000"
        keys = ["0"] + [f"{(ts + k * dt) / T:.5f}" for k in range(1, n + 1)]
        clips.append(
            f'<clipPath id="c{i}"><rect x="{tx}" y="{ty - 13}" width="2000" height="19">'
            f'<animate attributeName="width" calcMode="discrete" dur="{T:.2f}s" repeatCount="indefinite" '
            f'values="{";".join(values)}" keyTimes="{";".join(keys)}"/></rect></clipPath>')
        spans = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in segs)
        texts.append(f'<text x="{tx}" y="{ty}" font-size="{FS}" xml:space="preserve" clip-path="url(#c{i})">{spans}</text>')

    cur_y = term_text_y0 + (len(lines) - 1) * LINE_H
    cursor = (
        f'<g opacity="0"><animate attributeName="opacity" calcMode="discrete" dur="{T:.2f}s" repeatCount="indefinite" '
        f'values="0;1" keyTimes="0;{t_last / T:.5f}"/>'
        f'<rect x="{tx + 2 * CW + 1:.1f}" y="{cur_y - 11}" width="7" height="14" fill="{ORANGE}">'
        f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect></g>')

    d_h, hang = None, None
    defs_h, art = gs.spider("ab", speed=0.9)
    hx = W - 44
    hang = (
        f'<g transform="translate({hx},12)"><animateTransform attributeName="transform" type="translate" '
        f'values="{hx},12;{hx},26;{hx},12" dur="3.8s" repeatCount="indefinite"/>'
        f'<line x1="0" y1="-60" x2="0" y2="0" stroke="#cfc8e6" stroke-opacity=".55" stroke-width=".8"/>'
        f'<g transform="rotate(90) scale(.3)">{art}</g></g>')

    term_h = H - 48
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="About {escape(NAME)}: {escape(ROLE)}. {escape(ABOUT)} Focus: {escape(FOCUS)}. Learning: {escape(', '.join(LEARNING))}.">
<title>About {escape(NAME)}</title>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#140d24"/><stop offset="1" stop-color="#22123a"/></linearGradient>
{defs_h}
{''.join(clips)}
</defs>
<rect width="{W}" height="{H}" rx="14" fill="url(#bg)" stroke="#3a2a5c"/>
{gs.corner_web(W, H, -1, -1, 100)}
{gs.corner_web(W, 0, -1, 1, 80)}
<rect x="{TERM_X}" y="24" width="{TERM_W}" height="{term_h}" rx="10" fill="#0c0815" stroke="#3a2a5c"/>
<path d="M{TERM_X},58 L{TERM_X + TERM_W},58" stroke="#3a2a5c"/>
<circle cx="{TERM_X + 18}" cy="41" r="5" fill="{ORANGE}"/><circle cx="{TERM_X + 36}" cy="41" r="5" fill="{GOLD}"/><circle cx="{TERM_X + 54}" cy="41" r="5" fill="#8e44ad"/>
<g font-family="{FONT}">
<text x="{TERM_X + 76}" y="45" font-size="11" fill="{MUTED}">{escape(NAME.split()[0].lower())}@lair: ~</text>
{''.join(texts)}
{cursor}
<text x="{COL_X}" y="40" font-size="12" font-weight="700" fill="{ORANGE}">// stack</text>
{''.join(chips)}
</g>
{hang}
</svg>
"""


def main():
    out = Path("assets/about-card.svg")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()