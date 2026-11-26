#!/usr/bin/env python3
"""Draw the fui cursor theme for an edition: chrome cursors with a gel inset.

Every pointer is a small part of the device: a chrome body (a lit face, a dark horizon, a
lighter reflection) inside a dark rim, a fine lit edge along its top, a soft shadow below,
and an inset of glossy gel in the edition's signal. Busy cursors are a ring of boxy gel keys
lighting in turn. Drawn four times over and scaled down, at 24, 32 and 48 px, and written
straight into the Xcursor format (no xcursorgen needed).

Usage:
  python3 theme/make-cursor.py [--edition E] OUTDIR     # OUTDIR/index.theme, OUTDIR/cursors/*
`fui mode` renders the current edition's theme into ~/.local/share/icons/fui-cursors-<edition>
in the background and points ~/.local/share/icons/fui at it. Needs Pillow.
"""
import math
import struct
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from palette import EDS, E, edition  # noqa: E402

SIZES = (24, 32, 48)
S = 4                                  # supersampling
U = 32                                 # shapes are drawn in a 32-unit box


def rgb(c):
    h = c.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Kit:
    def __init__(self, ed):
        p = E(ed)
        self.face = [rgb(p[k]) for k in ("face_hi", "face_mid", "face_horizon", "face_lo")]
        self.gel = [rgb(p[k]) for k in ("gel_hi", "gel_mid", "signal", "gel_lo")]
        self.bad = rgb(p["bad"])
        self.rim = rgb(p["rim"])
        self.mark = rgb(p["mark"])

    @staticmethod
    def stops(cols, t):
        """The four-stop material at t (0 top .. 1 bottom), split at the horizon."""
        hi, mid, hor, lo = cols
        if t < 0.48:
            k = t / 0.48
            return tuple(round(hi[i] + (mid[i] - hi[i]) * k) for i in range(3))
        k = (t - 0.52) / 0.48 if t > 0.52 else 0.0
        return tuple(round(hor[i] + (lo[i] - hor[i]) * k) for i in range(3))


