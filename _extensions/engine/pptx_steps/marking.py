"""The marking strip (livery.yml marking:) on every slide of a deck.

Its text is the deck's `marking:` (pandoc records the string in docProps/custom.xml; `none` turns
the livery's default off), else the livery's `marking.text`; none, no strip. A text box in the
livery's box, over everything on the slide: no insets, the text centered on its height in the
type role's size and the text role's color, a solid fill behind it when the livery names one. The
template has no placeholder for it (pandoc fills none it does not know)."""

from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Pt

import livery as livery_mod

from .slide_layout import _custom_prop

LIVERY = livery_mod.load()
MARKING = LIVERY.get("marking") or {}
ALIGN = {"center": PP_ALIGN.CENTER, "left": PP_ALIGN.LEFT, "right": PP_ALIGN.RIGHT}


def _hex(value: str) -> str:
    """A role's or a hex's six digits."""
    return value.lstrip("#").upper() if value.startswith("#") else livery_mod.color(LIVERY, value)


def run(prs, name: str) -> None:
    deck = _custom_prop(prs, "marking")
    text = None if deck == "none" else deck or MARKING.get("text")
    if not text or not MARKING.get("box"):
        return
    x, y, w, h = MARKING["box"]
    W, H = prs.slide_width, prs.slide_height
    for slide in prs.slides:
        box = slide.shapes.add_textbox(int(x * W), int(y * H), int(w * W), int(h * H))
        box.name = "Marking"
        if MARKING.get("fill"):
            box.fill.solid()
            box.fill.fore_color.rgb = RGBColor.from_string(_hex(MARKING["fill"]))
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = ALIGN[MARKING.get("align", "center")]
        r = p.add_run()
        r.text = text
        r.font.size = Pt(livery_mod.type_pt(LIVERY, "marking"))
        r.font.color.rgb = RGBColor.from_string(_hex(MARKING.get("text-role", "muted")))
    print(f"marking: the marking strip on {len(prs.slides)} slide(s) → {name}")
