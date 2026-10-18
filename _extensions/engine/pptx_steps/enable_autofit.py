#!/usr/bin/env python3
"""Set every body-text placeholder in a pandoc-rendered pptx to "autofit on".

Pandoc emits `<a:bodyPr />` (empty) for body placeholders, which means
"no autofit, overflow." This script replaces empty bodyPr with one that
contains a bare `<a:normAutofit/>` — i.e. flips the "Shrink text on
overflow" dropdown to ON.

Note: PowerPoint computes the actual fontScale on edit, not on load.
For real shrink-to-fit at render time, follow this with the AppleScript
driver (autofit_powerpoint.applescript) which opens the file in
PowerPoint, touches each text frame to force scale recomputation, and
saves. Without that step, this script alone won't visibly shrink
overflowing text — it just primes the placeholder so a single click
inside the cell triggers the recompute.

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
