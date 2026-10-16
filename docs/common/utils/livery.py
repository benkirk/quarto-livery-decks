"""Read a livery's resolved truth, build/livery.json, for the post-render scripts.

The directory comes from the argument, else $LIVERY_DIR (exported by Make.common), else a
`_livery` link in the current directory. Generate the file with livery_build.py."""

import json
import os
from pathlib import Path


def livery_dir(path: str | os.PathLike | None = None) -> Path:
    for candidate in (path, os.environ.get("LIVERY_DIR"), "_livery"):
        if candidate and Path(candidate).is_dir():
            return Path(candidate).resolve()
    raise FileNotFoundError("no livery: pass a directory, export LIVERY_DIR, or run where _livery links")


def load(path: str | os.PathLike | None = None) -> dict:
    d = livery_dir(path)
    f = d / "build" / "livery.json"
    if not f.exists():
        raise FileNotFoundError(f"{f} missing: run livery_build.py {d}")
    data = json.loads(f.read_text())
    data["dir"] = str(d)
    return data


def color(livery: dict, role: str) -> str:
    """A role's hex without '#', as the pptx scripts write it."""
    return livery["roles"][role].lstrip("#").upper()
