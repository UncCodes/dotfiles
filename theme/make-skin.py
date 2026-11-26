#!/usr/bin/env python3
"""Draw a classic music-player skin (the Winamp 2 bitmap format, read by Audacious and qmmp)
from an edition, so the player wears the desktop's look.

Built from the look's materials, drawn four times over and scaled down so every edge is
smooth: a chrome shell (a bright lip, the lit upper face, a dark horizon, a lighter reflection
below, a fine brushed grain), a recessed tray holding square transport keys (play in glossy
gel with a specular band and a caustic glow underneath), lit readouts with glowing segment
digits and a glass sheen, boxy faders, LED dots, engraved labels in the brand face. Corners
are the look's: boxy. Every colour is a role from tokens.toml; nothing names a product.

Usage:
  python3 theme/make-skin.py [--edition E] OUTDIR       # the bitmaps, pledit.txt, viscolor.txt
`fui skin` renders the current edition into ~/.local/share/fui/skins/<edition> and points
~/.local/share/fui/skin at it. Sprite positions follow the classic format (as documented by
the Webamp project). Needs Pillow.
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from palette import EDS, LOOK, E, edition, is_dark, over  # noqa: E402

S = 4                                                           # supersampling
FONT = HERE.parent / "fui/.local/share/fonts/fui/Michroma-Regular.ttf"   # the vendored brand face
# corners in skin pixels (the skin is drawn at 1x on a 275 px window; the desktop's 4 px panels
# and 2 px controls become these): the shell, trays and readouts, keys
R_SHELL, R_TRAY, R_KEY = 2.0, 1.5, 1.2

# ── the format's 5x6 text font (the marquee): a 4x5 face, drawn crisp ───
GLYPHS = {
    "A": ".##.|#..#|####|#..#|#..#", "B": "###.|#..#|###.|#..#|###.", "C": ".###|#...|#...|#...|.###",
    "D": "###.|#..#|#..#|#..#|###.", "E": "####|#...|###.|#...|####", "F": "####|#...|###.|#...|#...",
    "G": ".###|#...|#.##|#..#|.###", "H": "#..#|#..#|####|#..#|#..#", "I": "###.|.#..|.#..|.#..|###.",
    "J": "..##|...#|...#|#..#|.##.", "K": "#..#|#.#.|##..|#.#.|#..#", "L": "#...|#...|#...|#...|####",
    "M": "#..#|####|####|#..#|#..#", "N": "#..#|##.#|#.##|#..#|#..#", "O": ".##.|#..#|#..#|#..#|.##.",
    "P": "###.|#..#|###.|#...|#...", "Q": ".##.|#..#|#..#|#.#.|.#.#", "R": "###.|#..#|###.|#.#.|#..#",
    "S": ".###|#...|.##.|...#|###.", "T": "###.|.#..|.#..|.#..|.#..", "U": "#..#|#..#|#..#|#..#|.##.",
    "V": "#..#|#..#|#..#|.##.|.##.", "W": "#..#|#..#|####|####|#..#", "X": "#..#|#..#|.##.|#..#|#..#",
    "Y": "#.#.|#.#.|.#..|.#..|.#..", "Z": "####|..#.|.#..|#...|####",
    "0": ".##.|#.##|##.#|#..#|.##.", "1": ".#..|##..|.#..|.#..|###.", "2": "###.|...#|.##.|#...|####",
    "3": "###.|...#|.##.|...#|###.", "4": "#..#|#..#|####|...#|...#", "5": "####|#...|###.|...#|###.",
    "6": ".##.|#...|###.|#..#|.##.", "7": "####|...#|..#.|.#..|.#..", "8": ".##.|#..#|.##.|#..#|.##.",
    "9": ".##.|#..#|.###|...#|.##.",
    '"': "#.#.|#.#.|....|....|....", "@": ".##.|#.##|#.##|#...|.###", "…": "....|....|....|....|#.#.",
    ".": "....|....|....|....|.#..", ":": "....|.#..|....|.#..|....", "(": "..#.|.#..|.#..|.#..|..#.",
    ")": ".#..|..#.|..#.|..#.|.#..", "-": "....|....|###.|....|....", "'": ".#..|.#..|....|....|....",
    "!": ".#..|.#..|.#..|....|.#..", "_": "....|....|....|....|####", "+": "....|.#..|###.|.#..|....",
    "\\": "#...|#...|.#..|..#.|..#.", "/": "..#.|..#.|.#..|#...|#...", "[": ".##.|.#..|.#..|.#..|.##.",
    "]": ".##.|..#.|..#.|..#.|.##.", "^": ".#..|#.#.|....|....|....", "&": ".#..|#.#.|.#..|#.#.|.#.#",
    "%": "#..#|..#.|.#..|#...|#..#", ",": "....|....|....|.#..|#...", "=": "....|###.|....|###.|....",
    "$": ".###|##..|.##.|..##|###.", "#": ".#.#|####|.#.#|####|.#.#", "Å": ".#..|.##.|#..#|####|#..#",
    "Ö": "#..#|.##.|#..#|#..#|.##.", "Ä": "#..#|.##.|#..#|####|#..#", "?": "###.|...#|.##.|....|.#..",
    "*": "....|#.#.|.#..|#.#.|....", " ": "....|....|....|....|....",
}
CELLS = {**{c: (0, i) for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}, '"': (0, 26), "@": (0, 27), " ": (0, 30),
         **{c: (1, i) for i, c in enumerate("0123456789")}, "…": (1, 10), ".": (1, 11), ":": (1, 12), "(": (1, 13),
         ")": (1, 14), "-": (1, 15), "'": (1, 16), "!": (1, 17), "_": (1, 18), "+": (1, 19), "\\": (1, 20), "/": (1, 21),
         "[": (1, 22), "]": (1, 23), "^": (1, 24), "&": (1, 25), "%": (1, 26), ",": (1, 27), "=": (1, 28), "$": (1, 29),
         "#": (1, 30), "Å": (2, 0), "Ö": (2, 1), "Ä": (2, 2), "?": (2, 3), "*": (2, 4)}

# seven segments in a 9x13 cell, as (x0, y0, x1, y1) bars
SEG = {"a": (2, 1, 7, 2), "b": (7, 2, 8, 6), "c": (7, 7, 8, 11), "d": (2, 11, 7, 12), "e": (1, 7, 2, 11),
       "f": (1, 2, 2, 6), "g": (2, 6, 7, 7)}
DIGITS = {0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc", 5: "afgcd", 6: "afgedc", 7: "abc", 8: "abcdefg", 9: "abcdfg"}

# where the main window's sprites sit (the format's fixed layout), for seamless backgrounds
AT = {"volume": (107, 57), "balance": (177, 57), "posbar": (16, 72), "cbuttons": (16, 88), "eject": (136, 89),
      "shuffle": (164, 89), "repeat": (210, 89), "eq": (219, 58), "pl": (242, 58), "monoster": (212, 41)}
TRAY = (12, 85, 162, 108)                                      # the recess the transport sits in
SEEK = (14, 70, 266, 84)                                       # the recess behind the seek bar
H_MAIN = 116
WHITE, BLACK = (255, 255, 255), (0, 0, 0)


# ── colour ──────────────────────────────────────────────────────────────
def rgb(c, base="#000000"):
    c = over(c, base) if len(c) > 7 else c
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def stops_at(stops, t):
    t = min(max(t, 0.0), 1.0)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return mix(c0, c1, 0 if t1 == t0 else (t - t0) / (t1 - t0))
    return stops[-1][1]


# ── a supersampled canvas: draw at 4x, scale down once ──────────────────
class Canvas:
    def __init__(self, w, h, fill=(0, 0, 0)):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w * S, h * S), (*fill, 255))

    @staticmethod
    def box(b):
        return tuple(round(v * S) for v in b)

    def mask(self, b, r=0, ellipse=False):
        m = Image.new("L", self.im.size, 0)
        d = ImageDraw.Draw(m)
        bb = self.box(b)
        if ellipse:
            d.ellipse(bb, fill=255)
        elif r:
            d.rounded_rectangle(bb, radius=round(r * S), fill=255)
        else:
            d.rectangle(bb, fill=255)
        return m

    def paint(self, m, colour, alpha=1.0):
        layer = Image.new("RGBA", self.im.size, (*colour, 255))
        a = m if alpha >= 1 else m.point(lambda v: round(v * alpha))
        self.im.paste(layer, (0, 0), a)

    def gradient(self, m, fn):
        """Fill the mask with colour fn(y) per row (y in 1x units of this canvas)."""
        H = self.im.size[1]
        col = Image.new("RGB", (1, H))
        col.putdata([fn(yy / S) for yy in range(H)])
        self.im.paste(col.resize(self.im.size, Image.NEAREST).convert("RGBA"), (0, 0), m)

    def shadow(self, m, blur=1.5, dy=1.0, alpha=0.45, colour=BLACK):
        sh = ImageChops.offset(m, 0, round(dy * S)).filter(ImageFilter.GaussianBlur(blur * S))
        self.paint(sh, colour, alpha)

    def inner_shadow(self, m, blur=1.2, dy=1.0, alpha=0.6, colour=BLACK):
        inv = ImageChops.invert(m)
        sh = ImageChops.offset(inv, 0, round(dy * S)).filter(ImageFilter.GaussianBlur(blur * S))
        self.paint(ImageChops.multiply(sh, m), colour, alpha)

    def glow(self, m, colour, blur=1.5, alpha=0.6):
        self.paint(m.filter(ImageFilter.GaussianBlur(blur * S)), colour, alpha)

    def stroke(self, b, r, colour, width=1.0, alpha=1.0):
        m = Image.new("L", self.im.size, 0)
        ImageDraw.Draw(m).rounded_rectangle(self.box(b), radius=round(r * S), outline=255, width=max(1, round(width * S)))
        self.paint(m, colour, alpha)

    def highlight(self, b, alpha=0.8, height=0.48):
        """A specular band: soft white across the top of a key, fading downward (a square
        band, as the keys are square)."""
        x0, y0, x1, y1 = b
        w, h = x1 - x0, y1 - y0
        lens = self.mask((x0 + w * 0.08, y0 + h * 0.05, x1 - w * 0.08, y0 + h * height * 1.6), R_KEY * 0.6)
        Y0, Y1 = y0 * S, (y0 + h * height) * S
        col = Image.new("L", (1, self.im.size[1]))
        col.putdata([round(255 * max(0.0, min(1.0, 1 - (yy - Y0) / max(1, Y1 - Y0))) ** 1.4) for yy in range(self.im.size[1])])
        self.paint(ImageChops.multiply(lens, col.resize(self.im.size, Image.NEAREST)), WHITE, alpha)

    def text(self, xy, s, colour, size=6.0, anchor="la", alpha=1.0, engrave=None):
        try:
            f = ImageFont.truetype(str(FONT), round(size * S))
        except OSError:
            f = ImageFont.load_default()
        x, y = xy
        if engrave:                                           # a lit edge under the letters: engraved in metal
            m = Image.new("L", self.im.size, 0)
            ImageDraw.Draw(m).text((round(x * S), round((y + 0.5) * S)), s, font=f, fill=255, anchor=anchor)
            self.paint(m, engrave, 0.55 * alpha)
        m = Image.new("L", self.im.size, 0)
        ImageDraw.Draw(m).text((round(x * S), round(y * S)), s, font=f, fill=255, anchor=anchor)
        self.paint(m, colour, alpha)

    def out(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS).convert("RGB")


# ── the edition's materials ─────────────────────────────────────────────
class Kit:
    def __init__(self, ed):
        self.ed, self.dark = ed, is_dark(ed)
        p = E(ed)
        k = {n: rgb(p[n]) for n in ("floor", "panel", "raised", "well", "rule", "rule_hi", "edge", "ink", "muted", "signal",
                                    "signal_hi", "signal_dim", "on_signal", "shell", "shell_hi", "readout", "readout_ink")}
        self.k = k
        sh, hi = k["shell"], k["shell_hi"]
        # chrome: a bright lip, the lit upper face, a dark horizon, then a lighter reflection
        self.chrome = [(0.00, mix(hi, WHITE, 0.55)), (0.05, hi), (0.46, mix(sh, hi, 0.45)), (0.50, mix(sh, BLACK, 0.05)),
                       (0.84, mix(sh, BLACK, 0.12)), (1.00, mix(sh, hi, 0.40))]
        self.rim = mix(sh, BLACK, 0.62)                       # the dark edge around every part
        self.lip = WHITE if not self.dark else mix(hi, WHITE, 0.4)
        self.tray = [(0.0, mix(sh, BLACK, 0.50)), (0.35, mix(sh, BLACK, 0.36)), (1.0, mix(sh, BLACK, 0.24))]
        self.engrave_ink = mix(sh, BLACK, 0.74) if not self.dark else mix(hi, WHITE, 0.82)
        self.engrave_lit = WHITE if not self.dark else BLACK
        lit = k["readout_ink"]
        self.lcd_stops = [(0.0, mix(k["readout"], BLACK, 0.30)), (0.55, k["readout"]), (1.0, mix(k["readout"], lit, 0.10))]
        self.gel = [(0.0, mix(k["signal"], WHITE, 0.45)), (0.48, mix(k["signal"], WHITE, 0.10)),
                    (0.52, k["signal"]), (1.0, mix(k["signal"], BLACK, 0.32))]
        self.face = [(0.0, mix(hi, WHITE, 0.78)), (0.5, mix(hi, WHITE, 0.18)), (0.53, mix(sh, hi, 0.50)), (1.0, mix(sh, WHITE, 0.30))]
        self.mark = mix(sh, BLACK, 0.72)                      # glyphs printed on chrome
        sig = k["signal"]                                     # glyphs on gel: white, or ink when the signal is pale
        self.on_gel = WHITE if (0.299 * sig[0] + 0.587 * sig[1] + 0.114 * sig[2]) < 150 else mix(sig, BLACK, 0.78)
        random.seed(7)
        raw = [random.uniform(-1, 1) for _ in range(H_MAIN * S * 4)]
        self.grain = [(raw[i - 1] + 2 * raw[i] + raw[(i + 1) % len(raw)]) / 4 for i in range(len(raw))]

    def chrome_at(self, y, height=H_MAIN):
        c = stops_at(self.chrome, y / height)
        g = self.grain[int(y * S) % len(self.grain)] * (3.0 if not self.dark else 2.2)   # a fine brushed grain
        return tuple(max(0, min(255, round(v + g))) for v in c)

    def tray_at(self, y, box=TRAY):
        return stops_at(self.tray, (y - box[1]) / (box[3] - box[1]))

    # ── parts ──
    def body(self, cv, b, r, height=H_MAIN):
        m = cv.mask(b, r)
        cv.gradient(m, lambda y: self.chrome_at(y, height))
        cv.stroke(b, r, self.rim, 1.0)
        x0, y0, x1, y1 = b
        cv.stroke((x0 + 1, y0 + 1, x1 - 1, y1 - 1), max(0, r - 1), self.lip, 0.75, 0.75 if not self.dark else 0.35)

    def recess(self, cv, b, r, fn):
        """A tray set into the shell: darker, shadowed at its top, lit along its bottom edge."""
        m = cv.mask(b, r)
        cv.gradient(m, fn)
        cv.inner_shadow(m, blur=1.4, dy=1.2, alpha=0.65)
        x0, y0, x1, y1 = b
        cv.stroke((x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5), r + 0.5, self.lip, 0.6, 0.55 if not self.dark else 0.25)

    def lcd(self, cv, b, r, glass=True):
        """A lit readout: dark glass, an inner shadow, a faint glow of its own light, a sheen."""
        m = cv.mask(b, r)
        x0, y0, x1, y1 = b
        cv.gradient(m, lambda y: stops_at(self.lcd_stops, (y - y0) / max(1, y1 - y0)))
        w, h = x1 - x0, y1 - y0
        core = cv.mask((x0 + w * 0.12, y0 + h * 0.25, x1 - w * 0.12, y1 + h * 0.2), ellipse=True)
        cv.paint(ImageChops.multiply(core.filter(ImageFilter.GaussianBlur(min(6, h / 3) * S)), m), self.k["readout_ink"], 0.10)
        cv.inner_shadow(m, blur=min(1.6, h / 6), dy=min(1.0, h / 8), alpha=0.75)
        cv.stroke(b, r, BLACK, 0.8, 0.55)
        cv.stroke((x0 - 0.7, y0 - 0.7, x1 + 0.7, y1 + 0.7), r + 0.7, self.lip, 0.6, 0.5 if not self.dark else 0.22)
        if glass:                                             # the cover glass catches the light at its top
            sheen = cv.mask((x0 - w * 0.2, y0 - h * 0.9, x1 + w * 0.1, y0 + h * 0.42), ellipse=True)
            cv.paint(ImageChops.multiply(sheen, m), WHITE, 0.07)

    def _face(self, cv, fb, r, gel, pressed):
        face = cv.mask(fb, r)
        stops = self.gel if gel else self.face
        if pressed:
            stops = [(1 - t, mix(c, BLACK, 0.18)) for t, c in reversed(stops)]
        cv.gradient(face, lambda y: stops_at(stops, (y - fb[1]) / max(0.5, fb[3] - fb[1])))
        return face

    def key(self, cv, cx, cy, rad, kind=None, gel=False, pressed=False):
        """A square key: a rim, a face lit from above, a specular band; gel ones glow below."""
        b = (cx - rad, cy - rad, cx + rad, cy + rad)
        k = self.k
        outer = cv.mask(b, R_KEY)
        cv.shadow(outer, blur=1.1, dy=0.9, alpha=0.5)
        cv.paint(outer, self.rim)
        fb = (b[0] + 0.9, b[1] + 0.9, b[2] - 0.9, b[3] - 0.9)
        face = self._face(cv, fb, max(0.4, R_KEY - 0.9), gel, pressed)
        if gel:                                               # the caustic: light gathering at the bottom of the glass
            cau = cv.mask((cx - rad * 0.6, cy + rad * 0.12, cx + rad * 0.6, cy + rad * 0.92), ellipse=True)
            cv.paint(ImageChops.multiply(cau.filter(ImageFilter.GaussianBlur(1.2 * S)), face), mix(k["signal"], WHITE, 0.55), 0.6)
        cv.inner_shadow(face, blur=0.8, dy=-0.6, alpha=0.5 if pressed else 0.22)
        cv.highlight(fb, alpha=0.30 if pressed else (0.88 if gel else 0.78), height=0.46)
        if kind:
            off = 0.5 if pressed else 0.0
            if gel and self.on_gel == WHITE:
                self.glyph(cv, kind, cx + off, cy + off + 0.5, rad, BLACK, alpha=0.35)
            self.glyph(cv, kind, cx + off, cy + off, rad, self.on_gel if gel else self.mark)

    def capsule(self, cv, b, gel=False, pressed=False, label=None, led=None):
        """A wide key (or a fader thumb): the key's materials, stretched."""
        x0, y0, x1, y1 = b
        r = R_KEY
        k = self.k
        outer = cv.mask(b, r)
        cv.shadow(outer, blur=0.9, dy=0.7, alpha=0.45)
        cv.paint(outer, self.rim)
        fb = (x0 + 0.8, y0 + 0.8, x1 - 0.8, y1 - 0.8)
        self._face(cv, fb, max(0.5, r - 0.8), gel, pressed)
        cv.highlight(fb, alpha=0.3 if pressed else 0.72, height=0.5)
        tx = x0 + 3.0
        if led is not None:
            self.led(cv, x0 + 4.4, (y0 + y1) / 2, led)
            tx = x0 + 7.2
        if label:
            ink = self.on_gel if gel else self.mark
            cv.text(((tx + x1 - 2.6) / 2, (y0 + y1) / 2 + 0.25 + (0.5 if pressed else 0)), label, ink, size=4.8, anchor="mm")

    def led(self, cv, cx, cy, on):
        b = (cx - 1.6, cy - 1.6, cx + 1.6, cy + 1.6)
        m = cv.mask(b, ellipse=True)
        k = self.k
        if on:
            cv.glow(m, k["signal"], blur=1.3, alpha=0.9)
            cv.paint(m, mix(k["signal"], WHITE, 0.35))
            cv.paint(cv.mask((cx - 0.9, cy - 1.2, cx + 0.3, cy - 0.3), ellipse=True), WHITE, 0.85)
        else:
            cv.paint(m, mix(k["readout"], k["readout_ink"], 0.14))
            cv.stroke(b, 1.6, BLACK, 0.5, 0.4)

    def glyph(self, cv, kind, cx, cy, rad, colour, alpha=1.0):
        s = rad * 0.42
        m = Image.new("L", cv.im.size, 0)
        d = ImageDraw.Draw(m)
        P = lambda pts: [(round(x * S), round(y * S)) for x, y in pts]
        if kind == "play":
            d.polygon(P([(cx - s * 0.7, cy - s), (cx - s * 0.7, cy + s), (cx + s * 1.0, cy)]), fill=255)
        elif kind == "pause":
            d.rectangle(cv.box((cx - s * 0.85, cy - s * 0.95, cx - s * 0.25, cy + s * 0.95)), fill=255)
            d.rectangle(cv.box((cx + s * 0.25, cy - s * 0.95, cx + s * 0.85, cy + s * 0.95)), fill=255)
        elif kind == "stop":
            d.rectangle(cv.box((cx - s * 0.8, cy - s * 0.8, cx + s * 0.8, cy + s * 0.8)), fill=255)
        elif kind in ("next", "prev"):
            k = 1 if kind == "next" else -1
            for dx in (-1.0, -0.05):
                d.polygon(P([(cx + k * dx * s, cy - s * 0.75), (cx + k * dx * s, cy + s * 0.75), (cx + k * (dx + 0.95) * s, cy)]), fill=255)
            bx = cx + k * 0.9 * s
            d.rectangle(cv.box((min(bx, bx + k * 0.28 * s), cy - s * 0.75, max(bx, bx + k * 0.28 * s), cy + s * 0.75)), fill=255)
        elif kind == "eject":
            d.polygon(P([(cx - s, cy + s * 0.15), (cx + s, cy + s * 0.15), (cx, cy - s * 0.9)]), fill=255)
            d.rectangle(cv.box((cx - s, cy + s * 0.45, cx + s, cy + s * 0.8)), fill=255)
        else:
            w = max(0.7, rad * 0.24)
            if kind == "min":
                d.rectangle(cv.box((cx - s, cy + s * 0.3, cx + s, cy + s * 0.3 + w)), fill=255)
            elif kind == "close":
                d.line(P([(cx - s, cy - s), (cx + s, cy + s)]), fill=255, width=round(w * S))
                d.line(P([(cx + s, cy - s), (cx - s, cy + s)]), fill=255, width=round(w * S))
            elif kind == "opt":
                d.ellipse(cv.box((cx - s * 0.55, cy - s * 0.55, cx + s * 0.55, cy + s * 0.55)), fill=255)
            else:                                             # shade: two bars
                d.rectangle(cv.box((cx - s, cy - s * 0.6, cx + s, cy - s * 0.6 + w)), fill=255)
                d.rectangle(cv.box((cx - s, cy + s * 0.3, cx + s, cy + s * 0.3 + w)), fill=255)
        cv.paint(m, colour, alpha)

    def segments(self, cv, x, y, n):
        """One seven-segment digit: lit bars with a bloom, unlit bars faintly visible."""
        on = set(DIGITS.get(n, "")) if n is not None else set()
        lit, unlit = Image.new("L", cv.im.size, 0), Image.new("L", cv.im.size, 0)
        dl, du = ImageDraw.Draw(lit), ImageDraw.Draw(unlit)
        for name, (a, b, c, d) in SEG.items():
            bb = cv.box((x + a + 0.15, y + b + 0.15, x + c - 0.15, y + d - 0.15))
            (dl if name in on else du).rounded_rectangle(bb, radius=round(0.45 * S), fill=255)
        cv.paint(unlit, self.k["readout_ink"], 0.12)
        cv.glow(lit, self.k["readout_ink"], blur=0.9, alpha=0.55)
        cv.paint(lit, mix(self.k["readout_ink"], WHITE, 0.15))

    def fill_bar(self, cv, b):
        m = cv.mask(b, min(0.6, (b[3] - b[1]) / 2))
        cv.glow(m, self.k["signal"], 1.0, 0.55)
        cv.gradient(m, lambda y: stops_at(self.gel, (y - b[1]) / max(0.5, b[3] - b[1])))

    def label(self, cv, xy, s, size=5.0, anchor="la"):
        cv.text(xy, s, self.engrave_ink, size=size + 0.4, anchor=anchor, engrave=self.engrave_lit)

    def ground(self, cv, b, fn):
        """A sprite's own background, matching what the window draws under it."""
        m = cv.mask(b)
        cv.gradient(m, fn)


