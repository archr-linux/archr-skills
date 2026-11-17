# OpenCL

## Files (from `pacman -Ql libmali` and the console)

- `/etc/OpenCL/vendors/mali.icd`, content: `libMaliOpenCL.so.1`
- `/usr/lib/mali/libMaliOpenCL.so.1` (and `.so`), `/usr/lib32/mali/libMaliOpenCL.so.1`:
  forwarders, `NEEDED libmali-hook.so.1` -> `libmali.so.1`.
- `libmali.so.1.9.0` exports 154 `cl*` symbols, including
  `clGetPlatformIDs@@OPENCL_1.0` and `clIcdGetPlatformIDsKHR`. Strings mention
  "OpenCL C 2.0 or OpenCL C 3."; the exact version reported at runtime was
  not measured.

Not present:

- no ICD loader (`libOpenCL.so*`) in `/usr/lib` or `/usr/lib32`;
- no `libMaliOpenCL.so.1` in `/usr/lib` (the boot mount needs an existing
  target, so it is never put there);
- Mesa has no Rusticl / Clover (no OpenCL files in `pacman -Ql mesa`).

## Consequences

| Driver | OpenCL |
|---|---|
| libmali | possible: link `libmali.so.1`, or `dlopen("/usr/lib/mali/libMaliOpenCL.so.1")`, or bundle an ICD loader `libOpenCL.so.1` and add `/usr/lib/mali` to `LD_LIBRARY_PATH` so it can open the name in `mali.icd` |
| panfrost | none (`mali_kbase` not loaded, `/dev/mali0` absent; no Mesa OpenCL) |

An OpenCL port must check for `/dev/mali0` and handle "no platform". If it
cannot run without OpenCL it needs libmali, which is the default; there is no
mechanism to ask the user to switch to libmali (the launcher only asks for
panfrost).

No OpenCL program has been run on the R36S by ArchR. Say so when advising.
