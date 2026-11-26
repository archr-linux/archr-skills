# Themes reference

Source of truth: `docs/temas.md`, `crates/archr-ui/src/theme.rs`,
`crates/archr-ui/src/layout.rs`, `crates/archr-ui/src/layout/scene.rs`, `crates/archr-ui/src/settings/store.rs`
and `crates/archr-ui/tests/resolutions.rs`
in github.com/archr-linux/archr-launcher. Published examples:
github.com/archr-linux/archr-theme-praia and archr-theme-retro. The 3.1
reference theme, using every key added in 3.1 (sections 6, 8 and 9), is
`themes/ellegance/` in the launcher repository: start from it for shelves,
glass, a sidebar Settings or the capsule OSD.

## Contents

1. Folder layout and inheritance
2. Name and languages
3. Colors
4. Fonts and text
5. Global geometry
6. Style
7. Theme images: background, 9-slice frames, text outline, decorations
8. Views (systems and games screens, shelves, free screens `el`)
9. Fixed-screen rectangles (details, achievements, saves, switcher...)
10. Screen sizes and `[aspect.*]` tables
11. Icons, console art, sounds
12. Test on a PC
13. Test on the device
14. Publish to the Theme store
15. Pitfalls

## 1. Folder layout and inheritance

```
<theme>/
  theme.toml        required, at most 64 KiB
  fonts/            .ttf/.otf named in theme.toml
  icons/            .svg files that replace built-in icons, same file names
  systems/          console pictures: <system>.png | .jpg | .webp
  backgrounds/      per-system screen backgrounds: <system>.png | .jpg (screen size)
  sounds/           <event>.ogg | .wav, sounds/systems/<system>.ogg
  images/ frames/ decor/   any folder names you like for theme images
  preview.png       store cover, 640x480 (store only)
  screenshots/1.png 2.png 3.png   store gallery (optional)
  LICENSE  README.md
```

Installed locations on the device:

- `/storage/.config/archr-launcher/themes/<name>/` user themes (win over system ones)
- `/usr/share/archr-launcher/themes/<name>/` system themes; `default` is "Grafite"

Every key is optional. What a theme does not set comes from the default theme,
key by key. Missing fonts, console pictures, icons and sounds come from the
installed default theme folder. Invalid values fall back to the default with a
warning in the launcher log; nothing in a theme can crash the launcher.

All file paths in `theme.toml` are relative to the theme folder. Absolute paths,
`..`, and symlinks that resolve outside the folder are rejected.

## 2. Name and languages

```toml
name = "Neon"                                                   # all languages
name = { en = "Beach", pt_BR = "Praia", es = "Playa", ru = "Пляж" }  # per language
```

Languages: `en`, `pt_BR`, `es`, `ru`. Lookup: the user's language, then its
base (`pt`), then a plain string, then `en`, then the first entry. Always give
`en`. Without `name`, Appearance shows the folder name and the store refuses
to install the theme.

## 3. Colors

`"#RRGGBB"` or `"#RRGGBBAA"` strings, top level.

| key | used for |
|---|---|
| `background` | screen background |
| `surface`, `surface_elevated` | panels, windows |
| `border`, `badge` | borders, footer button badges |
| `text`, `text_secondary`, `muted`, `dim` | text, strongest to faintest; every unselected list row uses `text_secondary` (collections `muted`) |
| `accent`, `accent_text`, `accent_text_secondary` | selection highlight and text on it |
| `success`, `warning`, `danger` | ok, attention, failure states |
| `scrim` | veil behind notices and menus (use alpha, e.g. `"#05080B99"`) |

Notifications (top-corner cards) use `surface`, `border`, `text`, `text_secondary`, and their kind's color for the icon and time bar: `success` (`icons/check.svg`), `accent` (`icons/info.svg`) or `warning` (`icons/triangle-alert.svg`, also tints the border). A theme that ships its own icons should include `info.svg` and `list.svg` (the long-list marker in Settings).

Legacy aliases: `highlight_bg` = `accent`, `highlight_text` = `accent_text`,
`dim_text` = `dim`. Write the new names.

The user can override the accent and background in Appearance. The first accent
swatch is the theme's own `accent`; picking another color makes the text on it
black or white by contrast. Keep `accent_text` readable on `accent`.

### User options laid over every theme

Appearance also saves several choices in `system.cfg`. None is a `theme.toml` key;
they apply after the theme is read, so a theme cannot declare or disable them.
Choosing another theme (Appearance, or Use in the Theme store) resets every
Appearance choice to its default (as Restore defaults does) and the view to the
theme's first: a theme always arrives as its author made it. Language,
controls, network and sounds are not Appearance choices and stay:

| option (`system.cfg`) | values | effect |
|---|---|---|
| Font weight (`launcher.font_weight`) | theme (empty) / `bold` | `bold` uses the theme's `font_semibold` (`font_mono_medium` with the mono font); no such face, keeps the regular |
| Battery percentage (`launcher.battery_percent`) | on (default) / off | hides the number in the status pill; the icon stays |
| Box art (`launcher.game_art`) | on (default) / off | off removes the games screen `art`, `meta`, `backdrop` and the `panel` that coincides with the art |
| Box art width (`launcher.art_width`) | theme / 35, 40, 45, 50, 55 % of screen width | art keeps its outer edge (away from the list); the list beside it keeps its gap; `meta` follows the art |
| Box art corners (`launcher.art_radius`) | theme / 0, 6, 12, 20 reference px | overrides the view's `art` `radius`; a coinciding `panel` follows (+1 px) |
| Switcher background (`launcher.switcher_curtain`) | theme background / 40, 60, 80 % | selected game's picture fills the screen behind the switcher under a `background`-colored curtain at that opacity; no picture keeps the background |
| Text color (`launcher.text_color`) | theme (empty) / `#RRGGBB` | replaces the theme `text`; `text_secondary` derived (25 % toward `background`) |
| Selected text color (`launcher.selected_text_color`) | theme (empty) / `#RRGGBB` | replaces `highlight_text` (and `accent_text_secondary`) |
| Secondary text color (`launcher.secondary_color`) | theme (empty) / `#RRGGBB` | replaces `muted` (and `dim_text`) |
| Background (`launcher.background`) | theme (empty) / `black` / `midnight` / `#RRGGBB` | custom: `background`, plus `surface`, `surface_elevated`, `border`, `badge` derived by mixing toward white 4/7/12/12 % |
| Text-only button hints (`launcher.text_hints`) | off (default) / on | footer hints draw the button letter alone in the theme `text` color, no badge circle or `badge` frame; START keeps its word without the box |
| System background (`launcher.system_background`) | on (default) / off | on a system's games list and details, the screen background is that system's picture (see `backgrounds/` below) |

These override the view's `[view.*].games` `art` rect/radius. Details that
matter when designing:

- Art off: a list beside the art (left or right) takes the whole width between
  equal margins (its margin on the side away from the art, on both sides). The `panel` is removed only if its `x`/`w` equal
  the art's; a panel with another rect stays drawn.
- Art wider: rebuilt from its outer edge (right edge when the art is right of
  the list, left edge when left of it); the list beside it steps back, keeping
  the gap and its other edge. A list above or below the art is not touched.
- So: place the games list beside the art, keep `art` and `panel` rects equal
  when the panel is the art's card, and make title/info work without the art.
- The curtain is the theme `background`: choose one that works over light and
  dark covers.
- The three text colors replace `text`, `highlight_text` and `muted` after the
  theme is read: do not rely on the exact theme colors for legibility
  decisions. Text-only hints draw in `text`, which must contrast with
  `background`.

## 4. Fonts and text