# ── the main window ─────────────────────────────────────────────────────
def main_bmp(K):
    cv = Canvas(275, 116, K.rim)
    K.body(cv, (0.5, 0.5, 274.5, 115.5), R_SHELL)
    K.lcd(cv, (8, 18, 107, 64), R_TRAY)                            # time, status, the analyser
    for y in (30, 35):                                        # the time's colon
        cv.paint(cv.mask((72.2, y, 73.8, y + 1.6), 0.6), K.k["readout_ink"])
    K.lcd(cv, (109, 22, 267, 37), R_TRAY)                          # the marquee
    K.lcd(cv, (109, 40.5, 129.5, 51.5), R_KEY, glass=False)       # kbps
    K.lcd(cv, (153, 40.5, 169.5, 51.5), R_KEY, glass=False)       # kHz
    K.label(cv, (132, 46.4), "KBPS", 4.4, "lm")
    K.label(cv, (172, 46.4), "KHZ", 4.4, "lm")
    K.recess(cv, SEEK, R_TRAY, lambda y: K.tray_at(y, SEEK))       # behind the seek groove
    K.recess(cv, TRAY, R_TRAY, K.tray_at)                       # the transport's tray
    K.key(cv, 259.5, 97, 6)                                   # the maker's place: a key with a lit point, no name
    K.led(cv, 259.5, 97, True)
    return cv.out()


