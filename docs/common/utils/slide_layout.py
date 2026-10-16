#!/usr/bin/env python3
"""Apply the theme's per-slide layout controls to a pandoc-rendered pptx.

pandoc drops slide classes, so common/slide-layout.lua leaves one speaker-notes line,
"engine-layout: vcenter scale=1.4", on each slide that asks for a layout; this removes the line
and applies what pptx can express. vcenter: body text anchored mid-placeholder, a table moved to
the middle of its area (an estimate: PowerPoint sizes rows itself). scale=S: every body and
table run at S times its inherited size. hcenter, fill: nothing (a text box cannot shrink-wrap).
caution: the body on the livery's caution-fill with a warning-colored bar at its left (footnotes
stay inside; pptx cannot move them). full: the one picture fills the slide, no title or master
art, pandoc's caption box centered under it in the muted color, the slide number kept.
feature: the brand cover, as the title slide with a `titlegraphic:` (pandoc records it in
docProps/custom.xml): the photo pushed to the back of the slide, cropped to cover, the livery's
field, band and wave lines over it, the text and logo on the field. Footnote paragraphs
(style_footnotes.py) keep their size. Idempotent: the marker is gone after one pass."""

import copy
import io
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Pt

import livery as livery_mod
import pptx_waves

LIVERY    = livery_mod.load()
MARKER    = "engine-layout:"
FOOTNOTES = ("†", "‡")
NOT_BODY  = {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.DATE,
             PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.SLIDE_NUMBER}
LINE      = 1.2           # line height / font size, for the table estimate
CELL_PAD  = Pt(7.2)       # a cell's default top + bottom margins (0.05 in each)
FULL_PAD   = LIVERY["geometry"]["full"]["pad"]       # full: margin round the figure (of the width),
FULL_FLOOR = LIVERY["geometry"]["full"]["floor"]     # the footline (slide number) and the caption
FULL_CAP   = LIVERY["geometry"]["full"]["caption"]   # line (of the height), as the themes draw them
CAP_SIZE   = Pt(13)       # style_footnotes.py's size and color: the livery's muted text
CAP_COLOR  = RGBColor.from_string(livery_mod.color(LIVERY, "muted"))
CAUTION_FILL = RGBColor.from_string(livery_mod.derived(LIVERY, "caution-fill"))  # warning at 18% on white
# the warning role, not the accent5 slot: the ncar template's accent5 (FDD509) is not brand yellow
CAUTION_BAR  = RGBColor.from_string(livery_mod.color(LIVERY, "warning"))
CAUTION_W    = Pt(6)
GEOM         = LIVERY["geometry"]
WAVES        = LIVERY.get("art", {}).get("waves")
FIELD_TEXT   = RGBColor.from_string(livery_mod.color(LIVERY, "primary-text"))
# the feature cover's text on the field, of the slide: title (top, height, pt), rule, body
COVER_TITLE, COVER_RULE, COVER_BODY = (0.34, 0.16, 32), 0.525, (0.55, 0.36, 18)


def _take_marker(slide):
    """The slide's layout words, with their notes paragraph removed."""
    if not slide.has_notes_slide:
        return None
    tf = slide.notes_slide.notes_text_frame
    if tf is None:
        return None
    for p in tf.paragraphs:
        if p.text.strip().startswith(MARKER):
            words = p.text.strip()[len(MARKER):].split()
            body = p._p.getparent()
            body.remove(p._p)
            if body.find(qn("a:p")) is None:
                etree.SubElement(body, qn("a:p"))
            return words
    return None


def _lvl_size(txstyle, level):
    """sz (hundredths of a point) for a paragraph level in a list-style element."""
    if txstyle is None:
        return None
    lvl = txstyle.find(qn(f"a:lvl{level + 1}pPr"))
    rpr = lvl.find(qn("a:defRPr")) if lvl is not None else None
    return int(rpr.get("sz")) if rpr is not None and rpr.get("sz") else None


