#!/usr/bin/env python3
"""Merge a section-divider slide's orphaned subtitle back onto the same slide, then dress it.

pandoc renders a `#` heading (with `slide-level: 2`) as a title-only "Section Header" slide and
drops the markdown after it onto a separate, untitled slide; the template's Section Header
layout has a subtitle placeholder (idx=1) pandoc never fills, so this moves the orphan's body
there and deletes the orphan. It then dresses every divider as HTML and PDF do: the livery's
divider label ("Section n"; none under section.label: null, nor on a divider the metadata's
`engine-unnumbered` names, which the count skips; "Section 3 of 5" under section.progress) in
section.label-color (secondary by default),
the tab beside the title, and label, title and subtitle stacked and centered as one block, line
counts measured in the livery's heading and body fonts. Zip surgery via lxml,
third in pptx_post.py (after svg_fallback and notes_clrmap), before embed_fonts rewrites
presentation.xml. Idempotent: merged dividers stay merged; label and tab are replaced."""

import copy
import posixpath

from lxml import etree

import livery as livery_mod

from . import docprops, measure
from .common import GEOM, LIVERY, TRACKING
from .measure import PT_PX, PX
from .ooxml import A, CT, NS, P, PR, R, parse, serialize

SECTION_LAYOUT = "Section Header"
TITLE_PH = {"title", "ctrTitle"}
CHROME_PH = {"dt", "ftr", "sldNum"}  # date, footer, slide number — ignore

# Divider geometry in the revealjs theme's 1600x900 px, from its section-slide rules
# (engine-revealjs.scss), on the livery's canvas (livery.json type.canvas, pt): 1 px is
# 7620 EMU and 1 px of type 0.6 pt on 13.333 x 7.5 in, 5715 EMU and 0.45 pt on 10 x 5.625.
COLUMN = LIVERY["compositions"]["section"]["column"]   # the divider's text column (compositions)
BLOCK_TOP = round(COLUMN["box"][1] * 900)                 # the block is centred between its top
BLOCK_BOTTOM = round((COLUMN["box"][1] + COLUMN["box"][3]) * 900)   # and bottom (120 ... 820 px)
TAB_W = round(GEOM["tab-width"] * 1600)     # the divider's tab, geometry.tab-width of the width
TAB = COLUMN["tab"]
LABEL_ALIGN = '<a:pPr algn="ctr"/>' if COLUMN.get("align") == "center" else ""   # column.align
EYEBROW = LIVERY["compositions"]["section"]["eyebrow"]   # {label, color}: "Section", cap="all"
                                            # sets it in capitals; None: no eyebrow (section.label: null)
LABEL_PT = livery_mod.type_pt(LIVERY, "eyebrow")   # the eyebrow role (HTML's 0.7em)
SECTION = LIVERY["section"]                 # the stack's gaps (section.eyebrow-gap, .subtitle-gap), em of the
LABEL_GAP = round(SECTION["eyebrow-gap"] * LABEL_PT / PT_PX)   # eyebrow and of the subtitle, as HTML and the PDF
HEAD_LINE = 1.4                             # a divider line's height in em: ascent + descent of the heading font
                                            # (measure.LINE, 1.2, is a body line's)
BLOCK_SLACK = 4                             # px grown onto a measured title or subtitle block
DECOR = ("engine-section-label", "engine-section-tab")


def _resolve(base_dir, target):
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(base_dir, target))


def _rels_for(parts, part_name):
    """(rels_part_name, [(Id, Type, resolved_target), ...]) for a part."""
    d = posixpath.dirname(part_name)
    rels_name = posixpath.join(d, "_rels", posixpath.basename(part_name) + ".rels")
    if rels_name not in parts:
        return rels_name, []
    root = parse(parts[rels_name])
    rels = [(rel.get("Id"), rel.get("Type"), _resolve(d, rel.get("Target")))
            for rel in root.findall("{%s}Relationship" % PR)]
    return rels_name, rels


