#!/usr/bin/env python3
"""Draw the HUD wallpaper: void black, generous empty space, sparse FUI micro-geometry.

No text. A faint atmospheric glow sits behind the radar so the frosted windows
have something to blur; everything else is near-black with hairline detail:
dot matrices, micro-square clusters, crosshair reticles, tick rulers and
L-shaped corner brackets. Colours are "muted neon": ice cyan, steel blue,
one dim amber mark.

Usage:
  python3 theme/make-wallpaper.py [out.png] [width] [height]          dark still
  python3 theme/make-wallpaper.py --mode light [out.png] [w] [h]      light still
  python3 theme/make-wallpaper.py --live [--mode M] out.mp4 [w] [h]   live loop

--live adds the portfolio's background on top of the still: a fine 24 px grid drifting
diagonally (96 px every 20 s, as in the portfolio's CSS), plus a slow radar sweep and one
blinking status mark. The 20 s loop is seamless. Frames are piped to ffmpeg.
Needs Pillow (and ffmpeg for --live).
"""
import math
import random
import subprocess
import sys
import tomllib
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

args = sys.argv[1:]
LIVE = "--live" in args
MODE = "dark"
if "--mode" in args:
    MODE = args[args.index("--mode") + 1]
    del args[args.index("--mode"):args.index("--mode") + 2]
args = [a for a in args if a != "--live"]
HYPR = Path(__file__).resolve().parent.parent / "hypr/.config/hypr"
OUT = Path(args[0]) if args else HYPR / ("wallpaper-light.png" if MODE == "light" else "wallpaper.png")
W = int(args[1]) if len(args) > 1 else 2560
H = int(args[2]) if len(args) > 2 else 1440
S = 2  # supersample for clean 1px lines
w, h = W * S, H * S

_all = tomllib.loads((Path(__file__).resolve().parent / "tokens.toml").read_text())
_tok = {**_all["color"], **(_all.get("light", {}).get("color", {}) if MODE == "light" else {})}
_rgb = lambda k: tuple(int(_tok[k][i:i + 2], 16) for i in (1, 3, 5))
VOID, GREY, ICE, ICE_HI = _rgb("void"), _rgb("fg_dim"), _rgb("ice"), _rgb("ice_hi")
STEEL, DEEP, AMBER = _rgb("steel"), _rgb("ice_dim"), _rgb("amber")

random.seed(11)


def rgba(c, a):
    return (*c, int(255 * a))


def glow(img, cx, cy, rx, ry, colour, alpha, blur):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=rgba(colour, alpha))
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(blur)))


