# Vulkan on ArchR 3.1.0

Available only with GPU driver **panfrost**. Driver: Mesa PanVK.

## Files

| | |
|---|---|
| Loader | `/usr/lib/libvulkan.so.1` -> `libvulkan.so.1.4.354` (package `vulkan-loader`) |
| ICD | `/usr/share/vulkan/icd.d/panfrost_icd.armv8-a+crc+fp+simd.json` (package `mesa`) |
| ICD library | `/usr/lib/libvulkan_panfrost.so` |
| Implicit layer | `/usr/share/vulkan/implicit_layer.d/MangoHud.aarch64.json` |
| Tools | `vulkaninfo`, `vkcube` (`vulkan-tools` 1.4.347), `vkmark` |
| 32-bit | nothing: no `libvulkan` in `/usr/lib32` |

ICD JSON on the console:

```json
{ "ICD": { "api_version": "1.4.354", "library_arch": "64",
           "library_path": "/usr/lib/libvulkan_panfrost.so" },
  "file_format_version": "1.0.1" }
```

Match it with the glob `panfrost_icd.*.json`; the middle part is the build's
CPU flags.

## Device (vulkaninfo --summary on an R36S)

```
apiVersion         = 1.0.354
driverVersion      = 26.2.7
vendorID           = 0x13b5
deviceID           = 0x70930000
deviceType         = PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU
deviceName         = Mali-G31 MC1
driverID           = DRIVER_ID_MESA_PANVK
driverName         = panvk
conformanceVersion = 0.0.0.0
```

Instance version 1.4.354. Instance extensions include `VK_KHR_surface`,
`VK_KHR_wayland_surface`, `VK_KHR_display`, `VK_EXT_acquire_drm_display`,
`VK_KHR_xcb_surface`, `VK_KHR_xlib_surface`, `VK_EXT_headless_surface`,
`VK_KHR_get_physical_device_properties2`, `VK_EXT_debug_utils`.

Why 1.0: `src/panfrost/vulkan/panvk_vX_physical_device.c`,
`get_api_version()` returns 1.4 for `PAN_ARCH >= 10` and 1.0 otherwise; the
G31 is arch 7. Features gated on `PAN_ARCH >= 10` (`KHR_draw_indirect_count`,
`KHR_robustness2`, `KHR_spirv_1_4`, `EXT_conditional_rendering`, ...) are
absent. Query every extension and feature.

`MESA_VK_VERSION_OVERRIDE` (read in `src/vulkan/util/vk_util.c`) makes PanVK
report another version. The features are not there; experiments only.

## The variable

`src/panfrost/vulkan/panvk_physical_device.c`: for arch 6, 7 and 14, unless
`PAN_I_WANT_A_BROKEN_VULKAN_DRIVER` is set, device creation fails with
`VK_ERROR_INCOMPATIBLE_DRIVER` and the message
`panvk is not well-tested on v7, pass PAN_I_WANT_A_BROKEN_VULKAN_DRIVER=1 ...`;
the loader then reports `Failed to detect any valid GPUs`.

ArchR 3.1.0 exports it from `/etc/profile.d/041-panfrost` (source:
`distribution/projects/ArchR/packages/hardware/quirks/profile.d/041-panfrost`):

```sh
[ -d /sys/module/panfrost ] && export PAN_I_WANT_A_BROKEN_VULKAN_DRIVER=1
```

Every process started through `/etc/profile` (runemu.sh, start_*.sh, ports,
SSH login shells) has it under panfrost; under libmali it is not set. Ports
must not set it themselves.

## libmali

No Vulkan device: the panfrost ICD is masked with `/dev/null` and
`libmali.so.1` has no Vulkan entry point (`vk_icdGetInstanceProcAddr` is not
exported). `vkCreateInstance` succeeds, `vkEnumeratePhysicalDevices` returns
no device.

## Detection and fallback

Code:

1. `dlopen("libvulkan.so.1", RTLD_NOW)` or `SDL_Vulkan_LoadLibrary(NULL)`
   (only the 64-bit regular SDL2 has Vulkan; it is the active one on
   panfrost).
2. `vkCreateInstance` with `VK_KHR_surface` + `VK_KHR_wayland_surface`.
3. `vkEnumeratePhysicalDevices` count > 0.
4. Required extensions, features and formats present.

Any failure -> start the GLES renderer.

Shell:

```bash
if [ -d /sys/module/panfrost ] && vulkaninfo --summary >/dev/null 2>&1; then
  RENDERER=vulkan
else
  RENDERER=gles
fi
```

Exit status measured on the R36S (panfrost): 1 without the variable, 0 with
it.

Vulkan-only port: declare the panfrost requirement (`panfrost.md`) and make
the binary 64-bit.

## Field results (R36S, panfrost, Mesa 26.2.7)

Reported working: `vkcube`, PPSSPP and RetroArch on Vulkan. `vkmark`: GPU job
faults in scenes with textures. Expect rendering faults in heavier workloads.

## Emulators

Emulators default to GLES. Settings › Games › Renderer sets
`graphics_backend` (`opengl` or `vulkan`) per system:

- RetroArch: `setsettings.sh` `set_ra_videodriver` writes
  `video_driver = vulkan`, or `gl` with a log line when panfrost is not
  loaded.
- PPSSPP standalone: `start_ppsspp.sh` -> `GraphicsBackend = 3 (VULKAN)`.
- Flycast standalone: `start_flycast.sh` -> `pvr.rend = 4`.
- Both standalone scripts turn `vulkan` into `opengl` when
  `/sys/module/panfrost` is absent.

Not relevant to ports, which pick their renderer themselves.
