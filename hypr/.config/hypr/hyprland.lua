-- ┌─ fui // HYPRLAND (Lua config, Hyprland 0.57+) ─────────────────────────┐
-- │ Y2K cybercore after aljulandani.dev: frosted plastic windows with a     │
-- │ 1px bevelled edge (the focused one carries the theme's gel colour), no  │
-- │ drop shadows, old-screen glass over the whole screen, a network lattice │
-- │ behind everything. Tokens: ~/.config/hypr/fui.lua (from tokens.toml).   │
-- │ Keys: SUPER+/ shows them all (fui keys reads the comments below).       │
-- └─────────────────────────────────────────────────────────────────────────┘

-- ── tokens and the current theme ────────────────────────────────────────
local HOME = os.getenv("HOME")
local ok, T = pcall(dofile, HOME .. "/.config/hypr/fui.lua")
if not ok or type(T) ~= "table" then        -- keeps Hyprland usable if fui.lua is missing
    T = {
        modes = { dark = { bg = "0C0A09FF", edge = "4AF48366", hi = "FFFFFF24", lo = "0000008C", gel_hi = "2AB2A9FF",
                           gel_mid = "1D7C76FF", gel = "186762FF", gel_edge = "0F3E3BFF", card = "171412FF", text = "F5F2F0FF",
                           muted = "A8959AFF", skin_teal = "4FD1C0FF", white = "FFFFFFFF" } },
        desktop = { dark = { gtk_base = "adw-gtk3-dark", icon_theme = "Papirus-Dark", scheme = "prefer-dark" } },
        order = { "dark" }, cursor = { theme = "Adwaita", size = 24 },
        geometry = { radius = 10, border = 2, gaps_in = 6, gaps_out = 12 },
        opacity = { window_active = 0.97, window_inactive = 0.92 },
        blur = { size = 8, passes = 3, noise = 0.02, contrast = 1.0, brightness = 1.0, vibrancy = 0.2 },
        screen = { on = false }, font = { mono = "JetBrainsMono Nerd Font", pixel = "ProFontIIx Nerd Font", sans = "Noto Sans", size = 10 },
        ease = { 0.2, 0.8, 0.2, 1.0 },
    }
end

local STATE = (os.getenv("XDG_STATE_HOME") or (HOME .. "/.local/state")) .. "/fui"
local function state(name, default)
    local f = io.open(STATE .. "/" .. name, "r")
    if not f then return default end
    local v = f:read("*l")
    f:close()
    return v or default
end

-- dark, mid or light: fui mode (SUPER+SHIFT+T) writes the file and reloads Hyprland
local mode = state("mode", T.order[1])
if type(T.modes[mode]) ~= "table" then mode = T.order[1] end
local C = T.modes[mode]
local DESK = T.desktop[mode] or T.desktop[T.order[1]]

local function rgba(hex8, a)                 -- "RRGGBBAA" (optionally with a new alpha) -> "rgba(...)"
    if a then return string.format("rgba(%s%02X)", hex8:sub(1, 6), math.floor(a * 255 + 0.5)) end
    return "rgba(" .. hex8 .. ")"
end

-- ── programs ────────────────────────────────────────────────────────────
local fui         = "$HOME/.local/bin/fui "  -- the fui command (fui help)
local terminal    = "kitty"
local browser     = "firefox"
local fileManager = "thunar"
local rofi        = "rofi -config ~/.config/rofi/config.rasi"
local mod         = "SUPER"

-- ── monitors ────────────────────────────────────────────────────────────
-- Every screen at its preferred mode. Pin one in local.lua, e.g.
--   hl.monitor({ output = "DP-1", mode = "2560x1440@144", position = "0x0", scale = 1 })
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })

-- ── environment ─────────────────────────────────────────────────────────
hl.env("XCURSOR_SIZE", tostring(T.cursor.size))
hl.env("XCURSOR_THEME", T.cursor.theme)
hl.env("HYPRCURSOR_SIZE", tostring(T.cursor.size))
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
-- No GTK_THEME: it would pin one theme. GTK picks it up from gsettings (below, and fui mode).

