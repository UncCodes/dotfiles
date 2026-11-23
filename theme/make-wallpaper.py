#!/usr/bin/env python3
"""Draw the fui wallpaper: aljulandani.dev's network lattice on the theme's desk colour.

The lattice (theme/lattice.py, the same drawing as the site) is mapped onto the screen the
way the site's CSS does it: scaled to cover, centred, enlarged 1.1x, and fading from the
top of the screen to the bottom. Lines in the theme's arc colour, bead strings in its bead
colour. The live version adds the site's travelling beads: dots that run along their lines
at eight speeds, each from its own starting point. Old-screen glass (scanlines) is not
baked in: the Hyprland screen shader lays it over everything.

Usage:
  python3 theme/make-wallpaper.py [--mode dark|mid|light] [out.png] [width] [height]
  python3 theme/make-wallpaper.py --live [--mode M] [--seconds N] out.mp4 [width] [height]
  python3 theme/make-wallpaper.py --all          # the three stills into hypr/.config/hypr/
The live loop is seamless at its default length (56 s, every bead speed divides it).
Needs Pillow (and ffmpeg for --live).
"""
import math
import subprocess
import sys
import tomllib
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lattice import OPACITY, SCALE, WIDTH, dash_points, lattice  # noqa: E402

TOK = tomllib.loads((HERE / "tokens.toml").read_text())
HYPR = HERE.parent / "hypr/.config/hypr"

LOOP = 56.0                                            # seconds: every speed below divides it
SPEEDS = [LOOP / k for k in (8, 7, 6, 5, 4, 3, 2, 1)]  # v0..v7: 7 s .. 56 s (the site: 7 .. 28 s)
DEPTH_K = {"f": 0.6, "m": 1.0, "n": 1.6}


def rgba(c):
    h = c.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return r, g, b, (int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)


def fade(y, h):
    """The site's mask: opaque at the top, 65% at the middle, 20% at the bottom."""
    t = min(max(y / h, 0.0), 1.0)
    return 1.0 - 0.35 * (t / 0.5) if t <= 0.5 else 0.65 - 0.45 * ((t - 0.5) / 0.5)


class Scene:
    def __init__(self, mode, W, H):
        c = TOK["mode"][mode]
        self.W, self.H = W, H
        self.ground = rgba(c["bg"])[:3]
        self.arc, self.bead = rgba(c["arc"]), rgba(c["bead"])
        self.art = lattice()
        vw, vh = self.art["view"]
        self.s = max(W / vw, H / vh) * 1.1            # cover, centred, enlarged 1.1x
        self.ox, self.oy = (W - vw * self.s) / 2, (H - vh * self.s) / 2

    def xy(self, x, y):
        return self.ox + x * self.s, self.oy + y * self.s

    def still(self, S=2):
        """The ground, lines and bead strings, supersampled S times for clean hairlines."""
        W, H, s = self.W * S, self.H * S, self.s * S
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ar, ag, ab, aa = self.arc
        for x1, y1, x2, y2, dc in self.art["lines"]:
            p, q = self.xy(x1, y1), self.xy(x2, y2)
            d.line([(p[0] * S, p[1] * S), (q[0] * S, q[1] * S)], fill=(ar, ag, ab, round(255 * aa * OPACITY[dc])),
                   width=max(1, round(0.7 * s)))
        br, bg, bb, ba = self.bead
        for x1, y1, x2, y2, dc, kind, dash in self.art["beads"]:
            r = WIDTH[kind] * SCALE[dc] * s / 2
            a = round(255 * ba * OPACITY[dc])
            for px, py in dash_points(x1, y1, x2, y2, dash):
                cx, cy = self.xy(px, py)
                cx, cy = cx * S, cy * S
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(br, bg, bb, a))
        # the fade from top to bottom, then onto the desk colour
        mask = Image.new("L", (1, H))
        mask.putdata([round(255 * fade(y / S, self.H)) for y in range(H)])
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask.resize((W, H))))
        base = Image.new("RGBA", (W, H), (*self.ground, 255))
        base.alpha_composite(layer)
        return base.resize((self.W, self.H), Image.LANCZOS)

    def packets(self):
        """(x1, y1, x2, y2, size px, duration s, phase) for every travelling bead, in screen pixels."""
        out = []
        for x1, y1, x2, y2, dc, v, p in self.art["packets"]:
            a, b = self.xy(x1, y1), self.xy(x2, y2)
            out.append((a[0], a[1], b[0], b[1], 5 * DEPTH_K[dc] * self.s, SPEEDS[v], p / 10))
        return out


