"""Check grid-pptx.lua: a two-column slide's shares on a notes line, a grid slide flattened.

    python3 -m pytest tests/test_grid_pptx.py

A two-column slide keeps the Two Content layout (pandoc's placeholders idx 1 and 2) and its notes
carry `engine-columns: <share> <share>` (engine-common.lua's column_shares(): width= or an equal
share of what is left), with `wide` when slide-layout.lua's line says so, and no marker paragraph.
A three-column slide is flattened into one placeholder with its markers, every column's text kept;
a picture in it or in a card is a picture marker (an executed plot's bytes carried in it), a
linked one warned of. engine-common.lua's cell_figure() and base64() under `pandoc lua`. pandoc's pptx writer itself keeps only the first two `.column`s: the
premise is checked without the filter, and when pandoc writes the third, the flattening's reason
for three columns is gone. Needs pandoc ($QUARTO_PANDOC).
"""

import base64
import json
import re
import shutil
import subprocess
import zipfile

import pytest

from conftest import ENGINE, ROOT, lua_common, pandoc_exe

FILTER = ENGINE / "grid-pptx.lua"
COL = "::: {{.column{}}}\n{}\n:::\n"
NOTES = "::: notes\nengine-layout: wide\n:::\n"   # slide-layout.lua's line, as it writes it
LEAD = "## Lead\n\n::: {.lead}\n**Head**\nline\n:::\n\n"
PIC = "## Picture\n\n:::: {.columns}\n" + "".join(COL.format("", w) for w in ("![](p.png)", "HHH", "III")) + "::::\n\n"
MD = ("## Three\n\n:::: {.columns}\n" + "".join(COL.format("", w) for w in ("AAA", "BBB", "CCC")) + "::::\n\n"
      "## Two\n\n:::: {.columns}\n" + COL.format(' width="55%"', "DDD") + COL.format("", "EEE") + "::::\n\n"
      "## Wide\n\n:::: {.columns}\n" + COL.format("", "FFF") + COL.format("", "GGG") + "::::\n\n" + NOTES)


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    pandoc = pandoc_exe()
    tmp = tmp_path_factory.mktemp("cols")
    shutil.copy(ROOT / "decks" / "quickstart" / "screenshots" / "hero.png", tmp / "p.png")

    def render(md, *args):
        out = tmp / "t.pptx"
        r = subprocess.run([pandoc, *args, "-o", str(out)], input=md, text=True, cwd=tmp, capture_output=True, check=True)
        with zipfile.ZipFile(out) as z:
            parts = {n: z.read(n).decode() for n in z.namelist() if re.match(r"ppt/(slides|notesSlides)/(_rels/)?\w+\d+\.xml(\.rels)?$", n)}
        return r.stderr, parts
    err, slides = render(MD + "\n" + PIC + LEAD, "--lua-filter", str(FILTER))
    _, plain = render(MD)
    return err, slides, plain


def text(slides, part):
    return "".join(re.findall(r"<a:t>([^<]*)</a:t>", slides[part]))


def notes(slides, n):
    """Slide n's notes text, through its relationship to its notes slide."""
    m = re.search(r'Target="\.\./notesSlides/(notesSlide\d+\.xml)"', slides[f"ppt/slides/_rels/slide{n}.xml.rels"])
    return text(slides, f"ppt/notesSlides/{m.group(1)}") if m else ""


def test_three_flattened(rendered):
    err, slides, _ = rendered
    one = slides["ppt/slides/slide1.xml"]
    assert one.count("<p:ph idx=") == 1 and 'idx="2"' not in one, "a three-column slide not in one placeholder"
    t = text(slides, "ppt/slides/slide1.xml")
    assert "⟦engine:columns widths=0.3333,0.3333,0.3333⟧" in t, "no columns marker"
    assert t.count("⟦engine:column⟧") == 3 and t.count("⟦engine:end⟧") == 4, "column markers"
    assert all(w in t for w in ("AAA", "BBB", "CCC")), "a column's text lost"
    assert '"Three"' not in err, "a warning for a text grid"
    assert '"Picture"' not in err, f"a warning for a picture in a column: {err!r}"


def paras_of(xml):
    return ["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", xml)]


