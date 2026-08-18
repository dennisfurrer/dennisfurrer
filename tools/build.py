#!/usr/bin/env python3
"""
Generates every SVG in assets/, in both themes, from one source of truth.

GitHub strips <style> and <script> from Markdown, but an SVG referenced as an
<img> keeps its own CSS - including @keyframes - so all the motion here lives
inside the files. Theme switching is the <picture> + prefers-color-scheme
pattern GitHub documents, which follows the GitHub theme rather than the OS.

Run:  python3 tools/build.py
"""

import math
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# ── palettes ────────────────────────────────────────────────────────────────
DARK = dict(
    bg="#04070f", panel="#080e1f", frame="#1b2440", cross="#2c3b64",
    text="#eaeeff", dim="#98a6cf", faint="#5d6a90",
    accent="#5d8bff", accent2="#5fe0ff", deep="#3f6fe2",
    glow=".55", dot=".62", grid="#101a33",
)
LIGHT = dict(
    bg="#f7f9ff", panel="#ffffff", frame="#d7e0f4", cross="#b4c3e4",
    text="#0c1330", dim="#46557a", faint="#7d8bae",
    accent="#3f6fe2", accent2="#1d93c8", deep="#2547a8",
    glow=".30", dot=".55", grid="#e6ecfa",
)

DISPLAY = ('-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", '
           'Inter, Helvetica, Arial, sans-serif')
MONO = ('ui-monospace, "SF Mono", "Cascadia Mono", "JetBrains Mono", '
        '"Roboto Mono", Menlo, Consolas, monospace')

# Motion shared by every file. Long expo-ish tails, nothing bouncing.
BASE_KEYFRAMES = """
    @keyframes rise  { from { opacity:0; transform:translateY(10px) } to { opacity:1; transform:none } }
    @keyframes fade  { from { opacity:0 } to { opacity:1 } }
    @keyframes draw  { from { transform:scaleX(0) } to { transform:scaleX(1) } }
    @keyframes blink { 0%,54% { opacity:1 } 55%,100% { opacity:0 } }
    @keyframes spin  { to { transform:rotate(360deg) } }
    @keyframes drift { 0%,100% { transform:translateY(0) } 50% { transform:translateY(-3px) } }
    @keyframes dash  { to { stroke-dashoffset:0 } }
"""

REDUCED = """
    @media (prefers-reduced-motion: reduce) {
      * { animation: none !important }
      .needs-motion { opacity: 1 !important; transform: none !important }
    }
"""


# The DFU mark, taken verbatim from the centered topnav on dfurrer.com so the
# brand is identical across surfaces. Gradient id is namespaced per file.
MARK_PATHS = ('<path d="M 130.37 116.16 L 145.3 100"/>'
              '<path d="M 55.5 59.1 L 93.3 100 L 55.5 140.9"/>'
              '<path d="M 148.5 59.1 L 110.7 100 L 148.5 140.9"/>')


def mark(x, y, size, gid="dfu"):
    k = size / 200.0
    return (f'<g transform="translate({x},{y}) scale({k:.4f})" '
            f'stroke="url(#{gid})" stroke-width="15" stroke-linecap="round" '
            f'stroke-linejoin="round" fill="none">{MARK_PATHS}</g>')


def mark_grad(gid="dfu"):
    return (f'<linearGradient id="{gid}" x1="30%" y1="0%" x2="70%" y2="100%">'
            f'<stop offset="0%" stop-color="#dfe8ff"/>'
            f'<stop offset="55%" stop-color="#9fb4e8"/>'
            f'<stop offset="100%" stop-color="#c7d3f5"/></linearGradient>')


def frame(c, w, h, inset=16.5):
    """Editorial hairline frame with corner crosshairs - carried over from the
    original header, which was the one thing worth keeping."""
    r = w - inset * 2 - 1
    b = h - inset * 2 - 1
    x2, y2 = w - inset, h - inset
    return f"""
  <rect width="{w}" height="{h}" fill="{c['bg']}"/>
  <rect x="{inset}" y="{inset}" width="{r}" height="{b}" fill="none"
        stroke="{c['frame']}" stroke-width="1" shape-rendering="crispEdges"/>
  <g fill="none" stroke="{c['cross']}" stroke-width="1" shape-rendering="crispEdges" class="fade-in">
    <path d="M {inset} {inset-8.5} V {inset+8.5} M {inset-8.5} {inset} H {inset+8.5}"/>
    <path d="M {x2} {inset-8.5} V {inset+8.5} M {x2-8.5} {inset} H {x2+8.5}"/>
    <path d="M {inset} {y2-8.5} V {y2+8.5} M {inset-8.5} {y2} H {inset+8.5}"/>
    <path d="M {x2} {y2-8.5} V {y2+8.5} M {x2-8.5} {y2} H {x2+8.5}"/>
  </g>"""


