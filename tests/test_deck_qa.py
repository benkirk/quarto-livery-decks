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


def test_a_bottom_right_frame_number_is_furniture(deck_qa, monkeypatch):
    """The frame number in the bottom right (cu, nsi, the NASA liveries; the pptx as LibreOffice
    draws it puts it past the text's margin) is no text past the right margin, and the footline
    beside it is no footer overrun (the pptx's linked-image URL, a caption's height, at the middle);
    a body word past the margin, or one that meets the number, still is."""
    monkeypatch.setattr(deck_qa, "EDGE", 0.94)
    monkeypatch.setattr(deck_qa, "WIDE_EDGE", 0.97)
    monkeypatch.setattr(deck_qa, "STRIPS", [])
    monkeypatch.setattr(deck_qa, "WATERMARK", "")
    number = (352, 190, 358, 196, "7")
    body = (30, 40, 120, 48, "Body")
    assert deck_qa.pdf_problems(W, H, [body, number], []) == []
    past = (330, 60, 356, 68, "beyond")
    assert deck_qa.pdf_problems(W, H, [body, number, past], []) == [("past the right margin", repr("beyond"))]
    url = (160, 186, 200, 196, "ncar.ucar.edu/")
    assert deck_qa.pdf_problems(W, H, [body, number, url], []) == []
    meets = (300, 186, 349, 196, "running-into-it")
    assert deck_qa.pdf_problems(W, H, [body, number, meets], []) == [("into the footer", repr("running-into-it"))]


def test_lines_under_a_table_are_not_cells(deck_qa):
    """A paragraph under the table at its first column's edge, wider than that column (a list's
    lead-in, single-body.lua's list under a table): unscoped it reads as a merged cell; the table's
    box with its top and bottom (MEASURE_JS's tableBox) leaves it out, and the table's own overrun
    is still found."""
    under = row(110, (120, 236, "A line under the table, across its columns"))
    box = (*SPAN, 66 / H, 101 / H)   # the header's top to the last row's foot
    page = lines(HEADER, *ROWS, under)
    assert deck_qa.table_overruns(page, W, H) != [], "the premise: unscoped, the line reads as a cell"
    assert deck_qa.table_overruns(page, W, H, box) == []
    rows = list(ROWS)
    rows[2] = row(96, (120, 180, "Gust-with-a-long-name HPC"), (228, 240, "128"))
    out = deck_qa.table_overruns(lines(HEADER, *rows, under), W, H, box)
    assert out == [("runs into the next table column", repr("Gust-with-a-long-name HPC"))], "the last row's overrun still found"


def test_a_lone_symbol_is_the_fallback_faces(deck_qa, monkeypatch):
    """A word that is one symbol (⚠︎ with its variation selector, ⚠, ✓) is drawn from a face the
    livery's lacks (the image's LibreOffice: Noto Color Emoji), so its box is the fallback's: no
    overlap with its neighbor (the sample's caution title and a card's status bullet, the boxes CI's
    LibreOffice gave, scaled to the page); a letter in the same box still overlaps."""
    monkeypatch.setattr(deck_qa, "EDGE", 0.94)
    monkeypatch.setattr(deck_qa, "WIDE_EDGE", 0.97)
    monkeypatch.setattr(deck_qa, "STRIPS", [])
    monkeypatch.setattr(deck_qa, "WATERMARK", "")
    k = W / 720   # CI's page is 720 pt wide
    title = [(43.2 * k, 25.0 * k, 93.0 * k, 48.5 * k, "⚠︎"), (72.4 * k, 20.9 * k, 87.1 * k, 56.1 * k, "A")]
    assert deck_qa.pdf_problems(W, H, title, []) == []
    letter = [(43.2 * k, 25.0 * k, 93.0 * k, 48.5 * k, "W")] + title[1:]
    assert deck_qa.pdf_problems(W, H, letter, []) == [("overlapping text", "'W'/'A'")]
    bullet = [(489.5 * k, 236.8 * k, 504.5 * k, 271.8 * k, "⚠"), (504.5 * k, 251.5 * k, 528.5 * k, 272.7 * k, "Two")]
    assert deck_qa.pdf_problems(W, H, bullet, []) == []
    tick = [(52.8 * k, 295.6 * k, 62.8 * k, 309.6 * k, "✓"), (52.8 * k, 295.0 * k, 67.7 * k, 329.9 * k, "⚠")]
    assert deck_qa.pdf_problems(W, H, tick, []) == []


