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
# at once instead of waiting to autolaunch a bus and services.
export DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent/bus"

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
t "theme build is current, contrast passes" python3 "$DOTS/theme/build.py" --check
t "Qt stylesheets have no // (qt6ct strips it as a comment)" bash -c '! grep -l "//" "$1"/theme/templates/*.qss.in' _ "$DOTS"
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
  t "still wallpaper renders" python3 "$DOTS/theme/make-wallpaper.py" /tmp/fui-test.png 320 180
  if command -v ffmpeg >/dev/null; then
    t "live wallpaper renders" python3 "$DOTS/theme/make-wallpaper.py" --live --seconds 1 /tmp/fui-test.mp4 320 240
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
t "theme links in place" bash -c 'for l in waybar/fui-colors.css rofi/fui-colors.rasi swaync/fui-colors.css swayosd/fui-colors.css hypr/fui-colors.conf kitty/fui-colors.conf gtk-3.0/fui-mode.css gtk-4.0/fui-mode.css; do [ -e "$HOME/.config/$l" ] || { echo "missing ~/.config/$l"; exit 1; }; done'
for m in mid light dark; do
  t "switch to $m" bash -c '"$HOME/.local/bin/fui" mode "$1" --quiet &&
    [ "$(readlink "$HOME/.config/kitty/fui-colors.conf")" = "colors-$1.conf" ] &&
    [ "$(readlink "$HOME/.config/gtk-4.0/fui-mode.css")" = "fui-$1.css" ] &&
    grep -q "fui-$1.conf" "$HOME/.config/qt6ct/qt6ct.conf" &&
    grep -q "data-theme=\"$1\"" "$HOME/.local/share/fui/start.html"' _ "$m"
done
t "theme cycles dark → mid → light" bash -c 'f="$HOME/.local/bin/fui"; "$f" mode dark --quiet; "$f" mode toggle --quiet; [ "$("$f" mode status)" = mid ] && "$f" mode toggle --quiet && [ "$("$f" mode status)" = light ] && "$f" mode toggle --quiet && [ "$("$f" mode status)" = dark ]'
t "key list reads hyprland.lua" bash -c '"$HOME/.local/bin/fui" keys --text | grep -q "command palette"'
t "the fui sound theme is installed" test -f "$HOME/.local/share/sounds/fui/stereo/desktop-login.oga"
t "fonts: Michroma, DSEG7, ProFont IIx, JetBrains Mono" bash -c 'fc-list | grep -q Michroma && fc-list | grep -q "DSEG7 Classic" && fc-list | grep -qi "ProFontIIx" && fc-list | grep -q "JetBrainsMono Nerd"'
t "boot splash renders" python3 "$DOTS/theme/make-boot.py" /tmp/fui-boot-test
if command -v nvim >/dev/null; then
  t "Neovim config loads (plugins install)" bash -c 'timeout 300 nvim --headless "+Lazy! sync" +qa >/dev/null 2>&1; timeout 60 nvim --headless -c "lua if vim.g.colors_name ~= [[fui]] then os.exit(1) end; require([[telescope]])" -c qa'
fi
t "fui doctor runs to the end" bash -c '"$HOME/.local/bin/fui" doctor > /tmp/doctor.txt 2>&1; grep -q "ok, .* warnings, .* problems" /tmp/doctor.txt || { cat /tmp/doctor.txt; exit 1; }'
wallpaper_checks
t "zsh loads the shell config" zsh -ic 'echo "$LS_COLORS" | grep -q "di=" && command -v starship >/dev/null'

printf '\n%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" = 0 ]
