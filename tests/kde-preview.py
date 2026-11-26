#!/usr/bin/env python3
"""Assemble the Plasma pieces the way Plasma draws them, for design review (CI preview).

Plasma draws a frame (the window frame, the panel, a pop-up) from nine SVG elements, picked by
id and stretched. This renders each element with rsvg-convert and lays them out at a size, so
the generated themes can be looked at without a Plasma session.
Usage: python3 tests/kde-preview.py OUT.png EDITION [EDITION ...]
"""
import io
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "theme"))
import kde  # noqa: E402
from palette import E  # noqa: E402

Z = 2
NINE = ("topleft", "top", "topright", "left", "center", "right", "bottomleft", "bottom", "bottomright")


def piece(svg, eid, tmp):
    f = Path(tmp) / "p.svg"
    f.write_text(svg)
    out = subprocess.run(["rsvg-convert", "-i", eid, "-z", str(Z), str(f)], capture_output=True).stdout
    return Image.open(io.BytesIO(out)).convert("RGBA")


def frame(svg, prefix, W, H, tmp):
    pf = f"{prefix}-" if prefix else ""
    P = {k: piece(svg, pf + k, tmp) for k in NINE}
    W, H = W * Z, H * Z
    out = Image.new("RGBA", (W, H))
    lw, th = P["topleft"].size
    rw, bh = P["bottomright"].size
    for row, y, h in ((("topleft", "top", "topright"), 0, th), (("left", "center", "right"), th, H - th - bh),
                      (("bottomleft", "bottom", "bottomright"), H - bh, bh)):
        for k, x, w in zip(row, (0, lw, W - rw), (lw, W - lw - rw, rw)):
            out.alpha_composite(P[k].resize((max(1, w), max(1, h))), (x, y))
    return out


def main(out, eds):
    tiles = []
    with tempfile.TemporaryDirectory() as tmp:
        for ed in eds:
            p = E(ed)
            bg = tuple(int(p["void"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
            c = Image.new("RGBA", (1040 * Z // 2, 300 * Z // 2), (*bg, 255))
            a, d = kde.aurorae(ed), kde.desktoptheme(ed)
            c.alpha_composite(frame(a["decoration.svg"], "decoration", 300, 180, tmp), (20, 20))
            x = 20 + 300 * Z - (3 * 21 + 12) * Z
            for b in ("minimize", "maximize", "close"):
                im = piece(a[f"{b}.svg"], "active-center", tmp)
                c.alpha_composite(im, (x, 20 + 6 * Z))
                x += im.width + 3 * Z
            c.alpha_composite(frame(d["dialogs/background.svg"], "", 160, 120, tmp), (340 * Z, 20))
            c.alpha_composite(frame(d["widgets/panel-background.svg"], "south", 480, 44, tmp), (20, 220 * Z))
            tiles.append(c)
    sheet = Image.new("RGB", (tiles[0].width, sum(t.height for t in tiles)))
    y = 0
    for t in tiles:
        sheet.paste(t.convert("RGB"), (0, y))
        y += t.height
    sheet.save(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
