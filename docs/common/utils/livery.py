#!/usr/bin/env python3
"""The engine's livery reader (build/livery.json), for the post-render scripts.

    import livery as livery_mod     load, color, scheme, derived, mix, font_file, mark, files
    livery.py deps <livery dir>     the files a deck build reads from the livery (Make.common)
    livery.py mono <livery dir>     the code face's family (typography.monospace), or nothing

The reader lives in the vendored engine (_extensions/benkirk/engine/livery.py, beside the
template builder); this loads it by path, since both files are named livery. `deps` prints
build/livery.{json,sty,css,theme}, the template and every file the data names (the parent's
too), joined to the directory as given; nothing when build/livery.json is missing."""

import importlib.util
import os
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent / "_extensions" / "benkirk" / "engine"


def engine_module(name: str):
    """A module of the vendored engine, loaded by path (engine_<name>, so it shadows nothing here)."""
    spec = importlib.util.spec_from_file_location(f"engine_{name}", ENGINE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_reader = engine_module("livery")
globals().update({k: v for k, v in vars(_reader).items() if not k.startswith("__")})


def deps(d: str) -> list[str]:
    if not (Path(d) / "build" / "livery.json").exists():
        return []
    lv = _reader.load(d)
    rel = [f"build/livery.{x}" for x in ("json", "sty", "css", "theme")] + [p for p, _ in _reader.files(lv)]
    return sorted({os.path.normpath(Path(d) / p) for p in rel if (Path(d) / p).exists()})


def mono(d: str) -> str:
    """typography.monospace's family when the livery bundles its files (the engine's mono_font())."""
    if not (Path(d) / "build" / "livery.json").exists():
        return ""
    return engine_module("livery_build").mono_font(_reader.load(d))[0]


if __name__ == "__main__":
    if sys.argv[1:2] not in (["deps"], ["mono"]) or len(sys.argv) != 3:
        sys.exit("usage: livery.py deps|mono <livery dir>")
    print(" ".join(deps(sys.argv[2])) if sys.argv[1] == "deps" else mono(sys.argv[2]))
