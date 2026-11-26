# dotfiles

Hyprland on EndeavourOS as **the owned device of the millennium, cut square**: windows in a
chrome chassis (a bright lip, the lit face, a dark horizon, a lighter reflection), boxy
corners, glossy gel keys with a specular band on the primary action and the selection, lit LCD
wells for the clock and readouts, one soft shadow, springy motion. The type is an
instrument's: Michroma for the clock and display numerals, Inter for controls, JetBrains Mono
for data, with tracked capital labels and codes. Behind everything, a live backdrop of light
drawn in the edition's colours (six to pick from: a survey map, a ribbon, a helix, a
gyroscope, a fibre-optic lamp, a wireframe landscape), and the music player wears a skin
drawn from the edition.

Twelve colour **editions** (cyan, amber, phosphor, acid, hazard, mono, paper, lab, ice, chrome,
slate, ruby), each drawn for three display **tiers**: a tube (`crt`), a backlit panel (`lcd`)
and a deep-black OLED / HDR panel (`deep`).

![backdrop](hypr/.config/hypr/wallpaper.png)

Design rules: [`theme/DESIGN.md`](theme/DESIGN.md) · colours and contrast:
[`theme/PALETTE.md`](theme/PALETTE.md) · every key: [`docs/KEYS.md`](docs/KEYS.md)

## Install

### During the EndeavourOS install

1. Boot the EndeavourOS USB. In the live session open a terminal and run:
   ```bash
   curl -fsSL -o ~/user_commands.bash https://raw.githubusercontent.com/UncCodes/dotfiles/main/user_commands.bash
   ```
2. Start the installer, choose **Online**, pick **No Desktop**.
3. At the end the installer runs the script inside the new system: packages, links, zsh.
4. Reboot, log in on the console, and Hyprland starts. Then run `fui setup all` for the
   graphics driver, audio, Bluetooth, firmware, system services and Firefox, and
   `fui setup boot` for the animated boot splash and the graphical login screen (from then
   on the machine boots straight into a sign-in, never a text prompt).

