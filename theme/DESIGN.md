# fui design

**An instrument issued by an institution to a trained operator.** The desktop is a
workstation issued by an original institution (`[brand]` in `tokens.toml`; never a real
company or one from a film or game). Its screens are dark, quiet fields with one signal
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
   atmosphere (glass, the finish, glow) is the first thing cut.

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
| `crt` | tubes (an analog input) | black floor, solid panels (no glass), labels lifted to 7:1 or more, every stroke 2 px, a 3% safe inset at the screen edges, no screen finish ever, static-content protection |
| `lcd` | backlit panels | the editions as they are: 1 px hairlines on the pixel grid, glass, the optional finish |
| `deep` | OLED, HDR, wide gamut (a 10-bit or HDR output) | true black outside the panels (wallpaper, gaps), one soft halo in the signal on the focused window, a Display P3 signal on the start page, static-content protection |

**Static-content protection** (crt and deep): after 2 minutes idle the screen dims and the
bar moves one pixel within its box (a four-step drift); after 5 minutes the screen blanks;
the lock screen's clock moves a little every minute. On lcd these steps do nothing.

An LCD on a VGA cable also reports an analog input, so `auto` calls it a tube: pin
`fui display lcd` for it.

## Type: three voices on screen

| Voice | Face | Used for |
|---|---|---|
| brand | Michroma | the institution, the clock |
| interface | Inter | controls and prose |
| data | JetBrains Mono | labels (tracked capitals), values, codes, terminals |

Labels are nouns in capitals (`DIRECTORY`, `SYSTEM CONSOLE`); actions are verbs; messages
are sentence case. Numbers keep their units, times are 24-hour, dates ISO in data and
`Tue 24 Nov` in chrome. No exclamation marks or emoji in system text.

## The panel

| Part | Built as |
|---|---|
| **Panel** | flat, a hairline, 4 px corners; glass (88% opaque, blurred by Hyprland) where the tier allows it |
| **Header plate** | 34 px, the panel colour, the signal stripe at the left (3 px; 4 px on crt), a tracked capital title, a code at the right in `faint` |
| **Field** | set in: the well colour, an `edge` boundary, 2 px corners; focus draws the signal; the caret is the signal, blinking at 1 Hz at most |
| **Row** | flat; the selected one takes `signal_dim` and the stripe |
| **Button** | secondary: an `edge` outline; primary: a solid signal fill; destructive: a `bad` outline that fills on hover |
| **Meter** | segments (`▮▮▮▯▯`), rounded down, always with the number beside it |
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
| Bar (waybar) | the status rail: the badge, workspace index segments `01 02 03`, the focused window, labelled readouts, volume and battery meters, the edition and tier, the clock in the brand voice |
| Launcher, palette, session, keys, pickers (rofi) | a directory panel: header plate, set-in search with a signal prompt, flat rows |
| Notifications (swaync) | memos: a stripe by urgency; a critical memo's summary is a solid plate in `bad` |
| Control centre (swaync) | the system console: header plate, flat toggle tiles, square sliders |
| OSD (swayosd) | a small plate with the stripe and a segment meter |
| Lock screen (hyprlock) | authentication: header plate, the mark and institution, the clock, operator and node in bracketed readouts, a passphrase field, the notice |
| Apps (GTK3/4, libadwaita, Qt) | header plates, outlined controls, square checks, set-in fields, signal selection, square progress |
| Terminal (kitty) and console tools | the edition's console: 16 colours mapped from the roles (light editions keep a dark console); shell colours are ANSI numbers so everything follows it |
| Browser (Firefox) | a flat tab strip with the stripe, the current tab underlined; the start page is the intranet |
| Start page | masthead, bracketed readouts (edition, display, operator, node), search, a directory with index codes, the clock framed by brackets and a day meter |
| Boot (Plymouth), consoles | the masthead over the network with a 4 px progress line; the console palette and a sign-in banner with the notice |
| Backdrop | the institution's network: hairline lattice and nodes, data packets in the signal when live; floor on lcd, true black on deep and crt. No text |
| Screen finish | optional (`fui screen toggle`), lcd and deep only: a faint vignette |

## Motion

Decisive: quick out, firm settle (`cubic-bezier(0.25, 0.9, 0.25, 1)`). Durations: 60 ms
(state), 140 (focus), 220 (panels), 400 (screen changes, the takeover). Nothing bounces,
glitches or blinks faster than once a second.

## Sound

Crisp synthetic cues (`make-sounds.py`): a dry tick for toggles and volume, two notes up a
fifth for a notice, an ascending arpeggio at sign-in and its mirror at sign-out, two even
pulses for attention, a falling third for an error. `fui sound off` silences them.

## Don't

- No gloss, bevels, gel, drop shadows for separation, or neon glow (deep's one halo is the
  only glow, and only in the signal).
- No borrowed brands, logos or franchise interfaces; no weapons or targeting imagery.
- No fake data: no decorative barcodes, waveforms, hex or progress that isn't progress.
- One signal at a time; status is never colour alone.
- No flashing; no emulated tube effects on a real tube.
- No text on the backdrop.
