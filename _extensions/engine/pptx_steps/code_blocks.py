"""Code blocks in the pptx: each a block of lines, its indentation kept, fit to its box.

pandoc writes a code block as one paragraph in the code face (pandoc's Courier, or the livery's
monofont: common.CODE_FACES): a highlighted block's lines parted by a:br, an unhighlighted one's
(no language, a text tree, terminal output) as raw line feeds inside its runs' text, which
LibreOffice draws as a paragraph a line (each with the body's space before it: a double-spaced
block) and a viewer may drop a line's leading spaces at (a tree read as a flat list, #178).

normalize(), first of the Presentation steps (pptx_post.py), so every step after it measures and
moves the block as its lines: a run's line feeds become a:br (each break carrying the run's
properties, so its size steps with the text), and a line's leading spaces no-break spaces, which
no viewer collapses.

fit(), after type_step (it reads the final sizes, the deck's step applied): a block whose longest
line is wider than its box (the box's width less its insets and the paragraph's left margin) is
set smaller until it fits, to the half point, no smaller than the table type (stepped as the deck
steps it); past that floor it stays at the floor and wraps, warned of, naming the slide. HTML
scrolls a wide block and the PDF's runs past the margin (make qa's edge check catches that one).
"""

import sys
from pathlib import Path

from lxml import etree
from pptx.oxml.ns import qn
from pptx.text.text import _Paragraph

import livery as livery_mod

from . import docprops
from .common import LIVERY, is_code_para, slide_title
from .measure import PX, face, para_size, BODY

NBSP = " "
DEFAULT_INS = 91440   # a:bodyPr's lIns/rIns when unset: 0.1 in


def _split_run(r):
    """A run whose text holds line feeds as runs parted by a:br; the new elements, in order."""
    t = r.find(qn("a:t"))
    if t is None or "\n" not in (t.text or ""):
        return [r]
    rpr = r.find(qn("a:rPr"))
    out = []
    for i, line in enumerate(t.text.split("\n")):
        if i:
            br = etree.Element(qn("a:br"))
            if rpr is not None:
                br.append(etree.fromstring(etree.tostring(rpr)))
            out.append(br)
        if line:
            nr = etree.fromstring(etree.tostring(r))
            nr.find(qn("a:t")).text = line
            out.append(nr)
    prev = r
    for el in out:
        prev.addnext(el)
        prev = el
    r.getparent().remove(r)
    return out


def _keep_indent(p):
    """Each line's leading spaces as no-break spaces (a line starts the paragraph or follows an a:br;
    its spaces may run over several runs: a highlighted block's indent is a run of its own)."""
    start = True
    for el in p:
        if el.tag == qn("a:br"):
            start = True
        elif el.tag == qn("a:r") and start:
            t = el.find(qn("a:t"))
            text = t.text or "" if t is not None else ""
            lead = len(text) - len(text.lstrip(" "))
            if lead:
                t.text = NBSP * lead + text[lead:]
            if text.strip(" "):
                start = False


def _code_paras(prs):
    """(slide, shape, a:p) for each code paragraph on the deck's slides, a table's cells included."""
    for slide in prs.slides:
        for sh in slide.shapes:
            for p in sh._element.iter(qn("a:p")):
                if is_code_para(p):
                    yield slide, sh, p


def normalize(prs, path: Path) -> None:
    n = 0
    for _, _, p in list(_code_paras(prs)):
        before = etree.tostring(p)
        for r in list(p.iterchildren(qn("a:r"))):
            _split_run(r)
        _keep_indent(p)
        n += etree.tostring(p) != before
    if n:
        print(f"code_blocks: {n} code block(s) as lines, their indentation kept → {path.name}")


def _lines(p):
    """The paragraph's lines, each a list of (text, typeface) runs."""
    rows = [[]]
    for el in p:
        if el.tag == qn("a:br"):
            rows.append([])
        elif el.tag == qn("a:r"):
            t, latin = el.find(qn("a:t")), el.find(qn("a:rPr") + "/" + qn("a:latin"))
            rows[-1].append((t.text or "" if t is not None else "", latin.get("typeface") if latin is not None else None))
    return rows


def _width(rows, pt):
    """The widest line's width in slide pixels at pt points (measure's faces: a bundled code face
    in its file, any other 0.6 em a character)."""
    return max((sum(face(name, BODY, 400, pt).getlength(text) for text, name in row) for row in rows), default=0)


def _room(sh, p, slide):
    """The width a paragraph of the shape has, in slide pixels: the frame less its insets and the
    paragraph's left margin (its own, else its level's in the master's body style)."""
    body = sh._element.find(".//" + qn("a:bodyPr"))
    ins = sum(int(body.get(k, DEFAULT_INS)) if body is not None else DEFAULT_INS for k in ("lIns", "rIns"))
    ppr = p.find(qn("a:pPr"))
    mar = ppr.get("marL") if ppr is not None else None
    if mar is None:
        level = int(ppr.get("lvl", "0")) if ppr is not None else 0
        lvl = slide.slide_layout.slide_master._element.find(".//" + qn("p:bodyStyle") + "/" + qn(f"a:lvl{level + 1}pPr"))
        mar = lvl.get("marL", "0") if lvl is not None else "0"
    return ((sh.width or 0) - ins - int(mar)) / PX


def _set_size(p, pt):
    sz = str(round(pt * 100))
    for el in p.iter(qn("a:rPr"), qn("a:endParaRPr")):
        el.set("sz", sz)


def fit(prs, path: Path) -> None:
    part = docprops.part(prs)
    step = 1.0
    if part is not None:
        from .type_step import factor
        step = factor(docprops.props(part)[1], quiet=True) or 1.0
    floor = livery_mod.half_pt(livery_mod.type_pt(LIVERY, "table") * step)
    n = 0
    for slide, sh, p in _code_paras(prs):
        if sh._element.tag == qn("p:graphicFrame"):   # a table cell's width is its column's: left as it is
            continue
        room = _room(sh, p, slide)
        rows = _lines(p)
        pt = para_size(_Paragraph(p, sh), sh, slide) / 12700
        if not room or _width(rows, pt) <= room:
            continue
        want = livery_mod.half_pt(pt * room / _width(rows, pt))
        while want > floor and _width(rows, want) > room:   # the half-point rounding may land a hair wide
            want -= 0.5
        if want < floor:
            print(f"code_blocks: WARNING: slide {slide_title(slide)!r}: a code block's longest line is wider than its box "
                  f"at {floor:g} pt; it wraps (shorten its lines, or split the block)", file=sys.stderr)
            want = floor
        if want < pt:
            _set_size(p, want)
            n += 1
    if n:
        print(f"code_blocks: {n} wide code block(s) set smaller to fit their boxes → {path.name}")

