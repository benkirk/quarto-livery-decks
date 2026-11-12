"""A details slide's tab and its hidden flag ({.details}, livery.json boxes.details).

slide-layout.lua leaves a notes line of its own on a details slide, "engine-details: hide" or
"engine-details: show" (engine-common.lua's one reader of the deck's `details:`: hidden in the pptx
unless the deck says show). pandoc puts a slide's notes on the last slide it splits a body onto
(content after a table or picture), so the line marks that slide and every slide before it back to
the one holding the title: the halves of one source slide. This step runs before slide_layout for
that reason: a {.full} slide loses its title there.

The tab is one rectangle "Details tab" on the paper's left edge, from the body's top down, as HTML
and the PDF draw it: boxes.details.width wide, as long as its label (measured in the livery's bold
face, small capitals tracked by type.tracking) and the pad at each end, turned to read upward, the
label knocked out in the slide's background (a dark slide's field). Its fill is the box's role, a
dark slide's twin of it (common.palette()). It is a shape of its own, so the steps after this one
that lay a body out (a grid, a full figure, a caution box) never see it, and type_step scales its
label with the deck's sizes, as HTML and the PDF do. A hidden slide is `show="0"` on the slide: it
stays in the file, in order, and PowerPoint, Keynote and LibreOffice skip it in a slide show."""

from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

import livery as livery_mod

from . import measure
from .common import BOXES, GEOM, LIVERY, TRACKING, palette, style_runs, take_marker

KEY = "engine-details:"   # slide-layout.lua's notes line
TAB = "Details tab"       # the shape's name
D = BOXES["details"]


def tab_box(width, height):
    """The tab's frame as it shows, (left, top, width, length) in EMU: on the left edge, from the
    body's top, the label's measured length and a pad at each end."""
    pt, label = D["size"], D["label"].upper()
    text = measure.font(measure.BODY, 700, pt).getlength(label) * measure.PX + len(label) * TRACKING * Pt(pt)
    return 0, round(GEOM["body"][1] * height), round(D["width"] * width), round(text + 2 * D["pad"] * Pt(pt))


def draw(slide, width, height):
    """The tab on the slide, over everything on it; a second call leaves the first."""
    if any(sh.name == TAB for sh in slide.shapes):
        return
    ink = palette(slide)
    x, y, w, length = tab_box(width, height)
    # turned a quarter clockwise-less (rot 270: the text reads upward): OOXML frames a turned shape by
    # its unturned box about the same center, so the box is length wide and w tall
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(x + (w - length) // 2), Emu(y + (length - w) // 2), Emu(length), Emu(w))
    box.name = TAB
    box.rotation = 270
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor.from_string(ink.get(D["role"]) or livery_mod.hex(LIVERY, D["role"]))
    box.line.fill.background()
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.add_run().text = D["label"]
    style_runs(p._p, D["size"], bold=True, color=ink["background"], caps=True)
    bp = tf._txBody.find(qn("a:bodyPr"))   # never shrunk or grown: the tab is the livery's size
    for fit in [e for e in bp if e.tag in (qn("a:spAutoFit"), qn("a:normAutofit"), qn("a:noAutofit"))]:
        bp.remove(fit)


def run(prs, path: Path) -> None:
    """The open deck, changed in place; path for the message."""
    slides = list(prs.slides)
    marked = {}
    for i, slide in enumerate(slides):
        words = take_marker(slide, KEY)
        if words is None:
            continue
        marked[i] = words
        j = i
        while j > 0 and slides[j].shapes.title is None:   # pandoc's continuation of a split slide: back to its title
            j -= 1
            marked[j] = words
    hidden = 0
    for i, words in sorted(marked.items()):
        draw(slides[i], prs.slide_width, prs.slide_height)
        if "hide" in words:
            slides[i]._element.set("show", "0")
            hidden += 1
    if marked:
        print(f"details: {len(marked)} details slide(s), {hidden} hidden → {path.name}")
