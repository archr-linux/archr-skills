# Libraries on ArchR 3.1.0 (RK3326)

## Architecture

- `aarch64` userland in `/usr/lib`; 32-bit `armhf` in `/usr/lib32`
  (`/etc/ld.so.conf.d/arm-lib32.conf`). glibc 2.40.
- `/lib` -> `/usr/lib`. `/lib/ld-linux-aarch64.so.1`,
  `/lib/ld-linux-armhf.so.3` -> `/usr/lib32/ld-linux-armhf.so.3`.
- Library cache: `/storage/.cache/ld.so.cache` (there is no
  `/etc/ld.so.cache`). `gpudriver --start` runs `ldconfig -X` when the bound
  driver differs from the one recorded in `/storage/.cache/ld.so.cache.driver`.

## Graphics libraries per driver

| Library | Path (64 / 32) | libmali | panfrost |
|---|---|---|---|
| EGL | `/usr/lib/libEGL.so.1`, `/usr/lib32/libEGL.so.1` | `/usr/lib*/mali/libEGL.so.1` bind-mounted | libglvnd, vendor `libEGL_mesa.so.0` (`/usr/share/glvnd/egl_vendor.d/50_mesa.json`) |
| GLESv2 | `libGLESv2.so.2` | mali (mounted) | libglvnd -> Mesa |
| GLESv1 | `libGLESv1_CM.so.1` | mali (mounted) | libglvnd -> Mesa |
| GBM | `libgbm.so.1` | mali (mounted) | Mesa |
| wayland-egl | `libwayland-egl.so.1` | mali (mounted) | wayland 1.25 |
| GL (desktop) | `libGL.so.1`, `libOpenGL.so.0`, `libGLX.so.0` (libglvnd 1.7.0) | `/dev/null` mounted over `libGL.so` | Mesa |
| DRI | `/usr/lib/dri/panfrost_dri.so`, `/usr/lib32/dri/panfrost_dri.so` | unused | used |
| Vulkan loader | `/usr/lib/libvulkan.so.1` (1.4.354); none in `/usr/lib32` | present, no device | present |
| Vulkan ICD | `/usr/share/vulkan/icd.d/panfrost_icd.armv8-a+crc+fp+simd.json` -> `/usr/lib/libvulkan_panfrost.so` | `/dev/null` mounted over it | active |
| libmali | `/usr/lib/libmali.so.1` -> `libmali.so.1.9.0`, same in `/usr/lib32`; also `libmali-bifrost-g31-g24p0-wayland-gbm.so` | used | present but unusable (no `/dev/mali0`) |
| OpenCL | `/usr/lib/mali/libMaliOpenCL.so.1`, `/usr/lib32/mali/libMaliOpenCL.so.1`; ICD `/etc/OpenCL/vendors/mali.icd` | see `opencl.md` | none |

The files in `/usr/lib/mali` and `/usr/lib32/mali` are small forwarders
(`NEEDED libmali-hook.so.1`, which needs `libmali.so.1`), owned by the
`libmali` package (64-bit) and `lib32` (32-bit).

### How the mounts are made (gpudriver, `/usr/bin/gpudriver`)

libmali (`load_driver libmali`):

```sh
find /usr/{lib,lib32}/mali -type f -exec bash -c 'lib={}; mount --bind $lib ${lib/\/mali\//\/}' ';'
find /usr/{lib,lib32}/glesonly -type f -exec bash -c 'lib={}; mount --bind $lib ${lib/\/glesonly\//\/}' ';'
mount --bind /dev/null /usr/lib/libGL.so
mount --bind /dev/null /usr/lib32/libGL.so
# and /dev/null over /usr/share/vulkan/icd.d/panfrost_icd.*.json
```

A mount over a link lands on the file it points to, so `/usr/lib/libEGL.so`
(-> `libEGL.so.1` -> `libEGL.so.1.1.0`) ends up serving the mali file.
`libMaliOpenCL.so.1` has no counterpart in `/usr/lib`, so that mount fails
and OpenCL stays only in `/usr/lib/mali`.

panfrost: no mounts (it removes any left), and masks
`/usr/share/vulkan/icd.d/mali.json` if it exists (it does not on RK3326).

pacman hooks run `archr-gpu-bind unbind|bind` and `archr-sdl-bind
unbind|bind` around transactions that touch these packages, so updates do
not fail with "Device or resource busy".

## SDL2

- Version 2.32.10. Regular build `/usr/lib/libSDL2-2.0.so.0.3200.10`
  (desktop GL + GLES + Wayland + KMSDRM + Vulkan), 32-bit
  `/usr/lib32/libSDL2-2.0.so.0.3200.10` (no Vulkan).
- GLES-only build (`-DSDL_OPENGL=OFF`): `/usr/lib/glesonly/` and
  `/usr/lib32/glesonly/`, package `SDL2_glesonly`. Mounted over the regular
  file on libmali, because PortMaster ports cannot pick a subfolder. It has
  no Vulkan support either.
- Patch `0010-forced-kmsdrm-falls-back.patch`: `SDL_VIDEODRIVER=kmsdrm` (or
  the hint) falls back to the normal order when `WAYLAND_DISPLAY` is set or
  KMSDRM fails. `ARCHR_SDL_KMSDRM=1` keeps it forced.
- SDL_image, SDL_mixer, SDL_ttf, SDL_net, SDL_gfx 2.x exist for both
  architectures (`/usr/lib32/libSDL2_*`).

## Debian multiarch paths

Created by the `archr` package (`package.mk`):

```
/usr/lib/aarch64-linux-gnu    -> .
/usr/lib/arm-linux-gnueabihf  -> ../lib32
```

Also reachable as `/lib/...`. They only redirect; a library missing from
`/usr/lib` or `/usr/lib32` is still missing.

## /usr/lib/compat

53 files from PortMaster's compat set plus `portmaster-compat-libs`
(Debian 11 sonames): `libavcodec.so.58`, `libavformat.so.58`,
`libavutil.so.56`, `libswscale.so.5`, `libswresample.so.3`,
`libcrypto.so.1.1`, `libjpeg.so.62`, `libvpx.so.6`, `libwebp.so.6`,
`libx264.so.155/.160`, `libx265.so.176/.192`, `libcodec2.so.0.8.1/.0.9`,
`libFLAC.so.8`, `libbluray.so.2`, `libva*.so.2`, `librsvg-2.so.2` and
others. PortMaster's `get_controls` sets `LD_LIBRARY_PATH=/usr/lib/compat/`.
`ls /usr/lib/compat` on the console for the full list.

Also installed for ports: 32-bit `libssl 1.1` (`lib32-openssl11`),
`lib32-libzip`, `physfs`, Arch's `libluajit-5.1.so.2` (mod_ArchR.txt
preloads it for Solarus runtimes), box86/box64.
