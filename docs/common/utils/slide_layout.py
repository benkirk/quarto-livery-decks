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
closing: the slide moves onto the template's Closing layout (Closing (light) under themeoptions
title=light, which slide-layout.lua records as `engine-title: light` and which also moves the
title slide onto Title Slide (light); a band title ignores it), its placeholders dropping pandoc's
copied frames to take the layout's. The title slide with a `titlegraphic:` (docProps/custom.xml;
else the livery's art.titlegraphic) is drawn from its composition (livery.json compositions):
the photo at the back, cropped to cover its box, the field and waves over it, the marks in their
boxes; the band takes the photo into its box over the layout's default. feature: by the
livery's feature.style, the photo under a dark bar with the title and the body on a panel, or the
cover with the title and body in its column. Footnote paragraphs
(style_footnotes.py) keep their size. Every slide also gets its layout's slide-number placeholder, which pandoc never writes
(so decks had no numbers). Idempotent: the marker is gone after one pass, a slide that has a
number keeps it."""

import copy
import io
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Pt

import livery as livery_mod

pptx_waves = livery_mod.engine_module("pptx_waves")   # shared with the engine's template builder

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
CAP_SIZE   = Pt(round(livery_mod.type_pt(LIVERY, "caption"), 1))   # the themes' caption size, the muted color
CAP_COLOR  = RGBColor.from_string(livery_mod.color(LIVERY, "muted"))
CAUTION_FILL = RGBColor.from_string(livery_mod.derived(LIVERY, "caution-fill"))  # warning at 18% on white
# the warning role, not the accent5 slot: the ncar template's accent5 (FDD509) is not brand yellow
CAUTION_BAR  = RGBColor.from_string(livery_mod.color(LIVERY, "warning"))
CAUTION_W    = Pt(6)
GEOM         = LIVERY["geometry"]
WAVES        = LIVERY.get("art", {}).get("waves")
BAND         = (LIVERY.get("title") or {}).get("style") == "band"
COMP         = LIVERY["compositions"]   # the title, closing, section and feature slides as boxes


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


def _custom_prop(prs, name):
    """A metadata string pandoc recorded in docProps/custom.xml, or None."""
    for part in prs.part.package.iter_parts():
        if str(part.partname) == "/docProps/custom.xml":
            for prop in etree.fromstring(part.blob):
                if prop.get("name") == name:
                    return "".join(prop.itertext()).strip() or None
    return None


def _title_graphic(prs, deck_dir):
    """The deck's `titlegraphic:` path from docProps/custom.xml, or None."""
    value = _custom_prop(prs, "titlegraphic")
    return deck_dir / value if value else None


def use_layout(prs, slide, name):
    """Point the slide at the named layout; its placeholders lose the frames pandoc copied from
    the old one and take the new layout's. False when the template has no such layout."""
    layout = next((l for l in prs.slide_layouts if l.name == name), None)
    if layout is None:
        return False
    for rel in slide.part.rels.values():
        if rel.reltype == RT.SLIDE_LAYOUT:
            rel._target = layout.part
            for cached in ("target_part", "target_ref"):   # python-pptx lazyproperties: drop the old layout's
                rel.__dict__.pop(cached, None)
    for sh in slide.placeholders:
        xfrm = sh._element.spPr.find(qn("a:xfrm"))
        if xfrm is not None:
            sh._element.spPr.remove(xfrm)
    return True


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


def _back_picture(slide, photo, x, y, w, h):
    """The photo cropped to cover the box, at the back of the slide (above the layout's shapes)."""
    tree = slide.shapes._spTree
    pic = slide.shapes.add_picture(io.BytesIO(photo), x, y, w, h)
    iw, ih = pic.image.size
    if iw * h > ih * w:
        pic.crop_left = pic.crop_right = (1 - (w / h) / (iw / ih)) / 2
    else:
        pic.crop_top = pic.crop_bottom = (1 - (iw / ih) / (w / h)) / 2
    tree.remove(pic._element)
    tree.insert(2, pic._element)   # after nvGrpSpPr and grpSpPr: the back of the slide
    return pic


def band_photo(slide, width, height, photo):
    """The band title's photo in its box (title-band.photo); nothing else sits there."""
    x, y, w, h = COMP["title-band"]["photo"]["box"]
    _back_picture(slide, photo, int(x * width), int(y * height), int(w * width), int(h * height)).name = "Title photo"


def band_date(slide, width, height):
    """The band's title stack is centred on its rule; the date goes just above the title's text
    (an estimate of its height), not at the column's top, so a short title leaves no gap."""
    title = next((sh for sh in slide.placeholders if sh.placeholder_format.type == PP_PLACEHOLDER.CENTER_TITLE), None)
    date = next((sh for sh in slide.placeholders if sh.placeholder_format.type == PP_PLACEHOLDER.DATE), None)
    if title is None or date is None:
        return
    x, y, w, h = COMP["title-band"]["column"]["box"]
    text_top = int((y + h / 2 - 0.015) * height) - _text_height(title, slide)
    dh = int(0.04 * height)
    date.left, date.top, date.width, date.height = int(x * width), max(int(y * height), text_top - dh - int(0.01 * height)), int(w * width), dh