```toml
font = "fonts/Inter-Regular.ttf"
font_semibold = "fonts/Inter-SemiBold.ttf"
font_mono = "fonts/JetBrainsMono-Regular.ttf"
font_mono_medium = "fonts/JetBrainsMono-Medium.ttf"

font_scale = 1.0       # 0.5..2, multiplies every text size
font_grid = 0          # 0..32 px; sizes snap to multiples (8 for Press Start 2P); 0 = free
font_smoothing = true  # false = hard-edged glyphs, for pixel fonts
font_hinting = "mono"  # "mono" (default, approved on the R36S: stems snapped both ways,
                       # crisper but a little wider), "light" (heights only: the font's own
                       # widths and spacing, as a browser), "none"
font_min = 8           # 6..32 px; nothing smaller, what does not fit wraps
```

`font_min` and `font_grid` are reference px (of the 480 px height) and scale
with the screen. Over them sits a fixed floor of **10 screen px** that no
theme key, `font_scale` or user text size can lower: on a 480×320 screen
that is 15 reference px, so any smaller size is drawn at 10 screen px and
takes more room than it does at 640×480. Start tile labels may go 2
reference px under `font_min` (never under 8), still above the floor. The
ceiling is 128 screen px.

Families come whole: naming `font` or `font_semibold` replaces both (the
regular one stands in for a missing semibold); naming neither inherits both.
Same for `font_mono` + `font_mono_medium`. A named font file that does not
exist falls back to system fonts (DejaVu/Liberation), not to the default theme.
Check that the font covers Cyrillic and Latin accents if you ship `ru`/`pt_BR`/`es` text.

## 5. Global geometry

Two kinds of number, both fractions (> 0 and <= 1):

- **Sizes** (fonts, row/header/footer heights, radii, `margin`, and in
  views `row`, `selected`, `gap`, `font`, `radius`) are fractions of a
  **480 px reference height**: 0.035416667 = 17 px. They keep their
  reference size on every screen.
- **Rectangles** (`cover`, `x y w h` in views and the fixed-screen
  rectangles) are fractions of the **screen**: x and w of its width, y and
  h of its height. They stretch with the screen.

At 640×480 both read as px/480 and px/640. On other screens see section 10.

```toml
font_size = 0.035416667      # 17 px
margin = 0.033333333         # 16 px
radius_item = 0.020833333    # 10 px
radius_card = 0.033333333    # 16 px
header_height = 0.091666667  # 44 px
footer_height = 0.1          # 48 px
row_height = 0.079166667     # systems rows
selected_height = 0.091666667
game_row_height = 0.075      # games rows
game_selected_height = 0.0875
list_width = 0.590625        # games list width
cover = { x = 0.640625, y = 0.1125, w = 0.328125, h = 0.583333333 }
```

These build the classic view `lista`.

## 6. Style

Top level; each applies to all screens including Settings.

| key | values | default | effect |
|---|---|---|---|
| `corners` | 0..1 | `1.0` | multiplies every corner radius; 0 = square |
| `border_width` | 1..8 | `1` | border thickness, reference px |
| `shadow` | `"soft"` `"hard"` `"none"` | `"soft"` | panel shadow (blurred / solid block offset 4 px / none) |
| `art_scaling` | `"smooth"` `"pixel"` | `"smooth"` | console pictures; `pixel` = integer upscale, no filtering. Game covers unaffected |
| `image_scaling` | `"smooth"` `"pixel"` | `"smooth"` | same for theme images (background, frames, decor) |
| `easing` | `"smooth"` `"steps"` | `"smooth"` | `steps` = four equal jumps ("8-bit" motion) |

Animation durations are fixed by the launcher (selection 180 ms, systems to
games 220 ms, ...); a theme picks only the curve. Users can reduce or turn
animations off.

### Shadow, glass, focus, motion, gradient (3.1)

Top level, all optional; a theme that names none draws exactly as before.
Unlike the keys above they reach Settings only when the theme reshapes it
with `[settings]` (section 9). Bad values warn in the log and keep the default.

| key | values | default | effect |
|---|---|---|---|
| `font_bold` | font file | none | titles (system name, game name, shelves, headings) in weight 700; without it they use the semibold |
| `shadow_color` | color | black | colour of the `"soft"` shadow; its alpha scales the shadow |
| `shadow_blur` | 0..0.1 | ~0.033 (16 px) | spread of the soft shadow (size, fraction of 480) |
| `shadow_offset` | -0.05..0.05 | 8 px | how far the soft shadow drops |
| `glass` | `{ fill, border, highlight, blur }` | white 12 %, border 20 %, highlight 25 %, no blur | the glass material a panel picks with `style = "glass"`: the translucent `fill`, a 1 px `border`, a 1 px `highlight` along the top and, behind it, the background blurred by `blur` (fraction of 480; `0` for none), once per image |
| `focus` | `"pill"` `"lift"` | `"pill"` | `lift`: the focused tile/card grows, gains the shadow and a ring (tiles, shelves, library, games grid, Start blocks); a new focus rises on the theme's motion, the first of a screen is up at once |
| `focus_scale` | 1..1.15 | `1.06` | growth with `lift` |
| `focus_ring` | `{ color, width }` | accent, 2 px | the lift ring; `width` 0..8 reference px |
| `motion` | `"tween"` `"spring"` | `"tween"` | `spring`: a critically damped spring that settles in 0.35 s and keeps its speed when the target changes (Animations On only) |
| `gradient` | `{ from, to, angle }` | none | background of systems, games and details; `angle` 0 = left to right, 90 = top to bottom. Also valid in a view's `panel` |
| `title_tracking` | -0.1..0.1 | `0` | letter spacing of titles (text of 20 reference px and up), in em; negative tightens large type (Ellegance `-0.022`, iOS large titles ~-0.02). Body text keeps the font's spacing. Drawn glyph by glyph where the shaped line puts each, merged into one cached texture; measures and ellipses count it |
| `caps_tracking` | 0..0.3 | `0` | letter spacing (em) of the small capitals over a title: the shelves' kicker, the switcher's "2 DAYS AGO", the resume screen's "RETURNING TO", the game menu's sections. Ellegance `0.12` |

```toml
font_bold = "fonts/Inter-Bold.ttf"
shadow_color = "#000000F0"
shadow_blur = 0.075
shadow_offset = 0.0375
glass = { fill = "#FFFFFF14", border = "#FFFFFF1F", highlight = "#FFFFFF29", blur = 0.05 }
focus = "lift"
focus_scale = 1.05
focus_ring = { color = "#F5F5F7EB", width = 2 }
motion = "spring"
gradient = { from = "#121219", to = "#07070A", angle = 90 }
```

A font family is whole: a theme naming `font`, `font_semibold` or `font_bold`
uses only its own files, so ship all three when you add a bold face.

## 7. Theme images

Only on the systems, games and details screens, never in Settings. PNG or JPG.
They load off the render thread, so the first frame may show the plain box.

```toml
background_image = "images/background.png"   # covers the screen, center-cropped
                                              # with image_scaling = "pixel", draw it at 320x240 for 2x2 pixels

text_outline = { color = "#3F2214", width = 2, ink = "#FFFFFF" }
# width 0..4 reference px; ink (optional) recolors that text.
# Applies to text drawn straight on the background: header, footer hints,
# the system name when the view has no panel.
```

### 9-slice frames

```toml
[frames.row]
image = "frames/row.png"
slice = [6, 5, 6, 7]   # image px kept whole: left, top, right, bottom (or one number), 0..256
scale = 2              # screen px (480 reference) per image px, 0.25..8
pad = 0                # how far the frame reaches beyond the box, ref px, 0..64 (or [l, t, r, b])
tile = false           # true = edges and middle repeat instead of stretching
```

Frame names (anything else is ignored): `header`, `footer`, `list`, `row`,
`selected`, `panel`, `art`, `button`, `button_selected`, `badge`, `tile`,
`tile_selected`. Text on frames keeps the normal colors (`text_secondary` on
rows, `accent_text` on the selected row, `text`/`muted` on panels, `text` on
badges).

