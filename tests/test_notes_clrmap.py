#!/usr/bin/env python3
"""Check pptx_steps/notes_clrmap.py on a deck pandoc writes with speaker notes.

    tests/test_notes_clrmap.py

pandoc writes a notes slide with no <p:clrMapOvr> (the premise; Keynote refuses such a deck).
After the step each notes slide has exactly one, right after its p:cSld, as PowerPoint writes it,
and python-pptx still reads the notes. A second run changes nothing, and a deck with no notes is
left as it is. Needs pandoc (Quarto's, $QUARTO_PANDOC).
"""

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_extensions" / "engine"))
from pptx_steps import notes_clrmap as nc   # noqa: E402  (the engine's tools import each other by name)

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def deck(tmp, md, name):
    """A pptx of md, by pandoc, as its zip members."""
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    out = tmp / name
    subprocess.run([pandoc, "-o", str(out)], input=md, text=True, cwd=tmp, check=True)
    with zipfile.ZipFile(out) as z:
        return {i.filename: z.read(i.filename) for i in z.infolist()}


def main():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        parts = deck(tmp, "## a\n\nOne.\n\n::: notes\nA note.\n:::\n\n## b\n\nTwo.\n\n"
                          "::: notes\nAnother.\n:::\n", "notes.pptx")
        notes = [n for n in parts if nc.NOTES.match(n)]
        check(len(notes) == 2, f"pandoc wrote {len(notes)} notes slides, not 2")
        check(not any(b"clrMapOvr" in parts[n] for n in notes),
              "pandoc already writes clrMapOvr on notes slides (the premise; the step may go)")
        nc.run(parts, "notes.pptx")
        for n in notes:
            x = etree.fromstring(parts[n])
            kids = [etree.QName(k).localname for k in x]
            check(kids[:2] == ["cSld", "clrMapOvr"] and kids.count("clrMapOvr") == 1,
                  f"{n}: children {kids}, not cSld then one clrMapOvr")
            check(x.find("{%s}clrMapOvr/{http://schemas.openxmlformats.org/drawingml/2006/main}"
                         "masterClrMapping" % P) is not None, f"{n}: no masterClrMapping")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for n, v in parts.items():
                z.writestr(n, v)
        from pptx import Presentation
        texts = [s.notes_slide.notes_text_frame.text for s in Presentation(buf).slides]
        check(texts == ["A note.", "Another."], f"python-pptx reads the notes as {texts}")

        again = dict(parts)
        nc.run(again, "notes.pptx")
        check(again == parts, "a second run changed the deck")

        plain = deck(tmp, "## a\n\nNo notes.\n", "plain.pptx")
        before = dict(plain)
        nc.run(plain, "plain.pptx")
        check(plain == before, "a deck with no notes changed")

    for f in fails:
        print("FAIL", f)
    print(f"notes_clrmap: {'one clrMapOvr after each cSld, notes intact, idempotent' if not fails else f'{len(fails)} failures'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