class Canvas:
    """One cursor at one size: shapes in 32-unit coordinates, supersampled."""

    def __init__(self, size, kit):
        self.size, self.k = size, kit
        self.px = size * S
        self.f = self.px / U
        self.im = Image.new("RGBA", (self.px, self.px), (0, 0, 0, 0))

    def P(self, pts):
        return [(x * self.f, y * self.f) for x, y in pts]

    def mask(self, draw):
        m = Image.new("L", self.im.size, 0)
        draw(ImageDraw.Draw(m), self)
        return m

    def fill(self, m, cols, y0=0, y1=U):
        col = Image.new("RGB", (1, self.px))
        col.putdata([Kit.stops(cols, min(1, max(0, (y / self.f - y0) / max(1, y1 - y0)))) for y in range(self.px)])
        layer = col.resize(self.im.size).convert("RGBA")
        layer.putalpha(m)
        self.im.alpha_composite(layer)

    def paint(self, m, colour, alpha=1.0):
        layer = Image.new("RGBA", self.im.size, (*colour, 0))
        layer.putalpha(m.point(lambda v: round(v * alpha)))
        self.im.alpha_composite(layer)

    def part(self, draw, cols=None, y0=0, y1=U, rim=1.4, shadow=True):
        """A chrome (or gel) part: a soft shadow, a dark rim, the body, a lit top edge."""
        k = self.k
        m = self.mask(draw)
        if shadow:
            sh = ImageChops.offset(m, round(0.6 * self.f), round(1.2 * self.f)).filter(ImageFilter.GaussianBlur(1.1 * self.f))
            self.paint(sh, (0, 0, 0), 0.38)
        grow = m.filter(ImageFilter.MaxFilter(max(3, round(rim * self.f) // 2 * 2 + 1)))
        self.paint(grow, k.rim)
        self.fill(m, cols or k.face, y0, y1)
        # the lit edge: the body's top rim, a hair of white
        edge = ImageChops.subtract(m, ImageChops.offset(m, 0, round(0.9 * self.f)))
        self.paint(edge, (255, 255, 255), 0.55)
        return m

    def out(self):
        return self.im.resize((self.size, self.size), Image.LANCZOS)


# ── shapes (32-unit box) ────────────────────────────────────────────────
ARROW = [(3, 2), (3, 25), (8.6, 19.6), (12.6, 28.4), (16.6, 26.6), (12.6, 18.2), (20.2, 18.2)]
ARROW_GEL = [(5.6, 8.2), (5.6, 19.2), (8.8, 16.2), (11.0, 16.0), (14.2, 15.8)]


def poly(pts):
    return lambda d, c: d.polygon(c.P(pts), fill=255)


def arrow(c):
    c.part(poly(ARROW), y0=2, y1=28)
    c.part(poly(ARROW_GEL), c.k.gel, 8, 19, rim=0.8, shadow=False)


def hand(c):
    def body(d, c):
        d.rounded_rectangle(c.P([(9, 14), (24, 28)]), radius=2.5 * c.f, fill=255)       # palm
        d.rounded_rectangle(c.P([(11, 3), (15.4, 18)]), radius=2.0 * c.f, fill=255)     # the index finger
        for x in (15.6, 18.6, 21.4):                                                       # three knuckles
            d.rounded_rectangle(c.P([(x, 11.5), (x + 3.0, 18)]), radius=1.4 * c.f, fill=255)
        d.polygon(c.P([(9, 17), (5, 13.5), (4, 15.5), (9, 22.5)]), fill=255)              # the thumb
    c.part(body, y0=3, y1=28)
    c.part(lambda d, c: d.rounded_rectangle(c.P([(12.1, 4.2), (14.3, 8.6)]), radius=1.0 * c.f, fill=255),
           c.k.gel, 4, 9, rim=0.6, shadow=False)


def ibeam(c):
    def body(d, c):
        d.rectangle(c.P([(14.6, 7), (17.4, 25)]), fill=255)
        d.rounded_rectangle(c.P([(10, 4), (22, 7.4)]), radius=1.2 * c.f, fill=255)
        d.rounded_rectangle(c.P([(10, 24.6), (22, 28)]), radius=1.2 * c.f, fill=255)
    c.part(body, y0=4, y1=28)
    c.part(lambda d, c: d.rectangle(c.P([(15.4, 9), (16.6, 23)]), fill=255), c.k.gel, 9, 23, rim=0.4, shadow=False)


def spinner(c, frame, cx=16, cy=16, R=9.5, key=3.2):
    """A ring of eight boxy gel keys; the lit one travels round, the two behind it fading."""
    for i in range(8):
        a = 2 * math.pi * i / 8 - math.pi / 2
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        age = (frame - i) % 8
        box = [(x - key / 2, y - key / 2), (x + key / 2, y + key / 2)]
        m = c.part(lambda d, c, box=box: d.rounded_rectangle(c.P(box), radius=0.7 * c.f, fill=255),
                   c.k.gel if age == 0 else c.k.face, box[0][1], box[1][1], rim=0.8, shadow=False)
        if age in (1, 2):
            c.paint(m, c.k.gel[2], 0.55 if age == 1 else 0.28)


def crosshair(c):
    def body(d, c):
        d.rectangle(c.P([(15, 3), (17, 13)]), fill=255); d.rectangle(c.P([(15, 19), (17, 29)]), fill=255)
        d.rectangle(c.P([(3, 15), (13, 17)]), fill=255); d.rectangle(c.P([(19, 15), (29, 17)]), fill=255)
    c.part(body, y0=3, y1=29, rim=1.0)
    c.part(lambda d, c: d.rectangle(c.P([(14.6, 14.6), (17.4, 17.4)]), fill=255), c.k.gel, 14, 18, rim=0.6, shadow=False)


def forbidden(c):
    red = [tuple(min(255, round(v + (255 - v) * t)) for v in c.k.bad) for t in (0.45, 0.12)] + \
          [c.k.bad, tuple(round(v * 0.65) for v in c.k.bad)]
    def body(d, c):
        d.ellipse(c.P([(5, 5), (27, 27)]), fill=255)
        d.ellipse(c.P([(9, 9), (23, 23)]), fill=0)
        d.line(c.P([(9.5, 22.5), (22.5, 9.5)]), fill=255, width=round(3.2 * c.f))
    c.part(body, red, 5, 27, rim=1.0)


def double_arrow(c, angle):
    """A boxy double arrow along `angle` (degrees, 0 = left-right)."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    shape = [(-13, 0), (-7, -6), (-7, -2.2), (7, -2.2), (7, -6), (13, 0), (7, 6), (7, 2.2), (-7, 2.2), (-7, 6)]
    pts = [(16 + x * ca - y * sa, 16 + x * sa + y * ca) for x, y in shape]
    c.part(poly(pts), y0=4, y1=28)
    inner = [(16 + x * ca - y * sa, 16 + x * sa + y * ca) for x, y in ((-6, -0.9), (6, -0.9), (6, 0.9), (-6, 0.9))]
    c.part(poly(inner), c.k.gel, 14, 18, rim=0.3, shadow=False)


def move(c):
    double_arrow(c, 0)
    double_arrow(c, 90)


# name: (draw, hotspot in units, frames)
SHAPES = {
    "default": (arrow, (3, 2), 1),
    "pointer": (hand, (13, 3), 1),
    "text": (ibeam, (16, 16), 1),
    "wait": (lambda c, f: spinner(c, f), (16, 16), 8),
    "progress": (lambda c, f: (arrow(c), spinner(c, f, 23, 23, 5.2, 2.2)), (3, 2), 8),
    "crosshair": (crosshair, (16, 16), 1),
    "not-allowed": (forbidden, (16, 16), 1),
    "move": (move, (16, 16), 1),
    "ns-resize": (lambda c: double_arrow(c, 90), (16, 16), 1),
    "ew-resize": (lambda c: double_arrow(c, 0), (16, 16), 1),
    "nwse-resize": (lambda c: double_arrow(c, 45), (16, 16), 1),
    "nesw-resize": (lambda c: double_arrow(c, -45), (16, 16), 1),
}
# every name apps ask for, mapped onto the shapes (freedesktop, X11 and CSS names)
ALIASES = {
    "default": "left_ptr arrow top_left_arrow left_arrow context-menu help question_arrow whats_this copy alias "
               "dnd-move dnd-copy dnd-link dnd-ask cell vertical-text zoom-in zoom-out center_ptr",
    "pointer": "hand hand1 hand2 pointing_hand grab openhand",
    "text": "xterm ibeam",
    "wait": "watch",
    "progress": "left_ptr_watch half-busy",
    "crosshair": "cross tcross cross_reverse diamond_cross",
    "not-allowed": "crossed_circle forbidden no-drop circle dnd-none pirate",
    "move": "fleur grabbing closedhand all-scroll size_all dnd-move-all",
    "ns-resize": "n-resize s-resize size_ver sb_v_double_arrow v_double_arrow row-resize top_side bottom_side "
                 "split_v ns-resize-rtl",
    "ew-resize": "e-resize w-resize size_hor sb_h_double_arrow h_double_arrow col-resize left_side right_side split_h",
    "nwse-resize": "nw-resize se-resize size_fdiag bd_double_arrow top_left_corner bottom_right_corner",
    "nesw-resize": "ne-resize sw-resize size_bdiag fd_double_arrow top_right_corner bottom_left_corner",
}


def xcursor(images):
    """The Xcursor file: [(size, image RGBA, xhot, yhot, delay ms)]."""
    head = struct.pack("<4sIII", b"Xcur", 16, 0x10000, len(images))
    toc, chunks, pos = b"", b"", 16 + 12 * len(images)
    for size, im, xh, yh, delay in images:
        w, h = im.size
        r, g, b, a = im.split()                               # premultiplied ARGB, little-endian: B G R A bytes
        px = Image.merge("RGBA", tuple(ImageChops.multiply(ch, a) for ch in (b, g, r)) + (a,)).tobytes()
        chunk = struct.pack("<IIIIIIIII", 36, 0xFFFD0002, size, 1, w, h, xh, yh, delay) + px
        toc += struct.pack("<III", 0xFFFD0002, size, pos)
        chunks += chunk
        pos += len(chunk)
    return head + toc + chunks


def build(ed, out):
    kit = Kit(ed)
    cur = out / "cursors"
    cur.mkdir(parents=True, exist_ok=True)
    for name, (draw, (hx_, hy_), frames) in SHAPES.items():
        images = []
        for size in SIZES:
            for f in range(frames):
                c = Canvas(size, kit)
                draw(c, f) if frames > 1 else draw(c)
                images.append((size, c.out(), round(hx_ * size / U), round(hy_ * size / U), 90 if frames > 1 else 0))
        (cur / name).write_bytes(xcursor(images))
        for alias in ALIASES.get(name, "").split():
            link = cur / alias
            if link.is_symlink() or link.exists():
                link.unlink()
            link.symlink_to(name)
    (out / "index.theme").write_text(f"[Icon Theme]\nName=fui\nComment=fui cursors, edition {ed}: chrome with a gel inset\n"
                                     "Inherits=Adwaita\n")
    return out


def main(argv):
    args = list(argv)
    ed = EDS[0]
    if "--edition" in args:
        i = args.index("--edition"); ed = edition(args[i + 1]); del args[i:i + 2]
    if not args:
        print(__doc__.split("Usage:")[1].strip(), file=sys.stderr)
        return 2
    build(ed, Path(args[0]))
    print(f"wrote {args[0]} ({ed})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
