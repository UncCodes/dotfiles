# fui design

**An instrument for a trained operator.** The desktop is a workstation that names itself by
its own machine (the distribution's logo, the host, the operating system and the operator,
read on the machine; never a company's name or mark). Its screens are dark, quiet fields with
one signal
colour, hairline structure, labels and codes everywhere, numbers shown large and honestly,
and ornament that measures, frames or indexes something. It is drawn for the display it runs
on: a tube, a backlit panel, or a deep-black OLED / HDR panel.

Tokens: [`tokens.toml`](tokens.toml) · values and contrast: [`PALETTE.md`](PALETTE.md) ·
keys: [`../docs/KEYS.md`](../docs/KEYS.md).

## Principles

1. **The screen is the material.** Every surface works on all three display tiers.
2. **Monochrome first, one signal.** The signal marks focus, the current item, the primary
   action and live data, and nothing else; at rest it covers about 5% of the screen. A
   counter colour carries a second data series only. Status colours always come with a word
   (`WARN`, `HIGH`, `LOW`, `FAULT`).
3. **Ornament has a job.** Stripes and brackets frame, segment meters measure, index codes
   index, hatching marks reserved or dangerous areas. An ornament without a job is removed.
4. **Everything is labelled.** Panels carry a title and a code (`DIR-01`, `PWR-05`,
   `AUTH-00`); readouts carry a tracked capital label and a unit. Every code refers to
   something real.
5. **Data is the image.** The most important value is the largest thing on its surface (the
   clock on the lock screen and the start page). Meters round down; nothing pretends to
   update.
6. **Quiet at rest, loud on event.** Nothing loops for attention. When something needs the
   operator now, the alert takeover turns the chrome's signal to the bad colour: one
   transition, then steady. Nothing flashes.
7. **Precision.** A 4 px unit, integer strokes, three corner kinds (square, a small radius
   where the toolkit expects one, chamfer), tabular figures with a slashed zero.
8. **Legible before cool.** Contrast floors, flash limits and reduced motion come first;
   the finish and the glow are the first things cut. Glass is the material and stays on
   every tier, so text on it is checked against the glass over the darkest backdrop.

## Colour: roles and editions

Components use **roles**, never hex:

| Role | Job |
|---|---|
| `void` | the outermost field: the wallpaper's ground on deep screens and tubes |
| `floor` · `panel` · `raised` · `well` | the base · flat panels · a hovered row or pressed control · set-in fields and terminals |
| `rule` · `rule_hi` · `edge` | decorative hairlines · grouping lines that must read · control boundaries (at least 3:1) |
| `ink` · `muted` · `faint` | text · labels (at least 4.5:1) · decorative or large text only |
| `signal` · `signal_hi` · `signal_dim` · `on_signal` | focus and current · hover · the tint behind a selected row · text on a signal fill |
| `counter` | the second data series, never focus |
| `ok` · `warn` · `bad` · `info` | status, always with a word |

An **edition** is a complete palette named for its signal. `fui mode` picks one; only colour
changes between them.

| Edition | Floor | Signal | Lineage |
|---|---|---|---|
| cyan (default) | obsidian | signal cyan | night operations |
| amber | warm black | amber | amber terminals |
| phosphor | green-black | phosphor green | green-screen terminals |
| acid | black | acid lime | techwear and dither prints |
| hazard | black | signal yellow | industrial plates |
| mono | black | white (focus by inversion; red only for faults) | the strictest edition |
| paper | warm paper | oxide red | technical print (light) |
| lab | clinical white | cobalt | the research lab (light) |

Every text and control pair is checked against WCAG on every build (`build.py --check`):
ink at 7:1 on every surface, labels and status at 4.5:1, control edges and the signal at
3:1, and every console colour at 4.5:1.

## Display tiers

`fui display` picks one; `auto` reads the connected screen.

| Tier | Screens | What changes |
|---|---|---|
| `crt` | tubes (an analog input) | black floor, labels lifted to 7:1 or more, every stroke 2 px, a 3% safe inset at the screen edges, no screen finish ever, static-content protection |
| `lcd` | backlit panels | the editions as they are: 1 px hairlines on the pixel grid, the optional finish |
| `deep` | OLED, HDR, wide gamut (a 10-bit or HDR output) | true black outside the panels (wallpaper, gaps), one soft halo in the signal on the focused window, a Display P3 signal on the start page, static-content protection |

**Static-content protection** (crt and deep): after 2 minutes idle the screen dims and the
bar moves one pixel within its box (a four-step drift); after 5 minutes the screen blanks;
the lock screen's clock moves a little every minute. On lcd these steps do nothing.

A DisplayPort or HDMI output that sends no EDID is taken for an adapter to VGA, and so a
tube too. An LCD on a VGA cable also reports an analog input, so `auto` calls it a tube: pin
`fui display lcd` for it.

A screen behind such an adapter only gets the kernel's fallback modes (60 Hz, up to
1024x768), which the boot splash and the login screen take. `fui setup boot` hands the
kernel the mode the desktop runs at (`video=<output>:<WxH@R>` on the kernel command line),
so all three match. The login screen keeps the tier's safe inset on a tube and steps its
type down on a screen of 800 lines or fewer.

