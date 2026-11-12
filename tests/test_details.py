"""Check the details slides (`## Title {.details}`, boxes.details): the tab's numbers from the build,
the one reader (engine-common.lua), the pptx filter and step, LibreOffice's copy, and the frame key.

    python3 -m pytest tests/test_details.py

A details slide is an optional-depth slide in the flow: every format marks it with the same tab (on
the paper's left edge from the body's top, the label turned), and the pptx hides it unless the deck
says `details: show`. The build resolves boxes.details' nulls (details_box()) into every
livery.json, livery.css and livery.sty; engine-common.lua's details_mode(), details_hidden() and
details_slides() read a deck alike for every format; pptx_steps/details.py draws and hides, the
halves of a slide pandoc split included; engine-revealjs.js leaves them out of an HTML show.
Needs pandoc ($QUARTO_PANDOC); the frame key needs XeLaTeX, the HTML show Playwright and Quarto's
reveal.js.
"""

import json
import os
import shutil
import subprocess
import zipfile

import pytest
from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Pt

import livery_build as lb

from conftest import ENGINE, ROOT, flat, lua_common, run_steps, slide_layout_shim
from test_latex import DECK, compile_tex

TAB = "Details tab"


def test_numbers_in_every_livery(livery):
    """The tab's derived numbers: no wider than the title tab or a {.wide} body's margin, its word
    no larger than the eyebrow and inside the tab; in livery.css and livery.sty too."""
    j = json.loads((livery / "build" / "livery.json").read_text())
    d, g, ty = j["boxes"]["details"], j["geometry"], j["type"]
    assert d["label"] == "Details" and d["role"] == "primary-contrast" and d["pad"] == 0.9, d
    assert 0 < d["width"] <= g["tab-width"] and d["width"] < g["wide-margin"], "clear of a {.wide} body"
    assert 0 < d["size"] <= ty["roles"]["eyebrow"]["pt"] and d["size"] * 2 == int(d["size"] * 2), "to the half point"
    assert d["size"] * lb.DETAILS_LINE <= d["width"] * ty["canvas"]["w"] + 1e-6 or d["size"] == ty["roles"]["eyebrow"]["pt"]
    assert d["size"] < d["width"] * ty["canvas"]["w"], "the word's line is inside the tab"
    css, sty = (livery / "build" / "livery.css").read_text(), (livery / "build" / "livery.sty").read_text()
    assert f"--engine-details-width: {round(d['width'] * 1600, 1):g}px;" in css
    assert ".engine-details-tab { --engine-details-fill: var(--engine-primary-contrast); }" in css
    assert "\\def\\engine@boxes@details@label{Details}" in sty and f"\\def\\engine@boxes@details@width{{{d['width']}}}" in sty
    assert f"\\def\\engine@boxes@details@type{{{{{round(d['size'] / ty['roles']['body']['pt'], 4)}}}{{1}}}}" in sty


def test_schema_defaults():
    s = json.loads((ENGINE / "livery.schema.json").read_text())["properties"]["boxes"]["properties"]["details"]["properties"]
    assert {k: v["default"] for k, v in s.items()} == lb.BOXES["details"]


@pytest.mark.parametrize("block, check", [
    ("  details:\n    label: Deep dive\n    role: secondary\n", lambda d, j: (d["label"], d["role"]) == ("Deep dive", "secondary")),
    ("  details:\n    width: 0.01\n    size: 6.2\n", lambda d, j: (d["width"], d["size"]) == (0.01, 6.0)),
])
def test_livery_look(tmp_path, tmp_livery, block, check):
    rc, err, j = tmp_livery(tmp_path, block)
    assert rc == 0, err
    assert check(j["boxes"]["details"], j), j["boxes"]["details"]
    if "Deep dive" in block:
        assert "\\def\\engine@boxes@details@label{Deep dive}" in (tmp_path / "liveries" / "ncar" / "build" / "livery.sty").read_text()


@pytest.mark.parametrize("block, why", [
    ("  details:\n    role: \"#FF0000\"\n", "is a hex, not a role or blend"),
    ("  details:\n    color: primary\n", "boxes.details.color: unknown key"),
    ("  details:\n    width: 0.5\n", "boxes.details.width"),
])
def test_refusals(tmp_path, tmp_livery, block, why):
    rc, err, _ = tmp_livery(tmp_path, block)
    assert rc != 0 and why in err, err


READER = """
local doc = pandoc.read(io.read("a"), "markdown")
local mode = C.details_mode(doc.meta, "test")
local marked = {}
local out, n = C.details_slides(doc.blocks, 2, "test", C.details_hidden(mode, arg[2]), function(h)
  table.insert(marked, pandoc.utils.stringify(h.content))
end)
print(mode, n, table.concat(marked, "|"))
for _, b in ipairs(out) do
  if b.t == "Header" then print("H" .. b.level, pandoc.utils.stringify(b.content), table.concat(b.classes, ","))
  elseif b.t == "Div" then print("NOTES", pandoc.utils.stringify(b)) end
end
"""