def test_picture_marked(rendered):
    """A picture in a three-column slide's column: a picture marker and its end inside the column's
    span, no picture shape, and no untitled continuation (pandoc drew it as a shape of its own and
    split the slide before)."""
    _, slides, _ = rendered
    parts = sorted((n for n in slides if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)), key=lambda n: int(re.search(r"\d+", n).group()))
    assert len(parts) == 5, f"the picture slide split: {len(parts)} slides"
    xml = next(slides[n] for n in parts if "HHH" in text(slides, n))
    assert "<p:pic>" not in xml, "pandoc drew the picture"
    paras = paras_of(xml)
    i = paras.index("⟦engine:column⟧")
    assert paras[i + 1:i + 4] == ["⟦engine:picture src=p.png⟧", "⟦engine:end⟧", "⟦engine:end⟧"], paras


def marked(tmp_path, md):
    """The filter's slides on md (rendered in tmp_path): (the warnings, each slide's paragraphs)."""
    out = tmp_path / "m.pptx"
    r = subprocess.run([pandoc_exe(), "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, cwd=tmp_path,
                       check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        names = sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)), key=lambda n: int(re.search(r"\d+", n).group()))
        return r.stderr, [paras_of(z.read(n).decode()) for n in names]


def test_card_picture_marked(tmp_path):
    """A captioned figure in a card: its marker, the caption a paragraph, its end, before the card's
    next line; a sized image carries its width; a linked one stays in the flow, warned of."""
    shutil.copy(ROOT / "decks" / "quickstart" / "screenshots" / "hero.png", tmp_path / "p.png")
    md = ("## Cards\n\n:::: {.columns}\n::: {.column .card}\n### One\n\n![The caption](p.png)\n\nA line\n:::\n"
          "::: {.column .card}\n![](p.png){width=50%}\n:::\n::::\n\n"
          "## Linked\n\n:::: {.columns}\n::: {.column .card}\n[![](p.png)](https://example.org)\n:::\n::: {.column}\nx\n:::\n::::\n")
    err, slides = marked(tmp_path, md)
    one = slides[0]
    i = one.index("⟦engine:picture src=p.png⟧")
    assert one[i - 1] == "⟦engine:title⟧One" and one[i + 1:i + 4] == ["The caption", "⟦engine:end⟧", "A line"], one
    assert "⟦engine:picture src=p.png size=50%⟧" in one, one
    assert 'slide "Linked": a linked picture in a card or a 3+ column slide is not drawn in pptx' in err, err
    assert not any("⟦engine:picture" in p for s in slides[1:] for p in s), "a linked picture marked"


def test_plot_bytes_carried(tmp_path):
    """An executed cell's plot (a src under figure-pptx/ in <deck>_files/: gone from disk when the
    pptx steps run) rides in its marker as base64 of the file's bytes; a missing one is warned of
    and left in the flow."""
    d = tmp_path / "t_files" / "figure-pptx"
    d.mkdir(parents=True)
    png = (ROOT / "decks" / "quickstart" / "screenshots" / "hero.png").read_bytes()
    (d / "cell-2-output-1.png").write_bytes(png)
    cell = ("::: {{.cell}}\n```python\nplot()\n```\n::: {{.cell-output .cell-output-display}}\n"
            "![](t_files/figure-pptx/{}){{fig-alt=\"x\"}}\n:::\n:::\n")
    md = ("## Plot\n\n:::: {.columns}\n::: {.column .card}\n" + cell.format("cell-2-output-1.png") + ":::\n"
          "::: {.column .card}\n" + cell.format("missing.png") + ":::\n::::\n")
    err, slides = marked(tmp_path, md)
    m = next(p for p in slides[0] if p.startswith("⟦engine:picture"))
    assert m.startswith("⟦engine:picture src=t_files/figure-pptx/cell-2-output-1.png data="), m[:120]
    assert base64.b64decode(m[:-1].split(" data=")[1]) == png, "the bytes carried are not the file's"
    assert "plot()" in slides[0], "the cell's code lost"
    assert "missing.png cannot be read" in err, err


