"""A grid slide (three or more columns, a lead box; cards later) redrawn from grid-pptx.lua's markers.

grid-pptx.lua flattens a grid slide's columns into one text flow, which pandoc writes into the
Title and Content body placeholder, with marker paragraphs (a run of `⟦engine:...⟧`):
`⟦engine:columns widths=a,b,c⟧`, then per column `⟦engine:column⟧` ... `⟦engine:end⟧`, and a last
`⟦engine:end⟧` closing the columns; `⟦engine:lead⟧` ... `⟦engine:end⟧` a lead box. This parses the
placeholder's paragraphs into segments, text and columns, and lays them top down from the
placeholder's frame (its top below the title, its foot geometry.body-bottom; its left and width,
so a {.wide} slide's widening by slide_layout carries over): text before the columns stays in the
placeholder, cut to its measured height; the columns are free text boxes (Column 1, Column 2, ...; a card, a lead or a strip is one group of
its shapes, "Card n", "Lead", "Strip", so a click in PowerPoint selects it whole)
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
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

import livery as livery_mod

from .columns import rules
from .common import BODY_PT, BOXES, GEOM, LIVERY, SLACK, column_frames, is_body, pads, ppr_place, rect, rpr, set_fill
from .measure import text_height

MARK = re.compile(r"^⟦engine:(\w+)(?:\s+(.*))?⟧$")
PREFIX = re.compile(r"^⟦engine:(title|sub|label|big)⟧")   # a card's lines (grid-pptx.lua)
CARD_GAP = 0.25   # a card's paragraphs sit this share of the body's spacing apart (beamer's card \parskip)
BODY_GAP = livery_mod.SPC_BEFORE[0] * BODY_PT * CARD_GAP   # pt: CARD_GAP of the template's space before a body paragraph


def _para_text(p):
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
        m = MARK.match(_para_text(p).strip())
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
        elif kind == "strip":   # in a column, an item of its flow; else a segment of its own
            seg = ("strip", attrs, [])
            if stack and stack[-1][0] == "column":
                stack[-1][2].append(seg)
            elif not stack:
                segs.append(seg)
            stack.append(seg)
        elif kind == "end" and stack:
            stack.pop()
    return segs if any(s[0] != "text" for s in segs) else None


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


def group(slide, shapes, name):
    """The shapes as one PowerPoint group, named: a click selects the whole box (a card, a lead),
    a second click a part. At the first shape's place in the stacking (python-pptx appends a
    group on top); its child coordinates are the slide's (recalculate_extents)."""
    tree = slide.shapes._spTree
    shapes = sorted((sh for sh in shapes if sh is not None), key=lambda sh: list(tree).index(sh._element))
    at = list(tree).index(shapes[0]._element)
    g = slide.shapes.add_group_shape(shapes)
    tree.remove(g._element); tree.insert(at, g._element)
    g.name = name
    return g


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
    h = min(int(text_height(tb, slide) * SLACK), room)
    tb.height = h
    fill = rect(slide, x, y, w, h, _hex(lead["fill"]), "Lead fill", behind=tb)
    bar_shape = rect(slide, x, y, bar, h, _hex(lead["bar-color"]), "Lead bar", behind=tb)
    group(slide, [fill, bar_shape, tb], "Lead")
    return h + vpad


def _hex(value):
    """A role's, or a box color's (#RRGGBB), six digits."""
    return livery_mod.hex(LIVERY, value)


def _prefix(p):
    """A paragraph's prefix marker (title, sub, label, big), taken off its first run; None if none."""
    t = p.find(".//" + qn("a:t"))
    m = PREFIX.match(t.text or "") if t is not None else None
    if m is None:
        return None
    t.text = t.text[m.end():]
    if not t.text:   # the marker's own run
        r = t.getparent()
        if r.getnext() is not None:
            r.getparent().remove(r)
    return m.group(1)


