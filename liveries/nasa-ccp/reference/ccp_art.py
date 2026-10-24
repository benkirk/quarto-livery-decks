"""Build the CCP livery's art and marks from the CCP PowerPoint template and the vector logos.
usage: python3 -I ccp_art.py <CCP template.pptx> <livery dir>

The art is drawn here, not rendered: the template's furniture is two pictures and a gradient, all on
white. Its title bar (a 1280 x 90 JPEG) and cover banner (2000 x 364) each have the NASA insignia
baked into them as a small bitmap; it is painted out (each row interpolated across its box, on a sky
that is smooth there) and the bar gets the insignia back from the vector, liveries/nasa/logos/
meatball.svg, at the art's resolution. The cover's insignia is a composition mark instead (vector in
every format). The CUI banner, the legend, the CCP emblem and the notices are the engine's.

The CCP emblem and lockup are NASA's own vectors (the CCP Program Collector Card, 2014), from
Wikimedia Commons, public domain in the US, use restricted by 14 CFR 1221 (reference/notes.md):
fetched once into logos/*.svg, then rendered to PNG (HTML, pptx) and PDF (beamer, still vector).
The template's sample slide is never read, so none of its talk reaches the livery."""
import io, subprocess, sys, urllib.request
from pathlib import Path
from pptx import Presentation
from PIL import Image, ImageFilter

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
NASA = OUT.parent / "nasa" / "logos" / "meatball.svg"
COMMONS = "https://upload.wikimedia.org/wikipedia/commons/"
LOGOS = {   # name: the Commons file (File:NASA_Commercial_Crew_Program_logo....svg)
    "ccp-lockup": COMMONS + "e/ee/NASA_Commercial_Crew_Program_logo.svg",              # with the wordmark
    "ccp-emblem": COMMONS + "c/cb/NASA_Commercial_Crew_Program_logo_%28cropped%29.svg",  # the emblem alone
}
W, H = 3840, 2160   # the art's pixels (16:9): the insignia in the bar is drawn from the vector at this size
SLATE = (0x41, 0x55, 0x6B)   # the section band's foot color (the layout's gradient stop)
EMU_W, EMU_H = 12192000, 6858000


def run(*a):
    return subprocess.run(a, check=True, capture_output=True).stdout


def box(shape):
    """a shape's box in art pixels"""
    return (round(shape.left / EMU_W * W), round(shape.top / EMU_H * H),
            round(shape.width / EMU_W * W), round(shape.height / EMU_H * H))


