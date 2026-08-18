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
SEP = "  \u00b7  "
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


def esc(t):
    """SVG is XML: a bare & in a label breaks the entire file, silently, and
    the browser just renders nothing. Escape everything that goes into a
    <text> node."""
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


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
# Globe left, pro right, name between them - nothing sits behind the type.
# The globe is drawn the way globe.li draws it: graticule wireframe, event
# markers, great-circle arcs, rather than a generic particle ball.
def globe(c, cx, cy, R):
    o = []
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#gsphere)"/>')
    # latitude rings
    for lat in (-60, -30, 0, 30, 60):
        rr = R * math.cos(math.radians(lat))
        yy = cy - R * math.sin(math.radians(lat))
        o.append(f'<ellipse cx="{cx}" cy="{yy:.1f}" rx="{rr:.1f}" ry="{rr*0.26:.1f}" '
                 f'fill="none" stroke="{c["accent"]}" stroke-width="0.7" opacity="{0.5 if lat==0 else 0.26}"/>')
    # meridians
    for k in range(6):
        rx = abs(R * math.cos(math.pi * k / 6))
        o.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{max(rx,0.6):.1f}" ry="{R}" '
                 f'fill="none" stroke="{c["accent"]}" stroke-width="0.7" opacity=".22"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{c["accent2"]}" '
             f'stroke-width="1.1" opacity=".55"/>')
    # event markers, front hemisphere only, and arcs between a few of them
    pts, N = [], 130
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(N):
        yv = 1 - 2 * (i + 0.5) / N
        rad = math.sqrt(max(0.0, 1 - yv * yv))
        th = i * ga
        x, z = math.cos(th) * rad, math.sin(th) * rad
        if z < 0.02:
            continue
        pts.append((cx + x * R, cy - yv * R, z))
    for (x, y, z) in pts:
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{0.6+z*0.9:.2f}" '
                 f'fill="{c["dim"]}" opacity="{0.10+z*0.34:.2f}"/>')
    hot = [pts[i] for i in (7, 23, 41, 58, 74) if i < len(pts)]
    for i, (x, y, z) in enumerate(hot):
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="#ffb648" opacity=".9"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="none" stroke="#ffb648" '
                 f'stroke-width="1" opacity=".35" class="ping" style="animation-delay:{i*0.7:.1f}s"/>')
    for i in range(len(hot) - 1):
        x1, y1, _ = hot[i]; x2, y2, _ = hot[i + 1]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - abs(x2 - x1) * 0.42 - 8
        o.append(f'<path d="M {x1:.1f} {y1:.1f} Q {mx:.1f} {my:.1f} {x2:.1f} {y2:.1f}" '
                 f'fill="none" stroke="{c["accent2"]}" stroke-width="1" opacity=".5"/>')
    return "".join(o)