def titlebar_bmp(K):
    cv = Canvas(344, 87, K.rim)
    k = K.k

    def bar(y, focused):
        b = (27, y, 302, y + 14)
        cv.gradient(cv.mask(b), lambda yy: K.chrome_at(yy - y))
        slot = (115, y + 5.6, 214, y + 8.4)                # the grip: a slot pressed into the chrome
        sm = cv.mask(slot, 1.4)
        cv.paint(sm, mix(k["shell"], BLACK, 0.55))
        cv.inner_shadow(sm, blur=0.6, dy=0.5, alpha=0.6)
        if focused:                                       # ...lit in the signal while the window has focus
            cv.glow(sm, k["signal"], blur=1.4, alpha=0.75)
            cv.paint(cv.mask((116.5, y + 6.4, 212.5, y + 7.6), 0.6), mix(k["signal"], WHITE, 0.3), 0.9)
        cv.stroke((27.5, y + 0.6, 301.5, y + 14), 0, K.lip, 0.5, 0.5 if focused else 0.25)
    for y, foc in ((0, True), (15, False), (57, True), (72, False), (29, True), (42, False)):
        bar(y, foc)
    for x, y, kind, pressed in ((0, 0, "opt", False), (0, 9, "opt", True), (9, 0, "min", False), (9, 9, "min", True),
                                (18, 0, "close", False), (18, 9, "close", True), (0, 18, "shade", False),
                                (9, 18, "shade", True), (0, 27, "shade", False), (9, 27, "shade", True)):
        K.ground(cv, (x, y, x + 9, y + 9), lambda yy, y=y: K.chrome_at(yy - y + 3))
        K.key(cv, x + 4.5, y + 4.5, 4.0, kind, pressed=pressed)
    for x, lit in ((304, True), (312, False)):                # the clutter bar (8x43)
        K.lcd(cv, (x + 0.5, 0.5, x + 7.5, 42.5), R_KEY, glass=False)
        for i, ch in enumerate("OAIDV"):
            cv.text((x + 4, 5 + i * 8), ch, k["readout_ink"], 4.2, "mm", alpha=0.85 if lit else 0.25)
    for i, (x, y, h) in enumerate(((304, 47, 8), (312, 55, 7), (320, 62, 7), (328, 69, 8), (336, 77, 7))):
        cv.paint(cv.mask((x, y, x + 8, y + h)), k["readout"])
        cv.text((x + 4, y + h / 2), "OAIDV"[i], mix(k["readout_ink"], WHITE, 0.3), 4.2, "mm")
    K.lcd(cv, (0, 36, 17, 43), R_KEY, glass=False)                # the shaded window's small seek bar
    for x in (17, 20, 23):
        cv.paint(cv.mask((x, 36, x + 3, 43), 1.4), k["signal"])
    return cv.out()


