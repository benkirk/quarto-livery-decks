"""What the pptx steps share: the livery and the numbers every step reads from it, the shape and run
helpers each step wrote for itself, and the shape tests.

The livery is read once here (livery.load(): $LIVERY_DIR, exported by Make.common, else a `_livery`
link in the current directory) and every step imports it, so one deck's steps agree on it. The
constants are the canvas scale (K: absolute pads were drawn for the 540 pt canvas), the boxes and
geometry blocks of livery.json, the body type in points, and SLACK, the share a measured text
height is grown by so PowerPoint's autofit stays idle. measure.py holds the text measuring
(text_height); this module holds no measuring.
"""

from lxml import etree
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.oxml.ns import qn
from pptx.util import Emu

import livery as livery_mod

LIVERY = livery_mod.load()
K = livery_mod.canvas_scale(LIVERY)                # the canvas height over 540 pt: scales absolute pads
BOXES = LIVERY["boxes"]                            # the boxes' numbers, every format's (livery.json boxes)
GEOM = LIVERY["geometry"]
BODY_PT = livery_mod.type_pt(LIVERY, "body")       # pads are em of the body type
SLACK = 1.1                                        # measured height x this: autofit stays idle
NOT_BODY = {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.DATE,
            PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.SLIDE_NUMBER}
# a:pPr's children, in schema order: a bullet's elements go before the rest
PPR_ORDER = ["lnSpc", "spcBef", "spcAft", "buClrTx", "buClr", "buSzTx", "buSzPct", "buSzPts", "buFontTx", "buFont",
             "buNone", "buAutoNum", "buChar", "buBlip", "tabLst", "defRPr", "extLst"]


def is_body(shape) -> bool:
    """A body text placeholder (not the title, date, footer or number)."""
    return (shape.is_placeholder and shape.has_text_frame
            and shape.placeholder_format.type not in NOT_BODY)


def is_table(shape) -> bool:
    """A table's graphic frame."""
    return bool(getattr(shape, "has_table", False))


def is_picture(shape) -> bool:
    return shape.shape_type == MSO_SHAPE_TYPE.PICTURE


def rpr(run):
    """A run's a:rPr, made when it has none (a run without one inherits; sz and color need a home)."""
    el = run.find(qn("a:rPr"))
    if el is None:
        el = etree.Element(qn("a:rPr"))
        run.insert(0, el)
    return el


def set_fill(rpr_el, hexv: str) -> None:
    """The run's color: one a:solidFill of the six-digit hex, after a:ln when there is one."""
    for old in rpr_el.findall(qn("a:solidFill")):
        rpr_el.remove(old)
    fill = etree.Element(qn("a:solidFill"))
    etree.SubElement(fill, qn("a:srgbClr")).set("val", hexv)
    ln = rpr_el.find(qn("a:ln"))
    ln.addnext(fill) if ln is not None else rpr_el.insert(0, fill)


def ppr_place(ppr, el) -> None:
    """el into a:pPr at its schema position (PPR_ORDER)."""
    rank = PPR_ORDER.index(etree.QName(el).localname)
    for child in ppr:
        name = etree.QName(child).localname
        if name in PPR_ORDER and PPR_ORDER.index(name) > rank:
            child.addprevious(el)
            return
    ppr.append(el)


def rect(slide, x, y, w, h, hexv: str, name=None, behind=None):
    """A filled rectangle (EMU, a six-digit hex), no line or shadow; behind: a shape it goes under."""
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(x), Emu(y), Emu(w), Emu(h))
    r.fill.solid(); r.fill.fore_color.rgb = RGBColor.from_string(hexv)
    r.line.fill.background(); r.shadow.inherit = False
    if name:
        r.name = name
    if behind is not None:
        behind._element.addprevious(r._element)
    return r


def take_marker(slide, key):
    """The words of the slide's notes lines that start with key, those paragraphs removed (for
    engine-layout:, slide-layout.lua writes one, single-body.lua another for a note; columns.py
    reads grid-pptx.lua's engine-columns:). None when the slide has no such line."""
    if not slide.has_notes_slide:
        return None
    tf = slide.notes_slide.notes_text_frame
    if tf is None:
        return None
    words = None
    for p in tf.paragraphs:
        if p.text.strip().startswith(key):
            words = (words or []) + p.text.strip()[len(key):].split()
            body = p._p.getparent()
            body.remove(p._p)
            if body.find(qn("a:p")) is None:
                etree.SubElement(body, qn("a:p"))
    return words


def pads(box, key="pad"):
    """A box's pads, (vertical, horizontal) in EMU: its em times the body type."""
    v, h = BOXES[box][key]
    return Emu(round(v * BODY_PT * 12700)), Emu(round(h * BODY_PT * 12700))   # round: Pt() truncates 91439.99


def fit_table(shape, left, width):
    """A table's frame at left for width (EMU), its grid columns scaled to it in their shares
    (style_tables re-splits them inside the frame later); its top and height kept."""
    cols = shape.table._tbl.findall(qn("a:tblGrid") + "/" + qn("a:gridCol"))
    total = sum(int(c.get("w")) for c in cols)
    for c in cols:   # integers: a float makes PowerPoint repair the deck
        c.set("w", str(round(int(c.get("w")) * width / total)))
    shape.left, shape.top, shape.width, shape.height = Emu(left), shape.top, Emu(width), shape.height
