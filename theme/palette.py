"""The fui palette model, shared by theme/build.py and the image makers.

Tokens live in tokens.toml. An edition is a complete palette named for its signal colour;
E(edition) gives its roles plus the colours derived from them, T(edition, tier) the same as
drawn on a display tier (crt, lcd, deep), console(edition) its 16 ANSI colours.
"""
import colorsys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOK = tomllib.loads((HERE / "tokens.toml").read_text())
EDS = TOK["meta"]["editions"]
TIERS = TOK["meta"]["tiers"]
RENAMED = TOK["meta"].get("renamed", {})
LOOK = TOK["look"]          # the one look: what it changes beyond colour
GL = TOK["glass"]

ROLES = ["void", "floor", "panel", "raised", "well", "rule", "rule_hi", "edge", "ink", "muted", "faint",
         "signal", "signal_hi", "signal_dim", "on_signal", "counter", "ok", "warn", "bad", "info"]
CRT_SWAP = ["void", "floor", "panel", "edge", "muted", "faint", "glass", "glass_well", "glass_window", "glass_view", "shell", "shell_hi"]   # roles crt replaces
DEEP_SWAP = ["void"]


def edition(name):
    """A saved edition name, with names from earlier versions mapped to today's."""
    name = RENAMED.get(name, name)
    return name if name in EDS else EDS[0]


def backdrop_of(ed):
    """The backdrop an edition opens with (tokens.toml: its `backdrop`, the survey when absent)."""
    return TOK["edition"][ed].get("backdrop", "survey")


# ── colour helpers ──────────────────────────────────────────────────────
def parse(c):
    h = c.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
    return r, g, b, a


def hx(c):                       # "#RRGGBB" (alpha dropped)
    return c[:7].upper()


def hx8(c):                      # "#RRGGBBAA"
    r, g, b, a = parse(c)
    return f"#{r:02X}{g:02X}{b:02X}{round(a * 255):02X}"


def css(c):                      # GTK3 has no #RRGGBBAA: alpha colours become rgba()
    r, g, b, a = parse(c)
    return f"#{r:02X}{g:02X}{b:02X}" if a >= 0.999 else f"rgba({r}, {g}, {b}, {a:.3f})"


