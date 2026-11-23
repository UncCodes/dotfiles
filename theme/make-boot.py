#!/usr/bin/env python3
"""Make the boot splash (Plymouth) and the text-console look. Run by `fui setup boot`.

  python3 theme/make-boot.py OUTDIR
writes
  OUTDIR/plymouth/   fui.plymouth, fui.script and images: the lattice on the dark desk, and a
                     boot window (gel title bar "[0x00] boot", the @user wordmark, an LCD
                     progress bar that fills as the system starts, a pill password field)
  OUTDIR/console/    issue (the login banner), vtrgb (the CRT palette for setvtrgb) and the
                     systemd unit that applies it
Needs Pillow; the fonts are looked up with fc-match (ProFont IIx for the title, Michroma for
the wordmark, JetBrains Mono for text).
"""
import getpass
import os
import socket
import subprocess
import sys
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TOK = tomllib.loads((HERE / "tokens.toml").read_text())
C = {**TOK["fixed"], **TOK["mode"]["dark"]}          # the splash is always the dark theme
F = TOK["font"]


def rgba(c):
    h = c.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + ((int(h[6:8], 16),) if len(h) == 8 else (255,))


def font(family, size, fallback="DejaVu Sans Mono"):
    for fam in (family, fallback):
        try:
            path = subprocess.run(["fc-match", "-f", "%{file}", fam], capture_output=True, text=True).stdout.strip()
            if path:
                return ImageFont.truetype(path, size)
        except (OSError, FileNotFoundError):
            pass
    vendored = HERE.parent / "fui/.local/share/fonts/fui/Michroma-Regular.ttf"
    if family == F["wordmark"] and vendored.exists():
        return ImageFont.truetype(str(vendored), size)
    return ImageFont.load_default()


def gel(draw, box, r):
    """The aero gel bar: four stops, top to bottom, and a highlight line along the top."""
    x0, y0, x1, y1 = box
    h = y1 - y0
    stops = [(0, rgba(C["gel_hi"])), (0.46, rgba(C["gel_mid"])), (0.54, rgba(C["gel"])), (1, rgba(C["gel_lo"]))]
    band = Image.new("RGBA", (x1 - x0, h))
    bd = ImageDraw.Draw(band)
    for y in range(h):
        t = y / max(1, h - 1)
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if a <= t <= b:
                u = (t - a) / (b - a) if b > a else 0
                bd.line([(0, y), (band.width, y)], fill=tuple(round(ca[i] + (cb[i] - ca[i]) * u) for i in range(4)))
                break
    mask = Image.new("L", band.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, band.width - 1, h - 1), radius=r, fill=255)
    draw._image.paste(band, (x0, y0), mask)
    draw.rounded_rectangle(box, radius=r, outline=rgba(C["gel_edge"]), width=1)
    draw.line([(x0 + r, y0 + 1), (x1 - r, y0 + 1)], fill=(255, 255, 255, 150))


def window(user, host):
    """The boot window: frame, gel bar, well with the wordmark and the host."""
    W, H = 520, 300
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=10, fill=rgba(C["card"])[:3] + (232,), outline=rgba(C["edge"]))
    d.line([(10, 1), (W - 10, 1)], fill=rgba(C["hi"]))
    gel(d, (5, 5, W - 6, 37), 16)
    pixel = font(F["pixel"], 18)
    d.text((22, 21), "[0x00]", font=pixel, fill=rgba(C["gel_code"]), anchor="lm")
    d.text((22 + d.textlength("[0x00] ", font=pixel), 21), "boot", font=pixel, fill=(255, 255, 255, 255), anchor="lm")
    d.line([(W - 140, 21), (W - 24, 21)], fill=(255, 255, 255, 120), width=2)
    d.rounded_rectangle((5, 42, W - 6, H - 6), radius=6, fill=rgba(C["well"])[:3] + (140,), outline=rgba(C["edge"]))
    d.text((W / 2, 112), f"@{user}", font=font(F["wordmark"], 30), fill=rgba(C["accent"]), anchor="mm")
    d.text((W / 2, 152), host, font=font(F["mono"], 15), fill=rgba(C["muted"]), anchor="mm")
    return img


def lcd(width=360, height=26):
    """The progress bar's glass (with its unlit segments) and its lit fill."""
    glass = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(glass)
    d.rounded_rectangle((0, 0, width - 1, height - 1), radius=3, fill=rgba(C["lcd_bg"]), outline=rgba(C["edge"]))
    d.line([(2, 2), (width - 3, 2)], fill=(0, 0, 0, 60))
    seg, gap = 8, 3
    for x in range(6, width - 6 - seg + 1, seg + gap):
        d.rectangle((x, 6, x + seg - 1, height - 7), fill=rgba(C["lcd_ghost"]))
    fill = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fill)
    for x in range(6, width - 6 - seg + 1, seg + gap):
        fd.rectangle((x, 6, x + seg - 1, height - 7), fill=rgba(C["lcd_ink"]))
    return glass, fill