## Type: three voices on screen

| Voice | Face | Used for |
|---|---|---|
| brand | Michroma | the host name, the clock |
| interface | Inter | controls and prose |
| data | JetBrains Mono | labels (tracked capitals), values, codes, terminals |

Labels are nouns in capitals (`DIRECTORY`, `SYSTEM CONSOLE`); actions are verbs; messages
are sentence case. Numbers keep their units, times are 24-hour, dates ISO in data and
`Tue 24 Nov` in chrome. No exclamation marks or emoji in system text.

## Icons

Everything carries an icon: every command in the palette and every row of every menu and
picker, every bar readout, the control centre's tiles, the lock screen, the start page,
notifications, fastfetch, the prompt, the terminal tabs, the key reference and the doctor's
output. One family only, Material Design outline glyphs from the Nerd Font, registered by
name in `tokens.toml` `[icons]` (the list with every glyph is in [`PALETTE.md`](PALETTE.md)).
Icons lead their label and dim with it; a status word still joins an icon over a threshold
(`CPU HIGH`), so state is never an icon or a colour alone. Edition pickers show a swatch of
each edition's signal. Apps keep their own (Papirus) icons in the launcher.

## The panel

| Part | Built as |
|---|---|
| **Panel** | glass: the panel colour at 72% with Hyprland blurring what is behind it (every tier), a hairline, 4 px corners; text is checked against the glass over the darkest backdrop |
| **Header plate** | 34 px, the panel colour, the signal stripe at the left (3 px; 4 px on crt), a tracked capital title, a code at the right in `faint` |
| **Field** | set in: the well colour, an `edge` boundary, 2 px corners; focus draws the signal; the caret is the signal, blinking at 1 Hz at most |
| **Row** | flat; the selected one takes `signal_dim` and the stripe |
| **Button** | secondary: an `edge` outline; primary: a solid signal fill; destructive: a `bad` outline that fills on hover |
| **Meter** | segments (`███░░`, block glyphs the data face carries), rounded down, always with the number beside it |
| **Readout** | a label dimmed and tracked, then the value in the data voice: `CPU 12%`; over a threshold the whole readout takes the status colour and the label gains its word |

## Codes

Every code names a real panel and stays stable:

| Code | Panel | Code | Panel |
|---|---|---|---|
| `DIR-01` | the app launcher | `AUTH-00` | the lock screen |
| `CMD-02` | the command palette (`SUPER+Space`) | `SRCH-01` | start page: search |
| `KEY-03` | the key reference (`SUPER+/`) | `DIR-02` | start page: the directory |
| `CLP-04` | clipboard history | `CLK-03` | start page: local time |
| `PWR-05` | the session menu and its confirmation | | |
| `ED-06` | the edition picker (`SUPER+ALT+T`) | | |
| `DSP-07` | the display-tier picker (`SUPER+SHIFT+D`) | | |

## Surfaces

