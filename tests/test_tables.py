"""Check a pptx table's columns and the note under it (pptx_steps/style_tables.py, #178).

    python3 -m pytest tests/test_tables.py

style_tables re-splits pandoc's equal columns by their longest cells and then holds every column at
least as wide as its widest word (in the face, size, capitals and tracking its cells show), the
columns pandoc took from the source's dash runs too, a short cell ("41.2 %") on one line where a
wrapping column can give the room; words wider than the table together warn. Its settle() runs
before slide_layout (prepare()), so a ::: note under a table is placed by the table as drawn: a
column the re-split narrows wraps the last row, and the note measured against the equal columns
overlapped it. single-body.lua folds the note (a `quarto` shim under plain pandoc), the driver runs
every step under ncar's LIVERY_DIR. Needs pandoc ($QUARTO_PANDOC).
"""

import os
import subprocess
import sys

import pytest

from conftest import ENGINE, ROOT, pandoc_exe, run_steps

NCAR = ROOT / "liveries" / "ncar"
SHIM = ('quarto = {{ doc = {{ is_format = function(f) return f == "pptx" end }},\n'
        '           utils = {{ resolve_path = function(p) return "{engine}/" .. p end }},\n'
        '           log = {{ warning = function(s) io.stderr:write("WARNING: " .. s .. "\\n") end }},\n'
        '           json = {{ decode = pandoc.json.decode }} }}\n'
        'dofile("{engine}/single-body.lua")\n')
LONG = "a long cell " * 8
MD = ("## Wrapped\n\n| Key | Value |\n|---|---|\n| " + LONG + " | short |\n"
      "| k | a value of some length that wraps when narrower |\n\n"
      "::: note\nThe note under the table.\n:::\n\n"
      "## Dashes\n\n| Group | Share | Of the allocation, by group and year, as the panel set it |\n|-|-|----|\n"
      "| COMMUNITY | 41.2 % | Allocated through the community panel for the year |\n"
      "| UNIVERSITY | 30.5 % | Allocated to university researchers for the year |\n\n"
      "## Crowded\n\n| " + " | ".join(f"Supercalifragilistic{i}" for i in range(9)) + " |\n|"
      + "---|" * 9 + "\n| " + " | ".join("x" for _ in range(9)) + " |\n")


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("tables")
    shim = tmp / "single-body-shim.lua"
    shim.write_text(SHIM.format(engine=ENGINE))
    out = tmp / "t.pptx"
    subprocess.run([pandoc_exe(), "--lua-filter", str(shim), "--reference-doc", str(NCAR / "template.pptx"), "-o", str(out)],
                   input=MD, text=True, cwd=tmp, check=True, capture_output=True)
    r = run_steps(out, None, NCAR)
    return out, r.stderr


