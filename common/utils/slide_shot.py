#!/usr/bin/env python3
"""One slide of a built deck as a PNG, found by its title: `make shot TITLE="..."` in a deck directory, or

    slide_shot.py <deck> <title>... [--format html|pdf|pptx|all] [--out DIR] [--width PX]

For a README's images, a talk about a deck, a review: the slide whose title holds the text ("" is the
title slide), as the HTML deck shows it in a browser (1600 x 900, hidden details slides included), as
the PDF's page (the first page whose text holds the title), or as LibreOffice draws the pptx's slide
(common/utils/pptx_pdf.py, as `make qa` does; a hidden slide too). Written to DIR (default
_qa/shots/) as <deck>-<slug of the title>-<format>.png, `--width` wide when given. A title no slide
has is an error that lists the titles there are. As a module: slide_shot(deck, title, fmt, out, width)
returns the PNG's path; html_slides() shoots every HTML slide in one browser session
(decks/quickstart/screenshots.py). Needs what `make qa` needs: Playwright for Python (CHROME names a
Chromium other than Playwright's) for HTML, poppler for the PDF, LibreOffice and python-pptx for the
pptx, Pillow to resize. Offline, or behind a proxy that blocks the MathJax CDN, set MATHJAX to a local
MathJax 2.7 directory (the npm package's contents) or an equation shoots as raw TeX.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True   # no __pycache__ beside deck_qa.py
HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
from deck_qa import serve  # noqa: E402

FORMATS = ("html", "pdf", "pptx")
VIEWPORT = {"width": 1600, "height": 900}


def slug(title):
    """A title as a file name's part: lower case, its runs of other characters a hyphen."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "title"


def _mathjax(route):
    rel = re.sub(r".*/mathjax@[^/]+/", "", route.request.url).split("?")[0]
    route.fulfill(path=os.path.join(os.environ["MATHJAX"], rel))


def html_slides(deck, out_dir, wait=600):
    """Every slide of <deck>.html (in the current directory) as out_dir/sNNN.png, in order:
    [(the slide's title, its path)], the title slide's first. Hidden details slides are shown."""
    from playwright.sync_api import sync_playwright
    httpd = serve(os.getcwd())
    base = "http://127.0.0.1:%d/" % httpd.server_address[1]
    shots = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get("CHROME") or None)
            page = browser.new_page(viewport=VIEWPORT)
            if os.environ.get("MATHJAX"):
                page.route(re.compile(r".*/mathjax@[^/]+/.*"), _mathjax)
            page.goto(base + deck + ".html?details=show")
            page.wait_for_function("window.Reveal && Reveal.isReady()")
            page.evaluate("document.fonts.ready.then(() => true)")
            page.evaluate("Reveal.configure({transition: 'none', backgroundTransition: 'none'})")
            titles = page.evaluate("Reveal.getSlides().map(s => "
                                   "(s.querySelector('h1, h2') || {textContent: ''}).textContent)")
            for i, title in enumerate(titles):
                # `##` slides nest under their `#` divider: Reveal.slide(i) would stay on it
                page.evaluate("i => { const ix = Reveal.getIndices(Reveal.getSlides()[i]);"
                              " Reveal.slide(ix.h, ix.v); }", i)
                page.wait_for_timeout(wait)
                path = os.path.join(out_dir, "s%03d.png" % (i + 1))
                page.screenshot(path=path)
                shots.append((title.strip(), path))
            browser.close()
    finally:
        httpd.shutdown()
    return shots


def find(titles, want):
    """The index of the first title holding `want` ("" is the first slide), or None."""
    if not want:
        return 0 if titles else None
    return next((i for i, t in enumerate(titles) if want in " ".join(t.split())), None)


def pdf_texts(pdf):
    """Each page's text, in order."""
    n = int([ln.split()[-1] for ln in subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True
                                                      ).stdout.splitlines() if ln.startswith("Pages:")][0])
    return [subprocess.run(["pdftotext", "-f", str(k), "-l", str(k), pdf, "-"],
                           capture_output=True, text=True, check=True).stdout for k in range(1, n + 1)]


def pdf_shot(pdf, page, prefix, dpi=160):
    """Page `page` (from 1) of the PDF as <prefix>.png; its path."""
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", "-f", str(page), "-l", str(page), pdf, prefix],
                   check=True)
    return prefix + ".png"


def pptx_titles(pptx):
    """Each slide's title text ("" for a slide without one: a {.full} slide, a split slide's rest)."""
    from pptx import Presentation
    return [(s.shapes.title.text_frame.text if s.shapes.title is not None else "") for s in Presentation(pptx).slides]


def _missing(deck, fmt, want, titles):
    sys.exit("slide_shot: no %s slide of %s titled %r; its titles: %s"
             % (fmt, deck, want, "; ".join(t for t in (" ".join(t.split()) for t in titles) if t)))


def _save(src, dst, width):
    from PIL import Image
    im = Image.open(src).convert("RGB")
    if width and im.width != width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    im.save(dst, optimize=True)
    return dst


def slide_shot(deck, title, fmt="html", out="_qa/shots", width=None):
    """The slide of <deck>.<fmt> (in the current directory) titled `title`, as a PNG in `out`; its path."""
    if fmt not in FORMATS:
        sys.exit("slide_shot: format %r is not one of %s" % (fmt, ", ".join(FORMATS)))
    src = "%s.%s" % (deck, fmt)
    if not os.path.exists(src):
        sys.exit("slide_shot: %s is not built (make %s)" % (src, fmt))
    dst = os.path.join(out, "%s-%s-%s.png" % (deck, slug(title), fmt))
    with tempfile.TemporaryDirectory() as tmp:
        if fmt == "html":
            shots = html_slides(deck, tmp)
            i = find([t for t, _ in shots], title)
            if i is None:
                _missing(deck, fmt, title, [t for t, _ in shots])
            return _save(shots[i][1], dst, width)
        if fmt == "pdf":
            texts = pdf_texts(src)
            i = find(texts, title)
            if i is None:
                sys.exit("slide_shot: no page of %s holds %r" % (src, title))
            return _save(pdf_shot(src, i + 1, os.path.join(tmp, "p")), dst, width)
        # pptx: by the slide's title; drawn by LibreOffice, every slide a page (a hidden one too)
        sys.path.append(os.path.join(HERE, "..", "..", "_extensions", "engine"))
        import livery as livery_mod
        import pptx_pdf
        titles = pptx_titles(src)
        i = find(titles, title)
        if i is None:
            _missing(deck, fmt, title, titles)
        pdf, why = pptx_pdf.to_pdf(src, livery_mod.load(), tmp)
        if pdf is None:
            sys.exit("slide_shot: " + why)
        return _save(pdf_shot(pdf, i + 1, os.path.join(tmp, "p")), dst, width)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("deck", help="the deck's name: <deck>.html, .pdf, .pptx in the current directory")
    ap.add_argument("titles", nargs="+", metavar="title", help='text in the slide\'s title ("" is the title slide)')
    ap.add_argument("--format", default="html", choices=FORMATS + ("all",))
    ap.add_argument("--out", default="_qa/shots", help="the directory the PNGs are written to")
    ap.add_argument("--width", type=int, help="resize to this width in pixels")
    args = ap.parse_args()
    for title in args.titles:
        for fmt in (FORMATS if args.format == "all" else (args.format,)):
            print(slide_shot(args.deck, title, fmt, args.out, args.width))


if __name__ == "__main__":
    main()
