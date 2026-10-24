"""A picture in a grid column or a card, drawn from grid-pptx.lua's markers (grid.py hands it the item).

grid-pptx.lua writes a picture in a flattened column or a card (engine-common.lua's cell_figure()) as
`⟦engine:picture src=<path>[ data=<base64>][ size=<width>]⟧`, its caption a paragraph, `⟦engine:end⟧`:
text, so pandoc embeds no picture and nothing splits. The bytes are data='s when it is there (an
executed cell's plot or a baked diagram, gone from disk by now), else the file at src (percent-encoded
as a gallery item's), relative to the deck's directory; an .svg rasterized to a PNG (no svgBlip twin,
as the gallery's). The picture is the column's width (a sized one its width=: a percentage of the
column, or a length), its aspect kept, centered, and no taller than the room less its caption; the
caption under it in the caption look (the caption size, muted, centered), boxes.note.gap em of the
caption type below the picture, as a ::: note under a figure. "<name>" and "<name> caption". A
missing file warns and draws nothing (its caption stays text).
"""

import base64
import re
import sys
from urllib.parse import unquote

from pptx.parts.image import Image
from pptx.util import Emu

from .common import BOXES, CAPTION_PT, SLACK, body_box, caption_para, em, fit_picture, slide_title
from .measure import text_height
from .svg_fallback import DPI, rasterize_svg   # an .svg's PNG at the deck's fig-dpi

EMU_PER = {"in": 914400, "cm": 360000, "mm": 36000, "pt": 12700, "px": 9525, "": 9525}   # pandoc's bare number: pixels
SIZE = re.compile(r"^([\d.]+)\s*(%|in|cm|mm|pt|px|)$")


def width_of(size, w):
    """A sized picture's width in EMU (a percentage of w, or a length), at most w; None when size is
    not one of those."""
    m = SIZE.match((size or "").strip())
    if m is None:
        return None
    v, unit = float(m.group(1)), m.group(2)
    return min(w, round(w * v / 100 if unit == "%" else v * EMU_PER[unit]))


def picture_bytes(attrs, deck_dir, slide):
    """A picture marker's image bytes (a PNG for an .svg), or None (warned of)."""
    src = unquote(attrs.get("src", ""))
    if attrs.get("data"):
        data = base64.b64decode(attrs["data"])
    else:
        path = deck_dir / src
        if not path.is_file():
            print(f"figures: WARNING: slide {slide_title(slide)!r}: {path} not found; the picture is not drawn", file=sys.stderr)
            return None
        data = path.read_bytes()
    return rasterize_svg(data, DPI) if src.lower().endswith(".svg") else data


def draw_picture(slide, x, y, w, room, attrs, caption, deck_dir, name):
    """The picture of a marker's attrs at (x, y) in a column w wide, the caption paragraphs under it,
    the two no taller than room: (picture, caption box or None, height) or None when there is no
    picture to draw."""
    data = picture_bytes(attrs, deck_dir, slide)
    if data is None:
        return None
    iw, ih = Image.from_blob(data).size
    cb, cap_h = None, 0
    if caption:
        for p in caption:
            caption_para(p)
        cb = body_box(slide, x, y, w, room, caption, f"{name} caption")
        tf = cb.text_frame
        tf.margin_top, tf.margin_bottom, tf.margin_left, tf.margin_right = em(BOXES["note"]["gap"], CAPTION_PT), 0, 0, 0
        cap_h = int(text_height(cb, slide, gap=0) * SLACK)
    pw = width_of(attrs.get("size"), w) or w
    ph = round(pw * ih / iw)
    if ph > room - cap_h:   # too tall: the room's height, narrower at its aspect
        ph = max(room - cap_h, 1)
        pw = max(round(ph * iw / ih), 1)
    pic = fit_picture(slide, data, x + (w - pw) // 2, y, pw, ph, "contain", name=name)
    if cb is not None:
        cb._element.addprevious(pic._element)   # the picture first in the stacking: a card's fill goes behind it
        cb.left, cb.top, cb.width, cb.height = Emu(x), Emu(y + ph), Emu(w), Emu(cap_h)
    return pic, cb, ph + cap_h


def shrink_picture(pic, cb, by):
    """A drawn picture by EMU shorter (its aspect kept, centered where it was; its caption raised
    under it): what a column or card gives up when its text needs the room."""
    if by <= 0:
        return
    k = max(pic.height - by, 1) / pic.height
    middle = pic.left + pic.width // 2
    pic.width, pic.height = Emu(max(round(pic.width * k), 1)), Emu(max(pic.height - by, 1))
    pic.left = Emu(middle - pic.width // 2)
    if cb is not None:
        cb.top = Emu(pic.top + pic.height)


def place_picture(pic, cb, top):
    """A picture and its caption moved to top."""
    pic.top = Emu(top)
    if cb is not None:
        cb.top = Emu(top + pic.height)
