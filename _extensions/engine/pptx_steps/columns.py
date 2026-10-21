"""A two-column slide's columns at their widths and the livery's gap, as HTML and PDF lay them out.

pandoc's pptx writer puts a `.columns` div's two columns into the Two Content layout's placeholders,
each the template's half width, and drops their `width=`. grid-pptx.lua leaves the shares on a
notes line, `engine-columns: 0.55 0.45` (`wide` added on a `{.wide}` slide); this reads and
deletes the line and frames the columns: the content box is the slide less the margin a side
(geometry.wide-margin on a wide slide), each column its share of the box less the gaps
(boxes.columns.gap), x_1 at the margin and each next one a gap after the last. Text placeholders
take the frame (all four fields: a placeholder inherits its frame, and setting one leaves the
others at 0). A picture or table pandoc placed in a column moves with it: a picture as wide as the
old column scales to the new one (its aspect kept, no taller than the column), a narrower one only
shrinks if it no longer fits, centered either way; a table takes the column's width, its grid
columns scaled to it (style_tables then re-splits them inside it). Idempotent: the line is gone
after one pass. After slide_layout (which leaves a columns slide's frames to this), before
style_tables and type_step.
"""

from pptx.oxml.ns import qn
from pptx.util import Emu

from .slide_layout import BOXES, GEOM, take_marker

KEY = "engine-columns:"


def frames(shares, width, wide=False):
    """(left, width) in EMU of each column, for shares of the content box less its gaps."""
    m, g = GEOM["wide-margin" if wide else "margin"], BOXES["columns"]["gap"]
    room, x, out = 1 - 2 * m - g * (len(shares) - 1), m, []
    for s in shares:
        out.append((Emu(round(x * width)), Emu(round(room * s * width))))
        x += room * s + g
    return out


def _old(width):
    """The template's two half frames (livery_template.py's Two Content), (left, width) in EMU."""
    m, g = GEOM["margin"], BOXES["columns"]["gap"]
    half = (1 - 2 * m - g) / 2
    return [(round(m * width), round(half * width)), (round((m + half + g) * width), round(half * width))]


def _column_of(shape, old):
    """The old column a shape sits in, by its center."""
    c = shape.left + shape.width // 2
    return min(range(len(old)), key=lambda i: abs(old[i][0] + old[i][1] // 2 - c))


def frame_slide(slide, words, width):
    try:
        shares = [float(w) for w in words if w != "wide"]
    except ValueError:
        return False
    if len(shares) != 2:
        return False
    new, old = frames(shares, width, "wide" in words), _old(width)
    area = {}   # each column's top and height, from its placeholder (the layout's when inherited)
    for sh in slide.placeholders:
        idx = sh.placeholder_format.idx
        if idx in (1, 2) and sh.has_text_frame:
            x, w = new[idx - 1]
            sh.left, sh.top, sh.width, sh.height = x, sh.top, w, sh.height
    for ph in slide.slide_layout.placeholders:
        if ph.placeholder_format.idx in (1, 2):
            area[ph.placeholder_format.idx - 1] = (ph.top, ph.height)
    for sh in slide.shapes:
        table = getattr(sh, "has_table", False) and sh.has_table
        if not (table or sh.shape_type == 13):   # 13: a picture
            continue
        i = _column_of(sh, old)
        x, w = new[i]
        if table:
            cols = sh.table._tbl.findall(qn("a:tblGrid") + "/" + qn("a:gridCol"))
            total = sum(int(c.get("w")) for c in cols)
            for c in cols:   # integers: a float makes PowerPoint repair the deck
                c.set("w", str(round(int(c.get("w")) * w / total)))
            sh.left, sh.top, sh.width, sh.height = x, sh.top, w, sh.height
            continue
        top, height = area.get(i, (sh.top, sh.height))
        k = w / sh.width if abs(sh.width - old[i][1]) <= old[i][1] * 0.02 else min(1.0, w / sh.width)
        k = min(k, height / sh.height)
        nw, nh = round(sh.width * k), round(sh.height * k)
        cy = sh.top + sh.height // 2
        sh.left, sh.top, sh.width, sh.height = Emu(x + (w - nw) // 2), Emu(cy - nh // 2), Emu(nw), Emu(nh)
    return True


def run(prs, name: str) -> None:
    done = 0
    for slide in prs.slides:
        words = take_marker(slide, KEY)
        if words is not None and slide.slide_layout.name == "Two Content":
            done += frame_slide(slide, words, prs.slide_width)
    if done:
        print(f"columns: framed {done} two-column slide(s) → {name}")