def _layout_name(parts, slide_part):
    for _id, typ, tgt in _rels_for(parts, slide_part)[1]:
        if typ.endswith("/slideLayout"):
            csld = parse(parts[tgt]).find("{%s}cSld" % P)
            return csld.get("name") if csld is not None else None
    return None


def _classify(root):
    """(has_title, has_body, first_body_sp) for a slide's shape tree."""
    tree = root.find("p:cSld/p:spTree", NS)
    has_title = has_body = False
    body_sp = None
    for sp in tree.findall("p:sp", NS):
        ph = sp.find("p:nvSpPr/p:nvPr/p:ph", NS)
        if ph is None:
            continue
        typ = ph.get("type") or "body"
        text = "".join(t.text or "" for t in sp.findall(".//a:t", NS)).strip()
        if not text:
            continue
        if typ in TITLE_PH:
            has_title = True
        elif typ not in CHROME_PH:
            has_body = True
            if body_sp is None:
                body_sp = sp
    return has_title, has_body, body_sp


def _merge_into(section_root, body_sp):
    """Append body_sp (a copy) to the section slide as its idx=1 subtitle."""
    tree = section_root.find("p:cSld/p:spTree", NS)
    sp = copy.deepcopy(body_sp)
    # inherit the Section Header layout's subtitle geometry, not the orphan's
    sp_pr = sp.find("p:spPr", NS)
    if sp_pr is not None:
        xfrm = sp_pr.find("a:xfrm", NS)
        if xfrm is not None:
            sp_pr.remove(xfrm)
    ph = sp.find("p:nvSpPr/p:nvPr/p:ph", NS)
    ph.set("type", "body")
    ph.set("idx", "1")
    # keep the shape id unique within the destination slide
    ids = {int(e.get("id")) for e in tree.iter("{%s}cNvPr" % P)
           if (e.get("id") or "").isdigit()}
    sp.find("p:nvSpPr/p:cNvPr", NS).set("id", str((max(ids) + 1) if ids else 2))
    tree.append(sp)


def _layout_part(parts, slide_part):
    for _id, typ, tgt in _rels_for(parts, slide_part)[1]:
        if typ.endswith("/slideLayout"):
            return tgt
    return None


def _ph_style(layout_root, ph_type):
    """(x, width, font_pt, line_spacing) of a layout placeholder, in px."""
    for sp in layout_root.find("p:cSld/p:spTree", NS).findall("p:sp", NS):
        ph = sp.find("p:nvSpPr/p:nvPr/p:ph", NS)
        if ph is None or (ph.get("type") or "body") != ph_type:
            continue
        off, ext = sp.find("p:spPr/a:xfrm/a:off", NS), sp.find("p:spPr/a:xfrm/a:ext", NS)
        rpr = sp.find(".//a:lvl1pPr/a:defRPr", NS)
        pct = sp.find(".//a:lvl1pPr/a:lnSpc/a:spcPct", NS)
        return (int(off.get("x")) / PX, int(ext.get("cx")) / PX, int(rpr.get("sz")) / 100,
                int(pct.get("val")) / 100000 if pct is not None else 1.0)
    return None


def _paragraphs(sp):
    return ["".join(t.text or "" for t in p.findall(".//a:t", NS))
            for p in sp.findall("p:txBody/a:p", NS)] if sp is not None else []


def _set_xfrm(sp, x, y, w, h):
    sp_pr = sp.find("p:spPr", NS)
    old = sp_pr.find("a:xfrm", NS)
    if old is not None:
        sp_pr.remove(old)
    xfrm = etree.SubElement(sp_pr, "{%s}xfrm" % A)
    sp_pr.insert(0, xfrm)
    etree.SubElement(xfrm, "{%s}off" % A, x=str(round(x * PX)), y=str(round(y * PX)))
    etree.SubElement(xfrm, "{%s}ext" % A, cx=str(round(w * PX)), cy=str(round(h * PX)))


