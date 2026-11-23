#!/usr/bin/env bash
# HUD // install
#
# Fresh EndeavourOS / Arch:
#   bash <(curl -fsSL https://raw.githubusercontent.com/UncCodes/dotfiles/main/install.sh)
# Afterwards, to update:  fui update
#
# Safe to run again: each step only changes what is out of date. A step that fails
# doesn't stop the others; the summary at the end lists what needs attention, and the
# exit code is 1 if anything failed.
#
# Options:
#   --no-packages   don't install packages (repo or AUR)
#   --no-hardware   skip graphics driver / audio / Bluetooth / firmware setup
#   --no-chsh       keep the current login shell
#   --ci            unattended test run: implies --no-hardware --no-chsh and skips the AUR
#
# Files that would be replaced are moved to ~/.dotfiles-backup/<timestamp>/ first.
set -uo pipefail

REPO="https://github.com/UncCodes/dotfiles.git"
DOTS="${DOTFILES_DIR:-$HOME/.dotfiles}"

do_packages=1 do_hardware=1 do_chsh=1 ci=0
for arg in "$@"; do
  case "$arg" in
    --no-packages) do_packages=0 ;;
    --no-hardware) do_hardware=0 ;;
    --no-chsh)     do_chsh=0 ;;
    --ci)          ci=1; do_hardware=0; do_chsh=0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

ICE=$'\033[38;2;143;211;220m' AMB=$'\033[38;2;201;154;78m' RED=$'\033[38;2;204;115;120m'
DIM=$'\033[38;2;125;138;143m' OFF=$'\033[0m'
say() { printf '  %s\n' "$*"; }

# ── step runner ─────────────────────────────────────────────────────────
# A step function returns 0 (ok), 3 (skipped) or anything else (failed), and may set
# NOTE to a short reason shown in the summary.
RESULTS=()
step() {
  local name="$1"; shift
  printf '\n%s▣ %s%s\n' "$ICE" "$name" "$OFF"
  NOTE=""
  "$@"
  local rc=$?
  case $rc in
    0) RESULTS+=("ok|$name|$NOTE") ;;
    3) RESULTS+=("skip|$name|$NOTE"); say "${DIM}skipped${NOTE:+: $NOTE}${OFF}" ;;
    *) RESULTS+=("FAIL|$name|$NOTE"); say "${RED}failed${NOTE:+: $NOTE}${OFF}" ;;
  esac
}

listed() { sed -e 's/#.*//' -e 's/[[:space:]]//g' "$1" 2>/dev/null | grep -v '^$'; }

# ── steps ───────────────────────────────────────────────────────────────
get_repo() {
  if [ -d "$DOTS/.git" ] || [ -f "$DOTS/stow.txt" ]; then
    NOTE="$DOTS"; return 0
  fi
  command -v git >/dev/null || sudo pacman -S --needed --noconfirm git || { NOTE="git missing"; return 1; }
  say "cloning $REPO -> $DOTS"
  git clone --depth 1 "$REPO" "$DOTS" || { NOTE="clone failed"; return 1; }
}

PKG_LIST=()
resolve_packages() {
  # Every listed package must exist in the repos. A package is skipped when something it
  # conflicts with is already installed (7zip vs p7zip, tealdeer vs tldr): the installed
  # one does the same job, and pacman --noconfirm would refuse to swap them.
  [ "$do_packages" = 1 ] || { NOTE="--no-packages"; return 3; }
  local p c clash missing="" skipped=""
  sudo pacman -Sy --noconfirm >/dev/null || { NOTE="couldn't refresh the package databases (offline?)"; return 1; }
  while IFS= read -r p; do
    if pacman -Qq "$p" >/dev/null 2>&1; then PKG_LIST+=("$p"); continue; fi
    if ! pacman -Si "$p" >/dev/null 2>&1; then missing="$missing $p"; continue; fi
    clash=""
    for c in $(pacman -Si "$p" 2>/dev/null | sed -n 's/^Conflicts With *: *//p' | head -1); do
      c="${c%%[<>=]*}"
      [ "$c" = None ] && continue
      if pacman -Qq "$c" >/dev/null 2>&1; then clash="$c"; break; fi
    done
    if [ -n "$clash" ]; then skipped="$skipped $p(→$clash)"; else PKG_LIST+=("$p"); fi
  done < <(listed "$DOTS/packages.txt")
  [ -n "$skipped" ] && say "using what's installed instead:$skipped"
  say "${#PKG_LIST[@]} packages to check"
  if [ -n "$missing" ]; then
    NOTE="not in the repos:$missing"; return 1
  fi
  NOTE="${#PKG_LIST[@]} packages${skipped:+, alternatives kept:$skipped}"
}