def _inherited(shape, slide, level):
    """A body placeholder's size at a level: its layout's lstStyle, then the master."""
    try:
        idx = shape.placeholder_format.idx
        lph = slide.slide_layout.placeholders.get(idx=idx)
    except (KeyError, ValueError, AttributeError):
        lph = None
    if lph is not None:
        sz = _lvl_size(lph._element.find(".//" + qn("a:lstStyle")), level)
        if sz:
            return sz
    master = slide.slide_layout.slide_master._element
    return _lvl_size(master.find(".//" + qn("p:bodyStyle")), level) or 1800


def _other_size(slide):
    master = slide.slide_layout.slide_master._element
    return _lvl_size(master.find(".//" + qn("p:otherStyle")), 0) or 1800


def _scale_paragraphs(paragraphs, scale, size_at):
    for p in paragraphs:
        if p.text.lstrip().startswith(FOOTNOTES):
            continue
        base = size_at(p.level)
        for r in p._p.iter(qn("a:rPr"), qn("a:endParaRPr")):
            sz = int(r.get("sz")) if r.get("sz") else base
            r.set("sz", str(round(sz * scale)))


def _is_body(shape):
    return (shape.is_placeholder and shape.has_text_frame
            and shape.placeholder_format.type not in NOT_BODY)


