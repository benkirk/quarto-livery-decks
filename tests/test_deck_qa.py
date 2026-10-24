"""Check deck_qa.py's table check on a PDF page's text lines, as pdftotext gives them.

    python3 -m pytest tests/test_deck_qa.py

table_overruns reports a cell that runs into the next column (pdftotext merges two touching
cells into one line spanning the next column's edge), in any row, the last included; a table's
caption above it and a note under it are wider than its columns but are not cells, and a
right-aligned column of numbers has no edge of its own. The lines are made up, laid out as the
sample's "Tables" page: (x0, y0, x1, y1, text) in points on a 362 x 204 page. html_findings fails a
gallery caption that runs past its cell (MEASURE_JS's galleryCapOver), on a content or a {.full} slide.
"""

import importlib.util

import pytest

from conftest import ROOT

W, H = 362, 204


@pytest.fixture(scope="module")
def deck_qa():
    spec = importlib.util.spec_from_file_location("deck_qa", ROOT / "common" / "utils" / "deck_qa.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def row(y, *cells):
    return [(x0, y, x1, y + 5, text) for x0, x1, text in cells]


HEADER = row(70, (120, 150, "RESOURCE"), (160, 175, "TYPE"), (190, 240, "CORES PER NODE"))
ROWS = [row(80, (120, 145, "Derecho"), (160, 172, "HPC"), (228, 240, "128")),
        row(88, (120, 143, "Casper"), (160, 173, "DAV"), (232, 240, "36")),
        row(96, (120, 138, "Gust"), (160, 172, "HPC"), (228, 240, "128"))]
CAPTION = row(58, (150, 212, "Sample HPC resources"))
NOTE = row(106, (130, 232, "A note under the table, wider than its columns"))


def lines(*rows):
    return [ln for r in rows for ln in r]


def test_caption_and_note_are_not_cells(deck_qa):
    assert deck_qa.table_overruns(lines(CAPTION, HEADER, *ROWS, NOTE), W, H) == []


@pytest.mark.parametrize("at", [1, 2], ids=["a middle row", "the last row"])
def test_a_merged_cell_is_reported(deck_qa, at):
    rows = list(ROWS)
    rows[at] = row(88 + 8 * (at - 1), (120, 180, "Casper-with-a-long-name DAV"), (228, 240, "36"))
    out = deck_qa.table_overruns(lines(CAPTION, HEADER, *rows, NOTE), W, H)
    assert out == [("runs into the next table column", repr("Casper-with-a-long-name DAV"))]


@pytest.mark.parametrize("kind", ["figure", "full"])
def test_a_gallery_caption_past_its_cell_fails(deck_qa, kind):
    slide = dict(level2=True, title="Six views", cls="slide level2", kind=kind, use=0.9, fit=1, scale=1,
                 overRight=False, galleryCapOver=True)
    fails, _ = deck_qa.html_findings([slide])
    assert fails == ['s1 "Six views": a gallery caption runs past its cell; shorten it']
    fails, _ = deck_qa.html_findings([{**slide, "galleryCapOver": False}])
    assert fails == []


def test_pptx_scan_counts_slides_and_finds_markers(deck_qa, tmp_path):
    """pptx_scan: the deck's slide count and the slides whose text still holds a grid marker
    (`⟦engine:…⟧`, which a step left undrawn): the zip's slide parts alone, no python-pptx."""
    import zipfile
    sld = '<p:sld xmlns:p="x" xmlns:a="y"><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>%s</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>'
    with zipfile.ZipFile(tmp_path / "d.pptx", "w") as z:
        z.writestr("ppt/slides/slide1.xml", sld % "Fine.")
        z.writestr("ppt/slides/slide2.xml", sld % "⟦engine:lead⟧The headline⟦engine:end⟧")
        z.writestr("ppt/slides/slide10.xml", sld % "Also fine.")
        z.writestr("ppt/slideLayouts/slideLayout1.xml", sld % "⟦engine:not a slide⟧")
    assert deck_qa.pptx_scan(str(tmp_path / "d")) == (3, [2])
    assert deck_qa.pptx_scan(str(tmp_path / "missing")) == (None, [])


# bullets beside the table (a .columns slide): three lines starting at one x, with wrapped
# continuations hanging at another, each running past that hang: the shape of a bullet list
BULLETS = [row(80, (20, 110, "• The first bullet, long")), row(86, (28, 100, "continued here")),
           row(96, (20, 112, "• The second one, long")), row(102, (28, 98, "and its tail")),
           row(112, (20, 108, "• The third bullet too")), row(118, (28, 104, "wrapping as well"))]
SPAN = (120 / W, 240 / W)   # the table's box in the HTML, as a share of the width


def test_bullets_beside_a_table_are_not_cells(deck_qa):
    """The rule reads only the lines inside the table's span (MEASURE_JS's tableBox): a bullet
    column beside the table, whose hanging lines start at an x of their own, is no table column."""
    page = lines(CAPTION, HEADER, *ROWS, NOTE, *BULLETS)
    assert deck_qa.table_overruns(page, W, H) != [], "the premise: unscoped, the bullets read as columns"
    assert deck_qa.table_overruns(page, W, H, SPAN) == []
    rows = list(ROWS)
    rows[1] = row(88, (120, 180, "Casper-with-a-long-name DAV"), (228, 240, "36"))
    out = deck_qa.table_overruns(lines(CAPTION, HEADER, *rows, NOTE, *BULLETS), W, H, SPAN)
    assert out == [("runs into the next table column", repr("Casper-with-a-long-name DAV"))], "the table's own overrun still found"


def test_indented_sub_rows_are_their_column(deck_qa):
    """A hierarchy table indents its sub-rows a few points right of the first column's edge
    (the fy27 deck's community portions): three of them are no column of their own, so the
    parent rows, which run past that x, are not overruns; a row running into the real next
    column still is."""
    rows = [row(80, (120, 152, "University"), (160, 172, "HPC"), (232, 240, "37")),
            row(88, (127, 160, "Large (CHAP)"), (160, 172, "HPC"), (232, 240, "90")),
            row(96, (127, 158, "Small-scale"), (160, 172, "DAV"), (232, 240, "10")),
            row(104, (120, 140, "NCAR"), (160, 172, "HPC"), (232, 240, "31")),
            row(112, (127, 138, "NSC"), (160, 172, "HPC"), (232, 240, "60")),
            row(120, (127, 140, "Labs"), (160, 172, "HPC"), (232, 240, "30"))]
    note = row(130, (130, 232, "A note under the table, wider than its columns"))
    assert deck_qa.table_overruns(lines(HEADER, *rows, note), W, H) == [], "the note under it is no cell either"
    rows[3] = row(104, (120, 185, "NCAR-with-a-long-name HPC"), (232, 240, "31"))
    assert deck_qa.table_overruns(lines(HEADER, *rows), W, H) == [("runs into the next table column", repr("NCAR-with-a-long-name HPC"))]


def test_the_watermark_is_furniture(deck_qa, monkeypatch):
    """A watermark's word is no text past an edge or overlapping, as a marking strip's is not: pdftotext
    gives the turned word as glyphs or pieces in boxes as tall as its letters, which the checks drop
    (a body word that matches, a line tall, stays); the HTML measurement skips its element."""
    monkeypatch.setattr(deck_qa, "EDGE", 0.94)
    monkeypatch.setattr(deck_qa, "WIDE_EDGE", 0.97)
    monkeypatch.setattr(deck_qa, "STRIPS", [])
    monkeypatch.setattr(deck_qa, "WM_HEIGHT", 0.22)
    words = [(300, 40, 360, 120, "FT"), (250, 60, 300, 140, "A"), (30, 40, 120, 48, "Body"), (340, 150, 365, 158, "A")]
    monkeypatch.setattr(deck_qa, "WATERMARK", "")
    assert ("past the right margin", repr("FT")) in deck_qa.pdf_problems(W, H, words, [])
    monkeypatch.setattr(deck_qa, "WATERMARK", "DRAFT")
    assert deck_qa.pdf_problems(W, H, words, []) == [("past the right margin", repr("A"))], "the body's A, a line tall, stays"
    assert ".engine-watermark" in deck_qa.MEASURE_JS.split("const skip = ")[1].split(";")[0]
