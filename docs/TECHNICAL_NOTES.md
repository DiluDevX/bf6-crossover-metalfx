# Verified changes and evidence limits

## NVAPI driver-version gate

The tested warning reports NVIDIA GeForce driver 576.2 and requires 576.88 or later. The installed x86_64 D3DMetal binary returns 57602 from both `nvapi::NvAPI_GetDisplayDriverVersion` and `nvapi::NvAPI_SYS_GetDriverAndBranchVersion`.

Only the exact binary with SHA-256 `a64950e8324cec32c9a442daa1fafd03823bd199fdd84fee5c73679b5fe86660` is supported. Its verified file offsets/instruction bytes are:

| Offset | Original | Local replacement |
|---|---|---|
| `0x17c585` | `48 c7 42 04 02 e1 00 00` | `48 c7 42 04 58 e1 00 00` |
| `0x17c5ac` | `c7 01 02 e1 00 00` | `c7 01 58 e1 00 00` |

The immediate integer changes from `0xe102` (57602) to `0xe158` (57688). This changes reported compatibility information; it does not install a Windows driver or add GPU capabilities. Afterward the copied binary is ad-hoc signed, which also changes its signature data. The setup manifest records the final hash.

The warning template exists in the game renderer. Matching return values and the isolated workaround support a renderer driver-version gate; a full runtime API-call trace was not captured. Successful gameplay with DLSS after the override was user-confirmed. Merely removing a warning is not sufficient validation on another build.

## Process-local runtime selection

The tested installed `libd3dshared.dylib` reads `D3DMETAL_FRAMEWORK_PATH` using `getenv` and passes the supplied full binary path to `dlopen` during `D3DRMDispatch_Init`. The actual loaded-file list confirmed the copied framework was selected, while NVAPI/NGX Wine wrappers remained the installed Apple versions.

The tested `D3DMDevice::MTL4OptionEnabled` implementation reads `D3DM_MTL4`, parses it with `atoi`, and treats zero as false. This verifies `D3DM_MTL4=0` selects the legacy backend. These are verified implementation details for this runtime, not a stable vendor API guarantee.

The launch environment is:

```text
CX_GRAPHICS_BACKEND=d3dmetal
D3DM_ENABLE_METALFX=1
D3DMETAL_FRAMEWORK_PATH=<absolute local framework binary path>
D3DM_MTL4=0
```

`CX_GRAPHICS_BACKEND=d3dmetal` was confirmed in Wine's process log, and MetalFX support is documented by CodeWeavers. No DXVK-specific driver override is used.

## HUD corruption vs temporal trails

Colored block/noise corruption appeared in objective/ammo HUD regions. It remained after a fresh start with NVIDIA FG verified off, and also with FSR/MetalFX disabled. At matched 96% resolution scale, the user confirmed a clean HUD on legacy Metal and recurring corruption on Metal 4. On legacy with DLSS and FG enabled, colored blocks remained absent but HUD/crosshair trails persisted.

This isolates the observed colored defect to the tested Metal 4 path relative to legacy; it does not identify a specific bad shader, format, synchronization operation or proprietary implementation bug. Early tests also changed resolution scale, so their apparent backend result was confounded until the matched-scale test. Scale was 100% in the preceding corrupt configuration and 96% in the final setup; 96% alone did not fix Metal 4.

## Optional direct campaign startup

Process logs show root `bf6.exe` launching `SP/bf6.exe`, followed by a second explicit campaign launch with:

```text
SP/bf6.exe -Steam -launchExperience -dataPath <game root>
```

Replaying that command removed the unwanted extra startup sequence on the tested build. The script gates this optional path on both SHA-256 values:

| File | SHA-256 |
|---|---|
| Root `bf6.exe` | `9ab6ff66ba75c485aac8edd95524d39ef9017a46dac006c9372cca365a153937` |
| `SP/bf6.exe` | `aff614e6fdc8c2a47a9fc1723fb6a02d84d42258d27fc617b99572f29970275d` |

Game binaries are neither patched nor redistributed. This is not a universal launcher method for other game releases or stores. Leave the option off for unverified builds and retain required normal launch/authentication flows.

## Performance interpretation

Sampled runs were manually played and not independently controlled for identical routes. They support the user's observations, not broad performance promises.

| Sample | Presented FPS | p95 presentation interval |
|---|---:|---:|
| MetalFX / FG off / default Metal 4 / TV 30 Hz | 24.65 | 66.67 ms |
| FSR / FG off / default Metal 4 / TV 30 Hz | 25.87 | 66.67 ms |
| MetalFX / FG off / default Metal 4 / TV 60 Hz | 30.60 | 50.04 ms |
| MetalFX / FG off / legacy / TV 60 Hz | 29.68 | 50.04 ms |
| MetalFX / FG on / default Metal 4 / TV 60 Hz | 61.98 including generated frames | 23.10 ms |

The FG sample predates final HUD tuning on legacy and is not a timed benchmark of the final setup. Separate engine-rendered FPS was not measured. Do not halve presented FPS and call the result a measurement. The 60 Hz TV cannot show 70 distinct full refreshes per second even when a presentation counter reports higher values.

The display-mode experiment changed desktop resolution as well as refresh rate (5K30 to QHD60), while requested game output remained 1080p. It does not isolate refresh rate from compositor/resolution effects.

`AGX: exceeded compiled variants footprint limit` occurred under both upscalers and backends. It remained in the clean-HUD legacy run, so it is not established as the cause of the colored HUD defect. Long-duration and whole-campaign validation are incomplete.
