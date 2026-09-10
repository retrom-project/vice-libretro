#!/usr/bin/env python3
"""Validate the fixed VICE VIC-20 source and Web build contract."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE = "1b4309f4d56ded7bfc5ad7ba8d5a9a44ac3388a8"
SOUND_FIX = "483e0bd4e6d24968306b8da932926b54bf936389"
LINKER = "6dd4353937ef48b6ec0bfbdbb15d1c5992d86927"
EMSDK = "af45409f3199d88db4b1b03af0098532c8fb33a375ac257463eeb0a622870d06"


def require(path: str, markers: tuple[str, ...]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    if any(marker not in text for marker in markers):
        raise SystemExit(f"RPG_RUNTIME_SOURCE_CONTRACT_INVALID:{path}")


def main() -> int:
    manifest = json.loads((ROOT / "retrom-fork.json").read_text(encoding="utf-8"))
    expected = {
        "schemaVersion": 1,
        "forkRepository": "https://github.com/retrom-project/vice-libretro",
        "defaultBranch": "retrom/g1b4309f4d56d",
        "upstreamMirrorBranch": "emulatorjs",
        "upstreams": [
            {
                "role": "emulatorjs-core",
                "repository": "https://github.com/EmulatorJS/vice-libretro",
                "refType": "COMMIT",
                "ref": BASELINE,
                "commit": BASELINE,
            },
            {
                "role": "serialization-sound-fix",
                "repository": "https://github.com/libretro/vice-libretro",
                "refType": "COMMIT",
                "ref": SOUND_FIX,
                "commit": SOUND_FIX,
            },
            {
                "role": "emulatorjs-retroarch-linker",
                "repository": "https://github.com/EmulatorJS/RetroArch",
                "refType": "COMMIT",
                "ref": LINKER,
                "commit": LINKER,
            },
        ],
        "releaseTagPattern": (
            r"^retrom-core-g1b4309f4d56d-r[1-9][0-9]*"
            r"(-rc\.[1-9][0-9]*)?$"
        ),
        "adapterAbi": "emulatorjs-state-v1",
        "releaseAssets": [
            "vice_xvic-wasm.data",
            "COPYING",
            "rpg-runtime-release.json",
        ],
    }
    expected["releaseAssets"] += [name for core in ("vice_xpet", "vice_xplus4")
                                  for name in (f"{core}-wasm.data", f"{core}-source.tar.gz", f"{core}-release.json")]
    expected["developmentCandidateAssets"] = {
        core: [f"{core}-wasm.data", "COPYING", "source.tar.gz"]
        for core in ("vice_xpet", "vice_xplus4")
    }
    if manifest != expected:
        raise SystemExit("RPG_RUNTIME_FORK_MANIFEST_INVALID")
    require("libretro/libretro-core.c", (
        "static void libretro_sound_reset(void)",
        "libretro_sound_reset();",
        "sound_close();",
    ))
    require("vice/src/sound.c", (
        "/* Serialization/rewind crash guard */",
        "snddata.lastclk > maincpu_clk",
        "snddata.fclk > maincpu_clk",
    ))
    require(".github/rpg-runtime/build-emulatorjs-core.sh", (
        LINKER,
        "emmake make",
        "/work/retroarch/libretro_emscripten.a",
    ))
    require(".github/rpg-runtime/build-web.sh", (
        EMSDK,
        '"EMUTYPE=$emutype"',
        '${core}-wasm.data',
        '"minimumEJSVersion":"4.2.2"',
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