def test_a_big_lines_spill_is_not_a_collision(deck_qa, monkeypatch):
    """A card's big number (a 53 pt font box, Poppins' 1.4 em) reaches 13 pt into the next line's
    21 pt box as LibreOffice leads it: no overlap, since 13 is under SPILL of 53; the same reach
    into a box of its own size is one (a word set inside another's line)."""
    monkeypatch.setattr(deck_qa, "EDGE", 0.94)
    monkeypatch.setattr(deck_qa, "WIDE_EDGE", 0.97)
    monkeypatch.setattr(deck_qa, "STRIPS", [])
    monkeypatch.setattr(deck_qa, "WATERMARK", "")
    k = W / 720
    big = (271.2 * k, 211.6 * k, 337.9 * k, 264.5 * k, "$5M")
    nxt = (284.7 * k, 251.5 * k, 327.4 * k, 272.7 * k, "Shared")
    assert deck_qa.pdf_problems(W, H, [big, nxt], []) == []
    inside = (284.7 * k, 240.0 * k, 327.4 * k, 262.0 * k, "Shared")   # 22 of its 22 pt inside the big box
    assert deck_qa.pdf_problems(W, H, [big, inside], []) == [("overlapping text", "'$5M'/'Shared'")]
    body, foot = (30, 100, 120, 114, "Body"), (30, 107, 90, 117, "footnote")   # a footnote half over a body line
    assert deck_qa.pdf_problems(W, H, [body, foot], []) == [("overlapping text", "'Body'/'footnote'")]


def test_a_full_caption_reaches_its_box(deck_qa, monkeypatch):
    """A {.full} slide's caption spans the slide less geometry.full.pad a side (HTML's box, the
    pptx's): a centered caption past the content margin but inside its box is no overrun (#178); a
    word past the box still is, and a content slide keeps the content margin."""
    monkeypatch.setattr(deck_qa, "EDGE", 0.94)
    monkeypatch.setattr(deck_qa, "WIDE_EDGE", 0.97)
    monkeypatch.setattr(deck_qa, "FULL_EDGE", 0.975)
    monkeypatch.setattr(deck_qa, "STRIPS", [])
    monkeypatch.setattr(deck_qa, "WATERMARK", "")
    caption = (20, 180, 348, 186, "a-caption-as-wide-as-its-box")   # to 0.961 of the width
    full, content = {"cls": "full", "kind": "pptx"}, {"cls": "", "kind": "pptx"}
    assert deck_qa.pdf_problems(W, H, [caption], [], full) == []
    assert deck_qa.pdf_problems(W, H, [caption], [], content) == [("past the right margin", repr(caption[4]))]
    past = (20, 180, 356, 186, "past-the-box")   # 0.983
    assert deck_qa.pdf_problems(W, H, [past], [], full) == [("past the right margin", repr(past[4]))]


def test_a_paragraph_over_a_table_is_no_cell(deck_qa):
    """A paragraph's last line just over the table, at its first column's edge and inside the box's
    padding (SPAN_VPAD), is above every other column's first line: no cell (#178); a header cell
    that overruns, level with the other headers, still is."""
    over = row(60, (120, 236, "A paragraph's last line, over the table"))
    box = (*SPAN, 66 / H, 101 / H)
    assert deck_qa.table_overruns(lines(over, HEADER, *ROWS), W, H, box) == []
    header = row(70, (120, 170, "RESOURCE-AND-TYPE"), (190, 240, "CORES PER NODE"))
    out = deck_qa.table_overruns(lines(over, header, *ROWS), W, H, box)
    assert out == [("runs into the next table column", repr("RESOURCE-AND-TYPE"))], out


def test_pptx_splits_name_the_slide(deck_qa, tmp_path):
    """pptx_splits(): a slide pandoc split (text after a picture: an untitled continuation) named with
    the title before it, in the deck's order; a {.full} slide's missing title (its master hidden) is
    none. pandoc's own writer, no filter: the split it makes."""
    import shutil
    import subprocess
    import zipfile
    from conftest import pandoc_exe
    shutil.copy(ROOT / "decks" / "quickstart" / "screenshots" / "hero.png", tmp_path / "p.png")
    md = "## First\n\nx\n\n## Split\n\n![](p.png)\n\nText after the picture.\n\n## Last\n\ny\n"
    subprocess.run([pandoc_exe(), "-o", str(tmp_path / "d.pptx")], input=md, text=True, cwd=tmp_path, check=True)
    assert deck_qa.pptx_splits(str(tmp_path / "d")) == [(3, "Split")]
    with zipfile.ZipFile(tmp_path / "d.pptx") as z:   # the continuation with its master hidden: a full slide's look
        parts = {n: z.read(n) for n in z.namelist()}
    parts["ppt/slides/slide3.xml"] = parts["ppt/slides/slide3.xml"].replace(b"<p:sld ", b'<p:sld showMasterSp="0" ', 1)
    with zipfile.ZipFile(tmp_path / "f.pptx", "w") as z:
        for n, data in parts.items():
            z.writestr(n, data)
    assert deck_qa.pptx_splits(str(tmp_path / "f")) == []