def _decor(name, sid, x, y, w, h, inner):
    return etree.fromstring(
        f'<p:sp xmlns:p="{P}" xmlns:a="{A}"><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/>'
        f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm>'
        f'<a:off x="{round(x * PX)}" y="{round(y * PX)}"/>'
        f'<a:ext cx="{round(w * PX)}" cy="{round(h * PX)}"/></a:xfrm>{inner}</p:sp>')


def _eyebrow_hex():
    """The eyebrow's color (section.label-color, a hex since livery_build resolved it), as HTML and PDF draw it."""
    return livery_mod.hex(LIVERY, EYEBROW["color"]) if EYEBROW else livery_mod.color(LIVERY, "secondary")


def _dress(root, layout_root, number, of=None):
    """Label, tab and a centered title block on one divider slide; number None: an unnumbered
    divider, no label (and no room for one). Under section.progress the label reads
    "Section 3 of 5", of the numbered dividers' count."""
    tree = root.find("p:cSld/p:spTree", NS)
    for sp in tree.findall("p:sp", NS):
        if sp.find("p:nvSpPr/p:cNvPr", NS).get("name") in DECOR:
            tree.remove(sp)
    title = body = None
    for sp in tree.findall("p:sp", NS):
        ph = sp.find("p:nvSpPr/p:nvPr/p:ph", NS)
        typ = None if ph is None else (ph.get("type") or "body")
        if typ in TITLE_PH:
            title = sp
        elif typ == "body" and ph.get("idx") == "1":
            body = sp
    t_style, b_style = _ph_style(layout_root, "title"), _ph_style(layout_root, "body")
    if title is None or t_style is None:
        return

    def height(style, sp, family, weight):
        _x, w, pt, spacing = style
        return measure.block_height(_paragraphs(sp), family, weight, pt, w, HEAD_LINE, spacing)

    labelled = EYEBROW and number is not None
    label_h = HEAD_LINE * LABEL_PT / PT_PX if labelled else 0
    label_gap = LABEL_GAP if labelled else 0
    title_h = height(t_style, title, measure.TITLE, 700) + BLOCK_SLACK   # the face the pptx sets titles in
    body_text = body is not None and any(p.strip() for p in _paragraphs(body))
    body_h = height(b_style, body, measure.BODY, 400) + BLOCK_SLACK if body_text else 0
    body_gap = round(SECTION["subtitle-gap"] * b_style[2] / PT_PX)   # em of the subtitle's size (the layout's)
    total = label_h + label_gap + title_h + (body_gap + body_h if body_text else 0)
    y = BLOCK_TOP if COLUMN["anchor"] == "top" else (BLOCK_TOP + BLOCK_BOTTOM - total) / 2   # column.anchor

    ids = [int(e.get("id")) for e in tree.iter("{%s}cNvPr" % P) if (e.get("id") or "").isdigit()]
    sid = max(ids, default=1) + 1
    label = _decor(DECOR[0], sid, t_style[0], y, t_style[1], label_h,
                   '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
                   '<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t">'
                   f'<a:noAutofit/></a:bodyPr><a:lstStyle/><a:p>{LABEL_ALIGN}'
                   f'<a:r><a:rPr lang="en-US" sz="{round(LABEL_PT * 100)}" b="1" cap="all" spc="{round(LABEL_PT * 100 * TRACKING)}">'
                   f'<a:solidFill><a:srgbClr val="{_eyebrow_hex()}"/></a:solidFill>'
                   f'<a:latin typeface="+mn-lt"/></a:rPr><a:t>{EYEBROW["label"] if EYEBROW else ""} {number}{f" of {of}" if EYEBROW and EYEBROW.get("progress") and of else ""}</a:t>'
                   '</a:r></a:p></p:txBody>')
    y += label_h + label_gap
    _set_xfrm(title, t_style[0], y, t_style[1], title_h)
    inset = 0.08 * t_style[2] / PT_PX
    tab = _decor(DECOR[1], sid + 1, 0, y + inset, TAB_W, title_h - 2 * inset,
                 '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill>'
                 '<a:schemeClr val="accent4"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>')
    if labelled:
        tree.append(label)
    if TAB:
        tree.append(tab)
    if body_text:
        _set_xfrm(body, b_style[0], y + title_h + body_gap, b_style[1], body_h)


