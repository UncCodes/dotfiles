#!/usr/bin/env bash
# fui // preview: screenshots of the real apps, for design review
#
# Runs after `install.sh --ci` (GitHub Actions does it; see .github/workflows/check.yml).
# X11 shots under Xvfb: GTK3 and GTK4 widget factories, qt6ct, rofi, kitty, and the Firefox
# start page, in every theme. Then it tries a headless Hyprland session (waybar, the
# wallpaper, windows, the launcher) and screenshots that with grim.
# Writes ~/preview/*.png. Never fails the build: a shot that can't be taken is skipped.
set -u
OUT="$HOME/preview"; mkdir -p "$OUT"
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

for m in dark mid light; do
  T 30 "$FUI" mode "$m" --quiet
  base=$([ "$m" = dark ] && echo adw-gtk3-dark || echo adw-gtk3)
  echo "theme: $m"
  shot_x "$m-gtk3" 5 env GDK_BACKEND=x11 GTK_THEME="$base" gtk3-widget-factory
  shot_x "$m-gtk4" 6 env GDK_BACKEND=x11 gtk4-widget-factory
  shot_x "$m-qt" 4 env QT_QPA_PLATFORM=xcb QT_QPA_PLATFORMTHEME=qt6ct qt6ct
  shot_x "$m-rofi" 3 rofi -config "$HOME/.config/rofi/config.rasi" -show drun
  T 90 firefox --headless --window-size=1280,800 --screenshot "$OUT/$m-start.png" "file://$HOME/.local/share/fui/start.html" \
    >/dev/null 2>&1 && echo "  shot $m-start" || echo "  no shot: $m-start"
done
T 30 "$FUI" mode dark --quiet
shot_x "kitty" 6 kitty --hold sh -c 'fastfetch; echo; ls -la --color=always ~ | head -12; echo; printf "\033[1;32mmo@fui\033[0m:\033[1;34m~\033[0m$ "'
kill "$XVFB" 2>/dev/null

# ── a headless Hyprland session ─────────────────────────────────────────
echo "hyprland (headless)"
HYPRLAND_HEADLESS_ONLY=1 timeout 150 Hyprland >"$OUT/hyprland.log" 2>&1 &
HYPR=$!
for _ in $(seq 20); do
  sig=$(ls "$XDG_RUNTIME_DIR/hypr" 2>/dev/null | head -1)
  [ -n "$sig" ] && [ -S "$XDG_RUNTIME_DIR/hypr/$sig/.socket.sock" ] && break
  sleep 1
done
if [ -n "${sig:-}" ]; then
  export HYPRLAND_INSTANCE_SIGNATURE="$sig"
  T 15 hyprctl output create headless FUI-1 >/dev/null 2>&1
  T 15 hyprctl dispatch 'hl.dsp.exec_cmd("swaybg -i '"$HOME"'/.config/hypr/wallpaper-dark.png -m fill")' >/dev/null 2>&1
  sleep 10
  export WAYLAND_DISPLAY=$(ls "$XDG_RUNTIME_DIR" | grep -E '^wayland-[0-9]+$' | head -1)
  T 15 grim "$OUT/hypr-1-desktop.png" 2>/dev/null && echo "  shot hypr-1-desktop" || echo "  no shot: hypr-1-desktop"
  T 15 hyprctl dispatch 'hl.dsp.exec_cmd("kitty --hold fastfetch")' >/dev/null 2>&1; sleep 4
  T 15 hyprctl dispatch 'hl.dsp.exec_cmd("gtk3-widget-factory")' >/dev/null 2>&1; sleep 4
  T 15 grim "$OUT/hypr-2-windows.png" 2>/dev/null && echo "  shot hypr-2-windows" || true
  T 15 rofi -config "$HOME/.config/rofi/config.rasi" -show drun >/dev/null 2>&1 & sleep 3
  T 15 grim "$OUT/hypr-3-launcher.png" 2>/dev/null && echo "  shot hypr-3-launcher" || true
  pkill -x rofi
  T 15 notify-send -a fui "[0x07] sample" "A notification for the preview." 2>/dev/null; sleep 2
  T 15 grim "$OUT/hypr-4-notification.png" 2>/dev/null && echo "  shot hypr-4-notification" || true
  T 15 swaync-client -op >/dev/null 2>&1; sleep 2
  T 15 grim "$OUT/hypr-5-control-centre.png" 2>/dev/null && echo "  shot hypr-5-control-centre" || true
  T 15 hyprctl dispatch 'hl.dsp.exit()' >/dev/null 2>&1
else
  echo "  Hyprland did not start headless (see hyprland.log)"
fi
kill "$HYPR" 2>/dev/null
ls -la "$OUT"
exit 0
