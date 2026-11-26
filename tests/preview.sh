#!/usr/bin/env bash
# fui // preview: screenshots of the real apps, for design review
#
# Runs after `install.sh --ci` (GitHub Actions does it; see .github/workflows/check.yml).
# X11 shots under Xvfb: GTK3 and GTK4 widget factories, qt6ct, rofi, kitty, and the Firefox
# start page, in every edition. Then it tries a headless Hyprland session (waybar, the
# wallpaper, windows, the launcher, the login screen) and screenshots that with grim.
# Writes ~/preview/*.png. Never fails the build: a shot that can't be taken is skipped.
set -u
OUT="$HOME/preview"; mkdir -p "$OUT"
DOTFILES_DIR="${DOTFILES_DIR:-$HOME/.dotfiles}"
FUI="$HOME/.local/bin/fui"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-$(mktemp -d)}"; chmod 700 "$XDG_RUNTIME_DIR"
export LIBGL_ALWAYS_SOFTWARE=1 GSK_RENDERER=cairo NO_AT_BRIDGE=1
export DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent/bus"   # no session: nothing waits on D-Bus
T() { timeout "$@"; }   # every step has a time limit

Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &
XVFB=$!
export DISPLAY=:99
sleep 2

shot_x() {   # shot_x <name> <seconds> <command...>: run a program, screenshot the screen, close it
  local name="$1" wait="$2"; shift 2
  timeout 40 "$@" >"$OUT/$name.log" 2>&1 &
  local pid=$!
  sleep "$wait"
  T 20 import -window root "$OUT/$name.png" 2>/dev/null && echo "  shot $name" || echo "  no shot: $name"
  kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
  [ -s "$OUT/$name.log" ] || rm -f "$OUT/$name.log"
}

EDITIONS=$(python3 -c 'import tomllib,sys; print(" ".join(tomllib.load(open(sys.argv[1],"rb"))["meta"]["editions"]))' "$DOTFILES_DIR/theme/tokens.toml")
light() { case "$1" in paper|lab) return 0 ;; *) return 1 ;; esac; }
T 30 "$FUI" display lcd
for m in $EDITIONS; do
  T 30 "$FUI" mode "$m" --quiet
  base=adw-gtk3-dark; light "$m" && base=adw-gtk3
  echo "edition: $m"
  shot_x "$m-gtk3" 5 env GDK_BACKEND=x11 GTK_THEME="$base" gtk3-widget-factory
  shot_x "$m-gtk4" 6 env GDK_BACKEND=x11 gtk4-widget-factory
  shot_x "$m-qt" 4 env QT_QPA_PLATFORM=xcb QT_QPA_PLATFORMTHEME=qt6ct qt6ct
  shot_x "$m-rofi" 3 rofi -config "$HOME/.config/rofi/config.rasi" -show drun
  T 90 firefox --headless --window-size=1280,800 --screenshot "$OUT/$m-start.png" "file://$HOME/.local/share/fui/start.html" \
    >/dev/null 2>&1 && echo "  shot $m-start" || echo "  no shot: $m-start"
done
T 30 "$FUI" mode cyan --quiet
for tier in crt deep; do   # the start page on the other two tiers
  T 30 "$FUI" display "$tier"
  T 90 firefox --headless --window-size=1280,800 --screenshot "$OUT/cyan-start-$tier.png" "file://$HOME/.local/share/fui/start.html" \
    >/dev/null 2>&1 && echo "  shot cyan-start-$tier" || echo "  no shot: cyan-start-$tier"
done
T 30 "$FUI" display lcd
shot_x "palette" 4 "$FUI" palette      # a rofi window with its own title and code
shot_x "kitty" 6 kitty --hold sh -c 'fastfetch; echo; ls -la --color=always ~ | head -12; echo; printf "\033[1;36moperator@fui\033[0m  \033[1;94m~\033[0m\n\033[1;36m>\033[0m "'
kill "$XVFB" 2>/dev/null

