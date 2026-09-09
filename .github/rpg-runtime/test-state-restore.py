#!/usr/bin/env python3
"""Restore a later VIC/TED clock in a fresh process; no external game inputs."""
import ctypes as c
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


class Variable(c.Structure):
    _fields_ = [("key", c.c_char_p), ("value", c.c_char_p)]


class Game(c.Structure):
    _fields_ = [("path", c.c_char_p), ("data", c.c_void_p), ("size", c.c_size_t), ("meta", c.c_char_p)]


def run_phase(phase, root, library):
    core = c.CDLL(str(library))
    variables = {}
    directory = str(root).encode()
    observed = {"frames": 0, "samples": 0}

    @c.CFUNCTYPE(None, c.c_int, c.c_char_p)
    def log(_level, _format):
        # The libretro callback is variadic; unused trailing arguments are ignored.
        pass

    @c.CFUNCTYPE(c.c_bool, c.c_uint, c.c_void_p)
    def environment(command, data):
        if command in (9, 31):
            c.cast(data, c.POINTER(c.c_char_p))[0] = directory
            return True
        if command == 27:
            c.cast(data, c.POINTER(c.c_void_p))[0] = c.cast(log, c.c_void_p).value
            return True
        if command == 16:
            entries = c.cast(data, c.POINTER(Variable))
            index = 0
            while entries[index].key:
                variables[entries[index].key] = entries[index].value.split(b"; ", 1)[-1].split(b"|")[0]
                index += 1
            return True
        if command == 15:
            variable = c.cast(data, c.POINTER(Variable)).contents
            if variable.key in variables:
                variable.value = variables[variable.key]
                return True
        if command == 17:
            c.cast(data, c.POINTER(c.c_bool))[0] = False
            return True
        if command == 52:
            c.cast(data, c.POINTER(c.c_uint))[0] = 0
            return True
        if command == 47:
            c.cast(data, c.POINTER(c.c_int))[0] = 3
            return True
        return command in (10, 11, 18, 35)

    @c.CFUNCTYPE(None, c.c_void_p, c.c_uint, c.c_uint, c.c_size_t)
    def video(_data, _width, _height, _pitch):
        observed["frames"] += 1

    @c.CFUNCTYPE(None, c.c_int16, c.c_int16)
    def sample(_left, _right):
        observed["samples"] += 1

    @c.CFUNCTYPE(c.c_size_t, c.c_void_p, c.c_size_t)
    def audio(_data, frames):
        observed["samples"] += frames
        return frames

    @c.CFUNCTYPE(None)
    def poll():
        pass

    @c.CFUNCTYPE(c.c_int16, c.c_uint, c.c_uint, c.c_uint, c.c_uint)
    def input_state(_port, _device, _index, _button):
        return 0

    for name, callback in [("environment", environment), ("video_refresh", video),
                           ("audio_sample", sample), ("audio_sample_batch", audio),
                           ("input_poll", poll), ("input_state", input_state)]:
        getattr(core, "retro_set_" + name)(callback)
    core.retro_load_game.argtypes = [c.POINTER(Game)]
    core.retro_load_game.restype = c.c_bool
    core.retro_serialize_size.restype = c.c_size_t
    for name in ("retro_serialize", "retro_unserialize"):
        getattr(core, name).argtypes = [c.c_void_p, c.c_size_t]
        getattr(core, name).restype = c.c_bool
    core.retro_init()
    game = Game(str(root / "loop.prg").encode(), None, 0, None)
    assert core.retro_load_game(c.byref(game)), "load failed"
    for _ in range(400 if phase == "save" else 2):
        core.retro_run()
    if phase == "save":
        size = core.retro_serialize_size()
        assert 0 < size < 16 * 1024 * 1024, "invalid state size"
        state = c.create_string_buffer(size)
        assert core.retro_serialize(state, size), "serialization failed"
        (root / "state").write_bytes(state.raw)
    else:
        data = (root / "state").read_bytes()
        state = c.create_string_buffer(data)
        # First jump forward from a fresh process, then backward within this one.
        for _ in range(2):
            before = dict(observed)
            assert core.retro_unserialize(state, len(data)), "restore failed"
            for _ in range(10):
                core.retro_run()
            assert observed["frames"] > before["frames"], "video did not resume"
            assert observed["samples"] > before["samples"], "audio did not resume"
    core.retro_unload_game()
    core.retro_deinit()


def main():
    if len(sys.argv) == 4:
        run_phase(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]))
        return
    if len(sys.argv) != 2:
        raise SystemExit("usage: test-state-restore.py <native xvic or xplus4 library>")
    library = Path(sys.argv[1]).resolve(strict=True)
    with TemporaryDirectory(prefix="retrom-xvic-state-") as directory:
        root = Path(directory)
        # Project-owned VIC BASIC: load address $1001, line 10 GOTO 10, terminator.
        (root / "loop.prg").write_bytes(bytes.fromhex("01100a100a00893130000000"))
        for phase in ("save", "load"):
            subprocess.run([sys.executable, __file__, phase, str(root), str(library)], check=True, timeout=15)
    print("VICE fresh-process and backward restore: video/audio resumed")


if __name__ == "__main__":
    main()
