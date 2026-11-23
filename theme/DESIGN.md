# fui design

The desktop follows aljulandani.dev's visual identity: **one person's computer from the 2000s
web. Every surface is a window you can operate, made of frosted, glossy plastic, sitting on a
desk over a quiet network-lattice backdrop.** The references are the Y2K aqua web (carrd
layouts, glossy gel buttons), WindowBlinds skins and the silver Windows Media Player 9 mini
player, with the small rituals of early personal sites: an LCD counter, blinking nav buttons,
a terminal, interface sounds.

It's hand-made and early-web. It's never a sci-fi HUD, neon glyph linework or game chrome.

Tokens: [`tokens.toml`](tokens.toml). Values, contrast table: [`PALETTE.md`](PALETTE.md).
Keys: [`../docs/KEYS.md`](../docs/KEYS.md).

## The window

Every surface is built from the same three parts:

1. **Frame**: translucent, frosted plastic with a 1px bevel (a light edge top-left, a shade
   bottom-right). Radius 10px.
2. **Title bar**: 28–32px, with a hex code and a short title in the pixel face:
   `[0x01] run`, `[0x07] notifications`.
3. **Well**: the inset area where content sits, radius 6px, with an inner shadow.

**Depth comes from bevels and insets only.** No drop shadows, nothing floats.

### Skins (they change only the title bar and frame)

| Skin | Look | Used for |
|---|---|---|
| **Aero** | glossy gel bar (four stops), white pixel-font title; grape / plum / teal by theme | app title bars (GTK headerbars), the launcher, the lock screen, the boot window, Firefox's tab strip |
| **Capsule** | fully rounded aqua-tinted bar with a glass lens | notifications, the volume / brightness OSD |
| **Tab** | flat tinted plate, cut corner, underlined in teal when current | tabs (GTK, Qt, Firefox), window groups |
| **Slab** | slim graphite plate, dark in every theme, steel cap | the control centre's title, tooltips |

## Surfaces

| Surface | Built as |
|---|---|
| Hyprland windows | frosted frame: radius 10, the focused one edged in the theme's gel, the rest in a plain bevel; no shadows |
| Bar (waybar) | the site's menubar strip: `@user` wordmark, white nav-button workspaces (`/1 /2 /3`, the current one blinking), a breadcrumb path, plain mono readouts, an LCD clock |
| Launcher / palette / power / keys (rofi) | an Aero window; rows are white nav buttons, the selected one turns accent |
| Notifications, control centre (swaync) | capsule windows; a slab-titled window with white-button toggles and LCD sliders |
| OSD (swayosd) | a small capsule with an LCD level |
| Lock screen (hyprlock) | a whoami window: gel bar, `@user`, LCD clock, pill password field |
| Apps (GTK3/4, libadwaita, Qt) | gel title bars, gel pill buttons, inset pill fields, wells for views, LCD progress bars, slab tooltips |
| Terminal (kitty) | the site's home terminal: a dark CRT screen in every theme; the tab bar in the theme's gel, tabs titled `[0x01] zsh` |
| Browser (Firefox) | gel tab strip, tab-skin tabs, pill address field; a start page of windows over the lattice |
| Boot (Plymouth), consoles | the boot window over the lattice with an LCD progress bar; the CRT palette and a `[0x00] login` banner |
| Backdrop | the site's network lattice (the same drawing), fading top to bottom; beads travel its lines when live |
| Screen | old-screen glass over everything: a scanline every 3 device pixels, faint RGB phosphor stripes, darker corners |

## Colour

Three themes; **only the colour changes**, never the plastic, shapes or type.

| Theme | Desk | Accent | Gel | Feel |
|---|---|---|---|---|
| dark | near-black | phosphor green | teal | night terminal |
| mid | peach | raspberry | plum | warm |
| light | near-white | blue | grape | clean desk |

- **Fixed materials** stay the same in every theme: the white nav buttons, the grey-green LCD
  glass and its ink, the graphite slab, the dark CRT and its 16 colours.
- **Skin tints** come from one cool family: aqua, teal, steel.
- **Kinds** (cyan, violet, green, amber, rose) colour small labels; a colour never carries
  meaning alone, there is always a word.
- Text pairs are checked against WCAG on every build (`build.py --check`).

## Type

| Role | Face |
|---|---|
| the `@user` wordmark | Michroma |
| structure: labels, readouts, paths, terminals | JetBrains Mono |
| window titles | ProFont IIx, only at 18px or 27px (it is drawn on a 9px grid) |
| LCD digits, only on LCD glass | DSEG7 Classic, bold italic |
| reading: app text | Noto Sans |

Navigation and paths are lowercase: `/home`, `/apps`, `/theme`.

## Motion

- The site's ease, `cubic-bezier(0.2, 0.8, 0.2, 1)`: fast out, long settle.
- The current nav button blinks on a 2 s cycle.
- A theme change is one quick sweep; the wallpaper and app colours follow.

## Sound

The site's synthesised interface cues, rendered as a freedesktop sound theme
(`make-sounds.py`): a soft tick (volume, toggles), a short two-tone cue (opening),
a glassy bell with an echo tail (notifications), a rising glide (theme change), a warm pad
that swells in (login) and falls away (logout). `fui sound off` silences them.

## Don't

- No sci-fi HUD, neon cyber linework or game-interface chrome.
- No drop shadows, floating cards or the generic rounded-card SaaS look.
- No decorative gradients: gloss on a bar or button is the only gradient.
- No fonts beyond the five above, and ProFont only at 18px or 27px.
- No colour alone to carry meaning.
