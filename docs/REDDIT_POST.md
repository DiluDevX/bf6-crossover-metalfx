# Battlefield 6 campaign on M1 Pro: downloadable CrossOver MetalFX workaround + HUD corruption fix

I put the tested workaround and setup instructions on GitHub so you can download the script instead of copying a long code block:

**https://github.com/DiluDevX/bf6-crossover-metalfx**

Use **Code → Download ZIP**, extract it, and follow the README. It is readable Python with no pip dependencies, no downloads performed by the script, and no game files or Apple binaries in the repository.

## Tested setup

- M1 Pro, 8-core CPU / 14-core GPU, 16 GB unified memory.
- macOS 27.2 (26B123).
- CrossOver Preview 20261015 / 27.0.0.41073.
- Manually installed D3DMetal 4.0b3; script requires the exact tested binary hash.
- Campaign already launching through CrossOver.

## What it addresses

**Outdated NVIDIA driver error:** D3DMetal reported 576.02, which Battlefield displayed as 576.2; the game required 576.88. The script copies the installed framework and changes two NVAPI version-return constants in that local copy. It then creates a launcher that selects the copy only for this game process. Actual campaign rendering with DLSS/MetalFX worked afterward.

**Colored blocks around the objective/ammo HUD:** these remained with FSR and FG off. At matched 96% scale, they returned on Metal 4 and disappeared on legacy Metal. The generated launcher uses `D3DM_MTL4=0`. This still uses D3DMetal 4.0b3, selecting its legacy backend.

**Extra press-Space/restart sequence:** an optional, separately hash-checked direct campaign launch removed it on the exact tested game build. This option is not a universal Steam startup method.

## Starting settings

1080p, DLSS enabled, 96% resolution scale, FG initially off, legacy Metal, and a display at 60 Hz if supported. The 96% value was part of the tested clean setup; it has not been proven necessary on legacy and did not fix Metal 4 by itself.

Once upscaling/HUD/gameplay work, try NVIDIA FG at 2× with MFG off. I saw roughly 30 FPS without FG in sampled runs and readings over 70 with FG. A logged FG sample averaged roughly 62 presentations/sec **including generated frames**—not 62–70 engine-rendered FPS. My physical screen was 60 Hz, and these were manually played samples rather than a controlled benchmark.

## Steam or another install folder?

The script takes your actual game path and bottle name, so it works with different folder layouts. **The current retail Steam/EA launch path is unverified.** The campaign must already launch normally with any required authentication intact. This does not solve DRM, anti-cheat, Secure Boot or multiplayer compatibility.

## Still imperfect

- HUD/crosshair trails remain with FG, even after fixing colored blocks.
- The AGX compiled-variants-limit message still appeared in logs.
- Stable in my campaign testing, but not whole-campaign or all-Mac validation.

The script rejects unknown framework builds instead of guessing offsets. It leaves original CrossOver/game files and saved bottle settings alone, includes a dry-run check and records the generated changes in a manifest. Rollback is to quit and stop using the generated launcher; restore any manual game/display setting changes separately.

No Battlefield `wine_get_version`/`frog_get_version` replacement is used.

If you test another setup, please report your chip/RAM, software versions, framework hash, normal launch method, settings, and whether the actual campaign, HUD and reloads work—not just whether the warning disappears.
