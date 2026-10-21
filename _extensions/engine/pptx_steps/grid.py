"""A grid slide (three or more columns, a lead box; cards later) redrawn from grid-pptx.lua's markers.

grid-pptx.lua flattens a grid slide's columns into one text flow, which pandoc writes into the
Title and Content body placeholder, with marker paragraphs (a run of `⟦engine:...⟧`):
`⟦engine:columns widths=a,b,c⟧`, then per column `⟦engine:column⟧` ... `⟦engine:end⟧`, and a last
`⟦engine:end⟧` closing the columns; `⟦engine:lead⟧` ... `⟦engine:end⟧` a lead box. This parses the
placeholder's paragraphs into segments, text and columns, and lays them top down from the
placeholder's frame (its top below the title, its foot geometry.body-bottom; its left and width,
so a {.wide} slide's widening by slide_layout carries over): text before the columns stays in the
placeholder, cut to its measured height; the columns are free text boxes (Column 1, Column 2, ...)
at columns.py's frames (each its share of the box less boxes.columns.gap, a livery's
boxes.columns.rule in each gap), their list style the master's body style, so pandoc's paragraphs,
moved into them with their own properties, keep the template's bullets and sizes; a lead is its
text box on a fill (boxes.lead.fill) with a bar at its left (bar, bar-color), padded (pad), cut to
its text, a pad's gap under it; text after the columns is a box of its own. Marker paragraphs are
deleted; a placeholder left with no text goes. After columns, before style_tables and type_step
(which scales the boxes' sizes with the rest). A grid slide's body-layout classes (.caution,
.vcenter) do not apply; scale= has run before.
"""

import copy
import re
import sys

from lxml import etree
from pptx.oxml.ns import qn
from pptx.util import Emu

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

from .columns import rules
from .slide_layout import BOXES, GEOM, _is_body, _text_height, pads

MARK = re.compile(r"^⟦engine:(\w+)(?:\s+(.*))?⟧$")
SLACK = 1.1   # measured height x this: autofit stays idle (as caution_box)


def _text(p):
    return "".join(t.text or "" for t in p.iter(qn("a:t")))


def _attrs(rest):
    """`widths=a,b role=x pick` -> {"widths": "a,b", "role": "x", "pick": True}."""
    out = {}
    for w in (rest or "").split():
        k, eq, v = w.partition("=")
        out[k] = v if eq else True
    return out


def parse(paragraphs):
    """The flow as segments: ("text", [p]), ("lead", attrs, [p]), ("columns", shares, [(attrs, [p])]);
    None when it holds no marker of a box (not a grid slide). Markers nest: a column inside its
    columns, each closed by its `end`."""
    segs, stack = [], []   # stack: the open containers, innermost last

    def text(p):
        if segs and segs[-1][0] == "text":
            segs[-1][1].append(p)
        else:
            segs.append(("text", [p]))
    for p in paragraphs:
        m = MARK.match(_text(p).strip())
        if m is None:
            top = stack[-1] if stack else None
            if top is None or top[0] == "columns":   # a stray paragraph between columns: text
                text(p)
            else:
                top[-1].append(p)
            continue
        kind, attrs = m.group(1), _attrs(m.group(2))
        if kind == "columns":
            seg = ("columns", [float(v) for v in attrs.get("widths", "").split(",") if v], [])
            segs.append(seg); stack.append(seg)
        elif kind == "column" and stack and stack[-1][0] == "columns":
            col = ("column", attrs, [])
            stack[-1][2].append(col); stack.append(col)
        elif kind == "lead" and not stack:
            seg = ("lead", attrs, [])
            segs.append(seg); stack.append(seg)
        elif kind == "end" and stack:
            stack.pop()
    return segs if any(s[0] != "text" for s in segs) else None


def column_frames(left, width, shares, slide_width):
    """(left, width) in EMU of each column in a box: its share of the box less the gaps."""
    g = round(BOXES["columns"]["gap"] * slide_width)
    room, x, out = width - g * (len(shares) - 1), left, []
    for s in shares:
        w = round(room * s)
        out.append((x, w))
        x += w + g
    return out


def body_box(slide, x, y, w, h, paragraphs, name):
    """A text box that renders as the body placeholder does: the master's body list style (bullets,
    sizes, spacing per level) in its lstStyle and its insets, word wrap, shrink on overflow; the
    paragraphs moved into it with their own properties."""
    tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    body = tf._txBody
    bp = body.find(qn("a:bodyPr"))
    for fit in list(bp):
        if fit.tag in (qn("a:spAutoFit"), qn("a:noAutofit"), qn("a:normAutofit")):
            bp.remove(fit)
    etree.SubElement(bp, qn("a:normAutofit"))
    master = slide.slide_layout.slide_master._element
    for sp in master.iter(qn("p:sp")):   # the body placeholder's insets (a text box's default is 0.1 in)
        ph = sp.find(".//" + qn("p:ph"))
        mbp = sp.find(".//" + qn("a:bodyPr"))
        if ph is not None and ph.get("type") == "body" and mbp is not None:
            for k in ("lIns", "tIns", "rIns", "bIns"):
                if mbp.get(k) is not None:
                    bp.set(k, mbp.get(k))
            break
    lst = body.find(qn("a:lstStyle"))
    style = master.find(".//" + qn("p:bodyStyle"))
    for lvl in (style if style is not None else []):
        if lvl.tag.endswith("pPr"):
            lst.append(copy.deepcopy(lvl))
    for p in body.findall(qn("a:p")):
        body.remove(p)
    for p in paragraphs:
        body.append(p)   # moves it
    if not paragraphs:
        etree.SubElement(body, qn("a:p"))
    return tb


