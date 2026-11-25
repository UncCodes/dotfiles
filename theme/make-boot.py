#!/usr/bin/env python3
"""Make the boot splash (Plymouth), the login screen (greetd + ReGreet) and the console look.
Run by `fui setup boot`, for the edition and display tier in use.

  python3 theme/make-boot.py [--edition E] [--tier T] [--size WxH] OUTDIR
writes
  OUTDIR/plymouth/   fui.plymouth, fui.script and images. The splash fades in the edition's
                     survey field and the machine's masthead (the distribution's logo, the
                     host, the OS), while traces of signal run along the contours; a 4 px
                     progress line fills as the system starts; a passphrase field when asked
  OUTDIR/greeter/    the login screen: config.toml (greetd: cage running ReGreet on vt1),
                     regreet.toml, regreet.css (a glass panel in the edition) and background.png
  OUTDIR/console/    issue (the sign-in banner), vtrgb (the console palette for setvtrgb) and
                     the systemd unit that applies it
Needs Pillow; fonts are looked up with fc-match (Michroma, Inter, JetBrains Mono Nerd Font).
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from palette import EDS, TOK, T, alpha, console, edition, is_dark  # noqa: E402
from survey import walk  # noqa: E402

_spec = importlib.util.spec_from_file_location("make_wallpaper", HERE / "make-wallpaper.py")
WALL = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(WALL)


def os_release():
    """(name, id) of the distribution, read on the machine."""
    vals = {}
    try:
        for line in open("/etc/os-release"):
            k, _, v = line.strip().partition("=")
            vals[k] = v.strip('"')
    except OSError:
        pass
    return vals.get("NAME", "Linux"), vals.get("ID", "")


LOGOS = {"endeavouros": "\uf322", "arch": "\uf303", "manjaro": "\uf312", "fedora": "\uf30a",
         "debian": "\uf306", "ubuntu": "\uf31b"}
OS_NAME, OS_ID = os_release()
try:
    HOST = open("/etc/hostname").read().strip() or "workstation"
except OSError:
    HOST = "workstation"
NOTICE = TOK["workstation"]["notice"]
F = TOK["font"]
ICONS = TOK["icons"]
ic = lambda n: chr(int(ICONS[n], 16))  # noqa: E731


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


def masthead(C):
    """The centre of the splash: the distribution's logo, the host, the OS, a status line."""
    W, H = 640, 260
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((W / 2, 46), LOGOS.get(OS_ID, "\uf17c"), font=font(F["mono"], 56), fill=rgba(C["signal"]), anchor="mm")
    d.text((W / 2, 112), HOST.upper(), font=font(F["brand"], 26), fill=rgba(C["ink"]), anchor="mm")
    d.text((W / 2, 146), OS_NAME.upper(), font=font(F["mono"], 12), fill=rgba(C["muted"]), anchor="mm")
    d.text((W / 2, 236), "STARTING WORKSTATION", font=font(F["mono"], 12), fill=rgba(C["muted"]), anchor="mm")
    return img


def dot(colour, size=7, S=4):
    """One link of a trace: a soft point in the signal."""
    n = size * S
    big = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ImageDraw.Draw(big).ellipse((S, S, n - S, n - S), fill=rgba(colour)[:3] + (255,))
    return big.resize((size, size), Image.LANCZOS)


SCRIPT = r"""// fui // Plymouth: the machine's masthead over the survey field, traces running along its
// contours (made by theme/make-boot.py; the routes are in 1920x1080 screen units)
Window.SetBackgroundTopColor(%(bg)s);
Window.SetBackgroundBottomColor(%(bg)s);
sw = Window.GetWidth(); sh = Window.GetHeight();
kx = sw / 1920; ky = sh / 1080;

bg = Image("background.png");
bgs = Sprite(bg.Scale(sw, sh)); bgs.SetZ(-100); bgs.SetOpacity(0);

win = Image("masthead.png");
ws = Sprite(win); ws.SetX((sw - win.GetWidth()) / 2); ws.SetY((sh - win.GetHeight()) / 2); ws.SetZ(10); ws.SetOpacity(0);

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

// the traces: TRAIL points per trace, each a step further back along its route and dimmer
%(routes)s
TRAIL = 9;
link = Image("dot.png");
for (r = 0; r < R; r++) {
    for (k = 0; k < TRAIL; k++) {
        TS[r * TRAIL + k] = Sprite(link);
        TS[r * TRAIL + k].SetZ(5);
        TS[r * TRAIL + k].SetOpacity(0);
    }
}

global.tick = 0;
fun refresh_cb() {
    global.tick = global.tick + 1;
    tick = global.tick;
    // the field and the masthead fade in over the first second and a half
    f = tick / 75; if (f > 1) f = 1;
    bgs.SetOpacity(f); ws.SetOpacity(f);
    for (r = 0; r < R; r++) {
        for (k = 0; k < TRAIL; k++) {
            p = tick * SPD[r] + PH[r] - k * 0.55;
            p = p - Math.Int(p / N) * N;
            if (p < 0) p = p + N;
            i = Math.Int(p);
            j = i + 1; if (j >= N) j = 0;
            u = p - i;
            x = RX[r * N + i] + (RX[r * N + j] - RX[r * N + i]) * u;
            y = RY[r * N + i] + (RY[r * N + j] - RY[r * N + i]) * u;
            TS[r * TRAIL + k].SetX(x * kx - 3);
            TS[r * TRAIL + k].SetY(y * ky - 3);
            TS[r * TRAIL + k].SetOpacity(f * (1 - k / TRAIL) * (1 - k / TRAIL) * VIS[r]);
        }
    }
}
Plymouth.SetRefreshFunction(refresh_cb);

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
Plymouth.SetDisplayNormalFunction(normal_cb);

msg = Sprite(); msg.SetZ(40);
fun message_cb(text) {
    m = Image.Text(text, %(muted)s, "JetBrains Mono 10");
    msg.SetImage(m); msg.SetX((sw - m.GetWidth()) / 2); msg.SetY(sh - 60);
}
Plymouth.SetMessageFunction(message_cb);
"""


