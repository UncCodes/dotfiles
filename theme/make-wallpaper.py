#!/usr/bin/env python3
"""Draw the fui backdrop for the edition's look: the survey field (instrument) or the ribbon
of light (y2k, theme/ribbon.py).

The instrument backdrop is described below.

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
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from survey import OPACITY, WIDTH, length, survey, walk  # noqa: E402
from palette import EDS, LOOK, E, T, edition, is_dark, look_of  # noqa: E402
from ribbon import RibbonScene  # noqa: E402

HYPR = HERE.parent / "hypr/.config/hypr"

TRACE = 90.0                                           # view-box units of lit contour behind a head
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


def Scene(mode, W, H, tier="lcd"):
    """The edition's backdrop: its look names it (tokens.toml [look.*] backdrop)."""
    if LOOK.get(look_of(mode), {}).get("backdrop") == "ribbon":
        return RibbonScene(mode, W, H, tier)
    return SurveyScene(mode, W, H, tier)


class SurveyScene:
    def __init__(self, mode, W, H, tier="lcd"):
        c = E(mode)
        self.W, self.H = W, H
        self.ground = rgba(ground(mode, tier))[:3]
        self.arc, self.bead, self.packet = rgba(c["arc"]), rgba(c["bead"]), rgba(c["packet"])
        self.art = survey(mode)
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
        """(view points, closed, duration s, phase) for every trace."""
        return [(pts, closed, SPEEDS[v], p / 10) for pts, closed, v, p in self.art["packets"]]

    def trace(self, img, route, t):
        """Draw one trace at time t: a lit stretch of contour, brightest at its head."""
        pts, closed, dur, ph = route
        L = length(pts)
        head = ((t / dur + ph) % 1.0) * L
        n, samples = 14, []
        for i in range(n + 1):
            s = head - TRACE * (1 - i / n)
            if closed:
                s %= L
            elif s < 0:
                continue
            samples.append((i / n, self.xy(*walk(pts, s / L))))
        if len(samples) < 2:
            return
        vis = 1.0 if closed else max(0.0, min(1.0, head / L / 0.08, (1 - head / L) / 0.08))
        hx_, hy_ = samples[-1][1]
        vis *= fade(hy_, self.H)
        if vis <= 0.02:
            return
        xs = [p[0] for _, p in samples]
        ys = [p[1] for _, p in samples]
        pad = 4
        x0, y0 = int(min(xs)) - pad, int(min(ys)) - pad
        x1, y1 = int(max(xs)) + pad + 1, int(max(ys)) + pad + 1
        if x1 <= 0 or y1 <= 0 or x0 >= self.W or y0 >= self.H:
            return
        S = 3                                         # supersampled tile, so the line is smooth
        tile = Image.new("RGBA", ((x1 - x0) * S, (y1 - y0) * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(tile)
        r, g, b, a = self.packet
        for (f0, p0), (f1, p1) in zip(samples, samples[1:]):
            k = f1 ** 1.6                              # fades away behind the head
            d.line([((p0[0] - x0) * S, (p0[1] - y0) * S), ((p1[0] - x0) * S, (p1[1] - y0) * S)],
                   fill=(r, g, b, round(255 * a * vis * k)), width=max(1, round((0.8 + 1.4 * k) * S)))
        tile = tile.resize((x1 - x0, y1 - y0), Image.LANCZOS)
        img.alpha_composite(tile, (x0, y0)) if x0 >= 0 and y0 >= 0 else img.alpha_composite(
            tile.crop((max(0, -x0), max(0, -y0), tile.width, tile.height)), (max(0, x0), max(0, y0)))


def render_still(mode, out, W, H, tier="lcd"):
    scene = Scene(mode, W, H, tier)
    img = scene.still()
    for route in scene.packets():                   # the traces where they stand at t = 0
        scene.trace(img, route, 0.0)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, optimize=True)
    print(f"wrote {out} ({W}x{H}, {mode}, {tier})")


def render_live(mode, out, W, H, seconds=LOOP, fps=24, tier="lcd"):
    W, H = W // 2 * 2, H // 2 * 2
    scene = Scene(mode, W, H, tier)
    base = scene.still()
    routes = scene.packets()
    ff = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-tune", "animation",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    moving = getattr(scene, "frame", None)           # the ribbon draws whole frames
    for n in range(int(seconds * fps)):
        t = n / fps
        if moving:
            frame = moving(t)
        else:
            frame = base.copy()
            for route in routes:
                scene.trace(frame, route, t)
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
