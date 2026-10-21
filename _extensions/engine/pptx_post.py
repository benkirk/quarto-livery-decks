#!/usr/bin/env python3
"""The engine's pptx post-render steps, on a deck `quarto render --to engine-pptx` wrote.

    pptx_post.py <deck.pptx> ...

pandoc's pptx writer cannot draw what the engine's other formats draw (divider dress, slide
numbers, footnotes, covers, tables in the livery's style), so Make.common's pptx recipe runs this
after rendering. Each deck is read once, the steps in pptx_steps/ run in the order below, and it
is saved once: the first five on the zip's parts (text and lxml), the rest on one python-pptx
Presentation. The livery comes from $LIVERY_DIR (Make.common exports it), else a `_livery` link
in the current directory (the engine's livery.py)."""

import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # livery, pptx_waves, pptx_steps

from pptx import Presentation  # noqa: E402

from pptx_steps import (  # noqa: E402  (each reads the livery as it loads)
    embed_fonts, enable_autofit, link_captions, marking, notes_clrmap, section_subtitle, slide_layout,
    style_footnotes, style_tables, svg_fallback, type_step)


def post(path: Path) -> None:
    with zipfile.ZipFile(path) as z:
        parts = {i.filename: z.read(i.filename) for i in z.infolist()}

    # The zip's parts. svg_fallback first: every later step, python-pptx's picture.image among
    # them (slide_layout's full slides), then sees a PNG picture, never a bare SVG. section_subtitle
    # next: it merges each divider's orphaned subtitle and deletes the slide pandoc split it onto,
    # before embed_fonts rewrites presentation.xml.
    svg_fallback.run(parts, path.name)      # an SVG plot's PNG fallback, PowerPoint's own shape
    notes_clrmap.run(parts, path.name)      # notes slides as PowerPoint writes them (Keynote)
    section_subtitle.run(parts, path.name)
    enable_autofit.run(parts, path.name)    # pandoc's bodies: shrink text on overflow
    embed_fonts.run(parts, path.name)       # the livery's typeface, which pandoc drops

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)
    prs = Presentation(buf)

    # One Presentation. Footnotes are styled before slide_layout, whose scale= leaves them at
    # their size; tables after it has scaled the runs; the marking strip before type_step, so a
    # deck's type step scales it as HTML and PDF do; type_step last, since it multiplies every
    # size the steps before it set.
    style_footnotes.run(prs, path.name)
    link_captions.run(prs, path.name)       # a linked picture's URL, a box pandoc cannot add
    slide_layout.run(prs, path.resolve())   # layout classes, covers, closings, slide numbers
    style_tables.run(prs, path.name)
    marking.run(prs, path.name)             # the marking strip, on every slide
    type_step.run(prs, path)                # a deck's type-body:/type-scale:
    prs.save(str(path))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        if not Path(arg).exists():
            sys.exit(f"pptx_post: {arg} not found")
        post(Path(arg))
