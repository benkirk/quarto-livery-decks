#!/usr/bin/env python3
"""README screenshots of the quickstart deck: `make screenshots` in decks/quickstart/.

Reads the built quickstart.{html,pdf} and writes the committed PNGs in screenshots/:
  NN-<name>.png   one HTML slide each, 960 px wide (SLIDES below)
  hero.png        2x2 grid of the HERO slides, for the top of the README
  overview.png    every HTML slide, four across
  pdf.png         2x2 grid of the PDF pages of PDF_SLIDES
Slides are found by title, so adding a slide does not shift the shots; the shooting is
common/utils/slide_shot.py's (`make shot TITLE=...` is one slide of any deck). Needs Playwright
(set CHROME to use a Chromium other than Playwright's), poppler and Pillow, as `make qa` does.
Offline, or behind a proxy that blocks the MathJax CDN, set MATHJAX to a local MathJax 2.7
directory (the npm package's contents) or the math slide shows raw TeX.
"""

import glob
import os
import sys
import tempfile

sys.dont_write_bytecode = True   # no __pycache__ beside slide_shot.py
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common", "utils"))
import slide_shot  # noqa: E402  (the shooting: every HTML slide in one browser session, a PDF page by its text)

DECK = "quickstart"
OUT = "screenshots"
WIDTH = 960
# (file name, text in the slide title; "" is the title slide)
SLIDES = [
    ("01-title", ""),
    ("02-divider", "Write Markdown"),
    ("03-text", "One source, three formats"),
    ("04-columns", "Columns: a list beside a table"),
    ("05-math", "MPAS-A"),
    ("06-code", "Code, static and live"),
    ("07-mermaid", "How a deck is built"),
    ("08-feature", "A full-bleed photo slide"),
    ("09-full", "A full-slide diagram"),
    ("10-short", "A short slide"),
    ("11-closing", "Thank you!"),
    ("12-cards", "Cards: options side by side"),
]
HERO = ["01-title", "05-math", "04-columns", "07-mermaid"]
PDF_SLIDES = ["One Markdown file", "MPAS-A", "Columns: a list", "How a deck is built"]


def save(im, path, width=WIDTH):
    from PIL import Image
    im = im.convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, optimize=True)


def grid(paths, out, cols, width, gap=12):
    from PIL import Image
    thumbs = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        thumbs.append(im.resize((width, round(im.height * width / im.width)), Image.LANCZOS))
    h = max(t.height for t in thumbs)
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * width + (cols - 1) * gap, rows * h + (rows - 1) * gap),
                      "#FFFFFF")
    for n, t in enumerate(thumbs):
        sheet.paste(t, ((n % cols) * (width + gap), (n // cols) * (h + gap)))
    sheet.save(out, optimize=True)


def html_shots(tmp):
    """Every HTML slide as tmp/sNNN.png (slide_shot.html_slides); returns {name: path} for SLIDES."""
    shots = slide_shot.html_slides(DECK, tmp)
    found = {}
    for i, (title, path) in enumerate(shots):
        for name, want in SLIDES:
            if name not in found and (want in title if want else i == 0):
                found[name] = path
    missing = [name for name, _ in SLIDES if name not in found]
    if missing:
        sys.exit("no HTML slide for %s; titles: %s" % (", ".join(missing), [t for t, _ in shots]))
    return found


def pdf_pages(tmp):
    """The PDF pages whose text holds each PDF_SLIDES title, in that order."""
    texts = slide_shot.pdf_texts(DECK + ".pdf")
    pages = []
    for want in PDF_SLIDES:
        k = slide_shot.find(texts, want)
        if k is None:
            sys.exit("no PDF page with %r" % want)
        pages.append(slide_shot.pdf_shot(DECK + ".pdf", k + 1, os.path.join(tmp, "p%02d" % (k + 1))))
    return pages


def main():
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    for old in glob.glob(os.path.join(OUT, "*.png")):
        if os.path.basename(old) != "liveries.png":   # gallery.py's, built under every livery
            os.remove(old)
    with tempfile.TemporaryDirectory() as tmp:
        shots = html_shots(tmp)
        for name, _ in SLIDES:
            save(Image.open(shots[name]), os.path.join(OUT, name + ".png"))
        grid([shots[name] for name in HERO], os.path.join(OUT, "hero.png"), 2, 640)
        grid(sorted(glob.glob(os.path.join(tmp, "s*.png"))),
             os.path.join(OUT, "overview.png"), 4, 400)
        grid(pdf_pages(tmp), os.path.join(OUT, "pdf.png"), 2, 640)
    for p in sorted(glob.glob(os.path.join(OUT, "*.png"))):
        print("%-28s %4d KB" % (p, os.path.getsize(p) // 1024))


if __name__ == "__main__":
    main()
