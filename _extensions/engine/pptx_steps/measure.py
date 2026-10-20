"""Text measured in the livery's own fonts (PIL): the pptx steps' one measurer. It counts the lines
paragraphs wrap to in a width, greedily, as PowerPoint wraps them.

Sizes and widths are the revealjs theme's slide pixels (1600 x 900 over the livery's canvas,
livery.json type.canvas): font() takes points of type, lines() and runs_lines() a width in
pixels. A face is the one the pptx sets, measured in the livery's bundled files
(livery.font_file): its typeface is the base family's stand-in (cu's Helvetica Neue measures as
TeX Gyre Heros), titles take the headings family only when the livery names a pptx
heading-typeface (else the template sets them in the typeface too), and a face the livery does
not bundle, pandoc's Courier for code, advances 0.6 em a character, as Courier does."""

import functools
import re

from PIL import ImageFont

import livery as livery_mod

LIVERY = livery_mod.load()
CANVAS = LIVERY["type"]["canvas"]
PX = CANVAS["w"] * 12700 / 1600             # EMU per slide pixel
PT_PX = CANVAS["h"] / 900                   # points of type per slide pixel
TYPE = LIVERY["typography"]
PPTX = LIVERY["pptx"]
BODY = TYPE["base"]                                            # the pptx's body text
TITLE = TYPE["headings"] if PPTX.get("heading-typeface") else BODY   # its titles (+mj-lt)
BUNDLED = {f["family"] for f in TYPE.get("fonts", []) if f.get("files")}
PPTX_FACES = {PPTX.get("typeface"): BODY, PPTX.get("heading-typeface"): TYPE.get("headings")}


class _Mono:
    """A face the livery does not bundle (pandoc's Courier): 0.6 em a character."""
    def __init__(self, px):
        self.px = px

    def getlength(self, text):
        return 0.6 * self.px * len(text)


@functools.lru_cache
def font(family, weight, pt):
    """The family's face at weight (400 when it has no such file) and pt points."""
    try:
        path = livery_mod.font_file(LIVERY, family, weight)
    except FileNotFoundError:
        path = livery_mod.font_file(LIVERY, family, 400)
    # BASIC, always: Pillow shapes with Raqm (HarfBuzz) whenever it can load a FriBiDi library at
    # run time, so the same text measured differently on a machine that had one (conda-forge
    # librsvg brings it) and moved a wrap
    return ImageFont.truetype(str(path), round(pt / PT_PX), layout_engine=ImageFont.Layout.BASIC)


def face(name, family, weight, pt):
    """The face a run named `name` (None: the placeholder's own, `family`) is shown in."""
    if name is None:
        return font(family, weight, pt)
    if name in BUNDLED:
        return font(name, weight, pt)
    if PPTX_FACES.get(name):
        return font(PPTX_FACES[name], weight, pt)
    return _Mono(pt / PT_PX)


def lines(paragraphs, font, width):
    """How many lines `paragraphs` (strings in one face) wrap to in `width` px."""
    n = 0
    for text in paragraphs:
        line = ""
        n += 1
        for word in text.split():
            trial = f"{line} {word}" if line else word
            if line and font.getlength(trial) > width:
                n, line = n + 1, word
            else:
                line = trial
    return n


def runs_lines(pieces, width):
    """How many lines one paragraph of (text, face) pieces wraps to in `width` px; a "\v" (a
    line break) starts a new line."""
    rows = [[]]
    for text, f in pieces:
        for i, part in enumerate(text.split("\v")):
            if i:
                rows.append([])
            if part:
                rows[-1].append((part, f))
    return sum(_wrap(row, width) for row in rows)


def _wrap(pieces, width):
    """Greedy, by words: a word's width the sum of its pieces' (one may cross runs: a code span
    and its comma), the space after it its run's."""
    words, cur, have = [], 0.0, False   # [width, space after]
    for text, f in pieces:
        for tok in re.split(r"(\s+)", text):
            if not tok:
                continue
            if tok.isspace():
                if have:
                    words.append([cur, f.getlength(" ")])
                    cur, have = 0.0, False
                elif words:
                    words[-1][1] = f.getlength(" ")
            else:
                cur, have = cur + f.getlength(tok), True
    if have:
        words.append([cur, 0.0])
    n, x, gap = 1, None, 0.0
    for w, space in words:
        if x is None:
            x = w
        elif x + gap + w > width:
            n, x = n + 1, w
        else:
            x += gap + w
        gap = space
    return n