### Decorations

Per view and screen:

```toml
[view.lista.systems]
decor = [
  { image = "decor/palm.png", x = 0.88, y = 0.02, scale = 2 },
  { image = "decor/wave.png", x = 0.0, y = 0.82, scale = 2, layer = "back" },
  { image = "decor/crab.png", x = 0.02, y = 0.8, scale = 2, frames = 2, fps = 2 },
]
```

`x`, `y`: top-left corner, screen fractions. `scale` 0.25..8. `frames` (1..64)
are laid side by side in the image and change `fps` (0..30) times a second
(still when animations are off). `layer = "back"` draws behind lists and
panels; default front. A `decor` list replaces the inherited one; `decor = []`
clears it. The details screen uses the games screen decorations.

### Per-system backgrounds (`backgrounds/`)

New theme feature, no `theme.toml` key. On a system's games list and game
details, with the System background option on, the screen background is
`<system>.png` or `.jpg` (system id as in es_systems: `snes`, `gba`, `psx`...).
Lookup: user folder `/storage/.config/archr-launcher/backgrounds/`, then the
theme `backgrounds/`, then the default theme `backgrounds/`. Drawn covering the
screen (cropped to fill) under a curtain of the theme `background` at ~59 %
opacity (alpha 150); it replaces `background_image` on those screens.
Collections (`@favorites`, `@recent`) keep the theme background. Pictures are scaled
to the screen when they load; ship them at screen size (640x480, 720x720 or
1280x720) so they load fast on the device.

## 8. Views

A view positions the elements of the systems screen and the games screen. The
user picks a view in Appearance › View. Every view starts from `lista` and
changes only what it writes. A theme inherits the default theme's views
(`lista` and `vitrine`), can override them and can add new ones.

```toml
[view.side]
name = { en = "Side", pt_BR = "Lado", es = "Lado", ru = "Сбоку" }

# Moving the list means moving everything that sat where it goes:
# on the games screen the cover lives in panel + art + meta.
[view.side.games]
list = { x = 0.4, w = 0.575 }
panel = { x = 0.025, w = 0.328125 }
art = { x = 0.025, w = 0.328125 }
meta = { x = 0.025, w = 0.328125 }
```

A table on an element changes only the fields it writes; the others keep
their inherited values (`list = { x = 0.4, w = 0.575 }` keeps `y`, `h`, `row`
and the rest).

Where `lista` puts things with the default geometry (the starting point of
every view), as fractions:

| screen | element | x | y | w | h |
|---|---|---|---|---|---|
| systems | `list` | 0.01875 | 0.104167 | 0.55 | 0.783333 |
| systems | `panel` | 0.590625 | 0.104167 | 0.390625 | 0.779167 |
| systems | `art` | 0.621875 | 0.2 | 0.328125 | 0.333333 |
| systems | `info` (bottom-aligned) | 0.615625 | 0.104167 | 0.340625 | 0.75 |
| games | `list` | 0.01875 | 0.104167 | 0.590625 | 0.783333 |
| games | `panel`, `art` (= `cover`) | 0.640625 | 0.1125 | 0.328125 | 0.583333 |
| games | `meta` | 0.640625 | 0.714583 | 0.328125 | 0.041667 |

`vitrine` (inherited from the default theme) removes the systems `panel` and
`art`, uses `mark = "tile"`, and on games adds a `backdrop`; read its values in
the default theme if you override it.

Draw order, back to front: `decor` with `layer = "back"`, `backdrop`, header,
`list`, then `panel`, `art`, `info`, `dots` (systems) or `panel`, `art`,
`meta` (games), footer, front `decor`. The panel is drawn over the list, so
an element left in its old place hides the list you moved under it.

Elements of `[view.<id>.systems]` and `[view.<id>.games]`:

| key | what | fields |
|---|---|---|
| `header` | header | `"full"` (name and counter) or `"compact"` (one muted line) |
| `title` | systems/Start title | `"brand"` (spaced ARCHR) or `"screen"` (localized screen name) |
| `status` | clock/battery pill | bool |
| `divider` | line above footer | bool |
| `summary` | library summary in footer (systems) | bool |
| `list` | the list | `x y w h`, `row` (0.02..1), `selected` (>= row), `gap` (0..0.5), `font`, `selected_font` (0.01..0.3), `radius` (0..0.5), `mark`, `scroll`, `cursor`, `axis` |
| `panel` | raised card | `x y w h`, `radius` |
| `art` | console picture / game cover | `x y w h`, `fit` (`"contain"`/`"cover"`), `radius` |
| `backdrop` | cover behind the games screen | `opacity`, `solid` (fraction of width in plain background), `edge` (background opacity at right edge), all 0..1 |
| `info` | system name and details | `x y w h`, `title`, `meta` (sizes 0.01..0.3), `align` (`left`/`center`/`right`), `valign` (`top`/`bottom`), `details` (`stacked`/`inline`) |
| `meta` | year, players, last played under the cover | `x y w h`, `size` |
| `dots` | position dots between systems | `x y w h` |
| `decor` | images (section 7) | list of tables |

List values:

- `mark`: `"pill"` (filled band), `"bar"` (small bar beside the text), or
  `"tile"` (systems screen only: tiles side by side, the selected one large in
  the center with the console picture; forces a horizontal row).
- `scroll`: `"edge"` or `"center"` (keeps the selection in the middle).
- `cursor`: up to 4 characters drawn before the selected entry, blinking
  (e.g. `"▶"`; the font must have the glyph). Not for tiles.
- `axis`: `"vertical"` or `"horizontal"`.

Optional elements (`panel`, `art`, `backdrop`, `info`, `meta`, `dots`) are
removed with `false` (`panel = false`) and added with a table. View rectangles
are clamped to the screen (`w` limited to `1 - x`, `h` to `1 - y`), with a
warning.

Since 3.1, also: `panel.style` (`"plain"` or `"glass"`), `panel.gradient`
(`{ from, to, angle }` or `false`), `opacity` (0..1) on `list`, `panel`,
`art`, `info` and `meta`, and on the games screen `list.mark = "grid"` (covers
in a grid with the name under each; `columns` 1..8, `row` = cover height,
`gap`, `font`, `radius`; L1/R1 change system) with `strip = { x, y, w, h }`,
the strip of systems above the grid.

### Shelves (3.1)

A view can open on shelves instead of the systems list: tabs on top (Home,
Library, Favorites), the focused item as a hero, rows of items below.
`home = true` turns them on with the defaults; `[view.<id>.home.*]` tables
change them (not both: TOML forbids `home` being a value and a table).

```toml
[view.lista.home.tabs]
items = ["home", "library", "favorites"]
rect = { x = 0.306, y = 0.029, w = 0.388, h = 0.071 }
style = "glass"
[view.lista.home.hero]
rect = { x = 0.05, y = 0.154, w = 0.469, h = 0.313 }
art = { x = 0.55, y = 0.146, w = 0.409, h = 0.313, fit = "contain" }
backdrop = { blur = 0.108, opacity = 0.6 }
actions = ["play", "favorite", "more"]
title = 0.071
[view.lista.home.shelves]
order = ["continue", "systems", "apps"]   # also "favorites", "collections"
y = 0.5125
gap = 0.033
title = 0.027
[view.lista.home.shelves.continue]
item = { w = 0.2625, h = 0.196, radius = 0.033 }
[view.lista.home.library]                 # the Library tab's grid of systems
rect = { x = 0.05, y = 0.233, w = 0.9, h = 0.733 }
columns = 3
item = 0.275
gap = 0.029
radius = 0.042
[view.lista.home.heading]                 # big title of Library, Favorites and the games grid
x = 0.05
y = 0.117
w = 0.9
h = 0.092
size = 0.0625
```

