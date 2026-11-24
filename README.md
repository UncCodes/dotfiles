# dotfiles

Hyprland on EndeavourOS as **an instrument issued by an institution**: dark quiet fields,
one signal colour, hairline structure, header plates with a signal stripe, tracked capital
labels and codes, segment meters, numbers shown large and honestly, the institution's
network behind everything. Eight colour **editions** (cyan, amber, phosphor, acid, hazard,
mono, paper, lab), each drawn for three display **tiers**: a tube (`crt`), a backlit panel
(`lcd`) and a deep-black OLED / HDR panel (`deep`).

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
   graphics driver, audio, Bluetooth, firmware, system services and Firefox.

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
| `fui mode toggle` / `pick` / `<edition>` | the next edition (`SUPER+SHIFT+T`, or click it in the bar) · pick one from a list (`SUPER+ALT+T`) · set one |
| `fui display auto` / `crt` / `lcd` / `deep` / `pick` | the display tier; `auto` reads the screen (`SUPER+SHIFT+D`); `fui display status` says why |
| `fui alert on` / `off` | the alert takeover: the chrome's signal turns to the bad colour (`fui watch` does it on its own for a nearly empty battery or overheating) |
| `fui wallpaper toggle` | the network backdrop live (data packets travelling) or still (`SUPER+SHIFT+W`) |
| `fui screen toggle` | the screen finish (a faint vignette) on / off, lcd and deep only (`SUPER+SHIFT+C`) |
| `fui sound on` / `off` | the interface cues |
| `fui brand` | the institution: name, division, motto (`[brand]` in `tokens.toml`) |
| `fui palette` | every action in one window (`SUPER+Space`) |
| `fui power` · `fui keys` · `fui clipboard` | power menu (`SUPER+X`), the key list (`SUPER+/`), clipboard history (`SUPER+SHIFT+V`) |
| `fui shot region` / `screen` / `edit` | screenshots, saved and copied (`Print`, `SHIFT+Print`, `SUPER+Print` to annotate) |
| `fui record toggle` | screen recording to `~/Videos/Recordings` (`SUPER+R`; the bar shows `● REC`) |
| `fui tabs` · `fui layout` | the startup terminal tabs · the startup layout |
| `fui idle dim` / `blank` / `wake` | the idle steps hypridle runs (crt and deep only: dim, drift the bar, blank) |
| `fui update` · `fui updates` | update the dotfiles · count pending package updates (also in the bar) |
| `fui version` · `fui rollback [version]` | the installed version · go back to an earlier one if an update misbehaves (`fui update` returns to the newest) |
| `fui doctor` / `--fix` | check graphics, audio, network, packages, fonts, links, the look (edition, tier, one bar running); fix what it can |
| `fui setup gpu` / `audio` / `bluetooth` / `firmware` / `system` / `firefox` / `boot` / `all` | machine setup (`boot`: the splash and the consoles; not part of `all`) |

When something looks wrong, run `fui doctor` and send its output.

## What it covers

| Area | What you get |
|---|---|
| Windows | flat panels, radius 4, a hairline edge (the focused one in the signal), no shadows (a soft signal halo on deep screens); dialogs, pickers and small tools float centred; picture-in-picture pinned |
| Bar | the status rail: the badge, workspace index segments `01 02 03`, the focused window, labelled readouts (`CPU`, `MEM`, `NET`), volume and battery segment meters, now playing, updates, recording, the edition and tier, notices, the clock |
| Launcher | apps, the command palette, the edition and tier pickers, the session menu, the key reference, clipboard, emoji, calculator: one directory panel |
| Notices | memos with a stripe by urgency (a critical one as a solid plate); the system console (`SUPER+N`) with do-not-disturb, toggles, volume and media |
| Volume / brightness | a small plate with a segment meter |
| Lock screen | authentication: the institution, a large clock, operator and node, a passphrase field, the notice |
| Apps | GTK3, GTK4 / libadwaita and Qt6 in all eight editions, including apps installed later |
| Terminal | the edition's console (light editions keep a dark one); zsh, starship, fastfetch (the workstation's asset sheet), btop, Neovim, git, mpv, zathura, imv and satty on the same palette |
| Terminal tools | yazi, lazygit, wiremix, nmtui, gdu, nvtop, cava, tealdeer, glow, zoxide |
| Browser | Firefox with a flat tab strip and signal details; the start page is the intranet (true readouts, a day meter, a Display P3 signal on wide-gamut screens) |
| Apps by default | zathura (PDF), imv (images), mpv (video), satty (annotation), Thunar (files) |
| Sound | crisp synthetic cues as a sound theme: the sign-in arpeggio, notice tones, ticks, alerts |
| Boot | a Plymouth splash (the masthead over the network, a 4 px progress line), the console palette and a sign-in banner |
| Displays | three tiers: tubes get black floors, 2 px lines, a safe inset and burn-in protection; OLED / HDR gets true black and burn-in protection; `fui display auto` picks one |
| System | keyring, firewall, weekly package-cache cleanup, firmware updates, the right graphics driver |

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
python3 theme/make-brand.py            # redraw the mark for every edition
```

`build.py` writes, per edition, a colour file for each app (waybar, rofi, swaync, swayosd,
hyprlock, kitty, Firefox, mpv, zathura, imv, satty, btop), the whole GTK and Qt themes and
the console; per tier, small overlay files that switch colours and strokes; and once, the
Hyprland token table, Neovim's colours, the start page, the shell colours, fonts, the bar's
meters, the screen finish and the docs. `fui mode` points each app's `fui-colors.*` link (and
the mark) at an edition, `fui display` points the `fui-tier.*` links at a tier, and both
reload what's running. The palette model is shared by every script
([`theme/palette.py`](theme/palette.py)); the network is a seeded 3D lattice
([`theme/lattice.py`](theme/lattice.py)), rendered per edition, tier and screen size into
`~/.cache/fui` by `fui wallpaper`.

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