# ── 1. header ───────────────────────────────────────────────────────────────
def header(c):
    W, H = 1200, 340
    cx, cy, R = 952, 176, 97

    # Fibonacci sphere, orthographic. Same construction as the WebGL field on
    # dfurrer.com - the point of the motif is that it is the same object.
    pts, N = [], 260
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(N):
        y = 1 - 2 * (i + 0.5) / N
        rad = math.sqrt(max(0.0, 1 - y * y))
        th = i * ga
        pts.append((math.cos(th) * rad, y, math.sin(th) * rad))

    dots = []
    for (x, y, z) in pts:
        depth = (z + 1) / 2                      # 0 back .. 1 front
        r = 0.7 + depth * 1.5
        o = 0.10 + depth * 0.72
        col = c["accent2"] if depth > 0.80 else c["accent"]
        dots.append(f'<circle cx="{cx + x*R:.1f}" cy="{cy - y*R:.1f}" '
                    f'r="{r:.2f}" fill="{col}" opacity="{o:.2f}"/>')
    sphere = "".join(dots)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="Dennis Furrer - founder, CTO. Zero to one, end to end.">
  <style>
    .name {{ font-family:{DISPLAY}; font-size:56px; font-weight:600; letter-spacing:11px; fill:{c['text']} }}
    .role {{ font-family:{MONO}; font-size:15.5px; letter-spacing:4.6px; fill:{c['dim']} }}
    .micro{{ font-family:{MONO}; font-size:12px; letter-spacing:3.4px; fill:{c['faint']} }}
    .rule {{ fill:{c['accent']}; transform-origin:left center; transform-box:fill-box;
             animation:draw 1.15s cubic-bezier(.16,1,.3,1) .5s both }}
    .r1   {{ animation:rise 1s cubic-bezier(.16,1,.3,1) .10s both }}
    .r2   {{ animation:rise 1s cubic-bezier(.16,1,.3,1) .70s both }}
    .fade-in {{ animation:fade 1.3s ease .25s both }}
    .late {{ animation:fade 1.5s ease 1.0s both }}
    .cur  {{ animation:blink 1.15s steps(1) 2s infinite both }}
    .orb  {{ transform-origin:{cx}px {cy}px; animation:spin 64s linear infinite }}
    .halo {{ animation:drift 7s ease-in-out infinite }}
    {BASE_KEYFRAMES}{REDUCED}
  </style>
  <defs>
    <radialGradient id="hg" cx="50%" cy="50%">
      <stop offset="0%"  stop-color="{c['accent']}" stop-opacity="{c['glow']}"/>
      <stop offset="60%" stop-color="{c['accent']}" stop-opacity=".05"/>
      <stop offset="100%" stop-color="{c['accent']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="ng" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{c['accent2']}"/>
      <stop offset="55%" stop-color="{c['accent']}"/>
      <stop offset="100%" stop-color="{c['deep']}"/>
    </linearGradient>
    {mark_grad()}
  </defs>
{frame(c, W, H)}
  <ellipse cx="{cx}" cy="{cy}" rx="172" ry="150" fill="url(#hg)" class="halo"/>
  <g class="orb late">{sphere}</g>

  <g class="fade-in">{mark(66, 44, 38)}</g>
  <g class="micro fade-in">
    <text x="116" y="70">FOUNDER &#183; CTO &#183; 10Y IN WEB3</text>
    <text x="66" y="306">ZERO &#8594; ONE, END TO END</text>
    <text x="1134" y="306" text-anchor="end">DFURRER.COM</text>
  </g>

  <text class="name r1" x="66" y="176">DENNIS<tspan fill="url(#ng)"> FURRER</tspan><tspan class="cur" fill="{c['accent2']}">_</tspan></text>
  <rect class="rule" x="66" y="198" width="232" height="2"/>
  <text class="role r2" x="66" y="230">DISTRIBUTED SYSTEMS &#183; LOW LATENCY</text>
  <text class="role r2" x="66" y="252">CONSUMER APPS &#183; WHITELABEL PLATFORMS</text>
