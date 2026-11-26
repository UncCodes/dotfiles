#!/usr/bin/env bash
# fui // tests
#
# Runs on Arch Linux as a normal user with sudo (GitHub Actions does this in an
# archlinux container on every push; see .github/workflows/check.yml).
#   bash tests/run.sh            lint + install + checks (installs packages: use a VM/container)
#   bash tests/run.sh --lint     only the checks that change nothing
set -uo pipefail

DOTS="${DOTFILES_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
export DOTFILES_DIR="$DOTS"
lint_only=0; [ "${1:-}" = --lint ] && lint_only=1

# No desktop session here: point D-Bus nowhere, so gsettings, notify-send and friends fail
# at once instead of waiting to autolaunch a bus and services. Run inside a live desktop, the
# tests must not reload Hyprland or restart the bar (that once left a second bar running):
# forget the session, and put the edition and tier back at the end.
export DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent/bus"
unset HYPRLAND_INSTANCE_SIGNATURE WAYLAND_DISPLAY
ST="${XDG_STATE_HOME:-$HOME/.local/state}/fui"
orig_mode=$(cat "$ST/mode" 2>/dev/null); orig_display=$(cat "$ST/display" 2>/dev/null)
restore() {
  [ -x "$HOME/.local/bin/fui" ] || return 0
  [ -n "$orig_mode" ] && "$HOME/.local/bin/fui" mode "$orig_mode" --quiet >/dev/null 2>&1
  [ -n "$orig_display" ] && "$HOME/.local/bin/fui" display "$orig_display" >/dev/null 2>&1
  "$HOME/.local/bin/fui" alert off >/dev/null 2>&1
  return 0
}
trap restore EXIT

pass=0; fail=0
t() {   # t "name" command...: run one check, at most 10 minutes
  local name="$1"; shift
  local out rc began
  began=$(date +%s)
  if command -v timeout >/dev/null; then out=$(timeout 600 "$@" 2>&1); else out=$("$@" 2>&1); fi; rc=$?
  local took=$(( $(date +%s) - began ))
  if [ "$rc" = 0 ]; then
    pass=$((pass + 1)); printf '  [pass] %s (%ss)\n' "$name" "$took"
  else
    fail=$((fail + 1))
    [ "$rc" = 124 ] && printf '  [FAIL] %s (timed out after %ss)\n' "$name" "$took" || printf '  [FAIL] %s (%ss)\n' "$name" "$took"
    printf '%s\n' "$out" | tail -n 25 | sed 's/^/         /'
  fi
}
listed() { sed -e 's/#.*//' -e 's/[[:space:]]//g' "$1" | grep -v '^$'; }

# ── checks that change nothing ──────────────────────────────────────────
echo "LINT"
SCRIPTS=("$DOTS/install.sh" "$DOTS/user_commands.bash" "$DOTS/fui/.local/bin/fui" "$DOTS/tests/run.sh")
t "bash syntax" bash -c 'for f in "$@"; do bash -n "$f" || exit 1; done' _ "${SCRIPTS[@]}"
if command -v shellcheck >/dev/null; then
  t "shellcheck" shellcheck -S warning "${SCRIPTS[@]}"
fi
if command -v luacheck >/dev/null; then
  t "luacheck" luacheck --config "$DOTS/.luacheckrc" "$DOTS/hypr/.config/hypr" "$DOTS/nvim/.config/nvim"
