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
