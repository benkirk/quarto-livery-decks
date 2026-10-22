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
runs under `pandoc lua` with a `quarto` shim (test_footnotes.py's harness). Needs pandoc
($QUARTO_PANDOC).
"""

import json
import os
import shutil
import subprocess

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


def read(tmp_path, md):
    """The harness's output on md: (the galleries, the warnings)."""
    lines = harness(tmp_path, md).splitlines()
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


def test_top_level_only(tmp_path):
    """A gallery at the slide's top level is drawn; one in a column is warned of and left as its
    pictures."""
    md = gallery(3) + "\n:::: {.columns}\n::: {.column}\n" + gallery(2) + ":::\n::::\n"
    text, *warnings = harness(tmp_path, md, "top").split("\nWARNING: ")
    assert "GALLERY 3" in text and "GALLERY 2" not in text, text
    assert "g2.png" in text, "the nested gallery kept as its pictures"
    assert len(warnings) == 1 and ".gallery inside a column or another div is not drawn" in warnings[0], warnings