DECK_MD = """---
{front}
---

# Part {{.details}}

## Core

Text.

## One {{.details}}

Text.

## Two {{.details .wide}}

Text.

## Again

Text.

# Next

## Three {{.details}}

Text.
"""


@pytest.mark.parametrize("front, fmt, mode, note", [
    ("title: T", "pptx", "auto", "The next 2 slides are details slides (hidden)."),
    ("title: T", "html", "auto", "The next 2 slides are details slides."),
    ("details: show", "pptx", "show", "The next 2 slides are details slides."),
    ("details: hide", "html", "hide", "The next 2 slides are details slides (hidden)."),
    ("details: hide", "pdf", "hide", "The next 2 slides are details slides."),
])
def test_reader(tmp_path, front, fmt, mode, note):
    """The class comes off every details slide, the layout classes stay; a divider's is warned of;
    the slide before a run gets the note (never a divider: "Three" follows one)."""
    out, warns = lua_common(tmp_path, READER, DECK_MD.format(front=front), fmt)
    lines = out.splitlines()
    assert lines[0].split("\t") == [mode, "3", "One|Two|Three"], lines[0]
    assert "H2\tOne\t" in lines and "H2\tTwo\twide" in lines and "H1\tPart\t" in lines, lines
    assert [l for l in lines if l.startswith("NOTES")] == ["NOTES\t" + note], lines
    assert lines.index("NOTES\t" + note) == lines.index("H2\tOne\t") - 1, "at the end of the slide before the run"
    assert warns == ['test: {.details} on the divider "Part" is ignored (it marks a slide)'], warns


def test_reader_refuses_a_mode(tmp_path):
    out, warns = lua_common(tmp_path, READER, DECK_MD.format(front="details: maybe"), "pptx")
    assert out.splitlines()[0].startswith("auto\t") and 'test: details: "maybe" is not show or hide; ignored' in warns


PPTX_MD = """---
title: T
{front}
---

## Core

Text.

## Split {{.details}}

![](pic.png)

```
code after a picture: pandoc splits the slide (after a table too, before pandoc 3.10.1)
```

## Full {{.details .full}}

![](pic.png)

## After

Text.

## Dark {{.details .brand-dark .vcenter}}

Text.
"""


def _deck(tmp_path, pandoc_deck, front, steps, livery="ncar"):
    from PIL import Image
    Image.new("RGB", (160, 90), "navy").save(tmp_path / "pic.png")
    pandoc_deck(tmp_path, PPTX_MD.format(front=front), "t.pptx", "--slide-level", "2",
                "--reference-doc", str(ROOT / "liveries" / livery / "template.pptx"),
                "--lua-filter", str(slide_layout_shim(tmp_path)), "-M", f"livery={ROOT / 'liveries' / livery}")
    run_steps(tmp_path / "t.pptx", steps, ROOT / "liveries" / livery)
    return Presentation(str(tmp_path / "t.pptx"))


def _tabs(slide):
    return [sh for sh in flat(slide.shapes) if sh.name == TAB]


@pytest.mark.parametrize("front, hidden", [("", True), ("details: show", False), ("details: hide", True)])
def test_pptx_tab_and_hidden(tmp_path, pandoc_deck, front, hidden):
    """Each details slide has one tab and is hidden unless the deck shows them: both halves of the
    slide pandoc split (the notes line lands on the second), a full slide (its title gone), a dark
    one; the other slides have neither. The notes line is taken, the layout's left for slide_layout."""
    prs = _deck(tmp_path, pandoc_deck, front, ["details"])
    slides = list(prs.slides)
    assert len(slides) == 7, "the title, Core, Split and its continuation, Full, After, Dark"
    want = [False, False, True, True, True, False, True]
    assert [len(_tabs(s)) for s in slides] == [int(w) for w in want]
    assert [s._element.get("show") == "0" for s in slides] == [w and hidden for w in want]
    notes = [s.notes_slide.notes_text_frame.text if s.has_notes_slide else "" for s in slides]
    assert not any("engine-details" in n for n in notes), notes
    assert "engine-layout: full" in notes[4] and "engine-layout: vcenter dark" in notes[6], notes
    assert ("The next 2 slides are details slides" + (" (hidden)." if hidden else ".")) in notes[1], notes[1]


