# Retrom VICE fork maintenance rules

This fork builds the EmulatorJS-compatible VIC-20 core consumed by
`retrom-project/retrom-runtime`. It must remain independent of Retrom host APIs,
databases, credentials, and private game content.

## Repository identity

- `master` is a fast-forward-only mirror of `libretro/vice-libretro`.
- `emulatorjs` is a fast-forward-only mirror of `EmulatorJS/vice-libretro`.
- `retrom/g1b4309f4d56d` is the only active Retrom maintenance baseline and the
  repository default branch. Retrom patches and release tags originate there.
- `retrom-fork.json` fixes the EmulatorJS source baseline, the upstream sound
  serialization fix, and the EmulatorJS RetroArch linker used for Web builds.

## Branches and releases

- Use only short-lived `fix/*`, `feat/*`, `build/*`, or `sync/upstream-*`
  branches, created from the active `retrom/*` branch.
- Keep downstream patches small and attributable to their upstream source.
- Release tags are annotated and match
  `retrom-core-g1b4309f4d56d-rN`, optionally followed by `-rc.N`.
- Never move a tag, overwrite a release asset, or publish aliases such as
  `latest`, `stable`, or `current`.
- `.github/rpg-runtime/build-candidate.sh` is the only PFB build entry. It must
  build the current worktree and emit only the declared release assets plus
  `retrom-core-candidate.json`.

Before publishing, build the native `xvic` core, build the Web candidate, and
verify checkpoint restoration through a fresh Retrom launch. Do not publish
ROMs, BIOS files, credentials, or host-specific code.