| Surface | Built as |
|---|---|
| Windows (Hyprland) | panels, the focused edge in the signal, no shadows; a soft signal halo on deep |
| Bar (waybar) | the status rail: the badge (the distribution's logo and the operator), workspace index segments `01 02 03`, the focused window, labelled readouts, volume and battery meters, the edition and tier, the clock in the brand voice |
| Launcher, palette, session, keys, pickers (rofi) | a directory panel: header plate, set-in search with a signal prompt, flat rows |
| Notifications (swaync) | memos: a stripe by urgency; a critical memo's summary is a solid plate in `bad` |
| Control centre (swaync) | the system console: header plate, flat toggle tiles, square sliders |
| OSD (swayosd) | a small plate with the stripe and a segment meter |
| Lock screen (hyprlock) | authentication: header plate, the distribution's logo, the host and the OS, the clock, operator and kernel in bracketed readouts, a passphrase field, the notice |
| Apps (GTK3/4, libadwaita, Qt) | header plates, outlined controls, square checks, set-in fields, signal selection, square progress |
| Terminal (kitty) and console tools | the edition's console: 16 colours mapped from the roles (light editions keep a dark console); shell colours are ANSI numbers so everything follows it |
| Browser (Firefox) | a flat tab strip with the stripe, the current tab underlined; the start page is the intranet |
| Start page | masthead (the distribution's logo, the host, the OS), bracketed readouts (edition, display, operator, node), search, a directory with index codes, the clock framed by brackets and a day meter |
| Boot (Plymouth), sign-in (greetd + ReGreet), consoles | the splash fades in the edition's survey field and the machine's logo, host and OS while traces of signal run along the contours, with a 4 px progress line; then the login screen, a glass panel in the edition over the same field; the console palette and a sign-in banner with the notice |
| Backdrop | the survey field: a topographic map of a terrain each edition seeds differently, contour hairlines with every fifth an index contour strung with survey stations, and traces (lit stretches of contour, bright at the head) running along the lines when live; floor on lcd, true black on deep and crt. No text |
| Screen finish | optional (`fui screen toggle`), lcd and deep only: a faint vignette |

## Motion

Decisive: quick out, firm settle (`cubic-bezier(0.25, 0.9, 0.25, 1)`). Durations: 60 ms
(state), 140 (focus), 220 (panels), 400 (screen changes, the takeover). Nothing bounces,
glitches or blinks faster than once a second.

## Sound

Deep, spacious cues (`make-sounds.py`, all original synthesis): slow detuned pads over a
sub-bass, glassy FM bells with long tails and soft filtered air, placed in a wide stereo hall.
Sign-in is a sub swell, a warm A major 9 pad, a breath and four rising bells; sign-out lets the
bells fall away; a notice is two bells a fifth apart; toggles and volume are a soft cursor
blip; an edition change is a whoosh and a bloom; attention is two round low bells; an error is
a muted fall. Small cues sit quieter than the thresholds. `fui sound off` silences them.

## Don't

- No gloss, bevels, gel, drop shadows for separation, or neon glow (deep's one halo is the
  only glow, and only in the signal).
- No borrowed brands, logos or franchise interfaces; no weapons or targeting imagery.
- No fake data: no decorative barcodes, waveforms, hex or progress that isn't progress.
- One signal at a time; status is never colour alone.
- No flashing; no emulated tube effects on a real tube.
- No text on the backdrop.

## Looks

The desktop has two looks on one core. They share the roles, the display tiers, the safety
floors, glass, the icon family and every behaviour; they differ in what the machine is.

- **instrument** (this document): an instrument for a trained operator. Eight editions.
- **y2k**: the owned device of the millennium (1997–2005: skinned media players, console
  menus, late-1990s sleeve design). Four editions: `ice` and `chrome` (light), `slate` and
  `ruby` (dark). `fui look` switches; `SUPER+CTRL+T`.

What y2k changes, each with a job:

| Material | Job | Where |
|---|---|---|
| Chrome (a bright lip, the lit face, a dark horizon, a lighter reflection; `chrome_*` roles) | the device's chassis | window frames (a 4 px gradient border), the bar, headers, title strips |
| Chrome capsules (`face_*`, text in `mark`) | pressable | buttons, workspaces, the badge, hovered readouts |
| Gel (`gel_*`, text in `on_gel`), with a specular lens | the primary action, the selection, the current workspace | suggested buttons, selected rows, the active workspace |
| Readouts (`readout`, `readout_ink`), glowing | live values | the bar's clock, the lock screen's time, the OSD level, the player |
| One soft shadow | floating | windows, menus, tooltips; never between flat panels |

Motion in y2k: expo-out glides (`0.16, 1, 0.3, 1`) and a pop with about 5% overshoot for
windows and pop-ups; presses answer at once; the only thing that moves at rest is the
backdrop's ribbon (a 56 s seamless loop with a glint along its spine).

Material roles exist in every edition (instrument editions derive them from their panels),
so a component can always resolve them. Contrast is checked for `ink` on the shell and lit
text in a readout, as for every other pair.
