"""Check how the dividers are counted: engine-common.lua's sections() and divider_subtitle(), and
the pptx dividers' numbers (pptx_steps/section_subtitle.py).

    python3 -m pytest tests/test_section_subtitle.py

The reader (under `pandoc lua` with a `quarto` shim, test_footnotes.py's harness) lists every `#`
divider in order, a `.unnumbered` one without a number and outside the count, each with the
paragraphs alone before the next slide as its subtitle (none when anything else follows them).
pandoc's pptx writer drops `.unnumbered`, so grid-pptx.lua writes the dividers outside the count
into the metadata (`engine-unnumbered: 2`, places among the dividers; test_grid_pptx.py checks
that line) and the step numbers only the others: of three dividers with the second named, the
first and third carry the eyebrow "Section 1" and "Section 2", the second none, its title placed
without the eyebrow's room. A deck without the line numbers every divider. The step runs in a
subprocess under ncar's LIVERY_DIR on the zip's parts, as pptx_post.py runs it. Needs pandoc
($QUARTO_PANDOC).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

import pytest

from conftest import ROOT

ENGINE = ROOT / "_extensions" / "engine"
LEVEL = ("--slide-level=2",)   # Quarto's; pandoc alone guesses 1 from a divider with a subtitle
BODY = "# One\n\n## A\n\nx\n\n# Backup\n\nIts subtitle.\n\n## B\n\ny\n\n# Two\n\n## C\n\nz\n"
STEP = """
import sys, zipfile
from pptx_steps import section_subtitle
p = sys.argv[1]
with zipfile.ZipFile(p) as z:
    parts = {i.filename: z.read(i.filename) for i in z.infolist()}
section_subtitle.run(parts, p)
with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
    for n, b in parts.items():
        z.writestr(n, b)
"""


READER = r"""
quarto = { log = { warning = function(s) end } }
local C = dofile(arg[1])
local doc = pandoc.read(io.read("a"), "markdown")
local out = {}
for _, s in ipairs(C.sections(doc.blocks, 2)) do
  table.insert(out, { number = s.number or pandoc.json.null, title = pandoc.utils.stringify(s.title),
                      sub = s.sub and pandoc.utils.stringify(s.sub) or pandoc.json.null, unnumbered = s.unnumbered, at = s.at })
end
io.write(pandoc.json.encode(out))
"""


def test_sections_read(tmp_path):
    exe = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not exe:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")
    script = tmp_path / "reader.lua"
    script.write_text(READER)
    md = (BODY.replace("# Backup", "# Backup {.unnumbered}")
          + "\n# Not a subtitle\n\nA paragraph.\n\n- then a list\n\n## D\n\nw\n")
    r = subprocess.run([exe, "lua", str(script), str(ENGINE / "engine-common.lua")], input=md, text=True,
                       capture_output=True, check=True)
    got = [(s["number"], s["title"], s["sub"], s["unnumbered"]) for s in json.loads(r.stdout)]
    assert got == [(1, "One", None, False), (None, "Backup", "Its subtitle.", True), (2, "Two", None, False),
                   (3, "Not a subtitle", None, False)]


def dividers(path):
    """Each divider slide, in deck order: (its title, its eyebrow's text or None, its title's y)."""
    with zipfile.ZipFile(path) as z:
        pres = z.read("ppt/presentation.xml").decode()
        rels = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(slides/slide\d+\.xml)"',
                               z.read("ppt/_rels/presentation.xml.rels").decode()))
        out = []
        for rid in re.findall(r'<p:sldId [^>]*r:id="(rId\d+)"', pres):
            xml = z.read("ppt/" + rels[rid]).decode()
            lay = z.read("ppt/slides/_rels/" + rels[rid].split("/")[1] + ".rels").decode()
            layout = z.read("ppt/slideLayouts/" + re.search(r'slideLayouts/(slideLayout\d+\.xml)', lay).group(1)).decode()
            if 'name="Section Header"' not in layout:
                continue
            label = re.search(r'name="engine-section-label".*?<a:t>([^<]*)</a:t>', xml, re.S)
            title = re.search(r'<p:sp>(?:(?!</p:sp>).)*?type="title".*?</p:sp>', xml, re.S).group(0)
            out.append(("".join(re.findall(r"<a:t>([^<]*)</a:t>", title)), label.group(1) if label else None,
                        int(re.search(r'<a:off x="\d+" y="(\d+)"', title).group(1))))
        return out


@pytest.fixture(scope="module")
def run_step():
    env = {**os.environ, "LIVERY_DIR": str(ROOT / "liveries" / "ncar"), "PYTHONPATH": str(ENGINE)}

    def run(path):
        subprocess.run([sys.executable, "-c", STEP, str(path)], env=env, check=True, capture_output=True)
        return dividers(path)
    return run


def test_unnumbered_skipped(tmp_path, pandoc_deck, run_step):
    parts = pandoc_deck(tmp_path, '---\nengine-unnumbered: "2"\n---\n\n' + BODY, "t.pptx", *LEVEL)
    assert "engine-unnumbered" in parts["docProps/custom.xml"].decode()
    (one, l1, _), (backup, l2, _), (two, l3, _) = run_step(tmp_path / "t.pptx")
    assert (one, l1) == ("One", "Section 1")
    assert (backup, l2) == ("Backup", None)
    assert (two, l3) == ("Two", "Section 2")


def test_every_divider_numbered_without_the_line(tmp_path, pandoc_deck, run_step):
    pandoc_deck(tmp_path, BODY, "t.pptx", *LEVEL)
    labels = [label for _t, label, _y in run_step(tmp_path / "t.pptx")]
    assert labels == ["Section 1", "Section 2", "Section 3"]


def test_unnumbered_title_takes_the_eyebrows_room(tmp_path, pandoc_deck, run_step):
    """The block is centered without the eyebrow: the unnumbered title sits higher than it would
    under one (the same divider, numbered)."""
    pandoc_deck(tmp_path, '---\nengine-unnumbered: "2"\n---\n\n' + BODY, "a.pptx", *LEVEL)
    pandoc_deck(tmp_path, BODY, "b.pptx", *LEVEL)
    assert run_step(tmp_path / "a.pptx")[1][2] < run_step(tmp_path / "b.pptx")[1][2]