</svg>
"""


# ── 2. stat band ────────────────────────────────────────────────────────────
STATS = [
    ("1M+", "MONTHLY ACTIVES", "globe.li"),
    ("#1", "OF 569 ON PM.WIKI", "globe.li"),
    ("4", "SDK LANGUAGES", "hip4.dev"),
    ("5", "COMPANIES 0→1", "founding / CTO"),
    ("9", "VENUES INTEGRATED", "pred · spot · perps"),
    ("65", "TOOLS SHIPPED", "in 2026"),
]


def stats(c):
    W, H = 1200, 168
    n = len(STATS)
    colw = (W - 88) / n
    # Adding a column silently shrinks every other one; the sub line overflowed
    # first and ran into its neighbour. Fail loudly instead of shipping it.
    for _b, lab, sub in STATS:
        for txt, adv in ((lab, 12 * .60 + 2.6), (sub, 10.5 * .60 + 1.2)):
            if len(txt) * adv > colw - 12:
                raise SystemExit(
                    f"stats: '{txt}' is ~{len(txt)*adv:.0f}px in a {colw:.0f}px "
                    f"column - shorten it or drop a column")
    out = []
    for i, (big, label, sub) in enumerate(STATS):
        x = 44 + colw * i + colw / 2
        d = 0.25 + i * 0.11
        out.append(f"""
  <g style="animation:rise .95s cubic-bezier(.16,1,.3,1) {d:.2f}s both" class="needs-motion">
    <text x="{x:.1f}" y="80" text-anchor="middle" class="big">{big}</text>
    <text x="{x:.1f}" y="110" text-anchor="middle" class="lab">{label}</text>
    <text x="{x:.1f}" y="132" text-anchor="middle" class="sub">{sub}</text>
  </g>""")
        if i:
            dx = 44 + colw * i
            out.append(f'<rect x="{dx:.1f}" y="48" width="1" height="76" fill="{c["frame"]}" '
                       f'class="fade-in" shape-rendering="crispEdges"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="{' - '.join(f'{b} {l} ({s})' for b, l, s in STATS)}">
  <style>
    .big {{ font-family:{DISPLAY}; font-size:46px; font-weight:600; letter-spacing:-1px; fill:{c['text']} }}
    .lab {{ font-family:{MONO}; font-size:12px; letter-spacing:2.6px; fill:{c['dim']} }}
    .sub {{ font-family:{MONO}; font-size:10.5px; letter-spacing:1.2px; fill:{c['faint']} }}
    .fade-in {{ animation:fade 1.2s ease .3s both }}
    {BASE_KEYFRAMES}{REDUCED}
  </style>
{frame(c, W, H, 12.5)}
{''.join(out)}
</svg>
"""


# ── 3. the 2026 arc ─────────────────────────────────────────────────────────
ARC = [
    ("APR 19", "axis v0.1", "the first evening"),
    ("APR 22", "globe.li", "still the current system"),
    ("MAY", "HIP-4 firsts", "testnet market, first SDK"),
    ("JUN", "perps.studio", "exchange in five minutes"),
    ("JUL", "Everex", "ingest → backtest → signals"),
    ("AUG", "builder.markets", "six venues, one book"),
]


