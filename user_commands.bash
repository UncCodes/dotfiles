#!/usr/bin/env bash
# HUD // EndeavourOS installer hook
#
# The EndeavourOS installer runs this at the end of the install, as root, inside
# the new system, with the new user's name as $1. It installs the packages and
# links the dotfiles, so the first boot is already themed.
#
# Use it from the live USB, before starting the installer:
#   curl -fsSL -o ~/user_commands.bash \
#     https://raw.githubusercontent.com/UncCodes/dotfiles/main/user_commands.bash
# Then pick "Online" install. Choose "No Desktop" (Hyprland comes from here), or
# any desktop if you want one alongside Hyprland.
set -euo pipefail

user="${1:?the installer passes the new username as \$1}"
home="/home/$user"
repo="https://github.com/UncCodes/dotfiles.git"

pacman -S --needed --noconfirm git
sudo -u "$user" git clone --depth 1 "$repo" "$home/.dotfiles"

mapfile -t listed < <(sed -e 's/#.*//' -e 's/[[:space:]]//g' "$home/.dotfiles/packages.txt" | grep -v '^$')
# skip packages whose rival is already installed (7zip vs p7zip, ...): --noconfirm can't swap them
pkgs=()
for p in "${listed[@]}"; do
  clash=""
  if ! pacman -Qq "$p" >/dev/null 2>&1; then
    for c in $(pacman -Si "$p" 2>/dev/null | sed -n 's/^Conflicts With *: *//p' | head -1); do
      c="${c%%[<>=]*}"
      [ "$c" != None ] && pacman -Qq "$c" >/dev/null 2>&1 && { clash="$c"; break; }
    done
  fi
  [ -z "$clash" ] && pkgs+=("$p")
done
pacman -S --needed --noconfirm "${pkgs[@]}"

sudo -u "$user" env HOME="$home" bash "$home/.dotfiles/install.sh" --no-packages --no-hardware --no-chsh
chsh -s /usr/bin/zsh "$user"