def cbuttons_bmp(K):
    """The transport: square keys in the tray; play is gel."""
    cv = Canvas(136, 36, K.rim)
    oy, ey = AT["cbuttons"][1], AT["eject"][1]
    kinds = [("prev", 0, 23), ("play", 23, 23), ("pause", 46, 23), ("stop", 69, 23), ("next", 92, 22)]
    for row, pressed in ((0, False), (18, True)):
        K.ground(cv, (0, row, 114, row + 18), lambda y, row=row: K.tray_at(y - row + oy))
        for kind, x, w in kinds:
            K.key(cv, x + w / 2, row + 9, 8.4 if kind == "play" else 7.6, kind, gel=kind == "play", pressed=pressed)
    for row, pressed in ((0, False), (16, True)):
        K.ground(cv, (114, row, 136, row + 16), lambda y, row=row: K.tray_at(y - row + ey))
        K.capsule(cv, (116, row + 2.5, 134, row + 13.5), pressed=pressed)
        K.glyph(cv, "eject", 125, row + 8 + (0.5 if pressed else 0), 8, K.mark)
    return cv.out()


def shufrep_bmp(K):
    cv = Canvas(92, 85, K.rim)
    for i, (on, pressed) in enumerate(((False, False), (False, True), (True, False), (True, True))):
        y = i * 15
        K.ground(cv, (0, y, 75, y + 15), lambda yy, y=y: K.chrome_at(yy - y + AT["repeat"][1]))
        K.capsule(cv, (1, y + 2, 27, y + 13), pressed=pressed, label="REP", led=on)
        K.capsule(cv, (29, y + 2, 74, y + 13), pressed=pressed, label="SHUFFLE", led=on)
    for x, y, lab, on, pressed in ((0, 61, "EQ", False, False), (23, 61, "PL", False, False), (0, 73, "EQ", True, False),
                                   (23, 73, "PL", True, False), (46, 61, "EQ", False, True), (69, 61, "PL", False, True),
                                   (46, 73, "EQ", True, True), (69, 73, "PL", True, True)):
        K.ground(cv, (x, y, x + 23, y + 12), lambda yy, y=y: K.chrome_at(yy - y + AT["eq"][1]))
        K.capsule(cv, (x + 0.5, y + 1, x + 22.5, y + 11), pressed=pressed, label=lab, led=on)
    return cv.out()