def _style(p, size=None, bold=None, color=None, caps=False):
    """Every run of the paragraph at a size (pt), bold, a six-digit color, small caps' tracking."""
    for r in p.iter(qn("a:r")):
        el = rpr(r)
        if size is not None:
            el.set("sz", str(round(livery_mod.half_pt(size) * 100)))
        if bold is not None:
            el.set("b", "1" if bold else "0")
        if caps:
            el.set("cap", "all"); el.set("spc", "100")
        if color is not None:
            set_fill(el, color)


def _shape(slide, x, y, w, h, radius, fill, name, line=None, behind=None, top_only=False):
    """A card's rectangle, rounded when radius (EMU) > 0 (top_only: its top corners, a head band's);
    fill a six-digit hex or None; line (hex, width EMU) an outline; behind: a shape it goes under.
    Its own shape, not common.rect(): the preset geometry differs."""
    kind = (MSO_SHAPE.ROUND_2_SAME_RECTANGLE if top_only else MSO_SHAPE.ROUNDED_RECTANGLE) if radius > 0 else MSO_SHAPE.RECTANGLE
    r = slide.shapes.add_shape(kind, Emu(x), Emu(y), Emu(w), Emu(h))
    if radius > 0:
        r.adjustments[0] = min(0.5, round(radius / min(w, h), 5))
        if top_only:
            r.adjustments[1] = 0.0
    if fill:
        r.fill.solid(); r.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        r.fill.background()
    if line:
        r.line.color.rgb = RGBColor.from_string(line[0]); r.line.width = Emu(line[1])
    else:
        r.line.fill.background()
    r.shadow.inherit = False
    r.name = name
    if behind is not None:
        behind._element.addprevious(r._element)
    return r


def _close(p):
    """A card paragraph's space before: CARD_GAP of the master body's (a:spcBef), as HTML's card lines
    and beamer's sit close; type_step scales it with the sizes."""
    ppr = p.find(qn("a:pPr"))
    if ppr is None:
        ppr = etree.Element(qn("a:pPr")); p.insert(0, ppr)
    for old in ppr.findall(qn("a:spcBef")):
        ppr.remove(old)
    bef = etree.Element(qn("a:spcBef"))
    etree.SubElement(bef, qn("a:spcPts")).set("val", str(round(BODY_GAP * 100)))
    ppr_place(ppr, bef)


def _card_height(tb, slide):
    return int(text_height(tb, slide, gap=Pt(BODY_GAP)))


def _card_text(paras, solid):
    """A card's paragraphs, their prefix markers taken off and styled: (head, body) lists. The band's
    title in the subhead size, bold, and its sub in the body size, both primary-text; a label in the
    eyebrow size, caps, muted; a big number in the display size, bold, primary-contrast; on a solid
    card the body in primary-text."""
    head, body = [], []
    on_role = _hex("primary-text")
    for p in paras:
        if isinstance(p, tuple):   # a strip: its own lines styled as a card's body
            body.append((p[0], p[1], _card_text(p[2], solid)[1]))
            continue
        kind = _prefix(p)
        _close(p)
        if kind == "title":
            _style(p, livery_mod.type_pt(LIVERY, "subhead"), True, on_role); head.append(p)
        elif kind == "sub":
            _style(p, livery_mod.type_pt(LIVERY, "body"), False, on_role); head.append(p)
        elif kind == "label":
            _style(p, livery_mod.type_pt(LIVERY, "eyebrow"), True, on_role if solid else _hex("muted"), caps=True); body.append(p)
        elif kind == "big":
            _style(p, livery_mod.type_pt(LIVERY, "display"), True, on_role if solid else _hex("primary-contrast")); body.append(p)
        else:
            if solid:
                _style(p, color=on_role)
            body.append(p)
    return head, body


def _flat(items):
    """A column's flow without its strips' boxes (a plain column draws no strip): paragraphs."""
    out = []
    for it in items:
        out.extend(it[2] if isinstance(it, tuple) else [it])
    return out


