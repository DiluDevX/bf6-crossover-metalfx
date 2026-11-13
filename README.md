# Battlefield 6 CrossOver MetalFX workaround

An unofficial, reversible graphics compatibility setup for an **already-launching Battlefield 6 campaign** on macOS/CrossOver.

Tested on an M1 Pro with D3DMetal 4.0b3: bypasses the reported NVIDIA driver-version mismatch using a local framework copy and selects the legacy Metal backend to avoid the tested colored HUD corruption. Optional direct campaign startup removes an extra relaunch on the exact tested game build.

**Current limitations:** HUD/crosshair trails remain with frame generation. The retail Steam/EA launch path has not been verified. This does not solve DRM, licensing, anti-cheat, Secure Boot or multiplayer compatibility.

## Download

Use **Code → Download ZIP**, then extract it. The repository contains readable Python and documentation—no game files, Apple frameworks, patched DLLs or bundled executables.

Alternatively:

```bash
git clone https://github.com/DiluDevX/bf6-crossover-metalfx.git
cd bf6-crossover-metalfx
```

Requires macOS, an existing working CrossOver bottle, Python 3.8+ and the macOS `codesign` tool. No pip dependencies or downloads are performed by the script.

## Supported configuration

Tested 13 November 2026:

| Component | Tested configuration |
|---|---|
| Mac | M1 Pro, 8-core CPU, 14-core GPU, 16 GB unified memory |
| macOS | 27.2, build 26B123 |
| CrossOver | Preview 20261015 / 27.0.0.41073 |
| D3DMetal | Manually installed 4.0b3; exact binary hash required |
| Game | Campaign already launches; retail Steam build not independently verified |

The script supports **only this D3DMetal binary SHA-256**, regardless of the version label:

```text
a64950e8324cec32c9a442daa1fafd03823bd199fdd84fee5c73679b5fe86660
```

A different hash is rejected. Do not remove the check or apply these offsets to another build. Other Macs and software combinations are unverified.

## Setup

1. Close the game. Identify its actual CrossOver bottle and root `bf6.exe`. In Steam, use Manage → Browse local files; custom libraries can be anywhere. Other installation paths are accepted too, provided the campaign already runs and its normal launch/authentication requirements are satisfied.
2. The script checks existing bottles in `~/Library/Application Support/CrossOver/Bottles/`. Custom bottle-storage locations are not supported by this version. Do not assume an existing desktop shortcut selects the expected bottle.
3. Open Terminal in the extracted repository folder. Replace the example paths/name below and validate without changing anything:

```bash
python3 prepare_bf6_metalfx.py \
  --app "/Applications/CrossOver Preview.app" \
  --bottle "YOUR EXISTING BOTTLE NAME" \
  --game "/full/path/to/Battlefield 6/bf6.exe" \
  --out "$HOME/BF6-MetalFX-Compatibility" \
  --check-only
```

Use `/Applications/CrossOver.app` if that is your installed app. The exact supported framework hash must still match. The script does not install GPTK or upgrade CrossOver.

4. If validation passes, run the same command **without `--check-only`**. Choose a new permanent output folder; the script refuses to overwrite an existing one.
5. Launch using `Launch BF6 MetalFX.command` inside that output folder. Keep the folder in place. The script prepares the files but does not automatically launch the game.

It copies the installed framework, backs up the original binary, verifies the expected bytes, patches two driver-version return constants, ad-hoc signs the local copy and generates a process-local launcher. It records paths/hashes in `manifest.json` and appends launch output to `last-launch.log`.

**Original CrossOver files, game binaries, saved bottle configuration and game profiles are not edited.** Never commit or upload the generated output folder: it contains a copy of Apple's framework. The MIT license here applies only to this project's code/documentation, not Apple, EA, CodeWeavers or NVIDIA software.

## In-game and display settings

Back up your graphics profile before changing settings. On the tested installation it was `~/Documents/Battlefield 6/settings/steam/PROFSAVE_profile`; your location may differ.

The verified clean HUD setup used:

- 1920×1080 output, DLSS enabled, resolution scale **96%**.
- Legacy Metal backend, selected by the launcher using `D3DM_MTL4=0`.
- Frame generation off for initial validation. Test actual campaign rendering, HUD, reloads and transitions.
- Then optionally NVIDIA FG at 2×, with Multi Frame Generation off. Colored blocks were absent in the tested scene, but HUD/crosshair trails remained.
- A display running at 60 Hz. Changing the test TV from 5K/30 Hz to a supported 1440p/60 Hz mode improved pacing. The script does not change display settings.

At matched 96% scale, colored HUD blocks returned on Metal 4 and disappeared on legacy Metal. **96% alone did not fix the Metal 4 path**, and we have not established that 96% is necessary on legacy. Start with the tested settings before experimenting.

## Optional startup workaround

On the tested build, the root executable explicitly launched/relaunched `SP/bf6.exe` after a press-Space screen. The `--direct-campaign` option replays the final observed campaign command and eliminated the extra startup sequence.

Add `--direct-campaign` to setup/check commands only if wanted. It checks both game executable hashes and refuses unverified builds. Omit it to retain normal root startup. It is **not established as a universal retail Steam/EA launch method** and does not disable shader compilation or protections.

See [technical details and exact hashes](docs/TECHNICAL_NOTES.md).

## Results and limits

User-reported stable campaign play; manually played samples were around 30 FPS without FG after improving display timing. A logged FG sample averaged about 62 **presentations/sec including generated frames**, with user-observed readings over 70. This is not a measurement of engine-rendered FPS; the physical test display was 60 Hz. These were not controlled benchmarks or whole-campaign validation.

Remaining issues:

- HUD/crosshair trails with FG.
- `AGX: exceeded compiled variants footprint limit` appeared in multiple configurations, including ones without visible colored corruption. This project does not establish a fix for that warning.
- Other builds, Macs, campaign scenes and retail Steam/EA startup remain unverified.

No `wine_get_version` → `frog_get_version` patch is applied. Neither tested BF6 executable contained that string.

## Rollback

Quit the game and stop using the generated launcher. A normal launch uses the original installed framework. No global environment variables were set and no saved bottle settings were edited. Restore your own backed-up graphics profile/display mode if you want to undo your manual setting changes.

After quitting the game, the generated output folder can be removed if no longer needed. Revalidate after any CrossOver/GPTK update; an old local copy will not automatically receive vendor updates. Keep copies per installation/build distinct.

## Checks and reports

```bash
python3 -m unittest discover -s tests -v
```

The tests cover refusal/nonmutation behavior and input validation using synthetic temporary fixtures. They do not emulate Metal or prove game compatibility. The original preparation was also smoke-tested on the supported local framework, including signature and generated shell syntax checks.

For a useful report, include chip/RAM, macOS, CrossOver build, framework hash, normal launch method, settings, and whether the campaign/HUD/reloads work. Redact personal paths from logs. Do not attach game files, framework binaries, credentials or entire registry files.

## References

- [CodeWeavers: DLSS powered by MetalFX](https://support.codeweavers.com/en_US/miscellanous/advanced-settings-in-crossover-mac-26)
- [NVIDIA NVAPI definitions](https://github.com/NVIDIA/nvapi/blob/main/nvapi.h)
- [NVIDIA Streamline frame-generation integration guide](https://github.com/NVIDIAGameWorks/Streamline/blob/main/docs/ProgrammingGuideDLSS_G.md)

No affiliation or endorsement by Apple, EA, CodeWeavers or NVIDIA.
