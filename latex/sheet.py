#!/usr/bin/env python3
"""The cookbook's contact sheet, latex/sample.png: four pattern slides of examples/sample.pdf under
three liveries (the default ncar, sample-cu.pdf, sample-nasa-dark.pdf), liveries down and patterns
across, at 60 dpi. A page is found by its title in `pdftotext` (as decks/quickstart/screenshots.py
finds the README's), and which page of a frame's steps by its place among them; `--pages` takes
page numbers instead (a negative one from the end), which the README's preview.png uses for the
starter's title, divider, content and closing slides. Needs poppler's pdftotext and pdftoppm (the
env's) and Pillow. `make previews` here; rebuild them whenever the slides they show change, and
commit them (latex/authoring.md and latex/README.md show them).

    python3 sheet.py [examples/sample.pdf examples/sample-cu.pdf examples/sample-nasa-dark.pdf] [-o sample.png]
    python3 sheet.py --pages 1,2,3,-1 talk.pdf talk-cu.pdf -o preview.png
"""

import argparse
import io
import re
import subprocess
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
# (title, which page of the frame's steps: 1 the first, -1 the last)
SLIDES = [("Options, the pick moving across steps", 2), ("Steps inside cards", -1),
          ("Status items, step by step", -1), ("A warning slide", 1)]
DPI = 60


def page_titles(pdf: Path) -> list[str]:
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout).group(1))
    out = []
    for k in range(1, n + 1):
        text = subprocess.run(["pdftotext", "-f", str(k), "-l", str(k), "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
        out.append(next((l.strip() for l in text.splitlines() if l.strip()), ""))
    return out


def find(titles: list[str], title: str, which: int) -> int:
    pages = [k + 1 for k, t in enumerate(titles) if title in t]   # (a ⚠ may lead the line)
    if not pages:
        raise SystemExit(f"no page titled {title!r}")
    return pages[which - 1] if which > 0 else pages[which]


def shoot(pdf: Path, page: int) -> Image.Image:
    png = subprocess.run(["pdftoppm", "-r", str(DPI), "-f", str(page), "-l", str(page), "-png", str(pdf)], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGB")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pdfs", nargs="*", default=[HERE / "examples" / f"{n}.pdf" for n in ("sample", "sample-cu", "sample-nasa-dark")], type=Path)
    ap.add_argument("-o", "--out", default=HERE / "sample.png", type=Path)
    ap.add_argument("--pages", help="page numbers in place of the pattern titles, comma-separated; a negative one counts from the end")
    a = ap.parse_args()
    rows = []
    for pdf in a.pdfs:
        if a.pages:
            n = len(page_titles(pdf))
            rows.append([shoot(pdf, p if p > 0 else n + 1 + p) for p in map(int, a.pages.split(","))])
        else:
            titles = page_titles(pdf)
            rows.append([shoot(pdf, find(titles, title, which)) for title, which in SLIDES])
    gap = 6
    w, h = rows[0][0].size
    sheet = Image.new("RGB", (len(rows[0]) * (w + gap) + gap, len(rows) * (h + gap) + gap), "#808080")
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            sheet.paste(im.resize((w, h)), (gap + c * (w + gap), gap + r * (h + gap)))
    sheet.save(a.out)
    print(f"wrote {a.out}: {len(rows)} liveries x {len(rows[0])} slides")


if __name__ == "__main__":
    main()