def draw_strip(slide, x, y, w, room, paras, role, solid, name):
    """A strip: its text box padded by boxes.strip.pad over a rectangle the strip.tint of its role
    over the background (on a solid card the role itself, its text primary-text), cut to its text.
    (text box, rectangle) at y, its measured height."""
    vpad, hpad = pads("strip")
    tb = body_box(slide, x, y, w, room, paras, f"{name} text")
    tf = tb.text_frame
    tf.margin_top = tf.margin_bottom = vpad; tf.margin_left = tf.margin_right = hpad
    if solid:
        for p in paras:
            _style(p, color=_hex("primary-text"))
    tb.height = min(_card_height(tb, slide), room)
    fill = _hex(role) if solid else _hex(livery_mod.mix(_hex(role), _hex("background"), BOXES["strip"]["tint"]))
    return tb, rect(slide, x, y, w, tb.height, fill, name, behind=tb)


def _pick_role(attrs, default, slide):
    """A marker's role= when it is a role or a blend of the livery, else the default, warned of
    (engine-common.lua's box_role, for HTML and PDF)."""
    r = attrs.get("role", default)
    if r == default or r in LIVERY["roles"] or r in LIVERY["blends"]:
        return r
    title = slide.shapes.title
    print(f"grid: WARNING: slide {title.text_frame.text if title else ''!r}: role={r!r} is not a role or a blend "
          f"of the livery; {default}", file=sys.stderr)
    return default


ROLES = BOXES["card"]["roles"]   # a card without role=: by its place in the row


