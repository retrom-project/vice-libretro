#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
core=${RETROM_VICE_CORE:-vice_xvic}
output=${1:?absolute empty output directory is required}
"$root/.github/rpg-runtime/build-web.sh" "$output"

commit=$(git -C "$root" rev-parse HEAD)
python3 "$root/.github/rpg-runtime/verify-release.py" --output "$output" \
  --repository "https://github.com/retrom-project/vice-libretro" \
  --tag retrom-core-g1b4309f4d56d-r999999 --commit "$commit" --core "$core"
rm "$output/rpg-runtime-release.json"
python3 "$root/.github/rpg-runtime/candidate_descriptor.py" finalize "$output" --core-id "$core"