def text_bmp(K):
    im = Image.new("RGB", (155, 18), K.k["readout"])
    d = ImageDraw.Draw(im)
    ink = mix(K.k["readout_ink"], WHITE, 0.15)
    for ch, (row, col) in CELLS.items():
        for j, line in enumerate(GLYPHS[ch].split("|")):
            for i, v in enumerate(line):
                if v == "#":
                    d.point((col * 5 + i, row * 6 + j), fill=ink)
    return im


def nums_bmp(K, width):
    cv = Canvas(width, 13, K.k["readout"])
    for n in range(10):
        K.segments(cv, n * 9, 0, n)
    K.segments(cv, 90, 0, None)
    if width >= 108:
        K.segments(cv, 99, 0, None)
        cv.paint(cv.mask((101.2, 6.1, 106.8, 6.9), 0.4), K.k["readout_ink"])
    else:
        cv.paint(cv.mask((20.2, 6.1, 24.8, 6.9), 0.4), K.k["readout_ink"])
    return cv.out()


def playpaus_bmp(K):
    cv = Canvas(42, 9, K.k["readout"])
    for kind, cx in (("play", 4.5), ("pause", 13.5), ("stop", 22.5)):
        K.glyph(cv, kind, cx, 4.5, 7.5, K.k["readout_ink"])
    K.led(cv, 37.5, 4.5, False)
    K.led(cv, 40.5, 4.5, True)
    return cv.out()