# ── the desktop surfaces, on a headless sway ────────────────────────────
# Hyprland needs a graphics device to start, which CI machines don't have. Sway renders in
# software (pixman) and speaks the same layer-shell protocol, so the bar, notifications,
# control centre, launcher and wallpaper render exactly as styled. (The bar's workspace
# and window modules are sway's here instead of Hyprland's.)
echo "desktop (headless sway)"
TMPD=$(mktemp -d)
cat > "$TMPD/sway.conf" <<'CONF'
output HEADLESS-1 resolution 1280x800
default_border pixel 2
gaps inner 6
gaps outer 12
CONF
cat > "$TMPD/bar.jsonc" <<'CONF'
{
  "include": ["~/.config/waybar/config.jsonc"],
  "modules-left": ["custom/brand", "sway/workspaces"],
  "modules-center": ["sway/window"],
  "modules-right": ["cpu", "memory", "network", "pulseaudio", "custom/sound", "custom/mode", "custom/notify", "clock", "custom/power"],
  "margin-top": 8, "margin-left": 12, "margin-right": 12,
  "sway/workspaces": { "format": "{icon}", "format-icons": { "1": "01", "2": "02", "3": "03", "4": "04" }, "persistent-workspaces": { "1": [], "2": [], "3": [], "4": [] } },
  "sway/window": { "format": "<span alpha='60%' size='small' letter_spacing='1600'>{app_id}</span>  {title}", "max-length": 60 }
}
CONF
cat > "$TMPD/desktop.sh" <<'EOS'
set -u
export WLR_BACKENDS=headless WLR_RENDERER=pixman WLR_LIBINPUT_NO_DEVICES=1
# Arch's sway carries a file capability, which a container won't execute: run a plain copy
cp "$(command -v sway)" "$TMPD/sway-bin"
timeout 880 "$TMPD/sway-bin" -c "$TMPD/sway.conf" >"$OUT/sway.log" 2>&1 &
for _ in $(seq 15); do [ -S "$XDG_RUNTIME_DIR/wayland-1" ] && break; sleep 1; done
export WAYLAND_DISPLAY=wayland-1
SWAYSOCK=$(ls "$XDG_RUNTIME_DIR"/sway-ipc.*.sock 2>/dev/null | head -1); export SWAYSOCK
unset DISPLAY
snap() { sleep "${2:-1}"; timeout 15 grim "$OUT/$1.png" 2>/dev/null && echo "  shot $1" || echo "  no shot: $1"; }
timeout 860 swaync >"$OUT/swaync.log" 2>&1 &
shots() {   # <edition> <tier>
  local m="$1" tier="$2" tag="$1"; [ "$tier" = lcd ] || tag="$1-$tier"
  timeout 30 "$FUI" display "$tier" >/dev/null
  timeout 30 "$FUI" mode "$m" --quiet
  timeout 60 python3 "$DOTFILES_DIR/theme/make-wallpaper.py" --edition "$m" --tier "$tier" "$TMPD/wall.png" 1280 800 >/dev/null 2>&1
  pkill -x swaybg; timeout 860 swaybg -i "$TMPD/wall.png" -m fill >/dev/null 2>&1 &
  pkill -x waybar; timeout 860 waybar -c "$TMPD/bar.jsonc" -s "$HOME/.config/waybar/style.css" >"$OUT/waybar-$m.log" 2>&1 &
  timeout 10 swaync-client -rs >/dev/null 2>&1
  base=adw-gtk3-dark; case "$m" in paper|lab) base=adw-gtk3 ;; esac
  timeout 60 env GDK_BACKEND=wayland GTK_THEME="$base" gtk3-widget-factory >/dev/null 2>&1 &
  WF=$!
  snap "$tag-desktop" 5
  timeout 10 notify-send -a fui "NOTE · Scheduled maintenance" "Workstation updates install tonight at 02:00. Save your work." 2>/dev/null
  snap "$tag-notification" 2
  timeout 10 swaync-client -op >/dev/null 2>&1; snap "$tag-control-centre" 2; timeout 10 swaync-client -cp >/dev/null 2>&1
  timeout 20 rofi -config "$HOME/.config/rofi/config.rasi" -show drun >"$OUT/rofi-$tag.log" 2>&1 &
  snap "$tag-launcher" 3; pkill -x rofi
  kill "$WF" 2>/dev/null
}
greeter() {   # <edition>: the login screen (ReGreet in demo mode, with the files make-boot.py writes)
  local m="$1" G="$TMPD/greeter-$1"
  timeout 30 "$FUI" mode "$m" --quiet
  timeout 120 python3 "$DOTFILES_DIR/theme/make-boot.py" --edition "$m" --size 1280x800 "$G" >"$OUT/greeter-$m.log" 2>&1 ||
    { echo "  no shot: $m-greeter (make-boot.py)"; return; }
  sed -i "s|/usr/share/fui/greeter/background.png|$G/greeter/background.png|" "$G/greeter/regreet.toml"
  # an empty config home: on the machine ReGreet runs as the greeter user, who has no
  # ~/.config/gtk-4.0/gtk.css (the desktop's theme would outrank the login screen's CSS)
  mkdir -p "$G/cfg"
  timeout 40 env GDK_BACKEND=wayland XDG_CONFIG_HOME="$G/cfg" regreet --demo --logs "$G/regreet.log" --config "$G/greeter/regreet.toml" --style "$G/greeter/regreet.css" \
    >>"$OUT/greeter-$m.log" 2>&1 &
  local pid=$!
  snap "$m-greeter" 8
  kill "$pid" 2>/dev/null
}
for m in $EDITIONS; do shots "$m" lcd; done
shots cyan crt; shots cyan deep; shots paper crt
pkill -x waybar; pkill -x swaync
# ReGreet lists the users through AccountsService on the system bus, which a container lacks
[ -s /etc/machine-id ] || dbus-uuidgen | sudo tee /etc/machine-id >/dev/null   # AccountsService needs one
if [ ! -S /run/dbus/system_bus_socket ]; then sudo mkdir -p /run/dbus && sudo dbus-daemon --system --fork; fi
# (and AccountsService asks polkit), and D-Bus can't start either in a container: run them here
[ -x /usr/lib/polkit-1/polkitd ] && sudo sh -c '/usr/lib/polkit-1/polkitd --no-debug >/dev/null 2>&1 &'
sudo sh -c "/usr/lib/accounts-daemon >'$OUT/accounts-daemon.log' 2>&1 &"; sleep 3
for m in cyan paper slate chrome; do greeter "$m"; done
greeter_crt() {   # the login screen on a 17-inch tube: 1024x768, crt tier
  local G="$TMPD/greeter-crt"
  timeout 120 python3 "$DOTFILES_DIR/theme/make-boot.py" --edition slate --tier crt --size 1024x768 "$G" >"$OUT/greeter-crt.log" 2>&1 || return
  sed -i "s|/usr/share/fui/greeter/background.png|$G/greeter/background.png|" "$G/greeter/regreet.toml"; mkdir -p "$G/cfg"
  swaymsg output HEADLESS-1 resolution 1024x768 >/dev/null 2>&1
  timeout 40 env GDK_BACKEND=wayland XDG_CONFIG_HOME="$G/cfg" regreet --demo --logs "$G/regreet.log" --config "$G/greeter/regreet.toml" --style "$G/greeter/regreet.css" >>"$OUT/greeter-crt.log" 2>&1 &
  local pid=$!; snap "slate-crt-greeter" 8; kill "$pid" 2>/dev/null
  swaymsg output HEADLESS-1 resolution 1280x800 >/dev/null 2>&1
}
greeter_crt
timeout 30 "$FUI" display lcd >/dev/null; timeout 30 "$FUI" mode cyan --quiet
pkill -x waybar; pkill -x swaync; pkill -x swaybg; pkill -f sway-bin
EOS
# shellcheck disable=SC2097,SC2098  # the same values, passed on explicitly
OUT="$OUT" FUI="$FUI" TMPD="$TMPD" HOME="$HOME" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" DOTFILES_DIR="$DOTFILES_DIR" EDITIONS="$EDITIONS" \
  timeout 900 dbus-run-session -- bash "$TMPD/desktop.sh" || echo "  the sway session ended early (see sway.log)"
