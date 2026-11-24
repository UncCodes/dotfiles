#!/usr/bin/env python3
"""Draw the fui backdrop: the survey field on the edition's ground.

The survey (theme/survey.py: a topographic map of a seeded terrain) is mapped onto the
screen scaled to cover, centred, enlarged 1.1x, fading from the top of the screen to the
bottom: contour lines in the edition's arc colour, every fifth (the index contours) brighter
and strung with survey stations in its bead colour. The live version sends data packets
along the contours in the signal, at eight speeds, each from its own starting point.
No text, ever.

The ground follows the display tier: the floor on lcd; true black (void) outside the panels
on deep and on a tube (the light editions keep their floor, dimmed on crt).

Usage:
  python3 theme/make-wallpaper.py [--edition E] [--tier T] [out.png] [width] [height]
  python3 theme/make-wallpaper.py --live [--edition E] [--tier T] [--seconds N] out.mp4 [width] [height]
  python3 theme/make-wallpaper.py --all     # the fallback still (first edition, lcd) into hypr/.config/hypr/
`fui wallpaper` renders the current edition and tier at the screen's size into ~/.cache/fui.
The live loop is seamless at its default length (56 s, every bead speed divides it).
Needs Pillow (and ffmpeg for --live).
"""
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from survey import OPACITY, WIDTH, survey, walk  # noqa: E402
from palette import EDS, E, T, edition, is_dark  # noqa: E402

HYPR = HERE.parent / "hypr/.config/hypr"

LOOP = 56.0                                            # seconds: every speed below divides it
SPEEDS = [LOOP / k for k in (8, 7, 6, 5, 4, 3, 2, 1)]  # v0..v7: 7 s .. 56 s (the site: 7 .. 28 s)


def rgba(c):
    h = c.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return r, g, b, (int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)


def fade(y, h):
    """The site's mask: opaque at the top, 65% at the middle, 20% at the bottom."""
    t = min(max(y / h, 0.0), 1.0)
    return 1.0 - 0.35 * (t / 0.5) if t <= 0.5 else 0.65 - 0.45 * ((t - 0.5) / 0.5)


def ground(ed, tier):
    """The wallpaper's ground: the floor on lcd; void on deep and crt for dark editions."""
    if tier == "lcd" or not is_dark(ed):
        return T(ed, tier)["floor"]
    return T(ed, tier)["void"]


class Scene:
    def __init__(self, mode, W, H, tier="lcd"):
        c = E(mode)
        self.W, self.H = W, H
        self.ground = rgba(ground(mode, tier))[:3]
        self.arc, self.bead, self.packet = rgba(c["arc"]), rgba(c["bead"]), rgba(c["packet"])
        self.art = survey()
        vw, vh = self.art["view"]
        self.s = max(W / vw, H / vh) * 1.1            # cover, centred, enlarged 1.1x
        self.ox, self.oy = (W - vw * self.s) / 2, (H - vh * self.s) / 2

    def xy(self, x, y):
        return self.ox + x * self.s, self.oy + y * self.s

    def still(self, S=2):
        """The ground, the contours and the stations, supersampled S times for clean hairlines."""
        W, H, s = self.W * S, self.H * S, self.s * S
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ar, ag, ab, aa = self.arc
        for pts, kind in self.art["lines"]:
            xy = [tuple(v * S for v in self.xy(x, y)) for x, y in pts]
            d.line(xy, fill=(ar, ag, ab, round(255 * aa * OPACITY[kind])), width=max(1, round(WIDTH[kind] * s)),
                   joint="curve")
        br, bg, bb, ba = self.bead
        for x, y, size in self.art["beads"]:
            cx, cy = self.xy(x, y)
            cx, cy, r = cx * S, cy * S, size * s / 2
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(br, bg, bb, round(255 * ba)))
        # the fade from top to bottom, then onto the ground
        mask = Image.new("L", (1, H))
        mask.putdata([round(255 * fade(y / S, self.H)) for y in range(H)])
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask.resize((W, H))))
        base = Image.new("RGBA", (W, H), (*self.ground, 255))
        base.alpha_composite(layer)
        return base.resize((self.W, self.H), Image.LANCZOS)

    def packets(self):
        """(screen points, closed, size px, duration s, phase) for every travelling packet."""
        return [([self.xy(x, y) for x, y in pts], closed, 5 * self.s, SPEEDS[v], p / 10)
                for pts, closed, v, p in self.art["packets"]]

    @staticmethod
    def at(route, t):
        """Where a packet is at time t, and how visible (open contours fade at their ends)."""
        pts, closed, size, dur, ph = route
        u = (t / dur + ph) % 1.0
        x, y = walk(pts, u)
        vis = 1.0 if closed else max(0.0, min(1.0, u / 0.08, (1 - u) / 0.08))
        return x, y, size, vis


def sprite(colour, alpha, size, S=4):
    """A soft-edged dot (antialiased by supersampling)."""
    n = max(2, math.ceil(size)) + 2
    big = Image.new("RGBA", (n * S, n * S), (*colour, 0))
    r = size * S / 2
    c = n * S / 2
    ImageDraw.Draw(big).ellipse((c - r, c - r, c + r, c + r), fill=(*colour, round(255 * alpha)))
    return big.resize((n, n), Image.LANCZOS)


def render_still(mode, out, W, H, tier="lcd"):
    scene = Scene(mode, W, H, tier)
    img = scene.still()
    # the data packets where they stand at t = 0
    br, bg, bb, ba = scene.packet
    for route in scene.packets():
        x, y, size, vis = Scene.at(route, 0.0)
        if vis <= 0:
            continue
        sp = sprite((br, bg, bb), ba * vis * fade(y, H), size)
        px, py = round(x - sp.width / 2), round(y - sp.height / 2)
        if 0 <= px <= W - sp.width and 0 <= py <= H - sp.height:
            img.alpha_composite(sp, (px, py))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, optimize=True)
    print(f"wrote {out} ({W}x{H}, {mode}, {tier})")


def render_live(mode, out, W, H, seconds=LOOP, fps=24, tier="lcd"):
    W, H = W // 2 * 2, H // 2 * 2
    scene = Scene(mode, W, H, tier)
    base = scene.still()
    br, bg, bb, ba = scene.packet
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
        for route in packets:
            x, y, size, vis = Scene.at(route, t)
            level = round(fade(y, H) * vis * LEVELS)
            if level < 1:
                continue
            sp = get(size, level)
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
    mode = edition(opt("--edition", opt("--mode", EDS[0])))
    tier = opt("--tier", "lcd")
    seconds = float(opt("--seconds", LOOP))
    if every:                        # --all [width] [height]: no output path
        args.insert(0, "")
    W = int(args[1]) if len(args) > 1 else 2560
    H = int(args[2]) if len(args) > 2 else 1440
    if every:
        render_still(EDS[0], HYPR / "wallpaper.png", W, H)
        return 0
    if live:
        if not args:
            print("--live needs an output file", file=sys.stderr)
            return 2
        return render_live(mode, Path(args[0]), W, H, seconds, tier=tier)
    render_still(mode, Path(args[0]) if args else HYPR / f"wallpaper-{mode}-{tier}.png", W, H, tier)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