def monoster_bmp(K):
    cv = Canvas(58, 24, K.rim)
    for y, lit in ((0, True), (12, False)):
        for x, w, lab in ((0, 29, "STEREO"), (29, 27, "MONO")):
            K.ground(cv, (x, y, x + w, y + 12), lambda yy, y=y: K.chrome_at(yy - y + AT["monoster"][1]))
            K.lcd(cv, (x + 0.6, y + 0.6, x + w - 0.6, y + 11.4), R_KEY, glass=False)
            if lit:
                cv.glow(cv.mask((x + 4, y + 4, x + w - 4, y + 8), 2), K.k["readout_ink"], 2.0, 0.22)
            cv.text((x + w / 2, y + 6.3), lab, K.k["readout_ink"], 4.2, "mm", alpha=1.0 if lit else 0.18)
    return cv.out()


def posbar_bmp(K):
    cv = Canvas(307, 10, K.rim)
    oy = AT["posbar"][1]
    K.ground(cv, (0, 0, 307, 10), lambda y: K.tray_at(y + oy, SEEK))
    K.lcd(cv, (1, 3, 247, 7.5), R_KEY, glass=False)
    for x0, pressed in ((248, False), (278, True)):
        K.capsule(cv, (x0 + 0.5, 0.5, x0 + 28.5, 9.5), gel=True, pressed=pressed)
    return cv.out()