### On an existing install

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/UncCodes/dotfiles/main/install.sh)
```

Safe to run again: each step reports ok / skip / FAIL, a failed step doesn't stop the rest,
and anything it would overwrite is moved to `~/.dotfiles-backup/<timestamp>/` first.
Options: `--no-packages`, `--no-hardware`, `--no-chsh`, `--ci`. Package lists:
[`packages.txt`](packages.txt) (official repos), [`aur.txt`](aur.txt) (AUR, via yay),
[`stow.txt`](stow.txt) (folders linked into `$HOME`).

### Updating

```bash
fui update
```

## The `fui` command

One command runs the desktop's moving parts. `fui help` lists it all.

| Command | Does |
|---|---|
| `fui mode toggle` / `pick` / `<edition>` | the next edition (`SUPER+SHIFT+T`, or click it in the bar) · pick any edition from a list (`SUPER+ALT+T`) · set one |
| `fui skin` | the music player's skin, drawn from the edition (runs on every edition change when Audacious is installed) |
| `fui display auto` / `crt` / `lcd` / `deep` / `pick` | the display tier; `auto` reads the screen (`SUPER+SHIFT+D`); `fui display status` says why |
| `fui alert on` / `off` | the alert takeover: the chrome's signal turns to the bad colour (`fui watch` does it on its own for a nearly empty battery or overheating) |
| `fui wallpaper toggle` | the backdrop live or still (`SUPER+SHIFT+W`); it is drawn in the edition's colours, every edition's still and the loops of this edition and the next are rendered ahead of time (loops only on mains power), so the next edition plays at once |
| `fui wallpaper pick` | which backdrop: each edition its own, or one for all: survey (contours, traces running along them), ribbon (a sheaf of light lines), helix (two braided strands), orbit (a gyroscope of rings), fibre (a fibre-optic lamp) or mesh (a wireframe landscape) |
| `fui screen toggle` | the screen finish (a faint vignette) on / off, lcd and deep only (`SUPER+SHIFT+C`) |
| `fui sound on` / `off` | the interface cues |
| `fui brand` | the machine's names: host, OS, operator (the bar badge, lock screen, start page and boot use them) |
| `fui palette` | every action in one window (`SUPER+Space`) |
| `fui power` · `fui keys` · `fui clipboard` | power menu (`SUPER+X`), the key list (`SUPER+/`), clipboard history (`SUPER+SHIFT+V`) |
| `fui shot region` / `screen` / `edit` | screenshots, saved and copied (`Print`, `SHIFT+Print`, `SUPER+Print` to annotate) |
| `fui record toggle` | screen recording to `~/Videos/Recordings` (`SUPER+R`; the bar shows `● REC`) |
| `fui tabs` · `fui layout` | the startup terminal tabs · the startup layout |
| `fui idle dim` / `blank` / `wake` | the idle steps hypridle runs (crt and deep only: dim, drift the bar, blank) |
| `fui update` · `fui updates` | update the dotfiles · count pending package updates (also in the bar) |
| `fui version` · `fui rollback [version]` | the installed version · go back to an earlier one if an update misbehaves (`fui update` returns to the newest) |
| `fui doctor` / `--fix` | check graphics, audio, network, packages, fonts, links, the look (edition, tier, one bar running); fix what it can |
| `fui setup gpu` / `audio` / `bluetooth` / `firmware` / `system` / `firefox` / `boot` / `all` | machine setup (`boot`: the animated splash, the login screen and the consoles; not part of `all`) |

When something looks wrong, run `fui doctor` and send its output.

## What it covers

| Area | What you get |
|---|---|
| Icons | one outline family (the Nerd Font's Material Design set) on everything: every palette command and menu row, the bar, the control centre, the lock screen, the start page, notifications, the prompt, fastfetch, terminal tabs, the key list and the doctor; registered in `tokens.toml` `[icons]` |
| Sessions | Hyprland (tiling) or labwc (overlapping windows with title bars, a taskbar in the bar, a right-click desktop menu), picked at the sign-in screen; both share the bar, notifications, launcher, lock and `fui`, and labwc's title bars (chrome, square gel keys) follow the edition |
| Windows | flat panels, radius 4, a hairline edge (the focused one in the signal), no shadows (a soft signal halo on deep screens); dialogs, pickers and small tools float centred; picture-in-picture pinned |
| Bar | the status rail: the badge, workspace index segments `01 02 03`, the focused window, labelled readouts (`CPU`, `MEM`, `NET`), volume and battery segment meters, now playing, updates, recording, the edition and tier, notices, the clock |
| Launcher | apps, the command palette, the edition and tier pickers, the session menu, the key reference, clipboard, emoji, calculator: one directory panel |
| Notices | memos with a stripe by urgency (a critical one as a solid plate); the system console (`SUPER+N`) with do-not-disturb, toggles, volume and media |
| Volume / brightness | a small plate with a segment meter |
| Lock screen | authentication: the distribution's logo, the host and the OS, a large clock, operator and kernel, a passphrase field, the notice |
| Apps | GTK3, GTK4 / libadwaita and Qt6 in all eight editions, including apps installed later |
| Terminal | the edition's console (light editions keep a dark one); zsh, starship, fastfetch (the workstation's asset sheet), btop, Neovim, git, mpv, zathura, imv and satty on the same palette |
| Terminal tools | lazygit, gdu, cava, tealdeer, glow, zoxide (one tool per job: files are Thunar, system and GPU monitoring btop) |
| Browser | Firefox with a flat tab strip and signal details; the start page is the intranet (true readouts, a day meter, a Display P3 signal on wide-gamut screens) |
| Apps by default | zathura (PDF), imv (images), mpv (video), Audacious (music), satty (annotation), Thunar (files) |
| System settings | windowed apps in the edition's GTK theme, one per job: Network (nm-connection-editor, plus the tray icon for Wi-Fi and VPN; `SUPER+SHIFT+N`, click the bar), Audio (pavucontrol; `SUPER+A`, click VOL), Bluetooth (blueman, after `fui setup bluetooth`); all three are in the palette. `fui doctor` offers to remove tools they replaced |
| Sound | deep, spacious cues as a sound theme: a sub-bass swell, a warm pad and glass bells at sign-in, glass bells for notices, soft blips for toggles, all in a stereo hall |
| Boot and sign-in | an animated Plymouth splash (the survey field fading in with the machine's logo, host and OS while traces of signal run along the contours, a 4 px progress line), then a graphical login screen (greetd + ReGreet in the look: a boxy shell with a chrome title strip, pressed-in fields, a gel Login key and the clock in a lit readout, over the edition's backdrop; run `fui setup boot` again after changing edition); the console palette and a sign-in banner |
| Displays | three tiers: tubes get black floors, 2 px lines, a safe inset and burn-in protection; OLED / HDR gets true black and burn-in protection; `fui display auto` picks one |
| System | keyring, firewall, weekly package-cache cleanup, firmware updates, the right graphics driver |
| Music | Audacious, with a classic player skin generated per edition (a chrome shell, square transport keys with a gel play key, glowing segment digits, an analyser, boxy faders, an equaliser and a playlist); EasyEffects for a system equaliser; Shortwave for internet radio |
| The look | windows in a chrome chassis with one soft shadow and a springy pop-in; a chrome bar with key-shaped workspaces (the current one gel) and an LCD clock; a launcher, notices and OSD in the same materials; GTK and Qt headers in chrome, chrome keys, gel selections; a welcome-screen lock; slanted tabs in the terminal; backdrops that move (seamless 56 s loops); the start page as a small device; a cursor theme drawn per edition (chrome with a gel inset; `fui cursor`). From the 2007 desktops: unified window headers (one smooth fall of light), a deep soft shadow under the focused window, source-list sidebars. The device's outer shells are round (the bar a capsule; the launcher, console, OSD, lock and login panels); everything on them is boxy: 4 px panels and windows, 2 px keys |

## Startup

At login: the edition and display tier, the wallpaper, the bar, notifications, the OSD, the login chime, a hidden
dropdown terminal (`SUPER+\``) and the startup layout,
[`fui/.config/fui/layout.conf`](fui/.config/fui/layout.conf), one app per line:

