---
name: archr-launcher-dev
description: Build, test and publish themes and modules for archr-launcher, the Rust + SDL2 front end of ArchR (640x480 reference design, also on 720x720 square and 480x320 screens), the Arch Linux distro for RK3326 handhelds such as the R36S. Use this skill whenever someone wants to create or change an ArchR theme (theme.toml, colors, fonts, views/layouts, 9-slice frames, decorations, sounds, console art, [aspect.square|classic|wide] layouts for other screen sizes), write an archr-launcher module (module.toml, JSON-RPC over stdin/stdout, Start menu tiles, widgets, Y-menu items, settings pages, permissions, launch.before, apps with screens and rom.install, art systems/app-<id>.png), debug why a theme key or module is ignored, or publish to the in-launcher Theme store or Module store (GitHub topics archr-launcher-theme / archr-launcher-module, releases, assets). Trigger even when the user just says "ArchR theme", "tema do ArchR", "R36S launcher skin", "module for the launcher" or "módulo do archr-launcher".
---

# archr-launcher themes and modules

archr-launcher draws every screen of an ArchR handheld from a 640×480
reference design, scaled to fit the real screen: 640×480 (R36S and most
RK3326 handhelds), 720×720 (R36 Plus) and 480×320 (Odroid Go Advance, RGB10,
RG351M); a 16:9 screen (1280×720 on the RK3562 handhelds) takes the 3:2 layout. A theme can change its layout per screen
shape with `[aspect.square]`, `[aspect.classic]` and `[aspect.wide]` tables.
Third parties extend it in two ways, and neither runs code inside
the launcher:

- A **theme** is a folder of data: `theme.toml` plus optional fonts, images,
  icons and sounds. It recolors everything and, with theme API 3.1, changes
  the layout of every screen: systems, games, details, the Start menu and
  shelves, one table per screen (menu, achievements, saves, screenshots,
  switcher, resume, search, keyboard, toast, dialogs, OSD) and Settings
  (`[settings]`: sidebar or list, tiles, inset groups, title, icon colours).
  Since update 20261125.15 the systems and games screens of a view can also
  be **free screens**: a list of `el` elements (image, text, rect, frame,
  panel, list, hints, status; since 20261125.16 also `rating` stars and a
  `fields` card; since 20261125.17 `carousel` (row, column or wheel) and
  `grid` drawn from an `item` template, one of list/carousel/grid per
  screen; since 20261125.18 one muted `video`) each in its own rectangle,
  with system/game data and
  pictures (`system.logo`, `system.image`, `game.cover`/`screenshot`/`logo`),
  `[vars]`, `when` and `base` (`references/themes.md`, section 8,
  "Free screens"). Since 20261125.19 a theme can also offer its own
  `[options]` (rows in Settings › Appearance whose choices swap `[vars]`),
  split itself into files with `include` and make a view inherit another
  (`base`, `remove`). Since 20261125.20 any element can animate with
  `enter` (screen comes in) and `select` (focus changes), 0.6 s at most.
  Nothing in a theme is executed.
- A **module** is an external program (sh, bash + `jq`, or an aarch64 binary)
  that the launcher starts in a systemd sandbox and talks to with JSON-RPC 2.0,
  one JSON object per line on stdin/stdout. The module *declares* in
  `module.toml` what it adds (Start tiles, a Start widget, a Y-menu item,
  settings pages, event hooks, since API 3 a per-game CPU ceiling and detail
  pages, and since API 4 an app with its own screens that can install games)
  and the launcher draws it. A module never draws pixels, never reads the
  gamepad and never runs as root.

The launcher validates both leniently: unknown keys and bad values are logged
and ignored, never fatal (except a few module fields). That means a mistake
usually shows up as "my setting has no effect", not as an error. Stick to the
keys in the references and check the result visually.

## Pick the right reference

Read only what the task needs:

| Task | Read |
|---|---|
| Any theme work | `references/themes.md` |
| Any module work | `references/modules.md` |
| Before publishing either | `references/checklist.md` |

Starting points that pass validation: `assets/theme-template/` and
`assets/module-template/`. Copy one, rename, then edit.
For a theme that uses the 3.1 keys (shelves, glass, focus lift, spring
motion, one table per screen, sidebar Settings, capsule OSD), the reference
is `themes/ellegance/` in the launcher repository (`references/themes.md`).
For a free screen (`el`), the reference is the test theme
`crates/archr-ui/tests/themes/cena/theme.toml` (views Solo and Albedo, and
Carrossel and Roda for the collections).

Users can also change appearance on top of any theme (font weight, battery
percentage, box art on/off/width/corners, switcher background, text and
background colours, text-only button hints, per-system background). A theme can
ship `backgrounds/<system>.png|jpg` for the last one (`references/themes.md`
section 7). Those are
`system.cfg` options, not theme keys: design the games screen so it still works
with the art off or wider, and test with them (`references/themes.md` section
3, checklist).

`scripts/precheck.py <folder>` (Python 3.11+) is a static check. For themes it
reports unknown keys (free screen `el` fields included), top-level keys trapped inside a table, pixel values,
off-screen fixed rectangles, misnamed or misused `[aspect.*]` tables,
missing files, file types the store drops, sound sizes, missing languages in names, and the preview size. For modules it
reports the fatal manifest errors, missing locale keys, unquoted dotted locale
keys, extension-point limits, and icons that differ from Lucide (it downloads
them to compare; `--offline` skips that). It does not render anything or run
the module: the launcher's own checks below still decide.