def test_pptx_tab_geometry(tmp_path, pandoc_deck):
    """The tab as it shows: on the left edge from the body's top, the livery's width, turned to read
    upward; its word in the box's size, bold small capitals in the background, on the role's fill;
    the dark slide's the dark twins. It survives the whole driver (a full slide, a grid)."""
    prs = _deck(tmp_path, pandoc_deck, "", None)
    j = json.loads((ROOT / "liveries" / "ncar" / "build" / "livery.json").read_text())
    d, W, H = j["boxes"]["details"], prs.slide_width, prs.slide_height
    slides = list(prs.slides)
    for i in (2, 3, 4, 6):
        (tab,) = _tabs(slides[i])
        assert tab.rotation == 270
        cx, cy = tab.left + tab.width // 2, tab.top + tab.height // 2   # turned about its center
        left, top, wide, long = cx - tab.height // 2, cy - tab.width // 2, tab.height, tab.width
        assert abs(left) <= 1 and abs(top - round(j["geometry"]["body"][1] * H)) <= 1, (left, top)
        assert abs(wide - round(d["width"] * W)) <= 1 and long > 3 * wide, (wide, long)
        run = tab.text_frame.paragraphs[0].runs[0]
        assert run.text == "Details" and run.font.size == Pt(d["size"]) and run.font.bold
        assert run.font._rPr.get("cap") == "all"
        fits = [e.tag.split("}")[1] for e in tab.text_frame._txBody.find(qn("a:bodyPr"))]
        assert fits == ["noAutofit"], f"never shrunk or grown (common.no_autofit()): {fits}"
        dark = i == 6
        assert str(run.font.color.rgb) == j["roles"]["dark" if dark else "background"][1:].upper()
        assert str(tab.fill.fore_color.rgb) == j["roles"]["secondary" if dark else "primary-contrast"][1:].upper()
    assert slides[4].shapes.title is None, "the full slide lost its title after the tab was placed"
    assert [s._element.get("show") for s in slides] == [None, None, "0", "0", "0", None, "0"]


def test_pptx_tab_follows_the_type_step(tmp_path, pandoc_deck):
    """A deck's type step scales the label (type_step, the last step), so the tab is drawn as long as
    the scaled label and its pads, as HTML and the PDF size theirs: at type-scale 1.4 the label and
    the tab's length are 1.4 times the plain deck's (8 pt to 11 on ncar), its width the livery's."""
    sizes = {}
    for name, front in (("plain", ""), ("big", "type-scale: 1.4"), ("small", "type-body: 9")):
        (tmp_path / name).mkdir()
        (tab,) = _tabs(list(_deck(tmp_path / name, pandoc_deck, front, None).slides)[2])
        sizes[name] = (tab.text_frame.paragraphs[0].runs[0].font.size.pt, tab.width, tab.height)
    (pt, long, wide) = sizes["plain"]
    for name, f in (("big", 1.4), ("small", 9 / 12)):
        want = int(pt * f * 2 + 0.5) / 2   # to the half point
        assert sizes[name][0] == want, sizes
        # (PIL's widths at these small sizes are not quite linear in the size: within 5 %)
        assert abs(sizes[name][1] / long - want / pt) < 0.05, f"the tab is as long as its label at {want} pt: {sizes}"
        assert sizes[name][2] == wide, "its width is the livery's"


def test_step_is_idempotent(tmp_path, pandoc_deck):
    prs = _deck(tmp_path, pandoc_deck, "", ["details", "details"])
    assert [len(_tabs(s)) for s in prs.slides] == [0, 0, 1, 1, 1, 0, 1]


def test_libreoffice_copy_shows_hidden_slides(tmp_path, pandoc_deck):
    """make qa draws the pptx through LibreOffice, whose export leaves hidden slides out: pptx_pdf
    counts them and its copy has every slide shown (the deck itself untouched)."""
    import sys
    sys.path.insert(0, str(ROOT / "common" / "utils"))
    import pptx_pdf
    _deck(tmp_path, pandoc_deck, "", ["details"])
    path = tmp_path / "t.pptx"
    assert pptx_pdf.hidden_slides(path) == 4
    with zipfile.ZipFile(path) as z:
        data = z.read("ppt/slides/slide3.xml")
    assert b'show="0"' in data and b'show="0"' not in pptx_pdf.HIDDEN.sub(rb"\1", data)
    assert pptx_pdf.HIDDEN.sub(rb"\1", data).startswith(data[:40]), "the root's other attributes kept"


FRAMES = r"""\begin{frame}[enginedetails]{A details frame}
Text.
\end{frame}
\begin{frame}{A core frame}
Text.
\end{frame}
\begin{frame}[enginedetails,enginedark]{Dark details}
Text.
\end{frame}
"""


