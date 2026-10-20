"""The engine's tests' shared harness (`make test`; `python3 -m pytest -q tests`).

pytest.ini puts _extensions/engine on the path, so a test imports the engine's tools by name
(`import livery_build`, `from pptx_steps import svg_fallback`) as the tools import each other.
Here: ROOT; `livery`, a test argument that runs the test once per bundled livery, named by it;
`run`, the livery command as a subprocess; `pandoc_deck`, a pptx pandoc writes from markdown, as
its zip parts. The rules that keep the suite parallel (`-n auto --dist loadfile`): a test writes
only under tmp_path or tmp_path_factory, never the tree; no os.chdir or os.environ mutation
in-process (a subprocess gets its own env=); expensive setup is a module-scoped fixture, and
loadfile keeps a file's tests on one worker.
"""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LIVERIES = sorted(p.parent for p in (ROOT / "liveries").glob("*/livery.yml"))
LIVERY_PY = ROOT / "_extensions" / "engine" / "livery.py"


def pytest_generate_tests(metafunc):
    if "livery" in metafunc.fixturenames:
        metafunc.parametrize("livery", LIVERIES, ids=[d.name for d in LIVERIES])


def run(*args, **kw):
    """The livery command on args, captured."""
    return subprocess.run([sys.executable, str(LIVERY_PY), *map(str, args)], capture_output=True, text=True, **kw)


@pytest.fixture(scope="session")
def pandoc_deck():
    """render(tmp, md, name): the pptx pandoc writes from md (its images relative to tmp), as its zip parts."""
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not pandoc:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")

    def render(tmp: Path, md: str, name: str) -> dict[str, bytes]:
        out = tmp / name
        subprocess.run([pandoc, "-o", str(out)], input=md, text=True, cwd=tmp, check=True)
        with zipfile.ZipFile(out) as z:
            return {i.filename: z.read(i.filename) for i in z.infolist()}

    return render
