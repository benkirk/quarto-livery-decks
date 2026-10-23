"""Check how the dividers are counted: engine-common.lua's sections() and divider_subtitle(), and
the pptx dividers' numbers (pptx_steps/section_subtitle.py).

    python3 -m pytest tests/test_section_subtitle.py

The reader (under `pandoc lua` with a `quarto` shim, conftest's lua_common) lists every `#`
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

from conftest import ENGINE, ROOT, lua_common, run

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
local doc = pandoc.read(io.read("a"), "markdown")
local out = {}
for _, s in ipairs(C.sections(doc.blocks, 2)) do
  table.insert(out, { number = s.number or pandoc.json.null, title = pandoc.utils.stringify(s.title),
                      sub = s.sub and pandoc.utils.stringify(s.sub) or pandoc.json.null, unnumbered = s.unnumbered, at = s.at })
end
io.write(pandoc.json.encode(out))
"""


def test_sections_read(tmp_path):
    md = (BODY.replace("# Backup", "# Backup {.unnumbered}")
          + "\n# Not a subtitle\n\nA paragraph.\n\n- then a list\n\n## D\n\nw\n")
    out, _ = lua_common(tmp_path, READER, md)
    got = [(s["number"], s["title"], s["sub"], s["unnumbered"]) for s in json.loads(out)]
    assert got == [(1, "One", None, False), (None, "Backup", "Its subtitle.", True), (2, "Two", None, False),
                   (3, "Not a subtitle", None, False)]


AGENDA_READER = r"""
local doc = pandoc.read(io.read("a"), "markdown")
local secs = C.sections(doc.blocks, 2)
local out = {}
for _, cur in ipairs({ 0, 2 }) do
  for _, r in ipairs(C.agenda_rows(secs, cur)) do
    table.insert(out, { cur = cur, number = r.number, title = pandoc.utils.stringify(r.title),
                        sub = r.sub and pandoc.utils.stringify(r.sub) or pandoc.json.null, state = r.state })
  end
end
io.write(pandoc.json.encode(out))
"""


def test_agenda_rows(tmp_path):
    """agenda_rows(): the numbered sections only (the Backup left out), each with its subtitle; up
    front (0) all next; from section 2, 1 done, 2 current, 3 next."""
    md = BODY.replace("# Backup", "# Backup {.unnumbered}") + "\n# Three\n\nIts own subtitle.\n\n## D\n\nw\n"
    out, _ = lua_common(tmp_path, AGENDA_READER, md)
    got = [(x["cur"], x["number"], x["title"], x["sub"], x["state"]) for x in json.loads(out)]
    assert got == [(0, 1, "One", None, "next"), (0, 2, "Two", None, "next"), (0, 3, "Three", "Its own subtitle.", "next"),
                   (2, 1, "One", None, "done"), (2, 2, "Two", None, "current"), (2, 3, "Three", "Its own subtitle.", "next")], got


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


@pytest.fixture(scope="module")
def progress(tmp_path_factory):
    """decks/fixtures/photo.qmd (one numbered divider, then the unnumbered Backup) rendered in every
    format under a tmp flavor of ncar with section.progress (as test_cover_field.py renders)."""
    tmp = tmp_path_factory.mktemp("progress")
    liv = tmp / "liveries"
    shutil.copytree(ROOT / "liveries" / "ncar", liv / "ncar", ignore=shutil.ignore_patterns("reference"))
    d = liv / "progress"; d.mkdir()
    (d / "_brand.yml").write_text("{}\n")
    (d / "livery.yml").write_text("schema: 1\nname: progress\nextends: ncar\nsection: {progress: true}\n")
    assert run("build", d).returncode == 0
    assert run("template", d).returncode == 0   # the pptx's template, the livery's own
    deck = tmp / "deck"; deck.mkdir()
    src = ROOT / "decks" / "fixtures"
    for f in ("photo.qmd", "_body.qmd"):
        shutil.copy(src / f, deck / f)
    shutil.copytree(src / "images", deck / "images")
    (deck / "Makefile").write_text(f"DECKS := photo\ninclude {ROOT / 'Make.common'}\n")
    env = {k: v for k, v in os.environ.items() if k not in ("LIVERY", "LIVERY_DIR")}
    r = subprocess.run(["make", "-C", str(deck), "all", f"LIVERY_DIR={d}"], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    return deck


def test_progress_pptx(progress):
    labels = [label for _t, label, _y in dividers(progress / "photo.pptx")]
    assert labels == ["Section 1 of 1", None], labels


def test_progress_pdf(progress):
    texts = [subprocess.run(["pdftotext", "-f", str(k), "-l", str(k), str(progress / "photo.pdf"), "-"],
                            capture_output=True, text=True).stdout for k in range(1, 10)]
    divs = [" ".join(t.split()) for t in texts if "A divider" in t.split("\n")[0:3] or "Backup" in t.split("\n")[0:3]]
    assert any(t.startswith("SECTION 1 OF 1 A divider") for t in divs), divs
    assert any(t.startswith("Backup") for t in divs), divs


def test_progress_html(progress):
    html = (progress / "photo.html").read_text()
    head = re.search(r'<section[^>]*engine-section[^>]*>\s*<h1>A divider', html)
    assert head and 'data-engine-section="1"' in head.group(0) and 'data-engine-section-total="1"' in head.group(0), head
    backup = re.search(r'<section[^>]*>\s*<h1>Backup', html)
    assert backup and "data-engine-section" not in backup.group(0), backup.group(0)
