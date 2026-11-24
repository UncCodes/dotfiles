#!/usr/bin/env python3
"""Draw the company mark as PNGs, one per theme: fui/.local/share/fui/brand/mark-<theme>.png.

The mark: a square plate with a notched corner and three bars stepping down in length (an F
read as a falling chart line), the top bar in the theme's accent. The same geometry as
brand_mark_svg() in build.py. `fui mode` links mark.png to the current theme's file
(the lock screen and the boot splash use it).
  python3 theme/make-brand.py
"""
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
TOK = tomllib.loads((HERE / "tokens.toml").read_text())
OUT = HERE.parent / "fui/.local/share/fui/brand"


def rgb(c):
    h = c.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mark(accent, ink, size=256, S=4):
    k = size * S / 40                                    # the SVG's 40-unit grid
    img = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(2, 2), (30, 2), (38, 10), (38, 38), (2, 38)]
    d.line([(x * k, y * k) for x, y in pts + [pts[0]]], fill=(*rgb(ink), 255), width=round(2 * k), joint="curve")
    for (x, y, w, h), col in [((9, 11, 20, 4), accent), ((9, 19, 14, 4), ink), ((9, 27, 8, 4), ink)]:
        d.rectangle((x * k, y * k, (x + w) * k, (y + h) * k), fill=(*rgb(col), 255))
    return img.resize((size, size), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for m in TOK["meta"]["modes"]:
        c = TOK["mode"][m]
        mark(c["accent"], c["text"]).save(OUT / f"mark-{m}.png", optimize=True)
        print(f"wrote {OUT / f'mark-{m}.png'}")


if __name__ == "__main__":
    main()
