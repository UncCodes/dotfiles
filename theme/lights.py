"""More backdrops in the ribbon's family: light drawn as fine line work over the haze.

Each one shares the ribbon's ground (theme/ribbon.py: a haze lit from one side, the shell's
colour glowing through it, faint disc rings and column rules) and draws its own figure on it:

  helix   two sheaves of light braided around each other, the near strand bright, the far one
          dim, faint rungs between them; the braid turns and a glint runs along it
  orbit   a gyroscope of tilted rings, each a sheaf of fine ellipses, precessing slowly round
          a soft core; a bead of light travels every ring
  fibre   a fibre-optic lamp: strands rising from below the screen, fanning out and bowing
          under their own weight, each tip a point of light; they sway, the tips breathe
  mesh    a wireframe landscape in perspective, rows of light rolling in from the horizon,
          the near rows bright, the far ones fading into the haze
  veil    curtains of light hanging in a night sky: fine threads from a rippling hem, the signal
          at the top fading into the counter colour below, swaying; a few stars

Every figure is lines(t) (polylines with an opacity and a width) and points(t) (glowing
dots); the base class draws them supersampled with a soft bloom, and writes them as SVG for the
start page. Every motion turns a whole number of times in LOOP, so the live loop is seamless.
No text, ever.
"""
import math

try:                                    # the drawing needs Pillow; the start page's line work (svg) does not
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    Image = ImageDraw = ImageFilter = None

from ribbon import LOOP, RibbonScene, bloom, mixc

TAU = 2 * math.pi
WHITE = (255, 255, 255)


def _seed(mode, salt):
    return (sum(map(ord, mode)) * 7 + salt) % 97


