# Modules reference (API 1 to 4)

Source of truth: `docs/modulos.md`,
`crates/archr-launcher/src/modules/manifest.rs` (the validator) and
`modules/store.rs` in github.com/archr-linux/archr-launcher. Published
examples: github.com/archr-linux/archr-module-bateria-detalhada (daemon) and
archr-module-perfil-cpu (oneshot).

API 4 (apps, section 15) is the newest API the launcher runs; modules of
lower `api_version` still run. Sections 1 to 13 describe API 1 and 2. Use
API 3 (CPU tuning and detail pages, section 14) only with
`api_version = 3` or higher, and API 4 only as section 15 lists it, with
`api_version = 4`.

## Contents

1. Package layout
2. module.toml
3. Extension points
4. Settings pages
5. Permissions
6. Runtime, sandbox and lifecycle
7. Protocol (JSON-RPC)
8. Texts and locales
9. Writing the entry script
10. Test on a PC
11. Test on the device
12. Publish to the Module store
13. Pitfalls
14. CPU tuning and detail pages (API 3)
15. Apps (API 4)

## 1. Package layout

```
<id>/                  folder name must equal id
  module.toml          required, at most 64 KiB
  main.sh | bin/<x>    the entry
  locales/en.toml      required; pt_BR.toml, es.toml, ru.toml recommended
  icons/<name>.svg     Lucide 0.468.0 SVGs, byte-for-byte unmodified, only the ones used
  preview.png          640x480, shown in the store (release asset)
  LICENSE
  README.md
```

Languages available on the image: **sh/bash + `jq`** and **aarch64 binaries**.
Python is not guaranteed; `runtime = "python3"` is refused.

## 2. module.toml

```toml
id = "battery-plus"            # [a-z0-9-]{3,40}, unique on the device
version = "1.0.0"              # x.y.z, digits only
api_version = 2                # 1 to 4
min_launcher = "0.1.0"         # optional, x.y.z
name = { en = "Battery plus", pt_BR = "Bateria+", es = "Batería+", ru = "Батарея+" }
description = { en = "...", pt_BR = "...", es = "...", ru = "..." }
author = "Name <mail@example.org>"
license = "MIT"
homepage = "https://github.com/you/archr-module-battery-plus"
icon = "battery-full"          # Lucide name; icons/battery-full.svg must exist

[run]
runtime = "bash"               # "sh" | "bash" | "native"
entry = "main.sh"              # relative path inside the module, no leading / or ., no ..
mode = "daemon"                # "daemon" | "oneshot"

[limits]
memory_mb = 16                 # default 32, clamped to 8..64

[permissions]                  # absent = denied
# net = true
# read = ["roms"]

[[hooks]]
event = "focus.game"
```

`name`/`description`: a string, an `"@key"` from `locales/`, or a table by
language (a table needs no copy in `locales/`). Prefer the table: the store shows it before installing; with
`@key` the store shows the repository name until the module is installed.

Every text field: at most 120 characters, no control characters.

**Fatal errors** (module does not run, `--check-module` exits non-zero):
invalid `id`, `version`, `api_version` or `[run]`; unknown permission, a
disallowed value in a permission list, or the reserved `write` permission;
API 2 permissions with `api_version = 1`; more than 48 settings rows in total;
folder name different from `id`; entry file missing; `locales/en.toml` missing
or not TOML; an icon (`icon`, or `icon` of a tile/shortcut/widget) missing or
not an unmodified Lucide 0.468.0 SVG. Everything else that is wrong is a
warning and that field or entry is dropped.

Getting a Lucide icon byte-for-byte (do not reformat or edit it):

```sh
curl -fsSL https://unpkg.com/lucide-static@0.468.0/icons/<name>.svg -o icons/<name>.svg
```

Offline, copy the file from an unmodified `lucide-static@0.468.0` package; a
hand-written SVG never passes.

## 3. Extension points

Entry ids (`id` of tiles, shortcuts, widgets) and setting keys:
`[A-Za-z0-9_.-]{1,40}`.

**Start tile** `[[start.tiles]]`: up to 2 per module, 4 in total.

```toml
[[start.tiles]]
id = "battery"
label = "@tile"
icon = "battery-full"        # optional; default: the module icon
open = "main"                # opens settings page "main"
# action = "refresh"         # or sends action.invoke instead
```

Needs `open` (an existing page id) or `action`, else it is dropped. Shows a
live value under its title after `ui.update` to `tile:<id>`.

**Start shortcut** `[[start.shortcuts]]`: same fields, 1 per module, 2 total,
between Wi-Fi and Suspend. `ui.update` target `shortcut:<id>`.

**Start widget** `[[start.widgets]]`: same fields, 1 per module, 2 total. A 2×1
block with icon and module name, a big value, a detail text and a bar:
`ui.update` to `widget:<id>` with `value`, `detail`, `progress` (0–100).
Position comes from the theme (`start_widgets`).

**Y-menu item** `[[quick]]`: 1 per module, 3 total, above Suspend.

```toml
[[quick]]
id = "suggest"
label = "@quick.suggest"
context = "game"             # "game" | "system"
systems = ["n64", "psp"]     # optional; empty = all
action = "suggest"           # required
```

