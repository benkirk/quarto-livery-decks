#!/usr/bin/env python3
"""Style every table in a pandoc-rendered pptx as the HTML deck draws them.

pandoc writes each table with PowerPoint's "Medium Style 2 - Accent 1" (filled header, banded
rows) and no way to choose another. This replaces the style with direct cell formatting, which
PowerPoint and LibreOffice both render, in the livery's colors (engine-revealjs.scss `table`): a
header row with no fill, bold letter-spaced capitals at 0.8x the body size and a 3 px rule in
the primary slot (dk2); body rows with a 1 px rule in the derived table-rule blend, every second
row filled with the table-band blend; columns left alone when pandoc took widths from the
source, else re-split in proportion to each column's longest cell, each 10-60% wide.
Run after slide_layout has scaled the runs (pptx_post.py). Idempotent."""

from lxml import etree
from pptx.oxml.ns import qn

import livery as livery_mod

from .common import LIVERY, em, is_table, rpr
from .measure import PX, other_size   # EMU per revealjs px (1600 px wide)

NO_STYLE    = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # "No Style, No Grid"
HEAD_RULE   = (3 * PX, livery_mod.hex(LIVERY, "primary"))       # 3px solid var(--engine-primary)
ROW_RULE    = (1 * PX, livery_mod.blend(LIVERY, "table-rule"))  # mix(foreground, surface, 20%)
BAND_FILL   = livery_mod.blend(LIVERY, "table-band")            # surface at 60% on white
HEAD_SCALE  = 0.8                      # th 0.8em of the table's 0.85em, ~0.8x td
HEAD_SPC    = 0.04                     # letter-spacing: 0.04em
CELL_MAR    = em(0.4, livery_mod.type_pt(LIVERY, "table"))   # EMU: HTML's 0.3em padding, its line height
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


def style_table(tbl, base):
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
            _style_cell(tc, HEAD_RULE if is_head else ROW_RULE, BAND_FILL if band else None)
            tc_pr = tc.find(qn("a:tcPr"))   # the cell's top and bottom margin, as HTML's padded rows
            tc_pr.set("marT", str(CELL_MAR)); tc_pr.set("marB", str(CELL_MAR))
            if is_head:
                _header_runs(tc, base)
    _rebalance(tbl)


def run(prs, name: str) -> None:
    """The open deck, changed in place; name for the message."""
    styled = 0
    for slide in prs.slides:
        base = other_size(slide)
        for shape in slide.shapes:
            if is_table(shape):
                style_table(shape.table._tbl, base)
                styled += 1
    print(f"style_tables: styled {styled} table(s) → {name}")
