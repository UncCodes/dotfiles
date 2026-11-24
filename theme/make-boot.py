#!/usr/bin/env python3
"""Make the boot splash (Plymouth) and the text-console look. Run by `fui setup boot`.

  python3 theme/make-boot.py OUTDIR
writes
  OUTDIR/plymouth/   fui.plymouth, fui.script and images: the company network on the night
                     floor, the brand mark and name, a slim accent progress line that fills as
                     the system starts, a status line, and a passphrase field when one is asked
  OUTDIR/console/    issue (the sign-in banner), vtrgb (the console palette for setvtrgb) and
                     the systemd unit that applies it
Needs Pillow; fonts are looked up with fc-match (Michroma, Inter, JetBrains Mono).
"""
import subprocess
import sys
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TOK = tomllib.loads((HERE / "tokens.toml").read_text())
C = {**TOK["fixed"], **TOK["mode"]["night"]}         # the splash is always the night theme
BR = TOK["brand"]
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
    if family == F["brand"] and vendored.exists():
        return ImageFont.truetype(str(vendored), size)
    return ImageFont.load_default()


def masthead():
    """The centre of the splash: the mark, the company, the division, a status line."""
    W, H = 640, 260
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    mark_png = HERE.parent / "fui/.local/share/fui/brand/mark-night.png"
    if mark_png.exists():
        m = Image.open(mark_png).convert("RGBA").resize((64, 64), Image.LANCZOS)
        img.alpha_composite(m, ((W - 64) // 2, 10))
    d.text((W / 2, 112), BR["name"], font=font(F["brand"], 26), fill=rgba(C["text"]), anchor="mm")
    d.text((W / 2, 146), BR["division"], font=font(F["ui"] + ":semibold", 12), fill=rgba(C["muted"]), anchor="mm")
    d.text((W / 2, 236), "INITIALIZING WORKSTATION", font=font(F["mono"], 12), fill=rgba(C["faint"]), anchor="mm")
    return img


def track(width=360, height=4):
    """The progress line: a hairline track and its accent fill."""
    t = Image.new("RGBA", (width, height), rgba(C["line"]))
    f = Image.new("RGBA", (width, height), rgba(C["accent"]))
    return t, f


SCRIPT = r"""// fui // Plymouth: the company masthead over the network (made by theme/make-boot.py)
Window.SetBackgroundTopColor(%(bg)s);
Window.SetBackgroundBottomColor(%(bg)s);
sw = Window.GetWidth(); sh = Window.GetHeight();

bg = Image("background.png");
bgs = Sprite(bg.Scale(sw, sh)); bgs.SetZ(-100);

win = Image("masthead.png");
ws = Sprite(win); ws.SetX((sw - win.GetWidth()) / 2); ws.SetY((sh - win.GetHeight()) / 2); ws.SetZ(10);

glass = Image("track.png");
gs = Sprite(glass); gx = (sw - glass.GetWidth()) / 2; gy = (sh - win.GetHeight()) / 2 + 196;
gs.SetX(gx); gs.SetY(gy); gs.SetZ(20);
fill = Image("track-fill.png");
fs = Sprite(); fs.SetX(gx); fs.SetY(gy); fs.SetZ(21);

fun progress_cb(duration, progress) {
    w = Math.Int(glass.GetWidth() * progress);
    if (w < 1) w = 1;
    fs.SetImage(fill.Crop(0, 0, w, fill.GetHeight()));
}
Plymouth.SetBootProgressFunction(progress_cb);

// passphrase prompt (encrypted disks): a field with bullets
field = Image("field.png");
fls = Sprite(); fls.SetX((sw - field.GetWidth()) / 2); fls.SetY(gy + 52); fls.SetZ(30);
dots = Sprite(); dots.SetZ(31);
prompt = Sprite(); prompt.SetZ(31);
fun password_cb(text, count) {
    fls.SetImage(field);
    p = Image.Text(text, %(muted)s, "JetBrains Mono 11");
    prompt.SetImage(p); prompt.SetX((sw - p.GetWidth()) / 2); prompt.SetY(gy + 28);
    s = ""; for (i = 0; i < count; i++) s += "* ";
    d = Image.Text(s, %(text)s, "JetBrains Mono 14");
    dots.SetImage(d); dots.SetX((sw - d.GetWidth()) / 2); dots.SetY(gy + 61);
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

    # the background: the night backdrop (the network), rendered for a 1920x1080 splash
    wall = HERE.parent / "hypr/.config/hypr/wallpaper-night.png"
    if wall.exists():
        Image.open(wall).convert("RGB").resize((1920, 1080), Image.LANCZOS).save(ply / "background.png")
    else:
        Image.new("RGB", (1920, 1080), rgba(C["bg"])[:3]).save(ply / "background.png")
    masthead().save(ply / "masthead.png")
    t, f = track()
    t.save(ply / "track.png")
    f.save(ply / "track-fill.png")
    field = Image.new("RGBA", (300, 36), (0, 0, 0, 0))
    ImageDraw.Draw(field).rounded_rectangle((0, 0, 299, 35), radius=4, fill=rgba(C["well"]), outline=rgba(C["line_hi"]))
    field.save(ply / "field.png")
    (ply / "fui.script").write_text(SCRIPT % {"bg": plyrgb(C["bg"]), "muted": plyrgb(C["muted"]), "text": plyrgb(C["text"])})
    (ply / "fui.plymouth").write_text(
        "[Plymouth Theme]\nName=fui\nDescription=The fui company masthead over the network\nModuleName=script\n\n"
        "[script]\nImageDir=/usr/share/plymouth/themes/fui\nScriptFile=/usr/share/plymouth/themes/fui/fui.script\n")

    # consoles: the console palette, a sign-in banner
    term = TOK["terminal"]["normal"] + TOK["terminal"]["bright"]
    term[0] = TOK["fixed"]["term_bg"]
    chans = list(zip(*(rgba(c)[:3] for c in term)))
    (con / "vtrgb").write_text("\n".join(",".join(str(v) for v in ch) for ch in chans) + "\n")
    (con / "issue").write_text(f"\n\\e{{cyan}}{BR['name']}\\e{{reset}}  {BR['division']}\n"
                               f"\\e{{bold}}NODE\\e{{reset}} \\n   \\e{{bold}}TERMINAL\\e{{reset}} \\l   \\d \\t\n"
                               f"{BR['notice']}\n\n")
    (con / "fui-vtrgb.service").write_text(
        "[Unit]\nDescription=fui: the console palette on the text consoles\nDefaultDependencies=no\n"
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