def routes(scene, n=96):
    """The survey's trace routes as point lists in screen units, sampled evenly."""
    out = []
    for pts, closed, v, ph in scene.art["packets"]:
        samples = [scene.xy(*walk(pts, k / (n if closed else n - 1))) for k in range(n)]
        speed = n / (WALL.SPEEDS[v] * 50)          # route points per frame at 50 frames a second
        out.append((samples, speed, ph / 10 * n, 1.0 if closed else 0.6))
    lines = [f"N = {n}; R = {len(out)};"]
    for r, (samples, speed, ph, vis) in enumerate(out):
        lines.append(f"SPD[{r}] = {speed:.4f}; PH[{r}] = {ph:.1f}; VIS[{r}] = {vis};")
        lines.append(" ".join(f"RX[{r * n + k}] = {x:.0f}; RY[{r * n + k}] = {y:.0f};" for k, (x, y) in enumerate(samples)))
    return "\n".join(lines)


def plyrgb(c):
    r, g, b, _ = rgba(c)
    return f"{r / 255:.3f}, {g / 255:.3f}, {b / 255:.3f}"


def greeter_css(C, ed):
    """ReGreet (GTK4): a glass panel in the edition over its survey field."""
    i = lambda n: ic(n)  # noqa: E731
    return f"""/* fui // the login screen (ReGreet), edition {ed}. Made by theme/make-boot.py. */
window, window.background {{ background-color: {C['floor']}; color: {C['ink']}; font-family: "{F['ui']}", "{F['mono']}"; }}
picture {{ opacity: 1; }}
frame, frame > border {{
  background-color: {alpha(C['panel'], 0.80)}; border: 1px solid {C['rule_hi']}; border-radius: 4px;
  box-shadow: inset 3px 0 {C['signal']}; padding: 20px 24px;
}}
label {{ color: {C['ink']}; }}
label.title, .title {{ font-family: "{F['brand']}"; letter-spacing: 2px; }}
label.dim-label, .dim-label {{ color: {C['muted']}; }}
entry, password-entry, dropdown > button, combobox > box > button, button {{
  background-color: {C['well']}; color: {C['ink']}; border: 1px solid {C['edge']}; border-radius: 2px;
  box-shadow: none; min-height: 32px;
}}
entry:focus-within, password-entry:focus-within {{ border-color: {C['signal']}; box-shadow: inset 0 0 0 1px {C['signal']}; }}
button:hover {{ background-color: {C['raised']}; border-color: {C['signal']}; }}
button.suggested-action {{ background-color: {C['signal']}; color: {C['on_signal']}; border-color: {C['signal']}; font-weight: 700; }}
button.suggested-action:hover {{ background-color: {C['signal_hi']}; }}
button.destructive-action {{ background-color: transparent; color: {C['bad']}; border-color: {C['bad']}; }}
popover > contents, popover.menu > contents {{ background-color: {C['panel']}; border: 1px solid {C['rule_hi']}; border-top: 2px solid {C['signal']}; border-radius: 4px; }}
row:selected, modelbutton:hover {{ background-color: {C['signal_dim']}; box-shadow: inset 3px 0 {C['signal']}; }}
.error, label.error {{ color: {C['bad']}; }}
infobar, infobar > revealer > box {{ background-color: {C['bad_dim']}; color: {C['ink']}; border-radius: 2px; }}
/* the clock */
.clock, label.clock {{ font-family: "{F['brand']}"; font-size: 40px; color: {C['ink']}; }}
/* icons come from the Nerd Font: {i('lock')} {i('operator')} {i('session')} */
"""


