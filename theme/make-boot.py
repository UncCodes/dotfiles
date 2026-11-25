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
from palette import EDS, LOOK, TOK, T, alpha, console, edition, is_dark, contrast, look_of  # noqa: E402
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


# ReGreet's clock: a frame.background hung from the top edge. Newer ReGreet classes it
# widget-clock; the released one (0.5) doesn't, so it is also picked out by its place in the
# overlay (the background picture, the sign-in panel, then the clock).
CLOCK = "frame.widget-clock, overlay > frame.background:nth-child(3)"
CLOCK_LABEL = "frame.widget-clock label, overlay > frame.background:nth-child(3) label"


def greeter_css(C, ed, tier="lcd", H=1080):
    """ReGreet (GTK4) in the edition's look.

    ReGreet's widgets (src/gui/templates.rs): the sign-in panel is `frame.background` (a grid
    with 15 px margins: the greeting, User and Session rows, Cancel and Login); the clock is
    `frame.background.widget-clock`, hung from the top edge; the notice bar sits in a plain
    `frame` above the Reboot and Power Off buttons (`button.destructive-action`). Only the two
    `.background` frames are panels: the plain one must stay invisible."""
    base = f"""/* fui // the login screen (ReGreet), edition {ed} ({look_of(ed)}). Made by theme/make-boot.py. */
window, window.background {{ background-color: {C['floor']}; color: {C['ink']}; font-family: "{F['ui']}", "{F['mono']}"; }}
picture {{ opacity: 1; }}
frame:not(.background) {{ background: none; border: none; box-shadow: none; padding: 0; }}
frame.background > grid > label {{ color: {C['ink']}; }}
.error, label.error {{ color: {C['bad']}; }}
"""
    return base + (greeter_y2k(C, ed) if look_of(ed) == "y2k" else greeter_instrument(C)) + greeter_fit(look_of(ed), tier, H)


def greeter_fit(look, tier, H):
    """The screen the login screen lands on. On a tube, nothing touches an edge: the clock and
    the Reboot / Power Off row keep the tier's safe inset (the glass curves and the edges
    overscan), and the clock becomes a whole plate instead of hanging from the top edge. On a
    short screen (768 lines and under, a 17-inch tube at 1024x768) the type and the controls
    step down so the panel doesn't crowd it."""
    out = ""
    inset = round(H * TOK["tier"][tier]["inset"])
    if inset:
        r = LOOK["y2k"]["shell"] if look == "y2k" else 4
        out += f"""/* ── a tube: the safe inset ({inset} px) ── */
{CLOCK} {{ margin-top: {inset}px; border-top-width: 1px; border-radius: {r}px; }}
overlay > box {{ margin-bottom: {inset}px; }}
"""
    if H <= 800:
        out += f"""/* ── a short screen ── */
window, window.background {{ font-size: 10pt; }}
{CLOCK_LABEL} {{ font-size: 24px; }}
entry, password-entry, button, combobox button {{ min-height: 28px; }}
"""
    return out


def greeter_instrument(C):
    """A glass panel with the signal stripe, hairline fields, the clock in the brand face."""
    return f"""frame.background {{
  background-color: {alpha(C['panel'], 0.80)}; border: 1px solid {C['rule_hi']}; border-radius: 4px;
  box-shadow: inset 3px 0 {C['signal']}; padding: 4px 8px;
}}
{CLOCK} {{ box-shadow: none; padding: 6px 24px; }}
{CLOCK_LABEL} {{ font-family: "{F['brand']}"; font-size: 30px; color: {C['ink']}; }}
entry, password-entry, combobox button, button {{
  background-color: {C['well']}; color: {C['ink']}; border: 1px solid {C['edge']}; border-radius: 2px;
  box-shadow: none; min-height: 32px; background-image: none;
}}
entry:focus-within, password-entry:focus-within {{ border-color: {C['signal']}; box-shadow: inset 0 0 0 1px {C['signal']}; }}
button:hover {{ background-color: {C['raised']}; border-color: {C['signal']}; }}
button.suggested-action {{ background-color: {C['signal']}; color: {C['on_signal']}; border-color: {C['signal']}; font-weight: 700; }}
button.suggested-action:hover {{ background-color: {C['signal_hi']}; }}
button.destructive-action {{ background-color: transparent; color: {C['bad']}; border-color: {C['bad']}; }}
popover > contents {{ background-color: {C['panel']}; border: 1px solid {C['rule_hi']}; border-top: 2px solid {C['signal']}; border-radius: 4px; }}
popover modelbutton:hover, popover row:selected {{ background-color: {C['signal_dim']}; box-shadow: inset 3px 0 {C['signal']}; }}
infobar > revealer > box {{ background-color: {C['bad_dim']}; color: {C['ink']}; border-radius: 2px; }}
"""