# ── the second session: labwc (title bars, the taskbar), headless ────────
if command -v labwc >/dev/null; then
  echo "desktop (headless labwc)"
  cat > "$TMPD/labwc.sh" <<'EOS'
set -u
export WLR_BACKENDS=headless WLR_RENDERER=pixman WLR_LIBINPUT_NO_DEVICES=1
lshot() {   # <edition>
  local m="$1" C="$TMPD/labwc-$1"
  timeout 30 "$FUI" mode "$m" --quiet
  timeout 60 python3 "$DOTFILES_DIR/theme/make-wallpaper.py" --edition "$m" "$TMPD/lwall.png" 1280 800 >/dev/null 2>&1
  mkdir -p "$C"
  cp -L "$HOME/.config/labwc/rc.xml" "$HOME/.config/labwc/menu.xml" "$C/"
  base=adw-gtk3-dark; case "$m" in paper|lab|ice|chrome) base=adw-gtk3 ;; esac
  cat > "$C/autostart" <<AUTO
swaybg -i "$TMPD/lwall.png" -m fill &
"$FUI" bar &
GTK_THEME=$base gtk3-widget-factory &
sleep 1; kitty --hold sh -c 'fastfetch' &
AUTO
  timeout 40 labwc -C "$C" >"$OUT/labwc-$m.log" 2>&1 &
  local pid=$!
  for _ in $(seq 15); do ls "$XDG_RUNTIME_DIR"/wayland-* >/dev/null 2>&1 && break; sleep 1; done
  sleep 9
  WAYLAND_DISPLAY=$(basename "$(ls "$XDG_RUNTIME_DIR"/wayland-? 2>/dev/null | tail -1)") timeout 15 grim "$OUT/$m-labwc.png" 2>/dev/null &&
    echo "  shot $m-labwc" || echo "  no shot: $m-labwc"
  kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null; pkill -x waybar; pkill -x swaybg; pkill -x kitty; pkill -f gtk3-widget-factory
}
for m in cyan paper slate chrome; do lshot "$m"; done
EOS
  # shellcheck disable=SC2097,SC2098  # the same values, passed on explicitly
  OUT="$OUT" FUI="$FUI" TMPD="$TMPD" HOME="$HOME" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" DOTFILES_DIR="$DOTFILES_DIR" \
    timeout 300 dbus-run-session -- bash "$TMPD/labwc.sh" || echo "  the labwc session ended early"
  timeout 30 "$FUI" mode cyan --quiet
fi
ls -la "$OUT"
exit 0
