#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

TAG = re.compile(r"^retrom-core-g1b4309f4d56d-r[1-9][0-9]*(?:-rc\.[1-9][0-9]*)?$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--repository", required=True)
parser.add_argument("--tag", required=True)
parser.add_argument("--commit", required=True)
parser.add_argument("--core", choices=("vice_xvic", "vice_xpet", "vice_xplus4"), default="vice_xvic")
args = parser.parse_args()
ARCHIVE = f"{args.core}-wasm.data"
MEMBERS = {f"{args.core}_libretro.js", f"{args.core}_libretro.wasm", "build.json", "core.json", "license.txt"}
if TAG.fullmatch(args.tag) is None or COMMIT.fullmatch(args.commit) is None:
    raise SystemExit("RETROM_CORE_RELEASE_IDENTITY_INVALID")

root_source = Path(__file__).resolve().parents[2]
if args.repository != "https://github.com/retrom-project/vice-libretro":
    raise SystemExit("RETROM_CORE_RELEASE_IDENTITY_INVALID")
archive = args.output / ARCHIVE
license_path = args.output / "COPYING"
if archive.is_symlink() or not archive.is_file() or archive.stat().st_size < 500_000:
    raise SystemExit("RETROM_CORE_ARCHIVE_INVALID")
if license_path.is_symlink() or not license_path.is_file():
    raise SystemExit("RETROM_CORE_LICENSE_INVALID")

listing = subprocess.run(["7z", "l", "-slt", str(archive)], capture_output=True, text=True, check=True).stdout
entries = listing.split("----------\n", 1)[1].strip().split("\n\n")
member_names = []
for entry in entries:
    fields = dict(line.split(" = ", 1) for line in entry.splitlines() if " = " in line)
    member_names.append(fields.get("Path"))
    if fields.get("Folder") == "+" or "Symbolic Link" in fields or "Hard Link" in fields:
        raise SystemExit("RETROM_CORE_ARCHIVE_INVALID")
if len(member_names) != len(MEMBERS) or set(member_names) != MEMBERS:
    raise SystemExit("RETROM_CORE_ARCHIVE_INVALID")
with tempfile.TemporaryDirectory() as temporary:
    subprocess.run(["7z", "x", "-bd", "-bso0", "-bsp0", f"-o{temporary}", str(archive)], check=True)
    root = Path(temporary)
    if {path.name for path in root.iterdir()} != MEMBERS:
        raise SystemExit("RETROM_CORE_ARCHIVE_INVALID")
    if any(path.is_symlink() or not path.is_file() for path in root.iterdir()):
        raise SystemExit("RETROM_CORE_ARCHIVE_INVALID")
    wasm = (root / f"{args.core}_libretro.wasm").read_bytes()
    javascript = (root / f"{args.core}_libretro.js").read_text(errors="strict")
    core = json.loads((root / "core.json").read_text())
    build = json.loads((root / "build.json").read_text())
    if wasm[:8] != b"\0asm\x01\0\0\0" or len(wasm) < 1_000_000:
        raise SystemExit("RETROM_CORE_WASM_INVALID")
    if args.core not in javascript or "Module" not in javascript:
        raise SystemExit("RETROM_CORE_JAVASCRIPT_INVALID")
    if core.get("name") != args.core or core.get("save") != "nvr":
        raise SystemExit("RETROM_CORE_MANIFEST_INVALID")
    if build != {"minimumEJSVersion": "4.2.2", "version": "2.0.2"}:
        raise SystemExit("RETROM_CORE_MANIFEST_INVALID")
    if not (root / "license.txt").read_bytes() == license_path.read_bytes() == (root_source / "COPYING").read_bytes():
        raise SystemExit("RETROM_CORE_LICENSE_INVALID")

assets = [{"filename": path.name, "observedSha256": digest(path), "sizeBytes": path.stat().st_size}
          for path in (archive, license_path)]
metadata = {
    "adapterAbi": "emulatorjs-state-v1",
    "assets": assets,
    "commit": args.commit,
    "digestPolicy": "OBSERVED_CACHE_INTEGRITY_ONLY",
    "repository": args.repository,
    "schemaVersion": 1,
    "tag": args.tag,
}
(args.output / "rpg-runtime-release.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
