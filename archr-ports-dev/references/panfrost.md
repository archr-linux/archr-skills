# Ports that need panfrost, and detecting the driver

## The setting

- Key `gpu.driver` in `/storage/.config/system/configs/system.cfg`, values
  `libmali` (default) or `panfrost`. UI: Settings › System › GPU driver,
  reboot required.
- `/usr/bin/gpudriver`: no argument prints the configured driver (and writes
  `libmali` if the key is empty); `--options` prints `panfrost libmali`;
  `panfrost|libmali` selects the driver for the next boot; `--start` is the
  boot hook. Log: `/storage/.config/gpudriver.log`.
- At boot a failed bind falls back to the other driver and saves it; a crash
  during the previous attempt (sentinel `/storage/.config/gpudriver.attempting`)
  forces libmali.

## Detecting the running driver (use this in ports)

```bash
if [ -d /sys/module/panfrost ]; then GPU=panfrost
elif [ -e /dev/mali0 ]; then GPU=libmali
else GPU=none; fi
```

Also: `/sys/bus/platform/drivers/panfrost/ff400000.gpu` exists when panfrost
is bound (gpudriver checks `/sys/bus/platform/drivers/panfrost/[a-f0-9]*.gpu`).
`libgl_ArchR.txt` uses `[ -d /sys/module/panfrost ]`.

Do not use `gpudriver`'s output for this: it is the configured value, which
differs from the running one after a selection that waits for a reboot. Never
call `gpudriver panfrost|libmali` from a port.

## Declaring that a port needs panfrost

Implemented in archr-launcher (`crates/archr-launcher/src/panfrost.rs`,
`Library::needs_panfrost` in `library.rs`, dialog in
`archr-ui/src/render/reports.rs`).

When the user presses A on a game of the `ports` system, and the configured
`gpu.driver` is `libmali` (missing = `libmali`), the launcher calls
`panfrost::needed(script, LIST)`:

1. Reads the first 4096 bytes of the script. In the first 10 lines it looks
   for a line starting with `#`, then optional spaces, then `PORTMASTER:`.
   The package name is the text up to the first comma, trimmed
   (`# PORTMASTER: bugdom.zip, Bugdom.sh` -> `bugdom.zip`). No header -> not
   needed, never.
2. If the package name is in `LIST` = `/usr/share/archr/portmaster/panfrost.txt`
   -> needed. Format: one name per line; text after `#` ignored; spaces
   trimmed; compared case-insensitively.
3. Otherwise reads `<script dir>/*/port.json` (each direct subfolder of the
   ports folder). The first one whose `"name"` equals the package name
   (case-insensitive) decides: needed if `attr.reqs` is an array containing
   the string `opengl` (case-insensitive). Unparseable JSON or another
   package's file is skipped.

If needed, the launch is replaced by the dialog (English / Portuguese strings
from `locales/en.toml` and `locales/pt_BR.toml`):

- title `{name} needs the panfrost driver` / `{name} precisa do driver panfrost`
  (`{name}` is the game title in the list);
- body `This game uses OpenGL, which the current GPU driver (libmali) does not have.`;
- note `The switch applies to the whole system and the console restarts. To go back: Settings › System › GPU driver.`;
- A = `Switch and restart` (`Trocar e reiniciar`): sets the GPU setting to
  `panfrost` through the same path as the settings page (`gpudriver`), then
  reboots; on failure a banner says the setting failed. B cancels; the port
  is not launched.

The check is not made when the port starts any other way (PortMaster app,
shell, SSH, `runemu.sh` directly).

### How a developer registers a port

Preferred: in the port's `port.json` (PortMaster format, installed at
`/storage/roms/ports/<folder>/port.json`):

```json
{ "version": 4, "name": "mygame.zip",
  "items": ["My Game.sh", "mygame/"],
  "attr": { "title": "My Game", "reqs": ["opengl"] } }
```

`name` must equal the package name in the script header. Any port that needs
desktop GL or Vulkan-only rendering uses this; the dialog text still says
"OpenGL".

For catalogue ports whose `port.json` does not say it but that fail on
libmali: ArchR's list, source
`distribution/projects/ArchR/packages/apps/portmaster/share/panfrost.txt`,
installed by `apps/portmaster/package.mk`. Changes go through an issue or PR
on archr-linux/Arch-R; the installed copy is replaced by updates. Current
entries: `bzflag.zip` (segfault in libmali's GLES1 `glDrawArrays`),
`a7xpg.zip` (gl4es on libmali aborts or draws without the tunnel).

A port that needs **libmali** (OpenCL, or a libmali-only bug) has no
equivalent mechanism; it must check `/dev/mali0` and tell the user.