def greeter_y2k(C, ed):
    """The welcome screen of an owned device: a rounded shell under a chrome title strip that
    carries the greeting, fields pressed into the shell as pills, chrome capsule buttons, gel on
    Login, the clock in a lit readout hung from the top edge."""
    L = LOOK["y2k"]
    sh = L["shadow_dark"] if is_dark(ed) else L["shadow_light"]
    # the greeting on the strip: whichever of ink and the maker's mark reads better on its face,
    # embossed the other way
    title = max((C["ink"], C["mark"]), key=lambda c: contrast(c, C["chrome_mid"]))
    title_emboss = alpha("#000000", 0.5) if title == C["ink"] else alpha(C["face_hi"], 0.7)
    r = L["shell"]
    lens = "radial-gradient(ellipse at 50% 0%, alpha(white, {a}), alpha(white, 0) 62%)"
    # the title strip is the top 50 px of the panel: the greeting's row (15 px margin, the
    # label, 15 px below it); a lit lip, the face, the horizon, a lighter reflection. The lip
    # is kept short so the greeting (15-34 px) sits on the face and below it, never on the lit band
    strip = (f"linear-gradient(to bottom, {C['chrome_lip']} 0px, {C['shell_hi']} 2px, {C['chrome_mid']} 13px, {C['chrome_mid']} 24px, "
             f"{C['chrome_horizon']} 26px, {C['chrome_low']} 44px, {C['chrome_reflect']} 49px, {C['rim']} 49px, "
             f"{C['rim']} 50px, transparent 50px)")
    body = f"linear-gradient(to bottom, {C['shell_hi']}, {C['shell']} 90px, {C['shell']} 70%, {C['shell_lo']})"
    face = (f"{lens.format(a=0.6)}, linear-gradient(to bottom, {C['face_hi']}, {C['face_mid']} 48%, "
            f"{C['face_horizon']} 52%, {C['face_lo']})")
    face_hover = (f"{lens.format(a=0.85)}, linear-gradient(to bottom, {C['face_hi']}, {C['face_hi']} 30%, "
                  f"{C['face_horizon']} 52%, {C['face_mid']})")
    pressed = f"linear-gradient(to bottom, {C['face_horizon']}, {C['face_mid']})"
    gel = (f"{lens.format(a=0.85)}, linear-gradient(to bottom, {C['gel_hi']}, {C['gel_mid']} 48%, "
           f"{C['signal']} 52%, {C['gel_lo']})")
    ease = "cubic-bezier({}, {}, {}, {})".format(*L["glide"])
    drop = f"0 {L['shadow_y']}px {L['shadow_blur']}px alpha(black, {sh})"
    lcd = L["font_lcd"]
    cr = L["control"] + 1                               # the controls' radius: fields, lists, rows
    return f"""/* ── the shell ── */
frame.background {{
  background-color: {C['shell']};
  background-image: {strip}, {body};
  border: 1px solid {C['rim']}; border-radius: {r}px; padding: 0 6px 4px;
  box-shadow: {drop}, inset 0 1px {C['sheen']};
}}
/* the greeting rides the title strip, embossed */
frame.background > grid > label:first-child {{ color: {title}; text-shadow: 0 1px {title_emboss}; }}
frame.background > grid > label {{ color: {C['ink']}; text-shadow: 0 1px {C['emboss']}; }}

/* ── the clock: a lit readout hung from the top edge ── */
{CLOCK} {{
  background-color: {C['readout']}; background-image: linear-gradient(to bottom, alpha(white, 0.07), alpha(white, 0) 45%);
  border: 1px solid {C['rim']}; border-top-width: 0; border-radius: 0 0 {r}px {r}px; padding: 8px 26px 10px;
  box-shadow: {drop}, inset 0 -1px {C['sheen']}, inset 0 0 0 3px {C['shell']}, inset 0 0 0 4px {C['rim']};
}}
{CLOCK_LABEL} {{
  font-family: "{lcd}", "{F['mono']}"; font-size: 30px; color: {C['readout_ink']};
  text-shadow: 0 0 6px {alpha(C['readout_ink'], 0.65)}, 0 0 1px {C['readout_ink']};
}}

/* ── fields: pressed into the shell, with the controls' small radius (fields hold content) ── */
entry, password-entry {{
  background-color: {C['well']}; color: {C['ink']}; caret-color: {C['signal']};
  border: 1px solid {C['rim']}; border-radius: {cr}px; min-height: 34px; padding: 0 12px;
  box-shadow: inset 0 2px 3px alpha(black, 0.35), 0 1px {C['sheen']};
}}
entry:focus-within, password-entry:focus-within {{
  box-shadow: inset 0 2px 3px alpha(black, 0.35), 0 0 0 2px {alpha(C['signal'], 0.55)};
}}
password-entry text, entry text {{ background: none; }}

/* ── buttons: standalone push buttons are chrome capsules; the User and Session lists hold
      content, so they take the fields' radius; the icon-only toggles are round ── */
button, combobox button {{
  background-color: transparent; background-image: {face};
  color: {C['mark']}; text-shadow: 0 1px {alpha(C['face_hi'], 0.6)};
  border: 1px solid {C['rim']}; border-radius: 99px; min-height: 32px; padding: 0 16px;
  box-shadow: 0 1px 2px alpha(black, 0.35);
  transition: box-shadow 90ms {ease};
}}
combobox button {{ padding: 0 10px 0 12px; border-radius: {cr}px; }}
button image, combobox button arrow {{ color: {C['mark']}; -gtk-icon-shadow: none; }}
button:hover {{ background-image: {face_hover}; box-shadow: 0 0 0 2px {alpha(C['signal'], 0.40)}, 0 1px 2px alpha(black, 0.35); }}
button:active, button:checked {{ background-image: {pressed}; box-shadow: inset 0 2px 3px alpha(black, 0.40); }}
button:disabled {{ background-image: none; background-color: {alpha(C['face_mid'], 0.5)}; color: {alpha(C['mark'], 0.5)}; box-shadow: none; }}
grid > button {{ min-width: 32px; padding: 0; border-radius: 99px; }}
button.suggested-action {{
  background-image: {gel}; border-color: {C['gel_lo']}; color: {C['on_gel']}; text-shadow: none; font-weight: 700;
  box-shadow: 0 0 8px {alpha(C['signal'], 0.5)}, 0 1px 2px alpha(black, 0.35);
}}
button.suggested-action:hover {{ background-image: {gel}; box-shadow: 0 0 12px {alpha(C['signal'], 0.7)}, 0 1px 2px alpha(black, 0.35); }}
button.suggested-action:active {{ box-shadow: inset 0 2px 3px alpha(black, 0.40); }}
/* Reboot and Power Off: capsules like the rest; the danger shows on hover */
button.destructive-action {{ min-width: 96px; }}
button.destructive-action:hover {{ box-shadow: 0 0 0 2px {alpha(C['bad'], 0.55)}, 0 1px 2px alpha(black, 0.35); }}

/* ── the lists that drop from User and Session ── */
popover > contents {{
  background-color: {C['shell']}; background-image: linear-gradient(to bottom, {C['shell_hi']}, {C['shell']} 24px);
  border: 1px solid {C['rim']}; border-radius: {L['radius']}px; padding: 4px; box-shadow: {drop};
}}
popover modelbutton, popover row {{ color: {C['ink']}; border-radius: {cr}px; padding: 4px 12px; }}
popover modelbutton:hover, popover row:hover, popover row:selected {{
  background-image: {gel}; color: {C['on_gel']}; text-shadow: none;
}}

/* ── the notice: a small readout ── */
infobar > revealer > box {{
  background-color: {C['readout']}; color: {C['readout_ink']}; border: 1px solid {C['rim']};
  border-radius: {L['radius']}px; box-shadow: inset 0 2px 3px alpha(black, 0.5);
}}
infobar.error > revealer > box {{ color: {C['bad']}; }}
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
    (gre / "regreet.css").write_text(greeter_css(C, ed, tier, H))
    dark = is_dark(ed)
    scheme = TOK["desktop"]["dark" if dark else "light"]
    greeting = f"Welcome to {HOST}" if look_of(ed) == "y2k" else f"{ic('auth')}  {HOST.upper()} · {NOTICE}"
    (gre / "regreet.toml").write_text(f"""# fui // the login screen (ReGreet), edition {ed}. Made by theme/make-boot.py.
[background]
path = "/usr/share/fui/greeter/background.png"
fit = "Cover"

[GTK]
application_prefer_dark_theme = {str(dark).lower()}
cursor_theme_name = "{TOK['desktop']['cursor_theme']}"
font_name = "{F['ui']} {10 if H <= 800 else 11}"
icon_theme_name = "{scheme['icon_theme']}"
theme_name = "{scheme['gtk_base']}"

[commands]
reboot = ["systemctl", "reboot"]
poweroff = ["systemctl", "poweroff"]

[appearance]
greeting_msg = "{greeting}"

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
