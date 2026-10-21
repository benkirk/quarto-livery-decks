"""Check the marking strip (livery.yml marking:): its box from the build, and pptx_steps/marking.py.

    python3 -m pytest tests/test_marking.py

The build places the strip by its edge, offset, width and alignment. The pptx step draws it on
every slide with the deck's `marking:` (pandoc records the string in docProps/custom.xml), else
the livery's default text, and none for `marking: none` or a livery without a default. The step
runs in a subprocess, under the livery its LIVERY_DIR names. Needs pandoc ($QUARTO_PANDOC).
"""

import os
import subprocess
import sys

import pytest

import livery_build as lb

from conftest import ROOT

ENGINE = ROOT / "_extensions" / "engine"
DEMO = "This presentation contains no sensitive information"
STEP = """
import sys
from pptx import Presentation
from pptx_steps import marking
prs = Presentation(sys.argv[1]); marking.run(prs, "t.pptx"); prs.save(sys.argv[1])
"""


def test_box():
    out = {"geometry": {"margin": 0.05}}
    assert lb.marking({}, out)["box"] == [0.1, 0.004, 0.8, 0.03], "the default: top, centered, 0.8 wide"
    m = lb.marking({"edge": "bottom", "align": "left", "width": 0.5, "height": 0.04, "offset": 0.01}, out)
    assert m["box"] == [0.05, 0.95, 0.5, 0.04], "bottom-left at the margin"
    assert lb.marking({"align": "right", "width": 0.5}, out)["box"][0] == 0.45
    assert lb.marking({"fill": "primary"}, out)["text-role"] == "primary-text", "text over a fill"


def strips(pandoc_deck, tmp, name, front):
    """The marking texts on each slide of a two-slide deck after the step, under the livery name."""
    md = (f"---\n{front}---\n\n" if front else "") + "## a\n\nOne.\n\n## b\n\nTwo.\n"
    pandoc_deck(tmp, md, "t.pptx")
    env = {**os.environ, "LIVERY_DIR": str(ROOT / "liveries" / name), "PYTHONPATH": str(ENGINE)}
    subprocess.run([sys.executable, "-c", STEP, str(tmp / "t.pptx")], env=env, check=True, capture_output=True)
    from pptx import Presentation
    prs = Presentation(str(tmp / "t.pptx"))
    return [[sh.text_frame.text for sh in s.shapes if sh.name == "Marking"] for s in prs.slides]


@pytest.mark.parametrize("name, front, want", [
    ("nasa-jsc-eg", "", DEMO),                       # the livery's default
    ("nasa-jsc-eg", "marking: CUI\n", "CUI"),        # the deck's own
    ("nasa-jsc-eg", "marking: none\n", None),        # turned off
    ("ncar", "", None),                              # no default, no strip
    ("ncar", "marking: CUI//SP-EXPT\n", "CUI//SP-EXPT"),
])
def test_pptx_step(pandoc_deck, tmp_path, name, front, want):   # not `livery`: conftest's per-livery argument
    got = strips(pandoc_deck, tmp_path, name, front)
    if want is None:
        assert got == [[], []], f"a strip where none belongs: {got}"
    else:
        assert all(len(s) == 1 and s[0].startswith(want) for s in got), f"not {want!r} on every slide: {got}"
