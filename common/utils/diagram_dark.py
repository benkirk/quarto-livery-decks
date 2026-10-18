#!/usr/bin/env python3
"""Turn a baked diagram PNG to the dark: lightness flipped, hue and saturation kept.

    diagram_dark.py <in.png> <out.png> <background hex> <foreground hex>

Mermaid and Graphviz draw dark lines and text on white. On a dark livery (livery.json "mode":
"dark") common/diagram-dark.lua sends each diagram Quarto baked for pptx and PDF through
this: every pixel's HLS lightness is inverted (c' = c + 255 - max - min, which keeps hue and
saturation), then black maps to the slide's background and white to its foreground, channel by
channel. White becomes the background, black text the foreground, a pale fill its dark shade of
the same hue. Alpha is kept. Pillow only (no numpy): the image's own channel math."""

import sys

from PIL import Image, ImageChops, ImageMath


def hexrgb(h: str) -> tuple[int, int, int]:
    return tuple(bytes.fromhex(h.lstrip("#")))


def dark(src: str, dst: str, bg: str, fg: str) -> None:
    im = Image.open(src).convert("RGBA")
    r, g, b, a = im.split()
    hi = ImageChops.lighter(ImageChops.lighter(r, g), b)
    lo = ImageChops.darker(ImageChops.darker(r, g), b)
    flip = [ImageMath.lambda_eval(lambda e: e["c"] + 255 - e["hi"] - e["lo"], c=c, hi=hi, lo=lo).convert("L")
            for c in (r, g, b)]
    out = [ch.point(lambda v, b0=b0, f0=f0: round(b0 + v * (f0 - b0) / 255))
           for ch, b0, f0 in zip(flip, hexrgb(bg), hexrgb(fg))]
    Image.merge("RGBA", (*out, a)).save(dst)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__.splitlines()[2].strip())
    dark(*sys.argv[1:])
