#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
output=${1:?absolute empty output directory is required}
python3 "$root/.github/rpg-runtime/candidate_descriptor.py" prepare "$output"
mkdir -p "$root/build"
work=$(mktemp -d "$root/build/retrom-vice-xvic-web.XXXXXX")
trap 'rm -rf "$work"' EXIT INT TERM
mkdir -p "$work/raw" "$work/build"
python3 "$root/.github/rpg-runtime/verify-source.py"
source_digest=$(python3 "$root/.github/rpg-runtime/candidate_descriptor.py" digest "$output")
python3 "$root/.github/rpg-runtime/candidate_descriptor.py" paths "$output" > "$work/source-files"
tar -C "$root" --null --verbatim-files-from -T "$work/source-files" -cf "$work/source.tar"

export RETROM_HOST_UID="$(id -u)"
export RETROM_HOST_GID="$(id -g)"
if ! docker run --rm --platform linux/amd64 --hostname retrom-vice-xvic \
  --env RETROM_HOST_UID --env RETROM_HOST_GID \
  --volume "$work/source.tar:/source.tar:ro" \
  --volume "$root/.github/rpg-runtime:/recipe:ro" \
  --volume "$work/build:/work" \
  --volume "$work/raw:/output" \
  emscripten/emsdk@sha256:af45409f3199d88db4b1b03af0098532c8fb33a375ac257463eeb0a622870d06 \
  /recipe/build-emulatorjs-core.sh vice_xvic EMUTYPE=xvic \
  >"$work/build.log" 2>&1; then
  tail -200 "$work/build.log" >&2
  exit 1
fi

test "$source_digest" = "$(python3 "$root/.github/rpg-runtime/candidate_descriptor.py" digest "$output")"
stage="$work/stage"
mkdir -p "$stage"
install -m 0644 "$work/raw/vice_xvic_libretro.js" "$stage/"
install -m 0644 "$work/raw/vice_xvic_libretro.wasm" "$stage/"
install -m 0644 "$root/COPYING" "$stage/license.txt"
printf '%s\n' '{"minimumEJSVersion":"4.2.2","version":"2.0.2"}' > "$stage/build.json"
printf '%s\n' '{"name":"vice_xvic","extensions":["d64","d71","d80","d81","d82","g64","x64","nib","t64","tap","prg","p00","crt","bin","cmd","rom"],"makeoptions":{"buildpath":"./","makescript":"Makefile","arguments":["EMUTYPE=xvic"]},"save":"nvr","options":{},"license":"COPYING","repo":"https://github.com/retrom-project/vice-libretro"}' > "$stage/core.json"

(cd "$stage" && 7z a -mtm=off -mta=off -mtc=off -bd -bso0 -bsp0 -t7z "$output/vice_xvic-wasm.data" \
  vice_xvic_libretro.js vice_xvic_libretro.wasm build.json core.json license.txt)
install -m 0644 "$root/COPYING" "$output/COPYING"
