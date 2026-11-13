"""Check pptx_steps/code_blocks.py: a code block's lines, its indentation, its fit (#178).

    python3 -m pytest tests/test_code_blocks.py

pandoc writes an unhighlighted code block as one paragraph with raw line feeds in its run's text
(LibreOffice draws a paragraph a line, double-spaced); normalize() parts its lines with a:br and
keeps each line's leading spaces as no-break spaces; a highlighted block (its lines already a:br,
its indent a run of its own) keeps its indent the same way. A paragraph of inline code alone is not
a code block. fit() sets a block wider than its box smaller until its longest line fits, to the half
point, and no smaller than the table type, warned of past it. grid.py's split_br() leaves a code
block one paragraph. Needs pandoc ($QUARTO_PANDOC).
"""

import os
import subprocess
import sys

import pytest

from conftest import ENGINE, ROOT, pandoc_exe

NCAR = ROOT / "liveries" / "ncar"
TREE = "decks/\n├── quickstart/\n│   └── Makefile\n└── sample/\n    └── sample.qmd"
MD = ("## Tree\n\n```\n" + TREE + "\n```\n\n"
      "## Highlighted\n\n```python\ndef f():\n    return 1\n```\n\n"
      "## Wide\n\n```\n" + "x" * 90 + "\nshort\n```\n\n"
      "## Too wide\n\n```\n" + "y" * 300 + "\n```\n\n"
      "## Inline\n\n`make pptx`\n")
STEPS = ("import sys\nfrom pathlib import Path\nfrom pptx import Presentation\nfrom pptx_steps import code_blocks\n"
         "p = Path(sys.argv[1]); prs = Presentation(p)\n{calls}\nprs.save(p)\n")


def steps(pptx, calls):
    env = {**os.environ, "LIVERY_DIR": str(NCAR), "PYTHONPATH": str(ENGINE)}
    r = subprocess.run([sys.executable, "-c", STEPS.format(calls=calls), str(pptx)], env=env, cwd=pptx.parent,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("code")
    out = tmp / "c.pptx"
    subprocess.run([pandoc_exe(), "--reference-doc", str(NCAR / "template.pptx"), "-o", str(out)], input=MD, text=True,
                   cwd=tmp, check=True, capture_output=True)
    r = steps(out, "code_blocks.normalize(prs, p); code_blocks.fit(prs, p)")
    from pptx import Presentation
    return Presentation(str(out)), r.stdout, r.stderr


def code_para(slide):
    from pptx.oxml.ns import qn
    return next(p for p in slide._element.iter(qn("a:p")) if p.find(".//" + qn("a:latin")) is not None)


def lines(p):
    """The paragraph's lines (its text between a:br)."""
    from pptx.oxml.ns import qn
    out = [""]
    for el in p:
        if el.tag == qn("a:br"):
            out.append("")
        elif el.tag == qn("a:r"):
            out[-1] += el.findtext(qn("a:t")) or ""
    return out


def test_premise_line_feeds(tmp_path):
    """pandoc still writes an unhighlighted block's lines as raw line feeds in one run's text: when
    it writes a:br, normalize()'s splitting has nothing left to do."""
    out = tmp_path / "p.pptx"
    subprocess.run([pandoc_exe(), "-o", str(out)], input="## T\n\n```\na\n  b\n```\n", text=True, check=True, cwd=tmp_path)
    import zipfile
    xml = zipfile.ZipFile(out).read("ppt/slides/slide1.xml").decode()
    assert "<a:t>a\n  b</a:t>" in xml, "pandoc no longer writes raw line feeds"


def test_tree_lines_and_indent(deck):
    """The tree: one paragraph, a line a break, leading spaces no-break spaces."""
    prs, _, _ = deck
    p = code_para(prs.slides[0])
    assert lines(p) == [line.replace("    ", " " * 4) for line in TREE.split("\n")], lines(p)
    assert "\n" not in "".join(lines(p)), "a line feed left"


def test_highlighted_indent(deck):
    """A highlighted block's indent (a run of spaces of its own) kept the same way."""
    prs, _, _ = deck
    assert lines(code_para(prs.slides[1])) == ["def f():", " " * 4 + "return 1"], lines(code_para(prs.slides[1]))


def test_fit(deck):
    """A 90-character line set smaller to fit its box (half points, under the body); a 300-character
    one held at the table type and warned of; a narrow block and inline code untouched."""
    from pptx.oxml.ns import qn
    import livery
    prs, out, err = deck
    sizes = lambda s: {r.get("sz") for r in code_para(prs.slides[s]).iter(qn("a:rPr"))}
    wide, too_wide = sizes(2), sizes(3)
    assert len(wide) == 1 and None not in wide, wide
    pt = int(next(iter(wide))) / 100
    assert pt * 2 == int(pt * 2) and pt < livery.type_pt(livery.load(NCAR), "body"), pt
    assert pt > livery.type_pt(livery.load(NCAR), "table"), "the 90-column block went to the floor"
    assert too_wide == {str(round(livery.type_pt(livery.load(NCAR), "table") * 100))}, too_wide
    assert "slide 'Too wide': a code block's longest line is wider than its box" in err, err
    assert sizes(0) == {None}, "a narrow block resized"
    assert sizes(4) == {None}, "inline code resized"


def test_split_br_keeps_code(deck, tmp_path):
    """grid.py's split_br() leaves a code block one paragraph (its lines a block's, no spacing)."""
    prs, _, _ = deck
    path = tmp_path / "s.pptx"
    prs.save(str(path))
    r = steps(path, "from pptx_steps.common import split_br\n"
                    "body = prs.slides[0].shapes.placeholders[1].text_frame._txBody\n"
                    "n = len(body.findall('{http://schemas.openxmlformats.org/drawingml/2006/main}p'))\n"
                    "split_br(body)\n"
                    "print(n, len(body.findall('{http://schemas.openxmlformats.org/drawingml/2006/main}p')))")
    before, after = r.stdout.split()
    assert before == after, "split_br cut the code block"
