"""Check the pptx and QA fixes a real talk asked for (#172): a hyperlink on a field slide, {.vcenter}
on a grid slide, one text size along a rail, a hyphenated word's wrap, a code block that scrolls in
HTML, and the one-slide picture's finder.

    python3 -m pytest tests/test_talk_fixes.py

The pptx is pandoc's, through slide-layout.lua and grid-pptx.lua, then the whole driver
(pptx_post.py), as a deck's build runs them. Needs pandoc ($QUARTO_PANDOC).
"""

import importlib.util
import json
import subprocess
import sys

import pytest
from pptx import Presentation
from pptx.oxml.ns import qn

from conftest import ENGINE, ROOT, flat, pandoc_exe, run_steps, slide_layout_shim

RAIL = """::: {.timeline}
- **2024** A short one
- **2025** NCAR-beamer-template-with-a-very-long-hyphenated-repository-name merges in here
- **2026** Movies
:::
"""

DECK = f"""## Plain

A [link](https://example.org) on a content slide.

## Dark {{.brand-dark}}

A [link](https://example.org) on the dark field, beside plain text.

## Top

- One bullet

{RAIL}
## Centered {{.vcenter}}

- One bullet

{RAIL}
## Thank you! {{.closing}}

[example.org/decks](https://example.org/decks)
"""


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    d = ROOT / "liveries" / "ncar"
    tmp = tmp_path_factory.mktemp("talk")
    out = tmp / "t.pptx"
    subprocess.run([pandoc_exe(), "--slide-level", "2", "--lua-filter", str(slide_layout_shim(tmp)),
                    "--lua-filter", str(ENGINE / "grid-pptx.lua"), "--reference-doc", str(d / "template.pptx"), "-o", str(out)],
                   input=f"---\nlivery: {d}\n---\n\n" + DECK, text=True, cwd=tmp, check=True, capture_output=True)
    run_steps(out, None, d)
    return json.loads((d / "build" / "livery.json").read_text()), Presentation(str(out))


def linked(slide):
    """(run's a:rPr, its a:hlinkClick) for each linked run of the slide."""
    return [(r.find(qn("a:rPr")), r.find(qn("a:rPr")).find(qn("a:hlinkClick"))) for r in slide._element.iter(qn("a:r"))
            if r.find(qn("a:rPr")) is not None and r.find(qn("a:rPr")).find(qn("a:hlinkClick")) is not None]


def test_a_link_on_a_field_takes_its_text_color(deck):
    """A closing slide's link and a dark slide's are in the field's text color, marked for PowerPoint
    to draw in the run's color (hlinkClr val="tx"); a content slide's is left to the theme."""
    j, prs = deck
    plain, dark, closing = prs.slides[0], prs.slides[1], prs.slides[4]
    (rpr, link), = linked(plain)
    assert rpr.find(qn("a:solidFill")) is None and len(link) == 0, "a content slide's link is the theme's"
    for slide, role in ((dark, "on-dark"), (closing, j["compositions"]["closing"]["column"]["role"])):
        (rpr, link), = linked(slide)
        assert rpr.find(qn("a:solidFill"))[0].get("val").upper() == j["roles"][role][1:].upper(), role
        clr = link.find(".//{http://schemas.microsoft.com/office/drawing/2018/hyperlinkcolor}hlinkClr")
        assert clr is not None and clr.get("val") == "tx"
        assert link.find(qn("a:extLst"))[0].get("uri") == "{A12FA001-AC4F-418D-AE19-62706E023703}"


def _group(slide, name):
    return next(sh for sh in slide.shapes if sh.name == name)


def test_vcenter_centers_a_grid_slide(deck):
    """The same flow on two slides: {.vcenter} moves it down by half the room it leaves, the bullet
    and the rail together, and it ends as far from the body's foot as it starts from its top."""
    j, prs = deck
    top, mid = prs.slides[2], prs.slides[3]
    H = prs.slide_height
    body_top, foot = round(j["geometry"]["body"][1] * H), round(j["geometry"]["body-bottom"] * H)
    a, b = _group(top, "Timeline"), _group(mid, "Timeline")
    shift = b.top - a.top
    assert shift > 0.1 * H, "the centered rail sits lower"
    first = lambda s: min(sh.top for sh in s.shapes if sh.has_text_frame and "One bullet" in sh.text_frame.text)
    assert first(mid) - first(top) == shift, "the text above the rail moved with it"
    assert abs((first(mid) - body_top) - (foot - (b.top + b.height))) < 0.06 * H, "centered between the body's top and its foot"


def test_a_rail_keeps_one_size(deck):
    """No rail text box shrinks on overflow (PowerPoint stepped one long item down alone), the boxes
    are one height, and it holds the long item's lines: its hyphenated name wraps at the hyphens."""
    _, prs = deck
    texts = [sh for sh in flat(prs.slides[2].shapes) if sh.name.startswith("Milestone") and sh.name.endswith("text")]
    assert len(texts) == 3 and len({sh.height for sh in texts}) == 1
    for sh in texts:
        bp = sh.text_frame._txBody.find(qn("a:bodyPr"))
        assert bp.find(qn("a:normAutofit")) is None and bp.find(qn("a:noAutofit")) is not None, sh.name
    sizes = {r.get("sz") for sh in texts for r in sh._element.iter(qn("a:rPr"))}
    assert len(sizes) <= 2, f"one size for the dates' line and one for the text: {sizes}"
    line = 1.2 * 12 * 12700   # a body line on ncar (12 pt)
    assert texts[0].height > 4 * line, "the row is as tall as the long item's wrapped lines"


def test_wrap_breaks_at_hyphens():
    """measure._wrap(): a hyphenated word wraps at its hyphens, a word wider than the line runs on,
    and ordinary words wrap as before."""
    code = ("from pptx_steps import measure\n"
            "class F:\n    def getlength(self, t): return 10 * len(t)\n"
            "f = F()\n"
            "print(measure._wrap([('one-two-three-four', f)], 60), measure._wrap([('aaaa bbbb cccc', f)], 100),\n"
            "      measure._wrap([('abcdefghijklmnopqrst', f)], 80), measure._wrap([('a -5 --flag x-', f)], 1000))\n")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       env={**__import__("os").environ, "LIVERY_DIR": str(ROOT / "liveries" / "ncar"), "PYTHONPATH": str(ENGINE)})
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == ["4", "2", "3", "1"], r.stdout


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "common" / "utils" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / "common" / "utils"))
    spec.loader.exec_module(mod)
    return mod


def test_a_code_block_that_scrolls_fails():
    qa = _load("deck_qa")
    slide = dict(level2=True, title="Code", cls="slide level2", kind="code", use=0.9, fit=1, scale=1,
                 overRight=False, codeClip=0.74)
    fails, _ = qa.html_findings([slide])
    assert len(fails) == 1 and fails[0].startswith('s1 "Code": a code block is taller than its box: 74% of it shows'), fails
    assert qa.html_findings([{**slide, "codeClip": 1}])[0] == []
    assert qa.html_findings([{**slide, "cls": "slide level2 scrollable"}])[0] == [], "{.scrollable} says it is meant"


def test_slide_shot_finds_by_title():
    shot = _load("slide_shot")
    titles = ["Deck", "Write Markdown", "Columns: a  list\nbeside a table", "Thank you!"]
    assert shot.find(titles, "") == 0 and shot.find(titles, "Columns: a list") == 2 and shot.find(titles, "Nope") is None
    assert shot.find([], "") is None
    assert shot.slug("Columns: a list beside a table") == "columns-a-list-beside-a-table" and shot.slug("") == "title"
