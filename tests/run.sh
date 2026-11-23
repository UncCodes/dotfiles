#!/usr/bin/env bash
# HUD // tests
#
# Runs on Arch Linux as a normal user with sudo (GitHub Actions does this in an
# archlinux container on every push; see .github/workflows/check.yml).
#   bash tests/run.sh            lint + install + checks (installs packages: use a VM/container)
#   bash tests/run.sh --lint     only the checks that change nothing
set -uo pipefail

DOTS="${DOTFILES_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
export DOTFILES_DIR="$DOTS"
lint_only=0; [ "${1:-}" = --lint ] && lint_only=1

pass=0; fail=0
t() {   # t "name" command...: run one check
  local name="$1"; shift
  local out
  if out=$("$@" 2>&1); then
    pass=$((pass + 1)); printf '  [pass] %s\n' "$name"
  else
    fail=$((fail + 1)); printf '  [FAIL] %s\n' "$name"; printf '%s\n' "$out" | tail -n 25 | sed 's/^/         /'
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
t "theme build is current" python3 "$DOTS/theme/build.py" --check
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

t "still wallpaper renders" python3 "$DOTS/theme/make-wallpaper.py" /tmp/fui-test.png 320 180
if command -v ffmpeg >/dev/null; then
  t "live wallpaper renders" python3 "$DOTS/theme/make-wallpaper.py" --live --seconds 1 /tmp/fui-test.mp4 320 240
fi

if [ "$lint_only" = 1 ]; then
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
t "fui is on the path and runs" "$HOME/.local/bin/fui" help
t "Hyprland --verify-config" Hyprland --verify-config
t "light / dark links in place" bash -c 'for l in kitty/fui-mode.conf waybar/fui-mode.css rofi/fui-mode.rasi mako/fui-mode hypr/fui-mode-hyprlock.conf gtk-3.0/fui-mode.css gtk-4.0/fui-mode.css fui/fui-mode.sh fui/starship.toml git/fui-mode.gitconfig; do [ -e "$HOME/.config/$l" ] || { echo "missing ~/.config/$l"; exit 1; }; done'
t "switch to light" bash -c '"$HOME/.local/bin/fui" mode light --quiet && [ "$(readlink "$HOME/.config/kitty/fui-mode.conf")" = colors-light.conf ] && grep -q fui-light.conf "$HOME/.config/qt6ct/qt6ct.conf"'
t "switch back to dark" bash -c '"$HOME/.local/bin/fui" mode dark --quiet && [ "$(readlink "$HOME/.config/kitty/fui-mode.conf")" = colors.conf ] && [ "$(readlink "$HOME/.config/waybar/fui-mode.css")" = style.css ]'
t "fui doctor runs to the end" bash -c '"$HOME/.local/bin/fui" doctor > /tmp/doctor.txt 2>&1; grep -q "ok, .* warnings, .* problems" /tmp/doctor.txt || { cat /tmp/doctor.txt; exit 1; }'
t "zsh loads the shell config" zsh -ic 'echo "$LS_COLORS" | grep -q "di=" && command -v starship >/dev/null'

printf '\n%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" = 0 ]