def run(parts: dict, name: str) -> None:
    """The deck's zip members (name -> bytes), changed in place; name for the message."""
    pres = parse(parts["ppt/presentation.xml"])
    sld_id_lst = pres.find("p:sldIdLst", NS)
    presrels_name, presrels = _rels_for(parts, "ppt/presentation.xml")
    relmap = {rid: tgt for rid, _typ, tgt in presrels}

    ordered = [(el, el.get("{%s}id" % R), relmap[el.get("{%s}id" % R)])
               for el in sld_id_lst.findall("p:sldId", NS)]

    info = {}
    for _el, _rid, part in ordered:
        root = parse(parts[part])
        has_title, has_body, body_sp = _classify(root)
        info[part] = dict(root=root, has_title=has_title, has_body=has_body,
                          body_sp=body_sp, layout=_layout_name(parts, part))

    merged, orphans = [], []
    for i in range(len(ordered) - 1):
        _s_el, _s_rid, s_part = ordered[i]
        o_el, o_rid, o_part = ordered[i + 1]
        s, o = info[s_part], info[o_part]
        if (s["layout"] == SECTION_LAYOUT and s["has_title"] and not s["has_body"]
                and not o["has_title"] and o["has_body"]):
            _merge_into(s["root"], o["body_sp"])
            merged.append(s_part)
            orphans.append((o_el, o_rid, o_part))

    # the dividers outside the count (.unnumbered, which pandoc drops: grid-pptx.lua writes their
    # places among the dividers into the metadata), so the numbers agree with HTML's and the PDF's
    custom = parts.get("docProps/custom.xml")
    skip = {int(w) for w in ((docprops.props_of(custom)[1].get("engine-unnumbered") or "").split()
                             if custom else [])}
    orphan_parts = {p for _el, _rid, p in orphans}
    dividers = [part for _el, _rid, part in ordered if info[part]["layout"] == SECTION_LAYOUT and part not in orphan_parts]
    total = sum(1 for k in range(1, len(dividers) + 1) if k not in skip)   # the numbered ones: section.progress's
    dressed, number = [], 0
    for part in dividers:
        layout_root = parse(parts[_layout_part(parts, part)])
        numbered = len(dressed) + 1 not in skip
        number += numbered
        _dress(info[part]["root"], layout_root, number if numbered else None, total)
        dressed.append(part)

    if not dressed:
        print("section_subtitle: no section dividers")
        return

    # Delete each orphan slide and everything that belongs only to it.
    delete_names = set()
    del_rids = {rid for _el, rid, _p in orphans}
    for o_el, _o_rid, o_part in orphans:
        sld_id_lst.remove(o_el)
        rels_name, rels = _rels_for(parts, o_part)
        delete_names.update({o_part, rels_name})
        for _id, typ, tgt in rels:
            if typ.endswith("/notesSlide"):
                delete_names.update({tgt, _rels_for(parts, tgt)[0]})

    presrels_root = parse(parts[presrels_name])
    for rel in presrels_root.findall("{%s}Relationship" % PR):
        if rel.get("Id") in del_rids:
            presrels_root.remove(rel)

    ct_root = parse(parts["[Content_Types].xml"])
    del_partnames = {"/" + n for n in delete_names if n.endswith(".xml")}
    for ov in ct_root.findall("{%s}Override" % CT):
        if ov.get("PartName") in del_partnames:
            ct_root.remove(ov)

    modified = {
        "ppt/presentation.xml": serialize(pres),
        presrels_name: serialize(presrels_root),
        "[Content_Types].xml": serialize(ct_root),
    }
    for s_part in dressed:
        modified[s_part] = serialize(info[s_part]["root"])

    for n in delete_names:
        parts.pop(n, None)
    parts.update(modified)

    print(f"section_subtitle: merged {len(merged)} subtitle(s), "
          f"removed {len(orphans)} orphan slide(s), dressed {len(dressed)} divider(s) "
          f"→ {name}")
