"""Check `::: {.lead scale="S"}` (#142): engine-common.lua's scale_attr() reads the attribute once
for every format (a number, taken off the div; one that is not a number warned and dropped), and in
pptx grid-pptx.lua carries it on the lead's marker and grid.py sets the lead's runs at S times the
body size, the box taller for it; a lead without one keeps its runs inheriting. The HTML's
font-size and beamer's enginescale are one-line wrappers of the same reader, read by eye on the
sample deck ("Options side by side", at 1.15). Needs pandoc ($QUARTO_PANDOC).

    python3 -m pytest tests/test_lead_scale.py
"""

import subprocess
import zipfile

import pytest

from conftest import ENGINE, ROOT, flat, lua_common, pandoc_exe, run_steps

NCAR = ROOT / "liveries" / "ncar"
HARNESS = """
local doc = pandoc.read(io.read("a"))
for _, d in ipairs(doc.blocks) do
  if d.t == "Div" then
    local s, had = C.scale_attr(d, "test: a .lead")
    print(tostring(s) .. " " .. tostring(had) .. " " .. tostring(d.attributes["scale"]))
  end
end
"""
DIVS = '::: {.lead scale="1.25"}\nA\n:::\n\n::: {.lead scale="big"}\nB\n:::\n\n::: {.lead}\nC\n:::\n'
MD = ('## Scaled\n\n::: {.lead scale="1.25"}\n**Head**\nline\n:::\n\n'
      '## Plain\n\n::: {.lead}\n**Head**\nline\n:::\n')


def test_scale_attr_reads_once(tmp_path):
    out, warnings = lua_common(tmp_path, HARNESS, DIVS)
    assert out.splitlines() == ["1.25 true nil", "nil true nil", "nil false nil"], out
    assert warnings == ['test: a .lead: scale="big" is not a number; ignored'], warnings


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("lead-scale")
    out = tmp / "t.pptx"
    subprocess.run([pandoc_exe(), "--lua-filter", str(ENGINE / "grid-pptx.lua"), "--reference-doc", str(NCAR / "template.pptx"),
                    "-o", str(out)], input=MD, text=True, cwd=tmp, check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        marked = z.read("ppt/slides/slide1.xml").decode()
    run_steps(out, ["slide_layout", "columns", "grid"], NCAR)
    from pptx import Presentation
    return marked, Presentation(str(out))


def lead_text(slide):
    return next(sh for sh in flat(slide.shapes) if sh.name == "Lead text")


def test_marker_carries_scale(deck):
    marked, _ = deck
    assert "⟦engine:lead scale=1.25⟧" in marked, marked[:400]


def test_lead_runs_scaled(deck):
    """ncar's body is 12 pt: the scaled lead's runs are 15 pt, the plain lead's inherit (no size);
    the scaled box is taller; no marker left."""
    _, prs = deck
    scaled, plain = lead_text(prs.slides[0]), lead_text(prs.slides[1])
    assert {r.font.size.pt for p in scaled.text_frame.paragraphs for r in p.runs} == {15.0}
    assert {r.font.size for p in plain.text_frame.paragraphs for r in p.runs} == {None}
    assert scaled.height > plain.height, (scaled.height, plain.height)
    assert "⟦" not in prs.slides[0]._element.xml, "a marker left"
