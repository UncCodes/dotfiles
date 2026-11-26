"""A backdrop: a ribbon of light over a haze.

A sheaf of fine lines follows two slow sine fields across the screen, pinching together where
the ribbon crests and fanning apart in its troughs, brightest at its spine (the console menus'
wave). Behind it, a haze lit from one side and a few faint layers of the device itself: disc
rings and the outlines of panels, drawn as translucent technical line work (the late-1990s
sleeve). The moving element is the ribbon: its phases drift, and a glint of light travels along
its spine. No text, ever.

RibbonScene has the same shape as make-wallpaper's survey Scene (still, packets, trace, xy,
art), plus frame(t) for the live loop. The loop is seamless at 56 s: every phase turns a whole
number of times.
"""
import math

try:                                    # the drawing needs Pillow; the start page's line work (svg) does not
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    Image = ImageDraw = ImageFilter = None

from palette import E, T, is_dark

LOOP = 56.0
LINES = 30
SEEDS = {"ice": 3, "chrome": 11, "slate": 17, "ruby": 29}


def rgb(c):
    h = c.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mixc(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


class RibbonScene:
    def __init__(self, mode, W, H, tier="lcd"):
        self.mode, self.W, self.H, self.tier = mode, W, H, tier
        p, pt = E(mode), T(mode, tier)
        self.dark = is_dark(mode)
        self.signal, self.hi, self.shell = rgb(p["signal"]), rgb(p["signal_hi"]), rgb(p["shell"])
        self.ink = rgb(p["ink"])
        seed = SEEDS.get(mode, sum(map(ord, mode)) % 31 + 1)   # every edition its own shape
        self.ph = [(seed * 0.37 + i * 1.3) % (2 * math.pi) for i in range(4)]
        if self.dark:
            ground = rgb(pt["void"] if tier != "lcd" else p["floor"])
            self.top, self.bottom = ground, mixc(ground, self.signal, 0.10)
            self.line = mixc(self.hi, (255, 255, 255), 0.35)
        else:
            self.top = mixc(rgb(p["panel"]), (255, 255, 255), 0.6)
            self.bottom = rgb(pt["floor"])
            self.line = mixc(self.signal, rgb(p["ink"]), 0.15)
        self.view = (W, H)
        self.art = {"packets": self._routes(), "view": (W, H)}
        self._base = None

    def xy(self, x, y):                       # the view is the screen
        return x, y

    # ── the field ──
    def _y(self, x, i, t, layer=0):
        """The height of line i at x and time t (t in seconds; every term is periodic in LOOP)."""
        W, H = self.W, self.H
        u = x / W
        w = 2 * math.pi * t / LOOP
        a, b, c, d = self.ph
        if layer:                                     # the second, fainter ribbon behind
            a, b, c, d, w = a + 2.1, b + 0.9, c + 1.7, d + 2.6, -w
        spine = (0.56 + 0.10 * math.sin(2 * math.pi * 0.9 * u + a + w)
                 + 0.05 * math.sin(2 * math.pi * 2.1 * u + b - 2 * w)) * H
        # the sheaf pinches at the crest and fans in the trough
        spread = (0.035 + 0.085 * (0.5 + 0.5 * math.sin(2 * math.pi * 1.3 * u + c - w))) * H
        k = (i - (LINES - 1) / 2) / ((LINES - 1) / 2)
        twist = 0.35 * math.sin(2 * math.pi * 0.7 * u + d + w)
        return spine + spread * k * (1 + twist * k)

    def _line_pts(self, i, t, step=8, layer=0):
        return [(x, self._y(x, i, t, layer)) for x in range(-step, self.W + 2 * step, step)]

    def _routes(self):
        """Routes for the boot splash's traces: a few ribbon lines, as they stand at t = 0."""
        out = []
        for n, i in enumerate((LINES // 2, LINES // 2 - 4, LINES // 2 + 5, 3, LINES - 4)):
            out.append((self._line_pts(i, 0.0, step=24), False, (n * 3) % 8, (n * 7) % 10))
        return out

    # ── drawing ──
    def ground(self):
        W, H = self.W, self.H
        col = Image.new("RGB", (1, H))
        col.putdata([mixc(self.top, self.bottom, (y / H) ** 1.2) for y in range(H)])
        img = col.resize((W, H)).convert("RGBA")
        # the haze: two soft blooms of the signal's light
        s = 4
        haze = Image.new("L", (W // s, H // s), 0)
        d = ImageDraw.Draw(haze)
        d.ellipse((-W * 0.15 / s, H * 0.25 / s, W * 0.55 / s, H * 1.05 / s), fill=255)
        haze = haze.filter(ImageFilter.GaussianBlur(max(W, H) / 10 / s)).resize((W, H))
        glow = Image.new("RGBA", (W, H), (*self.signal, 0))
        glow.putalpha(haze.point(lambda v: round(v * (0.16 if self.dark else 0.20))))
        img.alpha_composite(glow)
        # ...and one of the shell's colour, top right: the chassis glowing through the haze
        sh = Image.new("L", (W // s, H // s), 0)
        ImageDraw.Draw(sh).ellipse((W * 0.55 / s, -H * 0.45 / s, W * 1.25 / s, H * 0.40 / s), fill=255)
        sh = sh.filter(ImageFilter.GaussianBlur(max(W, H) / 9 / s)).resize((W, H))
        tint = Image.new("RGBA", (W, H), (*self.shell, 0))
        tint.putalpha(sh.point(lambda v: round(v * (0.30 if self.dark else 0.35))))
        img.alpha_composite(tint)
        # the device's own parts, as faint line work: disc rings, and hairline column rules each
        # topped with a dot counter (2, 4, 7: the column's index, as on the late-1990s sleeve)
        lw = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(lw)
        ln = (*self.line, 22 if self.dark else 30)
        cx, cy, R = W * 1.56, H * 0.62, H * 0.62
        for k in range(7):
            r = R * (0.32 + k * 0.11)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ln, width=2)
        dot = (*self.line, 60 if self.dark else 70)
        for n, (xf, count) in enumerate(((0.18, 2), (0.40, 4), (0.62, 7))):
            x = xf * W * 2
            d.line([(x, H * 0.10 * 2), (x, H * 0.44 * 2)], fill=ln, width=2)
            for j in range(count):
                cxd = x - (count - 1) * H * 0.006 + j * H * 0.012
                rr = H * 0.0028
                d.ellipse((cxd - rr, H * 0.08 * 2 - rr, cxd + rr, H * 0.08 * 2 + rr), fill=dot)
        img.alpha_composite(lw.resize((W, H), Image.LANCZOS))
        return img

    def ribbon(self, img, t):
        W, H = self.W, self.H
        s = 2
        layer = Image.new("RGBA", (W * s, H * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        mid = (LINES - 1) / 2
        for which, strength in ((1, 0.35), (0, 1.0)):
            for i in range(LINES):
                k = abs(i - mid) / mid                 # brightest at the spine, fading to the edges
                a = strength * ((0.55 if self.dark else 0.50) * (1 - k) ** 1.5 + 0.07)
                pts = [(x * s, y * s) for x, y in self._line_pts(i, t, layer=which)]
                d.line(pts, fill=(*self.line, round(255 * a)), width=max(1, round(s * (1.3 - 0.6 * k))))
        layer = layer.resize((W, H), Image.LANCZOS)
        # a soft bloom under the spine
        bloom = layer.filter(ImageFilter.GaussianBlur(max(2, H // 90)))
        img.alpha_composite(bloom)
        img.alpha_composite(layer)
        self.glint(img, t)

    def glint(self, img, t):
        """A point of light travelling the spine, once every 14 s."""
        W, H = self.W, self.H
        u = ((t / 14.0) % 1.0)
        x = -0.1 * W + 1.2 * W * u
        y = self._y(x, (LINES - 1) // 2, t)
        r = H * 0.05
        s = 4
        g = Image.new("L", (round(4 * r / s), round(4 * r / s)), 0)
        ImageDraw.Draw(g).ellipse((r / s, r / s, 3 * r / s, 3 * r / s), fill=255)
        g = g.filter(ImageFilter.GaussianBlur(r / s / 2)).resize((round(4 * r), round(4 * r)))
        spot = Image.new("RGBA", g.size, (*mixc(self.hi, (255, 255, 255), 0.6), 0))
        spot.putalpha(g.point(lambda v: round(v * (0.55 if self.dark else 0.40))))
        x0, y0 = round(x - 2 * r), round(y - 2 * r)
        if -g.width < x0 < W and -g.height < y0 < H:
            cx0, cy0 = max(0, -x0), max(0, -y0)
            img.alpha_composite(spot.crop((cx0, cy0, g.width, g.height)), (max(0, x0), max(0, y0)))

    # ── the Scene interface ──
    def still(self, S=2):
        if self._base is None:
            self._base = self.ground()
        img = self._base.copy()
        self.ribbon(img, 0.0)
        return img

    def frame(self, t):
        if self._base is None:
            self._base = self.ground()
        img = self._base.copy()
        self.ribbon(img, t)
        return img

    def packets(self):
        return []                                    # the ribbon moves itself (frame)

    def trace(self, img, route, t):
        return None


def svg(mode, W=1000, H=700):
    """The ribbon as line work for the start page (the lines as they stand at t = 0)."""
    sc = RibbonScene.__new__(RibbonScene)
    sc.W, sc.H = W, H
    sc.ph = [(SEEDS.get(mode, 5) * 0.37 + i * 1.3) % (2 * math.pi) for i in range(4)]
    mid = (LINES - 1) / 2
    paths = []
    for which, strength in ((1, 0.35), (0, 1.0)):
        for i in range(LINES):
            k = abs(i - mid) / mid
            a = strength * (0.55 * (1 - k) ** 1.5 + 0.07)
            pts = sc._line_pts(i, 0.0, step=20, layer=which)
            d = "M" + "L".join(f"{x:.0f} {y:.1f}" for x, y in pts)
            paths.append(f'<path d="{d}" stroke-opacity="{a:.2f}" stroke-width="{1.3 - 0.6 * k:.2f}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
            f'fill="none" stroke="currentColor">{"".join(paths)}</svg>')
