# Test checklist and common problems

Report each item to the user as done, failed or "needs the device". Do not
tick device items on their behalf.

## On the PC

- [ ] Binary architecture: `file <binary>` says `ARM aarch64` or
      `ARM, EABI5` (armhf, hard float).
- [ ] No GPU library bundled (`libEGL*`, `libGLES*`, `libgbm*`, `libGL*`,
      `libwayland-egl*`, `libvulkan*`, `*_icd.json`).
- [ ] Script header `# PORTMASTER: <name>.zip, <Script>.sh` in the first 10
      lines; `port.json` `name` equals `<name>.zip`.
- [ ] `attr.reqs` has `opengl` if the port cannot run on libmali.
- [ ] No `SDL_VIDEODRIVER=kmsdrm`, no hard-coded `/dev/dri/card0` output.
- [ ] Vulkan renderer (if any) has a GLES fallback, or the port is declared
      as needing panfrost and is 64-bit.

## On the handheld (SSH: `ssh root@archr.local`, password `archr`)

- [ ] `cat /etc/os-release`; `gpudriver`; `ls -d /sys/module/panfrost /dev/mali0`.
- [ ] 64-bit: `ldd <binary> | grep "not found"` is empty. 32-bit: `ldd`
      prints `not a dynamic executable`; use `readelf -d <binary> | grep NEEDED`
      and check each in `/usr/lib32` and the port's `libs.armhf`.
- [ ] Started from the launcher's Ports list (not the shell), on libmali:
      runs, or shows the panfrost dialog when it should.
- [ ] Same on panfrost (switch in Settings › System › GPU driver, reboot).
- [ ] Vulkan: `vulkaninfo --summary` lists `Mali-G31 MC1` on panfrost; the
      port picks Vulkan there and GLES on libmali.
- [ ] Fullscreen, controls (pad and, if used, gptokeyb), sound, exit back to
      the launcher, second start keeps saves.
- [ ] `/var/log/exec.log` has no missing-library or permission errors.
- [ ] Copied once from a PC over Samba (permissions lost) and still starts
      from the Ports list.

## Common problems

| Symptom | Cause | Fix |
|---|---|---|
| `Permission denied` | execute bit lost in a copy | start from the Ports list (`runemu.sh` restores it) or `chmod +x` |
| `libGL.so.1: cannot open shared object file`; SDL GL context fails | libmali: `libGL.so` is `/dev/null`, SDL is the GLES-only build | GLES, gl4es + `libgl_ArchR.txt`, or `reqs: opengl` |
| `kmsdrm not available` | sway holds the display | drop `SDL_VIDEODRIVER=kmsdrm` (ArchR SDL2 falls back anyway; `ARCHR_SDL_KMSDRM=1` forces it) |
| no Vulkan GPU, `panvk is not well-tested on v7` | variable missing (libmali, or unset by the port) | fall back to GLES; never set the variable in the port |
| 32-bit program cannot load `libvulkan.so.1` | no 32-bit Vulkan | build 64-bit |
| `/usr/lib/arm-linux-gnueabihf/libX.so` not found | links exist, the library does not | bundle it, or check `/usr/lib/compat` |
| missing `libcrypto.so.1.1`, `libavcodec.so.58` ... | old Debian sonames | call `get_controls` (sets `LD_LIBRARY_PATH=/usr/lib/compat/`) |
| black screen with gl4es on panfrost | `LIBGL_FB=4` (GBM) draws nothing under sway | source `libgl_ArchR.txt` (sets 3 on panfrost) |
| window not fullscreen | `app_id` differs from the name given to `pm_platform_helper` | pass the binary path, or set `app_id` |
| crash inside libmali GLES1 | libmali bug (bzflag) | ask for the port to be added to `panfrost.txt` |
| `tasksetter: No such file or directory` | old PortMaster folder | `portmaster_prepare` restores it from the bundled release |