def insignia_box(im):
    """the baked insignia's box in the picture's pixels: its blue sphere and red swoosh, padded (it
    sits in the picture's right tenth in both; the cover's photo has red and blue elsewhere)"""
    px, (w, h) = im.load(), im.size
    hits = [(x, y) for y in range(h) for x in range(int(w * 0.88), w)
            if (lambda r, g, b: (b > r + 60 and b > 120) or (r > 150 and g < 90 and b < 110))(*px[x, y][:3])]
    xs, ys = [p[0] for p in hits], [p[1] for p in hits]
    pad = max(2, w // 400)
    return max(min(xs) - pad, 0), max(min(ys) - pad, 0), min(max(xs) + pad, w - 1), min(max(ys) + pad, h - 1)


def paint_out(im, b):
    """each row of box b interpolated between the pixels just outside it (the right edge's own
    column when the box reaches it); the sky behind is a smooth gradient there"""
    px, (w, _) = im.load(), im.size
    x0, y0, x1, y1 = b
    for y in range(y0, y1 + 1):
        left = px[max(x0 - 1, 0), y]
        right = px[x1 + 1, y] if x1 + 1 < w else left
        for x in range(x0, x1 + 1):
            t = (x - x0 + 1) / (x1 - x0 + 2)
            px[x, y] = tuple(round(l + (r - l) * t) for l, r in zip(left, right))
    return im


def svg_png(svg, height):
    return Image.open(io.BytesIO(run("rsvg-convert", "-h", str(height), str(svg)))).convert("RGBA")


def place_insignia(art, pic_box, pic_size, b):
    """the vector insignia, centered on the baked one's box b (picture pixels) mapped into the art"""
    (px0, py0, pw, ph), (iw, ih) = pic_box, pic_size
    x0, y0, x1, y1 = px0 + b[0] * pw / iw, py0 + b[1] * ph / ih, px0 + (b[2] + 1) * pw / iw, py0 + (b[3] + 1) * ph / ih
    m = svg_png(NASA, round((y1 - y0) * 0.92))
    art.alpha_composite(m, (round((x0 + x1 - m.width) / 2), round((y0 + y1 - m.height) / 2)))
    return x0, y0, x1, y1


prs = Presentation(SRC)
master = prs.slide_masters[0]
layouts = {l.name: l for l in master.slide_layouts}
shape = lambda shapes, name: next(s for s in shapes if s.name == name)
(OUT / "art").mkdir(exist_ok=True); (OUT / "logos").mkdir(exist_ok=True)

# the title bar: the insignia painted out, the JPEG's blocks smoothed (a gradient has no detail)
bar_shape = shape(master.shapes, "Picture 10")
bar = Image.open(io.BytesIO(bar_shape.image.blob)).convert("RGB")
bar_ins = insignia_box(bar)
bar = paint_out(bar, bar_ins).filter(ImageFilter.GaussianBlur(1.2))
bx, by, bw, bh = box(bar_shape)
bx, bw = 0, W   # the picture overhangs the slide by a hair at the left; flush here


def with_bar():
    art = Image.new("RGBA", (W, H), "white")
    art.paste(bar.resize((bw, bh), Image.LANCZOS), (bx, by))
    place_insignia(art, (bx, by, bw, bh), bar.size, bar_ins)
    return art


# content slides: white, the bar with the vector insignia
with_bar().convert("RGB").save(OUT / "art" / "content.jpg", quality=88, optimize=True)

# dividers: the bar, and the band under it, slate at its top fading to white by its middle
band = shape(layouts["Section Title Page"].shapes, "Text Placeholder 7")
art = with_bar()
_, ty, _, th = box(band)
top = by + bh   # the band starts where the bar ends (the layout's box starts a hair above it)
for y in range(top, ty + th):
    t = min(1, (y - top) / (0.51 * (ty + th - top)))   # 0 at the top (slate), 1 at the middle (white)
    art.paste(tuple(round(s + (255 - s) * t) for s in SLATE), (0, y, W, y + 1))
art.convert("RGB").save(OUT / "art" / "section.jpg", quality=88, optimize=True)

# the cover: white, the banner (Dragon, Starliner, the station) with its insignia painted out; the
# composition's mark draws it back, in vector
cover = shape(layouts["Title Slide1"].shapes, "Picture 1")
banner = Image.open(io.BytesIO(cover.image.blob)).convert("RGB")
ban_ins = insignia_box(banner)
patched = paint_out(banner.copy(), ban_ins)
soft = patched.filter(ImageFilter.GaussianBlur(3))   # the painted box only, feathered into the sky
mask = Image.new("L", banner.size, 0)
mask.paste(255, (ban_ins[0] - 4, ban_ins[1], ban_ins[2] + 5, ban_ins[3] + 5))
patched.paste(soft, mask=mask.filter(ImageFilter.GaussianBlur(3)))
cx, cy, cw, ch = box(cover)
cx, cw = 0, W
art = Image.new("RGB", (W, H), "white")
art.paste(patched.resize((cw, ch), Image.LANCZOS), (cx, cy))
art.save(OUT / "art" / "title.jpg", quality=88, optimize=True)
iw, ih = banner.size
x0, y0 = cx + ban_ins[0] * cw / iw, cy + ban_ins[1] * ch / ih
x1, y1 = cx + (ban_ins[2] + 1) * cw / iw, cy + (ban_ins[3] + 1) * ch / ih
print("cover insignia box", [round(x0 / W, 4), round(y0 / H, 4), round((x1 - x0) / W, 4), round((y1 - y0) / H, 4)])
print("bar", [0, round(by / H, 4), 1, round(bh / H, 4)])

# the CCP marks: the Commons vectors, kept as fetched; PNG for HTML and pptx, PDF for beamer
for name, url in LOGOS.items():
    svg = OUT / "logos" / f"{name}.svg"
    if not svg.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "quarto-livery-decks (livery build script)"})
        svg.write_bytes(urllib.request.urlopen(req).read())
    run("rsvg-convert", "-f", "pdf", str(svg), "-o", str(svg.with_suffix(".pdf")))
    png = svg_png(svg, 600)
    png.save(svg.with_suffix(".png"), optimize=True)
    print(name, "aspect", round(png.width / png.height, 4))