The action gets `context = {system, game_key, rom}` (game) or `{system}`.

## 4. Settings pages

Up to 8 pages, 48 rows in total, under Settings › System › Modules › <module>.
Layout is the fixed Settings layout.

```toml
[[settings.pages]]
id = "main"
title = "@title"

[[settings.pages.rows]]
type = "toggle"
key = "watts"
label = "@row.watts"
subtitle = "@row.watts_sub"    # optional
section = "@section.options"   # optional header above the row
default = true
```

Every row takes `label`, and optionally `subtitle` and `section`; the table
lists the fields specific to each type.

| `type` | behavior | fields |
|---|---|---|
| `toggle` | switch | `key`, `default` (bool) |
| `check` | checkbox, A toggles | `key`, `default` (bool) |
| `value` | ‹ › between choices | `key`, `choices` (texts), `labels` (same length), `default` (one of choices; else the first) |
| `slider` | ‹ › numeric | `key`, `min`, `max`, `step` (integers, at most 200 steps), `default` |
| `action` | A sends `action.invoke`, shows "…" until the reply | `action`, `confirm` (optional question) |
| `text` | read-only; value from `ui.update` to `row:<id>` | `id`, `value` (initial) |
| `keyboard` | opens the on-screen keyboard | `key`, `max` (1..64), `secret` (bool) |
| `progress` | title, right text and bar from `ui.update` to `row:<id>` (`value`, `progress`) | `id` |
| `list` | rows sent by the module: `ui.update` to `row:<id>` with `items: [{id, title, subtitle?, value?, action?}]` (up to 20); A on an item with `id` and `action` sends `action.invoke` with `context: {item: "<id>"}` | `id` |

The launcher owns the values and writes them atomically to
`/storage/.config/archr-launcher/module-settings/<id>.json` (path in
`ARCHR_MODULE_SETTINGS`). The module only reads that file. Toggles and checks
are booleans, sliders numbers, everything else strings. A key not yet changed
by the user may be absent, and the file itself may be empty: read with a
default in jq (`.key // "x"`) and again in the shell, because jq prints nothing
for an empty file.
`secret = true` keyboard values go to `<id>.secret.json`
(`ARCHR_MODULE_SECRETS`, mode 0600) instead, and arrive in `initialize` and
`settings.changed`, never on the command line or in logs.

## 5. Permissions

