# Theme environment (Qt platform theme, cursor, colour vars) before the session starts.
[ -r ~/.config/fui/env.sh ] && source ~/.config/fui/env.sh

# Start Hyprland when logging in on the first console (no display manager needed).
if [ -z "$WAYLAND_DISPLAY" ] && [ "$XDG_VTNR" = 1 ]; then
  if command -v start-hyprland >/dev/null; then
    exec start-hyprland
  elif command -v Hyprland >/dev/null; then
    exec Hyprland
  fi
fi
