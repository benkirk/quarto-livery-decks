#!/usr/bin/env python3
"""Two builds of the same decks, slide by slide, pixel by pixel.

    slide_diff.py A B [deck ...] [--format html,pdf,pptx] [--out DIR] [--min-pixels N] [--tolerance T]

A and B are two deck directories holding the same built decks (<deck>.html, .pdf, .pptx): two
checkouts or worktrees of one commit under two environments (a Quarto minor against the one before,
as 1.10 and 1.11 were taken: #165, #175), or one checkout built twice. With no deck named, every
deck built in both. Each format's slides are drawn as `make qa` and `make shot` draw them
(slide_shot.py: the HTML in a browser, the PDF's pages, the pptx as LibreOffice draws it under the
livery `_livery` links in its directory) and each pair compared: a line per slide that differs, with
how many pixels and where, a line per deck and format, and under --out a picture per differing
slide, A beside B, the difference boxed. Exit 1 when any slide differs or a count does.

Where tests/parity.sh compares what a build wrote (the pptx's XML, the PDF's text, the HTML file),
which a new Quarto or pandoc changes wholesale, this compares what a reader sees. A pixel differs
past --tolerance (the largest channel difference, default 0), a slide past --min-pixels (default 0):
two builds of one HTML deck can differ by a few pixels at the tip of reveal's progress bar. A deck
that prints the time or a path (`date: last-modified`, a live shell cell) differs there by itself.
Needs what `make qa` needs: Playwright, poppler, LibreOffice, Pillow.
"""

import argparse
import os
import sys
import tempfile

sys.dont_write_bytecode = True   # no __pycache__ beside slide_shot.py
HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
import slide_shot  # noqa: E402

FORMATS = slide_shot.FORMATS


def compare(a, b, tolerance=0):
    """Two pictures' difference: (pixels that differ, their bounding box or None). Pictures of two
    sizes differ everywhere: (-1, None)."""
    from PIL import Image, ImageChops
    with Image.open(a) as ia, Image.open(b) as ib:
        if ia.size != ib.size:
            return -1, None
        diff = ImageChops.difference(ia.convert("RGB"), ib.convert("RGB"))
    r, g, bl = diff.split()   # a pixel's difference: its worst channel's
    mask = ImageChops.lighter(ImageChops.lighter(r, g), bl).point(lambda v: 255 if v > tolerance else 0)
    box = mask.getbbox()
    return (sum(mask.histogram()[255:]) if box else 0), box


def sheet(a, b, box, out):
    """A beside B, the differing box outlined on both, as out."""
    from PIL import Image, ImageDraw
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    w, h, gap = max(ia.width, ib.width), max(ia.height, ib.height), 12
    page = Image.new("RGB", (2 * w + gap, h), "#808080")
    for k, im in enumerate((ia, ib)):
        if box:
            ImageDraw.Draw(im).rectangle([box[0] - 3, box[1] - 3, box[2] + 2, box[3] + 2], outline="#FF0000", width=2)
        page.paste(im, (k * (w + gap), 0))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    page.save(out, optimize=True)


def shots(directory, deck, fmt, tmp):
    """The deck's slides in one format as PNGs, in order (slide_shot.py's shooters)."""
    src = os.path.join(directory, "%s.%s" % (deck, fmt))
    if fmt == "html":
        return [path for _, path in slide_shot.html_slides(deck, tmp, directory=directory)]
    if fmt == "pdf":
        return slide_shot.pdf_pages(src, tmp)
    sys.path.append(os.path.join(HERE, "..", "..", "_extensions", "engine"))
    import livery as livery_mod
    import pptx_pdf
    pdf, why = pptx_pdf.to_pdf(src, livery_mod.load(os.path.join(directory, "_livery")), tmp)
    if pdf is None:
        sys.exit("slide_diff: " + why)
    return slide_shot.pdf_pages(pdf, tmp)


def built(directory, fmt):
    return {f[:-len(fmt) - 1] for f in os.listdir(directory) if f.endswith("." + fmt)}


def diff_deck(a, b, deck, fmt, out=None, min_pixels=0, tolerance=0):
    """(slides, [(slide number, pixels, box)]) for one deck in one format; slides is None when the
    two builds' counts differ (said on stdout)."""
    with tempfile.TemporaryDirectory() as ta, tempfile.TemporaryDirectory() as tb:
        pa, pb = shots(a, deck, fmt, ta), shots(b, deck, fmt, tb)
        if len(pa) != len(pb):
            print("%s %s: %d slides against %d" % (deck, fmt, len(pa), len(pb)))
            return None, []
        differ = []
        for n, (x, y) in enumerate(zip(pa, pb), 1):
            pixels, box = compare(x, y, tolerance)
            if pixels < 0 or pixels > min_pixels:
                differ.append((n, pixels, box))
                print("%s %s slide %d: %s" % (deck, fmt, n, "another size" if pixels < 0 else
                                              "%d px differ, within x %d-%d, y %d-%d" % (pixels, box[0], box[2], box[1], box[3])))
                if out:
                    sheet(x, y, box, os.path.join(out, "%s-%s-s%03d.png" % (deck, fmt, n)))
        return len(pa), differ


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("a", help="a deck directory with built decks")
    ap.add_argument("b", help="the same decks, built otherwise")
    ap.add_argument("decks", nargs="*", help="deck names (default: every deck built in both)")
    ap.add_argument("--format", default=",".join(FORMATS), help="formats to compare, comma-separated (default: all three)")
    ap.add_argument("--out", help="a directory for a picture of each differing slide, A beside B")
    ap.add_argument("--min-pixels", type=int, default=0, help="a slide differs past this many pixels (default 0)")
    ap.add_argument("--tolerance", type=int, default=0, help="a pixel differs past this channel difference (default 0)")
    args = ap.parse_args(argv)
    formats = [f for f in args.format.split(",") if f]
    unknown = [f for f in formats if f not in FORMATS]
    if unknown:
        sys.exit("slide_diff: format %s is not one of %s" % (", ".join(unknown), ", ".join(FORMATS)))
    bad = compared = 0
    for fmt in formats:
        both = built(args.a, fmt) & built(args.b, fmt)
        for deck in args.decks or sorted(both):
            if deck not in both:
                print("%s %s: not built in both" % (deck, fmt))
                bad += bool(args.decks)   # a deck asked for by name must be there
                continue
            n, differ = diff_deck(args.a, args.b, deck, fmt, args.out, args.min_pixels, args.tolerance)
            compared += 1
            bad += n is None or bool(differ)
            if n is not None:
                print("%s %s: %d slides, %s" % (deck, fmt, n, "%d differ" % len(differ) if differ else "alike"))
    if not compared:
        sys.exit("slide_diff: no deck built in both %s and %s" % (args.a, args.b))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
