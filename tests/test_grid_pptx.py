"""Check grid-pptx.lua: a two-column slide's shares on a notes line, a third column warned about.

    python3 -m pytest tests/test_grid_pptx.py

A two-column slide keeps the Two Content layout (pandoc's placeholders idx 1 and 2) and its notes
carry `engine-columns: <share> <share>` (engine-common.lua's column_shares(): width= or an equal
share of what is left), with `wide` when slide-layout.lua's line says so. pandoc's pptx writer keeps
the first two `.column`s and drops the rest, silently; the filter says so at render time. The
premise is checked too: if pandoc ever writes the third column, the warning (and this test) can
go. Needs pandoc ($QUARTO_PANDOC).
"""

import os
import re
import shutil
import subprocess
import zipfile

import pytest

from conftest import ROOT

FILTER = ROOT / "_extensions" / "engine" / "grid-pptx.lua"
COL = "::: {{.column{}}}\n{}\n:::\n"
NOTES = "::: notes\nengine-layout: wide\n:::\n"   # slide-layout.lua's line, as it writes it
MD = ("## Three\n\n:::: {.columns}\n" + "".join(COL.format("", w) for w in ("AAA", "BBB", "CCC")) + "::::\n\n"
      "## Two\n\n:::: {.columns}\n" + COL.format(' width="55%"', "DDD") + COL.format("", "EEE") + "::::\n\n"
      "## Wide\n\n:::: {.columns}\n" + COL.format("", "FFF") + COL.format("", "GGG") + "::::\n\n" + NOTES)


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not pandoc:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")
    out = tmp_path_factory.mktemp("cols") / "t.pptx"
    r = subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=MD, text=True,
                       capture_output=True, check=True)
    with zipfile.ZipFile(out) as z:
        slides = {n: z.read(n).decode() for n in z.namelist() if re.match(r"ppt/(slides|notesSlides)/(_rels/)?\w+\d+\.xml(\.rels)?$", n)}
    return r.stderr, slides


def text(slides, part):
    return "".join(re.findall(r"<a:t>([^<]*)</a:t>", slides[part]))


def notes(slides, n):
    """Slide n's notes text, through its relationship to its notes slide."""
    m = re.search(r'Target="\.\./notesSlides/(notesSlide\d+\.xml)"', slides[f"ppt/slides/_rels/slide{n}.xml.rels"])
    return text(slides, f"ppt/notesSlides/{m.group(1)}") if m else ""


def test_warns_for_three(rendered):
    err, _ = rendered
    assert 'slide "Three" has 3 columns' in err, f"no warning for the three-column slide: {err!r}"
    assert '"Two"' not in err, "a warning for a two-column slide"


def test_pandoc_still_drops_the_third(rendered):
    _, slides = rendered
    body = "".join(text(slides, n) for n in slides if "/slides/" in n)
    assert "AAA" in body and "BBB" in body, "pandoc lost a column it keeps"
    assert "CCC" not in body, "pandoc now writes a third column: the warning may go"


def test_two_columns_marked(rendered):
    _, slides = rendered
    two = slides["ppt/slides/slide2.xml"]
    assert 'idx="1"' in two and 'idx="2"' in two, "the 55/45 slide is not on Two Content's placeholders"
    assert "DDD" in text(slides, "ppt/slides/slide2.xml"), "the body is not its columns"
    assert "engine-columns: 0.55 0.45" in notes(slides, 2), "no shares line"
    assert "engine-columns: 0.5 0.5 wide" in notes(slides, 3), "no wide on the shares line"
    assert "engine-columns" not in notes(slides, 1), "a shares line on a three-column slide"
    assert not any("engine-columns" in text(slides, n) for n in slides if re.match(r"ppt/slides/slide", n)), "the line in a body"
