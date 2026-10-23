"""Status items: a list item led by ✓, ⚠ or ✗ gets the glyph as its bullet, in its status color.

grid-pptx.lua normalizes a status item (engine-common.lua's status_lists(): `- [x]`, `- [!]`,
`- [-]` in a card or a `::: {.status}` list, a literal ✓ ⚠ ✗ anywhere) to the glyph first in its
paragraph. On every text frame of every slide, in a list item (pandoc writes a:buNone on every
other paragraph, a slide's title too: "## ⚠︎ Careful" keeps its glyph), this takes the glyph and its space off the
paragraph's text and makes it the paragraph's bullet (`a:buChar`, colored `a:buClr` in the
livery's boxes.status color), so it stands where the bullet was and the text keeps its indent,
as HTML's and beamer's do; a failed item's text is muted. Idempotent: a paragraph whose bullet
is already a status glyph is left alone. After grid (the cards' text boxes), before type_step.
"""

from pathlib import Path

from lxml import etree
from pptx.oxml.ns import qn

import livery as livery_mod

from .common import BOXES, LIVERY, ppr_place, rpr, set_fill

GLYPHS = {"✓": "done", "⚠": "warn", "✗": "fail"}
STATUS = BOXES["status"]
MUTED = livery_mod.color(LIVERY, "muted")


def mark(p) -> bool:
    """A paragraph (a:p) led by a status glyph: the glyph made its bullet; False if it is not one."""
    ppr = p.find(qn("a:pPr"))
    if ppr is not None and ppr.find(qn("a:buNone")) is not None:   # not a list item: a title, a paragraph
        return False
    if ppr is not None and (bu := ppr.find(qn("a:buChar"))) is not None and bu.get("char") in GLYPHS:
        return False
    runs = p.findall(qn("a:r"))
    t = runs[0].find(qn("a:t")) if runs else None
    if t is None or not t.text:
        return False
    text = t.text.lstrip()
    glyph = text[:1]
    if glyph not in GLYPHS:
        return False
    t.text = text[1:].lstrip("︎️").lstrip(" ")
    if not t.text and len(runs) > 1:   # the glyph's own run
        p.remove(runs[0])
        runs = runs[1:]
    if ppr is None:
        ppr = etree.Element(qn("a:pPr"))
        p.insert(0, ppr)
    for name in ("buClrTx", "buClr", "buNone", "buAutoNum", "buChar", "buBlip"):
        for old in ppr.findall(qn(f"a:{name}")):
            ppr.remove(old)
    kind = GLYPHS[glyph]
    clr = etree.Element(qn("a:buClr"))
    etree.SubElement(clr, qn("a:srgbClr")).set("val", livery_mod.hex(LIVERY, STATUS[kind]))
    ppr_place(ppr, clr)
    bu = etree.Element(qn("a:buChar"))
    bu.set("char", glyph)
    ppr_place(ppr, bu)
    if kind == "fail":   # the failed item's text muted
        for r in runs:
            set_fill(rpr(r), MUTED)
    return True


def run(prs, path: Path) -> None:
    n = 0
    for slide in prs.slides:
        for p in slide._element.iter(qn("a:p")):
            n += mark(p)
    if n:
        print(f"status_glyphs: {n} status item(s) → {path.name}")