fi
EDITIONS=$(python3 -c 'import tomllib,sys; print(" ".join(tomllib.load(open(sys.argv[1],"rb"))["meta"]["editions"]))' "$DOTS/theme/tokens.toml")
if command -v lua >/dev/null; then
  for m in $EDITIONS night; do
    for tier in crt lcd deep; do
      t "hyprland.lua runs: edition $m, tier $tier (startup included)" bash -c '
        h=$(mktemp -d); mkdir -p "$h/.config/hypr" "$h/.local/state/fui"
        cp "$1/hypr/.config/hypr/fui.lua" "$h/.config/hypr/"; echo "$2" > "$h/.local/state/fui/mode"; echo "$3" > "$h/.local/state/fui/tier"
        HOME="$h" XDG_STATE_HOME="$h/.local/state" lua "$1/tests/hyprland-mock.lua" "$1/hypr/.config/hypr/hyprland.lua"' _ "$DOTS" "$m" "$tier"
    done
  done
  t "hyprland.lua: the alert takeover lights the window's chrome frame bad" bash -c '
    h=$(mktemp -d); mkdir -p "$h/.config/hypr" "$h/.local/state/fui"
    cp "$1/hypr/.config/hypr/fui.lua" "$h/.config/hypr/"; echo on > "$h/.local/state/fui/alert"; echo slate > "$h/.local/state/fui/mode"
    HOME="$h" XDG_STATE_HOME="$h/.local/state" FUI_EXPECT_BORDER=FF5C6C lua "$1/tests/hyprland-mock.lua" "$1/hypr/.config/hypr/hyprland.lua"' _ "$DOTS"
  t "hyprland.lua runs without its token file (the fallback)" bash -c '
    h=$(mktemp -d); HOME="$h" XDG_STATE_HOME="$h/st" lua "$1/tests/hyprland-mock.lua" "$1/hypr/.config/hypr/hyprland.lua"' _ "$DOTS"
fi
t "theme build is current, contrast passes" python3 "$DOTS/theme/build.py" --check
t "Qt stylesheets have no // (qt6ct strips it as a comment)" bash -c '! grep -l "//" "$1"/theme/templates/*.qss.in' _ "$DOTS"
t "every edition has every per-edition file" bash -c '
  for e in $2; do
    for f in waybar/.config/waybar/colors-$e.css swaync/.config/swaync/colors-$e.css swayosd/.config/swayosd/colors-$e.css \
             rofi/.config/rofi/colors-$e.rasi hypr/.config/hypr/colors-$e.conf kitty/.config/kitty/colors-$e.conf \
             kitty/.config/kitty/console-$e.conf gtk/.config/gtk-3.0/fui-$e.css gtk/.config/gtk-4.0/fui-$e.css \
             qt/.config/qt6ct/colors/fui-$e.conf theme/templates/fui-$e.qss.in fui/.config/fui/firefox/colors-$e.css \
             btop/.config/btop/themes/fui-$e.theme mpv/.config/mpv/colors-$e.conf zathura/.config/zathura/colors-$e \
             imv/.config/imv/config-$e satty/.config/satty/config-$e.toml; do
      [ -s "$1/$f" ] || { echo "missing $f"; exit 1; }
    done
  done' _ "$DOTS" "$EDITIONS"
t "the look has its layer for the bar, notices, OSD, launcher and lock screen" bash -c '
  for f in waybar/.config/waybar/look.css swaync/.config/swaync/look.css swayosd/.config/swayosd/look.css \
           rofi/.config/rofi/look.rasi hypr/.config/hypr/lock-look.conf; do
    [ -s "$1/$f" ] || { echo "missing $f"; exit 1; }
  done' _ "$DOTS"
t "one corner language: boxy (no pills or circles but radios and LEDs; panels 4 px at most)" bash -c '
  ! grep -nE "border-radius: *(99|[5-9]|[1-9][0-9])px" "$1"/waybar/.config/waybar/look.css "$1"/swaync/.config/swaync/look.css \
      "$1"/swayosd/.config/swayosd/look.css "$1"/rofi/.config/rofi/look.rasi "$1"/theme/templates/start.html.in &&
  ! grep -nE "rounding = ([5-9]|[1-9][0-9]|-1)" "$1"/hypr/.config/hypr/lock-look.conf &&
  [ "$(grep -c "border-radius: 99px" "$1"/gtk/.config/gtk-4.0/fui-cyan.css)" -le 1 ]' _ "$DOTS"