```
1  fui tabs      # workspace 1: the terminal tabs (SHELL, FILES, GIT, SYS)
2  firefox
```

The tabs are listed in [`kitty/.config/kitty/startup.session`](kitty/.config/kitty/startup.session).
Machine-only versions go in `layout.conf.local` and `startup.session.local` (ignored by git);
an empty one turns that part off.

## Theme system

Every visual value lives in [`theme/tokens.toml`](theme/tokens.toml): the editions (roles
such as `floor`, `panel`, `ink`, `signal`, plus `crt` and `deep` variants), the tiers,
geometry, type, motion and safety limits. After editing:

```bash
python3 theme/build.py                 # regenerate everything (and check contrast)
python3 theme/make-wallpaper.py --all  # redraw the fallback backdrop
python3 theme/make-sounds.py           # re-synthesise the sounds
```

`build.py` writes, per edition, a colour file for each app (waybar, rofi, swaync, swayosd,
hyprlock, kitty, Firefox, mpv, zathura, imv, satty, btop), the whole GTK and Qt themes and
the console; per tier, small overlay files that switch colours and strokes; and once, the
Hyprland token table, Neovim's colours, the start page, the shell colours, fonts, the bar's
meters, the screen finish and the docs. `fui mode` points each app's `fui-colors.*` link (and
the btop theme) at an edition, `fui display` points the `fui-tier.*` links at a tier, and both
reload what's running. The palette model is shared by every script
([`theme/palette.py`](theme/palette.py)); the backdrop is a seeded survey field
([`theme/survey.py`](theme/survey.py)), rendered per edition, tier and screen size into
`~/.cache/fui` by `fui wallpaper`.

**The look.** `[look]` in the tokens holds what the look adds beyond colour: radii, the window
frame, shadows and motion curves. The bar, notices, OSD, launcher and lock screen read their
`look.*` layers; the GTK and Qt themes, kitty's tabs and the Hyprland frame read the look from
the generated files. Editions without a chassis of their own derive one from their palette.
The backdrops are [`theme/survey.py`](theme/survey.py), [`theme/ribbon.py`](theme/ribbon.py)
and [`theme/lights.py`](theme/lights.py); each edition names the one it opens with
(`backdrop` in its table). The player skin is [`theme/make-skin.py`](theme/make-skin.py).

Not reachable by a theme: apps that draw their own UI (Blender, games). They still get the
window frame, fonts and the dark / light preference.

## Testing

Every push runs [`.github/workflows/check.yml`](.github/workflows/check.yml) in a fresh Arch
Linux container: shellcheck and luacheck, the theme build and contrast check, a check that
every needed file is in git, a full `install.sh --ci`, Hyprland's own `--verify-config`, the
Hyprland config in every edition and tier, every edition switch, every tier, the alert
takeover, the key list, fonts, sounds, the boot splash and Neovim. It then screenshots the
real apps in every edition (GTK, Qt, rofi, kitty, the start page and a headless desktop
session), plus the crt and deep tiers, and attaches them to the run as "preview".

Run on a live desktop, `tests/run.sh` leaves the session alone (no reloads, no bar restarts)
and puts your edition and tier back when it finishes.

## Per-machine settings

`~/.config/hypr/local.lua` is created by the installer and ignored by git: monitor layouts,
and the NVIDIA environment variables when an NVIDIA card is present (`fui setup gpu` installs
the driver).