SCRIPT = r"""// fui // Plymouth: the boot window over the lattice (made by theme/make-boot.py)
Window.SetBackgroundTopColor(%(bg)s);
Window.SetBackgroundBottomColor(%(bg)s);
sw = Window.GetWidth(); sh = Window.GetHeight();

bg = Image("background.png");
bgs = Sprite(bg.Scale(sw, sh)); bgs.SetZ(-100);

win = Image("window.png");
ws = Sprite(win); ws.SetX((sw - win.GetWidth()) / 2); ws.SetY((sh - win.GetHeight()) / 2); ws.SetZ(10);

glass = Image("lcd.png");
gs = Sprite(glass); gx = (sw - glass.GetWidth()) / 2; gy = (sh - win.GetHeight()) / 2 + 200;
gs.SetX(gx); gs.SetY(gy); gs.SetZ(20);
fill = Image("lcd-fill.png");
fs = Sprite(); fs.SetX(gx); fs.SetY(gy); fs.SetZ(21);

fun progress_cb(duration, progress) {
    w = Math.Int(glass.GetWidth() * progress);
    if (w < 1) w = 1;
    fs.SetImage(fill.Crop(0, 0, w, fill.GetHeight()));
}
Plymouth.SetBootProgressFunction(progress_cb);

// password prompt (encrypted disks): a pill field with bullets
field = Image("field.png");
fls = Sprite(); fls.SetX((sw - field.GetWidth()) / 2); fls.SetY(gy + 40); fls.SetZ(30);
dots = Sprite(); dots.SetZ(31);
prompt = Sprite(); prompt.SetZ(31);
fun password_cb(text, count) {
    fls.SetImage(field);
    p = Image.Text(text, %(muted)s, "JetBrains Mono 11");
    prompt.SetImage(p); prompt.SetX((sw - p.GetWidth()) / 2); prompt.SetY(gy + 20);
    s = ""; for (i = 0; i < count; i++) s += "* ";
    d = Image.Text(s, %(text)s, "JetBrains Mono 14");
    dots.SetImage(d); dots.SetX((sw - d.GetWidth()) / 2); dots.SetY(gy + 49);
}
Plymouth.SetDisplayPasswordFunction(password_cb);
fun normal_cb() { fls.SetOpacity(0); dots.SetOpacity(0); prompt.SetOpacity(0); }
fun shown_cb() { fls.SetOpacity(1); dots.SetOpacity(1); prompt.SetOpacity(1); }
Plymouth.SetDisplayNormalFunction(normal_cb);

msg = Sprite(); msg.SetZ(40);
fun message_cb(text) {
    m = Image.Text(text, %(muted)s, "JetBrains Mono 10");
    msg.SetImage(m); msg.SetX((sw - m.GetWidth()) / 2); msg.SetY(sh - 60);
}
Plymouth.SetMessageFunction(message_cb);
"""


def plyrgb(c):
    r, g, b, _ = rgba(c)
    return f"{r / 255:.3f}, {g / 255:.3f}, {b / 255:.3f}"


def main(out):
    out = Path(out)
    ply, con = out / "plymouth", out / "console"
    ply.mkdir(parents=True, exist_ok=True)
    con.mkdir(parents=True, exist_ok=True)
    user = os.environ.get("SUDO_USER") or getpass.getuser()
    host = socket.gethostname()

    # the background: the dark wallpaper (the lattice), rendered for a 1920x1080 splash
    wall = HERE.parent / "hypr/.config/hypr/wallpaper-dark.png"
    if wall.exists():
        Image.open(wall).convert("RGB").resize((1920, 1080), Image.LANCZOS).save(ply / "background.png")
    else:
        Image.new("RGB", (1920, 1080), rgba(C["bg"])[:3]).save(ply / "background.png")
    window(user, host).save(ply / "window.png")
    glass, fill = lcd()
    glass.save(ply / "lcd.png")
    fill.save(ply / "lcd-fill.png")
    field = Image.new("RGBA", (300, 34), (0, 0, 0, 0))
    ImageDraw.Draw(field).rounded_rectangle((0, 0, 299, 33), radius=17, fill=rgba(C["well"]), outline=rgba(C["edge"]))
    field.save(ply / "field.png")
    (ply / "fui.script").write_text(SCRIPT % {"bg": plyrgb(C["bg"]), "muted": plyrgb(C["muted"]), "text": plyrgb(C["text"])})
    (ply / "fui.plymouth").write_text(
        "[Plymouth Theme]\nName=fui\nDescription=The fui boot window over the network lattice\nModuleName=script\n\n"
        "[script]\nImageDir=/usr/share/plymouth/themes/fui\nScriptFile=/usr/share/plymouth/themes/fui/fui.script\n")

    # consoles: the CRT palette, a banner in the house style
    term = TOK["terminal"]["normal"] + TOK["terminal"]["bright"]
    term[0] = TOK["fixed"]["crt_bg"]
    chans = list(zip(*(rgba(c)[:3] for c in term)))
    (con / "vtrgb").write_text("\n".join(",".join(str(v) for v in ch) for ch in chans) + "\n")
    (con / "issue").write_text("\n\\e{green}[0x00]\\e{reset} \\e{bold}login\\e{reset}  \\e{blue}\\n\\e{reset}  \\l  \\d \\t\n\n")
    (con / "fui-vtrgb.service").write_text(
        "[Unit]\nDescription=fui: the CRT palette on the text consoles\nDefaultDependencies=no\n"
        "After=systemd-vconsole-setup.service\nBefore=getty@tty1.service\n\n"
        "[Service]\nType=oneshot\nExecStart=/usr/bin/setvtrgb -C /dev/tty1 /etc/vtrgb\nRemainAfterExit=yes\n\n"
        "[Install]\nWantedBy=multi-user.target\n")
    print(f"wrote the splash and console files into {out}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
