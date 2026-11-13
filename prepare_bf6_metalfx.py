#!/usr/bin/env python3
"""Prepare a local BF6 graphics compatibility copy. Does not launch the game."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shlex
import shutil
import subprocess

EXPECTED = "a64950e8324cec32c9a442daa1fafd03823bd199fdd84fee5c73679b5fe86660"
CAMPAIGN_HASH = "aff614e6fdc8c2a47a9fc1723fb6a02d84d42258d27fc617b99572f29970275d"
ROOT_HASH = "9ab6ff66ba75c485aac8edd95524d39ef9017a46dac006c9372cca365a153937"
PATCHES = (
    (0x17C585, bytes.fromhex("48c7420402e10000"), bytes.fromhex("48c7420458e10000")),
    (0x17C5AC, bytes.fromhex("c70102e10000"), bytes.fromhex("c70158e10000")),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message):
    raise SystemExit(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, help="Installed CrossOver .app path")
    parser.add_argument("--bottle", required=True, help="Exact existing bottle name")
    parser.add_argument("--game", required=True, help="Absolute path to root bf6.exe")
    parser.add_argument("--out", required=True, help="New permanent output folder; must not exist")
    parser.add_argument("--check-only", action="store_true", help="Validate inputs without writing anything")
    parser.add_argument("--direct-campaign", action="store_true",
                        help="Optional startup workaround; restricted to the exact tested executable hashes")
    args = parser.parse_args()
    if platform.system() != "Darwin":
        fail("This script requires macOS.")
    app = Path(args.app).expanduser().resolve()
    game = Path(args.game).expanduser().resolve()
    out = Path(args.out).expanduser().absolute()
    if not args.bottle or Path(args.bottle).name != args.bottle:
        fail("Supply a bottle name, not a path.")
    bottle = Path.home() / "Library/Application Support/CrossOver/Bottles" / args.bottle
    if not (bottle / "cxbottle.conf").is_file():
        fail("Existing bottle not found in the standard CrossOver bottle folder. No bottle will be created.")
    base = app / "Contents/SharedSupport/CrossOver"
    wine = base / "bin/wine"
    framework = base / "lib/apple_gptk/external/D3DMetal.framework"
    original = framework / "Versions/A/D3DMetal"
    if not wine.is_file() or not original.is_file() or not game.is_file():
        fail("CrossOver runtime or game path not found. Check --app and --game.")
    if game.name.lower() != "bf6.exe" or game.parent.name.lower() == "sp":
        fail("--game must name the root bf6.exe, not SP/bf6.exe.")
    actual = digest(original)
    if actual != EXPECTED:
        fail("Unsupported D3DMetal binary. REFUSING TO PATCH.\nExpected: " + EXPECTED + "\nFound:    " + actual)
    for offset, old, new in PATCHES:
        if original.read_bytes()[offset:offset + len(old)] != old:
            fail("Expected instruction bytes do not match; refusing to patch.")
    campaign = game.parent / "SP/bf6.exe"
    if args.direct_campaign:
        if digest(game) != ROOT_HASH or not campaign.is_file() or digest(campaign) != CAMPAIGN_HASH:
            fail("Direct-campaign startup is unverified for these game executables. Omit --direct-campaign.")
    if args.check_only:
        print("Verified supported D3DMetal hash, instruction bytes, bottle and game path. Nothing changed.")
        return
    if out.exists():
        fail("Output folder already exists. Choose a NEW permanent folder; existing files will not be overwritten.")
    out.mkdir(parents=True)
    local_framework = out / "Frameworks/D3DMetal.framework"
    shutil.copytree(framework, local_framework, symlinks=True)
    binary = local_framework / "Versions/A/D3DMetal"
    try:
        binary.resolve().relative_to(out.resolve())
    except ValueError:
        fail("Copied framework binary resolves outside the output folder; refusing to modify it.")
    shutil.copy2(original, out / "D3DMetal.original")
    data = bytearray(binary.read_bytes())
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        fail("Copied binary hash mismatch; refusing to patch.")
    for offset, old, new in PATCHES:
        if data[offset:offset + len(old)] != old:
            fail("Copied instruction bytes do not match; refusing to patch.")
        data[offset:offset + len(old)] = new
    binary.write_bytes(data)
    subprocess.run(["/usr/bin/codesign", "--force", "--sign", "-", str(binary)], check=True)
    subprocess.run(["/usr/bin/codesign", "--verify", str(binary)], check=True)
    environment = {
        "CX_GRAPHICS_BACKEND": "d3dmetal",
        "D3DM_ENABLE_METALFX": "1",
        "D3DMETAL_FRAMEWORK_PATH": str(binary),
        "D3DM_MTL4": "0",
    }
    target = campaign if args.direct_campaign else game
    command = [str(wine), "--bottle", args.bottle, "--no-update", "--wait-children",
               "--env", " ".join(key + "=" + shlex.quote(value) for key, value in environment.items()),
               "--debugmsg", "-all", "--workdir", str(game.parent), str(target)]
    if args.direct_campaign:
        command += ["-Steam", "-launchExperience", "-dataPath", str(game.parent)]
    manifest = {
        "original_sha256": actual, "local_patched_sha256": digest(binary),
        "original_framework": str(framework), "local_framework": str(local_framework),
        "bottle": args.bottle, "game": str(game), "direct_campaign": args.direct_campaign,
        "environment": environment, "command": command,
        "patches": [{"offset": hex(off), "before": old.hex(), "after": new.hex()} for off, old, new in PATCHES],
        "rollback": "Stop using the generated launcher. Original CrossOver/game/bottle settings were not edited.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    launcher = out / "Launch BF6 MetalFX.command"
    log = out / "last-launch.log"
    launcher.write_text("#!/bin/zsh\n# Generated graphics compatibility launcher; see manifest.json.\n"
                        "cd " + shlex.quote(str(game.parent)) + " || exit 1\n"
                        "exec " + shlex.join(command) + " >> " + shlex.quote(str(log)) + " 2>&1\n")
    launcher.chmod(0o755)
    print("Prepared:", launcher)
    print("Game not launched. Original CrossOver/game/bottle/profile files were not edited.")
    print("Keep this output folder in place. Read manifest.json and the guide before launching.")


if __name__ == "__main__":
    main()