Ask for the minimum; the user sees them before installing ("Allow and
install"), amber ones first. A hand-copied module starts disabled, "Waiting for
your permission". An update that asks for more shows only the new ones.

| permission | grants | API |
|---|---|---|
| (none) | own folder, `/sys` and `/proc` read-only | 1 |
| `net = true` | network (otherwise a private loopback only) | 1 |
| `read = ["roms", "bios", "screenshots"]` | `/storage/roms`, `/storage/roms/bios`, `/storage/roms/screenshots`, read-only | 1 |
| `config_read = [...]` | `config.get` of the listed keys | 1 |
| `config_write = [...]` | `config.set` of the listed keys, values checked | 2 |
| `hooks = ["launch"]` | receives `launch.before` before each game (daemon) | 2 |
| `system = ["cpu-profile"]` | may choose the CPU governor of one launch in `launch.before` | 2 |
| `system = ["cpu-tune"]` | may choose the CPU ceiling of one launch in `launch.before`; gets `perf` in `game.ended` (section 14) | 3 |
| `system = ["brightness"]` / `["volume"]` / `["wifi"]` / `["screenshot"]` | `system.call` of that action | 2 |
| `launch = true` | `game.launch` right after the user picks one of the module's actions | 2 |

`config_read` keys: `system.language`, `system.timezone`,
`system.cpugovernor`, `system.hostname`, `global.netplay.nickname`,
`global.retroachievements`, `audio.volume`, `display.brightness`. Passwords,
tokens and Wi-Fi keys are never readable.

`config_write` keys and accepted values: `system.cpugovernor` =
`performance|ondemand|schedutil|powersave`; `global.netplay.nickname` =
`[A-Za-z0-9 _.]`, 1–32 chars.

Even with `read = ["roms"]`, `/storage/roms/backup` and `/storage/roms/backups`
stay inaccessible. `write` is reserved: asking for it blocks the module.

## 6. Runtime, sandbox and lifecycle

Each process runs via `systemd-run --pipe` in its own unit. What is enforced
on the current image:

- Own user: a uid/gid per module id (60600–61099), no root, no capabilities,
  `NoNewPrivileges`. Other modules' processes, files and signals are invisible
  (`ProtectProc=invisible`, `PrivateUsers=yes`).
- Filesystem: `ProtectSystem=strict`, `ProtectHome`, `PrivateTmp`,
  `PrivateDevices`, kernel tunables/modules/logs, cgroups, clock and hostname
  protected. All of `/storage` is hidden except the module folder (read-only),
  `module-data/<id>` (writable, the `HOME`, 0700), the settings and secrets
  files (read-only) and what `read` grants. D-Bus and userdb sockets are
  inaccessible.
- Network only with `net`. Even then, no `localhost` (except the
  systemd-resolved DNS stub 127.0.0.53/54) and no address of the device itself.
- Resources: `MemoryMax` = `memory_mb`, no swap, `TasksMax=16`,
  `CPUWeight=20`, `IOWeight=20`, `Nice=10`.
- Seccomp is **not** active: the ArchR systemd is built without it, so
  `SystemCallFilter`, `RestrictAddressFamilies` and friends are not applied.
  Do not claim syscall filtering.

| mode | life | use for |
|---|---|---|
| `oneshot` | one process per message: one line in, then exit | user actions, rare events |
| `daemon` | one process while the launcher is on screen | live values, focus events, `launch.before` |

- Starting a process costs ~190 ms on the R36S; focus events go to daemons only.
- Daemons start one at a time ~2 s after the first frame. At most 3 daemons
  are enabled; the fourth is refused.
- **No module runs during a game.** Before a game the launcher sends
  `game.started`, then `shutdown`, waits 500 ms and kills what is left. On
  return, daemons are started again and get `game.ended`.
- EOF on stdin means exit.
- Timeouts: `initialize` 3 s; `action.invoke` 1 s (daemon); a whole oneshot 2 s.
- Failures (timeout, invalid JSON, non-zero exit, dying before replying, not
  reading stdin): 3 in 10 minutes disable the module ("stopped responding").
  A crashed daemon restarts after 1 s, 5 s, 30 s. A store update that fails
  rolls back to the previous version.

Environment: `HOME` and `ARCHR_MODULE_DATA` (writable), `ARCHR_MODULE_DIR`
(code, read-only), `ARCHR_MODULE_SETTINGS`, `ARCHR_MODULE_SECRETS` (only with
secret rows), `ARCHR_MODULE_ID`, `ARCHR_API_VERSION`,
`ARCHR_LAUNCHER_VERSION`, `ARCHR_LANG`, `ARCHR_DEVICE`. `PATH` is the
system's; do not assume tools beyond the base system, `sh`, `bash` and `jq`.

## 7. Protocol (JSON-RPC 2.0)

One JSON object per line (UTF-8, `\n`, at most 64 KiB) on stdin/stdout. Every
message has `"jsonrpc":"2.0"`. **stdout is the protocol only**: any stray
`echo` breaks it. Log to stderr (first lines go to the launcher log, the rest
to the journal) or with the `log` notification.

### Launcher → module requests (have `id`, need exactly one reply)

| method | params | result |
|---|---|---|
| `initialize` (daemon only) | `{api_version, launcher_version, language, device, settings, permissions, capabilities}` | `{"ready": true}` |
| `action.invoke` | `{action, context: {system?, game_key?, rom?, item?}}` | `{}` |
| `shutdown` (daemon only) | `{}` | `{}`, then exit |
| `launch.before` (daemon with `hooks = ["launch"]`) | `{game: {system, game_key, name}}` | `{"decision":"allow"}` or `{"decision":"modify","changes":{"governor":"<g>"}}` |

`launch.before`: all modules together get 300 ms; a late answer counts as
`allow` (the game never waits), 3 late answers in a row count as a failure.
There is no deny. `changes.governor` needs `system = ["cpu-profile"]` and one
of the four governors; it applies to that launch only. If two modules choose,
the first by `id` order wins. Netplay and Moonlight do not ask.

Reply to unknown requests with error `-32601` (not counted as a failure).

### Launcher → module events (no `id`, never reply)

`{"jsonrpc":"2.0","method":"event","params":{"name":"focus.game","data":{...}}}`,
only for events listed in `[[hooks]]` (except `settings.changed`):

| event | data | delivered to |
|---|---|---|
| `launcher.started` | `{cold}` (false when returning from a game) | daemon and oneshot |
| `game.started` | `{game:{system, game_key, name}}` | daemon and oneshot (stopped right after) |
| `game.ended` | `{game:{system, game_key, name}, exit_code, seconds}` | daemon and oneshot |
| `focus.system` | `{system}`, after 400 ms still | daemon only |
| `focus.game` | `{system, game_key, name}`, after 400 ms still | daemon only |
| `settings.changed` | `{key, value}` | daemon, always, no subscription |

### Module → launcher

| method | kind | params |
|---|---|---|
| `ui.update` | notification | `{target: "tile:<id>"\|"shortcut:<id>"\|"widget:<id>"\|"row:<id>"\|"quick:<id>", value?: text or {key,args}, detail?: text, progress?: 0–100, items?: [...], hidden?: bool}` |
| `ui.notify` | notification | `{text: text or {key,args}}` or `{key, args}`; a banner, at most 1 per 10 s |
| `log` | notification | `{level: "info"\|"error", message}` |
| `settings.set` | request | `{key, value}`, declared keys only → `{}` |
| `config.get` | request | `{key}`, with `config_read` → `{value}` (`null` if unset) |
| `config.set` | request | `{key, value}`, with `config_write` and an accepted value → `{}`; 1/s and 10/h |
| `game.launch` | request | `{system, game_key}`, with `launch` → `{}` |
| `system.call` | request | `{name, value?}`, with that `system` action → `{}`, `-32000` if it failed |

`system.call` actions: `brightness` (integer 10–100, 1/s), `volume` (0–100,
1/s), `wifi` (`true`/`false`, 1/min, banner shown), `screenshot` (no value,
1/10 s, refused with `-32001` while a keyboard is open).

`game.launch` works only within 5 s after the user picked one of the module's
actions (tile, shortcut, Y item, action row), once per pick, emulated games
only. The `{}` reply only acknowledges.

`ui.update` reaches the screen at most 4 times a second (merged).
`hidden: true` hides a tile, shortcut or Y item until `hidden: false`.

**Oneshot specifics**: the launcher writes one message and closes stdin. The
module may emit notifications (`ui.update`, `ui.notify`, `log`) and, if the
message had an `id`, exactly one reply, then exit. No `initialize`, no
`shutdown`; settings come from `ARCHR_MODULE_SETTINGS`. Module requests
(`config.get`, `config.set`, `settings.set`, `game.launch`, `system.call`)
work in daemons only.

Error codes: `-32700` invalid JSON, `-32600` invalid request, `-32601` unknown
method, `-32602` invalid params, `-32001` permission denied, `-32002` timeout,
`-32003` rate limit, `-32004` not found, `-32000` launcher failure.

## 8. Texts and locales

`"@key"` in the manifest or in `ui.update`/`ui.notify` resolves in
`locales/<ARCHR_LANG>.toml`, then `locales/en.toml`. Placeholders:
`{"key":"@st.watts","args":{"pct":87,"w":"1.9"}}` fills `{pct}` and `{w}`.

Locale files are **flat**: one level of string keys. Quote keys that contain
dots, otherwise TOML builds nested tables and those keys are silently lost:

```toml
"name" = "Battery plus"
"row.watts" = "Show power"        # right
# row.watts = "Show power"        # wrong: becomes [row] watts, ignored
```

Ship `en.toml` (required), `pt_BR.toml`, `es.toml`, `ru.toml` with the same keys.

## 9. Writing the entry script

Daemon skeleton (bash + jq):

```bash
#!/bin/bash
send()  { printf '%s\n' "$1"; }
reply() { send "{\"jsonrpc\":\"2.0\",\"id\":$1,\"result\":$2}"; }
handle() {
    eval "$(printf '%s' "$1" | jq -r '@sh "id=\(.id // "null") method=\(.method // "") name=\(.params.name // "")"')"
    case "$method" in
        initialize) reply "$id" '{"ready":true}'; update ;;
        event) [ "$name" = settings.changed ] && update ;;
        action.invoke) update; reply "$id" '{}' ;;
        shutdown) reply "$id" '{}'; exit 0 ;;
        *) [ "$id" = null ] || send "{\"jsonrpc\":\"2.0\",\"id\":$id,\"error\":{\"code\":-32601,\"message\":\"unknown\"}}" ;;
    esac
}
update() { jq -cn --arg v "$(date +%H:%M)" '{jsonrpc:"2.0",method:"ui.update",params:{target:"tile:clock",value:$v}}'; }
while true; do
    if IFS= read -r -t 15 line; then handle "$line"
    elif [ $? -gt 128 ]; then update   # timeout: periodic refresh
    else exit 0; fi                    # EOF: launcher is gone
done
```

Oneshot skeleton (sh + jq): one message in, notifications out, exactly one
reply if the message had an `id`, exit.

```sh
#!/bin/sh
IFS= read -r msg || exit 0
eval "$(printf '%s' "$msg" | jq -r '@sh "id=\(.id // "null") method=\(.method // "") action=\(.params.action // "")"')"
# Settings: the file may be missing, empty or /dev/null, so default in shell too.
short=$(jq -r 'if .short == true then "true" else "false" end' "$ARCHR_MODULE_SETTINGS" 2>/dev/null)
[ -n "$short" ] || short=false
value=$(date +%H:%M)
jq -cn --arg v "$value" '{jsonrpc:"2.0",method:"ui.update",params:{target:"tile:clock",value:$v}}'
case "$method" in
    action.invoke) printf '{"jsonrpc":"2.0","id":%s,"result":{}}\n' "$id" ;;
    event) ;;                                   # events never get a reply
    *) [ "$id" = null ] || printf '{"jsonrpc":"2.0","id":%s,"error":{"code":-32601,"message":"unknown method"}}\n' "$id" ;;
esac
```

A oneshot fills its tile and text rows when something wakes it: subscribe to
`launcher.started` (delivered to oneshots, also after each game) for the first
value, and refresh on its own `action.invoke`. Until then a text row shows its
manifest `value`. Opening a page (`open = "main"`) does not send anything.
`assets/module-template/` is a complete working oneshot.

Build JSON with `jq -cn --arg ...`, never by pasting raw strings into JSON
(quotes and non-ASCII names break it). The launcher's request ids are
integers; echo them back unchanged.

A `native` module is an aarch64 Linux binary (static linking is safest); the
store sets the entry to 0755 and everything else to 0644.

## 10. Test on a PC

1. Validate with the launcher itself:

   ```sh
   git clone https://github.com/archr-linux/archr-launcher && cd archr-launcher
   cargo build --release -p archr-launcher     # needs SDL2, SDL2_ttf, SDL2_image, SDL2_mixer dev libs
   ./target/release/archr-launcher --check-module /path/to/<id>
   ```

   Exit 0 and `<path>: ok` means valid; `warning:` lines name dropped fields.
   Treat warnings as bugs. The binary links SDL2_mixer even for this check,
   so the library must be installed. On the device the same command works
   with the installed `archr-launcher`.
2. Drive the entry by hand. Oneshot:

   ```sh
   echo '{"jsonrpc":"2.0","id":1,"method":"action.invoke","params":{"action":"refresh","context":{}}}' \
     | ARCHR_MODULE_SETTINGS=/dev/null sh main.sh
   ```

   Daemon: send `initialize`, then events and requests, then close stdin; the
   script must exit. Pipe every stdout line through `jq -e .` to prove it is
   valid JSON, and time it with `time` (a oneshot should finish in a few
   hundred ms on a PC; the R36S is several times slower and the limit
   there is 2 s).
3. Optional: `ARCHR_LAUNCHER_ROOT=<fake root>` runs the whole launcher on a PC
   with modules **without sandbox** (development only).

## 11. Test on the device

Copy to `/storage/.config/archr-launcher/modules/<id>/` over SSH, open
Settings › System › Modules (it shows as "Local"), grant the permissions,
enable it. Check every tile, widget, Y item, page and action; check that it
keeps working after a game (stopped during the game, restarted after). Logs:
`journalctl -u 'archr-mod-<id>*'`. A module that never starts with
`status=217/USER` is on an image older than 2026-10-28 (missing
`libnss_systemd`); update ArchR.

## 12. Publish to the Module store

The store lists every public, non-archived repository with the topic
`archr-launcher-module`. It reads the latest release, not the branch.

Release rules (the latest non-prerelease release):

- tag `v<version>`, equal to `version` in `module.toml`;
- three assets with these exact names: `<id>-<version>.tar.gz`, `module.toml`
  (identical byte for byte to the one inside the package) and `preview.png`
  (640×480);
- the tarball: at most 8 MB, at most 16 MB unpacked, at most 500 entries,
  everything inside a top folder `<id>/`; only regular files and folders (a
  link, device, absolute path or `..` refuses the whole package). Modes are
  normalized (0644; the entry 0755).

Simplest way: the repository root is the module folder, and the package comes
from the tag with `git archive`, which adds the `<id>/` prefix and leaves out
`.git` and links:

```sh
git tag v1.0.0 && git push origin main v1.0.0
git archive --format=tar.gz --prefix=<id>/ -o ../<id>-1.0.0.tar.gz v1.0.0
gh release create v1.0.0 --latest ../<id>-1.0.0.tar.gz module.toml preview.png
gh repo edit --add-topic archr-launcher-module
```

Write the tarball outside the module folder, or it ends up inside the next
package. Commit `preview.png` and `module.toml` before tagging so the loose
assets match the tag.

The store checks the SHA-256 GitHub publishes for the asset, requires the loose
`module.toml` to match the packaged one, and runs the same validation as
`--check-module`. An `id` belongs to the first repository that used it on that
device; another repository with the same `id` is refused. The previous version
is kept until the new one runs.

**The "Reviewed by ArchR" badge**: only the ArchR maintainer grants it, by
reviewing the package and adding its repository and digest to a list signed
with the project key (release of `archr-linux/archr-modules`). Reviewed modules
come first and may auto-update when the user enables it and the update asks
for nothing new. Any new package loses the badge until it is reviewed again.
To ask for a review, open an issue at github.com/archr-linux/archr-modules
with the link to your module's release.

## 13. Pitfalls

- Folder name differs from `id` → fatal.
- An icon re-saved, minified or pretty-printed → "not an unmodified Lucide
  icon". Download it with curl, never write it by hand. Icons of `[[quick]]`
  items are not used.
- Dotted locale keys without quotes → texts show as raw `@keys`.
- `open = "x"` without a page `x` → the tile is silently dropped.
- `value` row whose `default` is not in `choices` → the first choice is used.
- Slider with more than 200 steps → the row is dropped.
- `[[hooks]] event = "focus.game"` on a oneshot never fires (daemons only).
- Writing anything but protocol JSON to stdout → counted as a failure.
- A oneshot that does not exit within 2 s, or a daemon slow to answer
  `initialize` (3 s) → failure; 3 failures in 10 min disable the module.
- Writing to the settings file or the module folder → read-only; use
  `settings.set` (daemon) and `$HOME`.
- Assuming network, `curl`, Python or `/storage/roms` access without the
  permission.
- Tag `v1.0.0` with `version = "1.0.1"` in the manifest → `modules.bad_tag`.
- Repacking with `tar` from inside the folder → no `<id>/` prefix → refused.

## 14. CPU tuning and detail pages (API 3)

Source: `docs/modulos.md` section 9 and `examples/modules/ajuste-cpu` in the
launcher (not yet in the Module store).

API 3 adds only what automatic CPU tuning needs. In a manifest with
`api_version` below 3, the page keys and row types below are ignored with a
warning and `cpu-tune` is an error.

### `system = ["cpu-tune"]`

Only the CPU frequency ceiling of one launch: never the user's governor
(that is `cpu-profile`), never GPU or memory, never free writes to `/sys`.
Needs `hooks = ["launch"]` to have any effect.

- `initialize` adds `cpu: {opps, max_khz}`: the frequencies the CPU accepts
  now, in kHz, lowest first (boost ones only with boost on); `max_khz` is the
  highest. RK3326: 408000, 816000, 1008000, 1416000, and 1512000 with turbo.
- `launch.before` reply: `{"decision":"modify","changes":{"cpu_max_khz":816000}}`.
  Only a value from `cpu.opps` is accepted. The launcher passes
  `--cpu-max=<kHz>` to `runemu.sh`, which checks it against
  `scaling_available_frequencies` / `scaling_boost_frequencies` and applies it
  after the governor, for that launch only. Two modules: first by `id` wins.
- With any `cpu-tune` module on, the launcher also passes `--measure`;
  `archr-perf-probe` measures the game and `game.ended` gets `perf`, sent to
  `cpu-tune` modules only:

```json
"perf": {"cpu_max_khz": 816000, "seconds": 150, "busy_p95": 71,
         "limit_seconds": 0, "idle_seconds": 4, "current_ma": 420}
```

| field | meaning |
|---|---|
| `cpu_max_khz` | ceiling the game ran with |
| `seconds` | seconds measured (the first 30 s do not count) |
| `busy_p95` | p95 load (%) of the emulator's busiest thread, per second |
| `limit_seconds` | seconds that thread was above 92 % |
| `idle_seconds` | seconds it was below 20 % (pause, menu, waiting) |
| `current_ma` | average battery current in mA while discharging, `null` on the charger |

Only processes inside the launch's tree count. It is a CPU load heuristic,
not a speed measurement (no frame counting yet): never promise "100 % speed"
from it, and discard sessions that are mostly idle. After every game
`archr-launcher-session` restores the highest ceiling, even if `runemu.sh`
was killed.

### New page keys and row types

All drawn by the launcher; content comes from `ui.update` with `items` to
`row:<id>`. The layout is fixed. Colors by name only (`tone`): `good`,
`info`, `bad`, `muted` or none.

| key | where | effect |
|---|---|---|
| `hint` | page | footer text, left of the buttons |
| `layout = "detail"` | page | detail layout |
| `open = "<page>"` | `list` row | A on an item sends its action and opens that page for that item only |
| `alt_action`, `alt_label` | `list` row | X on an item sends `alt_action` with `context.item`; footer shows `alt_label` |
| `icon` | `action` row | Lucide icon of the button on a detail page |

| `type` | drawing | item fields |
|---|---|---|
| `stats` | up to 3 cards at the top, never selected | `title`, `value` (large, `tone` color), `subtitle` |
| `header` | detail page header: game cover, name, line, badge | `id` (of the opened item), `title`, `subtitle`, `badge`, `tone`, `game: {system, game_key}` |
| `bars` | bars, title left, value right; the row `label` is the section title | `title`, `value`, `progress` (0 to 100), `tone` |
| `facts` | name/value lines in the right column | `title`, `value`, `tone` |

`list` items gain `detail` (second line, right), `badge` (tag in place of the
value), `tone` and `open: false` (A sends the action without opening the
`open` page; use it for next/previous page items of a long list).

Detail page: left, the `header`, `bars` and `text` rows; right, the `facts`
and below them the `action` rows as buttons, the only selectable rows. Each
button sends its action with `context.item` of the opened item. The page
stays empty until the module sends a `header` whose `id` is the opened item.
The cover comes from the launcher's library through `header.game`; the
module reads no ROMs or images.

```toml
api_version = 3
[run]
runtime = "bash"
entry = "main.sh"
mode = "daemon"
[permissions]
hooks = ["launch"]
system = ["cpu-tune"]
[[settings.pages]]
id = "main"
hint = "@hint"
[[settings.pages.rows]]
type = "stats"
id = "summary"
[[settings.pages.rows]]
type = "list"
id = "games"
open = "game"
alt_action = "relearn"
alt_label = "@relearn"
[[settings.pages]]
id = "game"
layout = "detail"
[[settings.pages.rows]]
type = "header"
id = "head"
[[settings.pages.rows]]
type = "bars"
id = "bars"
[[settings.pages.rows]]
type = "facts"
id = "facts"
[[settings.pages.rows]]
type = "action"
action = "maximum"
icon = "zap"
```

`ajuste-cpu` lowers one step only with clear headroom (p95 under 75 % and
under 1 % of the time at the limit), raises one at the limit, calls a game
learned after 3 stable sessions at the same ceiling, discards short or idle
sessions and skips N64, PSP, Dreamcast and Saturn. Its list goes in pages of
18 games with `open: false` items for next/previous, at most 20 items per
update. PC test: `bash examples/modules/ajuste-cpu.test.sh`.

## 15. Apps (API 4)

Source: `docs/modulos.md` section 10 and `examples/modules/catalogo-demo` in
the launcher; real app: github.com/archr-linux/archr-module-itchio.

A module with `api_version = 4` can have **one app**: its own carousel item
that opens full screens (catalog, detail, search) and can install games and
ports into the library. The module describes; the launcher draws, with the
theme's `games` and `details_*` layouts, at 640×480, 720×720 and 480×320.

### Manifest

```toml
api_version = 4
[run]
mode = "daemon"            # required for apps
[app]
label = "@app.name"        # default: module name
subtitle = "@app.subtitle"
icon = "store"             # Lucide, intact SVG in icons/
art = "art.png"            # optional PNG/JPEG/WebP in the package, <= 1 MiB
home = "catalog"           # id of the first screen (required to run)
[permissions]
install = ["gb", "gbc", "ports"]   # system folders and/or "ports"
launch = true                      # "Play" after installing
```

- One `[app]` per module. With api_version < 4, `[app]` is ignored with a
  warning and `install` is an error. `oneshot` or no `home`: no app.
- `install` systems are checked against the system catalog at install time.
  Always refused (already at the manifest): `tools`, `windows`, `setup`,
  `shell`, `moonlight`, `music`, `idtech`, `scummvm`, `j2me`. Only emulated
  systems (run through `runemu.sh`) are accepted.
- The store shows "Has its own screens" and "Installs games in: ..." (amber)
  before install. The carousel row is `@app:<id>`; art lookup: user/theme
  `systems/app-<id>.png`, the module's `art`, the large icon.
- Summary text (carousel and panel): `ui.update` with
  `target:"app:summary"`, `value:<text or {key,args}>`.

### Lifecycle

- A on the item opens the app at once with a wait indicator and only B
  until the first `screen.show`; 30 s without one shows "not responding".
- The app process is the same sandbox with `ARCHR_MODULE_ROLE=app`,
  `MemoryMax=96M`, `TasksMax=32`, outside the 3-daemon limit, one app at a
  time. `initialize` has `role:"app"`; after `{"ready":true}` the launcher
  sends `screen.opened {screen:"<home>"}`.
- A module with only `[app]` has no resident daemon. With tiles, widgets or
  events there are two processes; both get `settings.changed`.
- It ends (`shutdown`, 500 ms, kill) on B at the first screen, when a game
  opens, on suspend/power off and when the launcher closes. Never restarted;
  an error exit counts as a failure. START opens the module's Settings pages.

### Screens (module to launcher, notifications)

| method | params |
|---|---|
| `screen.show` | `{id, title, layout:"collection"\|"detail", ...}` |
| `screen.patch` | `{screen?, append?, more?, chips?, footer?, target?, ...}` |
| `screen.toast` | `{text, tone?}` |
| `screen.confirm` | `{id, text, yes?, no?}`; reply `screen.answer` |
| `screen.busy` | `{text}`; `{text:null}` clears |
| `screen.offline` | `{text?}`; `{text:null}` clears |

- Collection: `chips` (<= 8 `{id,label,selected}`), `items` (<= 50 per
  message, 1000 per screen: `{id,title,subtitle?,badge?,tone?,image?}`),
  `more`, `buttons:{x?,y?:{label,action}}`, `footer`. `tone`: good, info, bad,
  muted.
- Detail: `image`, `gallery` (<= 8), `subtitle`, `facts` (<= 8
  `{title,value,tone?}`), `text` (<= 4000 chars), `buttons` (<= 4
  `{id,label,icon?,action,progress?}`).
- `show` with an id already on the stack replaces it in place; a new id goes
  on top (max 8). `patch target`: `"item:<id>"` or `"button:<id>"`
  (`progress:null` removes the bar). At most 4 shows/patches per second; over
  256 queued are dropped; only the last of several toasts shows.
- Ids and action names: 1 to 128 chars, no control characters.
- Texts: `@key` or `{key,args}`; any other text is plain, no markup.
- **Pictures** (`image`, `gallery`): relative paths inside the module's
  `HOME` only. Refused: `..`, absolute paths, any symlink, hard links, > 4 MiB,
  not PNG/JPEG/WebP. Only the pictures on screen are read; the launcher
  copies and decodes its own copy. An item may get its `image` later with
  `screen.patch {screen, target:"item:<id>", image}`.

### What the app hears

`screen.opened {screen}`, `screen.select {screen,item}`, `screen.chip
{screen,chip}`, `screen.more {screen,count}` (5 items from the end, once per
`append`), `screen.search {screen,text}` (SELECT keyboard, <= 64 bytes),
`screen.answer {id,yes}`, `screen.back {screen}`, `screen.visible
{screen,from,to}` (150 ms after the window stops; in a detail `from == to`
is the shown picture), `port.progress {name,progress}`. Module buttons come
as `action.invoke` with `context:{screen,item?}` (X/Y on a collection) or
`{screen,button}`.

### Installing and removing

| method | params | result |
|---|---|---|
| `rom.install` | `{system,file,name?,cover?,meta?:{developer,description,year}}` | `{game_key}` |
| `rom.list` | `{}` | `{games:[{game_key,system,size,date}],used,limit}` |
| `rom.remove` | `{game_key}` | `{removed}` |
| `port.install` | `{name}` | `{game_key}` |
| `port.list` / `port.remove` | `{}` / `{name}` | `{ports:[...]}` / `{removed}` |

Security rules the launcher enforces:

- **User action first.** Each A/X/Y on an app screen (`action.invoke`) allows
  one install in the next 5 s; otherwise `-32001`. Download first, install on
  a separate "Install" button.
- `file` is inside `HOME`, <= 64 MiB, with an extension of the system and not
  one the device executes (`.sh .bash .run .appimage .desktop .py .pl .jar`).
- `cover` that is not a valid image is dropped; the game still installs.
- Quota 2 GiB per module (games and ports together): `-32003`. One copy at a
  time, one `rom.install` per second.
- Removal only of what the module installed (`-32001`). The launcher asks the
  user itself ("Remove <name>?", Cancel focused); the module never hears it
  and a module `screen.confirm` cannot hide it. The reply is `{removed}`.
- `port.install`: `name` matches `^[a-z0-9][a-z0-9._-]*\.zip$` and is in the
  PortMaster catalog. The launcher runs `/usr/bin/archr-port-install`; it never
  accepts port files from the module. One at a time, up to 15 min,
  `port.progress` while it runs. `game.launch` works for a port the module
  installed (`system:"ports"`).
- The module never reads the ROM folder or the library; `rom.list` and
  `port.list` return only what it installed and still exists.

Error codes: `-32001` not allowed, `-32602` bad params, `-32003` quota,
`-32004` not found, `-32005` port already installed, `-32000` other (last
script error line), `-32601` unknown method (`screen.qr` does not exist yet:
carry on without it).

### Minimal app (sh + jq), from catalogo-demo

`module.toml` (plus `icons/gamepad-2.svg` from Lucide and `locales/en.toml`
with `app.name`, `app.subtitle`, `title`, `get`, `installed`):

```toml
id = "mini-catalog"
version = "1.0.0"
api_version = 4
name = { en = "Mini catalog" }
description = { en = "One test game the app installs into Game Boy." }
author = "You <you@example.com>"
license = "MIT"
icon = "gamepad-2"

[run]
runtime = "sh"
entry = "main.sh"
mode = "daemon"

[app]
label = "@app.name"
subtitle = "@app.subtitle"
icon = "gamepad-2"
home = "catalog"

[permissions]
install = ["gb"]
launch = true
```

`main.sh`:

```sh
#!/bin/sh
# One item, one detail screen, install on a button press.
send() { printf '%s\n' "$1"; }
reply() { send "{\"jsonrpc\":\"2.0\",\"id\":$1,\"result\":$2}"; }
NEXT=10; WAIT=""
show_catalog() {
    send '{"jsonrpc":"2.0","method":"screen.show","params":{"id":"catalog","title":"@title","layout":"collection","items":[{"id":"demo","title":"Demo cartridge","subtitle":"Game Boy"}]}}'
}
show_detail() {
    send '{"jsonrpc":"2.0","method":"screen.show","params":{"id":"game:demo","title":"Demo cartridge","layout":"detail","text":"A 32 KiB test cartridge.","buttons":[{"id":"get","label":"@get","icon":"download","action":"get"}]}}'
}
while IFS= read -r line; do
    eval "$(printf '%s' "$line" | jq -r '@sh "id=\(.id // "null") method=\(.method // "") action=\(.params.action // "") failed=\(.error.message // "")"')" || continue
    case $method in
        initialize) mkdir -p "$HOME/downloads"; reply "$id" '{"ready":true}' ;;
        shutdown) reply "$id" '{}'; exit 0 ;;
        screen.opened) show_catalog ;;
        screen.select) show_detail ;;
        action.invoke)
            reply "$id" '{}'
            if [ "$action" = get ]; then
                head -c 32768 /dev/zero >"$HOME/downloads/demo.gb"
                NEXT=$((NEXT + 1)); WAIT=$NEXT
                send "{\"jsonrpc\":\"2.0\",\"id\":$NEXT,\"method\":\"rom.install\",\"params\":{\"system\":\"gb\",\"file\":\"downloads/demo.gb\",\"name\":\"Demo cartridge\"}}"
            fi ;;
        "")  # a reply to our own request
            [ "$id" = "$WAIT" ] || continue
            if [ -n "$failed" ]; then
                send "$(jq -cn --arg t "$failed" '{jsonrpc:"2.0",method:"screen.toast",params:{text:$t,tone:"bad"}}')"
            else
                send '{"jsonrpc":"2.0","method":"screen.toast","params":{"text":"@installed","tone":"good"}}'
            fi ;;
        *) [ "$id" = null ] || send "{\"jsonrpc\":\"2.0\",\"id\":$id,\"error\":{\"code\":-32601,\"message\":\"$method\"}}" ;;
    esac
done
```

The install request is sent right inside the `action.invoke` of the button,
so the user-action window is open. Test on a PC with
`sh examples/modules/catalogo-demo.test.sh` for the full demo, and pipe
`initialize`, `screen.opened`, `screen.select` and `action.invoke` by hand to
your own script. Installing really needs the device.

App pitfalls: a first screen that waits on the network (show a screen at once,
fill it with `patch`); sending every cover at once (use `screen.visible`);
an install request fired after the 5 s window; relying on `screen.confirm` to
remove (the launcher asks itself).