Those are the defaults (Ellegance at 640x480). `rect`, `art`,
`library.rect`, `heading` and `item.w`/`item.h` are screen fractions; `radius`,
`title`, `gap`, `size` and `library.item` are sizes (fraction of 480). Empty
shelves disappear. `decor` works inside `home` too. There is no `progress`
key on a shelf (removed before 3.1 shipped: the launcher has no measure of how
far a game has gone, and a bar without one would lie); precheck warns on it.

On Home, Up from the first shelf moves the focus to the hero's `actions`
(Continue/Play, Favorite, More; a system or app only Open): Left/Right walk
them, A presses (Continue resumes, Favorite toggles with the star in
`warning`, More opens the game menu beside the button), Down or B go back.

A theme cannot pick the view a user starts on: it is `launcher.view`, `lista`
on a fresh install. To open on the shelves by default, put them in your own
`[view.lista]` and offer the classic list under another id (Ellegance:
`[view.classica]`).

### Free screens (`el`, since update 20261125.15; phase 2 in 20261125.16)

The systems and games screens of a view can be a **list of elements**
instead of the fixed places above (`list`, `panel`, `art`, `info`...): full
art per system, cut-out frames over the content, rotated text, several texts
and pictures with system and game data (the EmulationStation way). Source:
`docs/temas.md` "Telas livres", `crates/archr-ui/src/layout/scene.rs`,
`crates/archr-ui/src/render/scene.rs`; a working test theme with two views
(Solo, Albedo) is `crates/archr-ui/tests/themes/cena/theme.toml`.

Use it only when the fixed places cannot give the look. Colors, fonts and
moving list/art are simpler in the view table.

A screen is free when its table has `[[view.<id>.systems.el]]` or
`[[view.<id>.games.el]]` entries. Nothing else changes: Details, Start, menus
and Settings keep their tables. On a launcher older than 20261125.15 `el` is
an unknown key: the view draws from its fixed places (the inherited ones if
the theme gives none).

```toml
[view.solo]
name = { en = "Solo", pt_BR = "Solo", es = "Solo", ru = "Соло" }

[[view.solo.systems.el]]
id = "art"
kind = "image"
src = ["arts/${system}.jpg", "arts/default.jpg"]
fit = "cover"

[[view.solo.systems.el]]
id = "list"
kind = "list"
rect = { x = 0.6, y = 0.15, w = 0.36, h = 0.68 }
row = 0.075
size = 0.04
mark = "bar"
scroll = "center"
z = 10

[[view.solo.systems.el]]
id = "count"
kind = "text"
text = "${system.games}"
rect = { x = 0.5, y = 0.868, w = 0.448, h = 0.05 }
align = "right"
size = 0.032
shadow = { color = "#000000A0", x = 0.002, y = 0.002 }
z = 20

[[view.solo.systems.el]]
id = "hints"
kind = "hints"
rect = { x = 0.565, y = 0.94, w = 0.41, h = 0.05 }
style = "outline"
color = "#FFFFFF"
z = 50
```

Rules that bite:

- The screen draws **nothing by itself**: header, footer, clock (`status`)
  and button hints (`hints`) appear only as elements.
- Draw order: lowest `z` first; equal `z` keep file order.
- `el` lists never merge: the theme's list replaces the inherited one whole;
  `el = []` brings the fixed places back. An `el` inside
  `[aspect.<shape>]` replaces the whole list on that shape, so prefer
  `when = { aspect = "square" }` on single elements.
- One `list` element per screen (a second is ignored). Without one the d-pad
  still moves through an unseen list.
- Unknown field, wrong type or out of range: log warning, field dropped or
  clamped. Unknown `kind` or an image with no source: element dropped.