# ── void with a faint atmosphere behind the radar ───────────────────────
img = Image.new("RGBA", (w, h), (*VOID, 255))
rx, ry = w * 0.72, h * 0.42                        # radar centre
img = glow(img, rx, ry, w * 0.22, h * 0.30, STEEL, 0.16, w // 14)
img = glow(img, rx, ry, w * 0.08, h * 0.10, ICE, 0.10, w // 30)
img = glow(img, w * 0.22, h * 0.62, w * 0.16, h * 0.16, DEEP, 0.18, w // 16)

lines = Image.new("RGBA", (w, h), (0, 0, 0, 0))
d = ImageDraw.Draw(lines)

# ── sparse crosshair markers on a 5-cell lattice, instead of a full grid ─
cell = 48 * S
for gx in range(cell * 5, w, cell * 5):
    for gy in range(cell * 3, h, cell * 5):
        a = 0.16 if random.random() > 0.15 else 0.32
        d.line([(gx - 5 * S, gy), (gx + 5 * S, gy)], fill=rgba(GREY, a), width=1)
        d.line([(gx, gy - 5 * S), (gx, gy + 5 * S)], fill=rgba(GREY, a), width=1)

# ── tick rulers along the left and bottom edges ─────────────────────────
for i, y in enumerate(range(int(h * 0.2), int(h * 0.8), 12 * S)):
    L = 10 * S if i % 5 == 0 else 5 * S
    d.line([(36 * S, y), (36 * S + L, y)], fill=rgba(GREY, 0.30 if i % 5 == 0 else 0.15), width=1)
for i, x in enumerate(range(int(w * 0.3), int(w * 0.7), 12 * S)):
    L = 10 * S if i % 5 == 0 else 5 * S
    d.line([(x, h - 36 * S), (x, h - 36 * S - L)], fill=rgba(GREY, 0.30 if i % 5 == 0 else 0.15), width=1)

# ── radar: rings, ticks, sweep arcs, diamond, reticle ───────────────────
R = h * 0.20
for r, a in [(R * 1.20, 0.08), (R, 0.30), (R * 0.78, 0.16), (R * 0.45, 0.10)]:
    d.ellipse((rx - r, ry - r, rx + r, ry + r), outline=rgba(ICE, a), width=S if a > 0.2 else 1)
for deg in range(0, 360, 3):
    t = math.radians(deg)
    major = deg % 30 == 0
    r0 = R * (0.93 if major else 0.965)
    d.line([(rx + r0 * math.cos(t), ry + r0 * math.sin(t)), (rx + R * math.cos(t), ry + R * math.sin(t))],
           fill=rgba(ICE, 0.45 if major else 0.16), width=1)
Ra = R * 1.08
d.arc((rx - Ra, ry - Ra, rx + Ra, ry + Ra), 200, 318, fill=rgba(ICE_HI, 0.60), width=S)
d.arc((rx - Ra, ry - Ra, rx + Ra, ry + Ra), 330, 341, fill=rgba(AMBER, 0.75), width=S)   # the one amber mark
d.line([(rx - R * 1.25, ry), (rx - R * 0.5, ry)], fill=rgba(ICE, 0.14), width=1)
d.line([(rx + R * 0.5, ry), (rx + R * 1.25, ry)], fill=rgba(ICE, 0.14), width=1)
d.line([(rx, ry - R * 1.25), (rx, ry - R * 0.5)], fill=rgba(ICE, 0.14), width=1)
d.line([(rx, ry + R * 0.5), (rx, ry + R * 1.25)], fill=rgba(ICE, 0.14), width=1)
r = h * 0.03
d.polygon([(rx, ry - r), (rx + r, ry), (rx, ry + r), (rx - r, ry)], outline=rgba(ICE, 0.55), width=S)
for sx in (-1, 1):                                   # reticle brackets around the diamond
    for sy in (-1, 1):
        x0, y0 = rx + sx * r * 1.8, ry + sy * r * 1.8
        d.line([(x0, y0), (x0 - sx * r * 0.6, y0)], fill=rgba(ICE, 0.4), width=1)
        d.line([(x0, y0), (x0, y0 - sy * r * 0.6)], fill=rgba(ICE, 0.4), width=1)

# ── dot matrix block (bottom left) ──────────────────────────────────────
ox, oy = w * 0.06, h * 0.70
for row in range(10):
    for col in range(28):
        on = random.random() < 0.55 - row * 0.03
        a = (0.35 if random.random() < 0.08 else 0.16) if on else 0.05
        x, y = ox + col * 9 * S, oy + row * 9 * S
        d.rectangle((x, y, x + 2 * S, y + 2 * S), fill=rgba(ICE, a))

# ── micro-square clusters (near the radar and top left) ─────────────────
def cluster(cx, cy, n, size, colour):
    for _ in range(n):
        gx, gy = random.randint(-6, 6), random.randint(-3, 3)
        x, y = cx + gx * (size + 3 * S), cy + gy * (size + 3 * S)
        filled = random.random() < 0.35
        a = 0.45 if filled else 0.22
        if filled:
            d.rectangle((x, y, x + size, y + size), fill=rgba(colour, a * 0.6))
        d.rectangle((x, y, x + size, y + size), outline=rgba(colour, a), width=1)

cluster(rx + R * 1.45, ry - R * 0.9, 18, 7 * S, ICE)
cluster(rx - R * 1.6, ry + R * 0.9, 12, 7 * S, STEEL)
cluster(w * 0.12, h * 0.18, 10, 6 * S, ICE)

# ── stacked translucent panels drifting back (ref 5), kept faint ────────
for n in range(7):
    px, py = w * 0.10 + n * 30 * S, h * 0.32 + n * 22 * S
    pw, ph = 260 * S, 160 * S
    a = 0.04 + n * 0.012
    d.rectangle((px, py, px + pw, py + ph), fill=rgba(DEEP, a * 0.25), outline=rgba(ICE, a + 0.06), width=1)
    d.rectangle((px, py - 10 * S, px + 70 * S, py), fill=rgba(ICE, a * 0.8))
    for sx, sy in [(px, py + ph), (px + pw, py + ph)]:   # corner ticks
        d.line([(sx - 6 * S, sy), (sx + 6 * S, sy)], fill=rgba(ICE, a + 0.1), width=1)

# ── screen-frame corner brackets ────────────────────────────────────────
m, L, top = 28 * S, 34 * S, 60 * S
for (x, y, sx, sy) in [(m, top, 1, 1), (w - m, top, -1, 1), (m, h - m, 1, -1), (w - m, h - m, -1, -1)]:
    d.line([(x, y), (x + sx * L, y)], fill=rgba(ICE, 0.50), width=S)
    d.line([(x, y), (x, y + sy * L)], fill=rgba(ICE, 0.50), width=S)
    d.rectangle((x + sx * 6 * S - S, y + sy * 6 * S - S, x + sx * 6 * S + S, y + sy * 6 * S + S), fill=rgba(ICE, 0.5))

# faint emissive bloom on the line work, then the sharp lines on top
bloom = lines.filter(ImageFilter.GaussianBlur(5 * S))
img = Image.alpha_composite(img, bloom)
img = Image.alpha_composite(img, lines)

img = img.convert("RGB").resize((W, H), Image.LANCZOS)
noise = Image.effect_noise((W, H), 14).convert("RGB")
img = ImageChops.add(img, Image.blend(Image.new("RGB", (W, H)), noise, 0.03))

OUT.parent.mkdir(parents=True, exist_ok=True)
if not LIVE:
    img.save(OUT, optimize=True)
    print(f"wrote {OUT} ({W}x{H})")
    sys.exit(0)


# ── live loop ───────────────────────────────────────────────────────────
FPS, SECONDS = 24, 20
CELL, DRIFT = 24, 96                       # the portfolio's grid: 24 px cells, -96 px per 20 s
base = img.convert("RGBA")

# grid layer, a little larger than the screen so it can slide. Transparent pixels carry the
# line colour so bilinear sampling fades alpha only (sub-pixel motion without dark fringes).
grid_rgb = STEEL if MODE == "light" else ICE
grid_a = 0.10 if MODE == "light" else 0.075
grid = Image.new("RGBA", (W + 2 * CELL, H + 2 * CELL), (*grid_rgb, 0))
gd = ImageDraw.Draw(grid)
for x in range(0, grid.width, CELL):
    gd.line([(x, 0), (x, grid.height)], fill=rgba(grid_rgb, grid_a))
for y in range(0, grid.height, CELL):
    gd.line([(0, y), (grid.width, y)], fill=rgba(grid_rgb, grid_a))

# radar sweep: a lit leading edge with a fading wedge behind it, drawn once at 2x,
# then rotated per frame
cx, cy, Rr = W * 0.72, H * 0.42, H * 0.20
half = int(Rr * 1.02) + 2
sw = Image.new("RGBA", (4 * half, 4 * half), (0, 0, 0, 0))
sd = ImageDraw.Draw(sw)
c2, R2 = 2 * half, 2 * Rr
TRAIL = 48
for i in range(TRAIL):                          # 48 one-degree slices, fading out behind the edge
    a = 0.16 * (1 - i / TRAIL) ** 2
    sd.pieslice((c2 - R2, c2 - R2, c2 + R2, c2 + R2), -i - 1, -i, fill=rgba(ICE, a))
sd.line([(c2, c2), (c2 + R2, c2)], fill=rgba(ICE_HI, 0.55), width=2)
sweep = sw.resize((2 * half, 2 * half), Image.LANCZOS)
sx, sy = int(cx) - half, int(cy) - half

# blinking status mark (the portfolio's 2 s blink) on the top-right corner bracket
bm = 28
bx, by = W - bm - 6, 60 + 6

ff = subprocess.Popen(
    ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
     "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-tune", "animation",
     "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)],
    stdin=subprocess.PIPE)
for n in range(FPS * SECONDS):
    t = n / FPS
    o = (DRIFT * t / SECONDS) % CELL                 # grid slides up-left, wraps every cell
    frame = base.copy()
    frame.alpha_composite(grid.transform((W, H), Image.AFFINE, (1, 0, o, 0, 1, o), resample=Image.BILINEAR))
    angle = 360 * t / SECONDS                        # one turn per loop, clockwise
    frame.alpha_composite(sweep.rotate(-angle, resample=Image.BICUBIC), dest=(sx, sy))
    if t % 2 < 1:
        ImageDraw.Draw(frame).rectangle((bx - 2, by - 2, bx + 2, by + 2), fill=rgba(ICE_HI, 0.85))
    ff.stdin.write(frame.convert("RGB").tobytes())
ff.stdin.close()
sys.exit(ff.wait())
