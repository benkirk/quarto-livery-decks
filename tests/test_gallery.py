"""Check image galleries: engine-common.lua's reader (is_gallery(), gallery_items(), top_galleries()).

    python3 -m pytest tests/test_gallery.py

A `::: {.gallery}` div holds image files only, each its own paragraph (`![Caption](path)` a Figure,
`![](path)` a Para of one Image; several images on consecutive lines are one paragraph, an item
each): cols defaults to ceil(sqrt(n)), rows to ceil(n/cols) (rows alone: cols = ceil(n/rows)); a
caption from a Figure, else the image's alt text; `captioned` when any image has one; fit contain by
default, cover, anything else warned of (contain); height= a share in (0, 1]. Refused with one
warning each, the div left alone: more than cols*rows, a paragraph, a plot under figure-*/, a link
round an image, a gallery inside it, thirteen images, a cols= that is not a positive whole number, a
height out of range. One inside a column is not drawn (top_galleries()), warned of. engine-common.lua
runs under `pandoc lua` with a `quarto` shim (test_footnotes.py's harness).

The pptx half: pandoc writes a deck with grid-pptx.lua (slide-layout.lua's notes lines by hand), the
driver's slide_layout, columns and grid steps draw it under ncar, and the gallery is one group of
pictures at the formula's cells (cells() recomputed from livery.json); contain keeps a file's aspect
inside its box, cover fills the box with a symmetric crop; the captions one height and one top per row,
in the caption size, muted, centered, the line reserved under an image without one; an .svg item a PNG;
height= its share of the body box; a {.wide} slide's cells at the wide margin; a {.full} slide's inside
the full pads, its caption in the caption line, the furniture gone; no marker left, every EMU an
integer; a missing file warned of. Needs pandoc ($QUARTO_PANDOC) and rsvg-convert.
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

# gallery_items() on every gallery div of the markdown from stdin, as JSON lines: {cols, rows, fit,
# height, captioned, items: [{src, caption, attrs}]} or {nil: true}; each warning a line "WARNING: ..."
HARNESS = r"""
local warnings = {}
quarto = { log = { warning = function(s) table.insert(warnings, s) end }, json = { decode = pandoc.json.decode } }
local C = dofile(arg[1])
local doc = pandoc.read(io.read("a"), "markdown")
if arg[2] == "latexfig" then   -- Quarto's PDF shape of ![Caption](path): a classless Div round raw \begin{figure}
  doc = doc:walk({ Figure = function(f)
    local img
    f = f:walk({ Image = function(im) im.caption = pandoc.Inlines({}); img = im; return im end })
    local cap = pandoc.Inlines({ pandoc.RawInline("latex", "\\caption"), pandoc.RawInline("latex", "{") })
    cap:extend(pandoc.utils.blocks_to_inlines(f.caption.long)); cap:insert(pandoc.RawInline("latex", "}"))
    return pandoc.Div({ pandoc.RawBlock("latex-merge", "\\begin{figure}[H]"),
      pandoc.Para({ pandoc.RawInline("latex", "{\\centering "), img, pandoc.RawInline("latex", "\n\n}"), pandoc.RawInline("latex", "\n") }),
      pandoc.Para(cap), pandoc.RawBlock("latex-merge", "\\end{figure}%") })
  end })
  for _, b in ipairs(doc.blocks) do   -- the shape is a .full slide's figure too
    if C.is_gallery(b) then io.write(pandoc.json.encode({ full = C.split_full(pandoc.Blocks({ b.content[1] })) ~= nil }) .. "\n") end
  end