t "the type is the instrument'"'"'s: no pixel or segment faces anywhere" bash -c '
  ! git -C "$1" grep -n -i -E "silkscreen|dseg" -- . ":!CYBERCORE.md" ":!tests"' _ "$DOTS"
t "the bar meters round down (100 icons, full only at 99 and up)" python3 -c '
import json, re, sys
m = json.loads(re.sub(r"^\s*//.*$", "", open(sys.argv[1]).read(), flags=re.M))
icons = m["pulseaudio"]["format-icons"]["default"]
assert len(icons) == 100, len(icons)
assert icons[19].count("█") == 0 and icons[20].count("█") == 1 and icons[98].count("█") == 4 and icons[99].count("░") == 0
' "$DOTS/waybar/.config/waybar/meters.jsonc"
t "waybar configs parse" python3 -c '
import json, re, sys
for f in sys.argv[1:]:
    json.loads(re.sub(r"^\s*//.*$", "", open(f).read(), flags=re.M))
' "$DOTS"/waybar/.config/waybar/*.jsonc

# Every file under a stow folder must be in git, or the machine never gets it
# (a .gitignore rule once hid every script this way).
t "no ignored files inside the stow folders" bash -c '
  cd "$1" || exit 1
  [ -d .git ] || exit 0
  ignored=$(git ls-files --others --ignored --exclude-standard -- $(sed -e "s/#.*//" stow.txt) | grep -v "\.DS_Store$")
  [ -z "$ignored" ] || { echo "ignored by .gitignore:"; echo "$ignored"; exit 1; }' _ "$DOTS"

t "every package exists in the official repos" bash -c '
  command -v pacman >/dev/null || { echo "no pacman: skipped"; exit 0; }
  missing=""
  for p in $(sed -e "s/#.*//" -e "s/[[:space:]]//g" "$1/packages.txt" | grep -v "^$"); do
    pacman -Si "$p" >/dev/null 2>&1 || missing="$missing $p"
  done
  [ -z "$missing" ] || { echo "not found:$missing"; exit 1; }' _ "$DOTS"