def _role(role):
    return RGBColor.from_string(livery_mod.color(LIVERY, role))


def _box_picture(slide, path, box, width, height, name):
    x, y, w, h = box
    pic = slide.shapes.add_picture(str(path), int(x * width), int(y * height), int(w * width), int(h * height))
    pic.name = name
    return pic


def draw_cover(slide, width, height, photo, comp):
    """A composition with a photo (the title's, or the feature cover): the photo at the back,
    cropped to cover its box, the field and waves over it (pptx_waves.comp_shapes), the mark and
    sign-off in their boxes. Returns the next free shape id."""
    tree = slide.shapes._spTree
    x, y, w, h = comp["photo"]["box"]
    _back_picture(slide, photo, int(x * width), int(y * height), int(w * width), int(h * height)).name = "Photo"
    sid = max(int(e.get("id")) for e in tree.iter(qn("p:cNvPr"))) + 1
    slot = pptx_waves.ROLE_SLOT[comp["field"]["role"]]
    shapes = pptx_waves.comp_shapes(WAVES and WAVES["lines"], comp, sid, width, height, field_slot=slot,
                                    line_slot=pptx_waves.ROLE_SLOT[comp["waves"]["role"]] if comp["waves"] else "accent1")
    for i, xml in enumerate(shapes):
        tree.insert(3 + i, etree.fromstring(xml))
        sid += 1
    for key, kind, name in (("mark", "logo", "Logo"), ("signoff", "signoff", "Sign-off")):
        if comp[key]:
            _box_picture(slide, Path(LIVERY["dir"]) / livery_mod.mark(LIVERY, comp[key]["role"], kind),
                         comp[key]["box"], width, height, f"{name} ({comp[key]['role']})")
    return sid


def title_cover(slide, width, height, photo):
    """The title slide over its photo: its composition (title-photo, or -light on Title Slide
    (light)); the layout's tab and rule (hidden by the photo) are copied onto the slide."""
    light = slide.slide_layout.name == "Title Slide (light)"
    draw_cover(slide, width, height, photo, COMP["title-photo-light" if light else "title-photo"])
    tree = slide.shapes._spTree
    for sp in slide.slide_layout.shapes:
        if sp.is_placeholder or sp.shape_type == MSO_SHAPE_TYPE.PICTURE or sp.name.startswith("Wave "):
            continue
        tree.append(copy.deepcopy(sp._element))


def _text(shape, color, pt=None):
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            r.font.color.rgb = color
            if pt:
                r.font.size = Pt(pt)


def _rect(slide, box, width, height, color, alpha=None, name=None):
    """A filled rectangle at a box; alpha (0-1) written as <a:alpha>, which python-pptx lacks."""
    x, y, w, h = box
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, int(x * width), int(y * height), int(w * width), int(h * height))
    r.fill.solid(); r.fill.fore_color.rgb = color
    if alpha is not None:
        clr = r.fill._xPr.find(qn("a:solidFill"))[0]
        etree.SubElement(clr, qn("a:alpha")).set("val", str(round(alpha * 100000)))
    r.line.fill.background(); r.shadow.inherit = False
    if name:
        r.name = name
    return r


