# fui // Plasma: sourced by startplasma before the session starts.
# Hyprland's apps read the Qt look through qt5ct/qt6ct; Plasma has its own platform theme
# (with the fui colour scheme), so the variable must not leak into this session.
unset QT_QPA_PLATFORMTHEME
