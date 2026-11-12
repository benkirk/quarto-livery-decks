"""A hyperlink on a field slide in the field's text color.

PowerPoint draws a hyperlink in the theme's `hlink` color whatever its run says, and a livery's
hlink is its primary role (ncar: #0057C2), so a link on a slide whose field is primary (a closing, a
cover, a divider) was invisible there, and one on a dark slide dim (#172); HTML and the PDF draw it
in the field's text. On every slide that is a field of its own (common.field_ink(): a dark slide, a
composed slide), each linked run takes the field's text color, with Office's own extension that
tells PowerPoint to draw a link in its run's color (`hlinkClr val="tx"`, what "use the text color"
writes; LibreOffice and Keynote read the run's color as it is). It keeps its underline, which is
what says link there. A content slide's links are left to the theme. After every step that draws a
slide's text or decides its field (slide_layout, grid), before type_step."""

from pathlib import Path

from lxml import etree
from pptx.oxml.ns import qn

from .common import field_ink, rpr, set_fill

EXT_URI = "{A12FA001-AC4F-418D-AE19-62706E023703}"   # Office's hyperlink-color extension
AHYP = "http://schemas.microsoft.com/office/drawing/2018/hyperlinkcolor"


def text_colored(link) -> None:
    """The a:hlinkClick marked to be drawn in its run's color; a second call changes nothing."""
    if link.find(f".//{{{AHYP}}}hlinkClr") is not None:
        return
    lst = link.find(qn("a:extLst"))
    if lst is None:
        lst = etree.SubElement(link, qn("a:extLst"))
    ext = etree.SubElement(lst, qn("a:ext"))
    ext.set("uri", EXT_URI)
    etree.SubElement(ext, f"{{{AHYP}}}hlinkClr", nsmap={"ahyp": AHYP}).set("val", "tx")


def run(prs, path: Path) -> None:
    """The open deck, changed in place; path for the message."""
    n = 0
    for slide in prs.slides:
        ink = field_ink(slide)
        if ink is None:
            continue
        for r in slide._element.iter(qn("a:r")):
            el = rpr(r)
            link = el.find(qn("a:hlinkClick"))
            if link is None:
                continue
            set_fill(el, ink)
            text_colored(link)
            n += 1
    if n:
        print(f"links: {n} link(s) on a field in its text color → {path.name}")