def draw_feature(slide, width, height, photo):
    """A {.feature} slide by feature.style: bar (the photo full, the title in the column on the
    dark bar, the body on the panel cut to its text) or cover (draw_cover, the title, rule and
    body in the column). No master shapes either way."""
    c = COMP["feature"]
    slide._element.set("showMasterSp", "0")
    title, body = slide.shapes.title, [sh for sh in slide.shapes if _is_body(sh)]
    x, y, w, h = c["column"]["box"]
    text = _role(c["column"]["role"])
    if c["bar"]:
        _back_picture(slide, photo, 0, 0, width, height).name = "Photo"
        bar = _rect(slide, c["bar"]["box"], width, height, _role(c["bar"]["role"]), c["bar"]["opacity"], "Feature bar")
        tree = slide.shapes._spTree
        tree.remove(bar._element); tree.insert(3, bar._element)   # over the photo, under the text
        for sh in slide.placeholders:   # the number on the photo, white as HTML's
            if sh.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
                for para in sh.text_frame.paragraphs:
                    para.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        if title is not None:
            _frame(title, x, y, w, h, width, height)
            title.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE if c["column"]["anchor"] == "middle" else MSO_ANCHOR.TOP
            _text(title, text)
        px, py, pw, ph = c["panel"]["box"]
        for shape in body:
            _frame(shape, px, py, pw, ph, width, height)
            tf = shape.text_frame
            tf.margin_left = tf.margin_right = Pt(14); tf.margin_top = tf.margin_bottom = Pt(10)
            est = min(int(_text_height(shape, slide) * 1.1), int(ph * height))
            panel = _rect(slide, [px, py, pw, est / height], width, height, _role(c["panel"]["role"]), c["panel"]["opacity"], "Feature panel")
            tree = slide.shapes._spTree
            tree.remove(panel._element); tree.insert(list(tree).index(shape._element), panel._element)
            shape.height = est
            _text(shape, RGBColor(0xFF, 0xFF, 0xFF))
    else:
        draw_cover(slide, width, height, photo, c)
        if c["column"]["tab"]:
            _rect(slide, [0, y, GEOM["tab"], 0.16], width, height, RGBColor.from_string(livery_mod.scheme(LIVERY, "accent4")), name="Title tab")
        if c["column"]["rule"]:
            _rect(slide, [x, y + 0.185, c["column"]["rule"][0], c["column"]["rule"][1]], width, height,
                  RGBColor.from_string(livery_mod.scheme(LIVERY, "accent1")), name="Title rule")
        if title is not None:
            _frame(title, x, y, w, 0.16, width, height)
            title.text_frame.vertical_anchor = MSO_ANCHOR.TOP
            _text(title, text, round(livery_mod.type_pt(LIVERY, "frametitle"), 1))
        for shape in body:
            _frame(shape, x, y + 0.21, w, h - 0.21, width, height)
            _text(shape, text, round(livery_mod.type_pt(LIVERY, "body"), 1))


def add_slide_number(slide):
    """The layout's slide-number placeholder, copied onto the slide (pandoc leaves it out)."""
    for sh in slide.placeholders:
        if sh.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
            return False
    for sh in slide.slide_layout.placeholders:
        if sh.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
            el = copy.deepcopy(sh._element)
            for e in el.iter(qn("p:cNvPr")):
                e.set("id", str(max(int(c.get("id")) for c in slide.shapes._spTree.iter(qn("p:cNvPr"))) + 1))
            slide.shapes._spTree.append(el)
            return True
    return False


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
    light = _custom_prop(prs, "engine-title") == "light"
    if light and BAND:
        print("slide_layout: WARNING: themeoptions title=light is ignored under the livery's band title", file=sys.stderr)
        light = False
    if light and len(prs.slides) and prs.slides[0].slide_layout.name == "Title Slide":
        if not use_layout(prs, prs.slides[0], "Title Slide (light)"):
            print("slide_layout: WARNING: title=light, but the template has no Title Slide (light)", file=sys.stderr)
    graphic = _title_graphic(prs, pptx.parent)
    default = LIVERY.get("art", {}).get("titlegraphic")
    if graphic is None and default and not BAND:   # the band's layout carries the default itself
        graphic = Path(LIVERY["dir"]) / default
    if graphic is not None and len(prs.slides) and prs.slides[0].slide_layout.name.startswith("Title Slide"):
        if graphic.exists():
            (band_photo if BAND else title_cover)(prs.slides[0], w, h, graphic.read_bytes())
            done += 1
        else:
            print(f"slide_layout: WARNING: titlegraphic {graphic} not found", file=sys.stderr)
    markers = [_take_marker(slide) for slide in prs.slides]
    for slide, words in zip(prs.slides, markers):   # before numbering: the number is the new layout's
        if words and "closing" in words:
            if use_layout(prs, slide, "Closing (light)" if light else "Closing"):
                words.remove("closing")
            else:
                print("slide_layout: WARNING: {.closing} slide, but the template has no Closing layout", file=sys.stderr)
    numbered = sum(add_slide_number(slide) for slide in prs.slides)
    for slide, words in zip(prs.slides, markers):
        if words is None:
            continue
        if not words or words == ["closing"]:   # a closing slide with nothing else to do
            done += 1
            continue
        if "feature" in words:
            photo = _background_photo(slide)
            if photo is None:
                print("slide_layout: WARNING: {.feature} slide without a background-image; left as it is",
                      file=sys.stderr)
            else:
                draw_feature(slide, w, h, photo)
        elif "full" in words:
            if not full_slide(slide, w, h):
                title = slide.shapes.title
                print("slide_layout: WARNING: {.full} slide %r needs one picture and at most a "
                      "caption; left as it is" % (title.text_frame.text if title else ""),
                      file=sys.stderr)
        else:
            lay_out(slide, words)
        done += 1
    if BAND and len(prs.slides) and prs.slides[0].slide_layout.name == "Title Slide":   # after any re-framing
        band_date(prs.slides[0], w, h)
    prs.save(str(pptx))
    print(f"slide_layout: laid out {done} slide(s), numbered {numbered} → {pptx.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