# cell_figure() on each top-level block of the markdown from stdin, as JSON lines ({src, caption,
# sized} or {nil, linked}); with arg[2] "latexfig" a Figure in Quarto's PDF shape first (test_gallery's);
# with "b64" base64() of each line of stdin
CELL = r"""
local src = io.read("a")
if arg[2] == "b64" then
  for line in (src .. "\n"):gmatch("(.-)\n") do io.write(C.base64(line) .. "\n") end
  return
end
local doc = pandoc.read(src, "markdown")
if arg[2] == "latexfig" then
  doc = doc:walk({ Figure = function(f)
    local img
    f = f:walk({ Image = function(im) im.caption = pandoc.Inlines({}); img = im; return im end })
    local cap = pandoc.Inlines({ pandoc.RawInline("latex", "\\caption"), pandoc.RawInline("latex", "{") })
    cap:extend(pandoc.utils.blocks_to_inlines(f.caption.long)); cap:insert(pandoc.RawInline("latex", "}"))
    return pandoc.Div({ pandoc.RawBlock("latex-merge", "\\begin{figure}[H]"),
      pandoc.Para({ pandoc.RawInline("latex", "{\\centering "), img, pandoc.RawInline("latex", "\n\n}") }),
      pandoc.Para(cap), pandoc.RawBlock("latex-merge", "\\end{figure}%") })
  end })
end
for _, b in ipairs(doc.blocks) do
  local fig, linked = C.cell_figure(b)
  io.write(pandoc.json.encode(fig and { src = fig.src, caption = fig.caption and pandoc.utils.stringify(fig.caption) or pandoc.json.null,
    sized = fig.sized or pandoc.json.null } or { ["nil"] = true, linked = linked or false }) .. "\n")
end
"""


def test_cell_figure(tmp_path):
    """The shapes a picture in a cell takes: a Figure (its caption), an image paragraph (sized), an
    executed cell's Div of one picture, Quarto's PDF figure; not a cell with its code beside the
    picture, two images, or text; an image in a link nil and linked."""
    md = ("![A caption](a.png)\n\n![](b.png){width=40%}\n\n"
          "::: {.cell}\n::: {.cell-output-display}\n![](c.png)\n:::\n:::\n\n"
          "::: {.cell}\n```\ncode\n```\n::: {.cell-output-display}\n![](d.png)\n:::\n:::\n\n"
          "![](e.png) ![](f.png)\n\nSome text\n\n[![](g.png)](https://example.org)\n")
    out, warnings = lua_common(tmp_path, CELL, md)
    got = [json.loads(x) for x in out.splitlines()]
    assert got == [{"src": "a.png", "caption": "A caption", "sized": None}, {"src": "b.png", "caption": None, "sized": "40%"},
                   {"src": "c.png", "caption": None, "sized": None}, {"nil": True, "linked": False},
                   {"nil": True, "linked": False}, {"nil": True, "linked": False}, {"nil": True, "linked": True}], got
    assert not warnings, warnings
    out, _ = lua_common(tmp_path, CELL, "![The PDF caption](h.png)\n", "latexfig")
    assert json.loads(out) == {"src": "h.png", "caption": "The PDF caption", "sized": None}, out


def test_base64(tmp_path):
    """base64() against Python's, RFC 4648's vectors and some bytes past ASCII."""
    lines = ["", "f", "fo", "foo", "foob", "fooba", "foobar", "⟦engine⟧ ü"]
    out, _ = lua_common(tmp_path, CELL, "\n".join(lines), "b64")
    assert out.splitlines() == [base64.b64encode(x.encode()).decode() for x in lines], out


def test_pandoc_still_drops_the_third(rendered):
    *_, plain = rendered
    body = "".join(text(plain, n) for n in plain if re.match(r"ppt/slides/slide", n))
    assert "AAA" in body and "BBB" in body, "pandoc lost a column it keeps"
    assert "CCC" not in body, "pandoc now writes a third column: grid-pptx.lua need not flatten for it"


def test_two_columns_marked(rendered):
    _, slides, _ = rendered
    two = slides["ppt/slides/slide2.xml"]
    assert 'idx="1"' in two and 'idx="2"' in two, "the 55/45 slide is not on Two Content's placeholders"
    assert "DDD" in text(slides, "ppt/slides/slide2.xml"), "the body is not its columns"
    assert "engine-columns: 0.55 0.45" in notes(slides, 2), "no shares line"
    assert "engine-columns: 0.5 0.5 wide" in notes(slides, 3), "no wide on the shares line"
    assert "engine-columns" not in notes(slides, 1), "a shares line on a three-column slide"
    assert not any("engine-columns" in text(slides, n) for n in slides if re.match(r"ppt/slides/slide", n)), "the line in a body"
    assert "⟦" not in text(slides, "ppt/slides/slide2.xml"), "a marker on a plain columns slide"