def main(argv):
    args = list(argv)

    def opt(name, default):
        if name in args:
            k = args.index(name)
            val = args[k + 1]
            del args[k:k + 2]
            return val
        return default
    ed = edition(opt("--edition", EDS[0]))
    tier = opt("--tier", "lcd")
    W, H = (int(v) for v in opt("--size", "1920x1080").split("x"))
    if len(args) != 1:
        print(__doc__)
        return 2
    out = Path(args[0])
    C = T(ed, tier)
    ply, con, gre = out / "plymouth", out / "console", out / "greeter"
    for d in (ply, con, gre):
        d.mkdir(parents=True, exist_ok=True)

    # the splash: the survey field without its traces (the script moves them), 1920x1080
    scene = WALL.Scene(ed, 1920, 1080, tier)
    scene.still().convert("RGB").save(ply / "background.png")
    masthead(C).save(ply / "masthead.png")
    Image.new("RGBA", (360, 4), rgba(C["rule"])).save(ply / "track.png")
    Image.new("RGBA", (360, 4), rgba(C["signal"])).save(ply / "track-fill.png")
    dot(C["signal"]).save(ply / "dot.png")
    field = Image.new("RGBA", (300, 36), (0, 0, 0, 0))
    ImageDraw.Draw(field).rounded_rectangle((0, 0, 299, 35), radius=2, fill=rgba(C["well"]), outline=rgba(C["edge"]))
    field.save(ply / "field.png")
    (ply / "fui.script").write_text(SCRIPT % {"bg": plyrgb(C["floor"]), "muted": plyrgb(C["muted"]),
                                              "text": plyrgb(C["ink"]), "routes": routes(scene)})
    (ply / "fui.plymouth").write_text(
        "[Plymouth Theme]\nName=fui\nDescription=The machine's masthead over the survey field\nModuleName=script\n\n"
        "[script]\nImageDir=/usr/share/plymouth/themes/fui\nScriptFile=/usr/share/plymouth/themes/fui/fui.script\n")

    # the login screen: greetd runs ReGreet in cage on the first console
    WALL.render_still(ed, gre / "background.png", W, H, tier)
    (gre / "regreet.css").write_text(greeter_css(C, ed))
    dark = is_dark(ed)
    scheme = TOK["desktop"]["dark" if dark else "light"]
    (gre / "regreet.toml").write_text(f"""# fui // the login screen (ReGreet), edition {ed}. Made by theme/make-boot.py.
[background]
path = "/usr/share/fui/greeter/background.png"
fit = "Cover"

[GTK]
application_prefer_dark_theme = {str(dark).lower()}
cursor_theme_name = "{TOK['desktop']['cursor_theme']}"
font_name = "{F['ui']} 11"
icon_theme_name = "{scheme['icon_theme']}"
theme_name = "{scheme['gtk_base']}"

[commands]
reboot = ["systemctl", "reboot"]
poweroff = ["systemctl", "poweroff"]

[appearance]
greeting_msg = "{ic('auth')}  {HOST.upper()} · {NOTICE}"

[widget.clock]
format = "%H:%M"
resolution = "500ms"
label_width = 160
""")
    (gre / "config.toml").write_text("""# fui // greetd: the login screen on the first console (made by theme/make-boot.py)
[terminal]
vt = 1

[default_session]
command = "cage -s -m last -- regreet"
user = "greeter"
""")

    # consoles: the console palette, a sign-in banner
    cons = console(ed)
    term = list(cons["ansi"])
    term[0] = cons["bg"]
    chans = list(zip(*(rgba(c)[:3] for c in term)))
    (con / "vtrgb").write_text("\n".join(",".join(str(v) for v in ch) for ch in chans) + "\n")
    (con / "issue").write_text(f"\n\\e{{cyan}}\\n\\e{{reset}}  \\S{{NAME}}\n"
                               f"\\e{{bold}}TERMINAL\\e{{reset}} \\l   \\e{{bold}}KERNEL\\e{{reset}} \\r   \\d \\t\n"
                               f"{NOTICE}\n\n")
    (con / "fui-vtrgb.service").write_text(
        "[Unit]\nDescription=fui: the console palette on the text consoles\nDefaultDependencies=no\n"
        "After=systemd-vconsole-setup.service\nBefore=getty@tty1.service\n\n"
        "[Service]\nType=oneshot\nExecStart=/usr/bin/setvtrgb -C /dev/tty1 /etc/vtrgb\nRemainAfterExit=yes\n\n"
        "[Install]\nWantedBy=multi-user.target\n")
    print(f"wrote the splash, login screen and console files into {out} ({ed}, {tier})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
