# fui design

**The owned device of the millennium, cut square, set in an instrument's type.** The desktop
is a device you own (the late 1990s and early 2000s: skinned media players, console menus,
the sleeve design of the time): chrome shells lit from above, glossy gel on what you press,
lit LCD wells for live values, one soft shadow, springy motion. Its corners are boxy and its
type is an instrument's: labels and codes everywhere, numbers shown large and honestly. It
names itself by its own machine (the distribution's logo, the host, the operating system and
the operator, read on the machine; never a company's name or mark), and it is drawn for the
display it runs on: a tube, a backlit panel, or a deep-black OLED / HDR panel.

Tokens: [`tokens.toml`](tokens.toml) · values and contrast: [`PALETTE.md`](PALETTE.md) ·
keys: [`../docs/KEYS.md`](../docs/KEYS.md).

## Principles

1. **The screen is the material.** Every surface works on all three display tiers.
2. **Monochrome first, one signal.** The signal marks focus, the current item, the primary
   action and live data, and nothing else; at rest it covers about 5% of the screen. A
   counter colour carries a second data series only. Status colours always come with a word
   (`WARN`, `HIGH`, `LOW`, `FAULT`).
3. **Every material has a job.** Chrome is the chassis, chrome keys are pressable, gel is the
   primary action and the selection, a lit readout is a live value, the one soft shadow means
   floating. Segment meters measure, index codes index. A finish without a job is removed.
4. **Everything is labelled.** Panels carry a title and a code (`DIR-01`, `PWR-05`,
   `AUTH-00`); readouts carry a tracked capital label and a unit. Every code refers to
   something real.
5. **Data is the image.** The most important value is the largest thing on its surface (the
   clock on the lock screen and the start page). Meters round down; nothing pretends to
   update.
6. **Quiet at rest, loud on event.** Nothing loops for attention. When something needs the
   operator now, the alert takeover turns the chrome's signal to the bad colour: one
   transition, then steady. Nothing flashes.
7. **Precision: a round shell, boxy parts.** A 4 px unit, integer strokes. The device's outer
   shells are round (the bar a capsule; the launcher, console, OSD, lock and login panels at
   14 to 16 px); everything on them is boxy: 4 px windows and panels, 2 px keys, fields and
   rows. Only the shapes whose roundness is their meaning stay round: a radio, a switch and its knob, a slider's knob on its capsule track, a notification's close button (a round chrome bead, red gel on hover). Tabular figures with a slashed zero.
8. **Legible before cool.** Contrast floors, flash limits and reduced motion come first;
   the finish, the gloss and the glow are the first things cut. Glass is the material and stays on
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
| cyan | obsidian | signal cyan | night operations |
| amber | warm black | amber | amber terminals |
| phosphor | green-black | phosphor green | green-screen terminals |
| acid | black | acid lime | techwear and dither prints |
| hazard | black | signal yellow | industrial plates |
| mono | black | white (focus by inversion; red only for faults) | the strictest edition |
| paper | warm paper | oxide red | technical print (light) |
| lab | clinical white | cobalt | the research lab (light) |
| ice | ice haze | electric blue | the 1998 sleeve (light) |
| chrome | brushed aluminium | blue LCD | the modern player skin (light) |
| slate | gunmetal | periwinkle | the skinned desktop |
| ruby | navy in a ruby shell | sky blue | the disc suite |
| aurora (default) | deep indigo | violet, magenta as the counter | the cosmic night of the 2007 desktops |

Ice, chrome, slate and ruby define their own chassis (`shell`, `shell_hi`, `readout`,
`readout_ink`); the others derive one from their palette: gunmetal tinted by the signal on the
dark ones, aluminium on the light ones, and a dark LCD lit in the signal on all of them.

Every text and control pair is checked against WCAG on every build (`build.py --check`):
ink at 7:1 on every surface, labels and status at 4.5:1, control edges and the signal at
3:1, and every console colour at 4.5:1.

## Display tiers

`fui display` picks one; `auto` reads the connected screen.

| Tier | Screens | What changes |
|---|---|---|
| `crt` | tubes (an analog input) | black floor, labels lifted to 7:1 or more, every stroke 2 px, a 3% safe inset at the screen edges, no screen finish ever, static-content protection |
| `lcd` | backlit panels | the editions as they are: 1 px hairlines on the pixel grid, the optional finish |
| `deep` | OLED, HDR, wide gamut (a 10-bit or HDR output) | true black outside the panels (wallpaper, gaps), a Display P3 signal on the start page, static-content protection |

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
| brand | Michroma | the host name, the clock and display numerals (the LCD readouts) |
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

## The parts

| Part | Built as |
|---|---|
| **Panel** | glass: the panel colour at 72% with Hyprland blurring what is behind it (every tier), a rim, 4 px corners; text is checked against the glass over the darkest backdrop |
| **Title strip** | chrome split at the horizon (a bright lip, the lit face, a dark horizon, a lighter reflection), a tracked capital title embossed on it, a code at the right |
| **Field** | pressed in: the well colour, an inner shadow, 2 px corners; focus rings it in the signal; the caret is the signal, blinking at 1 Hz at most |
| **Row** | flat; the selected one is gel |
| **Key** (button) | secondary: a chrome key (`face_*`, its text in `mark`) with a specular band; primary: gel in the signal; destructive: a `bad` ring on hover. 2 px corners |
| **Meter** | segments (`███░░`, block glyphs the data face carries), rounded down, always with the number beside it |
| **Readout** | a label dimmed and tracked, then the value in the data voice: `CPU 12%`; over a threshold the whole readout takes the status colour and the label gains its word. Live values that matter most (the clock) sit in a lit LCD well in the brand face |

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
| Windows (Hyprland) | panels in a chrome chassis (a 2 px gradient frame lit from above; dimmer when unfocused), one soft shadow, 4 px corners |
| Bar (waybar) | the status rail: the badge (the distribution's logo and the operator), workspace keys `01 02 03` (the current one gel), the focused window embossed, labelled readouts, volume and battery meters, the edition and tier, the clock in a lit readout in the brand voice; chrome, boxy |
| Launcher, palette, session, keys, pickers (rofi) | a small device: a chrome title strip with a tracked title and code, a pressed-in search field, a striped list, gel on the selection |
| Notifications (swaync) | tinted plastic slips; a critical one takes `bad`, its summary a solid plate |
| Control centre (swaync) | brushed metal under a chrome strip, rubber-key toggles, boxy gel sliders |
| OSD (swayosd) | an LCD panel in a shell bezel: lit segments, the number glowing in the brand face |
| Lock screen (hyprlock) | authentication: a round frosted panel under a chrome title strip (AUTHENTICATION, AUTH-00), the distribution's logo in the signal, the host and the OS, the clock as the hero value, the operator and kernel as readouts, the passphrase field, the notice |
| Apps (GTK3/4, libadwaita, Qt) | chrome headers, chrome keys, gel on the primary action and the selection, pressed-in fields, readout-well progress and sliders, brushed-metal sidebars, one soft shadow under a window |
| Terminal (kitty) and console tools | the edition's console: 16 colours mapped from the roles (light editions keep a dark console); shell colours are ANSI numbers so everything follows it |
| Browser (Firefox) | a flat tab strip with the stripe, the current tab underlined; the start page is the intranet |
| Start page | a small device: a chrome masthead (the distribution's logo, the host, the OS), readouts (edition, display, operator, node), a pressed-in search with a gel key, a directory with index codes in chrome panels, the clock in a lit readout and a day meter |
| Boot (Plymouth), sign-in (greetd + ReGreet), consoles | the splash fades in the edition's survey field and the machine's logo, host and OS while traces of signal run along the contours, with a 4 px progress line; then the login screen, a boxy chrome shell over the edition's backdrop; the console palette and a sign-in banner with the notice |
| Backdrop | light drawn as fine line work over a haze, in the edition's colours, one of six (each edition opens with its own; `fui wallpaper pick` chooses one for all): **survey** (a topographic map, traces running along its contours), **ribbon** (a sheaf of light lines pinching and fanning), **helix** (two braided strands, the near one bright), **orbit** (a gyroscope of tilted rings, beads travelling them), **fibre** (a fibre-optic lamp, its tips breathing), **mesh** (a wireframe landscape rolling in from the horizon), **veil** (curtains of light hanging in a night sky, the signal fading into the counter colour, stars). Still by default; live, each is a seamless 56 s loop. No text |
| Screen finish | optional (`fui screen toggle`), lcd and deep only: a faint vignette |

## Motion

Expo-out glides (`cubic-bezier(0.16, 1, 0.3, 1)`) and a pop with about 5% overshoot for
windows and pop-ups; presses answer at once (90 ms). Durations: 60 ms (state), 140 (focus),
220 (panels), 400 (screen changes, the takeover). The only thing that moves at rest is the
backdrop. Nothing glitches or blinks faster than once a second.

## Sound

Deep, spacious cues (`make-sounds.py`, all original synthesis): slow detuned pads over a
sub-bass, glassy FM bells with long tails and soft filtered air, placed in a wide stereo hall.
Sign-in is a sub swell, a warm A major 9 pad, a breath and four rising bells; sign-out lets the
bells fall away; a notice is two bells a fifth apart; toggles and volume are a soft cursor
blip; an edition change is a whoosh and a bloom; attention is two round low bells; an error is
a muted fall. Small cues sit quieter than the thresholds. `fui sound off` silences them.

## Don't

- No pills or circles among the parts but radios, LEDs, switches, slider knobs and close buttons; round corners otherwise only on the outer shells.
- No gloss without a job: gel only on the primary action, the selection and the current
  workspace; the shadow only under what floats; glow only on lit readouts and gel.
- No pixel or segment typefaces: the type is the instrument's three voices.
- No borrowed brands, logos or franchise interfaces; no weapons or targeting imagery.
- No fake data: no decorative barcodes, waveforms, hex or progress that isn't progress.
- One signal at a time; status is never colour alone.
- No flashing; no emulated tube effects on a real tube.
- No text on the backdrop.

## The materials

| Material | Job | Where |
|---|---|---|
| Chrome (a bright lip, the lit face, a dark horizon, a lighter reflection; `chrome_*` roles) | the device's chassis | window frames (a 2 px gradient border), the bar, headers, title strips |
| Chrome keys (`face_*`, text in `mark`), with a specular band | pressable | buttons, workspaces, the badge, hovered readouts |
| Gel (`gel_*`, text in `on_gel`), with a specular band | the primary action, the selection, the current workspace | suggested buttons, selected rows, the active workspace |
| Readouts (`readout`, `readout_ink`), glowing | live values | the bar's clock, the lock screen's time, the OSD level, the player |
| One soft shadow | floating | windows (deep and soft under the focused one, light under the rest), menus, tooltips; never between flat panels |
| Unified chrome (one smooth fall of light, no horizon) | a window's header | GTK header bars, Plasma's window frames; flat and quiet when unfocused |
| Source list (`source`: the panel tinted by the signal) | the places beside the content | app sidebars, their selection a band of gel |
| The pointer: the macOS-style set (apple_cursor) | where you are | one theme everywhere: Hyprland, GTK, Qt, XWayland, Plasma and the login screen |

### One family, many parts

Each surface is a different part of the same device, built from the same roles, so the whole
reads as designed rather than skinned:

| Surface | Part |
|---|---|
| Bar | the chrome chassis, keys for the workspaces, a readout for the clock |
| Notification | tinted translucent plastic: the signal's tint, fine ribbing, a sheen along the top |
| Control centre | brushed metal; its switches matte rubber keys, a lit strip along the foot when on |
| Launcher | a chrome title strip, a pressed-in search field, a striped library list, gel on the selection |
| Volume overlay | an LCD panel in a shell bezel: lit segments, the number glowing |
| Window frame (Plasma) | unified chrome, the title left, square gel keys (red gel for close), a 4 px chassis, a soft shadow |
| Panel and pop-ups (Plasma) | round chrome shells; Plasma's own parts on them in the edition's colour scheme |
| App sidebars (GTK) | brushed metal beside the glass content |
| Music player (Audacious) | a chrome shell, square transport keys in a tray, gel play, glowing segment digits |

Parts never borrow each other's material: a notification is never brushed metal, a rubber key
never appears on the bar. Variety comes from the part, not from new colours.

### Two sessions

Hyprland (tiling, no title bars, our bar and tools) and KDE Plasma (the full desktop) are
both offered at the sign-in screen. Plasma keeps its own shell, settings and keys; it is
dressed in the edition rather than rebuilt (theme/kde.py): a colour scheme (keys are chrome
faces printed in the mark, the selection is the signal, headers are chrome), an Aurorae window
frame, a Plasma style whose panel and pop-ups are round chrome shells, the cursor and the
edition's backdrop. `fui plasma apply` points Plasma at the current edition at sign-in and
whenever `fui mode` runs inside it. One keyring (gnome-keyring) serves both sessions.

Material roles exist in every edition (editions without a chassis derive them),
so a component can always resolve them. Contrast is checked for `ink` on the shell and lit
text in a readout, as for every other pair.