def test_lead_marked(rendered):
    _, slides, _ = rendered
    part = next(n for n in slides if re.match(r"ppt/slides/slide\d+\.xml$", n) and "Head" in text(slides, n))
    t = text(slides, part).removeprefix("Lead")
    assert t.startswith("⟦engine:lead⟧Head") and "line⟦engine:end⟧" in t, f"lead markers: {t!r}"
    paras = ["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", slides[part])]
    assert "Head" in paras and "line" in paras, f"the lead's two lines not two paragraphs: {paras}"


def test_card_marked(pandoc_deck, tmp_path):
    """A card column: its marker carries the role and flags, its heading is a ⟦engine:title⟧
    paragraph (no heading: pandoc would add spcBef), its sub, label and big lines theirs."""
    md = ('## Cards\n\n:::: {.columns}\n::: {.column .card .pick role="secondary"}\n### OPTION 1\n'
          '[The sub]{.sub}\n\n[LABEL]{.label}\n[$20M]{.big}\n:::\n::: {.column}\nPlain\n:::\n::::\n')
    pandoc = pandoc_exe()
    out = tmp_path / "c.pptx"
    subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        xml = z.read("ppt/slides/slide1.xml").decode()
    paras = ["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", xml)]
    for want in ("⟦engine:column card role=secondary pick⟧", "⟦engine:title⟧OPTION 1", "⟦engine:sub⟧The sub",
                 "⟦engine:label⟧LABEL", "⟦engine:big⟧$20M", "⟦engine:column⟧"):
        assert want in paras, f"{want!r} not a paragraph: {paras}"


def test_rail_marked(tmp_path):
    """Steps and a timeline: a rail marker with the kind and the role, an item marker per item
    (`done` on a done milestone), the title or date a ⟦engine:title⟧ paragraph, the text after it,
    every marker closed."""
    md = ('## Steps\n\n::: {.steps role="secondary"}\n1. **Propose** A case.\n2. **Pilot** Six weeks.\n:::\n\n'
          '## Timeline\n\n::: {.timeline}\n- [x] **Q1** Accepted\n- **2026** Full\n:::\n\n'
          '## Later\n\n::: {.steps}\n4. **Review** r\n:::\n')
    pandoc = pandoc_exe()
    out = tmp_path / "r.pptx"
    subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        slides = [z.read(f"ppt/slides/slide{n}.xml").decode() for n in (1, 2, 3)]
    paras = [["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", x)] for x in slides]
    paras = [[p for p in ps if p not in ("Steps", "Timeline", "Later")] for ps in paras]   # the titles
    assert paras[2][0] == "⟦engine:rail kind=steps role=primary-contrast start=4⟧", "a list from 4 carries its start"
    assert paras[0] == ["⟦engine:rail kind=steps role=secondary⟧", "⟦engine:item⟧", "⟦engine:title⟧Propose", "A case.",
                        "⟦engine:end⟧", "⟦engine:item⟧", "⟦engine:title⟧Pilot", "Six weeks.", "⟦engine:end⟧", "⟦engine:end⟧"], paras[0]
    assert paras[1] == ["⟦engine:rail kind=timeline role=primary-contrast⟧", "⟦engine:item done⟧", "⟦engine:title⟧Q1", "Accepted",
                        "⟦engine:end⟧", "⟦engine:item⟧", "⟦engine:title⟧2026", "Full", "⟦engine:end⟧", "⟦engine:end⟧"], paras[1]


