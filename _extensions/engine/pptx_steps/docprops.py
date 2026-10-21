"""The deck's metadata as pandoc records it in docProps/custom.xml: one user-defined property
per front-matter key (a string; a list as an empty string). Read by the steps that take a deck's
word (titlegraphic, marking, the type step, the cover's byline)."""

from lxml import etree

PART = "/docProps/custom.xml"


def part(prs):
    """The custom-properties part, or None (a deck with no front matter has none)."""
    for p in prs.part.package.iter_parts():
        if str(p.partname) == PART:
            return p
    return None


def props(part):
    """The part's root and its properties as {name: text}."""
    root = etree.fromstring(part.blob)
    return root, {p.get("name"): "".join(p.itertext()).strip() for p in root}


def prop(prs, name):
    """One property's string, or None (absent, or empty: pandoc's list)."""
    p = part(prs)
    return (props(p)[1].get(name) or None) if p is not None else None
