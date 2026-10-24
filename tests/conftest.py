"""The engine's tests' shared harness (`make test`; `python3 -m pytest -q tests`).

pytest.ini puts _extensions/engine on the path, so a test imports the engine's tools by name
(`import livery_build`, `from pptx_steps import svg_fallback`) as the tools import each other.
Here: ROOT and ENGINE; `livery`, a test argument that runs the test once per bundled livery, named
by it; `run`, the livery command as a subprocess; `pandoc_exe`, pandoc's path; `lua_common`,
engine-common.lua's functions on markdown under `pandoc lua` with a `quarto` shim; `pandoc_deck`,
a pptx pandoc writes from markdown, as its zip parts; `tmp_livery`, a bundled livery copied with one
top-level block replaced and built; `flat`, a slide's shapes with the ones in groups. The rules that keep the
suite parallel (`-n auto --dist loadfile`): a test writes only under tmp_path or tmp_path_factory,
never the tree; no os.chdir or os.environ mutation in-process (a subprocess gets its own env=);
expensive setup is a module-scoped fixture, and loadfile keeps a file's tests on one worker.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "_extensions" / "engine"
LIVERIES = sorted(p.parent for p in (ROOT / "liveries").glob("*/livery.yml"))
LIVERY_PY = ENGINE / "livery.py"

# what a harness run under `pandoc lua` needs of Quarto: its log (each warning a line on stderr,
# which lua_common returns) and its json; C the engine-common.lua module (arg[1])
LUA_SHIM = r"""
quarto = { log = { warning = function(s) io.stderr:write("WARNING: " .. s .. "\n") end }, json = { decode = pandoc.json.decode } }
local C = dofile(arg[1])
"""


def pytest_generate_tests(metafunc):
    if "livery" in metafunc.fixturenames:
        metafunc.parametrize("livery", LIVERIES, ids=[d.name for d in LIVERIES])


def run(*args, **kw):
    """The livery command on args, captured."""
    return subprocess.run([sys.executable, str(LIVERY_PY), *map(str, args)], capture_output=True, text=True, **kw)


def pandoc_exe():
    """pandoc's path ($QUARTO_PANDOC, else the one on PATH); the test fails without one."""
    exe = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not exe:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")
    return exe


def lua_common(tmp_path, body, md, *args):
    """engine-common.lua's functions on md: body a Lua script run after LUA_SHIM under `pandoc lua`
    (C the module, args its arg[2] on), md on its stdin. (its stdout, the warnings it logged)."""
    script = tmp_path / "harness.lua"
    script.write_text(LUA_SHIM + body)
    r = subprocess.run([pandoc_exe(), "lua", str(script), str(ENGINE / "engine-common.lua"), *args],
                       input=md, text=True, capture_output=True, check=True)
    return r.stdout, [w[len("WARNING: "):] for w in r.stderr.splitlines() if w.startswith("WARNING: ")]


def flat(shapes):
    """Every shape, the ones in groups too (a card, a lead, a strip is a group of its shapes)."""
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:   # a group
            yield from flat(sh.shapes)


@pytest.fixture(scope="session")
def pandoc_deck():
    """render(tmp, md, name, *args): the pptx pandoc writes from md (its images relative to tmp; args
    pandoc's own options), as its zip parts."""
    pandoc = pandoc_exe()

    def render(tmp: Path, md: str, name: str, *args: str) -> dict[str, bytes]:
        out = tmp / name
        subprocess.run([pandoc, *args, "-o", str(out)], input=md, text=True, cwd=tmp, check=True)
        with zipfile.ZipFile(out) as z:
            return {i.filename: z.read(i.filename) for i in z.infolist()}

    return render


@pytest.fixture(scope="session")
def tmp_livery():
    """make(tmp, block, name="ncar", key="boxes"): the livery copied into tmp/liveries/<name> with a
    top-level key: block (its indented lines) in place of its own, built: (return code, stderr,
    livery.json or None)."""
    def make(tmp: Path, block: str, name: str = "ncar", key: str = "boxes"):
        d = tmp / "liveries" / name
        shutil.copytree(ROOT / "liveries" / name, d, ignore=shutil.ignore_patterns("build", "*.pptx", "reference"))
        y = d / "livery.yml"
        text = re.sub(rf"\n{key}:.*?\n\n", "\n", y.read_text(), flags=re.S)   # the livery's own block out
        y.write_text(text.replace("\npptx:", f"\n{key}:\n{block}\npptx:", 1))
        r = run("build", d)
        j = json.loads((d / "build" / "livery.json").read_text()) if r.returncode == 0 else None
        return r.returncode, r.stderr, j

    return make