def test_unnumbered_in_the_metadata(tmp_path):
    """pandoc's pptx writer drops `.unnumbered`: the filter writes the dividers outside the count,
    by their places among the dividers, as `engine-unnumbered` (docProps/custom.xml), for
    section_subtitle.py; a deck without one has no such property."""
    pandoc = pandoc_exe()

    def custom(md):
        out = tmp_path / "u.pptx"
        subprocess.run([pandoc, "--slide-level=2", "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True,
                       check=True, capture_output=True)
        with zipfile.ZipFile(out) as z:
            return z.read("docProps/custom.xml").decode() if "docProps/custom.xml" in z.namelist() else ""
    md = "# One\n\n## a\n\nx\n\n# Backup {.unnumbered}\n\n## b\n\ny\n\n# Two\n\n## c\n\nz\n\n# More {.unnumbered}\n\n## d\n\nw\n"
    prop = re.search(r'name="engine-unnumbered"[^>]*>.*?<vt:lpwstr>([^<]*)</vt:lpwstr>', custom(md), re.S)
    assert prop and prop.group(1) == "2 4", custom(md)
    assert "engine-unnumbered" not in custom(md.replace(" {.unnumbered}", ""))


def test_quote_marked(tmp_path):
    """A quote: `⟦engine:quote⟧` (role= only when it names one), a paragraph per source line, the
    attribution a paragraph led by `⟦engine:attribution⟧` without its dash, `⟦engine:end⟧`; a bare
    `>` the same. A quote in a column makes a two-column slide a grid slide (its columns flattened),
    and a quote on its own is marked too."""
    md = ('## Quote\n\n::: {.quote role="accent"}\nOne line\nanother\n— Who, 1962\n:::\n\n'
          '## Column\n\n:::: {.columns}\n::: {.column}\nLeft\n:::\n::: {.column}\n> Right\n> -- Them\n:::\n::::\n')
    pandoc = pandoc_exe()
    out = tmp_path / "q.pptx"
    subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        slides = [z.read(f"ppt/slides/slide{n}.xml").decode() for n in (1, 2)]
    paras = [["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", x)] for x in slides]
    assert paras[0][1:] == ["⟦engine:quote role=accent⟧", "One line", "another", "⟦engine:attribution⟧Who, 1962", "⟦engine:end⟧"], paras[0]
    assert paras[1][1:] == ["⟦engine:columns widths=0.5,0.5⟧", "⟦engine:column⟧", "Left", "⟦engine:end⟧", "⟦engine:column⟧",
                            "⟦engine:quote⟧", "Right", "⟦engine:attribution⟧Them", "⟦engine:end⟧", "⟦engine:end⟧", "⟦engine:end⟧"], paras[1]


def test_agenda_marked(tmp_path):
    """An agenda slide: its title, `⟦engine:agenda current=n⟧` (the numbered dividers before it), per
    numbered section an item marker with its number and state, the title and the divider's
    subtitle led by their prefixes; the unnumbered Backup absent; a body of its own dropped."""
    md = ("## Agenda {.agenda}\n\nAn author's line.\n\n# One\n\nIts subtitle.\n\n## a\n\nx\n\n"
          "# Two\n\n## Where we are {.agenda}\n\n# Backup {.unnumbered}\n\n## b\n\ny\n")
    pandoc = pandoc_exe()
    out = tmp_path / "a.pptx"
    r = subprocess.run([pandoc, "--slide-level=2", "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True,
                       check=True, capture_output=True)
    assert "has a body of its own" in r.stderr, r.stderr
    with zipfile.ZipFile(out) as z:
        texts = [[("".join(re.findall(r"<a:t>([^<]*)</a:t>", p))) for p in re.findall(r"<a:p>.*?</a:p>", z.read(n).decode())]
                 for n in sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                                 key=lambda n: int(re.search(r"(\d+)", n).group(1)))]
    front = next(t for t in texts if t and t[0] == "Agenda")
    assert front[1:] == ["⟦engine:agenda current=0⟧", "⟦engine:item n=1 state=next⟧", "⟦engine:title⟧One", "⟦engine:sub⟧Its subtitle.",
                         "⟦engine:end⟧", "⟦engine:item n=2 state=next⟧", "⟦engine:title⟧Two", "⟦engine:end⟧", "⟦engine:end⟧"], front
    later = next(t for t in texts if t and t[0] == "Where we are")
    assert "⟦engine:agenda current=2⟧" in later and "⟦engine:item n=1 state=done⟧" in later and "⟦engine:item n=2 state=current⟧" in later
    assert not any("Backup" in x for x in front + later), "an unnumbered divider is not on the agenda"


