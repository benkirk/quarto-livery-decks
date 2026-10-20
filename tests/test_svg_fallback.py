#!/usr/bin/env python3
"""Check pptx_steps/svg_fallback.py on a deck pandoc writes with an SVG picture.

    tests/test_svg_fallback.py

pandoc puts a one-slide deck's SVG in as a plain .svg picture; after the step its blip's r:embed
is a real PNG at the step's dpi, the SVG hangs off the blip's svgBlip extension, [Content_Types]
has png and svg, python-pptx opens the deck and reads the picture, and there is no stroke="0"
(Google Slides refuses a deck that has one, #109). A second run changes nothing, and a deck with
no SVG is left as it is. Needs pandoc (Quarto's, $QUARTO_PANDOC) and rsvg-convert.
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
from pptx_steps import svg_fallback as sf   # noqa: E402  (the engine's tools import each other by name)

SVG = (b'<svg xmlns="http://www.w3.org/2000/svg" width="72pt" height="36pt" viewBox="0 0 72 36">'
       b'<rect x="4" y="4" width="64" height="28" fill="#0057C2"/></svg>')
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def deck(tmp, image, name):
    """A one-slide pptx of image, by pandoc, as its zip members."""
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    out = tmp / name
    subprocess.run([pandoc, "-o", str(out)], input=f"## s\n\n![]({image.name})\n", text=True,
                   cwd=tmp, check=True)
    with zipfile.ZipFile(out) as z:
        return {i.filename: z.read(i.filename) for i in z.infolist()}


def main():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "x.svg").write_bytes(SVG)
        parts = deck(tmp, tmp / "x.svg", "svg.pptx")
        check(any(n.endswith(".svg") for n in parts), "pandoc wrote no .svg picture (the premise)")
        sf.run(parts, "svg.pptx")

        slide = next(n for n in parts if re.match(r"ppt/slides/slide\d+\.xml$", n)
                     and b"<p:pic>" in parts[n])
        rels = {r.get("Id"): r.get("Target") for r in
                etree.fromstring(parts[slide.replace("slides/", "slides/_rels/") + ".rels"])}
        blip = etree.fromstring(parts[slide]).find(".//{%s}blip" % sf.A)
        png = rels.get(blip.get("{%s}embed" % sf.R), "")
        check(png.endswith(".png"), f"the blip's r:embed is {png!r}, not a PNG")
        data = parts.get("ppt/media/" + png.rsplit("/", 1)[-1], b"")
        check(data[:8] == b"\x89PNG\r\n\x1a\n", "the fallback is not a PNG")
        width = int.from_bytes(data[16:20], "big") if len(data) > 20 else 0
        check(abs(width - sf.DPI) <= 1, f"the fallback is {width} px wide, not 1 in at {sf.DPI} dpi")
        svg_blip = blip.find(".//{%s}svgBlip" % sf.ASVG)
        check(svg_blip is not None and svg_blip.getparent().get("uri") == sf.SVG_EXT,
              "no svgBlip in the blip's extension list")
        if svg_blip is not None:
            check(rels.get(svg_blip.get("{%s}embed" % sf.R), "").endswith(".svg"),
                  "the svgBlip does not point at the SVG")
        ct = parts["[Content_Types].xml"].decode()
        for ext, mime in (("png", "image/png"), ("svg", "image/svg+xml")):
            check(f'Extension="{ext}" ContentType="{mime}"' in ct, f"no {ext} Default content type")
        check(not any(b'stroke="0"' in v for n, v in parts.items() if n.endswith(".xml")),
              'stroke="0" in the deck')

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for n, v in parts.items():
                z.writestr(n, v)
        from pptx import Presentation
        pics = [sh for s in Presentation(buf).slides for sh in s.shapes if sh.shape_type == 13]
        check(len(pics) == 1 and pics[0].image.content_type == "image/png",
              "python-pptx does not read the picture as the PNG")

        again = dict(parts)
        sf.run(again, "svg.pptx")
        check(again == parts, "a second run changed the deck")

        (tmp / "y.png").write_bytes(data)   # the fallback itself, as a PNG-only deck's picture
        plain = deck(tmp, tmp / "y.png", "png.pptx")
        before = dict(plain)
        sf.run(plain, "png.pptx")
        check(plain == before, "a deck with no SVG changed")

    for f in fails:
        print("FAIL", f)
    print(f"svg_fallback: {'a PNG r:embed, the svgBlip, both content types, idempotent' if not fails else f'{len(fails)} failures'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