install_packages() {
  [ "$do_packages" = 1 ] || { NOTE="--no-packages"; return 3; }
  [ ${#PKG_LIST[@]} -gt 0 ] || { NOTE="nothing to install"; return 3; }
  # -Syu: Arch doesn't support installing new packages onto an out-of-date system
  sudo pacman -Syu --needed --noconfirm "${PKG_LIST[@]}" || { NOTE="pacman failed (see above)"; return 1; }
}

install_aur() {
  [ "$do_packages" = 1 ] || { NOTE="--no-packages"; return 3; }
  [ "$ci" = 0 ] || { NOTE="--ci"; return 3; }
  local aur=()
  local p; while IFS= read -r p; do aur+=("$p"); done < <(listed "$DOTS/aur.txt")
  [ ${#aur[@]} -gt 0 ] || return 3
  command -v yay >/dev/null || { NOTE="yay not found: ${aur[*]} not installed"; return 3; }
  yay -S --needed --noconfirm "${aur[@]}" || { NOTE="yay failed for: ${aur[*]}"; return 1; }
  NOTE="${aur[*]}"
}

setup_hardware() {
  [ "$do_hardware" = 1 ] || { NOTE="skipped by option"; return 3; }
  [ -t 0 ] || { NOTE="not interactive"; return 3; }
  bash "$DOTS/fui/.local/bin/fui" setup all || { NOTE="see above"; return 1; }
}

STOW_PKGS=()
backup_conflicts() {
  local p; while IFS= read -r p; do STOW_PKGS+=("$p"); done < <(listed "$DOTS/stow.txt")
  local backup pkg src rel target n=0
  backup="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"
  for pkg in "${STOW_PKGS[@]}"; do
    while IFS= read -r -d '' src; do
      rel="${src#"$DOTS/$pkg/"}"
      target="$HOME/$rel"
      if [ -e "$target" ] || [ -L "$target" ]; then
        if [ "$(readlink -f "$target")" != "$(readlink -f "$src")" ]; then
          mkdir -p "$backup/$(dirname "$rel")"
          mv "$target" "$backup/$rel" && n=$((n + 1))
        fi
      fi
    done < <(find "$DOTS/$pkg" -type f -print0)
  done
  [ "$n" = 0 ] && { NOTE="nothing in the way"; return 0; }
  NOTE="$n files moved to $backup"
}

link_files() {
  # --no-folding links files, not folders, so programs that write into ~/.config/<app>/
  # never write into the repo
  command -v stow >/dev/null || { NOTE="stow is not installed"; return 1; }
  stow --no-folding --restow -d "$DOTS" -t "$HOME" "${STOW_PKGS[@]}" || { NOTE="stow failed"; return 1; }
  NOTE="${STOW_PKGS[*]}"
}

remove_stale_links() {
  # links left behind by files that were renamed or removed in the repo
  local l n=0
  while IFS= read -r l; do
    case "$(readlink "$l")" in *"$(basename "$DOTS")/"*) rm -f "$l" && n=$((n + 1)) ;; esac
  done < <(find "$HOME/.config" "$HOME/.local/bin" -xtype l 2>/dev/null)
  NOTE="$n removed"
}

machine_files() {
  # per-machine files that are never committed
  local lc="$HOME/.config/hypr/local.lua"
  if [ ! -e "$lc" ]; then
    mkdir -p "$(dirname "$lc")"
    printf '%s\n' "-- Machine-specific Hyprland settings (not in git)." \
      '-- Example: hl.monitor({ output = "DP-1", mode = "2560x1440@144", position = "0x0", scale = 1 })' > "$lc"
  fi
  if command -v lspci >/dev/null && lspci | grep -qiE '(vga|3d).*nvidia' && ! grep -q LIBVA_DRIVER_NAME "$lc"; then
    printf '\n-- NVIDIA (needs the nvidia driver: fui setup gpu)\nhl.env("LIBVA_DRIVER_NAME", "nvidia")\nhl.env("__GLX_VENDOR_LIBRARY_NAME", "nvidia")\nhl.env("NVD_BACKEND", "direct")\n' >> "$lc"
    say "added the NVIDIA settings to local.lua"
  fi
  local bc="$HOME/.config/btop/btop.conf"
  if [ ! -e "$bc" ]; then
    mkdir -p "$(dirname "$bc")"
    printf 'color_theme = "hud"\ntheme_background = False\n' > "$bc"
  fi
  return 0
}

toolkit_files() {
  # Qt needs absolute asset paths, so its config is rendered for this $HOME
  # (real files, not links; qt6ct may rewrite its own conf)
  mkdir -p "$HOME/.config/qt6ct/qss"
  sed "s|@HOME@|$HOME|g" "$DOTS/theme/templates/qt6ct.conf.in" > "$HOME/.config/qt6ct/qt6ct.conf" || return 1
  local q
  for q in fui fui-light; do
    sed "s|@HOME@|$HOME|g" "$DOTS/theme/templates/$q.qss.in" > "$HOME/.config/qt6ct/qss/$q.qss" || return 1
  done
  if command -v git >/dev/null && ! git config --global --get-all include.path 2>/dev/null | grep -q 'fui.gitconfig'; then
    # shellcheck disable=SC2088  # git expands the ~ itself
    git config --global --add include.path "~/.config/git/fui.gitconfig"
  fi
  command -v fc-cache >/dev/null && fc-cache -f >/dev/null 2>&1
  command -v tldr >/dev/null && { tldr --update >/dev/null 2>&1 || true; }
  return 0
}

fui_on_path() {
  # ~/.local/bin is added to PATH by the shell config, but only in shells started after the
  # install; a link in /usr/local/bin makes `fui` work everywhere, right away
  local want="$HOME/.local/bin/fui"
  [ "$(readlink /usr/local/bin/fui 2>/dev/null)" = "$want" ] && { NOTE="/usr/local/bin/fui"; return 0; }
  if sudo -n true 2>/dev/null || [ -t 0 ]; then
    sudo mkdir -p /usr/local/bin && sudo ln -sfn "$want" /usr/local/bin/fui || { NOTE="couldn't link /usr/local/bin/fui"; return 1; }
    NOTE="/usr/local/bin/fui"
  else
    NOTE="no sudo here: fui works in new terminals via ~/.local/bin"; return 3
  fi
}

apply_mode() {
  # light / dark links for the current mode (dark on a fresh install)
  "$HOME/.local/bin/fui" mode apply --quiet || return 1
  NOTE="$("$HOME/.local/bin/fui" mode status) mode"
}

login_shell() {
  [ "$do_chsh" = 1 ] || { NOTE="skipped by option"; return 3; }
  [ "$(basename "${SHELL:-}")" = zsh ] && { NOTE="already zsh"; return 0; }
  chsh -s "$(command -v zsh)" || { NOTE="chsh failed"; return 1; }
  NOTE="zsh from the next login"
}

# ── run ─────────────────────────────────────────────────────────────────
printf '%sHUD // install%s  %s\n' "$AMB" "$OFF" "$DOTS"
step "dotfiles"            get_repo
[ -d "$DOTS" ] || { echo "no dotfiles at $DOTS"; exit 1; }
step "package list"        resolve_packages
step "packages"            install_packages
step "AUR packages"        install_aur
step "hardware"            setup_hardware
step "move conflicting files aside" backup_conflicts
step "link config files"   link_files
step "remove stale links"  remove_stale_links
step "machine files"       machine_files
step "toolkit files"       toolkit_files
step "fui command"         fui_on_path
step "light / dark"        apply_mode
step "login shell"         login_shell

# ── summary ─────────────────────────────────────────────────────────────
printf '\n%sSUMMARY%s\n' "$AMB" "$OFF"
failed=0
for r in "${RESULTS[@]}"; do
  IFS='|' read -r status name note <<<"$r"
  case "$status" in
    ok)   c="$ICE"; mark=" ok " ;;
    skip) c="$DIM"; mark="skip" ;;
    *)    c="$RED"; mark="FAIL"; failed=1 ;;
  esac
  printf '  %s[%s]%s %-30s %s%s%s\n' "$c" "$mark" "$OFF" "$name" "$DIM" "$note" "$OFF"
done
echo
if [ "$failed" = 1 ]; then
  echo "Some steps failed. Fix them (fui doctor helps) and run this again: it's safe to repeat."
  exit 1
fi
echo "Done. Log out and back in (SUPER+SHIFT+E); on tty1 Hyprland starts on its own."
echo "SUPER+SHIFT+T light/dark · SUPER+SHIFT+W live/still wallpaper · fui doctor checks the machine."
exit 0
