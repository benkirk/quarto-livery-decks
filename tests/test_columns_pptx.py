"""Check columns-pptx.lua: a slide of more than two columns warns, naming it; two do not.

    python3 -m pytest tests/test_columns_pptx.py

pandoc's pptx writer keeps the first two `.column`s and drops the rest, silently; the filter
says so at render time. The premise is checked too: if pandoc ever writes the third column,
the warning (and this test) can go. Needs pandoc ($QUARTO_PANDOC).
"""

import os
import shutil
import subprocess
import zipfile

import pytest

from conftest import ROOT

FILTER = ROOT / "_extensions" / "engine" / "columns-pptx.lua"
COL = "::: {{.column}}\n{}\n:::\n"
MD = ("## Three\n\n:::: {.columns}\n" + "".join(COL.format(w) for w in ("AAA", "BBB", "CCC")) + "::::\n\n"
      "## Two\n\n:::: {.columns}\n" + "".join(COL.format(w) for w in ("DDD", "EEE")) + "::::\n")


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not pandoc:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")
    out = tmp_path_factory.mktemp("cols") / "t.pptx"
    r = subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=MD, text=True,
                       capture_output=True, check=True)
    with zipfile.ZipFile(out) as z:
        text = b"".join(z.read(n) for n in z.namelist() if n.startswith("ppt/slides/slide"))
    return r.stderr, text


def test_warns_for_three(rendered):
    err, _ = rendered
    assert 'slide "Three" has 3 columns' in err, f"no warning for the three-column slide: {err!r}"
    assert '"Two"' not in err, "a warning for a two-column slide"


def test_pandoc_still_drops_the_third(rendered):
    _, text = rendered
    assert b"AAA" in text and b"BBB" in text, "pandoc lost a column it keeps"
    assert b"CCC" not in text, "pandoc now writes a third column: the warning may go"
