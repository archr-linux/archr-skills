# Launch environment, paths and packaging

## How a port starts

`/usr/share/archr/systems.cfg`, system `ports`: path `/storage/roms/ports`,
extensions `.sh .appimage`, command `/usr/bin/runemu.sh %ROM% -P%SYSTEM% ...`,
emulator/core `portmaster`.

`runemu.sh`, case `ports`:

1. `portmaster_ready`: if `/storage/roms/ports/PortMaster/control.txt`,
   `mod_ArchR.txt` or `libgl_ArchR.txt` differ from `/usr/config/PortMaster/`
   (or `mapper.txt` is missing), runs `/usr/bin/portmaster_prepare`.
2. Drops bind mounts of deleted ports (`port_binds dead | port_unbind`) and
   remembers the current ones to drop new ones after the game.
3. `chmod +x` on the script; `port_exec_bits`: finds the port folder (the
   subfolder whose `port.json` `items` lists the script, else the `GAMEDIR=`
   line of the script) and sets `u+x,go+x` on ELF and `#!` files with no
   extension or `.sh .aarch64 .arm64 .armhf .bin .elf .x86 .x86_64`, depth 4,
   plus depth 1 of `PortMaster/`.
4. `port_runtime_ready`: runtimes from `port.json` `attr.runtime` or
   `runtime="..."` lines; a missing one is fetched when online, otherwise the
   port is not started and a toast names it.
5. Runs `${EMUPERF} /usr/bin/bash "<script>"` (`.appimage`: run directly).
   `EMUPERF` pins to `SLOW_CORES` or `FAST_CORES`. Output:
   `/var/log/exec.log`.

Everything runs as root. `HOME=/storage`.

## PortMaster variables (sourced `control.txt` on an R36S)

```
directory=roms                       (run/archr/roms2 for a port on the 2nd card)
controlfolder=/roms/ports/PortMaster
ESUDO=                               ESUDOKILL=-1
CFW_NAME=ArchR                       CFW_VERSION=20261105 (build date)
CFW_GLIBC=240
DEVICE_NAME=R36S  DEVICE_CPU=RK3326  DEVICE_ARCH=aarch64  DEVICE_RAM=1
DEVICE_HAS_ARMHF=Y DEVICE_HAS_AARCH64=Y DEVICE_HAS_X86=N DEVICE_HAS_X86_64=N
DISPLAY_WIDTH=640 DISPLAY_HEIGHT=480 ASPECT_X=4 ASPECT_Y=3
ANALOG_STICKS=2  LOWRES=Y  param_device=ogs
clibs=/usr/lib/compat/  raloc=/usr/bin
raconf=--config /storage/.config/retroarch/retroarch.cfg
SDLDBUSERFILE=/storage/.config/SDL-GameControllerDB/gamecontrollerdb.txt
GPTOKEYB=" /roms/ports/PortMaster/gptokeyb -1"
GPTOKEYB2=" env LD_PRELOAD=/roms/ports/PortMaster/libinterpose.aarch64.so /roms/ports/PortMaster/gptokeyb2 -1"
```