end
if arg[2] == "bag" then   -- latex_file(): a media-bag item (an .svg's PDF, as Quarto leaves it) written out under arg[3]
  pandoc.mediabag.insert("images/vec.pdf", "application/pdf", "%PDF-1.4 fake")
  io.write(C.latex_file("images/vec.pdf", arg[3]) .. "\n" .. C.latex_file("pics/my%20pic.jpg", arg[3]) .. "\n")
  return
end
if arg[2] == "composed" then   -- composed_kind() per slide heading, unwrap_galleries() on the slide after one
  local i = 1
  while i <= #doc.blocks do
    local blk, slide = doc.blocks[i], nil
    slide, i = C.slide_from(doc.blocks, i + 1, 2)
    local where = C.composed_kind(blk, 2)
    if where then slide = C.unwrap_galleries(slide, "t", where) end
    local n = 0
    for _, b in ipairs(slide) do if C.is_gallery(b) then n = n + 1 end end
    io.write(pandoc.json.encode({ where = where or false, galleries = n, blocks = #slide }) .. "\n")
  end
  for _, w in ipairs(warnings) do io.write("WARNING: " .. w .. "\n") end
  return
end
if arg[2] == "top" then   -- top_galleries(): each drawn gallery a paragraph naming it, the rest as it was
  local out = C.top_galleries(doc.blocks, "t", function(g) return { pandoc.Para("GALLERY " .. #g.items) } end)
  io.write(pandoc.write(pandoc.Pandoc(out), "markdown", { wrap_text = "none" }))
  for _, w in ipairs(warnings) do io.write("\nWARNING: " .. w) end
  return
end
doc.blocks:walk({ Div = function(d)
  if not C.is_gallery(d) then return nil end
  local g = C.gallery_items(d, "t")
  local out
  if g then
    out = { cols = g.cols, rows = g.rows, fit = g.fit, height = g.height or pandoc.json.null, captioned = g.captioned, items = {} }
    for _, it in ipairs(g.items) do
      local attrs = {}
      for k, v in pairs(it.image.attributes) do attrs[k] = v end
      table.insert(out.items, { src = it.src, caption = it.caption and pandoc.utils.stringify(it.caption) or pandoc.json.null,
                                attrs = next(attrs) and attrs or pandoc.json.null })
    end
  else
    out = { ["nil"] = true }
  end
  io.write(pandoc.json.encode(out) .. "\n")
end })
for _, w in ipairs(warnings) do io.write("WARNING: " .. w .. "\n") end
"""


def images(n, caption=lambda k: "", sep="\n\n"):
    return sep.join(f"![{caption(k)}](g{k}.png)" for k in range(1, n + 1)) + "\n"


def gallery(n, attrs="", **kw):
    return f"::: {{.gallery{attrs}}}\n" + images(n, **kw) + ":::\n"


def harness(tmp_path, md, *mode):
    exe = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not exe:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")
    script = tmp_path / "harness.lua"
    script.write_text(HARNESS)
    return subprocess.run([exe, "lua", str(script), str(ENGINE / "engine-common.lua"), *mode],
                          input=md, text=True, capture_output=True, check=True).stdout


def read(tmp_path, md, *mode):
    """The harness's output on md: (the galleries, the warnings)."""
    lines = harness(tmp_path, md, *mode).splitlines()
    return ([json.loads(x) for x in lines if not x.startswith("WARNING: ")],
            [x[len("WARNING: "):] for x in lines if x.startswith("WARNING: ")])


@pytest.mark.parametrize("n, attrs, cols, rows", [
    (5, "", 3, 2), (4, "", 2, 2), (1, "", 1, 1), (7, "", 3, 3), (12, "", 4, 3),
    (6, " rows=2", 3, 2), (5, " rows=1", 5, 1), (6, " cols=6", 6, 1), (6, " cols=3 rows=2", 3, 2),
], ids=lambda v: str(v).strip() or "-")
def test_cells(tmp_path, n, attrs, cols, rows):
    """Square-ish by default (cols ceil(sqrt(n)), rows ceil(n/cols)); either given overrides."""
    (g,), warnings = read(tmp_path, gallery(n, attrs))
    assert not warnings and (g["cols"], g["rows"]) == (cols, rows), (g, warnings)
    assert [i["src"] for i in g["items"]] == [f"g{k}.png" for k in range(1, n + 1)]


def test_captions(tmp_path):
    """A Figure's caption, or the alt text of an image among several on one paragraph; none for
    `![](x)`; captioned when any image has one."""
    md = "::: {.gallery}\n![The cover](g1.png)\n\n![](g2.png)\n\n![A](g3.png)\n![](g4.png)\n:::\n"
    (g,), warnings = read(tmp_path, md)
    assert not warnings, warnings
    assert [i["caption"] for i in g["items"]] == ["The cover", None, "A", None], "consecutive lines: an item each"
    assert g["captioned"] is True
    (g,), _ = read(tmp_path, gallery(3))
    assert g["captioned"] is False and all(i["caption"] is None for i in g["items"])


def test_fit_and_height(tmp_path):
    (g,), warnings = read(tmp_path, gallery(4))
    assert g["fit"] == "contain" and g["height"] is None and not warnings, "the defaults"
    (g,), warnings = read(tmp_path, gallery(4, ' fit=cover height=0.6'))
    assert g["fit"] == "cover" and g["height"] == 0.6 and not warnings
    (g,), warnings = read(tmp_path, gallery(4, ' fit=fill'))
    assert g["fit"] == "contain" and len(warnings) == 1 and "fit=fill is contain or cover; contain" in warnings[0], warnings


def test_quarto_latex_figure(tmp_path):
    """Under Quarto's PDF filters a captioned image on its own paragraph reaches the reader as a
    classless Div round raw \\begin{figure} ... \\caption{...} (the Figure is gone, the alt emptied):
    its image and caption are read, and the shape is a figure to split_full (a .full slide's)."""
    md = "::: {.gallery cols=2}\n![One](g1.png)\n\n![](g2.png)\n:::\n"
    (full, g), warnings = read(tmp_path, md, "latexfig")
    assert not warnings, warnings
    assert full == {"full": True}
    assert [(i["src"], i["caption"]) for i in g["items"]] == [("g1.png", "One"), ("g2.png", None)] and g["captioned"] is True


def test_latex_file(tmp_path):
    """The file a gallery's \\engineimage names: an .svg's PDF, which Quarto converts into pandoc's
    media bag (pandoc writes a bag item out only where an Image references it), written where pandoc
    would put it, <output>_files/mediabag/<src>; any other src percent-decoded to the file's name."""
    bag, plain = harness(tmp_path, "", "bag", str(tmp_path / "deck.tex")).splitlines()
    assert bag == str(tmp_path / "deck_files" / "mediabag" / "images" / "vec.pdf"), bag
    assert (tmp_path / "deck_files" / "mediabag" / "images" / "vec.pdf").read_bytes() == b"%PDF-1.4 fake"
    assert plain == "pics/my pic.jpg"


def test_size_attributes_dropped(tmp_path):
    """A per-image width= or height= goes: the cell sizes the picture."""
    (g,), _ = read(tmp_path, "::: {.gallery}\n![A](g1.png){width=50% height=2in}\n\n![](g2.png){width=300}\n:::\n")
    assert [i["attrs"] for i in g["items"]] == [None, None], g


@pytest.mark.parametrize("md, why", [
    (gallery(7, " cols=3 rows=2"), "of 7 images does not fit cols=3 rows=2"),
    ("::: {.gallery}\n![](g1.png)\n\nA paragraph.\n:::\n", "a plot or diagram is not drawn"),
    ("::: {.gallery}\n![](g1.png)\n\n![](deck_files/figure-revealjs/cell-2-output-1.svg)\n:::\n", "an executed cell's plot"),
    ("::: {.gallery}\n![](g1.png)\n\n![](figure-pptx/plot.png)\n:::\n", "an executed cell's plot"),
    ("::: {.gallery}\n[![](g1.png)](https://ncar.ucar.edu/)\n:::\n", "inside a link is not drawn"),
    ("::: {.gallery}\n![](g1.png)\n\n" + gallery(2) + ":::\n", "inside a .gallery is not drawn"),
    (gallery(13), "has 13 images, more than 12"),
    (gallery(4, " cols=0"), "cols=0 is not a positive whole number"),
    (gallery(4, " rows=1.5"), "rows=1.5 is not a positive whole number"),
    (gallery(4, " height=1.2"), "height=1.2 is not a share of the body in (0, 1]"),
    ("::: {.gallery}\n:::\n", "holds no image"),
], ids=["too many for 3x2", "a paragraph", "a plot", "a pptx plot", "a link", "nested", "thirteen", "cols=0",
        "rows=1.5", "height=1.2", "empty"])
def test_refused(tmp_path, md, why):
    out, warnings = read(tmp_path, md)
    assert out[-1].get("nil") and len(warnings) == 1 and why in warnings[0], (out, warnings)   # the outer last (bottom-up)


def test_content_slides_only(tmp_path):
    """A gallery is drawn on a content slide only (a .full slide's is its branch's): on a feature or
    closing slide, after a divider or on an untitled slide it is warned of and unwrapped into its
    paragraphs, so the pictures stay in every format (composed_kind(), unwrap_galleries())."""
    md = ("# Part\n\n" + gallery(2) + "## Content\n\n" + gallery(2) + "## Full {.full}\n\n" + gallery(2)
          + "## Photo {.feature}\n\n" + gallery(2) + "## Thanks {.closing}\n\nA line.\n\n" + gallery(2))
    slides, warnings = read(tmp_path, md, "composed")
    assert [(s["where"], s["galleries"], s["blocks"]) for s in slides] == [
        ("divider", 0, 2), (False, 1, 1), (False, 1, 1), ("feature", 0, 2), ("closing", 0, 3)], slides
    assert [w.split(": ", 1)[1] for w in warnings] == [f"a .gallery on a {k} slide is not drawn; left as its pictures"
                                                        for k in ("divider", "feature", "closing")], warnings


def test_top_level_only(tmp_path):
    """A gallery at the slide's top level is drawn; one in a column is warned of and left as its
    pictures."""
    md = gallery(3) + "\n:::: {.columns}\n::: {.column}\n" + gallery(2) + ":::\n::::\n"
    text, *warnings = harness(tmp_path, md, "top").split("\nWARNING: ")
    assert "GALLERY 3" in text and "GALLERY 2" not in text, text
    assert "g2.png" in text, "the nested gallery kept as its pictures"
    assert len(warnings) == 1 and ".gallery inside a column or another div is not drawn" in warnings[0], warnings


# ---------------------------------------------------------------------------- the pptx drawer

SVG = (b'<svg xmlns="http://www.w3.org/2000/svg" width="72pt" height="36pt" viewBox="0 0 72 36">'
       b'<rect x="4" y="4" width="64" height="28" fill="#0057C2"/></svg>')
PPTX_MD = ("## Captioned\n\nA line above it.\n\n::: {.gallery cols=2 rows=2}\n"
           "![Landscape](p.jpg)\n\n![](tall.png)\n\n![Vector](v.svg)\n\n![Hero](hero.png)\n:::\n\n"
           "## Cover\n\n::: {.gallery cols=2 fit=cover}\n![](p.jpg)\n\n![](tall.png)\n:::\n\n"
           "## Half\n\n::: {.gallery cols=2 height=0.5 fit=cover}\n![](p.jpg)\n\n![](tall.png)\n:::\n\n"
           "## Wide\n\n::: {.gallery cols=2 fit=cover}\n![](p.jpg)\n\n![](tall.png)\n:::\n\n"
           "::: notes\nengine-layout: wide\n:::\n\n"
           "## Full\n\n::: {.gallery cols=2 fit=cover}\n![](p.jpg)\n\n![](tall.png)\n:::\n\n"
           "The caption line.\n\n::: notes\nengine-layout: full\n:::\n\n"
           "## Missing\n\n::: {.gallery}\n![](p.jpg)\n\n![](nope.png)\n:::\n")
STEP = """
import sys
from pathlib import Path
from pptx import Presentation
from pptx_steps import columns, grid, slide_layout
p = Path(sys.argv[1]); prs = Presentation(p)
slide_layout.run(prs, p); columns.run(prs, p); grid.run(prs, p); prs.save(p)
"""   # the driver's order


@pytest.fixture(scope="module")
def pptx_deck(tmp_path_factory):
    from PIL import Image
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not pandoc:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")
    assert shutil.which("rsvg-convert"), "rsvg-convert not found (conda-forge librsvg)"
    tmp = tmp_path_factory.mktemp("gallery")
    shutil.copy(ROOT / "decks" / "quickstart" / "images" / "example.jpg", tmp / "p.jpg")
    shutil.copy(ROOT / "decks" / "quickstart" / "screenshots" / "hero.png", tmp / "hero.png")
    Image.new("RGB", (300, 600), "#0057C2").save(tmp / "tall.png")
    (tmp / "v.svg").write_bytes(SVG)
    d = ROOT / "liveries" / "ncar"
    out = tmp / "g.pptx"
    subprocess.run([pandoc, "--lua-filter", str(ENGINE / "grid-pptx.lua"), "--reference-doc", str(d / "template.pptx"),
                    "-o", str(out)], input=PPTX_MD, text=True, cwd=tmp, check=True, capture_output=True)
    r = subprocess.run([sys.executable, "-c", STEP, str(out)], env={**os.environ, "LIVERY_DIR": str(d), "PYTHONPATH": str(ENGINE)},
                       check=True, capture_output=True, text=True)
    from pptx import Presentation
    livery = json.loads((d / "build" / "livery.json").read_text())
    return livery, Presentation(out), out, r.stderr


def flat(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:   # a group
            yield from flat(sh.shapes)


ORDER = {"Captioned": 0, "Cover": 1, "Half": 2, "Wide": 3, "Full": 4, "Missing": 5}


def parts(prs, title):
    slide = prs.slides[ORDER[title]]
    shapes = list(flat(slide.shapes))
    pics = sorted((sh for sh in shapes if re.fullmatch(r"Gallery \d+ picture", sh.name)), key=lambda sh: sh.name)
    caps = {int(sh.name.split()[1]): sh for sh in shapes if re.fullmatch(r"Gallery \d+ caption", sh.name)}
    return slide, shapes, pics, caps


def frame(livery, prs, left, top, width, height, cols, rows):
    """The cells, as gallery.py lays them: the box less the gaps, shared equally."""
    gap = round(livery["boxes"]["gallery"]["gap"] * prs.slide_width)
    cw, ch = round((width - gap * (cols - 1)) / cols), round((height - gap * (rows - 1)) / rows)
    return [(left + c * (cw + gap), top + r * (ch + gap), cw, ch) for r in range(rows) for c in range(cols)]


def pads(livery):
    body = livery["type"]["roles"]["body"]["pt"]
    v, h = livery["boxes"]["gallery"]["pad"]
    return round(v * body * 12700), round(h * body * 12700)


def body_frame(prs):
    """The Title and Content body placeholder's frame (left, top, width) and the body's foot."""
    layout = next(l for l in prs.slide_layouts if l.name == "Title and Content")
    ph = next(p for p in layout.placeholders if p.placeholder_format.idx == 1)
    return ph.left, ph.top, ph.width


def test_one_group_of_pictures(pptx_deck):
    _, prs, _, _ = pptx_deck
    for title, n in (("Captioned", 4), ("Cover", 2), ("Half", 2), ("Wide", 2), ("Full", 2)):
        slide, shapes, pics, _ = parts(prs, title)
        assert [sh.name for sh in slide.shapes if sh.name == "Gallery"] == ["Gallery"], (title, [sh.name for sh in slide.shapes])
        assert len(pics) == n and all(p.shape_type == 13 for p in pics), (title, [sh.name for sh in shapes])
        assert not any(sh.has_text_frame and "⟦" in sh.text_frame.text for sh in shapes), f"{title}: a marker left"


def test_cover_fills_its_cell(pptx_deck):
    """cover: each picture is its cell less the pads, cropped symmetrically to its aspect: the landscape
    photo at its sides, the tall file top and bottom."""
    livery, prs, _, _ = pptx_deck
    left, top, width = body_frame(prs)
    bottom = round(livery["geometry"]["body-bottom"] * prs.slide_height)
    vpad, hpad = pads(livery)
    _, _, pics, _ = parts(prs, "Cover")
    for pic, (cx, cy, cw, ch) in zip(pics, frame(livery, prs, left, top, width, bottom - top, 2, 1)):
        assert (pic.left, pic.top, pic.width, pic.height) == (cx + hpad, cy + vpad, cw - 2 * hpad, ch - 2 * vpad), pic.name
    landscape, tall = pics
    assert landscape.crop_left == pytest.approx(landscape.crop_right) and landscape.crop_left > 0 and landscape.crop_top == 0
    assert tall.crop_top == pytest.approx(tall.crop_bottom) and tall.crop_top > 0 and tall.crop_left == 0
    for pic in pics:   # what shows is the box's aspect
        iw, ih = pic.image.size
        shown = iw * (1 - pic.crop_left - pic.crop_right) / (ih * (1 - pic.crop_top - pic.crop_bottom))
        assert shown == pytest.approx(pic.width / pic.height, rel=0.01), pic.name


def test_contain_and_captions(pptx_deck):
    """contain: each picture its file's aspect, uncropped, inside its cell; the captions one height,
    one top per row, the caption size, muted, centered; the image without a caption still has the
    line under it (its picture ends above its row's captions); the .svg item a PNG."""
    livery, prs, _, _ = pptx_deck
    _, shapes, pics, caps = parts(prs, "Captioned")
    group = next(sh for sh in prs.slides[0].shapes if sh.name == "Gallery")
    for pic in pics:
        iw, ih = pic.image.size
        assert pic.crop_left == pic.crop_top == 0, pic.name
        assert pic.width / pic.height == pytest.approx(iw / ih, rel=0.01), pic.name
        assert group.left <= pic.left and pic.left + pic.width <= group.left + group.width, pic.name
    assert sorted(caps) == [1, 3, 4], "a caption box per captioned image"
    assert len({c.height for c in caps.values()}) == 1, "one caption height"
    assert caps[3].top == caps[4].top, "one top per row"
    tall = pics[1]
    assert tall.top + tall.height <= caps[1].top, "the line reserved under an image without a caption"
    size = round(2 * next(r["pt"] for k, r in livery["type"]["roles"].items() if k == "caption")) * 50
    muted = livery["roles"]["muted"].lstrip("#").upper()
    for c in caps.values():
        p = c.text_frame._txBody.find("{http://schemas.openxmlformats.org/drawingml/2006/main}p")
        xml = c.text_frame._txBody.xml
        assert p.find("{http://schemas.openxmlformats.org/drawingml/2006/main}pPr").get("algn") == "ctr"
        assert f'sz="{size}"' in xml and muted in xml.upper(), c.name
    assert pics[2].image.content_type == "image/png", "the .svg item rasterized"


def test_height_share(pptx_deck):
    """height=0.5: the rows take half the body box's height."""
    livery, prs, _, _ = pptx_deck
    vpad, _ = pads(livery)
    _, _, pics, _ = parts(prs, "Half")
    assert pics[0].height == round(0.5 * livery["geometry"]["body"][3] * prs.slide_height) - 2 * vpad


def test_wide(pptx_deck):
    livery, prs, _, _ = pptx_deck
    _, hpad = pads(livery)
    _, _, pics, _ = parts(prs, "Wide")
    assert pics[0].left == round(livery["geometry"]["wide-margin"] * prs.slide_width) + hpad, "the wide margin"


def test_full(pptx_deck):
    """{.full}: no master art or title, the cells inside the full pads above the footline and the
    caption line, the slide's caption in that line."""
    livery, prs, _, _ = pptx_deck
    slide, shapes, pics, _ = parts(prs, "Full")
    W, H = prs.slide_width, prs.slide_height
    f = livery["geometry"]["full"]
    pad, floor, cap = round(f["pad"] * W), round(f["footline"] * H), round(f["caption"] * H)
    assert slide._element.get("showMasterSp") == "0" and slide.shapes.title is None
    for pic in pics:
        assert pad <= pic.left and pic.left + pic.width <= W - pad and pad <= pic.top and pic.top + pic.height <= H - floor - cap
    caption = next(sh for sh in shapes if sh.name == "Gallery caption")
    assert caption.top == H - floor - cap and caption.text_frame.text == "The caption line."


def test_integers_and_warnings(pptx_deck):
    _, _, out, err = pptx_deck
    with zipfile.ZipFile(out) as z:
        xml = "".join(z.read(n).decode() for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n))
    floats = re.findall(r'\b(x|y|cx|cy|w|h|sz|l|t|r|b)="-?[0-9]+\.[0-9]+"', xml)
    assert not floats, f"non-integer values: {floats[:5]}"
    assert "slide 'Missing'" in err and "nope.png not found; its cell left empty" in err, err