def arc(c):
    W, H = 1200, 256
    y = 130
    x0, x1 = 92, W - 92
    step = (x1 - x0) / (len(ARC) - 1)
    out = []
    for i, (when, what, note) in enumerate(ARC):
        x = x0 + step * i
        d = 0.8 + i * 0.16
        up = i % 2 == 0
        ty = y - 30 if up else y + 46
        ny = y - 48 if up else y + 64
        out.append(f"""
  <g style="animation:fade .8s ease {d:.2f}s both" class="needs-motion">
    <circle cx="{x:.1f}" cy="{y}" r="5.5" fill="{c['bg']}" stroke="{c['accent']}" stroke-width="2"/>
    <circle cx="{x:.1f}" cy="{y}" r="2" fill="{c['accent2']}"/>
    <text x="{x:.1f}" y="{ty}" text-anchor="middle" class="what">{what}</text>
    <text x="{x:.1f}" y="{ny}" text-anchor="middle" class="note">{note}</text>
    <text x="{x:.1f}" y="{y + (20 if up else -12)}" text-anchor="middle" class="when">{when}</text>
  </g>""")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="2026 arc: {'; '.join(f'{w} {t} - {n}' for w, t, n in ARC)}">
  <style>
    .what {{ font-family:{DISPLAY}; font-size:19.5px; font-weight:600; letter-spacing:-.2px; fill:{c['text']} }}
    .note {{ font-family:{MONO}; font-size:11.5px; letter-spacing:1.2px; fill:{c['faint']} }}
    .when {{ font-family:{MONO}; font-size:11.5px; letter-spacing:2px; fill:{c['accent']} }}
    .title{{ font-family:{MONO}; font-size:12px; letter-spacing:3.2px; fill:{c['faint']} }}
    .line {{ stroke:{c['accent']}; stroke-width:1.5; fill:none; stroke-dasharray:1020;
             stroke-dashoffset:1020; animation:dash 2.2s cubic-bezier(.16,1,.3,1) .35s both }}
    .fade-in {{ animation:fade 1.2s ease .25s both }}
    {BASE_KEYFRAMES}{REDUCED}
  </style>
{frame(c, W, H, 12.5)}
  <text x="44" y="42" class="title">THE 2026 ARC &#183; SIXTEEN WEEKS, BESIDE THE DAY JOB</text>
  <path class="line" d="M {x0} {y} H {x1}"/>
{''.join(out)}
</svg>
"""


# ── 4. the stack ────────────────────────────────────────────────────────────
# The trading stack only. pro., laptime.dev and this.poc.rocks are separate
# products and deliberately not on this diagram.
# "→" renders as a built-on arrow rather than a chip.
LAYERS = [
    ("VENUES", ["Hyperliquid", "Polymarket", "Kalshi", "Limitless", "Myriad",
                "Metaculus", "Manifold", "Aster", "Lighter"]),
    ("PROTOCOL", ["hip4.dev  ·  TS / Rust / Python / Go"]),
    ("INFRASTRUCTURE", ["perps.studio", "→", "Everex", "OMEN"]),
    ("MARKETS", ["outcome.xyz"]),
    ("AGGREGATION", ["builder.markets", "parlayer.xyz", "ide.finance"]),
    ("TERMINAL", ["globe.li"]),
]


def stack(c):
    W = 1200
    rowh, top = 74, 82
    H = top + rowh * len(LAYERS) - 18
    out = []
    for li, (name, items) in enumerate(LAYERS):
        y = top + rowh * li
        d = 0.3 + li * 0.14
        out.append(f'<text x="44" y="{y+26}" class="layer">{name}</text>')
        if li:
            out.append(f'<rect x="44" y="{y-14}" width="{W-88}" height="1" fill="{c["frame"]}" '
                       f'shape-rendering="crispEdges" class="fade-in"/>')
        bx = 254
        derived = False
        for it in items:
            if it == "\u2192":                       # built-on marker
                out.append(f'<text x="{bx+9:.0f}" y="{y+28}" class="arrow">&#8594;</text>')
                bx += 30
                derived = True
                continue
            w = 17 + len(it) * 8.5
            accent = li in (1, len(LAYERS) - 1) and not derived
            fill = c["panel"] if not accent else c["accent"]
            txt = c["text"] if not accent else ("#04070f" if c is DARK else "#ffffff")
            stroke = c["frame"] if not accent else c["accent"]
            out.append(f"""
  <g style="animation:rise .9s cubic-bezier(.16,1,.3,1) {d:.2f}s both" class="needs-motion">
    <rect x="{bx:.0f}" y="{y+6}" width="{w:.0f}" height="34" rx="6" fill="{fill}" stroke="{stroke}"/>
    <text x="{bx + w/2:.0f}" y="{y+28}" text-anchor="middle" class="chip" fill="{txt}">{it}</text>
  </g>""")
            bx += w + 13
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="The stack: {'; '.join(n + ': ' + ', '.join(i) for n, i in LAYERS)}">
  <style>
    .layer{{ font-family:{MONO}; font-size:12px; letter-spacing:2.8px; fill:{c['faint']} }}
    .chip {{ font-family:{MONO}; font-size:13.5px; letter-spacing:.4px }}
    .arrow{{ font-family:{MONO}; font-size:15px; fill:{c['accent']} }}
    .title{{ font-family:{MONO}; font-size:12px; letter-spacing:3.2px; fill:{c['faint']} }}
    .fade-in {{ animation:fade 1.2s ease .3s both }}
    {BASE_KEYFRAMES}{REDUCED}
  </style>
{frame(c, W, H, 12.5)}
  <text x="44" y="44" class="title">ONE STACK, NOT A PILE OF SIDE PROJECTS</text>
{''.join(out)}
</svg>
"""


BUILDERS = {"header": header, "stats": stats, "arc": arc, "stack": stack}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILDERS.items():
        for theme, pal in (("dark", DARK), ("light", LIGHT)):
            path = os.path.join(OUT, f"{name}-{theme}.svg")
            with open(path, "w") as f:
                f.write(fn(pal))
            print(f"  {os.path.relpath(path, os.path.dirname(OUT))}  {os.path.getsize(path):,} bytes")
    print("done")
