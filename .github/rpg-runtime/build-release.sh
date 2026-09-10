#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
output=${1:?absolute empty output directory is required}
tag=${2:?release tag is required}
python3 "$root/.github/rpg-runtime/candidate_descriptor.py" prepare "$output"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
for core in vice_xvic vice_xpet vice_xplus4; do
  mkdir "$work/$core"
  RETROM_VICE_CORE="$core" "$root/.github/rpg-runtime/build-web.sh" "$work/$core"
  flags=()
  if [[ "$core" != vice_xvic ]]; then
    mv "$work/$core/source.tar.gz" "$work/$core/$core-source.tar.gz"
    flags+=(--source-name "$core-source.tar.gz" --metadata-name "$core-release.json")
  fi
  python3 "$root/.github/rpg-runtime/verify-release.py" --output "$work/$core" \
    --repository https://github.com/retrom-project/vice-libretro --tag "$tag" \
    --commit "$(git -C "$root" rev-parse HEAD)" --core "$core" "${flags[@]}"
  cp "$work/$core/"* "$output/"
done