def _text_height(shape, slide):
    """An estimate of the text's height: characters per line from the font size (half an em
    each), one LINE per line plus a little paragraph spacing."""
    tf = shape.text_frame
    width = shape.width - tf.margin_left - tf.margin_right - Pt(18)   # less the bullet indent
    total = tf.margin_top + tf.margin_bottom
    for p in tf.paragraphs:
        sized = [r.font.size for r in p.runs if r.font.size]
        size = sized[0] if sized else Pt(_inherited(shape, slide, p.level) / 100)
        per_line = max(1, int(width / (size * 0.5)))
        lines = max(1, -(-len(p.text) // per_line))
        total += int(lines * size * LINE) + Pt(6)
    return total


def caution_box(slide, shape, vcenter):
    """The body text box on the soft yellow field, a brand-yellow bar at its left, cut down to
    about its text (pandoc gives it the whole content area); 10% slack keeps autofit idle."""
    tf = shape.text_frame
    tf.margin_left = tf.margin_right = Pt(14)
    tf.margin_top = tf.margin_bottom = Pt(8)
    left, top, width, height = shape.left, shape.top, shape.width, shape.height
    est = int(_text_height(shape, slide) * 1.1)
    if est < height:
        if vcenter:
            top += (height - est) // 2
        height = est
    # all four: a placeholder inherits its frame, and setting one leaves the rest at 0
    shape.left, shape.top, shape.width, shape.height = left, top, width, height
    shape.fill.solid()
    shape.fill.fore_color.rgb = CAUTION_FILL
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, shape.left, shape.top, CAUTION_W, shape.height)
    bar.fill.solid()
    bar.fill.fore_color.rgb = CAUTION_BAR
    bar.line.fill.background()
    bar.shadow.inherit = False


def lay_out(slide, words):
    scale = 1.0
    for w in words:
        if w.startswith("scale="):
            try:
                scale = float(w[len("scale="):])
            except ValueError:
                pass
    vcenter = "vcenter" in words
    if "caution" in words:
        for shape in [sh for sh in slide.shapes if _is_body(sh)]:
            caution_box(slide, shape, vcenter)
    for shape in slide.shapes:
        if _is_body(shape):
            if scale != 1.0:
                # runs without an rPr inherit too: give each one, so sz has a home
                for r in shape.text_frame._txBody.iter(qn("a:r")):
                    if r.find(qn("a:rPr")) is None:
                        r.insert(0, etree.Element(qn("a:rPr")))
                _scale_paragraphs(shape.text_frame.paragraphs, scale,
                                  lambda lvl, s=shape: _inherited(s, slide, lvl))
            if vcenter:
                shape.text_frame._txBody.find(qn("a:bodyPr")).set("anchor", "ctr")
        elif getattr(shape, "has_table", False):
            other = _other_size(slide)
            rows = list(shape.table.rows)
            biggest = other
            for row in rows:
                for cell in row.cells:
                    tf = cell.text_frame
                    if scale != 1.0:
                        for r in tf._txBody.iter(qn("a:r")):
                            if r.find(qn("a:rPr")) is None:
                                r.insert(0, etree.Element(qn("a:rPr")))
                        _scale_paragraphs(tf.paragraphs, scale, lambda lvl: other)
                    for r in tf._txBody.iter(qn("a:rPr")):
                        if r.get("sz"):
                            biggest = max(biggest, int(r.get("sz")))
            if vcenter and rows:
                est = int(len(rows) * (Pt(biggest / 100) * LINE + CELL_PAD))
                if est < shape.height:
                    shape.top = shape.top + (shape.height - est) // 2
                    shape.height = est


def full_slide(slide, width, height):
    """One picture over the whole slide; False (slide untouched) for any other body."""
    pics = [sh for sh in slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]
    texts = [sh for sh in slide.shapes if _is_body(sh)]
    if len(pics) != 1 or len(texts) > 1:
        return False
    pic, caption = pics[0], (texts[0] if texts else None)
    slide._element.set("showMasterSp", "0")
    title = slide.shapes.title
    if title is not None:
        title._element.getparent().remove(title._element)
    pad, floor = int(FULL_PAD * width), int(FULL_FLOOR * height)
    if caption is not None:
        cap = int(FULL_CAP * height)
        caption.left, caption.width = pad, width - 2 * pad
        caption.top, caption.height = height - floor - cap, cap
        tf = caption.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for p in tf.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size, r.font.color.rgb = CAP_SIZE, CAP_COLOR
        floor += cap
    box_w, box_h = width - 2 * pad, height - pad - floor
    iw, ih = pic.image.size
    k = min(box_w / iw, box_h / ih)
    pic.width, pic.height = int(iw * k), int(ih * k)
    pic.left = pad + (box_w - pic.width) // 2
    pic.top = pad + (box_h - pic.height) // 2
    return True


def _title_graphic(prs, deck_dir):
    """The deck's `titlegraphic:` path from docProps/custom.xml, or None."""
    for part in prs.part.package.iter_parts():
        if str(part.partname) == "/docProps/custom.xml":
            for prop in etree.fromstring(part.blob):
                if prop.get("name") == "titlegraphic":
                    value = "".join(prop.itertext()).strip()
                    return deck_dir / value if value else None
    return None


def _background_photo(slide):
    """The bytes of pandoc's `background-image` (a slide <p:bg> blip), removed; or None."""
    csld = slide._element.find(qn("p:cSld"))
    bg = csld.find(qn("p:bg"))
    blip = bg.find(".//" + qn("a:blip")) if bg is not None else None
    if blip is None:
        return None
    blob = slide.part.related_part(blip.get(qn("r:embed"))).blob
    csld.remove(bg)
    return blob


def _frame(shape, x, y, w, h, width, height):
    """All four of a placeholder's frame, in slide fractions (setting one leaves the rest at 0)."""
    shape.left, shape.top = int(x * width), int(y * height)
    shape.width, shape.height = int(w * width), int(h * height)


def cover(slide, width, height, photo):
    """The brand cover: the photo at the back, cropped to cover the slide, the field, band and
    wave lines over it (pptx_waves), the dark logo top left. Returns the next free shape id."""
    tree = slide.shapes._spTree
    pic = slide.shapes.add_picture(io.BytesIO(photo), 0, 0, width, height)
    iw, ih = pic.image.size
    if iw * height > ih * width:
        pic.crop_left = pic.crop_right = (1 - (width / height) / (iw / ih)) / 2
    else:
        pic.crop_top = pic.crop_bottom = (1 - (iw / ih) / (width / height)) / 2
    tree.remove(pic._element)
    tree.insert(2, pic._element)   # after nvGrpSpPr and grpSpPr: the back of the slide
    sid = max(int(e.get("id")) for e in tree.iter(qn("p:cNvPr"))) + 1
    if WAVES:
        for i, xml in enumerate(pptx_waves.cover_shapes(WAVES["lines"], sid, width, height)):
            tree.insert(3 + i, etree.fromstring(xml))
            sid += 1
    logo_h = GEOM["logo"].get("title", 0.09)
    logo = slide.shapes.add_picture(str(Path(LIVERY["dir"]) / livery_mod.logo_path(LIVERY, "dark")),
                                    int(GEOM["margin"] * width), int(0.06 * height), height=int(logo_h * height))
    logo.name = "Logo (dark)"
    return sid


def title_cover(slide, width, height, photo):
    """The title slide over its photo: the layout's tab and rule (hidden by the photo) are copied
    onto the slide; its placeholders already sit on top."""
    cover(slide, width, height, photo)
    tree = slide.shapes._spTree
    for sp in slide.slide_layout.shapes:
        if sp.is_placeholder or sp.shape_type == MSO_SHAPE_TYPE.PICTURE or sp.name.startswith("Wave "):
            continue
        tree.append(copy.deepcopy(sp._element))


def _field_text(shape, pt):
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            r.font.size, r.font.color.rgb = Pt(pt), FIELD_TEXT


def feature_cover(slide, width, height, photo):
    """A {.feature} slide as a cover: title and body on the field, in the title slide's manner."""
    cover(slide, width, height, photo)
    slide._element.set("showMasterSp", "0")
    m, w = GEOM["margin"], 0.44
    tab = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, int(COVER_TITLE[0] * height),
                                 int(GEOM["tab"] * width), int(COVER_TITLE[1] * height))
    tab.fill.solid(); tab.fill.fore_color.rgb = RGBColor.from_string(livery_mod.scheme(LIVERY, "accent4"))
    tab.line.fill.background(); tab.shadow.inherit = False
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, int(m * width), int(COVER_RULE * height),
                                  int(0.065 * width), int(1.5 * width / 1600))
    rule.fill.solid(); rule.fill.fore_color.rgb = RGBColor.from_string(livery_mod.scheme(LIVERY, "accent1"))
    rule.line.fill.background(); rule.shadow.inherit = False
    title = slide.shapes.title
    if title is not None:
        _frame(title, m, COVER_TITLE[0], w, COVER_TITLE[1], width, height)
        title.text_frame.vertical_anchor = MSO_ANCHOR.TOP
        _field_text(title, COVER_TITLE[2])
    for shape in [sh for sh in slide.shapes if _is_body(sh)]:
        _frame(shape, m, COVER_BODY[0], w, COVER_BODY[1], width, height)
        _field_text(shape, COVER_BODY[2])


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: slide_layout.py <file.pptx>", file=sys.stderr)
        return 2
    pptx = Path(sys.argv[1]).resolve()
    if not pptx.exists():
        print(f"error: {pptx} not found", file=sys.stderr)
        return 2

    prs = Presentation(str(pptx))
    w, h = prs.slide_width, prs.slide_height
    done = 0
    graphic = _title_graphic(prs, pptx.parent)
    if graphic is not None and len(prs.slides) and prs.slides[0].slide_layout.name == "Title Slide":
        if graphic.exists():
            title_cover(prs.slides[0], w, h, graphic.read_bytes())
            done += 1
        else:
            print(f"slide_layout: WARNING: titlegraphic {graphic} not found", file=sys.stderr)
    for slide in prs.slides:
        words = _take_marker(slide)
        if words is None:
            continue
        if "feature" in words:
            photo = _background_photo(slide)
            if photo is None:
                print("slide_layout: WARNING: {.feature} slide without a background-image; left as it is",
                      file=sys.stderr)
            else:
                feature_cover(slide, w, h, photo)
        elif "full" in words:
            if not full_slide(slide, w, h):
                title = slide.shapes.title
                print("slide_layout: WARNING: {.full} slide %r needs one picture and at most a "
                      "caption; left as it is" % (title.text_frame.text if title else ""),
                      file=sys.stderr)
        else:
            lay_out(slide, words)
        done += 1
    prs.save(str(pptx))
    print(f"slide_layout: laid out {done} slide(s) → {pptx.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