def mix(c1, c2, t):              # t of c2 into c1
    a, b = parse(c1), parse(c2)
    r, g, bl = (round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    al = a[3] + (b[3] - a[3]) * t
    return f"#{r:02X}{g:02X}{bl:02X}{round(al * 255):02X}" if al < 0.999 else f"#{r:02X}{g:02X}{bl:02X}"


def alpha(c, a):
    r, g, b, _ = parse(c)
    return f"#{r:02X}{g:02X}{b:02X}{round(a * 255):02X}"


# ── contrast (WCAG 2) ───────────────────────────────────────────────────
def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b, _ = parse(c)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def over(fg, bg):               # composite an alpha colour over an opaque one
    f, b = parse(fg), parse(bg)
    return "#" + "".join(f"{round(f[i] * f[3] + b[i] * (1 - f[3])):02X}" for i in range(3))


def contrast(fg, bg):
    l1, l2 = sorted((lum(fg), lum(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def best_on(bg):
    return max(("#000000", "#FFFFFF"), key=lambda c: contrast(c, bg))


def lift(c, need, bg, toward):
    """c moved toward `toward` just far enough to reach `need`:1 on bg."""
    for i in range(101):
        m = mix(c, toward, i / 100)
        if contrast(m, bg) >= need:
            return m
    return toward


# ── the palette model ───────────────────────────────────────────────────
def is_dark(ed):
    return TOK["edition"][ed]["scheme"] == "dark"


def E(ed):
    """An edition's roles plus the colours derived from them (lcd, the baseline)."""
    e = TOK["edition"][ed]
    p = {r: e[r] for r in ROLES}
    dark = is_dark(ed)
    p["glass"] = alpha(p["panel"], GL["panel"])
    p["glass_well"] = alpha(p["well"], GL["well"])
    p["glass_window"] = alpha(p["floor"], GL.get("window", 1.0))
    p["glass_view"] = alpha(p["well"], GL.get("window", 1.0))
    p["arc"] = alpha(p["muted"], 0.20 if dark else 0.24)     # the backdrop's contour lines
    p["bead"] = alpha(p["muted"], 0.28 if dark else 0.35)    # ...and its survey stations
    p["packet"] = alpha(p["signal"], 0.80)                   # live data travelling it
    p["bad_dim"] = mix(p["bad"], p["floor"], 0.80)
    p["on_bad"] = best_on(p["bad"])
    p["white"], p["black"] = "#FFFFFF", "#000000"
    # material roles: the device editions define the chassis and the LCD; the others derive them
    # derived chassis: dark editions get gunmetal tinted by the signal, light ones aluminium;
    # the LCD is always a dark well lit in the signal (the light editions' a deep ink)
    if dark:
        shell = mix(mix(p["panel"], "#FFFFFF", 0.16), p["signal"], 0.12)
        shell_hi = mix(shell, "#FFFFFF", 0.42)
        readout, readout_ink = mix(p["well"], "#000000", 0.4), p["signal_hi"]
    else:
        shell = mix(mix(p["floor"], "#000000", 0.18), p["signal"], 0.06)
        shell_hi = mix(p["panel"], "#FFFFFF", 0.7)
        readout, readout_ink = mix(p["ink"], p["signal"], 0.12), mix(p["signal"], "#FFFFFF", 0.6)
    p["shell"] = e.get("shell", shell)
    p["shell_hi"] = e.get("shell_hi", shell_hi)
    p["readout"] = e.get("readout", readout)
    p["readout_ink"] = e.get("readout_ink", readout_ink)
    p["readout_dim"] = alpha(p["readout_ink"], 0.14)
    p["sheen"] = alpha("#FFFFFF", 0.14 if dark else 0.70)    # a bevel's lit edge
    p["shade"] = alpha("#000000", 0.45 if dark else 0.18)    # ...and its shadow edge
    # the materials, as gradient stops (theme/make-skin.py draws the same ones):
    # chrome: a bright lip, the lit upper face, a dark horizon, a lighter reflection below
    sh, hi = p["shell"], p["shell_hi"]
    p["chrome_lip"] = mix(hi, "#FFFFFF", 0.55)                # a 1 px lit edge only: nothing is written on it
    if dark:   # gunmetal: the light ink must read on every band (checked: 4.5:1 and up, build.py)
        p["chrome_top"] = mix(sh, hi, 0.40)
        p["chrome_mid"] = mix(sh, hi, 0.15)
        p["chrome_horizon"] = mix(sh, "#000000", 0.10)
        p["chrome_low"] = mix(sh, "#000000", 0.22)
        p["chrome_reflect"] = mix(sh, hi, 0.18)
    else:      # aluminium: the dark ink reads on every band
        p["chrome_top"] = hi
        p["chrome_mid"] = mix(sh, hi, 0.45)
        p["chrome_horizon"] = mix(sh, "#000000", 0.05)
        p["chrome_low"] = mix(sh, "#000000", 0.12)
        p["chrome_reflect"] = mix(sh, hi, 0.40)
    p["shell_lo"] = mix(sh, "#000000", 0.10)
    p["rim"] = mix(sh, "#000000", 0.62)                       # the dark edge around every part
    p["tray_top"] = mix(sh, "#000000", 0.50)                  # a recess pressed into the shell
    p["tray_low"] = mix(sh, "#000000", 0.24)
    # gel: glossy glass in the signal, lit at the top, a horizon at the middle, deep below
    p["gel_hi"] = mix(p["signal"], "#FFFFFF", 0.45)
    p["gel_mid"] = mix(p["signal"], "#FFFFFF", 0.10)
    p["gel_lo"] = mix(p["signal"], "#000000", 0.30)
    p["on_gel"] = p["on_signal"]
    # the face of a chrome button
    p["face_hi"] = mix(hi, "#FFFFFF", 0.78)
    p["face_mid"] = mix(hi, "#FFFFFF", 0.18)
    p["face_horizon"] = mix(sh, hi, 0.50)
    p["face_lo"] = mix(sh, "#FFFFFF", 0.30)
    p["mark"] = mix(sh, "#000000", 0.74)                      # text and glyphs printed on chrome
    p["mark_off"] = mix(p["mark"], p["face_mid"], 0.45)       # ...on a disabled key: dimmer, still legible
    p["source"] = mix(p["panel"], p["signal"], 0.07 if dark else 0.10)   # a source list beside the content
    p["chrome_ink_off"] = lift(mix(p["ink"], p["chrome_mid"], 0.45), 4.5, p["chrome_mid"], p["ink"])   # an unfocused title
    p["emboss"] = alpha("#000000", 0.55) if dark else alpha("#FFFFFF", 0.65)   # a text shadow that lifts type off chrome
    return p


def T(ed, tier):
    """The edition as drawn on one display tier."""
    p = E(ed)
    if tier == "crt":
        p.update(TOK["edition"][ed]["crt"])
        p["glass"] = alpha(p["panel"], GL["panel"])           # glass on a tube too, over its darker panel
        p["glass_well"] = alpha(p["well"], GL["well"])
        p["glass_window"] = alpha(p["floor"], GL.get("window", 1.0))
        p["glass_view"] = alpha(p["well"], GL.get("window", 1.0))
    elif tier == "deep":
        p["void"] = TOK["edition"][ed]["deep"].get("void", p["void"])
    return p


def variants(ed):
    """The extra named colours the tier overlays switch to: <role>_crt and <role>_deep."""
    c, dp = T(ed, "crt"), T(ed, "deep")
    v = {f"{r}_crt": c[r] for r in CRT_SWAP}
    v.update({f"{r}_deep": dp[r] for r in DEEP_SWAP})
    return v


def full(ed):
    return {**E(ed), **variants(ed)}


def hue(c):
    r, g, b, _ = parse(c)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360, s


VIOLET = "#B78CFF"


def console(ed):
    """The terminal: 16 ANSI colours mapped from the roles, so every program inherits the
    edition. Light editions keep a dark console (the first edition's)."""
    src = ed if is_dark(ed) else EDS[0]
    p = E(src)
    bg, white = p["floor"], "#FFFFFF"
    counter = p["counter"]
    h, s = hue(counter)
    near = any(min(abs(h - hue(p[k])[0]), 360 - abs(h - hue(p[k])[0])) < 30 for k in ("ok", "warn", "bad", "info", "signal"))
    if s < 0.2 or near:            # the counter colour is taken (or grey): a neutral violet instead
        counter = VIOLET
    br = lambda c: lift(mix(c, white, 0.28), 4.5, bg, white)
    normal = [p["raised"], p["bad"], p["ok"], p["warn"], p["info"], counter, p["signal"], p["ink"]]
    bright = [lift(p["faint"], 4.5, bg, p["ink"]), br(p["bad"]), br(p["ok"]), br(p["warn"]), br(p["info"]),
              br(counter), p["signal_hi"], mix(p["ink"], white, 0.5)]
    return {"source": src, "bg": bg, "fg": p["ink"], "panel": p["panel"], "raised": p["raised"],
            "signal": p["signal"], "on_signal": p["on_signal"], "signal_dim": p["signal_dim"],
            "dim": bright[0], "bright": bright[7], "ansi": normal + bright}