**Common fields** (every kind): `id` (name, for `base`), `kind`, `rect`
`{ x, y, w, h }` in **screen fractions** (default the whole screen; x/y
-1..2, w/h up to 4, may go off screen), `anchor` (`top-left` default, `top`,
`top-right`, `left`, `center`, `right`, `bottom-left`, `bottom`,
`bottom-right` or `[x, y]`: the rectangle's point placed at x, y), `z`
(-1000..1000, default 0), `opacity` (0..1), `rotate` (degrees -360..360,
clockwise), `pivot` (`[x, y]` of the rectangle, default `[0.5, 0.5]`),
`when`, `base`.

**Sizes inside an element** (`size`, `row`, `radius`, shadow offsets) are
fractions of the **screen height** (0.035 = 17 px at 480 tall, 25 px at
720), not of the 480 reference used elsewhere. The 10 px text floor holds.

| `kind` | own fields |
|---|---|
| `image` | `src`, `fit` (`contain` default, `cover`, `stretch`), `align` (`left`/`center`/`right`, for a narrower `contain`), `tint` (color multiplied in), `radius`, `fallback` (one more theme path), `fallback_text` (text or a table of text fields, drawn when no source exists) |
| `text` | `text`, `font` (`regular`/`semibold`/`bold`/`mono` or a `.ttf` in the theme), `size` (0.01..0.3, default 0.035), `color` (default theme `text`), `align`, `valign` (`top`/`middle`/`bottom`), `upper`, `shadow` `{ color, x, y }`, `wrap` (ends in "…"), `fit_text` (`ellipsis` default, `shrink` down to 60 % of size), `line` (0.8..3, default 1.25) |
| `rect` | `fill`, `border` (colors), `radius`, `gradient` `{ from, to, angle }` |
| `frame` | `image`, `slice` (number or `[l, t, r, b]`), `scale` (0.25..8), `tile` (9-slice over the rectangle) |
| `panel` | `radius`, `style` (`plain`, `glass`), `gradient` |
| `list` | `row`, `gap`, `radius`, `selected` (height or `{ height, fill, color }`), `size`, `selected_size`, `color`, `mark`, `scroll`, `cursor`, `axis`, `columns` (as the view's `list`; `tile` only on systems, `grid` only on games) |
| `hints` | `align` (default `right`), `style` (`filled`, `outline`, `text`), `color`, `badge`, `letter_color` |
| `status` | `color` (with it: icons and text straight on the screen, no pill) |
| `rating` (20261125.16) | `game.rating` as five stars rounded to halves: `star`, `star_half`, `star_empty` (theme pictures; default the launcher's star, half = full cut over an empty, empty = full in `empty`), `color` (multiplies the full star; default theme `text` on the launcher star, none on a theme picture), `empty` (color), `empty_opacity` (0..1; 0.35, or 1 with `empty`/`star_empty`), `size` (one star's side, 0.005..0.3 of the height; default the rect height), `spacing` (0..0.2; default a fifth of a star), `align` (default `left`), `value` (may only be `"game.rating"`). No rating: nothing drawn |
| `fields` (20261125.16) | a label/value card: `rows` (required list of `{ label, value }` or `{ label, rating = "game.rating" }`, both take `${data}` and `@phrase`), `hide_empty` (default true: an empty line disappears, the ones below move up; the rating line disappears without a rating), `row` (line height, 0.01..1; default rect / lines), `font`, `size` (0.03), `color` (values, right-aligned, shrink to 60 % then "…"), `label_font`, `label_size`, `label_color` (default the theme's `muted`), `upper_labels`, `divider` (color of a thin line under each line), and the rating line's `star`, `star_half`, `star_empty`, `empty`, `empty_opacity`, `spacing`, `align` (default `right`), `star_size` (default the value size; color = `color`). Lines past the rect are left out |

**Image sources**: `src` is a path or a list, first existing wins; paths are
relative to the theme (no `..`) and may hold data (`arts/${system}.jpg`,
`frames/${aspect}/border.png`). Besides paths, `src` takes the launcher's
pictures:

| source | what it is |
|---|---|
| `game.cover` | focused game's cover (`<thumbnail>`, else `<image>`) |
| `game.screenshot` | its screenshot (`<image>` when there is a cover, or `media/screenshots`) |
| `game.logo` | game logo (`<marquee>` or `media/wheel`); `game.wheel` and `game.marquee` are aliases |
| `system.logo` (20261125.16) | the theme's `logos/<system>.svg/.png/.webp/.jpg`, also under the system's alias (`megadrive` finds `genesis`) |
| `system.image` (20261125.16) | the system picture the launcher shows: the user's, the theme's `systems/`, or the shipped one |

`src = ["system.logo", "system.image"]` plus `fallback_text` gives the
theme logo, else the built-in picture, else the name. These five are
pictures, not text: valid in `src` and `when.has`, not in `${...}`.
PNG, JPG, WebP, SVG; loaded off the draw thread, shrunk to at most 1.5x the
screen and never enlarged (the screen scales smaller ones; cache
`thumbs/scene`); the element is absent until loaded. On the systems screen
the two neighbours' pictures preload after the focused one's (a full-screen
art takes 0.3-1 s cold on the RK3326).

**Data** (`${...}` in `text` and paths): `system` (id; a collection without
`@`), `system.name`, `system.maker`, `system.year`, `system.count` ("213"),
`system.games` ("213 games", localized), `system.favorites`, `game.name`,
`game.description`, `game.genre`, `game.developer`, `game.publisher`,
`game.year`, `game.players`, `game.rating` (0..5, one decimal),
`game.last_played` ("2 days ago"), `list.index` (from 1), `list.total`,
`item` (system id or game file name), `aspect` (`classic`/`square`/`wide`).
`game.*` is empty on the systems screen. An unknown name stays literal with
a warning. Empty text draws nothing.

**Phrases**: `text = "@key"` (the whole value) is a launcher phrase in the
user's language: `@description`, `@last_played` (free screens), `@genre`,
`@players`, `@released`, `@developer`, `@publisher`, `@rating` (Details) or
any catalog key (`@hint.play`). Use them instead of hard-coded labels so the
four languages work.

**Variables**: a top-level `[vars]` table (and `[aspect.<shape>.vars]` to
change them per shape). A value that is exactly `"$name"` becomes the
variable with its type (color, number, path); `${name}` inside a string is
its text. Works in the whole file, top-level keys included
(`accent = "$gold"`). Data names are never variables. Unknown variable:
warning, value kept literally.

**Conditions**: `when = { system = [...], aspect = ..., has = "game.year" }`,
each a name or a list, all keys must hold. A failing element is not drawn
and does not load its picture.

**Reuse**: `base = "systems.hints"` (or `"hints"` on the same screen) copies
an element of the same view; written fields override.

**Appearance options**: Box art, its width and corners and System background
do nothing on a free screen. Accent, text colors, background and text-only
hints apply to list, hints and status when the element sets no color.

**Not there yet** (keys warn and are dropped): system carousel or wheel, a
grid with an item template (logo over it, favorite badge), video, theme
options in Appearance, `include`,
per-element animations, Details as a scene. Say "not available yet" instead
of inventing keys.

**Test**: every block above is checked the launcher's way: parse it with
`Theme::parse` and build each view at 640x480, 720x720 and 1024x768 with no
log warning (`crates/archr-ui/tests/scene_render.rs`,
`every_example_of_the_docs_chapter_reads_without_warnings`). For a theme,
`cargo test -p archr-ui --test shipped_themes` with the folder copied into
`themes/` fails on any warning, and the `scene_render` test shows how
captures wait for pictures (`ui.pictures_idle()`) before saving a frame. On
the device, check the launcher log for `Theme view.<id>.<screen>.el[...]`
warnings.

## 9. Fixed-screen rectangles

Top-level `{ x, y, w, h }` tables, valid for every view. Each must fit on screen
(`x + w <= 1`, `y + h <= 1`, all values 0..1); an invalid one reverts to the
default as a whole (it is not clamped). Defaults:

```toml
# Game details (Y › Details)
details_shot = { x = 0.0375, y = 0.104166667, w = 0.390625, h = 0.3125 }     # screenshot (or cover)
details_info = { x = 0.0375, y = 0.4375, w = 0.390625, h = 0.445833333 }     # genre, players, release, developer, publisher, rating
details_title = { x = 0.45625, y = 0.104166667, w = 0.50625, h = 0.095833333 } # logo or name
details_subtitle = { x = 0.45625, y = 0.216666667, w = 0.50625, h = 0.033333333 }
details_text = { x = 0.45625, y = 0.266666667, w = 0.50625, h = 0.529166667 }  # description, scrolls
details_actions = { x = 0.45625, y = 0.8125, w = 0.50625, h = 0.070833333 }    # Play, Favorite, Scrape again
# Start menu module widgets (up to 2 side by side); clamped to start below 178 px,
# at least 40 px tall, ending above the shortcuts
start_widgets = { x = 0.153125, y = 0.454166667, w = 0.69375, h = 0.216666667 }
# Achievements (Y › Achievements)
achievements_progress = { x = 0.025, y = 0.108333333, w = 0.94375, h = 0.0625 }
achievements_list = { x = 0.025, y = 0.183333333, w = 0.94375, h = 0.7125 }     # 50 px rows
# Saves and Screenshots
saves_list = { x = 0.01875, y = 0.1, w = 0.4875, h = 0.783333333 }
saves_card = { x = 0.53125, y = 0.1, w = 0.440625, h = 0.783333333 }
shots_grid = { x = 0.040625, y = 0.108333333, w = 0.91875, h = 0.791666667 }
# Switcher (FN during a game) and resume at power on
switcher_card = { x = 0.1875, y = 0.108333333, w = 0.625, h = 0.625 }
switcher_side = { x = 0.046875, y = 0.129166667, w = 0.375, h = 0.375 }  # w,h,y = neighbours' size/top; x = gap to the card
switcher_info = { x = 0.0, y = 0.758333333, w = 1.0, h = 0.125 }
resume_shot = { x = 0.25, y = 0.110416667, w = 0.5, h = 0.5 }
resume_info = { x = 0.0, y = 0.6375, w = 1.0, h = 0.258333333 }
# Start menu: the box its 640x480 composition is centered in (section 10)
start_area = { x = 0.0, y = 0.0, w = 1.0, h = 1.0 }
```

`start_widgets` is a fraction of the Start menu's 640×480 composition (x of
640, y of 480), not of the screen; `start_area` places that composition.

Colors on these screens come from the general color keys. Text never gets
ellipsized: it shrinks and wraps; table rows that do not fit are omitted.

Fixed layouts a theme cannot move: the ROM migration screen (always the
default theme). Settings are 640 reference px wide, centered on wider
screens, more rows on taller ones; until 3.0 only colors, fonts and icons
applied there, since 3.1 `[settings]` reshapes them (below).

### One table per screen (3.1)

Each screen can have a top-level table, outside `[view]` (it applies to every
view). Every key is optional and inherits from the default theme; an unknown
key or a wrong value warns and keeps the default. Without the table, or the
style key, the screen draws as always. The rectangles above also live here
(`[details] shot`, `[saves] preview` = old `saves_card`, `[start] area`...);
when both spellings appear, the table wins.

| table | keys (style words) |
|---|---|
| `[toast]` | `position` (`top-left` `top` `top-right`), `width` (size, default 0.575), `icon` (`circle` `square` `none`), `style` (`glass` `plain`) |
| `[hints]` | `style` (`bar` `capsule`), `position` (`left` `center` `right`), `lit` (bool: A's badge and label in `text`, the others in `text_secondary`); use `divider = false` in the view with the capsule. A layer (question, menu, keyboard, an app's question/keyboard) shows only its own hints at full brightness; on the keyboard sheet they sit inside the sheet |
| `[status]` | `style` (`glass` `plain`), `battery`, `radios` (bool), `clock` (`mono` `text`), `rect` |
| `[header]` | `style` (`path` `capsule`): Achievements, Saves, Screenshots and Search trade the path in text for "‹ game" in a glass capsule (the details hero's) with the screen title 28 px bold on its own line under it; their rectangles start 44 px lower and end where they did. With the ring achievements the title sits beside the ring (nothing moves); the save preview's picture shrinks before its note is cut; the field search drops capsule and clock, field at the top with Cancel in the accent beside it |
| `[dialog]` | `width`, `radius`, `icon` (bool), `buttons` (`row` `hints`), `style`; destructive answers turn `danger`. With the table, the save/screenshot question (delete, play from a state) is a centered alert: icon disc in the action's color, question 16 px and text centered, Cancel and the action side by side; with `row` the action is always filled (red when it deletes) and the focused answer gets `focus_ring` |
| `[start]` | `style` (`tiles` `control`: control center over the blurred previous screen), `radius`, `shortcut`, `clock` (a size, or a rect with `size` inside: where the hour stands), `tiles` (rect: the three blocks), `shortcuts` (rect: the round shortcuts, centered), `area`, `widgets` |
| `[menu]` | `style` (`list` `context`: glass card beside the focused item with Play/Favorite/Details; from Details or the hero's buttons, beside the focused button), `anchor` (`focus` `center`), `width`, `row`, `radius`, `rect` (a fixed box; the list scrolls inside) |
| `[details]` | `style` (`panels` `hero`: full screen, blurred art, big bold title), `shelf` (bool, "More from <system>"), `shot` `info` `title` `subtitle` `text` `actions` (not used by `hero`) |
| `[achievements]` | `progress` (rect, `"ring"`/`"bar"`, or a rect with `style`), `list`, `style` (`plain` `glass`), `row`, `gap`, `badge`, `badge_radius` |
| `[saves]` | `style` (`list` `preview`: big 4:3 preview, slots in glass), `preview`, `list`, `row`, `thumb` |
| `[shots]` | `sections` (bool: "This week" / "Earlier"), `columns` (0 = as many as fit), `gap`, `radius`, `grid` |
| `[switcher]` | `cards` (`row` `depth`), `card`, `side`, `info` |
| `[resume]` | `style` (`picture` `title`), `shot`, `info`, `progress` (rect: the countdown bar), `backdrop = { blur, opacity }` (the game's picture behind; blur 0 = sharp) |
| `[search]` | `style` (`plain` `field`: glass field, results in glass, docked keyboard), `row`, `height`, `field` (rect), `results` (rect), `dock` (`bottom` `results`: the keyboard on a card right under the results, never moving) |
| `[keyboard]` | `sheet` (bool: text editing on a glass sheet, as tall as it holds, docked over the dimmed page), `key = { h, gap, radius }` (enlarge in `[aspect.square.keyboard]`) |
| `[osd]` | `style` (`pill` `capsule`), `position` (`right` `left` `top` `bottom`), `fill`, `track` (colors), `radius` |
| `[settings]` | `layout` (`list` `sidebar`), `sidebar = { x, w, style, title }` (x, w fractions of the 640 px Settings width), `row`, `icon` (`plain` `tile`), `groups` (`flat` `inset`), `title` (`beside` `below`: page title 28 px bold on its own line under the "‹ Parent" capsule; the page moves down 36 px and ends where it did), `[settings.icon_colors]` |

`[settings.icon_colors]` keys: `network`, `sound`, `controls`, `games`,
`region`, `appearance`, `launcher`, `achievements`, `system`, `storage`
(defaults `#0A84FF #FF375F #30B050 #FF7A00 #5E5CE6 #BF5AF2 #30B0C7 #D98E04
#6E6E76 #1E9BD7`).
With any `[settings]` key off its default, the theme's style (`corners`,
`border_width`, shadow, glass, `easing`, `motion`) and `font_bold` titles
also apply in Settings; the focused row becomes a translucent panel with
`focus_ring`. With `groups = "inset"` Wi-Fi heads the scanned networks with
"NETWORKS" and a spinner while it searches.

Layouts adapt to the height: on 720x720 the hero details centre their block
and stop growing the shelf, the search rows grow up to 40 %, the keyboard
sheet keeps its own height. Glass over a dimmed screen (dialog, sheet, toast)
gets the theme's `surface` under it. Footers of progress screens and
achievements take `[hints]` (no rule above a capsule).

`[osd]`: archr-osd does not read `theme.toml`. The launcher writes the
resolved active theme to `/run/archr-launcher/osd-theme.toml` whenever the
appearance changes; the OSD rereads it. Its cards (battery, report, disk)
take the theme's colors and `font`/`font_semibold`.

```toml
[start]
style = "control"
[menu]
style = "context"
[details]
style = "hero"
[achievements]
progress = { x = 0.05, y = 0.11, w = 0.9, h = 0.18, style = "ring" }
style = "glass"
[settings]
layout = "sidebar"
icon = "tile"
groups = "inset"
title = "below"
[settings.icon_colors]
network = "#0A84FF"
[osd]
style = "capsule"
position = "right"
```

## 10. Screen sizes and `[aspect.*]` tables

The 640×480 design is scaled by `min(width/640, height/480)` so it fits
whole; the spare room goes to the longer side.

| screen | devices | scale | reference px | shape |
|---|---|---|---|---|
| 640×480 | R36S, most RK3326 handhelds | 1 | 640×480 | `classic` |
| 720×720 | R36 Plus | 1.125 | 640×640 | `square` |
| 480×320 | Odroid Go Advance, RGB10, RG351M (portrait panel turned by Sway) | 0.667 | 720×480 | `wide` |
| 854×480 | 16:9 | 1 | 854×480 | `wide` |
| 1024×768 | 4:3 | 1.6 | 640×480 | `classic` |
| 1024×600 | RK3562 handhelds | 1.25 | 819×480 | `wide` |
| 1280×720 | 16:9, RG43V PRO / RG52 MINI (RK3562) | 1.5 | 853×480 | `wide` |

Shape from width/height: `square` below 1.2 (6:5), `classic` 1.2 to 1.45
(29:20) inclusive, `wide` above 1.45. Code: `Aspect::of` in
`crates/archr-ui/src/theme.rs`.

Consequences with no `[aspect]` table at all: sizes keep their reference px,
so a square screen shows more list rows of the same height (Grafite: 10
game rows at 640×480, at least 13 at 720×720); rectangles stretch, so a
portrait cover gets taller and narrower, except the game pictures of the
Switcher (`switcher_card`, `switcher_side`) and of the resume screen
(`resume_shot`), which always stay 4:3, centered in their rectangle
(`picture_pixels` in `render.rs`), so they never stretch on 16:9; the built-in `lista` geometry
(250 px system panel, margins) is computed in reference px for the real
screen and does not stretch.

`[aspect.square]`, `[aspect.classic]`, `[aspect.wide]` hold any top-level
key, including `[view.*]`, `frames`, `background_image`, `text_outline`,
`font_size`, `font_scale`, `font_min`, and every rectangle. The matching
table is laid over its own file key by key: tables (views and their
elements) merge field by field, other values replace; a top-level rectangle
(`cover`, `details_*`, `switcher_*`, `start_area`...) replaces whole, so give
all four fields. Other names (`[aspect.tall]`) are ignored with a warning.

```toml
# ...all top-level keys first...

[aspect.square]
switcher_card = { x = 0.1875, y = 0.1, w = 0.625, h = 0.46875 }
start_area = { x = 0.0, y = 0.1796875, w = 1.0, h = 0.75 }

[aspect.square.view.lista.games]
list = { w = 0.5 }
art = { x = 0.55, w = 0.4, h = 0.7 }

[aspect.wide]
font_size = 0.039583333   # 19 reference px = 13 px on 480x320
```

Merge order: default theme, the default's `[aspect.<shape>]`, the theme,
the theme's `[aspect.<shape>]`. So:

- A theme with no `[aspect]` table inherits Grafite's. Grafite's
  `[aspect.square]`: 4:3 switcher and resume pictures, the Start menu
  centered between header and footer (`start_area`), `list_width = 0.5`
  with `cover = { x = 0.555, y = 0.1125, w = 0.41, h = 0.583333333 }`,
  details picture and table sharing the column, console art centered in
  the systems panel, a wider `vitrine` cover. Grafite's `[aspect.wide]`:
  `font_size = 0.039583333` and `vitrine` games list `font = 0.0375`.
- A top-level key in the theme beats the default's aspect value for every
  shape. A theme that sets `cover` or `list_width` at the top level loses
  Grafite's square cover and list; it needs its own `[aspect.square]`
  (Praia: `[aspect.square.view.lista.games]` with list, panel, art and meta).
- Font files (`font`, `font_semibold`, `font_mono`, `font_mono_medium`),
  `name`, sounds, icons and console pictures do not change per shape.

**Text floor**: no text under 10 screen px at any size (section 4). The
only exception is the MangoHud preview miniature in Settings.

**`start_area`** (`{ x, y, w, h }`, screen fractions, default the whole
screen): the box the Start menu composition (title, tiles, shortcuts,
widgets) is centered in. The composition is 480 reference px tall and as
wide as the box; tiles may reach its edges; the footer stays at the bottom
of the screen. Keep it at least 480 reference px tall (on 720×720, `h =
0.75`) or the composition is squeezed.

## 11. Icons, console art, sounds

**Icons**: `icons/<name>.svg` replaces the built-in icon of the same file name
(the names are those in `themes/default/icons/` of the launcher repository,
Lucide names such as `wifi.svg`, `battery-full.svg`, `star.svg`,
`triangle-alert.svg`). Draw with `stroke="currentColor"`/`fill="currentColor"`;
the launcher tints them.

**Console art**: `systems/<system>.png|.jpg|.webp`, named after the ArchR
system id (`snes`, `gba`, `gb`, `gbc`, `nes`, `n64`, `psx`, `psp`, `nds`,
`genesis`, `mastersystem`, `gamegear`, `pcengine`, `neogeo`, `mame`, `dreamcast`,
`saturn`, `ports`, ...). Missing ones come from the default theme. Transparent
PNG works best; `art_scaling = "pixel"` for pixel art.

**App art** (API 4 modules): `systems/app-<id>.png|.jpg|.webp`, where `<id>` is
the module id, is the carousel picture of that module's app (same lookup as
console art: user folder, theme, default); without it the launcher uses the
module's own `art`, then its large icon. App collection screens are always
a vertical list with the focused item's picture, whatever the view (a grid or
shelves never take it away): the theme's `[app]` table (same keys as a view's
`games`: `header`, `divider`, `list`, `panel`, `art`, `meta`, `backdrop`,
`decor`; no `strip`; grid/tile/horizontal lists fall back to rows) over the
classic games layout. `header = "large"` (only in `[app]`) draws the screen's
name large under the clock with the position at the right. App pictures are
made at the `[app]` art's size. `[aspect.<shape>.app]` works. Detail screens
use the `details_*` rectangles (module picture in `details_shot`, buttons in
`details_actions`); chips, tags, the search keyboard and the confirm question
use the theme colors. Text is never drawn under 10 px.

**Sounds**: put `sounds/<event>.ogg` (Ogg Vorbis) or `.wav`, mono or stereo,
at most 1 MiB each. No declaration needed. Events: `boot`, `move`, `page`,
`select`, `back`, `launch`, `menu_open`, `menu_close`, `toggle`, `error`,
`notice`, `favorite`. Per system: `sounds/systems/<system>.ogg`, played after
the cursor rests ~350 ms on that system. A missing event plays the default
theme's sound. To rename or silence:

```toml
[sounds]
move = "sounds/tick.wav"
select = ""            # silent even if sounds/select.ogg exists

[sounds.systems]
snes = "sounds/jingle.ogg"
nes = ""
```

## 12. Test on a PC

The launcher repository has a capture test that renders the real UI offscreen
with your theme and saves PNGs (systems, games with and without cover, game
details, dialog, Start menu, Appearance, mid-animation frames). It needs Rust
and the SDL2, SDL2_ttf and SDL2_image development libraries.

```sh
git clone https://github.com/archr-linux/archr-launcher
cd archr-launcher
mkdir -p /tmp/captures
ARCHR_SETTINGS_CAPTURE_DIR=/tmp/captures \
ARCHR_SETTINGS_CAPTURE_LANGUAGES=en,pt_BR,es,ru \
ARCHR_CAPTURE_VIEWS=/abs/path/to/mytheme:lista,/abs/path/to/mytheme:vitrine,/abs/path/to/mytheme:lista:noart \
cargo test -p archr-ui --lib capture_views -- --ignored
```

Every screen size, one folder each (file names do not carry the size):

```sh
for size in 640x480 720x720 480x320; do
  mkdir -p /tmp/captures/$size
  ARCHR_CAPTURE_SIZE=$size \
  ARCHR_SETTINGS_CAPTURE_DIR=/tmp/captures/$size \
  ARCHR_SETTINGS_CAPTURE_LANGUAGES=en,pt_BR,es,ru \
  ARCHR_CAPTURE_VIEWS=/abs/path/to/mytheme:lista,/abs/path/to/mytheme:vitrine \
  cargo test -p archr-ui --lib capture_views -- --ignored
done
```

Layout fit at every size: the `resolutions` integration test loads every
folder with a `theme.toml` in the clone's `themes/` and checks each view at
640×480, 720×720, 480×320, 1024×768, 1024×600 and 1280×720 (list under the header, everything on screen,
panel/art/info/meta/dots clear of the list, details, saves, switcher and
resume rectangles not overlapping). Copy the theme in, run it, take it out:

```sh
cp -r /abs/path/to/mytheme themes/mytheme
cargo test -p archr-ui --test resolutions
rm -r themes/mytheme
```

- `ARCHR_CAPTURE_VIEWS` is a comma list of `folder:view[:noart]`. The folder is
  relative to the repository's `themes/` or absolute. `:noart` renders as if
  no console pictures existed.
- `ARCHR_SETTINGS_CAPTURE_LANGUAGES` defaults to `pt_BR,ru`.
- `ARCHR_CAPTURE_SIZE` (`<width>x<height>`) defaults to `640x480`; any size
  works (`854x480` for 16:9). The other manual captures in `archr-ui`
  (settings, achievements, resume, status bar) read it too.
- Run it from the root of the launcher clone. With a warm build cache it
  takes about 20 s; the first build takes minutes. `CARGO_TARGET_DIR` may
  point anywhere.
- It writes about 20 PNGs per view and language, named
  `<folder-name>-<view>-<screen>-<lang>.png`. Look at these first:
  `-systems-`, `-games-`, `-games-nocover-`, `-details-`, `-hub-tile0-`
  (Start menu) and `-appearance-` (Settings colors). The `-mid-` files are
  frames in the middle of animations.
- A view defined only in your theme can be captured by its id.
- The test does not print theme warnings: it passes even when your keys are
  ignored. The captures are the check; `scripts/precheck.py` catches unknown
  keys and misplaced tables.
- A capture of the systems or games screen makes a good `preview.png`.

### Screens restyled by 3.1 keys

The capture test above covers systems, games, details, dialog, Start and
Appearance. The shelves and the screen tables (menu, achievements, saves,
captures, switcher, resume, search, keyboard, toast) are drawn by
`home_render`, and the sidebar Settings by the lib test; the launcher runs
them for its test theme and for Ellegance. To see your theme there, copy it
over `themes/ellegance/` in a scratch checkout (keep `[view.lista]` or set
the view the test opens) and run:

```sh
mkdir -p /tmp/ell
ARCHR_ELLEGANCE_CAPTURE_DIR=/tmp/ell cargo test -p archr-ui --test home_render ellegance
ARCHR_ELLEGANCE_CAPTURE_DIR=/tmp/ell cargo test -p archr-ui --lib ellegance_draws_settings
```

They write every screen at 640x480, 720x720 and 480x320 (the golden
comparison then fails, expected for another theme). The launcher's clock is
pinned (`Ui::pin_clock`, UTC) and each frame waits for its pictures, so every
Ellegance frame is golden, dates and toast timers included;
`ARCHR_GOLDEN_UPDATE=1` rewrites them. `ARCHR_SETTINGS_EVERY=1` makes the
Settings test draw every page, to look them all over. `cargo test -p archr-ui
--test shipped_themes` fails on any log warning a theme in `themes/` raises.

## 13. Test on the device

Copy the folder to `/storage/.config/archr-launcher/themes/<name>/` (scp over
SSH, or the SD card's STORAGE partition), then Settings › Appearance › Theme,
and Appearance › View for each view you define. Leaving the Appearance page
applies it; no restart. Check: readability on the device's real screen
(640×480, 720×720 or 480×320; the captures of the other sizes stand in for
the screens the user does not have), every view,
the details screen, Start menu, Settings colors, sounds and speed of
animated decorations.

## 14. Publish to the Theme store

The store (Settings › Appearance › Theme store) searches GitHub for
`topic:archr-launcher-theme archived:false`, 30 results, by stars or by update.
Repositories that do not follow these rules do not appear or do not install.

1. Public, not archived GitHub repository with the topic
   `archr-launcher-theme` (`gh repo edit --add-topic archr-launcher-theme`).
2. The repository root is the theme folder: `theme.toml` at the root. One
   repository = one theme.
3. `theme.toml` must parse and must have `name`.
4. `preview.png` at the root: 640×480 PNG, at most 2 MB. The grid crops its
   middle into a wide strip, so keep the center representative.
5. Optional `screenshots/1.png`, `2.png`, `3.png`: 640×480, at most 2 MB each.
6. Owner, repository and tag names: letters, digits, `.`, `_`, `-`.

Optional store metadata, top level in `theme.toml`:

```toml
description = { en = "Neon pink over deep purple.", pt_BR = "...", es = "...", ru = "..." }  # <= 200 chars
author = "you"            # <= 40 chars; default: repository owner
version = "1.2.0"         # <= 24 chars; default: release tag
license = "CC BY 4.0"     # <= 40 chars; LICENSE file is installed too
min_launcher = "0.1.0"    # older launchers refuse to install
```

`min_launcher` is compared with the launcher **package** version
(`CARGO_PKG_VERSION`, today `0.1.0`), not with the system version Settings
shows (`v3.1.0 · …`) nor with the theme API number (3.1). Anything above
`0.1.0` makes today's store refuse the theme ("This theme needs a newer
launcher version."). Write `0.1.0` or leave the key out.

Which version installs: the latest GitHub release (by tag) if there is one,
otherwise the default branch as it is. A new release turns the installed
theme's button into "Update". Theme releases need no assets: the store
downloads the tag's source tarball from codeload.github.com.

```sh
git tag v1.0.0 && git push origin v1.0.0
gh release create v1.0.0 --title "v1.0.0" --notes "First release" --latest
```

What the store installs (everything else is silently dropped):

- files with extensions `toml png jpg jpeg webp svg ttf otf ogg wav txt md`
  (so no `.gif`, `.mp3`, `.woff`, `.aseprite`, ...), plus `LICENSE`,
  `LICENCE`, `COPYING`;
- never dotfiles or dot-folders (`.github/`), symlinks, hard links or special
  files. A path with `..` or an absolute path refuses the whole theme.

Limits: download 25 MB, installed content 60 MB, 5000 entries, 8 folder levels;
sounds 1 MiB each; `theme.toml` 64 KiB.

The store installs into `themes/<owner>-<repo>/` with a `.archr-store.toml`
marker; it never overwrites a folder it did not create. Installing does not
activate: the user presses "Use now".

The store reads the card's name and `preview.png` from the **default branch**,
but details and installation come from the **latest release**. Keep them in
sync: push to the default branch, then release.

## 15. Pitfalls

- Top-level keys written after a `[view...]`, `[frames...]` or `[sounds]`
  header end up inside that table and are ignored. Put all top-level keys
  first, tables last. Inline tables (`cover = { ... }`) are fine anywhere
  above the first header.
- Moving `list` alone: the default `panel`, `art` and `meta` stay where they
  were and cover it. Move every element of that side (section 8 table).
- `art` is not clipped to `panel`: keep the art rectangle inside the panel
  rectangle or the picture spills over its edge.
- Pixels instead of fractions (`x = 120`) are clamped to 1 in views and
  rejected in the fixed-screen rectangles.
- A fixed-screen rectangle with `x + w > 1` reverts entirely to the default.
- Naming only `font` replaces the whole family; semibold becomes the regular.
- Font path typo: you get DejaVu/Liberation, not the default theme font.
- `mark = "tile"` only works on the systems screen.
- `decor` in a view replaces, not appends to, the inherited list.
- Files the store drops (`.gif`, `.mp3`, `.woff`) work when copied by hand but
  vanish after a store install. Test the store-installed copy too.
- The store folder is `<owner>-<repo>`, not your local folder name; never
  depend on the folder name.
- Unknown keys never fail loudly. Verify every change in a capture.
- A top-level key written after `[aspect.square]` lands inside it and only
  applies on square screens. Aspect tables go last, like every table.
- A layout tuned only at 640×480: on 720×720 rectangles stretch (portrait
  covers float in a tall box) and on 480×320 the 10 px text floor makes
  small text bigger. Capture all three sizes; fix a shape in its
  `[aspect.<shape>]` table.
- Designing only for the theme's own art: users can turn the art off, widen it
  to 55 %, change its corners, or put the game picture behind the switcher
  (see section 3, "User options laid over every theme"). A list to the right
  of the art, or a `panel` that differs from `art`, does not adapt. Capture
  `:noart` and test the options on the device.
- Setting `cover` or `list_width` at the top level drops the default
  theme's square layout for them; add your own `[aspect.square]`.
- Font files, `name` and sounds inside `[aspect.*]` have no effect.
- Shape bounds are strict: a ratio of exactly 1.2 (6:5) or exactly 1.45
  is `classic`.
- Shelves are fractions of the screen: on 720x720 cards stretch and a third
  shelf can fall under the hints. Ellegance shrinks the hero and the items
  in `[aspect.square.view.lista.home.*]`; do the same.
- A games grid draws one more row clipped at the list's bottom as a scroll
  hint; size `list.h` so whole rows end at it (row + label + gap per row).
- `home = true` and `[view.<id>.home.*]` in the same file is a TOML error:
  the whole theme falls back to the default.
- A screen table key you misspell is only a log warning; the precheck now
  reports them.
- Free screen (`el`) draws nothing it is not told to: forgetting `hints` or
  `status` leaves the screen without button hints or clock.
- Free screen sizes (`size`, `row`, `radius`) are fractions of the **screen
  height**, not of the 480 reference; rectangles are screen fractions as
  usual. Pixels (`size = 18`) are clamped to the maximum.
- An `el` inside `[aspect.square]` replaces the screen's whole list on square
  screens; use `when = { aspect = "square" }` on the elements that differ.
- A free screen with images only and no `list` element still navigates, but
  the user cannot see where the cursor is. Give every free screen a `list`.
