#!/usr/bin/env python3
"""Style every table in a pandoc-rendered pptx as the HTML deck draws them.

pandoc writes each table with PowerPoint's "Medium Style 2 - Accent 1" (filled header, banded
rows) and no way to choose another. This replaces the style with direct cell formatting, which
PowerPoint and LibreOffice both render, in the livery's colors (engine-revealjs.scss `table`): a
header row with no fill, bold letter-spaced capitals at 0.8x the body size over a rule in
boxes.table's head-rule-color; body rows with a rule in the derived table-rule blend (the widths
boxes.table's, of the slide's height), every second
row filled with the table-band blend; columns left alone when pandoc took widths from the
source, else re-split in proportion to each column's longest cell, each 10-60% wide; a list in a
cell (a grid table's) bulleted and indented as the body's list, which a cell does not inherit.
Run after slide_layout has scaled the runs (pptx_post.py). Idempotent."""

import copy
from pathlib import Path

from lxml import etree
from pptx.oxml.ns import qn

import livery as livery_mod

from .common import BOXES, CELL_MAR, DARK_INK, LIVERY, is_table, on_dark, palette, ppr_place, rpr
from .measure import CANVAS, other_size

NO_STYLE    = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # "No Style, No Grid"
TABLE       = BOXES["table"]
HEAD_RULE   = TABLE["head-rule"] * CANVAS["h"] * 12700   # EMU; in the role TABLE["head-rule-color"]
ROW_RULE    = TABLE["rule"] * CANVAS["h"] * 12700        # in the table-rule blend, mix(foreground, surface, 20%)
HEAD_SCALE  = 0.8                      # th 0.8em of the table's 0.85em, ~0.8x td
HEAD_SPC    = LIVERY["type"]["tracking"]   # the small caps' letter spacing, em (type.tracking, every format)
SHARE       = (0.10, 0.60)             # column width bounds when re-split


def _ln(tag, rule):
    ln = etree.Element(qn(tag))
    if rule is None:
        etree.SubElement(ln, qn("a:noFill"))
        return ln
    width, color = rule
    ln.set("w", str(round(width)))   # an integer: "5715.0" makes PowerPoint repair the deck
    fill = etree.SubElement(ln, qn("a:solidFill"))
    etree.SubElement(fill, qn("a:srgbClr"), val=color)
    return ln


def _style_cell(tc, rule, fill):
    """Borders and fill on a cell's tcPr, in schema order, replacing any before."""
    tc_pr = tc.find(qn("a:tcPr"))
    if tc_pr is None:
        tc_pr = etree.SubElement(tc, qn("a:tcPr"))
    for child in list(tc_pr):
        if child.tag in {qn(t) for t in ("a:lnL", "a:lnR", "a:lnT", "a:lnB",
                                         "a:noFill", "a:solidFill")}:
            tc_pr.remove(child)
    pos = 0
    for tag, r in (("a:lnL", None), ("a:lnR", None), ("a:lnT", None), ("a:lnB", rule)):
        tc_pr.insert(pos, _ln(tag, r))
        pos += 1
    if fill is None:
        tc_pr.insert(pos, etree.Element(qn("a:noFill")))
    else:
        solid = etree.Element(qn("a:solidFill"))
        etree.SubElement(solid, qn("a:srgbClr"), val=fill)
        tc_pr.insert(pos, solid)


def _header_runs(tc, base):
    for r in tc.iter(qn("a:r")):
        r_pr = rpr(r)
        if r_pr.get("cap") != "all":   # idempotent: scale the size only once
            size = int(r_pr.get("sz") or base) * HEAD_SCALE
            r_pr.set("sz", str(round(size)))
            r_pr.set("spc", str(round(size * HEAD_SPC)))
        r_pr.set("b", "1")
        r_pr.set("cap", "all")


def _rebalance(tbl):
    cols = tbl.findall(qn("a:tblGrid") + "/" + qn("a:gridCol"))
    widths = [int(c.get("w")) for c in cols]
    if len(cols) < 2 or max(widths) - min(widths) > len(cols):
        return
    longest = [1] * len(cols)
    for tr in tbl.findall(qn("a:tr")):
        for i, tc in enumerate(tr.findall(qn("a:tc"))[:len(cols)]):
            text = "".join(t.text or "" for t in tc.iter(qn("a:t")))
            longest[i] = max(longest[i], len(text))
    total = sum(widths)
    shares = [min(max(n / sum(longest), SHARE[0]), SHARE[1]) for n in longest]
    norm = sum(shares)
    for col, share in zip(cols, shares):
        col.set("w", str(round(total * share / norm)))


