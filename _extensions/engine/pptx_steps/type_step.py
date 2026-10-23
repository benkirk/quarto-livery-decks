#!/usr/bin/env python3
"""Apply a deck's size step to a pandoc-rendered pptx: front matter `type-body: <pt>` (the body
in points; every size scales by it over the livery's body, livery.json type) or
`type-scale: <factor>`, type-body winning, as the engine does for HTML and PDF.

pandoc records both in docProps/custom.xml. Every text size in the master, the layouts and the
slides (rPr, defRPr and endParaRPr sz, spcPts) is multiplied and rounded to the half point, so
12 pt at type-body 10 is 10, not 10.02; a slide's own scale= (slide_layout.py) multiplies on
top. A deck without either is left alone. Last in pptx_post.py; it marks
the deck (engine-type-step in custom.xml), so a second run changes nothing."""

import sys
from pathlib import Path

from lxml import etree
from pptx.oxml.ns import qn

import livery as livery_mod

from . import docprops
from .common import LIVERY
from .ooxml import CP, VT, serialize

SIZED = (qn("a:rPr"), qn("a:defRPr"), qn("a:endParaRPr"))
FMTID = "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"   # a user-defined property's, as pandoc writes them


def factor(props):
    """The step from type-body or type-scale, or None (absent or not a positive number)."""
    for key, f in (("type-body", lambda v: v / livery_mod.type_pt(LIVERY, "body")), ("type-scale", lambda v: v)):
        raw = props.get(key)
        if raw:
            try:
                v = float(raw)
            except ValueError:
                v = 0
            if v > 0:
                return f(v)
            print(f"type_step: {key}: {raw!r} is not a positive number; ignored", file=sys.stderr)
    return None


def scale(root, f):
    n = 0
    for el in root.iter(*SIZED):
        if el.get("sz"):
            el.set("sz", str(round(livery_mod.half_pt(int(el.get("sz")) * f / 100) * 100)))
            n += 1
    for el in root.iter(qn("a:spcPts")):
        el.set("val", str(round(int(el.get("val")) * f)))
    return n


def run(prs, path: Path) -> None:
    """The open deck, changed in place; path for the messages."""
    part = docprops.part(prs)
    if part is None:
        return
    root, props = docprops.props(part)
    f = factor(props)
    if f is None or abs(f - 1) < 1e-6:
        return
    if "engine-type-step" in props:
        print(f"type_step: {path.name} already stepped ({props['engine-type-step']})")
        return
    n = sum(scale(x._element, f) for x in (*prs.slide_masters, *prs.slide_layouts, *prs.slides))
    pid = max((int(p.get("pid")) for p in root if p.get("pid")), default=1) + 1
    mark = etree.SubElement(root, f"{{{CP}}}property", fmtid=FMTID, pid=str(pid), name="engine-type-step")
    etree.SubElement(mark, f"{{{VT}}}lpwstr").text = f"{f:.4f}"
    part._blob = serialize(root)
    print(f"type_step: sizes x {f:.4f} ({n} runs and styles, to the half point) → {path.name}")