def test_quote_beside_a_picture(tmp_path):
    """A two-column slide with a quote in one column and a picture in the other stays pandoc's (a grid
    column cannot hold the picture): no marker, the quote pandoc's own blockquote, and a warning."""
    shutil.copy(ROOT / "decks" / "quickstart" / "screenshots" / "hero.png", tmp_path / "p.png")
    md = "## Beside\n\n:::: {.columns}\n" + COL.format("", "> Quoted\n> -- Them") + COL.format("", "![](p.png)") + "::::\n"
    pandoc = pandoc_exe()
    out = tmp_path / "b.pptx"
    r = subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, check=True,
                       capture_output=True, cwd=tmp_path)
    assert "a quote beside a picture or table in a two-column slide is not drawn in pptx" in r.stderr, r.stderr
    with zipfile.ZipFile(out) as z:
        xml = z.read("ppt/slides/slide1.xml").decode()
    assert "⟦engine:" not in xml and "Quoted" in xml and "<p:pic>" in xml, "pandoc's own slide, the picture in it"


def test_gallery_marked(tmp_path):
    """A gallery: its marker with the cells, the fit and height= (`full` from slide-layout.lua's notes
    line), an item marker per image with its path percent-encoded where it would break the marker, its
    caption a paragraph before the item's end, no picture embedded; a refused gallery is unwrapped into
    its pictures (pandoc drops a picture in a Div), warned of by its slide's title."""
    for name in ("g1.png", "g 2=x.png"):
        shutil.copy(ROOT / "decks" / "quickstart" / "screenshots" / "hero.png", tmp_path / name)
    md = ('## Gallery\n\n::: {.gallery cols=2 height=0.6}\n![The cover](g1.png)\n\n![](<g 2=x.png>)\n:::\n\n'
          '## Full\n\n::: {.gallery fit=cover}\n![](g1.png)\n:::\n\nThe caption.\n\n::: notes\nengine-layout: full\n:::\n\n'
          '## Refused\n\n::: {.gallery cols=1 rows=1}\n![](g1.png)\n\n![](g1.png)\n:::\n\n'
          '## Thanks\n\n::: {.gallery}\n![](g1.png)\n:::\n\n::: notes\nengine-layout: closing\n:::\n')
    pandoc = pandoc_exe()
    out = tmp_path / "g.pptx"
    r = subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, check=True,
                       capture_output=True, cwd=tmp_path)
    with zipfile.ZipFile(out) as z:
        slides = [z.read(n).decode() for n in sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                                                     key=lambda n: int(re.search(r"(\d+)", n).group(1)))]
    paras = [["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", x)] for x in slides]
    assert paras[0][1:] == ["⟦engine:gallery cols=2 rows=1 fit=contain height=0.6⟧", "⟦engine:item src=g1.png⟧", "The cover",
                            "⟦engine:end⟧", "⟦engine:item src=g%202%3Dx.png⟧", "⟦engine:end⟧", "⟦engine:end⟧"], paras[0]
    assert "<p:pic>" not in slides[0] and "<p:pic>" not in slides[1], "the files are gallery.py's to read, not pandoc's"
    assert paras[1][1:4] == ["⟦engine:gallery cols=1 rows=1 fit=cover full⟧", "⟦engine:item src=g1.png⟧", "⟦engine:end⟧"], paras[1]
    assert "The caption." in paras[1], "the slide caption after the gallery, for grid.py"
    first = next(k for k, x in enumerate(slides) if "Refused" in x)
    closing = next(k for k, x in enumerate(slides) if "Thanks" in x)
    refused = slides[first:closing]   # it and pandoc's continuations
    assert "⟦engine:" not in "".join(refused) and "".join(refused).count("<p:pic>") == 2, "a refused gallery: pandoc's pictures"
    assert 'grid-pptx.lua: slide "Refused": a .gallery of 2 images does not fit cols=1 rows=1' in r.stderr, r.stderr
    assert "⟦engine:" not in slides[closing] and "<p:pic>" in slides[closing], "a closing slide's gallery: pandoc's picture"
    assert 'grid-pptx.lua: slide "Thanks": a .gallery on a closing slide is not drawn; left as its pictures' in r.stderr, r.stderr
