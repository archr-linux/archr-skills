---
name: archr-ports-dev
description: Build, adapt, package and debug game ports for ArchR 3.1.0, the Arch Linux ARM distro for RK3326 handhelds such as the R36S (aarch64 + armhf lib32, Mali-G31, sway/Wayland, PortMaster preinstalled). Use this skill whenever someone wants to make a port run on ArchR, port a game or engine to the R36S, fix a PortMaster port that fails on ArchR, choose between OpenGL ES, desktop OpenGL (gl4es), Vulkan or OpenCL there, find where libEGL/libGLESv2/libgbm/libGL/libvulkan/SDL2 live under the libmali or panfrost GPU driver, detect the active GPU driver, make a port tell the system it needs panfrost (port.json reqs opengl, panfrost.txt, the launcher's switch dialog), deal with SDL_VIDEODRIVER=kmsdrm, Debian multiarch paths (/usr/lib/aarch64-linux-gnu, /usr/lib/arm-linux-gnueabihf), /usr/lib/compat sonames, gptokeyb, PortMaster control.txt / mod_ArchR.txt / libgl_ArchR.txt variables, or test a port on the console. Trigger even when the user just says "port para o Arch R", "PortMaster no R36S", "jogo precisa do panfrost", "Vulkan no R36S" or "libmali vs panfrost".
---

# Game ports for ArchR

ArchR runs every game inside sway (Wayland) as root, on an RK3326 with a
Mali-G31 GPU. Ports are shell scripts in `/storage/roms/ports` started by
`runemu.sh`, almost always PortMaster ports. The one thing that changes what
a port can use is the **GPU driver** the user picked:

- `libmali` (default): ARM blob. OpenGL ES 1.1/2.0/3.x, EGL, GBM, OpenCL in
  `libmali.so.1`. No desktop GL (`libGL.so` is `/dev/null`), no Vulkan.
- `panfrost`: Mesa 26.2.7. OpenGL 3.1, OpenGL ES 3.1, Vulkan 1.0 (PanVK,
  64-bit only, needs `PAN_I_WANT_A_BROKEN_VULKAN_DRIVER=1`, which the system
  exports when panfrost is active). No OpenCL.

Both drivers keep the same file names. At boot `gpudriver --start`
bind-mounts the libmali files (and a GLES-only SDL2) over the Mesa ones, or
leaves Mesa visible. A port never bundles or mounts GPU libraries.

## Pick the right reference

| Task | Read |
|---|---|
| Which library is where, per driver; Debian paths; compat libs; SDL2 builds | `references/libraries.md` |
| OpenGL vs GLES, gl4es, EGL/Wayland/KMS, Mesa variables | `references/graphics.md` |
| Vulkan: loader, ICD, version, variable, detection, GLES fallback | `references/vulkan.md` |
| OpenCL on libmali, none on panfrost | `references/opencl.md` |
| Declaring that a port needs panfrost; detecting the active driver | `references/panfrost.md` |
| Launch environment, PortMaster variables, paths, audio, input, packaging | `references/environment.md` |
| Testing on the console and common failures | `references/checklist.md` |

The public page with the same content is https://arch-r.io/docs/ports-dev/.

## Default advice

1. Target **OpenGL ES 2.0/3.0 through EGL on Wayland** (SDL2 with an ES
   profile). It runs on both drivers without asking the user anything.
2. Desktop GL only: bundle gl4es and source `libgl_ArchR.txt`, or declare
   the panfrost requirement.
3. Vulkan: treat it as optional. Probe at runtime, fall back to GLES. A
   Vulkan-only port declares the panfrost requirement and is 64-bit.
4. Declare the panfrost requirement with `"reqs": ["opengl"]` in the port's
   `port.json` (PortMaster's field). The launcher then offers the switch
   instead of launching on libmali.
5. Detect the running driver with `[ -d /sys/module/panfrost ]` /
   `[ -e /dev/mali0 ]`, not with `gpudriver` (that prints the configured
   value, which can differ until reboot).

## Working rules

- Use only paths, variables and behaviours that appear in the references.
  They were read from the ArchR sources and checked on an R36S. If the user
  asks about something they do not cover (Xwayland, OpenCL kernels actually
  running, a device other than the RK3326), say it is not confirmed instead
  of guessing.
- Never tell a port to call `gpudriver panfrost|libmali`, edit
  `/usr/share/archr/portmaster/panfrost.txt` on the console, mount over
  system libraries, or set `PAN_I_WANT_A_BROKEN_VULKAN_DRIVER` itself. The
  first two change system state and are replaced by updates; the last hides
  that Vulkan is not supposed to be used.
- Never bundle `libEGL*`, `libGLES*`, `libgbm*`, `libGL*`, `libwayland-egl*`,
  `libvulkan*` or ICD JSON files in a port.
- `SDL_VIDEODRIVER=kmsdrm` cannot get the screen under sway; ArchR's SDL2
  falls back to Wayland on its own. Remove the variable rather than fight it.
- The panfrost dialog only appears when the port is started from the
  launcher's Ports list. Scripts should still check the driver and print a
  message.
- Switching the driver needs a reboot. Do not plan tests that switch it in
  place.
- Testing on the PC proves nothing about the GPU path. Say which items still
  need a run on the handheld (`references/checklist.md`).
