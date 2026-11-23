# dotfiles

A sci-fi FUI theme for Hyprland on EndeavourOS. Void-black space, hazy translucent panels
with razor 1px hairlines, micro-geometry (dot matrices, reticles, tick marks, L-brackets),
muted-neon colours (ice cyan, steel blue, dim amber, muted crimson) and monospace type with
wide-tracked micro-labels. Colours and rules: [`theme/PALETTE.md`](theme/PALETTE.md).

![wallpaper](hypr/.config/hypr/wallpaper.png)

Open [`theme/preview.html`](theme/preview.html) for a mock of the full desktop and
[`theme/components.html`](theme/components.html) for the component geometry.

## System-wide theming

Every visual value lives in one file: [`theme/tokens.toml`](theme/tokens.toml)
(palette, opacity, blur, border, chamfer / notch / bracket sizes, fonts, gaps).

```bash
$EDITOR theme/tokens.toml
python3 theme/build.py          # regenerate everything
python3 theme/build.py --check  # fail if anything is stale
python3 theme/make-wallpaper.py # redraw the wallpaper from the tokens
```

`build.py` does two things:
1. **Generates the layers new apps inherit**, so anything you install later is themed
   without per-app work:

   | Layer | Reaches | Files |
   |---|---|---|
   | GTK3 overrides on adw-gtk3-dark | every GTK3 app | `gtk/.config/gtk-3.0/gtk.css` + `assets/` |
   | GTK4 overrides | every GTK4 and libadwaita app | `gtk/.config/gtk-4.0/gtk.css` + `assets/` |
   | qt6ct palette + stylesheet | every Qt6 app | `qt/.config/qt6ct/`, `theme/templates/*.in` |
   | Hyprland window rule | every window: radius 0, 1px border, opacity, blur | `hyprland.lua` reads `hypr/.config/hypr/fui.lua` |
   | Shell colour env | ls, eza, grep, less/man, fzf, jq, gcc, bat | `fui/.config/fui/env.sh` |
   | ANSI 16 | every terminal program | kitty colours |
   | systemd environment.d | apps started by portals / D-Bus | `fui/.config/environment.d/60-fui.conf` |
   | fontconfig | any app asking for monospace / sans-serif | `fui/.config/fontconfig/conf.d/60-fui.conf` |
   | Chromium / Electron flags | dark mode, Wayland | `fui/.config/*-flags.conf` |
   | git colours | git | `fui/.config/git/fui.gitconfig` (included by install.sh) |
   | Neovim colorscheme | nvim, unless your config picks another | `nvim/.config/nvim/` |
   | btop theme | btop | `btop/.../hud.theme` |
   | Web tokens | your own pages | `theme/web/fui-tokens.css` |

   Geometry is drawn with SVG assets generated from the tokens: `[ ]` bracket buttons,
   45° chamfered entries / popovers / frames, parallelogram tabs, a notched headerbar,
   diamond checkboxes, hollow-square radios, a notched slider thumb, plus skewed
   segmented progress bars and ticked, stepped scrollbars.
2. **Sweeps changed colours through the hand-written configs** (kitty, waybar, rofi, mako,
   starship, hyprlock, hyprland.lua, zsh), keeping their structure.
   `theme/.applied.json` records the last applied palette.

Not reachable by a system-wide setting: Firefox (needs a per-profile `userChrome.css`),
Qt5-only apps (would need `qt5ct`), and apps that draw their own UI (Blender, games).
They still get the window rules, fonts and dark-mode preference.

## What's in it

| Folder      | Configures                                     |
|-------------|------------------------------------------------|
| `hypr`      | Hyprland (Lua config, 0.57+), hyprlock, hypridle, wallpaper |
| `waybar`    | top bar: framed readouts, amber clock          |
| `rofi`      | app launcher (`SUPER+D`), clipboard (`SUPER+SHIFT+V`) |
| `kitty`     | terminal and its 16 colours                    |
| `mako`      | notifications                                  |
| `zsh`       | shell; `.zprofile` starts Hyprland on tty1     |
| `starship`  | prompt                                         |
| `fastfetch` | system info                                    |
| `btop`      | `hud` theme                          |
| `gtk`       | GTK3/4 FUI overrides + geometry assets (generated) |
| `qt`        | qt6ct palette + assets (generated)             |
| `fui`       | theme env, fontconfig, git, browser flags (generated) |
| `nvim`      | FUI colorscheme (generated)                    |

Each folder mirrors `$HOME` and is linked with GNU Stow (`--no-folding`).

## Install

### During the EndeavourOS install (themed on first boot)

1. Boot the EndeavourOS USB. In the live session open a terminal and run:
   ```bash
   curl -fsSL -o ~/user_commands.bash https://raw.githubusercontent.com/UncCodes/dotfiles/main/user_commands.bash
   ```
2. Start the installer, choose **Online**, and pick **No Desktop** (Hyprland comes from
   the script) or any desktop you also want.
3. At the end of the install the installer runs the script inside the new system: it installs
   [`packages.txt`](packages.txt), clones this repo to `~/.dotfiles`, links it, and sets zsh.
4. Reboot, log in on the console, and Hyprland starts.

### On an existing install

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/UncCodes/dotfiles/main/install.sh)
```

Anything it would overwrite is moved to `~/.dotfiles-backup/<timestamp>/` first.
`--no-packages` only links files; `--no-chsh` keeps your current shell.

## Keys

| Keys                 | Does                                |
|----------------------|-------------------------------------|
| `SUPER+Return`       | terminal                            |
| `SUPER+D`            | launcher                            |
| `SUPER+E`            | file manager                        |
| `SUPER+Q`            | close window                        |
| `SUPER+F` / `V`      | fullscreen / float                  |
| `SUPER+arrows`       | focus (add `SHIFT` to move window)  |
| `SUPER+1..9`         | workspace (add `SHIFT` to send window) |
| `SUPER+Escape`       | lock                                |
| `SUPER+SHIFT+E`      | quit Hyprland                       |
| `Print` / `SHIFT+Print` | region to clipboard / screen to `~/Pictures` |
| `Alt+Shift`          | switch English / Arabic keyboard    |

## Per-machine settings

`~/.config/hypr/local.lua` is created by the installer and ignored by git. Put monitor
layouts there. On machines with an NVIDIA card the installer adds the NVIDIA environment
variables to it; you still need the driver (`nvidia-open-dkms`, or choose the NVIDIA boot
entry on the EndeavourOS USB).

## Changing the theme

Colours live in each app's config, listed in `theme/PALETTE.md`. The wallpaper is generated:

```bash
python3 theme/make-wallpaper.py                       # 2560x1440 into hypr/
python3 theme/make-wallpaper.py out.png 3840 2160     # other sizes
```
