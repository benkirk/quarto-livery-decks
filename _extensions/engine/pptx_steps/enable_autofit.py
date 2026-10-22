#!/usr/bin/env python3
"""Set every body-text placeholder in a pandoc-rendered pptx to "autofit on".

Pandoc emits `<a:bodyPr />` (empty) for body placeholders, which means
"no autofit, overflow." This script replaces empty bodyPr with one that
contains a bare `<a:normAutofit/>` — i.e. flips the "Shrink text on
overflow" dropdown to ON.

Note: PowerPoint computes the actual fontScale on edit, not on load, so
this alone does not visibly shrink overflowing text; it primes the
placeholder so a click inside it triggers the recompute. The engine keeps
its own boxes within their text by measuring them (pptx_steps/measure.py),
not by a driver that touches each frame.

Idempotent: any bodyPr that already contains an autofit child
(`normAutofit`, `spAutoFit`, `noAutofit`) is left alone."""

import re

EMPTY_BODYPR = re.compile(rb"<a:bodyPr\s*/>")
NEW_BODYPR   = b"<a:bodyPr><a:normAutofit/></a:bodyPr>"


def patch_slide(xml: bytes) -> tuple[bytes, int]:
    return EMPTY_BODYPR.subn(NEW_BODYPR, xml)


def run(parts: dict, name: str) -> None:
    """The deck's zip members (name -> bytes), changed in place; name for the message."""
    total = 0
    for member, data in parts.items():
        if member.startswith("ppt/slides/slide") and member.endswith(".xml"):
            parts[member], n = patch_slide(data)
            total += n
    print(f"enable_autofit: enabled normAutofit on {total} placeholder(s) → {name}")