class LightScene(RibbonScene):
    """The ribbon's ground and colours; a figure of lines and points instead of the ribbon."""
    name = "light"

    def __init__(self, mode, W, H, tier="lcd"):
        self.seed = _seed(mode, len(self.name))
        super().__init__(mode, W, H, tier)

    # the figure: [(points, alpha, width)] in screen pixels, and [(x, y, radius, alpha)]
    def lines(self, t):
        return []

    def points(self, t):
        return []

    def _routes(self):
        """Routes for the boot splash's traces: the brightest lines, as they stand at t = 0."""
        ls = sorted(self.lines(0.0), key=lambda l: -l[1])[:5]
        return [(item[0][::3], False, (n * 3) % 8, (n * 7) % 10) for n, item in enumerate(ls)]

    def ribbon(self, img, t):                     # draws the figure where the ribbon drew its sheaf
        W, H = self.W, self.H
        s = 2
        layer = Image.new("RGBA", (W * s, H * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        dim = 1.0 if self.dark else 0.9
        for pts, a, w, *colour in self.lines(t):     # an optional fourth item: the line's own colour
            if a <= 0.01 or len(pts) < 2:
                continue
            d.line([(x * s, y * s) for x, y in pts], fill=(*(colour[0] if colour else self.line), round(255 * min(1.0, a * dim))),
                   width=max(1, round(s * w)))
        layer = layer.reduce(s)                        # 2x supersampled down to the screen: a box filter is enough
        img.alpha_composite(bloom(layer, H))
        img.alpha_composite(layer)
        self.dots(img, self.points(t))

    def dots(self, img, pts):
        """Points of light: a bright core in a soft halo."""
        if not pts:
            return
        W, H = self.W, self.H
        halo = Image.new("L", (W // 4, H // 4), 0)
        core = Image.new("L", (W * 2, H * 2), 0)
        dh, dc = ImageDraw.Draw(halo), ImageDraw.Draw(core)
        for x, y, r, a in pts:
            R = r * 3.2 / 4
            dh.ellipse((x / 4 - R, y / 4 - R, x / 4 + R, y / 4 + R), fill=round(255 * a * 0.5))
            dc.ellipse((x * 2 - r * 2, y * 2 - r * 2, x * 2 + r * 2, y * 2 + r * 2), fill=round(255 * a))
        halo = halo.filter(ImageFilter.GaussianBlur(max(1, H // 400))).resize((W, H), Image.BILINEAR)
        core = core.reduce(2)
        glow = mixc(self.hi, WHITE, 0.25 if self.dark else 0.0)
        for mask, colour, k in ((halo, glow, 0.8 if self.dark else 0.35), (core, mixc(self.hi, WHITE, 0.6 if self.dark else 0.15), 1.0)):
            lit = Image.new("RGBA", (W, H), (*colour, 0))
            lit.putalpha(mask.point(lambda v, k=k: round(v * k)))
            img.alpha_composite(lit)

    def glint(self, img, t):                      # the figures carry their own points of light
        return None


def _chunks(pts, alphas, n=6):
    """A polyline cut into runs of n segments, each with the mean opacity of its points, so a
    line can fade along its length (Pillow draws one colour per call)."""
    out = []
    for i in range(0, len(pts) - 1, n):
        seg = pts[i:i + n + 1]
        if len(seg) > 1:
            out.append((seg, sum(alphas[i:i + n + 1]) / len(alphas[i:i + n + 1])))
    return out


class HelixScene(LightScene):
    name = "helix"
    STRAND = 9

    def lines(self, t):
        W, H = self.W, self.H
        w = TAU * t / LOOP
        a, b = self.seed * 0.21, self.seed * 0.53
        step = max(6, W // 240)
        xs = list(range(-step, W + 2 * step, step))
        out = []
        cols = []
        for x in xs:
            u = x / W
            mid = (0.54 + 0.07 * math.sin(TAU * 0.55 * u + a + w)) * H
            phase = TAU * 1.5 * u + b - 2 * w
            amp = (0.10 + 0.03 * math.sin(TAU * 0.8 * u + a - w)) * H
            cols.append((mid, math.sin(phase) * amp, math.cos(phase)))
        for strand in (1, -1):
            for i in range(self.STRAND):
                k = (i - (self.STRAND - 1) / 2) / ((self.STRAND - 1) / 2)
                pts, al = [], []
                for x, (mid, off, depth) in zip(xs, cols):
                    near = 0.5 + 0.5 * depth * strand            # 1 in front, 0 behind
                    pts.append((x, mid + strand * off + k * H * (0.010 + 0.016 * near)))
                    al.append((0.12 + 0.50 * near ** 1.5) * (1 - 0.55 * abs(k)))
                out += [(seg, al_, 1.25 - 0.5 * abs(k)) for seg, al_ in _chunks(pts, al)]
        # rungs: faint ties between the strands
        for j in range(0, len(xs), 5):
            x = xs[j]
            mid, off, depth = cols[j]
            out.append(([(x, mid - abs(off) + 0.012 * H), (x, mid + abs(off) - 0.012 * H)], 0.10, 1.0))
        return out

    def points(self, t):
        W, H = self.W, self.H
        out = []
        for n, period in enumerate((14.0, 28.0 / 3)):           # 4 and 6 crossings a loop
            u = ((t / period + n * 0.5) % 1.0)
            x = -0.05 * W + 1.1 * W * u
            w = TAU * t / LOOP
            a, b = self.seed * 0.21, self.seed * 0.53
            ux = x / W
            mid = (0.54 + 0.07 * math.sin(TAU * 0.55 * ux + a + w)) * H
            phase = TAU * 1.5 * ux + b - 2 * w
            amp = (0.10 + 0.03 * math.sin(TAU * 0.8 * ux + a - w)) * H
            strand = 1 if n == 0 else -1
            near = 0.5 + 0.5 * math.cos(phase) * strand
            out.append((x, mid + strand * math.sin(phase) * amp, H * 0.006, 0.35 + 0.6 * near))
        return out


class OrbitScene(LightScene):
    name = "orbit"
    # radius, tilt (deg), turns a loop: a gyroscope's gimbals, nested, each on its own axis
    RINGS = ((1.00, 76, 1), (0.88, 62, -1), (1.12, 82, 1), (0.74, 48, -1), (1.24, 70, -1), (0.60, 30, 1))
    SHEAF = 7

    def _centre(self):
        return self.W * (0.66 + 0.04 * math.sin(self.seed)), self.H * 0.52, self.H * 0.33

    def _ring(self, n, t, theta, k=0.0):
        cx, cy, R = self._centre()
        r, tilt, turns = self.RINGS[n]
        r = R * r * (1 + 0.009 * k)
        phi = self.seed * 0.4 + n * 1.1 + TAU * turns * t / LOOP     # the ring's precession
        ci = math.cos(math.radians(tilt))
        x, y = r * math.cos(theta), r * math.sin(theta) * ci
        return (cx + x * math.cos(phi) - y * math.sin(phi), cy + x * math.sin(phi) + y * math.cos(phi),
                math.sin(theta))                                       # depth: > 0 in front

    def lines(self, t):
        out = []
        steps = 128
        for n in range(len(self.RINGS)):
            for i in range(self.SHEAF):
                k = i - (self.SHEAF - 1) / 2
                pts, al = [], []
                for j in range(steps + 1):
                    x, y, depth = self._ring(n, t, TAU * j / steps, k)
                    pts.append((x, y))
                    al.append((0.06 + 0.40 * (0.5 + 0.5 * depth) ** 1.6) * (1 - 0.11 * abs(k)))
                out += [(seg, a, 1.1 - 0.1 * abs(k)) for seg, a in _chunks(pts, al, 16)]
        # spokes: faint radial ticks round the outer ring, a dial's scale
        cx, cy, R = self._centre()
        for j in range(48):
            th = TAU * j / 48 + TAU * t / LOOP
            r0, r1 = R * 1.42, R * (1.47 if j % 4 else 1.53)
            out.append(([(cx + r0 * math.cos(th), cy + r0 * math.sin(th)), (cx + r1 * math.cos(th), cy + r1 * math.sin(th))],
                        0.16 if j % 4 else 0.26, 1.0))
        return out

    def points(self, t):
        out = []
        for n, (_, _, turns) in enumerate(self.RINGS):
            theta = self.seed + n * 2.0 + TAU * (abs(turns) + 2) * t / LOOP
            x, y, depth = self._ring(n, t, theta)
            out.append((x, y, self.H * 0.0045, 0.25 + 0.6 * (0.5 + 0.5 * depth)))
        return out


class FibreScene(LightScene):
    name = "fibre"
    STRANDS = 56

    def _strand(self, j, t):
        W, H = self.W, self.H
        bx, by = W * (0.30 + 0.08 * math.sin(self.seed)), H * 1.06
        f = j / (self.STRANDS - 1)
        g = (self.seed * 0.618 + j * 0.381966) % 1.0                  # a scatter, the same every run
        ang = math.radians(-74 + 148 * f + 6 * (g - 0.5))
        sway = 0.045 * math.sin(TAU * (1 + j % 3) * t / LOOP + g * TAU)
        ang += sway
        L = H * (0.62 + 0.38 * (1 - abs(f - 0.5) * 1.6) * (0.7 + 0.3 * g))
        droop = 0.55 * math.sin(ang) ** 2
        pts = []
        for i in range(25):
            s = i / 24
            x = bx + math.sin(ang) * L * s * (1 + 0.25 * droop * s)
            y = by - math.cos(ang) * L * s + droop * L * s * s * 0.55
            pts.append((x, y))
        return pts, g

    def lines(self, t):
        out = []
        for j in range(self.STRANDS):
            pts, g = self._strand(j, t)
            al = [0.03 + 0.32 * (i / (len(pts) - 1)) ** 1.8 for i in range(len(pts))]
            out += [(seg, a, 1.0) for seg, a in _chunks(pts, al, 4)]
        return out

    def points(self, t):
        out = []
        for j in range(self.STRANDS):
            pts, g = self._strand(j, t)
            breath = 0.5 + 0.5 * math.sin(TAU * 2 * t / LOOP + g * TAU * 3)   # the tips breathe, out of step
            x, y = pts[-1]
            out.append((x, y, self.H * (0.0028 + 0.0018 * breath), 0.45 + 0.5 * breath))
        return out


class MeshScene(LightScene):
    name = "mesh"
    ROWS = 34
    COLS = 46

    def _height(self, X, Z, t):
        w = TAU * t / LOOP
        a = self.seed * 0.3
        return (0.55 * math.sin(0.9 * X + a + w) * math.cos(0.45 * Z - 2 * w)
                + 0.30 * math.sin(0.35 * X - 0.8 * Z + 2 * w + a)
                + 0.18 * math.cos(1.7 * X + 0.3 * Z - 3 * w))

    def _project(self, X, Z, t):
        W, H = self.W, self.H
        horizon, cam, focal = H * 0.40, 2.2, H * 0.55
        h = self._height(X, Z, t)
        return W / 2 + X * focal / Z, horizon + (cam - h) * focal / Z

    def _z(self, r, t):
        """Row r's depth: rows roll toward the viewer and wrap, one row spacing every 7 s."""
        roll = (t / 7.0) % 1.0
        return 1.4 + (r + 1 - roll) * 0.62

    def lines(self, t):
        out = []
        zfar = self._z(self.ROWS - 1, 0.0)
        xs = [(-1 + 2 * c / (self.COLS * 4 - 1)) * 14 for c in range(self.COLS * 4)]   # rows: fine steps
        grid = []
        for r in range(self.ROWS):
            Z = self._z(r, t)
            fade = (1 - (Z - 1.4) / (zfar - 1.4)) ** 1.6                 # bright near, gone at the horizon
            near = min(1.0, (Z - 1.4) / 0.9)                              # a row arriving fades in
            row = [self._project(X, Z, t) for X in xs]
            grid.append((row, fade * near))
            out.append((row, 0.06 + 0.46 * fade * near, 1.3 if fade > 0.6 else 1.0))
        for c in range(0, self.COLS * 4, 8):                              # the long lines, every other column
            pts = [grid[r][0][c] for r in range(self.ROWS)]
            al = [0.04 + 0.22 * grid[r][1] for r in range(self.ROWS)]
            out += [(seg, a, 1.0) for seg, a in _chunks(pts, al, 3)]
        return out

    def points(self, t):
        out = []
        for n in range(3):                                                # beacons riding the swell
            X = (-6 + 6 * n) + 0.6 * math.sin(self.seed + n)
            Z = self._z(4 + n * 3, t)
            x, y = self._project(X, Z, t)
            out.append((x, y - self.H * 0.012, self.H * 0.005, 0.7))
        return out


class VeilScene(LightScene):
    name = "veil"
    THREADS = 200

    def _tint(self):
        from palette import E
        p = E(self.mode)
        rgb = lambda c: tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        return rgb(p["signal_hi"]), rgb(p["counter"])

    def _hem(self, u, t, fold):
        """The curtain's top edge at u (0..1 across): a slow, deep ripple, each fold its own."""
        w = TAU * t / LOOP
        a = self.seed * 0.2 + fold * 1.9
        return self.H * (0.16 + 0.10 * math.sin(TAU * 0.9 * u + a + w) + 0.05 * math.sin(TAU * 2.3 * u - a + 2 * w)
                         + 0.04 * fold)

    def _length(self, u, t, fold):
        w = TAU * t / LOOP
        return self.H * (0.30 + 0.20 * (0.5 + 0.5 * math.sin(TAU * 1.6 * u + self.seed + fold - w)))

    def lines(self, t):
        W = self.W
        w = TAU * t / LOOP
        top, low = self._tint()
        out = []
        for j in range(self.THREADS):
            g = (self.seed * 0.618 + j * 0.381966) % 1.0
            fold = j % 3                                                      # three curtains, one behind another
            u = (j + 0.5) / self.THREADS
            hem, length = self._hem(u, t, fold), self._length(u, t, fold)
            x0 = W * (-0.05 + 1.1 * u)
            sway = W * 0.010 * (1 + fold)
            bright = (0.62 - 0.16 * fold) * (0.55 + 0.45 * g)
            pts, al = [], []
            for i in range(15):
                k = i / 14
                x = x0 + sway * k * k * math.sin(w * (1 + fold) + TAU * (u * 1.7 + g) + k * 2.0)
                pts.append((x, hem + length * k))
                al.append(bright * (0.25 + 0.75 * math.sin(math.pi * min(1, k * 1.25))) * (1 - k) ** 0.8)
            for n, (seg, a) in enumerate(_chunks(pts, al, 3)):
                f = min(1.0, n / 4)
                c = tuple(round(top[i] + (low[i] - top[i]) * f) for i in range(3))
                out.append((seg, a, 1.0, c))
        return out

    def ribbon(self, img, t):
        """A soft glow behind the curtains (drawn small and blurred: cheap), then the threads."""
        W, H = self.W, self.H
        top, low = self._tint()
        q = 6
        glow = Image.new("RGBA", (W // q, H // q), (0, 0, 0, 0))
        d = ImageDraw.Draw(glow)
        for fold in range(3):
            n = 48
            hems = [(W * (-0.05 + 1.1 * i / n) / q, self._hem(i / n, t, fold) / q) for i in range(n + 1)]
            feet = [(x, y + self._length(i / n, t, fold) * 0.8 / q) for i, (x, y) in enumerate(hems)]
            a = (70, 46, 30)[fold] if self.dark else (60, 40, 26)[fold]
            d.polygon(hems + feet[::-1], fill=(*top, a))
            d.polygon([(x, y + (fy - y) * 0.45) for (x, y), (_, fy) in zip(hems, feet)] + feet[::-1], fill=(*low, a // 2))
        glow = glow.filter(ImageFilter.GaussianBlur(max(2, H // q // 30))).resize((W, H), Image.BILINEAR)
        img.alpha_composite(glow)
        super().ribbon(img, t)

    def points(self, t):
        W, H = self.W, self.H
        out = []
        for n in range(30):                                                   # stars, each breathing out of step
            g = (self.seed * 0.73 + n * 0.618034) % 1.0
            h = (self.seed * 0.29 + n * 0.754877) % 1.0
            breath = 0.5 + 0.5 * math.sin(TAU * (1 + n % 3) * t / LOOP + g * TAU)
            out.append((W * g, H * (0.03 + 0.92 * h), H * (0.0011 + 0.0009 * breath), 0.20 + 0.45 * breath))
        return out


SCENES = {"helix": HelixScene, "orbit": OrbitScene, "fibre": FibreScene, "mesh": MeshScene, "veil": VeilScene}


def svg(name, mode, W=1000, H=700):
    """A figure as line work for the start page (as it stands at t = 0)."""
    sc = SCENES[name].__new__(SCENES[name])
    sc.mode, sc.W, sc.H, sc.seed = mode, W, H, _seed(mode, len(name))
    paths = []
    for pts, a, w, *_ in sc.lines(0.0):
        if a > 0.02:
            d = "M" + "L".join(f"{x:.0f} {y:.1f}" for x, y in pts)
            paths.append(f'<path d="{d}" stroke-opacity="{min(1, a * 1.2):.2f}" stroke-width="{w:.2f}"/>')
    dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{max(1.5, r):.1f}" fill="currentColor" fill-opacity="{a:.2f}" stroke="none"/>'
                   for x, y, r, a in sc.points(0.0))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
            f'fill="none" stroke="currentColor">{"".join(paths)}{dots}</svg>')
