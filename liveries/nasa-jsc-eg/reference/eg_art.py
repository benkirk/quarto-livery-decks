"""Build the JSC EG livery's art and marks from the EG PowerPoint template.
usage: python3 -I eg_art.py <NASA-EG-template.pptx> <livery dir>

The art is the template's own layouts, rendered by LibreOffice with their placeholders and the
marks the engine draws itself taken out: the cover (EG - Title Slide, less the insignia), the
light cover (EG - Title Slide- Light, less the insignia), the
content slides (EG - Title & Content, less the insignia, the division bar and the title rule) and
the closing (EG - Closing, less the insignia and the agency name). The sample talk's slides are
dropped before anything is written, so none of their content reaches the livery."""
import shutil, subprocess, sys, tempfile
from pathlib import Path
from pptx import Presentation
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
ART = {   # art name: (layout name, shapes the engine draws instead)
    "title": ("EG - Title Slide", {"Picture 9"}),                                  # the insignia
    "title-light": ("EG - Title Slide- Light", {"Picture 7"}),                     # the insignia
    "content": ("EG - Title & Content", {"Picture 4", "Picture 11", "Straight Connector 6"}),
    "closing": ("EG - Closing", {"Picture 8", "Picture 2"}),                       # insignia, name
}
LOGOS = {  # logo name: (layout or slide, shape name); the media are the template's own files
    "eg-footer": ("EG - Title & Content", "Picture 11"),   # the division bar
    "eg-patch": ("EG - Closing", "Picture 5"),             # the division patch
    "group-patch": (1, "Picture 4"),                       # the Flight Sciences Lab patch, slide 1
}
W, H = 1920, 1080


def run(*a):
    subprocess.run(a, check=True, capture_output=True)


def pdf_twin(png: Path):
    """the same mark as a PDF for LaTeX, alpha kept (cairo through an SVG wrapper)"""
    w, h = Image.open(png).size
    svg = png.with_suffix(".tmp.svg")
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                   f'width="{w}" height="{h}"><image width="{w}" height="{h}" xlink:href="{png.resolve().as_uri()}"/></svg>')
    run("rsvg-convert", "-f", "pdf", str(svg), "-o", str(png.with_suffix(".pdf")))
    svg.unlink()


prs = Presentation(SRC)
layouts = {l.name: l for m in prs.slide_masters for l in m.slide_layouts}
(OUT / "art").mkdir(exist_ok=True); (OUT / "logos").mkdir(exist_ok=True)

# the marks: the template's media as they are
for name, (where, shape) in LOGOS.items():
    shapes = prs.slides[where - 1].shapes if isinstance(where, int) else layouts[where].shapes
    pic = next(s for s in shapes if s.name == shape)
    png = OUT / "logos" / f"{name}.png"
    Image.open(__import__("io").BytesIO(pic.image.blob)).convert("RGBA").save(png, optimize=True)
    pdf_twin(png)

# the art: drop the talk's slides, add one bare slide per layout, render, save
lst = prs.slides._sldIdLst
for sid in list(lst):
    prs.part.drop_rel(sid.rId); lst.remove(sid)
for name, (layout, drop) in ART.items():
    lay = layouts[layout]
    for s in [s for s in lay.shapes if s.name in drop]:
        s._element.getparent().remove(s._element)
    slide = prs.slides.add_slide(lay)
    for ph in list(slide.placeholders):
        ph._element.getparent().remove(ph._element)
with tempfile.TemporaryDirectory() as tmp:
    deck = Path(tmp) / "art.pptx"; prs.save(deck)
    run("soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, str(deck))
    run("pdftoppm", "-png", "-scale-to-x", str(W), "-scale-to-y", str(H), str(deck.with_suffix(".pdf")), f"{tmp}/p")
    for i, name in enumerate(ART, 1):
        Image.open(f"{tmp}/p-{i}.png").convert("RGB").save(OUT / "art" / f"{name}.jpg", quality=85, optimize=True)

# the agency name, two lines right-aligned in Arial Bold's metrics (Liberation Sans Bold), white, as
# outlines: the closing slide's identifier beside the insignia
font = TTFont(OUT / "fonts" / "LiberationSans-Bold.ttf")
gs, cmap, upm = font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm
lines, lead = ["National Aeronautics and", "Space Administration"], 1.15 * upm
width = lambda t: sum(font["hmtx"][cmap[ord(c)]][0] for c in t)
wmax, asc, desc = max(map(width, lines)), 0.73 * upm, 0.21 * upm   # cap height and descender of Arial
paths = []
for i, t in enumerate(lines):
    x, y = wmax - width(t), asc + i * lead
    for c in t:
        g = cmap[ord(c)]; pen = SVGPathPen(gs)
        gs[g].draw(pen)
        paths.append(f'<path transform="translate({x},{y}) scale(1,-1)" d="{pen.getCommands()}"/>')
        x += font["hmtx"][g][0]
h = asc + lead + desc
svg = OUT / "logos" / "nasa-name-2line.svg"
svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{100 * wmax / h:.1f}" height="100" '   # a page LaTeX can hold
              f'viewBox="0 0 {wmax} {h:.0f}" fill="#fff">{"".join(paths)}</svg>')
run("rsvg-convert", "-f", "pdf", str(svg), "-o", str(svg.with_suffix(".pdf")))
run("rsvg-convert", "-h", "240", str(svg), "-o", str(svg.with_suffix(".png")))
print("nasa-name-2line aspect", round(wmax / h, 4))
for name in LOGOS:
    w, h = Image.open(OUT / "logos" / f"{name}.png").size
    print(name, "aspect", round(w / h, 4))