def pro_panels(c, x, y, w, h):
    """pro's six tools, two across and three down. Two columns rather than
    three because at this size a three-wide grid cannot hold the labels."""
    o, gap = [], 8
    pw, ph = (w - gap) / 2, (h - gap * 2) / 3
    for i, name in enumerate(("think", "plan", "design", "code", "collab", "glass")):
        px_ = x + (i % 2) * (pw + gap)
        py_ = y + (i // 2) * (ph + gap)
        o.append(f'<rect x="{px_:.0f}" y="{py_:.0f}" width="{pw:.0f}" height="{ph:.0f}" rx="4" '
                 f'fill="{c["panel"]}" stroke="{c["frame"]}"/>')
        o.append(f'<rect x="{px_:.0f}" y="{py_:.0f}" width="{pw:.0f}" height="9" rx="4" fill="{c["frame"]}" opacity=".55"/>')
        for d in range(3):
            o.append(f'<circle cx="{px_+7+d*5.5:.1f}" cy="{py_+4.5:.1f}" r="1.3" fill="{c["faint"]}" opacity=".8"/>')
        o.append(f'<text x="{px_+pw/2:.0f}" y="{py_+ph/2+8:.0f}" text-anchor="middle" class="pn">{name}</text>')
    return "".join(o)


def header(c):
    W, H = 1200, 340
    gx, gy, gr = 186, 170, 78
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="Dennis Furrer - founder, CTO. dfurrer.com.">
  <style>
    .name {{ font-family:{DISPLAY}; font-size:50px; font-weight:600; letter-spacing:9px; fill:{c['text']} }}
    .micro{{ font-family:{MONO}; font-size:12px; letter-spacing:3.4px; fill:{c['faint']} }}
    .pn   {{ font-family:{MONO}; font-size:10px; letter-spacing:.4px; fill:{c['dim']} }}
    .rule {{ fill:{c['accent']}; transform-origin:center; transform-box:fill-box;
             animation:draw 1.15s cubic-bezier(.16,1,.3,1) .5s both }}
    .r1   {{ animation:rise 1s cubic-bezier(.16,1,.3,1) .10s both }}
    .fade-in {{ animation:fade 1.3s ease .25s both }}
    .late {{ animation:fade 1.5s ease .9s both }}
    .cur  {{ animation:blink 1.15s steps(1) 2s infinite both }}
    .ping {{ animation:ping 3.2s ease-out infinite }}
    @keyframes ping {{ 0% {{ transform:scale(.5); opacity:.6 }} 70%,100% {{ transform:scale(1.5); opacity:0 }} }}
    {BASE_KEYFRAMES}{REDUCED}
  </style>
  <defs>
    <radialGradient id="gsphere" cx="38%" cy="32%">
      <stop offset="0%" stop-color="{c['accent']}" stop-opacity=".30"/>
      <stop offset="70%" stop-color="{c['bg']}" stop-opacity=".85"/>
      <stop offset="100%" stop-color="{c['bg']}" stop-opacity=".98"/>
    </radialGradient>
    <linearGradient id="ng" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{c['accent2']}"/>
      <stop offset="55%" stop-color="{c['accent']}"/>
      <stop offset="100%" stop-color="{c['deep']}"/>
    </linearGradient>
    {mark_grad()}
  </defs>
{frame(c, W, H)}
  <g class="late">{globe(c, gx, gy, gr)}</g>
  <g class="late">{pro_panels(c, 918, 104, 200, 132)}</g>
  <text x="{gx}" y="272" text-anchor="middle" class="micro">GLOBE.LI</text>
  <text x="1018" y="272" text-anchor="middle" class="micro">PRO.</text>

  <g class="fade-in">{mark(583, 34, 34)}</g>
  <text class="name r1" x="600" y="176" text-anchor="middle">DENNIS<tspan fill="url(#ng)"> FURRER</tspan><tspan class="cur" fill="{c['accent2']}">_</tspan></text>
  <rect class="rule" x="490" y="198" width="220" height="2"/>
  <text class="micro fade-in" x="600" y="306" text-anchor="middle">DFURRER.COM</text>
</svg>
"""


# ── 2. stat band ────────────────────────────────────────────────────────────
STATS = [
    ("5", "COMPANIES 0→1", "founding · CTO"),
    ("$1.1B+", "MARKET CAP", "combined"),
    ("#1", "HYPERLIQUID", "HIP-4 builder, worldwide"),
    ("$39M+", "RAISED", "combined"),
    ("1M+", "MONTHLY ACTIVES", "across the work"),
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
    <text x="{x:.1f}" y="80" text-anchor="middle" class="big">{esc(big)}</text>
    <text x="{x:.1f}" y="110" text-anchor="middle" class="lab">{esc(label)}</text>
    <text x="{x:.1f}" y="132" text-anchor="middle" class="sub">{esc(sub)}</text>
  </g>""")
        if i:
            dx = 44 + colw * i
            out.append(f'<rect x="{dx:.1f}" y="48" width="1" height="76" fill="{c["frame"]}" '
                       f'class="fade-in" shape-rendering="crispEdges"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="{esc(' - '.join(f'{b} {l} ({s})' for b, l, s in STATS))}">
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


# ── 4. the stack ────────────────────────────────────────────────────────────
# The trading stack only. pro., laptime.dev and this.poc.rocks are separate
# products and deliberately not on this diagram.
# "→" renders as a built-on arrow rather than a chip. Rows wrap.
INTEGRATIONS = [
    "Hyperliquid", "Polymarket", "Kalshi", "Limitless", "Metaculus", "Myriad",
    "Manifold", "Lighter", "Aster", "Arcus", "Uniswap", "Jupiter", "1inch",
    "0x", "Relay", "LiFi", "deBridge", "Across", "OogaBooga", "yield.xyz",
]
LAYERS = [
    ("INTEGRATIONS", INTEGRATIONS),
    ("INFRASTRUCTURE", ["hip4 SDKs", "perps.studio", "rwas.studio", "prps.app",
                        "predict.prps.app", "spot.prps.app"]),
    ("MARKETS", ["outcome.xyz", "everex.pro", "vyper.rekt.fi", "omen.predi.cc",
                 "predict.perps.studio", "+ many more"]),
    ("AGGREGATION", ["globe.li", "app.builder.markets", "ide.finance", "tr8.wtf",
                     "prism.predi.cc", "question.markets"]),
    ("INNOVATION", ["rfq.fi", "parlays.live", "parlayer.xyz", "hyperhedge",
                    "composites", "ide.finance", "globe.li"]),
    # real rows rather than one dim line - these layers exist, they are just
    # not enumerated here
    ("AUTOMATION", ["fleet", "predator-bots", "legion", "…"]),
    ("INTELLIGENCE", ["everex.pro", "quants.run", "prism.predi.cc", "…"]),
    ("PRODUCTIVITY", ["pro.", "laptime.dev", "this.poc.rocks", "…"]),
]
TEASED = {"AUTOMATION", "INTELLIGENCE", "PRODUCTIVITY"}


def stack(c):
    """Rows wrap: the integrations row is twenty chips and will not fit on one
    line, so each row grows by however many lines it needs and the rows below
    shift down. Row heights are measured first, then drawn."""
    W, LEFT, RIGHT = 1200, 254, 1160
    CHIP_H, LINE_H, PAD_TOP, GAP = 34, 44, 46, 13

    def chip_w(t):
        return 17 + len(t) * 8.5

    # measure: how many lines does each row need?
    layout, y = [], PAD_TOP
    for name, items in LAYERS:
        bx, lines = LEFT, 1
        placed = []
        for it in items:
            if it == "\u2192":
                placed.append(("arrow", bx, lines - 1))
                bx += 30
                continue
            w = chip_w(it)
            if bx + w > RIGHT:                    # wrap
                lines += 1
                bx = LEFT
            placed.append((it, bx, lines - 1))
            bx += w + GAP
        h = LINE_H * lines + 22
        layout.append((name, placed, y, h, lines))
        y += h
    H = y + 10

    out = []
    for li, (name, placed, y, h, lines) in enumerate(layout):
        d = 0.3 + li * 0.13
        lop = ' opacity=".55"' if name in TEASED else ''
        out.append(f'<text x="44" y="{y+26}" class="layer"{lop}>{esc(name)}</text>')
        if li:
            out.append(f'<rect x="44" y="{y-12}" width="{W-88}" height="1" fill="{c["frame"]}" '
                       f'shape-rendering="crispEdges" class="fade-in"/>')
        derived = False
        for it, bx, line in placed:
            ly = y + 6 + LINE_H * line
            if it == "arrow":
                out.append(f'<text x="{bx+9:.0f}" y="{ly+22}" class="arrow">&#8594;</text>')
                derived = True
                continue
            w = chip_w(it)
            teased = name in TEASED
            accent = (name == "INNOVATION") and not derived
            fill = c["panel"] if not accent else c["accent"]
            txt = c["text"] if not accent else ("#04070f" if c is DARK else "#ffffff")
            stroke = c["frame"] if not accent else c["accent"]
            out.append(f"""
  <g style="animation:rise .9s cubic-bezier(.16,1,.3,1) {d:.2f}s both" class="needs-motion">
    <rect x="{bx:.0f}" y="{ly}" width="{w:.0f}" height="{CHIP_H}" rx="6" fill="{fill}" stroke="{stroke}"
          opacity="{0.42 if teased else 1}"/>
    <text x="{bx + w/2:.0f}" y="{ly+22}" text-anchor="middle" class="chip" fill="{txt}"
          opacity="{0.55 if teased else 1}">{esc(it)}</text>
  </g>""")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="{esc('The stack: ' + '; '.join(n + ': ' + ', '.join(i) for n, i in LAYERS))}">
  <style>
    .layer{{ font-family:{MONO}; font-size:12px; letter-spacing:2.8px; fill:{c['faint']} }}
    .chip {{ font-family:{MONO}; font-size:13.5px; letter-spacing:.4px }}
    .arrow{{ font-family:{MONO}; font-size:15px; fill:{c['accent']} }}
    .faded{{ font-family:{MONO}; font-size:12px; letter-spacing:2.4px; fill:{c['faint']}; opacity:.5 }}
    .title{{ font-family:{MONO}; font-size:12px; letter-spacing:3.2px; fill:{c['faint']} }}
    .fade-in {{ animation:fade 1.2s ease .3s both }}
    {BASE_KEYFRAMES}{REDUCED}
  </style>
{frame(c, W, H, 12.5)}
{''.join(out)}
</svg>
"""



BUILDERS = {"header": header, "stats": stats, "stack": stack}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILDERS.items():
        for theme, pal in (("dark", DARK), ("light", LIGHT)):
            path = os.path.join(OUT, f"{name}-{theme}.svg")
            svg = fn(pal)
            import xml.dom.minidom
            try:
                xml.dom.minidom.parseString(svg)      # never ship a broken SVG
            except Exception as e:
                raise SystemExit(f"{name}-{theme}: malformed XML -> {e}")
            with open(path, "w") as f:
                f.write(svg)
            print(f"  {os.path.relpath(path, os.path.dirname(OUT))}  {os.path.getsize(path):,} bytes")
    print("done")
