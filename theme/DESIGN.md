# fui design

**A megacorporation's company-issued workstation, a few decades out.** The desktop feels
institutional, precise and confident: a brand mark, flat engineered panels with hairline
rules, small-caps labels, asset-tag codes, one signature colour per theme, glass where it
helps. It is an original company (`[brand]` in `tokens.toml`), not any film's or game's.

Tokens: [`tokens.toml`](tokens.toml). Values, contrast table: [`PALETTE.md`](PALETTE.md).
Keys: [`../docs/KEYS.md`](../docs/KEYS.md).

## Principles

1. **Engineered, not decorated.** Flat panels, 1px hairlines, consistent radii (6px panels,
   4px controls). No gloss, no bevels, no drop shadows.
2. **One signature colour.** The accent marks focus, the current item, the primary action
   and nothing else. Status colours (ok, warn, bad) only carry status, always with a word.
3. **Labels like a facility.** Section titles are tracked capitals (`DIRECTORY`,
   `SYSTEM CONSOLE`); panels carry an asset code (`DIR-01`, `PWR-05`) in mono, faint.
4. **Data in mono.** Readouts, codes, times and terminals are JetBrains Mono with tabular
   figures; prose and controls are Inter; the company and the clock are Michroma.
5. **The company is present, quietly.** The mark and name appear where the workstation
   identifies itself: sign-in, boot, the bar's badge, the start page, the asset sheet.

## The panel

Every surface is built from the same parts:

| Part | Built as |
|---|---|
| **Panel** | flat glass (85–90% opaque, blurred by Hyprland), a 1px hairline, 6px corners |
| **Header plate** | 34px, the panel colour, a 3px accent stripe at the left, a tracked capital title, an asset code at the right |
| **Field** | set into the panel: the well colour, a hairline, 4px corners; focus draws the accent |
| **Row** | flat; the selected one takes the accent tint and the stripe |
| **Button** | outlined, 4px; the primary action is filled with the accent |
| **Progress** | a 4px accent line on a hairline track |

## Surfaces

| Surface | Built as |
|---|---|
| Windows (Hyprland) | panels: radius 6, a hairline edge, the focused one edged in the accent; no shadows |
| Bar (waybar) | the status rail: the brand badge, workspace segments `01 02 03` (the current one underlined), the focused window, labelled telemetry, the clock in Michroma |
| Launcher / palette / session / keys (rofi) | a directory panel: header plate, set-in search, flat rows |
| Notifications (swaync) | memo cards: a stripe by urgency (accent, bad for critical), the summary in bold, the body in muted |
| Control centre (swaync) | the system console: a header plate, flat toggle tiles, slim sliders |
| OSD (swayosd) | a small plate with the stripe and a slim accent level |
| Lock screen (hyprlock) | employee authentication: header plate, the mark and company, a large clock, operator and node, a passphrase field, the logging notice |
| Apps (GTK3/4, libadwaita, Qt) | header plates, outlined controls, set-in fields, accent selection, slim progress |
| Terminal (kitty) | a night console in every theme; tabs numbered like asset codes, the current one in the accent |
| Browser (Firefox) | flat tab strip with the accent stripe, the current tab underlined; the start page is the company intranet |
| Boot (Plymouth), consoles | the masthead over the network with a slim progress line; the console palette and a sign-in banner with the notice |
| Backdrop | the company network: hairline lattice and nodes, accent data packets travelling it when live; no text |
| Screen | optional finish (`fui screen toggle`): a faint vignette |

## Colour

Three themes; only the colour changes.

| Theme | Floor | Signature | Feel |
|---|---|---|---|
| night | obsidian | signal cyan | night operations |
| concrete | concrete grey | safety orange | industrial floor |
| lab | clinical white | cobalt | research lab |

The terminal is a night console in every theme. Text pairs are checked against WCAG on every
build (`build.py --check`).

## Type

| Role | Face |
|---|---|
| the company, headings, the clock | Michroma |
| interface text | Inter |
| data, codes, terminals | JetBrains Mono |

## Motion

Decisive: quick out, firm settle (`cubic-bezier(0.25, 0.9, 0.25, 1)`), about 220 ms. Nothing
bounces or blinks.

## Sound

Crisp synthetic cues (`make-sounds.py`): a dry tick for toggles and volume, two notes up a
fifth for a notice, an ascending arpeggio over a low swell at sign-in and its mirror at
sign-out, two even pulses for attention, a falling third for an error. `fui sound off`
silences them.

## Don't

- No gloss, bevels, gel bars, drop shadows or neon glow.
- No borrowed corporations, logos or franchise interfaces.
- The accent marks one thing at a time; status is never colour alone.
- No text on the backdrop.