`control.txt` (ArchR's, `/usr/config/PortMaster/control.txt`) sources
`/etc/profile`, `device_info.txt` and `funcs.txt`, sets `param_device` from
`QUIRK_DEVICE` (R36S -> `oga`, then `ogs` because the joypad path is
`odroidgo3-joypad`). `get_controls`: writes `/tmp/gamecontrollerdb.txt` via
`mapper.txt`, exports `SDL_GAMECONTROLLERCONFIG_FILE` to it, sets
`sdl_controllerconfig`, exports `LD_LIBRARY_PATH=/usr/lib/compat/`.
`CFW_NAME` comes from `NAME="ArchR"` in `/etc/os-release`.

`mod_ArchR.txt`: `PORT_32BIT` default `N`; if `Y` exports
`SPA_PLUGIN_DIR=/usr/lib32/spa-0.2` and
`PIPEWIRE_MODULE_DIR=/usr/lib32/pipewire-0.3/`; exports
`LIBGL_DRIVERS_PATH=/usr/lib32/dri:/usr/lib/dri`; sets
`GODOT2_OPTS="-r ${DISPLAY_WIDTH}x${DISPLAY_HEIGHT} -f"`,
`GODOT_OPTS="--resolution ${DISPLAY_WIDTH}x${DISPLAY_HEIGHT} -f"`; preloads
`/usr/lib/libluajit-5.1.so.2` for Solarus runtimes; makes westonwrap think
it is on ROCKNIX (nested Weston under sway); defines `pm_platform_helper`.

## System environment (`/etc/profile`, every process)

`HW_DEVICE=RK3326`, `QUIRK_DEVICE=Game Console R36S` (device tree model),
`UI_SERVICE="sway.service archr-launcher-session.service"`,
`WAYLAND_DISPLAY=wayland-1`, `XDG_RUNTIME_DIR=/var/run/0-runtime-dir`,
`SDL_VIDEODRIVER=wayland`, `SDL_AUDIODRIVER=pulseaudio`, `DISPLAY=:0.0`,
`WLR_DRM_DEVICES=/dev/dri/card0`, `MESA_NO_ERROR=1`,
`MESA_SHADER_CACHE_DIR=/var/cache/mesa`, `MESA_SHADER_CACHE_MAX_SIZE=128MB`,
`MALI_WAYLAND_AFBC=0`, `MALI_SCHED_RT_THREAD_PRIORITY=95`,
`DEVICE_*` (for example `DEVICE_HAS_DUAL_SCREEN=false`), and on panfrost
`PAN_I_WANT_A_BROKEN_VULKAN_DRIVER=1`. `ARCHR_*` path variables from
`/etc/profile.d/010-archr-fhs`.

## Standard script header

```bash
#!/bin/bash
# PORTMASTER: mygame.zip, My Game.sh
XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}
if [ -d "/opt/system/Tools/PortMaster/" ]; then controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then controlfolder="$XDG_DATA_HOME/PortMaster"
else controlfolder="/roms/ports/PortMaster"; fi
source $controlfolder/control.txt
[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"
get_controls
GAMEDIR="/$directory/ports/mygame"
cd "$GAMEDIR"
export SDL_GAMECONTROLLERCONFIG="$sdl_controllerconfig"
$GPTOKEYB "mygame.aarch64" -c "./mygame.gptk" &     # only if the game needs keyboard/mouse
pm_platform_helper "$GAMEDIR/mygame.aarch64"
./mygame.aarch64
pm_finish
```

(Pattern taken from an installed catalogue port, `100 Lil Jumps.sh`, on the
console.)

## Paths

| Path | What |
|---|---|
| `/storage/roms/ports/` (`/roms` -> `/storage/roms`) | scripts and port folders, `gamelist.xml` |
| `/storage/roms/ports/PortMaster/` | PortMaster, `control.txt`, `mod_ArchR.txt`, `libgl_ArchR.txt`, `gptokeyb*`, `libinterpose.*.so`, runtimes in `libs/` (squashfs) |
| `/storage/.config/PortMaster/` | refreshed copies (`control.txt`, `mapper.txt`, `mod_ArchR.txt`, `gamecontrollerdb.txt` link) |
| `/usr/config/PortMaster/` | the system's originals |
| `/run/archr/roms2` | ROM folder of the second card, when present |
| `/storage` | `$HOME`; games write dot folders here |
| `/var/log/exec.log` | last launch output |

`/storage` is ext4 (`/dev/mmcblk1p3`), root is ext4, `/flash` is vfat ro.

## Audio

PipeWire + `pipewire-pulse` + WirePlumber. Pulse socket
`/var/run/0-runtime-dir/pulse/native`. ALSA card 0 `rk817int`. 32-bit
`libpulse.so.0`, `libasound.so.2`, `libpipewire-0.3.so.0` installed. Use SDL
(pulseaudio backend) or libpulse.

## Input

Built-in pad: `r36s_Gamepad`,
`/dev/input/by-path/platform-odroidgo3-joypad-event-joystick` (event3) and
`...-joystick` (js0). Also `gpio-keys-vol`, `rk805 pwrkey`. `/dev/uinput`
mode 666 for gptokeyb. Use SDL GameController with the generated mapping.

## Packaging checklist (PortMaster format)

- Script with the `# PORTMASTER:` header in the first 10 lines.
- Folder with `port.json` (`version`, `name` = package name, `items`,
  `attr.title`, `attr.reqs`, `attr.arch`, `attr.runtime`).
- Own libraries in `libs.aarch64` / `libs.armhf`; gl4es in `gl4es.aarch64` /
  `gl4es.armhf`.
- Never ship GPU libraries (EGL, GLES, GBM, GL, wayland-egl, vulkan, ICDs).
- Saves inside `GAMEDIR` (PortMaster `bind_directories`).