## Workflow

Every theme or module goes through the same four stages. Do not skip the
device stage: the PC cannot reproduce the sandbox, how the real screen
reads, the gamepad or the R36S speed.

1. **Create** from the template. Keep the folder name equal to the module
   `id` (modules) or a short lowercase name (themes). Write user-facing text
   in the four languages the launcher ships: `en` (required, the fallback),
   `pt_BR`, `es` and `ru`.
2. **Test on the PC.**
   - Theme: render it with the launcher's capture test at 640x480, 720x720
     and 480x320 (`ARCHR_CAPTURE_SIZE`; exact commands in
     `references/themes.md`, "Test on a PC"), look at the PNGs of every size,
     and run the `resolutions` test with the theme copied into the
     launcher's `themes/`.
   - Module: run `archr-launcher --check-module <folder>` (exit 0 = valid),
     then pipe JSON lines into the entry script by hand and read its stdout.
3. **Test on the device.** Enable SSH on the handheld (Settings › Network ›
   Network services › SSH; `ssh root@archr.local`), copy the folder to
   `/storage/.config/archr-launcher/themes/<name>/` or
   `/storage/.config/archr-launcher/modules/<id>/`, then pick the theme in
   Settings › Appearance or enable the module in Settings › System › Modules.
   Logs: `journalctl -u 'archr-mod-<id>*'` for modules; the launcher's log for
   theme warnings.
4. **Publish** to the store: a public GitHub repository whose root is the
   theme or module folder, with the topic `archr-launcher-theme` or
   `archr-launcher-module`, and a GitHub release. The rules differ between the
   two stores and are strict; follow the "Publish" section of the matching
   reference and then `references/checklist.md`.

## Things to tell the user plainly

- The "Reviewed by ArchR" badge (Revisado) in the Module store is given only by
  the ArchR maintainer, by adding the exact package digest to a signed list.
  Nobody can earn it by following rules, and publishing a new package removes
  it until the maintainer reviews again. Ask for it with an issue at
  `archr-linux/archr-modules` carrying the release link. Themes have no badge.
- A module release needs three assets: `<id>-<version>.tar.gz`, the loose
  `module.toml` and `preview.png`. Without the loose `module.toml` the store
  says "The release does not carry the module package." Check with
  `gh release view v<version> --json assets -q '.assets[].name'`, fix with
  `gh release upload`, then press **Refresh (Y)** in the store, which reads
  every listed release again.
- `min_launcher` is the launcher package version (`0.1.0` today), not the
  system version (v3.1.0) nor the theme API (3.1). A higher value makes the
  store refuse the theme or module; `precheck.py` flags it.
- A passing `--check-module` or a nice capture does not prove the thing works
  on the handheld. Say so when you hand over the result, and list what still
  needs a device test.
- Module isolation is enforced by systemd, not by the module's good manners:
  only its own folder, its data folder and what its permissions grant are
  visible. Seccomp filters are not active on the current ArchR image. Never
  promise more isolation than `references/modules.md` describes.

## Working rules

- Use only keys, values, limits and method names that appear in the
  references. If the user asks for something the launcher does not offer
  (a new widget type, a permission that does not exist, and on free screens
  video with sound or Details as a scene), say it is not available yet instead of inventing a
  key; the launcher would silently ignore it or refuse the module.
- Free screen (`el`) sizes (`size`, `row`, `radius`) are fractions of the
  real screen height, unlike the 480 reference below, and the screen draws
  only its elements: add `hints` and `status` yourself. Prefer `@phrase`
  texts (`@description`) over fixed labels so the four languages work.
- Theme numbers are fractions, never pixels, of two kinds. **Sizes**
  (`font_size`, row/header/footer heights, radii, `margin`, list `row`,
  `font`) are fractions of a 480 px reference height and keep their
  reference size on every screen. **Rectangles** (`x y w h`) are fractions
  of the screen and stretch with it. At 640×480 convert with px/640 and
  px/480; a square 720×720 screen is 640×640 reference px, 480×320 is
  720×480.
- A layout that looks right at 640×480 can break on a square or 3:2 screen.
  Check every theme at the three sizes (1280×720 too for 16:9), and fix a shape with its
  `[aspect.<shape>]` table rather than the top-level values, which apply
  to every screen.
- No text is ever drawn under 10 screen px, whatever `font_min` or
  `font_scale` say; on 480×320 that is 15 reference px, so small text there
  takes more room than at 640×480.
- In TOML, every top-level key must come before the first `[table]` header,
  or it lands inside that table and is ignored. This is the most common
  theme bug.
- Modules API 4 (apps) is the current API. `system = ["cpu-tune"]`, `system = ["perf-limits"]`, `system = ["boot-tuning"]`, the page keys and row types of the detail page (`hint`, `layout = "detail"`, `open`, `alt_action`, `stats`, `header`, `bars`, `facts`) and the side panel, live value rows and page rows (`aside`, `choices = []`, value-row `action`/`alt_action`, `type = "page"`) need `api_version = 3`; `[app]` and `permissions.install` need `api_version = 4`. Lower versions ignore or refuse them. Newer API 4 features (`screen.qr`, `rom.install` with `replace`) exist only when `initialize` lists them in `capabilities`.