def style_table(tbl, base, ink):
    """A table styled in ink (common.palette(): the head rule in boxes.table's role, the row rules and
    bands the table blends; on a dark slide the role's swap (primary-contrast's secondary), the dark
    blends, and every cell's text on-dark)."""
    role = TABLE["head-rule-color"]
    head = ink[role] if role in ink else livery_mod.hex(LIVERY, role)   # a role the dark slide does not swap: its own
    tbl_pr = tbl.find(qn("a:tblPr"))
    tbl_pr.attrib.pop("bandRow", None)
    style_id = tbl_pr.find(qn("a:tableStyleId"))
    if style_id is None:
        style_id = etree.SubElement(tbl_pr, qn("a:tableStyleId"))
    style_id.text = NO_STYLE

    rows = tbl.findall(qn("a:tr"))
    header = tbl_pr.get("firstRow") == "1" and rows and any(
        (t.text or "").strip() for t in rows[0].iter(qn("a:t")))
    for i, tr in enumerate(rows):
        is_head = header and i == 0
        body_index = i - 1 if header else i
        band = not is_head and body_index % 2 == 1
        for tc in tr.findall(qn("a:tc")):
            _style_cell(tc, (HEAD_RULE, head) if is_head else (ROW_RULE, ink["table-rule"]), ink["table-band"] if band else None)
            tc_pr = tc.find(qn("a:tcPr"))   # the cell's top and bottom margin, as HTML's padded rows
            tc_pr.set("marT", str(CELL_MAR)); tc_pr.set("marB", str(CELL_MAR))
            if is_head:
                _header_runs(tc, base)
    if ink is DARK_INK:   # the cells' text on the dark slide
        on_dark(list(tbl.iter(qn("a:p"))), ink["foreground"])
    _rebalance(tbl)


BULLET = ("buClr", "buClrTx", "buSzPct", "buSzPts", "buSzTx", "buFont", "buFontTx", "buChar")


def cell_lists(tbl, master):
    """A list in a cell bulleted as the body's list: pandoc writes a list item there as a paragraph
    with a level and no buNone (a plain line has buNone), and a cell inherits no bullet, so each
    item takes its level's indent and bullet from the master's body style (a numbered item keeps
    pandoc's number), and its spacing above, but for the cell's first line, which stays level with
    its row's other cells."""
    style = master.find(".//" + qn("p:bodyStyle"))
    if style is None:
        return
    for p in tbl.iter(qn("a:p")):
        ppr = p.find(qn("a:pPr"))
        if ppr is None or ppr.get("lvl") is None or ppr.find(qn("a:buNone")) is not None:
            continue
        lvl = style.find(qn(f"a:lvl{int(ppr.get('lvl')) + 1}pPr"))
        if lvl is None:
            continue
        for k in ("marL", "indent"):
            if lvl.get(k) is not None:
                ppr.set(k, lvl.get(k))
        before = lvl.find(qn("a:spcBef"))
        if before is not None and p.getprevious() is not None and ppr.find(qn("a:spcBef")) is None:
            ppr_place(ppr, copy.deepcopy(before))
        if ppr.find(qn("a:buAutoNum")) is not None:
            continue
        for el in list(ppr):
            if etree.QName(el).localname in BULLET:
                ppr.remove(el)
        for el in lvl:
            if etree.QName(el).localname in BULLET:
                ppr_place(ppr, copy.deepcopy(el))


def run(prs, path: Path) -> None:
    """The open deck, changed in place; path for the message."""
    styled = 0
    for slide in prs.slides:
        base = other_size(slide)
        for shape in slide.shapes:
            if is_table(shape):
                style_table(shape.table._tbl, base, palette(slide))
                cell_lists(shape.table._tbl, slide.slide_layout.slide_master._element)
                styled += 1
    print(f"style_tables: styled {styled} table(s) → {path.name}")
