# OpenGL, OpenGL ES, EGL and the window system

## What each driver offers

| | libmali | panfrost (Mesa 26.2.7) |
|---|---|---|
| GLES | 1.1 (`OpenGL ES-CM 1.1` string in the blob), 2.0, 3.x (blob string `OpenGL ES 3.2`; not measured with wflinfo, the test console ran panfrost) | `OpenGL ES 3.1 Mesa 26.2.7` (wflinfo, gles2 and gles3) |
| Desktop GL | none | `3.1 Mesa 26.2.7`, compatibility and core (wflinfo) |
| Renderer string | not measured | `Mali-G31 MC1 (Panfrost)` |
| EGL platforms | Wayland and GBM (blob `wayland-gbm`; exports `wl_egl_window_create`, `gbm_create_device`) | Wayland, GBM, surfaceless |

## Recommendation

GLES 2.0 or 3.0 over EGL, Wayland window, via SDL2 with
`SDL_GL_CONTEXT_PROFILE_MASK = SDL_GL_CONTEXT_PROFILE_ES`. Works on both
drivers. On libmali the GLES-only SDL2 is active and a desktop GL context
request fails.

## gl4es

PortMaster ports source `$controlfolder/libgl_${CFW_NAME}.txt` when it
exists, else `libgl_default.txt` (PortMaster convention; ArchR's file says it
is used "in place of PortMaster's libgl_default.txt"). ArchR ships
`/roms/ports/PortMaster/libgl_ArchR.txt` (copied from
`/usr/config/PortMaster/libgl_ArchR.txt` by `portmaster_prepare`, and checked
by `runemu.sh` before every port):

```bash
export LIBGL_ES=2
export LIBGL_GL=21
if [ -d /sys/module/panfrost ]; then
  export LIBGL_FB=3   # panfrost: GBM backend draws nothing under sway; PBuffer works
else
  export LIBGL_FB=4   # GBM
fi
[ ! -e "/dev/dri/card0" ] && export LIBGL_FB=2
# prepends $PWD/gl4es.$DEVICE_ARCH (or $PWD/gl4es) and $PWD/libs.$DEVICE_ARCH (or $PWD/libs) to LD_LIBRARY_PATH
```

Source it after `cd "$GAMEDIR"` (it uses `$PWD`).

`mod_ArchR.txt` exports `LIBGL_DRIVERS_PATH=/usr/lib32/dri:/usr/lib/dri`.

## Environment that affects GL

From `/etc/profile.d/041-panfrost` (all processes, both drivers):

```
MESA_NO_ERROR=1
MESA_SHADER_CACHE_DIR=/var/cache/mesa      (-> /storage/.cache/mesa_shader_cache)
MESA_SHADER_CACHE_MAX_SIZE=128MB
```

From `/etc/profile.d/mali-priority.sh`: `MALI_SCHED_RT_THREAD_PRIORITY=95`.
Exported by `999-export`: `MALI_WAYLAND_AFBC` (value `0` on the R36S),
`PAN_MESA_DEBUG` when set.

`runemu.sh` exports `PAN_MESA_DEBUG=forcepack` only when the setting
`forcepack` is `On` for the system or game.

## Window system

- sway owns the display: `WAYLAND_DISPLAY=wayland-1`,
  `XDG_RUNTIME_DIR=/var/run/0-runtime-dir`, `SWAYSOCK` set,
  `SDL_VIDEODRIVER=wayland` (`/etc/profile.d/050-sway.conf`).
  `DISPLAY=:0.0` is also in the environment; whether Xwayland runs for X11
  programs was not checked.
- KMS/DRM direct output does not work while sway runs. SDL2's kmsdrm request
  falls back to Wayland (see `libraries.md`).
- Fullscreen: `pm_platform_helper "<binary path>"` (defined in
  `mod_ArchR.txt`) closes a pending PortMaster dialog and runs
  `/usr/bin/portmaster_sway_fullscreen.sh <basename>`, which calls
  `sway_fullscreen` (`/etc/profile.d/001-functions`) on that `app_id`
  (5 attempts).
- DRM nodes on panfrost: `/dev/dri/card0`, `/dev/dri/card1`,
  `/dev/dri/renderD128` (mode 666). libmali node: `/dev/mali0`.
- Screen on the R36S: 640x480 (`DISPLAY_WIDTH`, `DISPLAY_HEIGHT` from
  PortMaster's `device_info.txt`).