def rect(slide, x, y, w, h, hexv, name, behind=None):
    """A filled rectangle (EMU, a #RRGGBB fill), no line or shadow; behind: a shape it goes under."""
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(x), Emu(y), Emu(w), Emu(h))
    r.fill.solid(); r.fill.fore_color.rgb = RGBColor.from_string(hexv[1:])
    r.line.fill.background(); r.shadow.inherit = False
    r.name = name
    if behind is not None:
        behind._element.addprevious(r._element)
    return r


def draw_lead(slide, x, y, w, room, paras, slide_height):
    """The lead box: its text on boxes.lead.fill, a bar of bar-color at its left, the text padded
    by boxes.lead.pad, the box cut to its measured text; the height it takes, a pad's gap under it
    included (HTML's margin-bottom)."""
    lead = BOXES["lead"]
    bar = round(lead["bar"] * slide_height)
    vpad, hpad = pads("lead")
    tb = body_box(slide, x + bar, y, w - bar, room, paras, "Lead text")
    tf = tb.text_frame
    tf.margin_top = tf.margin_bottom = vpad; tf.margin_left = tf.margin_right = hpad
    h = min(int(_text_height(tb, slide) * SLACK), room)
    tb.height = h
    rect(slide, x, y, w, h, lead["fill"], "Lead", behind=tb)
    rect(slide, x, y, bar, h, lead["bar-color"], "Lead bar", behind=tb)
    return h + vpad


def lay_out(slide, ph, segs, slide_width, slide_height):
    left, top, width = ph.left, ph.top, ph.width
    bottom = round(GEOM["body-bottom"] * slide_height)
    y, n_col, keep = top, 0, False
    for i, seg in enumerate(segs):
        later = segs[i + 1:]
        if seg[0] == "text":
            if i == 0:   # before the columns: the placeholder keeps it, cut to its text
                body = ph.text_frame._txBody
                for p in body.findall(qn("a:p")):
                    if p not in seg[1]:
                        body.remove(p)
                h = min(int(_text_height(ph, slide) * SLACK), bottom - y)
                ph.left, ph.top, ph.width, ph.height = left, y, width, h
                keep = True
            else:
                tb = body_box(slide, left, y, width, max(bottom - y, 0), seg[1], "Body text")
                h = min(int(_text_height(tb, slide) * SLACK), max(bottom - y, 0))
                tb.height = h
            y += h
            continue
        if seg[0] == "lead":
            y += draw_lead(slide, left, y, width, max(bottom - y, 0), seg[2], slide_height)
            continue
        _, shares, columns = seg
        frames = column_frames(left, width, shares[:len(columns)] or [1 / len(columns)] * len(columns), slide_width)
        room = max(bottom - y, 0)
        boxes = []
        for (_, attrs, paras), (x, w) in zip(columns, frames):
            n_col += 1
            boxes.append(body_box(slide, x, y, w, room, paras, f"Column {n_col}"))
        h = room
        tallest = min(max(int(_text_height(b, slide)) for b in boxes), room)
        if any(s[0] == "text" for s in later):   # text below: the row as tall as its tallest column
            h = min(int(tallest * SLACK), room)
            for b in boxes:
                b.height = h
        rules(slide, frames, y, tallest, slide_width, slide_height)
        y += h
    if not keep:
        ph._element.getparent().remove(ph._element)


def run(prs, name: str) -> None:
    done = 0
    for slide in prs.slides:
        for ph in [sh for sh in slide.shapes if _is_body(sh)]:
            paragraphs = ph.text_frame._txBody.findall(qn("a:p"))
            if not any(_text(p).startswith("⟦engine:") for p in paragraphs):
                continue
            segs = parse(paragraphs)
            if segs is None:
                continue
            for p in paragraphs:   # the marker paragraphs go
                if MARK.match(_text(p).strip()):
                    p.getparent().remove(p)
            lay_out(slide, ph, segs, prs.slide_width, prs.slide_height)
            done += 1
        left = [t.text for t in slide._element.iter(qn("a:t")) if t.text and "⟦" in t.text]
        if left:
            print(f"grid: WARNING: slide {prs.slides.index(slide) + 1}: markers left: {left[:3]}", file=sys.stderr)
    if done:
        print(f"grid: drew {done} grid slide(s) → {name}")