wallpaper_checks() {   # needs Pillow (and ffmpeg for the loop), which the install provides
  python3 -c "import PIL" 2>/dev/null || { echo "  [skip] wallpaper renders (no Pillow)"; return; }
  t "still wallpaper renders (cyan lcd, amber deep, paper crt), a different survey per edition" bash -c '
    python3 "$1/theme/make-wallpaper.py" /tmp/fui-test.png 320 180 &&
    python3 "$1/theme/make-wallpaper.py" --edition amber /tmp/fui-test-amber.png 320 180 &&
    ! cmp -s /tmp/fui-test.png /tmp/fui-test-amber.png &&
    python3 "$1/theme/make-wallpaper.py" --edition amber --tier deep /tmp/fui-test-deep.png 320 180 &&
    python3 "$1/theme/make-wallpaper.py" --edition concrete --tier crt /tmp/fui-test-crt.png 320 180' _ "$DOTS"
  t "any backdrop renders in any edition (--scene): the ribbon in cyan, the survey in ruby" bash -c '
    python3 "$1/theme/make-wallpaper.py" --edition cyan --scene ribbon /tmp/fui-test-cr.png 320 180 &&
    python3 "$1/theme/make-wallpaper.py" --edition cyan /tmp/fui-test-cs.png 320 180 &&
    ! cmp -s /tmp/fui-test-cr.png /tmp/fui-test-cs.png &&
    python3 "$1/theme/make-wallpaper.py" --edition ruby --scene survey /tmp/fui-test-rs.png 320 180 &&
    ! python3 "$1/theme/make-wallpaper.py" --scene nope /tmp/fui-test-x.png 320 180 2>/dev/null' _ "$DOTS"
  t "the ribbon renders: a ribbon of light, its own per edition" bash -c '
    python3 "$1/theme/make-wallpaper.py" --edition slate /tmp/fui-test-slate.png 320 180 &&
    python3 "$1/theme/make-wallpaper.py" --edition ice --tier crt /tmp/fui-test-ice.png 320 180 &&
    ! cmp -s /tmp/fui-test-slate.png /tmp/fui-test-ice.png &&
    python3 -c "import sys; sys.path.insert(0, sys.argv[1] + \"/theme\"); import importlib.util as u
s = u.spec_from_file_location(\"w\", sys.argv[1] + \"/theme/make-wallpaper.py\"); w = u.module_from_spec(s); s.loader.exec_module(w)
sc = w.Scene(\"ruby\", 320, 180, scene=\"ribbon\"); a, b, c = sc.frame(0), sc.frame(14), sc.frame(56)
assert list(a.getdata()) != list(b.getdata()), \"the ribbon does not move\"
assert list(a.getdata()) == list(c.getdata()), \"the loop is not seamless at 56 s\"" "$1"' _ "$DOTS"
  t "the four figures of light render, move and loop seamlessly (helix orbit fibre mesh)" bash -c '
    python3 -c "import sys; sys.path.insert(0, sys.argv[1] + \"/theme\"); import importlib.util as u
s = u.spec_from_file_location(\"w\", sys.argv[1] + \"/theme/make-wallpaper.py\"); w = u.module_from_spec(s); s.loader.exec_module(w)
import lights
for name in (\"helix\", \"orbit\", \"fibre\", \"mesh\"):
    sc = w.Scene(\"amber\", 320, 180, scene=name); a, b, c = sc.frame(0), sc.frame(7), sc.frame(56)
    assert list(a.getdata()) != list(b.getdata()), name + \" does not move\"
    assert list(a.getdata()) == list(c.getdata()), name + \" does not loop at 56 s\"
    assert sc.packets() == [] and lights.svg(name, \"amber\").startswith(\"<svg\")
" "$1"' _ "$DOTS"
  t "the player skin renders: every bitmap the classic format needs, at its size" bash -c '
    for e in slate cyan; do
      rm -rf /tmp/fui-skin && python3 "$1/theme/make-skin.py" --edition $e /tmp/fui-skin >/dev/null || exit 1
      python3 -c "
import sys
from PIL import Image
sizes = {\"main\": (275, 116), \"titlebar\": (344, 87), \"cbuttons\": (136, 36), \"shufrep\": (92, 85), \"text\": (155, 18),
         \"numbers\": (99, 13), \"nums_ex\": (108, 13), \"playpaus\": (42, 9), \"monoster\": (58, 24), \"posbar\": (307, 10),
         \"volume\": (68, 433), \"balance\": (68, 433), \"eqmain\": (275, 315), \"pledit\": (280, 186)}
for n, sz in sizes.items():
    im = Image.open(f\"/tmp/fui-skin/{n}.bmp\")
    assert im.size == sz, f\"{n}.bmp is {im.size}, expected {sz}\"
vis = open(\"/tmp/fui-skin/viscolor.txt\").read().split()
assert len(vis) == 24, \"viscolor.txt needs 24 colours\"
assert \"[Text]\" in open(\"/tmp/fui-skin/pledit.txt\").read()
" || exit 1
    done' _ "$DOTS"
  if command -v ffmpeg >/dev/null; then
    t "live wallpaper renders" python3 "$DOTS/theme/make-wallpaper.py" --live --edition phosphor --seconds 1 /tmp/fui-test.mp4 320 240
  fi
}

if [ "$lint_only" = 1 ]; then
  wallpaper_checks
  printf '\n%s passed, %s failed\n' "$pass" "$fail"; [ "$fail" = 0 ]; exit
fi

# ── install for real ────────────────────────────────────────────────────
echo; echo "INSTALL"
t "install.sh --ci" bash "$DOTS/install.sh" --ci
t "install.sh again (safe to repeat)" bash "$DOTS/install.sh" --ci --no-packages

echo; echo "AFTER INSTALL"
t "every stowed file is linked" bash -c '
  bad=0
  for pkg in $(sed -e "s/#.*//" -e "s/[[:space:]]//g" "$1/stow.txt" | grep -v "^$"); do
    while IFS= read -r f; do
      rel="${f#"$1/$pkg/"}"
      [ "$(readlink -f "$HOME/$rel")" = "$(readlink -f "$f")" ] || { echo "not linked: ~/$rel"; bad=1; }
    done < <(find "$1/$pkg" -type f)
  done
  exit $bad' _ "$DOTS"
t "fui runs from ~/.local/bin" "$HOME/.local/bin/fui" help
t "fui is on the default PATH" env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/bin HOME="$HOME" bash -c 'command -v fui && fui help >/dev/null'
# Hyprland wants a runtime folder even just to check the config; containers have none
XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-$(mktemp -d)}"; chmod 700 "$XDG_RUNTIME_DIR"; export XDG_RUNTIME_DIR
t "Hyprland --verify-config" Hyprland --verify-config
LINKS="waybar/fui-colors.css waybar/fui-tier.css waybar/fui-alert.css rofi/fui-colors.rasi rofi/fui-tier.rasi swaync/fui-colors.css swaync/fui-tier.css swaync/fui-alert.css swayosd/fui-colors.css swayosd/fui-tier.css hypr/fui-colors.conf hypr/fui-tier.conf kitty/fui-colors.conf kitty/fui-console.conf kitty/fui-tier.conf gtk-3.0/fui-mode.css gtk-3.0/fui-tier.css gtk-4.0/fui-mode.css gtk-4.0/fui-tier.css btop/themes/fui.theme mpv/fui-colors.conf zathura/fui-colors imv/config satty/config.toml"
t "edition and tier links in place" bash -c 'for l in $1; do [ -e "$HOME/.config/$l" ] || { echo "missing ~/.config/$l"; exit 1; }; done' _ "$LINKS"
for m in $EDITIONS; do
  t "switch to $m" bash -c '"$HOME/.local/bin/fui" mode "$1" --quiet &&
    [ "$("$HOME/.local/bin/fui" mode status)" = "$1" ] &&
    [ "$(readlink "$HOME/.config/kitty/fui-colors.conf")" = "colors-$1.conf" ] &&
    [ "$(readlink "$HOME/.config/kitty/fui-console.conf")" = "console-$1.conf" ] &&
    [ "$(readlink "$HOME/.config/gtk-4.0/fui-mode.css")" = "fui-$1.css" ] &&
    [ "$(readlink "$HOME/.config/btop/themes/fui.theme")" = "fui-$1.theme" ] &&
    [ "$(readlink "$HOME/.config/imv/config")" = "config-$1" ] &&
    grep -q "fui-$1.conf" "$HOME/.config/qt6ct/qt6ct.conf" &&
    grep -q "data-theme=\"$1\"" "$HOME/.local/share/fui/start.html"' _ "$m"
done
t "all twelve editions cycle in order and wrap" bash -c 'f="$HOME/.local/bin/fui"; set -- $1; first=$1; "$f" mode "$first" --quiet
  for want in "${@:2}" "$first"; do "$f" mode toggle --quiet; [ "$("$f" mode status)" = "$want" ] || { echo "expected $want, got $("$f" mode status)"; exit 1; }; done' _ "$EDITIONS"
t "links from the two looks are cleared (the stowed labwc rc stays)" bash -c 'f="$HOME/.local/bin/fui"
  ln -sfn look-y2k.css "$HOME/.config/waybar/fui-look.css" && "$f" mode apply --quiet &&
  [ ! -e "$HOME/.config/waybar/fui-look.css" ] && [ ! -L "$HOME/.config/waybar/fui-look.css" ] && [ -s "$HOME/.config/labwc/rc.xml" ]'
t "fui skin draws the player skin for the edition and points Audacious at it" bash -c 'f="$HOME/.local/bin/fui"
  "$f" mode slate --quiet && FUI_SKIN_ALWAYS=1 "$f" skin apply --quiet &&
  [ -s "$HOME/.local/share/fui/skin/main.bmp" ] && [ "$(readlink "$HOME/.local/share/fui/skin")" = "$HOME/.local/share/fui/skins/slate" ] &&
  grep -qx "skin=$HOME/.local/share/fui/skin" "$HOME/.config/audacious/config" && "$f" mode cyan --quiet' 
t "a saved name from an earlier version still works (night is cyan)" bash -c '
  echo night > "$1/mode"; [ "$("$HOME/.local/bin/fui" mode status)" = cyan ] && "$HOME/.local/bin/fui" mode concrete --quiet && [ "$("$HOME/.local/bin/fui" mode status)" = paper ]' _ "$ST"
for tier in crt lcd deep; do
  t "display tier $tier" bash -c '"$HOME/.local/bin/fui" display "$1" >/dev/null &&
    [ "$(cat "$2/tier")" = "$1" ] &&
    [ "$(readlink "$HOME/.config/waybar/fui-tier.css")" = "tier-$1.css" ] &&
    [ "$(readlink "$HOME/.config/gtk-3.0/fui-tier.css")" = "fui-tier-$1.css" ] &&
    [ "$(readlink "$HOME/.config/kitty/fui-tier.conf")" = "tier-$1.conf" ] &&
    grep -q "data-display=\"$1\"" "$HOME/.local/share/fui/start.html"' _ "$tier" "$ST"
done
t "display tier auto resolves to one of crt, lcd, deep" bash -c '"$HOME/.local/bin/fui" display auto >/dev/null && grep -qxE "crt|lcd|deep" "$1/tier" && "$HOME/.local/bin/fui" display status' _ "$ST"
t "the lock clock moves only on crt and deep" bash -c 'f="$HOME/.local/bin/fui"
  "$f" display lcd >/dev/null; [ "$("$f" lockclock)" = "$(date +%H:%M)" ] || exit 1
  "$f" display crt >/dev/null; "$f" lockclock | grep -qE "^ *[0-9]{2}:[0-9]{2} *$"; r=$?; "$f" display auto >/dev/null; exit $r'
t "the alert takeover links on and off" bash -c 'f="$HOME/.local/bin/fui"
  "$f" alert on FAULT test >/dev/null 2>&1; [ "$(readlink "$HOME/.config/waybar/fui-alert.css")" = alert-on.css ] && [ "$("$f" alert status)" = on ] &&
  "$f" alert off >/dev/null 2>&1; [ "$(readlink "$HOME/.config/waybar/fui-alert.css")" = alert-off.css ] && [ "$("$f" alert status)" = off ]'
t "a second wallpaper change never waits on the first (the backdrop follows the edition)" bash -c '
  fake=$(mktemp -d); printf "#!/bin/bash\nwhile :; do sleep 1; done\n" > "$fake/swaybg"; chmod +x "$fake/swaybg"
  f="$HOME/.local/bin/fui"
  PATH="$fake:$PATH" "$f" mode amber --quiet
  PATH="$fake:$PATH" timeout 120 "$f" wallpaper still || { echo "the first change did not finish"; exit 1; }
  PATH="$fake:$PATH" "$f" mode phosphor --quiet
  PATH="$fake:$PATH" timeout 120 "$f" wallpaper still || { echo "the second change hung"; exit 1; }
  ls "${XDG_CACHE_HOME:-$HOME/.cache}"/fui/still-mesh-phosphor-* >/dev/null || { echo "no phosphor still"; exit 1; }
  pkill -x swaybg; rm -rf "$fake"'
t "the backdrop can be chosen apart from the edition: the ribbon behind amber, and back" bash -c '
  fake=$(mktemp -d); printf "#!/bin/bash\nwhile :; do sleep 1; done\n" > "$fake/swaybg"; chmod +x "$fake/swaybg"
  f="$HOME/.local/bin/fui"; c="${XDG_CACHE_HOME:-$HOME/.cache}/fui"
  PATH="$fake:$PATH" "$f" mode amber --quiet
  PATH="$fake:$PATH" "$f" wallpaper ribbon >/dev/null 2>&1; PATH="$fake:$PATH" timeout 120 "$f" wallpaper still
  ls "$c"/still-ribbon-amber-* >/dev/null || { echo "no ribbon behind amber"; exit 1; }
  [ "$("$f" wallpaper status)" = "still ribbon" ] || { echo "status: $("$f" wallpaper status)"; exit 1; }
  PATH="$fake:$PATH" "$f" wallpaper auto >/dev/null 2>&1; [ "$("$f" wallpaper status)" = "still auto" ] || exit 1
  pkill -x swaybg; rm -rf "$fake"'
t "idle steps do nothing on lcd" bash -c 'f="$HOME/.local/bin/fui"; "$f" display lcd >/dev/null; "$f" idle dim && "$f" idle wake; r=$?; "$f" display auto >/dev/null; exit $r'
t "key list reads hyprland.lua" bash -c '"$HOME/.local/bin/fui" keys --text | grep -q "command palette"'
t "the fui sound theme is installed" test -f "$HOME/.local/share/sounds/fui/stereo/desktop-login.oga"
t "fonts: Michroma, Inter, JetBrains Mono" bash -c 'fc-list | grep -q Michroma && fc-list | grep -q "Inter" && fc-list | grep -q "JetBrainsMono Nerd"'
t "the data face carries every icon in tokens.toml [icons]" bash -c '
  for cp in $(python3 -c "import tomllib,sys; print(\" \".join(tomllib.load(open(sys.argv[1],\"rb\"))[\"icons\"].values()))" "$1/theme/tokens.toml"); do
    fc-list ":family=JetBrainsMono Nerd Font:charset=$cp" | grep -q . || { echo "JetBrainsMono Nerd Font lacks U+$cp"; exit 1; }
  done' _ "$DOTS"
t "the data face carries every glyph the bar and shell use (█ ░ ■ ▌ ⏻ ·)" bash -c '
  for cp in 2588 2591 25a0 258c 23fb b7; do
    fc-list ":family=JetBrainsMono Nerd Font:charset=$cp" | grep -q . || { echo "JetBrainsMono Nerd Font lacks U+$cp"; exit 1; }
  done'
t "no institution's name anywhere the operator looks" bash -c '! grep -rIl "FUI SYSTEMS\|WORKSTATION DIVISION" "$1" --exclude-dir=.git --exclude-dir=tests --exclude=CYBERCORE.md' _ "$DOTS"
t "fui brand names the machine (host · OS · operator)" bash -c '"$HOME/.local/bin/fui" brand | grep -q "$(cat /etc/hostname 2>/dev/null || uname -n)"'
t "the bar badge shows the distribution logo and the operator" bash -c '"$HOME/.local/bin/fui" brand --badge | grep -q "Nerd Font.*  $(id -un)$"'
t "boot splash, login screen and consoles render (and the splash animates its traces)" bash -c '
  rm -rf /tmp/fui-boot-test && python3 "$1/theme/make-boot.py" --edition amber --size 1024x768 /tmp/fui-boot-test &&
  for f in plymouth/fui.script plymouth/background.png plymouth/dot.png greeter/config.toml greeter/regreet.toml greeter/regreet.css greeter/background.png console/issue; do
    [ -s "/tmp/fui-boot-test/$f" ] || { echo "missing $f"; exit 1; }
  done
  grep -q "SetRefreshFunction" /tmp/fui-boot-test/plymouth/fui.script && grep -q "regreet" /tmp/fui-boot-test/greeter/config.toml' _ "$DOTS"
t "labwc: a theme per edition (themerc and square gel keys) and one rc, all well formed" bash -c '
  for d in "$1"/labwc/.local/share/themes/fui-*/openbox-3; do
    [ -s "$d/themerc" ] || { echo "no themerc in $d"; exit 1; }
    for b in iconify max max_toggled close; do for v in "" _hover; do for s in active inactive; do
      [ -s "$d/$b$v-$s.svg" ] || { echo "missing $d/$b$v-$s.svg"; exit 1; }
    done; done; done
  done
  [ "$(ls -d "$1"/labwc/.local/share/themes/fui-* | wc -l)" -eq "$(python3 -c "import tomllib,sys; print(len(tomllib.load(open(sys.argv[1],\"rb\"))[\"meta\"][\"editions\"]))" "$1/theme/tokens.toml")" ] || exit 1
  python3 -c "
import sys, xml.dom.minidom as m, glob
for f in glob.glob(sys.argv[1] + \"/labwc/.config/labwc/*.xml\") + glob.glob(sys.argv[1] + \"/labwc/.local/share/themes/*/openbox-3/*.svg\"):
    m.parse(f)
" "$1"
  [ "$(readlink "$HOME/.local/share/themes/fui")" = "fui-$("$HOME/.local/bin/fui" mode status)" ] || { echo "the labwc theme link does not follow the edition"; exit 1; }' _ "$DOTS"
t "rofi themes put no @reference inside linear-gradient() (rofi rejects it)" bash -c '
  ! grep -n "linear-gradient([^)]*@" "$1"/rofi/.config/rofi/*.rasi' _ "$DOTS"
t "the login screen wears the look, and styles only ReGreet's two panels" bash -c '
  for e in cyan slate; do
    rm -rf "/tmp/fui-gre-$e" && python3 "$1/theme/make-boot.py" --edition "$e" --size 800x600 "/tmp/fui-gre-$e" >/dev/null || exit 1
    css="/tmp/fui-gre-$e/greeter/regreet.css"
    grep -q "frame:not(.background) { background: none; border: none" "$css" || { echo "$e: the notice frame is styled as a panel"; exit 1; }
    grep -q "frame.widget-clock" "$css" || { echo "$e: no clock rules"; exit 1; }
  done
  grep -q "the shell" /tmp/fui-gre-cyan/greeter/regreet.css && ! grep -q "border-radius: 99px" /tmp/fui-gre-slate/greeter/regreet.css &&
  grep -q "Welcome to" /tmp/fui-gre-slate/greeter/regreet.toml &&
  ! grep -q "safe inset" /tmp/fui-gre-slate/greeter/regreet.css || { echo "no inset expected on an 800x600 lcd"; exit 1; }
  # on a tube at 1024x768 (a 17-inch CRT behind an adapter) nothing touches an edge, and the type steps down
  rm -rf /tmp/fui-gre-crt && python3 "$1/theme/make-boot.py" --edition slate --tier crt --size 1024x768 /tmp/fui-gre-crt >/dev/null &&
  grep -q "the safe inset (23 px)" /tmp/fui-gre-crt/greeter/regreet.css &&
  grep -q "a short screen" /tmp/fui-gre-crt/greeter/regreet.css &&
  grep -q "Inter 10" /tmp/fui-gre-crt/greeter/regreet.toml' _ "$DOTS"
if command -v nvim >/dev/null; then
  t "Neovim config loads (plugins install)" bash -c 'timeout 300 nvim --headless "+Lazy! sync" +qa >/dev/null 2>&1; timeout 60 nvim --headless -c "lua if vim.g.colors_name ~= [[fui]] then os.exit(1) end; require([[telescope]])" -c qa'
fi
t "fui doctor runs to the end" bash -c '"$HOME/.local/bin/fui" doctor > /tmp/doctor.txt 2>&1; grep -q "ok, .* warnings, .* problems" /tmp/doctor.txt || { cat /tmp/doctor.txt; exit 1; }'
wallpaper_checks
t "zsh loads the shell config" zsh -ic 'echo "$LS_COLORS" | grep -q "di=" && command -v starship >/dev/null'

printf '\n%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" = 0 ]
