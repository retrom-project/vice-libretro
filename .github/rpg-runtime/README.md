# Retrom EmulatorJS VIC-20 build

`build-candidate.sh <absolute-empty-directory>` builds the patched `xvic` core
with Emscripten 3.1.74, links it through the EmulatorJS RetroArch revision fixed
in `retrom-fork.json`, and emits an EmulatorJS 4.2.3-compatible
`vice_xvic-wasm.data` archive.

The archive contains the JavaScript/Wasm pair plus the fixed core/build
manifests and license. Formal releases additionally publish `COPYING` and
`rpg-runtime-release.json`. ROMs and BIOS files are never build inputs.

The build snapshots the Git-tracked and non-ignored working files, excluding native
outputs and Python caches. It rejects source changes during compilation and fixes
the emsdk image digest and linker commit. Candidate metadata records the source
commit, branch, dirty status, tree digest, and every emitted asset hash. Archive
member timestamps are omitted. Release CI checks annotated tags against the fixed
maintenance baseline, runs native gates, and publishes RC tags as prereleases.

The upstream sound guard prevents backward clock deltas. Retrom also reopens the
VIC-20 sound device after a successful restore: loading a later snapshot into a
fresh instance otherwise leaves sample leftovers behind the restored CPU clock
and can hang the next frame in `vic_sound_clock`. This is a downstream fix,
separate from the attributed upstream backport.

Run `python3 .github/rpg-runtime/test-state-restore.py ./vice_xvic_libretro.so`
after the native build. It generates a project-owned BASIC loop in a temporary
directory, saves in one process, restores in another, then tests a backward
restore. Both video and audio must resume within the hard process timeout.

Formal releases use `build-release.sh <absolute-empty-directory> <tag>` to build
VIC-20, PET and Plus/4. PET/Plus4 each have a dedicated `<core>-release.json`
and `<core>-source.tar.gz`; their metadata covers the core, COPYING and source.
The existing VIC-20 metadata filename and asset contract remain compatible.