def sprite(colour, alpha, size, S=4):
    """A soft-edged dot (antialiased by supersampling)."""
    n = max(2, math.ceil(size)) + 2
    big = Image.new("RGBA", (n * S, n * S), (*colour, 0))
    r = size * S / 2
    c = n * S / 2
    ImageDraw.Draw(big).ellipse((c - r, c - r, c + r, c + r), fill=(*colour, round(255 * alpha)))
    return big.resize((n, n), Image.LANCZOS)


def render_still(mode, out, W, H):
    scene = Scene(mode, W, H)
    img = scene.still()
    # the travelling beads where they stand at t = 0
    br, bg, bb, ba = scene.bead
    for x1, y1, x2, y2, size, dur, ph in scene.packets():
        t = ph % 1.0
        x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        sp = sprite((br, bg, bb), ba * fade(y, H), size)
        px, py = round(x - sp.width / 2), round(y - sp.height / 2)
        if 0 <= px <= W - sp.width and 0 <= py <= H - sp.height:
            img.alpha_composite(sp, (px, py))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, optimize=True)
    print(f"wrote {out} ({W}x{H}, {mode})")


def render_live(mode, out, W, H, seconds=LOOP, fps=24):
    W, H = W // 2 * 2, H // 2 * 2
    scene = Scene(mode, W, H)
    base = scene.still()
    br, bg, bb, ba = scene.bead
    LEVELS = 24                                     # fade quantised: sprites made once
    cache = {}

    def get(size, level):
        key = (round(size * 4), level)
        if key not in cache:
            cache[key] = sprite((br, bg, bb), ba * level / LEVELS, size)
        return cache[key]

    packets = scene.packets()
    ff = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-tune", "animation",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for n in range(int(seconds * fps)):
        t = n / fps
        frame = base.copy()
        for x1, y1, x2, y2, size, dur, ph in packets:
            u = (t / dur + ph) % 1.0
            x, y = x1 + (x2 - x1) * u, y1 + (y2 - y1) * u
            sp = get(size, max(1, round(fade(y, H) * LEVELS)))
            px, py = round(x - sp.width / 2), round(y - sp.height / 2)
            if 0 <= px <= W - sp.width and 0 <= py <= H - sp.height:
                frame.alpha_composite(sp, (px, py))
        ff.stdin.write(frame.convert("RGB").tobytes())
    ff.stdin.close()
    return ff.wait()


def main(argv):
    args = list(argv)
    flag = lambda name: name in args and not args.remove(name)
    def opt(name, default):
        if name in args:
            i = args.index(name)
            val = args[i + 1]
            del args[i:i + 2]
            return val
        return default
    live, every = flag("--live"), flag("--all")
    mode = opt("--mode", TOK["meta"]["modes"][0])
    seconds = float(opt("--seconds", LOOP))
    if every:                        # --all [width] [height]: no output path
        args.insert(0, "")
    W = int(args[1]) if len(args) > 1 else 2560
    H = int(args[2]) if len(args) > 2 else 1440
    if every:
        for m in TOK["meta"]["modes"]:
            render_still(m, HYPR / f"wallpaper-{m}.png", W, H)
        return 0
    if live:
        if not args:
            print("--live needs an output file", file=sys.stderr)
            return 2
        return render_live(mode, Path(args[0]), W, H, seconds)
    render_still(mode, Path(args[0]) if args else HYPR / f"wallpaper-{mode}.png", W, H)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