def draw_cards(slide, columns, frames, y, room, n_col, slide_height):
    """A row of cards (and plain columns beside them): each card a head band in its role over a
    body on boxes.card.fill (all of it the role's on a .solid card), rounded by card.radius, a
    .pick outlined in outline-color; its body a stack of text and strips (each at the card's full
    width); each head its own text's height (as HTML's) and the cards one height, the row's
    tallest, capped at the room left. Returns the row's height and the column boxes' count."""
    card = BOXES["card"]
    radius = round(card["radius"] * slide_height)
    hv, hh = pads("card", "head-pad")
    bv, bh = pads("card", "pad")
    cards = []
    for k, ((_, attrs, paras), (x, w)) in enumerate(zip(columns, frames), 1):
        n_col += 1
        if not attrs.get("card"):
            cards.append(dict(plain=body_box(slide, x, y, w, room, _flat(paras), f"Column {n_col}"), attrs=attrs))
            continue
        solid = attrs.get("solid")
        head, items = _card_text(paras, solid)
        hb = body_box(slide, x, y, w, room, head, f"Card {n_col} title") if head else None
        if hb is not None:
            hb.text_frame.margin_top = hb.text_frame.margin_bottom = hv
            hb.text_frame.margin_left = hb.text_frame.margin_right = hh
        parts, run, n_strip = [], [], 0   # the body: text boxes and strips, in order
        def text_part():
            nonlocal run
            if run or not parts:
                tb = body_box(slide, x, y, w, room, run, f"Card {n_col} body" + (f" {len(parts) + 1}" if parts else ""))
                tb.text_frame.margin_top = tb.text_frame.margin_bottom = bv
                tb.text_frame.margin_left = tb.text_frame.margin_right = bh
                parts.append(("text", tb, None, _card_height(tb, slide)))
            run = []
        for it in items:
            if isinstance(it, tuple):
                text_part() if run else None
                n_strip += 1
                tb, r = draw_strip(slide, x, y, w, room, it[2], _pick_role(it[1], "accent", slide), solid, f"Card {n_col} strip {n_strip}")
                parts.append(("strip", tb, r, tb.height))
            else:
                run.append(it)
        if run or not parts or parts[-1][0] == "strip":
            text_part()
        first = hb if hb is not None else parts[0][1]
        head_h = _card_height(hb, slide) if hb is not None else 0
        body_h = sum(h for _, _, _, h in parts)   # measured, no slack: the last part runs to the foot
        cards.append(dict(attrs=attrs, k=k, x=x, w=w, n=n_col, hb=hb, parts=parts, first=first, head_h=head_h, h=head_h + body_h))
    total = min(int(max(c["h"] for c in cards if "plain" not in c) * SLACK), room)   # the slack once, at the foot
    for c in cards:
        if "plain" in c:
            c["plain"].top, c["plain"].height = y, total
            continue
        attrs, x, w, n, hb, head_h = c["attrs"], c["x"], c["w"], c["n"], c["hb"], c["head_h"]
        role, solid = _hex(_pick_role(attrs, ROLES[(c["k"] - 1) % len(ROLES)], slide)), attrs.get("solid")
        mine = [_shape(slide, x, y, w, total, radius, role if solid else _hex(card["fill"]), f"Card {n} fill", behind=c["first"])]
        if hb is not None and not solid:   # rounded at the top only, square where the body starts
            mine.append(_shape(slide, x, y, w, head_h, radius, role, f"Card {n} head", behind=c["first"], top_only=True))
        if attrs.get("pick"):
            mine.append(_shape(slide, x, y, w, total, radius, None, f"Card {n} outline",
                               line=(_hex(card["outline-color"]), round(card["outline"] * slide_height))))
        if hb is not None:
            hb.top, hb.height = y, head_h
        cy = y + head_h
        for i, (kind, tb, r, h) in enumerate(c["parts"]):
            if i == len(c["parts"]) - 1 and kind == "text":   # the last text runs to the card's foot
                h = max(y + total - cy, 0)
            tb.top, tb.height = cy, h
            if r is not None:
                r.top = cy
            cy += h
        mine += [hb] + [part for _, tb, r, _ in c["parts"] for part in (tb, r)]
        group(slide, mine, f"Card {n}")   # one object to move or copy in PowerPoint
    return total, n_col


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
                h = min(int(text_height(ph, slide) * SLACK), bottom - y)
                ph.left, ph.top, ph.width, ph.height = left, y, width, h
                keep = True
            else:
                tb = body_box(slide, left, y, width, max(bottom - y, 0), seg[1], "Body text")
                h = min(int(text_height(tb, slide) * SLACK), max(bottom - y, 0))
                tb.height = h
            y += h
            continue
        if seg[0] == "lead":
            y += draw_lead(slide, left, y, width, max(bottom - y, 0), seg[2], slide_height)
            continue
        if seg[0] == "strip":   # on its own: as wide as the body, a vertical pad under it
            tb, r = draw_strip(slide, left, y, width, max(bottom - y, 0), seg[2], _pick_role(seg[1], "accent", slide), False, "Strip fill")
            tb.name = "Strip text"
            group(slide, [r, tb], "Strip")
            y += tb.height + pads("strip")[0]
            continue
        _, shares, columns = seg
        frames = column_frames(left, width, shares[:len(columns)] or [1 / len(columns)] * len(columns), slide_width)
        room = max(bottom - y, 0)
        if any(c[1].get("card") for c in columns):
            h, n_col = draw_cards(slide, columns, frames, y, room, n_col, slide_height)
            rules(slide, frames, y, h, slide_width, slide_height)
            y += h
            continue
        boxes = []
        for (_, attrs, paras), (x, w) in zip(columns, frames):
            n_col += 1
            boxes.append(body_box(slide, x, y, w, room, _flat(paras), f"Column {n_col}"))
        h = room
        tallest = min(max(int(text_height(b, slide)) for b in boxes), room)
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
        for ph in [sh for sh in slide.shapes if is_body(sh)]:
            paragraphs = ph.text_frame._txBody.findall(qn("a:p"))
            if not any(_para_text(p).startswith("⟦engine:") for p in paragraphs):
                continue
            segs = parse(paragraphs)
            if segs is None:
                continue
            for p in paragraphs:   # the marker paragraphs go
                if MARK.match(_para_text(p).strip()):
                    p.getparent().remove(p)
            lay_out(slide, ph, segs, prs.slide_width, prs.slide_height)
            done += 1
        left = [t.text for t in slide._element.iter(qn("a:t")) if t.text and "⟦" in t.text]
        if left:
            print(f"grid: WARNING: slide {prs.slides.index(slide) + 1}: markers left: {left[:3]}", file=sys.stderr)
    if done:
        print(f"grid: drew {done} grid slide(s) → {name}")