def fader_frames(K, width, x0, centred, abs_y):
    """28 frames of a level (volume) or a centred one (balance) on the shell, and the thumbs."""
    cv = Canvas(68, 433, K.rim)
    for i in range(28):
        y = i * 15
        K.ground(cv, (0, y, 68, y + 13), lambda yy, y=y: K.chrome_at(yy - y + abs_y))
        K.lcd(cv, (x0 + 0.5, y + 4.6, x0 + width - 0.5, y + 8.4), R_KEY, glass=False)
        t = i / 27
        if centred:
            mid, half = x0 + width / 2, (width / 2 - 1.5) * t
            if half > 0.3:
                K.fill_bar(cv, (mid - half, y + 5.2, mid + half, y + 7.8))
        elif (width - 3) * t > 0.3:
            K.fill_bar(cv, (x0 + 1.5, y + 5.2, x0 + 1.5 + (width - 3) * t, y + 7.8))
    for x, pressed in ((15, False), (0, True)):
        K.ground(cv, (x, 422, x + 14, 433), lambda yy: K.chrome_at(yy - 422 + abs_y + 1))
        K.capsule(cv, (x + 0.5, 423, x + 13.5, 432), pressed=pressed)
        cv.paint(cv.mask((x + 6.3, 425, x + 7.7, 430), 0.5), K.k["signal"], 0.9)
    return cv.out()


# ── the equaliser ───────────────────────────────────────────────────────
EQ_TRAYS = ((15, 36, 41, 103), (73, 36, 263, 103))


def eqmain_bmp(K):
    cv = Canvas(275, 315, K.rim)
    k = K.k
    K.body(cv, (0.5, 0.5, 274.5, 115.5), R_SHELL)
    eq_tray = lambda y: stops_at(K.tray, (y - 36) / 67)
    for tb in EQ_TRAYS:
        K.recess(cv, tb, R_TRAY, eq_tray)
    K.lcd(cv, (85, 16, 200, 37), R_TRAY)                           # the curve graph's place
    K.label(cv, (28, 109), "PREAMP", 4.2, "mm")
    for i, f in enumerate(("60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K")):
        K.label(cv, (85 + i * 18, 109), f, 4.2, "mm")
    for y, lab in ((41, "+12"), (69.5, "0"), (98, "-12")):
        K.label(cv, (70, y), lab, 4.0, "rm")
    for y, foc in ((134, True), (149, False)):               # title bars
        m = cv.mask((0, y, 275, y + 14))
        cv.gradient(m, lambda yy, y=y: K.chrome_at(yy - y))
        if foc:
            cv.glow(cv.mask((96, y + 6, 179, y + 8), 1), k["signal"], 1.6, 0.6)
        K.label(cv, (137.5, y + 7.4), "EQUALIZER", 4.8, "mm")
    for y, pressed in ((116, False), (125, True)):
        K.ground(cv, (0, y, 9, y + 9), lambda yy, y=y: K.chrome_at(yy - y + 3))
        K.key(cv, 4.5, y + 4.5, 4.0, "close", pressed=pressed)
    for x_on, x_auto, lit, pressed in ((10, 36, False, False), (128, 154, False, True), (69, 95, True, False), (187, 213, True, True)):
        for x, w, lab in ((x_on, 26, "ON"), (x_auto, 32, "AUTO")):
            K.ground(cv, (x, 119, x + w, 131), lambda yy: K.chrome_at(yy - 119 + 18))
            K.capsule(cv, (x + 0.5, 119.5, x + w - 0.5, 130.5), pressed=pressed, label=lab, led=lit)
    for n in range(28):                                       # fader frames: 14x63, 14 a row, 15 apart
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        K.ground(cv, (x, y, x + 14, y + 63), lambda yy, y=y: eq_tray(yy - y + 38))
        K.lcd(cv, (x + 5.2, y + 1.5, x + 8.8, y + 61.5), R_KEY, glass=False)
        top, zero = y + 59.5 - 56 * n / 27, y + 31.5
        if abs(top - zero) > 0.6:
            K.fill_bar(cv, (x + 5.9, min(top, zero), x + 8.1, max(top, zero)))
    for y, pressed in ((164, False), (176, True)):           # the capsule thumb
        K.ground(cv, (0, y, 11, y + 11), lambda yy: stops_at(K.tray, 0.5))
        K.capsule(cv, (0.5, y + 2, 10.5, y + 9), pressed=pressed)
        cv.paint(cv.mask((2.5, y + 5.1, 8.5, y + 5.9), 0.3), k["signal"])
    K.lcd(cv, (0, 294, 113, 313), 0, glass=False)            # the graph's background
    for yy in (298.5, 303.5, 308.5):
        cv.paint(cv.mask((1, yy, 112, yy + 0.4)), k["readout_ink"], 0.10)
    for i in range(19):                                       # the graph line's colours, top to bottom
        cv.paint(cv.mask((115, 294 + i, 116, 295 + i)), mix(k["signal_hi"], k["readout_ink"], i / 18))
    for y, pressed in ((164, False), (176, True)):
        K.ground(cv, (224, y, 268, y + 12), lambda yy: K.chrome_at(yy - y + 18))
        K.capsule(cv, (224.5, y + 0.5, 267.5, y + 11.5), pressed=pressed, label="PRESETS")
    cv.paint(cv.mask((0, 314, 113, 315)), k["readout_ink"], 0.4)
    return cv.out()