-- ── autostart ───────────────────────────────────────────────────────────
hl.on("hyprland.start", function()
    -- each falls back to the plain program if the fui command is missing
    hl.exec_cmd(fui .. "mode apply --quiet")
    hl.exec_cmd(fui .. "wallpaper start || swaybg -i ~/.config/hypr/wallpaper-dark.png -m fill")  -- the lattice, live or still
    hl.exec_cmd(fui .. "bar || waybar")                                                           -- compact on small screens
    hl.exec_cmd("swaync")                                                                         -- notifications + control centre
    hl.exec_cmd("swayosd-server")                                                                 -- volume / brightness on screen
    hl.exec_cmd("hypridle")
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    hl.exec_cmd("nm-applet --indicator")
    hl.exec_cmd("wl-paste --watch cliphist store")
    hl.exec_cmd("gsettings set org.gnome.desktop.interface color-scheme " .. DESK.scheme)
    hl.exec_cmd("gsettings set org.gnome.desktop.interface gtk-theme " .. DESK.gtk_base)
    hl.exec_cmd("gsettings set org.gnome.desktop.interface icon-theme " .. DESK.icon_theme)
    hl.exec_cmd("gsettings set org.gnome.desktop.interface cursor-theme " .. T.cursor.theme)
    hl.exec_cmd("gsettings set org.gnome.desktop.interface font-name '" .. T.font.sans .. " " .. T.font.size .. "'")
    hl.exec_cmd("gsettings set org.gnome.desktop.interface monospace-font-name '" .. T.font.mono .. " " .. T.font.size .. "'")
    hl.exec_cmd("gsettings set org.gnome.desktop.sound theme-name fui")
    hl.exec_cmd("gsettings set org.gnome.desktop.sound event-sounds true")
    -- the dropdown terminal waits, hidden, on its special workspace (SUPER+`)
    hl.exec_cmd(terminal .. " --class fui-drop", { workspace = "special:drop silent" })
    hl.exec_cmd(fui .. "sound login")                      -- the startup chime (fui sound off to silence)
    hl.exec_cmd(fui .. "layout")                           -- the startup layout (~/.config/fui/layout.conf)
end)

-- ── look ────────────────────────────────────────────────────────────────
local screen_on = T.screen.on and state("screen", "on") ~= "off"

hl.config({
    general = {
        gaps_in  = T.geometry.gaps_in,
        gaps_out = T.geometry.gaps_out,
        border_size = T.geometry.border,
        col = {
            -- the focused window wears the gel: its light top-left into its deep edge
            active_border   = { colors = { rgba(C.gel_hi), rgba(C.gel_edge) }, angle = 135 },
            -- the others: a plain bevel, highlight into shade
            inactive_border = { colors = { rgba(C.hi), rgba(C.edge) }, angle = 135 },
        },
        resize_on_border = true,
        layout = "dwindle",
    },

    -- Frosted plastic: windows let the lattice through, softly blurred. No drop
    -- shadows: depth comes from bevels and insets only.
    decoration = {
        rounding = T.geometry.radius,
        active_opacity   = T.opacity.window_active,
        inactive_opacity = T.opacity.window_inactive,
        shadow = { enabled = false },
        blur = {
            enabled    = true,
            size       = T.blur.size,
            passes     = T.blur.passes,
            noise      = T.blur.noise,
            contrast   = T.blur.contrast,
            brightness = T.blur.brightness,
            vibrancy   = T.blur.vibrancy,
            popups     = true,
        },
        dim_inactive = false,
        -- old-screen glass: scanlines, phosphor stripes, darker corners (fui screen toggles it)
        screen_shader = screen_on and (HOME .. "/.config/hypr/screen.frag") or "",
    },

    animations = { enabled = true },

    -- window groups are tabs: the "tab" skin's teal plates with pixel-font titles
    group = {
        col = { border_active = rgba(C.gel_hi), border_inactive = rgba(C.edge) },
        groupbar = {
            enabled = true,
            font_family = T.font.mono,
            font_size = 11,
            height = 18,
            gradients = true,
            rounding = 4,
            render_titles = true,
            col = { active = rgba(C.skin_teal, 0.85), inactive = rgba(C.card, 0.85) },
            text_color = rgba(C.white),
            text_color_inactive = rgba(C.muted),
        },
    },

    dwindle = { preserve_split = true },

    misc = {
        disable_hyprland_logo    = true,
        disable_splash_rendering = true,
        force_default_wallpaper  = 0,
        background_color         = rgba(C.bg),
        font_family              = T.font.mono,
    },

    input = {
        kb_layout  = "us,ara",
        kb_options = "grp:alt_shift_toggle",   -- Alt+Shift switches English / Arabic
        follow_mouse  = 1,
        sensitivity   = 0,
        accel_profile = "flat",
    },
})

-- ── motion: the site's ease (fast out, long settle) ─────────────────────
local e = T.ease
hl.curve("glide", { type = "bezier", points = { { e[1], e[2] }, { e[3], e[4] } } })
hl.curve("snap",  { type = "bezier", points = { { 0.2, 0.9 }, { 0.1, 1 } } })
hl.animation({ leaf = "windowsIn",   enabled = true, speed = 3, bezier = "glide", style = "popin 94%" })
hl.animation({ leaf = "windowsOut",  enabled = true, speed = 2.5, bezier = "snap", style = "popin 94%" })
hl.animation({ leaf = "windowsMove", enabled = true, speed = 3, bezier = "glide" })
hl.animation({ leaf = "border",      enabled = true, speed = 4, bezier = "glide" })
hl.animation({ leaf = "fade",        enabled = true, speed = 3, bezier = "glide" })
hl.animation({ leaf = "layers",      enabled = true, speed = 3, bezier = "glide", style = "fade" })
hl.animation({ leaf = "workspaces",  enabled = true, speed = 3, bezier = "glide", style = "slidefade 10%" })
hl.animation({ leaf = "specialWorkspace", enabled = true, speed = 3, bezier = "glide", style = "slidevert" })

-- ── window rules ────────────────────────────────────────────────────────
-- every window, including apps installed later: the frame's radius and edge
hl.window_rule({ name = "fui-geometry", match = { class = ".*" },
    rounding = T.geometry.radius, border_size = T.geometry.border })
-- terminal tools opened from the bar or the keys (fui tui): floating, centred
hl.window_rule({ name = "fui-tui", match = { class = "^fui-tui$" },
    float = true, size = "monitor_w*0.62 monitor_h*0.66", center = true })
-- the dropdown terminal
hl.window_rule({ name = "fui-drop", match = { class = "^fui-drop$" },
    float = true, size = "monitor_w*0.84 monitor_h*0.46", move = "monitor_w*0.08 52" })
-- dialogs and pickers float, centred
hl.window_rule({ name = "fui-dialogs",
    match = { title = "^(Open File|Open Folder|Open Files|Save As|Save File|Select a File|File Upload|Choose Files|Export|Import|Preferences|Properties).*$" },
    float = true, center = true, size = "monitor_w*0.56 monitor_h*0.62" })
hl.window_rule({ name = "fui-portal", match = { class = "^(xdg-desktop-portal-gtk|org.freedesktop.impl.portal.desktop.kde)$" },
    float = true, center = true, size = "monitor_w*0.56 monitor_h*0.62" })
hl.window_rule({ name = "fui-small-tools",
    match = { class = "^(pavucontrol|org.pulseaudio.pavucontrol|nm-connection-editor|blueman-manager|qt6ct|nwg-look|com.gabm.satty)$" },
    float = true, center = true, size = "monitor_w*0.5 monitor_h*0.6" })
-- picture-in-picture: small, pinned, bottom right
hl.window_rule({ name = "fui-pip", match = { title = "^Picture-in-Picture$" },
    float = true, pin = true, size = "monitor_w*0.26 monitor_h*0.26", move = "monitor_w*0.72 monitor_h*0.70" })

-- ── frosted bar, launcher, notifications and OSD ────────────────────────
for _, ns in ipairs({ "waybar", "rofi", "swaync-control-center", "swaync-notification-window", "swayosd" }) do
    hl.layer_rule({ name = "glass-" .. ns, match = { namespace = "^" .. ns .. "$" }, blur = true, ignore_alpha = 0.1 })
end

-- ── keys ────────────────────────────────────────────────────────────────
-- Every binding carries a "-- description" comment: fui keys (SUPER+/) lists them.
local function k(keys) return mod .. " + " .. keys end

hl.bind(k("Return"), hl.dsp.exec_cmd(terminal))                                  -- terminal
hl.bind(k("SHIFT + Return"), hl.dsp.exec_cmd(fui .. "tabs"))                     -- the startup terminal tabs
hl.bind(k("grave"), hl.dsp.workspace.toggle_special("drop"))                     -- dropdown terminal
hl.bind(k("D"), hl.dsp.exec_cmd(rofi .. " -show drun"))                          -- apps
hl.bind(k("space"), hl.dsp.exec_cmd(fui .. "palette"))                           -- command palette
hl.bind(k("slash"), hl.dsp.exec_cmd(fui .. "keys"))                              -- this list of keys
hl.bind(k("B"), hl.dsp.exec_cmd(browser))                                        -- browser
hl.bind(k("E"), hl.dsp.exec_cmd(fileManager))                                    -- file manager
hl.bind(k("Y"), hl.dsp.exec_cmd(fui .. "tui yazi"))                              -- files in the terminal
hl.bind(k("A"), hl.dsp.exec_cmd(fui .. "tui wiremix"))                           -- audio mixer
hl.bind(k("SHIFT + N"), hl.dsp.exec_cmd(fui .. "tui nmtui"))                     -- network
hl.bind(k("N"), hl.dsp.exec_cmd("swaync-client -t -sw"))                         -- notifications and control centre
hl.bind(k("period"), hl.dsp.exec_cmd("rofi -modi emoji -show emoji"))            -- emoji
hl.bind(k("SHIFT + V"), hl.dsp.exec_cmd(fui .. "clipboard"))                     -- clipboard history
hl.bind(k("Q"), hl.dsp.window.close())                                           -- close window
hl.bind(k("F"), hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))  -- fullscreen
hl.bind(k("V"), hl.dsp.window.float({ action = "toggle" }))                      -- float / tile
hl.bind(k("P"), hl.dsp.window.pseudo())                                          -- pseudotile
hl.bind(k("J"), hl.dsp.layout("togglesplit"))                                    -- split direction
hl.bind(k("G"), hl.dsp.group.toggle())                                           -- group windows as tabs
hl.bind(k("Tab"), hl.dsp.group.next())                                           -- next tab in the group
hl.bind(k("SHIFT + Tab"), hl.dsp.group.prev())                                   -- previous tab in the group
hl.bind(k("Escape"), hl.dsp.exec_cmd("hyprlock"))                                -- lock
hl.bind(k("X"), hl.dsp.exec_cmd(fui .. "power"))                                 -- power menu
hl.bind(k("SHIFT + E"), hl.dsp.exit())                                           -- quit Hyprland
hl.bind(k("SHIFT + T"), hl.dsp.exec_cmd(fui .. "mode toggle"))                   -- theme: dark → mid → light
hl.bind(k("SHIFT + W"), hl.dsp.exec_cmd(fui .. "wallpaper toggle"))              -- live / still wallpaper
hl.bind(k("SHIFT + C"), hl.dsp.exec_cmd(fui .. "screen toggle"))                 -- old-screen glass on / off
hl.bind(k("R"), hl.dsp.exec_cmd(fui .. "record toggle"))                         -- screen recording start / stop
hl.bind("Print", hl.dsp.exec_cmd(fui .. "shot region"))                          -- screenshot a region (copied and saved)
hl.bind("SHIFT + Print", hl.dsp.exec_cmd(fui .. "shot screen"))                  -- screenshot the screen
hl.bind(k("Print"), hl.dsp.exec_cmd(fui .. "shot edit"))                         -- screenshot a region and annotate it

-- focus and move with the arrows
for _, dir in ipairs({ "left", "right", "up", "down" }) do
    hl.bind(k(dir), hl.dsp.focus({ direction = dir }))
    hl.bind(k("SHIFT + " .. dir), hl.dsp.window.move({ direction = dir }))
end
--@ SUPER+arrows | focus the window in that direction
--@ SUPER+SHIFT+arrows | move the window in that direction

-- workspaces 1-9 (the bar's /1 /2 /3 buttons)
for i = 1, 9 do
    hl.bind(k(tostring(i)), hl.dsp.focus({ workspace = i }))
    hl.bind(k("SHIFT + " .. i), hl.dsp.window.move({ workspace = i }))
end
--@ SUPER+1..9 | go to workspace
--@ SUPER+SHIFT+1..9 | send the window to workspace

hl.bind(k("mouse_down"), hl.dsp.focus({ workspace = "e+1" }))
hl.bind(k("mouse_up"),   hl.dsp.focus({ workspace = "e-1" }))
hl.bind(k("mouse:272"),  hl.dsp.window.drag(),   { mouse = true })
hl.bind(k("mouse:273"),  hl.dsp.window.resize(), { mouse = true })
--@ SUPER+drag | move a window (left button) or resize it (right button)

-- volume and brightness: shown by swayosd, with the site's tick
local osd, tick = "swayosd-client ", " && " .. fui .. "sound volume"
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd(osd .. "--output-volume raise" .. tick), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd(osd .. "--output-volume lower" .. tick), { locked = true, repeating = true })
hl.bind("XF86AudioMute",        hl.dsp.exec_cmd(osd .. "--output-volume mute-toggle"), { locked = true })
hl.bind("XF86AudioMicMute",     hl.dsp.exec_cmd(osd .. "--input-volume mute-toggle"), { locked = true })
hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd(osd .. "--brightness raise"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd(osd .. "--brightness lower"), { locked = true, repeating = true })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"),       { locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"),   { locked = true })
--@ volume / brightness / media keys | shown on screen by swayosd

-- ── machine-specific overrides ──────────────────────────────────────────
-- ~/.config/hypr/local.lua is created by install.sh and ignored by git
-- (monitor layout, NVIDIA env vars). Loaded only if it exists.
pcall(function()
    local path = HOME .. "/.config/hypr/local.lua"
    local f = io.open(path, "r")
    if f then
        f:close()
        dofile(path)
    end
end)