def test_ink_under_the_body(deck_qa, monkeypatch, tmp_path):
    """ink_below(): a page whose picture runs past the body's foot inks the band under it (#178); a
    clean page, a page with its furniture in the corners (left out) and a marking strip at the foot
    (left out) do not; a dark slide reads against the dark role."""
    from PIL import Image, ImageDraw
    monkeypatch.setattr(deck_qa, "BODY_BOTTOM", 0.9)
    monkeypatch.setattr(deck_qa, "INKS", {"background": (255, 255, 255), "dark": (0, 30, 60)})
    monkeypatch.setattr(deck_qa, "STRIPS", [])

    def page(name, fill=(255, 255, 255), draw=None):
        im = Image.new("RGB", (400, 225), fill)
        if draw:
            draw(ImageDraw.Draw(im))
        im.save(tmp_path / name)
        return str(tmp_path / name)
    clean = page("clean.png", draw=lambda d: d.rectangle((60, 40, 340, 180), fill=(200, 80, 40)))
    corner = page("corner.png", draw=lambda d: d.rectangle((380, 205, 398, 223), fill=(0, 0, 0)))
    over = page("over.png", draw=lambda d: d.rectangle((60, 40, 340, 224), fill=(200, 80, 40)))
    assert deck_qa.ink_below(clean) == 0 and deck_qa.ink_below(corner) == 0
    assert deck_qa.ink_below(over) > deck_qa.INK_SHARE
    monkeypatch.setattr(deck_qa, "STRIPS", [(0, 0.9, 1, 0.1)])
    assert deck_qa.ink_below(over) == 0, "a marking strip's box counted"
    monkeypatch.setattr(deck_qa, "STRIPS", [])
    monkeypatch.setattr(deck_qa, "MARKS", [(0.03, 0.9, 0.84, 0.1)])   # a corner mark reaching far in (nasa-jsc-eg's bar)
    assert deck_qa.ink_below(over) == 0, "a corner mark's box counted"
    monkeypatch.setattr(deck_qa, "MARKS", [])
    dark = page("dark.png", fill=(0, 30, 60))
    assert deck_qa.ink_below(dark, dark=True) == 0 and deck_qa.ink_below(dark) > deck_qa.INK_SHARE

    # a livery whose content art fills the paper (cu's photo): the band reads against the art, pixel by
    # pixel, so every clean content page passes and a picture over the art still fails; a light
    # livery's dark slide has no art (the dark role's paper), a dark livery's keeps it
    art = Image.new("RGB", (800, 450), (255, 255, 255))
    ImageDraw.Draw(art).rectangle((0, 300, 800, 450), fill=(120, 120, 120))   # a mountain at the foot
    art.save(tmp_path / "art.png")
    on_art = page("on-art.png", draw=lambda d: (d.rectangle((0, 150, 400, 225), fill=(120, 120, 120)),
                                                d.rectangle((60, 40, 340, 180), fill=(200, 80, 40))))
    over_art = page("over-art.png", draw=lambda d: (d.rectangle((0, 150, 400, 225), fill=(120, 120, 120)),
                                                    d.rectangle((60, 40, 340, 224), fill=(200, 80, 40))))
    assert deck_qa.ink_below(on_art) > deck_qa.INK_SHARE, "the premise: against the background the art reads as ink"
    monkeypatch.setattr(deck_qa, "ART", str(tmp_path / "art.png"))
    assert deck_qa.ink_below(on_art) == 0, "the content art read as ink"
    assert deck_qa.ink_below(over_art) > deck_qa.INK_SHARE, "a picture over the art missed"
    assert deck_qa.ink_below(dark, dark=True) == 0, "a light livery's dark slide read against the art"
    monkeypatch.setattr(deck_qa, "DARK_MODE", True)
    assert deck_qa.ink_below(on_art, dark=True) == 0, "a dark livery's .brand-dark (a no-op) lost its art"