# ── the playlist ────────────────────────────────────────────────────────
def pledit_bmp(K):
    cv = Canvas(280, 186, K.rim)
    k = K.k

    def strip(b, focused=False):
        h = b[3] - b[1]
        cv.gradient(cv.mask(b), lambda y: K.chrome_at((y - b[1]) / h * 20, 20))
        cv.stroke((b[0], b[1] + 0.5, b[2], b[3]), 0, K.lip, 0.5, 0.35)

    for y, foc in ((0, True), (21, False)):
        for x, w in ((0, 25), (26, 100), (127, 25), (153, 25)):
            strip((x, y, x + w, y + 20), foc)
        if foc:
            cv.glow(cv.mask((44, y + 9, 108, y + 11), 1), k["signal"], 1.6, 0.55)
        K.label(cv, (76, y + 10.4), "PLAYLIST", 4.8, "mm")
    for x0, x1 in ((0, 12), (31, 51)):                        # the side edges: chrome lit from the left
        row = Image.new("RGB", ((x1 - x0) * S, 1))
        row.putdata([stops_at(K.chrome, 0.12 + 0.6 * i / ((x1 - x0) * S)) for i in range((x1 - x0) * S)])
        cv.im.paste(row.resize(((x1 - x0) * S, 29 * S)).convert("RGBA"), (x0 * S, 42 * S))
    K.lcd(cv, (36, 42, 44, 71), 0, glass=False)               # the scroll groove
    for x, sel in ((52, False), (61, True)):
        cv.paint(cv.mask((x, 53, x + 8, 71)), k["readout"])
        K.capsule(cv, (x + 0.5, 53.5, x + 7.5, 70.5), gel=True, pressed=sel)
    strip((179, 0, 204, 38))
    strip((0, 72, 125, 110))
    for i, lab in enumerate(("ADD", "REM", "SEL", "MISC")):
        x = 11 + i * 29
        K.capsule(cv, (x, 86, x + 23, 103), label=lab)
    strip((126, 72, 276, 110))
    K.lcd(cv, (133, 78, 217, 92), R_TRAY)
    K.capsule(cv, (226, 86, 252, 103), label="LIST")
    K.lcd(cv, (205.5, 0.5, 279.5, 37.5), R_KEY, glass=False)      # the visualiser's place
    for x, y, w in ((72, 57, 25), (72, 42, 25), (99, 57, 50), (99, 42, 50)):
        strip((x, y, x + w, y + 14))
    for x, y, kind in ((52, 42, "close"), (62, 42, "min"), (150, 42, "shade")):
        K.ground(cv, (x, y, x + 9, y + 9), lambda yy, y=y: K.chrome_at(yy - y + 3))
        K.key(cv, x + 4.5, y + 4.5, 4.0, kind, pressed=True)
    for col, x in enumerate((0, 54, 104, 154, 204)):          # the menus: 22x18 buttons and 3 px bars
        for row in range(4 if col == 1 else 3):
            y = 111 + row * 19
            for dx, sel in ((0, False), (23, True)):
                cv.paint(cv.mask((x + dx, y, x + dx + 22, y + 18)), stops_at(K.tray, 0.5))
                K.capsule(cv, (x + dx + 1, y + 2, x + dx + 21, y + 16), gel=sel)
    for x in (48, 100, 150, 200, 250):
        cv.paint(cv.mask((x, 111, x + 3, 183), 1.5), k["signal"])
    return cv.out()


def write(out, ed):
    K = Kit(ed)
    out.mkdir(parents=True, exist_ok=True)
    images = {"main": main_bmp(K), "titlebar": titlebar_bmp(K), "cbuttons": cbuttons_bmp(K), "shufrep": shufrep_bmp(K),
              "text": text_bmp(K), "numbers": nums_bmp(K, 99), "nums_ex": nums_bmp(K, 108), "playpaus": playpaus_bmp(K),
              "monoster": monoster_bmp(K), "posbar": posbar_bmp(K),
              "volume": fader_frames(K, 68, 0, False, AT["volume"][1]),
              "balance": fader_frames(K, 38, 9, True, AT["balance"][1]),
              "eqmain": eqmain_bmp(K), "pledit": pledit_bmp(K)}
    for name, im in images.items():
        im.save(out / f"{name}.bmp")
    k = K.k
    hexc = lambda t: "#%02X%02X%02X" % t
    # a lit playlist: the readout's colours
    normal, current, bg = k["readout_ink"], mix(k["readout_ink"], WHITE, 0.7), k["readout"]
    sel = mix(k["readout"], k["signal"], 0.45)
    (out / "pledit.txt").write_text(f"[Text]\nNormal={hexc(normal)}\nCurrent={hexc(current)}\nNormalBG={hexc(bg)}\n"
                                    f"SelectedBG={hexc(sel)}\nmbFG={hexc(k['ink'])}\nmbBG={hexc(k['panel'])}\nFont=Inter\n")
    # viscolor: 0 background, 1 dots, 2..17 analyser bars (top to bottom), 18..22 scope, 23 peaks
    vis = [mix(k["readout"], BLACK, 0.1), mix(k["readout"], k["readout_ink"], 0.10)]
    vis += [mix(mix(k["signal_hi"], WHITE, 0.25), k["readout_ink"], i / 9) if i < 10 else
            mix(k["readout_ink"], mix(k["signal"], k["readout"], 0.35), (i - 9) / 6) for i in range(16)]
    vis += [mix(k["readout_ink"], k["signal"], i / 4) for i in range(5)]
    vis += [mix(k["signal_hi"], WHITE, 0.5)]
    (out / "viscolor.txt").write_text("".join(f"{r},{g},{b}\n" for r, g, b in vis))
    (out / "readme.txt").write_text(f"fui skin, edition {ed}. Generated by theme/make-skin.py from the\n"
                                    f"dotfiles' tokens: run fui skin again after changing them.\n")
    return images


def main(argv):
    args = list(argv)
    ed = EDS[0]
    if "--edition" in args:
        i = args.index("--edition")
        ed = edition(args[i + 1])
        del args[i:i + 2]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    write(Path(args[0]), ed)
    print(f"wrote {args[0]} ({ed})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
