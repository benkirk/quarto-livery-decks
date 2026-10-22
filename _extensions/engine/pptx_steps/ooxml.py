"""The OOXML namespaces and the parse and serialize the zip-stage steps share (svg_fallback,
section_subtitle, type_step, embed_fonts): a part's bytes to an lxml root and back, serialized as
PowerPoint writes a part (an XML declaration, UTF-8, standalone). Livery-free: svg_fallback reads
no livery, and common.py loads one as it is imported."""

from lxml import etree

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
CP = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"   # docProps/custom.xml
VT = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
NS = {"p": P, "a": A, "r": R}   # the prefixes an XPath over a slide uses


def parse(data: bytes):
    """A part's root element."""
    return etree.fromstring(data)


def serialize(root) -> bytes:
    """The part's bytes, as PowerPoint writes it."""
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
