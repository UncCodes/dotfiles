#!/usr/bin/env bash
# HUD // install
#
# Fresh EndeavourOS / Arch:
#   bash <(curl -fsSL https://raw.githubusercontent.com/UncCodes/dotfiles/main/install.sh)
#
# Options:
#   --no-packages   only link the config files (skip pacman)
#   --no-chsh       do not change the login shell to zsh
#
# Files that would be replaced are moved to ~/.dotfiles-backup/<timestamp>/ first.
set -euo pipefail

REPO="https://github.com/UncCodes/dotfiles.git"
DOTS="${DOTFILES_DIR:-$HOME/.dotfiles}"
PKGS=(hypr waybar kitty rofi mako zsh starship fastfetch btop gtk qt fui nvim lazygit cava)

do_packages=1
do_chsh=1
for arg in "$@"; do
  case "$arg" in
    --no-packages) do_packages=0 ;;
    --no-chsh)     do_chsh=0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

say() { printf '\033[38;2;43;196;180m▣\033[0m %s\n' "$*"; }

# ── 1. get the repo ─────────────────────────────────────────────────────
if [ ! -d "$DOTS/.git" ]; then
  command -v git >/dev/null || sudo pacman -S --needed --noconfirm git
  say "cloning $REPO -> $DOTS"
  git clone --depth 1 "$REPO" "$DOTS"
fi

# ── 2. packages ─────────────────────────────────────────────────────────
if [ "$do_packages" = 1 ]; then
  mapfile -t pkgs < <(sed -e 's/#.*//' -e 's/[[:space:]]//g' "$DOTS/packages.txt" | grep -v '^$')
  say "installing ${#pkgs[@]} packages"
  sudo pacman -S --needed --noconfirm "${pkgs[@]}"
  # AUR: mpvpaper plays the live wallpaper (without it the still image is used)
  if command -v yay >/dev/null; then
    say "installing mpvpaper from the AUR"
    yay -S --needed --noconfirm mpvpaper || say "mpvpaper failed to install: the wallpaper stays still"
  else
    say "yay not found: skipping mpvpaper, the wallpaper stays still"
  fi
fi

command -v stow >/dev/null || { echo "stow is missing: run without --no-packages or install it" >&2; exit 1; }

# ── 3. move aside anything stow would collide with ─────────────────────
backup="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"
for pkg in "${PKGS[@]}"; do
  while IFS= read -r -d '' src; do
    rel="${src#"$DOTS/$pkg/"}"
    target="$HOME/$rel"
    if [ -e "$target" ] || [ -L "$target" ]; then
      if [ "$(readlink -f "$target")" != "$(readlink -f "$src")" ]; then
        mkdir -p "$backup/$(dirname "$rel")"
        mv "$target" "$backup/$rel"
        say "backed up ~/$rel"
      fi
    fi
  done < <(find "$DOTS/$pkg" -type f -print0)
done

# ── 4. link ─────────────────────────────────────────────────────────────
# --no-folding links files, not whole folders, so programs that write into
# ~/.config/<app>/ never write into the repo.
say "linking: ${PKGS[*]}"
stow --no-folding --restow -d "$DOTS" -t "$HOME" "${PKGS[@]}"

# ── 5. machine-specific bits (not tracked) ─────────────────────────────
local_conf="$HOME/.config/hypr/local.lua"
if [ ! -e "$local_conf" ]; then
  mkdir -p "$(dirname "$local_conf")"
  {
    echo "-- Machine-specific Hyprland settings (not in git)."
    echo '-- Example: hl.monitor({ output = "DP-1", mode = "2560x1440@144", position = "0x0", scale = 1 })'
  } > "$local_conf"
  if command -v lspci >/dev/null && lspci | grep -qi 'vga.*nvidia\|3d.*nvidia'; then
    say "NVIDIA GPU found: adding the Hyprland NVIDIA settings to local.lua"
    cat >> "$local_conf" <<'EOF'

-- NVIDIA (needs the nvidia-open or nvidia driver installed)
hl.env("LIBVA_DRIVER_NAME", "nvidia")
hl.env("__GLX_VENDOR_LIBRARY_NAME", "nvidia")
hl.env("NVD_BACKEND", "direct")
EOF
  fi
fi

btop_conf="$HOME/.config/btop/btop.conf"
if [ ! -e "$btop_conf" ]; then
  mkdir -p "$(dirname "$btop_conf")"
  printf 'color_theme = "hud"\ntheme_background = False\n' > "$btop_conf"
fi

# ── 5b. system-wide theme layers ────────────────────────────────────────
# Qt needs absolute asset paths, so its config is rendered for this $HOME
# (real files, not links; qt6ct may rewrite its own conf).
mkdir -p "$HOME/.config/qt6ct/qss"
sed "s|@HOME@|$HOME|g" "$DOTS/theme/templates/qt6ct.conf.in" > "$HOME/.config/qt6ct/qt6ct.conf"
for qss in fui fui-light; do
  sed "s|@HOME@|$HOME|g" "$DOTS/theme/templates/$qss.qss.in" > "$HOME/.config/qt6ct/qss/$qss.qss"
done

# git colours: include the generated file once
if command -v git >/dev/null && ! git config --global --get-all include.path 2>/dev/null | grep -q 'fui.gitconfig'; then
  git config --global --add include.path "~/.config/git/fui.gitconfig"
fi

command -v fc-cache >/dev/null && fc-cache -f >/dev/null 2>&1 || true
command -v tldr >/dev/null && { tldr --update >/dev/null 2>&1 || true; }   # tealdeer's page cache

# light / dark links: keep the current mode (dark on a fresh install)
"$HOME/.local/bin/fui-mode" apply --quiet || true

# ── 6. shell ────────────────────────────────────────────────────────────
if [ "$do_chsh" = 1 ] && [ "$(basename "${SHELL:-}")" != zsh ]; then
  say "setting zsh as login shell"
  chsh -s "$(command -v zsh)"
fi

say "done. Log out and back in (or reboot). On tty1, Hyprland starts on its own."
say "SUPER+SHIFT+T switches light / dark, SUPER+SHIFT+W live / still wallpaper."
say "Startup tabs: ~/.config/kitty/startup.session. Sounds off: fui-sound off"
[ -d "$backup" ] && say "your old files are in $backup"
exit 0
