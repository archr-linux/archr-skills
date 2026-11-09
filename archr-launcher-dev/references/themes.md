# Themes reference

Source of truth: `docs/temas.md`, `crates/archr-ui/src/theme.rs`,
`crates/archr-ui/src/layout.rs`, `crates/archr-ui/src/settings/store.rs`
and `crates/archr-ui/tests/resolutions.rs`
in github.com/archr-linux/archr-launcher. Published examples:
github.com/archr-linux/archr-theme-praia and archr-theme-retro.

## Contents

1. Folder layout and inheritance
2. Name and languages
3. Colors
4. Fonts and text
5. Global geometry
6. Style
7. Theme images: background, 9-slice frames, text outline, decorations
8. Views (systems and games screens)
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

Legacy aliases: `highlight_bg` = `accent`, `highlight_text` = `accent_text`,
`dim_text` = `dim`. Write the new names.

The user can override the accent and background in Appearance. The first accent
swatch is the theme's own `accent`; picking another color makes the text on it
black or white by contrast. Keep `accent_text` readable on `accent`.

## 4. Fonts and text

```toml
font = "fonts/Inter-Regular.ttf"
font_semibold = "fonts/Inter-SemiBold.ttf"
font_mono = "fonts/JetBrainsMono-Regular.ttf"
font_mono_medium = "fonts/JetBrainsMono-Medium.ttf"

font_scale = 1.0       # 0.5..2, multiplies every text size
font_grid = 0          # 0..32 px; sizes snap to multiples (8 for Press Start 2P); 0 = free
font_smoothing = true  # false = hard-edged glyphs, for pixel fonts
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

Fixed layouts a theme cannot move: Settings (only colors, fonts and icons
apply there; 640 reference px wide, centered on wider screens, more rows on
taller ones) and the ROM migration screen (always the default theme).

## 10. Screen sizes and `[aspect.*]` tables

The 640×480 design is scaled by `min(width/640, height/480)` so it fits
whole; the spare room goes to the longer side.

| screen | devices | scale | reference px | shape |
|---|---|---|---|---|
| 640×480 | R36S, most RK3326 handhelds | 1 | 640×480 | `classic` |
| 720×720 | R36 Plus | 1.125 | 640×640 | `square` |
| 480×320 | Odroid Go Advance, RGB10, RG351M (portrait panel turned by Sway) | 0.667 | 720×480 | `wide` |
| 854×480 | 16:9 | 1 | 854×480 | `wide` |
| 1280×720 | 16:9 | 1.5 | 853×480 | `wide` |

Shape from width/height: `square` below 1.2 (6:5), `classic` 1.2 to 1.45
(29:20) inclusive, `wide` above 1.45. Code: `Aspect::of` in
`crates/archr-ui/src/theme.rs`.

Consequences with no `[aspect]` table at all: sizes keep their reference px,
so a square screen shows more list rows of the same height (Grafite: 10
game rows at 640×480, at least 13 at 720×720); rectangles stretch, so a
portrait cover gets taller and narrower; the built-in `lista` geometry
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
640×480, 720×720 and 480×320 (list under the header, everything on screen,
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
- Setting `cover` or `list_width` at the top level drops the default
  theme's square layout for them; add your own `[aspect.square]`.
- Font files, `name` and sounds inside `[aspect.*]` have no effect.
- Shape bounds are strict: a ratio of exactly 1.2 (6:5) or exactly 1.45
  is `classic`.
