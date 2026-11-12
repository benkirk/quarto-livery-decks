#!/usr/bin/env python3
"""Give every notes slide of a pandoc-rendered pptx the color map PowerPoint writes.

pandoc's notes slides end at `</p:cSld>`, with no `<p:clrMapOvr>`. The schema lets it go
(minOccurs 0) and PowerPoint and Google Slides open the deck, but Keynote (15.4, 2026-10) refuses
the whole file, "The file format is invalid", for one slide with speaker notes. This adds
`<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>` after the notes slide's `p:cSld`, as
PowerPoint itself writes it: the notes master's colors, unchanged. pandoc's slides lack it too,
and Keynote takes those.

Idempotent: a notes slide that already has one is left alone. REEVALUATE WHEN QUARTO'S PANDOC
ROLLS (#166): pandoc 3.13 writes `clrMapOvr` on notes slides itself; Quarto 1.10 and 1.11 bundle pandoc
3.10, which does not (probed 2026-11-01; 3.13 itself 2026-11-12, CLAUDE.md's gotchas). Being idempotent, this step can stay until the probe
says the writer's is there, then go."""

import re

NOTES = re.compile(r"ppt/notesSlides/notesSlide\d+\.xml$")
CLRMAP = b"<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>"


def run(parts: dict, name: str) -> None:
    """The deck's zip members (name -> bytes), changed in place; name for the message."""
    done = 0
    for member, data in parts.items():
        if NOTES.match(member) and b"<p:clrMapOvr" not in data:
            parts[member], n = re.subn(rb"</p:cSld>", b"</p:cSld>" + CLRMAP, data, count=1)
            done += n
    print(f"notes_clrmap: color map on {done} notes slide(s) → {name}")