def test_frame_key(tmp_path):
    """[enginedetails]: the tab on the page's left edge by the body's top, in the role's color (ncar's
    primary-contrast, read off the page), its word in the text; none on the frame after it (the key
    is reset); on a dark frame the dark twin (secondary)."""
    if not (shutil.which("xelatex") and shutil.which("latexmk")):
        pytest.skip("xelatex and latexmk")
    from PIL import Image
    tex = DECK.split("\\begin{document}")[0] + "\\begin{document}\n" + FRAMES + "\\end{document}\n"
    r, log = compile_tex(tmp_path, "dt", tex)
    assert r.returncode == 0, log[-2000:]
    assert "Overfull" not in log
    j = json.loads((ROOT / "liveries" / "ncar" / "build" / "livery.json").read_text())
    text = subprocess.run(["pdftotext", "-raw", str(tmp_path / "dt.pdf"), "-"], capture_output=True, text=True).stdout.split("\f")
    assert "DETAILS" in text[0] and "DETAILS" not in text[1] and "DETAILS" in text[2], text
    subprocess.run(["pdftoppm", "-r", "100", "-png", str(tmp_path / "dt.pdf"), str(tmp_path / "pg")], check=True)
    rgb = lambda role: tuple(int(j["roles"][role][k:k + 2], 16) for k in (1, 3, 5))
    for page, want in ((1, rgb("primary-contrast")), (2, rgb("background")), (3, rgb("secondary"))):
        im = Image.open(tmp_path / f"pg-{page}.png").convert("RGB")
        x = round(0.15 * j["boxes"]["details"]["width"] * im.width)   # in the tab, left of its word
        y = round((j["geometry"]["body"][1] + 0.004) * im.height)     # just under the body's top: the pad above the word
        px = im.getpixel((x, y))
        assert all(abs(a - b) <= 6 for a, b in zip(px, want)), (page, px, want)


PAGE = """<!doctype html><html{cls}><head><meta charset="utf-8">
<link rel="stylesheet" href="reveal.css"><script src="engine-revealjs.js"></script></head><body>
<div class="reveal"><div class="slides">
<section><h1>Deck</h1></section>
<section><section><h1>Part</h1></section><section><h2>Core</h2></section>
<section class="engine-details"><h2>Deep</h2></section><section><h2>After</h2></section></section>
<section><section class="engine-details"><h2>Alone</h2></section></section>
<section><h2>End</h2></section>
</div></div>
<script src="reveal.js"></script><script>Reveal.initialize({{hash: true}});</script></body></html>
"""


def test_html_show(tmp_path):
    """engine-revealjs.js on a page laid out as Quarto's (the theme's script in the head, reveal
    started at the end of the body): the deck's `details: hide` (html.engine-details-hide) and
    ?details=hide leave the details slides out, a stack emptied with them; ?details=show brings them
    back; and the address is read against the slides shown (#/1/2 is the stack's third shown slide,
    #/2 the third column: it landed on the title slide)."""
    sync_api = pytest.importorskip("playwright.sync_api")
    share = os.environ.get("QUARTO_SHARE_PATH") or (
        shutil.which("quarto") and os.path.join(os.path.dirname(os.path.realpath(shutil.which("quarto"))), "..", "share", "quarto"))
    dist = share and os.path.join(share, "formats", "revealjs", "reveal", "dist")
    if not (dist and os.path.exists(os.path.join(dist, "reveal.js"))):
        pytest.skip("Quarto's reveal.js")
    import sys
    sys.path.insert(0, str(ROOT / "common" / "utils"))
    from deck_qa import serve
    for f in ("reveal.js", "reveal.css"):
        shutil.copy(os.path.join(dist, f), tmp_path)
    shutil.copy(ENGINE / "engine-revealjs.js", tmp_path)
    (tmp_path / "shown.html").write_text(PAGE.format(cls=""))
    (tmp_path / "hidden.html").write_text(PAGE.format(cls=' class="engine-details-hide"'))
    every, shown = "Deck|Part|Core|Deep|After|Alone|End", "Deck|Part|Core|After|End"
    want = [("shown.html", every, "Deck"), ("shown.html#/1/2", every, "Deep"), ("shown.html?details=hide", shown, "Deck"),
            ("hidden.html", shown, "Deck"), ("hidden.html?details=show", every, "Deck"), ("hidden.html?details", every, "Deck"),
            ("hidden.html#/1/2", shown, "After"), ("hidden.html#/2", shown, "End"), ("shown.html?details=hide#/1/1", shown, "Core")]
    httpd = serve(str(tmp_path))
    try:
        with sync_api.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get("CHROME") or None)
            for url, slides, at in want:
                page = browser.new_page()
                page.goto("http://127.0.0.1:%d/%s" % (httpd.server_address[1], url))
                page.wait_for_function("window.Reveal && Reveal.isReady()")
                page.wait_for_timeout(100)   # reveal's ready event, a tick after it starts
                got = page.evaluate("[Reveal.getSlides().map(s => s.querySelector('h1, h2').textContent).join('|'),"
                                    " Reveal.getCurrentSlide().querySelector('h1, h2').textContent]")
                assert got == [slides, at], (url, got)
                page.close()
            browser.close()
    finally:
        httpd.shutdown()
