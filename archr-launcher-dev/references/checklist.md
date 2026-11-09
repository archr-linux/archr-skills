# Pre-publish checklist

Go through the list that applies. Report each item as done, failed or "needs
the device" to the user; do not tick device items on their behalf.

## Theme

Content
- [ ] `theme.toml` at the repository root, under 64 KiB, valid TOML.
- [ ] All top-level keys come before the first `[table]` header.
- [ ] `name` with `en`, plus `pt_BR`, `es`, `ru` (also for each new view's `name`
      and for `description`).
- [ ] Positions are fractions (0..1); every `cover`, `details_*`,
      `achievements_*`, `saves_*`, `shots_grid`, `switcher_*`, `resume_*`,
      `start_widgets`, `start_area` rectangle has `x + w <= 1` and
      `y + h <= 1`, also inside `[aspect.*]` tables.
- [ ] `[aspect.*]` tables are named only `square`, `classic` or `wide`, come
      after all top-level keys, and hold no font files, `name` or sounds.
- [ ] If the theme sets `cover` or `list_width` at the top level, or moves
      the games screen, it has its own `[aspect.square]` for them (the
      default theme's square layout no longer applies).
- [ ] Every file named in `theme.toml` exists, inside the folder, with the
      exact case.
- [ ] Only store-kept file types: `toml png jpg jpeg webp svg ttf otf ogg wav
      txt md` and `LICENSE`. Sounds at most 1 MiB each.
- [ ] Fonts cover Latin accents and Cyrillic; their license allows
      redistribution (put it in the repo).
- [ ] `accent_text` is readable on `accent`, `text_secondary` on
      `background`/frames.

PC test
- [ ] Capture test run for every view the theme defines, plus `:noart`, in
      `en,pt_BR,es,ru`, at `ARCHR_CAPTURE_SIZE` 640x480, 720x720 and 480x320
      (one output folder per size); every PNG looked at (systems, games,
      games-nocover, details, dialog, Start menu, Appearance).
- [ ] User Appearance options checked over the theme: box art off (the list
      takes the whole width, no orphan `panel`), art at 55 % wide, corners 0
      and 20, Bold weight, battery percentage off, switcher background at 40 %
      and 80 % (readable over light and dark covers), text-only button hints,
      custom text and background colours (legible, `text_secondary` derived
      sensibly), and a system background (`backgrounds/<system>.png`, at screen
      size for fast loading, text readable under the curtain).
- [ ] `cargo test -p archr-ui --test resolutions` passes with the theme
      copied into the launcher's `themes/` (removed again afterwards).
- [ ] No "Unknown theme key" / "Invalid theme field" warnings for your keys.

Device test (only the user can do these)
- [ ] Copied to `/storage/.config/archr-launcher/themes/<name>/`, selected in
      Appearance, every view checked on the real screen (and on a square or
      3:2 handheld too, if the user has one).
- [ ] Same Appearance options tried on the device (art off/wider, Bold,
      switcher background).
- [ ] Sounds, decorations and animations feel right at R36S speed.

Store
- [ ] `preview.png` 640×480 PNG ≤ 2 MB, center representative;
      optional `screenshots/1..3.png` 640×480 ≤ 2 MB.
- [ ] Public repo, topic `archr-launcher-theme`, root = theme folder.
- [ ] Optional metadata: `description` (≤ 200), `author`, `version`, `license`,
      `min_launcher`.
- [ ] Default branch pushed, then a release `v<version>` created (theme
      releases need no assets).
- [ ] Installed once from the store on the device and checked again.

## Module

Content
- [ ] Folder / repository root named exactly as `id` (`[a-z0-9-]{3,40}`).
- [ ] `version` x.y.z, `api_version` 1 to 4 (2 if using `config_write`,
      `hooks`, `system`, `launch`; 4 for `[app]` and `install`).
- [ ] `[run]` runtime `sh`|`bash`|`native`, entry exists, mode fits the job
      (daemon for focus events, live values, `launch.before`).
- [ ] Minimal permissions; none reserved (`write`) or unknown.
- [ ] `locales/en.toml` plus `pt_BR`, `es`, `ru`, flat, dotted keys quoted,
      same key set in all four; `name`/`description` as language tables.
- [ ] Icons downloaded from `lucide-static@0.468.0`, untouched, only those used.
- [ ] Settings rows ≤ 48, pages ≤ 8; tiles ≤ 2, shortcut ≤ 1, widget ≤ 1,
      Y item ≤ 1.
- [ ] Only protocol JSON on stdout; logs on stderr; unknown requests answered
      with `-32601`; EOF exits.

PC test
- [ ] `archr-launcher --check-module <folder>` exits 0 with no warnings.
- [ ] Every request and event the module handles piped by hand; every stdout
      line passes `jq -e .`; oneshot finishes well under 2 s.
- [ ] Behaviour with an empty or missing settings file (defaults used).

Device test (only the user can do these)
- [ ] Copied to `/storage/.config/archr-launcher/modules/<id>/`, permission
      granted, enabled; every tile, widget, Y item, page and action used.
- [ ] Still works after playing a game; `journalctl -u 'archr-mod-<id>*'`
      clean.

Store
- [ ] Public repo, topic `archr-launcher-module`, root = module folder,
      `preview.png` 640×480 committed.
- [ ] Tag `v<version>` matching the manifest, pushed.
- [ ] Release assets: `<id>-<version>.tar.gz` (from `git archive
      --prefix=<id>/`, written outside the folder), `module.toml` (same bytes
      as in the tag), `preview.png`; ≤ 8 MB packed, ≤ 16 MB unpacked,
      ≤ 500 entries.
- [ ] Installed once from the store on the device.
- [ ] Told the user: the "Reviewed by ArchR" badge is up to the maintainer
      (issue at archr-linux/archr-modules with the release link), and any new
      package needs a new review.

App (API 4, only if the module has `[app]`)
- [ ] `api_version = 4`, `mode = "daemon"`, `[app].home` set; `install` lists
      only emulated systems (never `tools`, `windows`, `setup`, `shell`,
      `moonlight`, `music`, `idtech`, `scummvm`, `j2me`) and `"ports"` only if
      it installs ports.
- [ ] First screen is placeholder-friendly: a `screen.show` goes out right
      after `initialize`/`screen.opened` (empty or cached), network results
      arrive later with `patch`; nothing blocks the first 30 s.
- [ ] Long lists: `more` plus `screen.more` for paging; covers fetched only
      for the window in `screen.visible`, not all at once.
- [ ] Pictures are PNG/JPEG/WebP under 4 MiB, relative paths inside `HOME`,
      no symlinks; `art` <= 1 MiB.
- [ ] No install without a user action: `rom.install`/`port.install` only
      inside the handling of an `action.invoke` (5 s window), on its own
      "Install" button, after the download.
- [ ] Removal sends `rom.remove`/`port.remove` and relies on the launcher's
      own question; no custom confirm in front of it.
- [ ] Quota (2 GiB, games and ports) and every error code handled with a
      readable `screen.toast`; failures leave the screen usable.
- [ ] Shutdown handled in 500 ms; no state kept only in memory.
- [ ] Looked at with the three screen sizes and with a theme other than the
      default; the carousel art `systems/app-<id>.png` is optional.
- [ ] Tested on the device: opens at once, installs, plays, removes.