def measured(out, script):
    """script run on the deck under ncar's livery (the steps' modules import it as they load)."""
    env = {**os.environ, "LIVERY_DIR": str(NCAR), "PYTHONPATH": str(ENGINE)}
    head = ("import sys, json\nfrom pptx import Presentation\nfrom pptx.oxml.ns import qn\n"
            "from pptx_steps.measure import table_height, other_size\nfrom pptx_steps.style_tables import floors\n"
            "prs = Presentation(sys.argv[1])\n")
    r = subprocess.run([sys.executable, "-c", head + script, str(out)], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.split()


def test_note_under_the_drawn_table(deck):
    """The note sits under the table as drawn (its re-split columns, its header in capitals)."""
    out, _ = deck
    top, bottom = measured(out, "s = prs.slides[0]\n"
                                "t = next(sh for sh in s.shapes if sh.has_table)\n"
                                "n = next(sh for sh in s.shapes if sh.name == 'Note')\n"
                                "print(n.top, t.top + table_height(t, s))\n")
    assert int(top) >= int(bottom), "the note overlaps the table's last row"


def test_no_column_under_its_widest_word(deck):
    """Columns pandoc took from short dash runs are raised to their widest words, a short cell's
    column to its whole text; no warning for a table that fits."""
    out, err = deck
    widths, least, whole = (list(map(int, x.split(","))) for x in measured(out,
        "s = prs.slides[1]\nt = next(sh for sh in s.shapes if sh.has_table).table._tbl\n"
        "w = [int(c.get('w')) for c in t.findall(qn('a:tblGrid') + '/' + qn('a:gridCol'))]\n"
        "least, whole = floors(t, other_size(s))\n"
        "print(','.join(map(str, w)), ','.join(map(str, least)), ','.join(map(str, whole)))\n"))
    assert all(w >= f - 2 for w, f in zip(widths, least)), (widths, least)
    assert widths[1] >= whole[1] - 2, "the short cell's column under its whole text"
    assert "'Dashes'" not in err and "'Wrapped'" not in err, err


def test_crowded_table_warns(deck):
    """Nine columns of long words: wider together than the table, warned of, naming the slide."""
    _, err = deck
    assert "slide 'Crowded': a table's longest words are wider than its columns together" in err, err


def test_settled_narrow_then_widened(deck):
    """A table settled in a narrow frame (a lead's Content with Caption: its floors pass that width,
    so its columns go by their floors) and widened after is re-split from pandoc's widths at its new
    width, as if settled there: it kept the narrow frame's shares (#179, the Derecho deck's "The
    formula": its code headers took the width, its long column wrapped every row)."""
    out, _ = deck
    narrow_then_wide, wide = measured(out,
        "import copy\nfrom pptx_steps.style_tables import settle, rebalance\n"
        "s = prs.slides[1]\nt = next(sh for sh in s.shapes if sh.has_table).table._tbl\n"
        "grid = lambda x: x.findall(qn('a:tblGrid') + '/' + qn('a:gridCol'))\n"
        "fresh = copy.deepcopy(t)\nsettle(fresh, other_size(s))\n"
        "for c in grid(t): c.set('w', str(int(c.get('w')) * 3 // 10))\n"
        "settle(t, other_size(s))\n"
        "total = sum(int(c.get('w')) for c in grid(fresh))\nnow = sum(int(c.get('w')) for c in grid(t))\n"
        "for c in grid(t): c.set('w', str(round(int(c.get('w')) * total / now)))\n"
        "rebalance(t, other_size(s))\n"
        "print(','.join(c.get('w') for c in grid(t)), ','.join(c.get('w') for c in grid(fresh)))\n")
    a, b = (list(map(int, x.split(","))) for x in (narrow_then_wide, wide))
    assert all(abs(x - y) <= len(a) for x, y in zip(a, b)), (a, b)


def test_header_measured_as_drawn(tmp_path):
    """table_height() before style_tables measures the header in the capitals and tracking it will
    be drawn in: a header that wraps only in capitals made the table taller than measured, and a †
    line placed under it was drawn over the last row (#179, the Derecho deck's "Why no factor
    reaches 0.5")."""
    head = " | ".join(["abcdefgh ijk"] * 8)   # one line in lower case at the table size, two in its header capitals (ncar)
    md = "## T\n\n| " + head + " |\n|" + "---|" * 8 + "\n| " + " | ".join(["x"] * 8) + " |\n"
    out = tmp_path / "h.pptx"
    subprocess.run([pandoc_exe(), "--reference-doc", str(NCAR / "template.pptx"), "-o", str(out)], input=md, text=True,
                   cwd=tmp_path, check=True, capture_output=True)
    before, after = measured(out, "from pptx_steps import style_tables\nfrom pptx_steps.common import palette\n"
                                  "s = prs.slides[0]\nt = next(sh for sh in s.shapes if sh.has_table)\nb = table_height(t, s)\n"
                                  "style_tables.style_table(t.table._tbl, other_size(s), palette(s))\n"
                                  "print(b, table_height(t, s))\n")
    assert int(before) >= int(after), (before, after)


def test_rows_measured_at_the_faces_line(tmp_path):
    """A table's rows measure at the face's own line height (Poppins 1.4 em, ncar's), not the 1.2 the
    text estimates take: LibreOffice in the image drew the rows that tall, and a † line placed under
    a measure of 1.2 sat on the last row (#179). A stand-in face (cu's Heros for Helvetica Neue) keeps
    1.2: its metrics are not the face's."""
    md = "## T\n\n| a |\n|---|\n" + "".join(f"| r{k} |\n" for k in range(6))
    out = tmp_path / "r.pptx"
    subprocess.run([pandoc_exe(), "--reference-doc", str(NCAR / "template.pptx"), "-o", str(out)], input=md, text=True,
                   cwd=tmp_path, check=True, capture_output=True)
    h, line, size = measured(out, "from pptx_steps.measure import face_line, BODY\nfrom pptx_steps.common import CELL_MAR\n"
                                  "s = prs.slides[0]\nt = next(sh for sh in s.shapes if sh.has_table)\n"
                                  "print(table_height(t, s), face_line(BODY), other_size(s))\n")
    assert float(line) >= 1.4, line
    assert int(h) >= 7 * int(size) * 127 * 1.4, (h, size)   # sz in hundredths of a point; 12700 EMU a point
