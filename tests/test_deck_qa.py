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
