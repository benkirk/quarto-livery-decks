"""Check a columns slide's frames in the pptx (grid-pptx.lua, then pptx_steps/columns.py).

    python3 -m pytest tests/test_grid.py

pandoc writes a deck on the livery's template with grid-pptx.lua (slide-layout.lua's `wide` line
written by hand: that filter needs Quarto), then the driver's steps run in a subprocess under the
livery's LIVERY_DIR. A 55/45 slide's placeholders are the shares of the content box less the gap,
within 1 EMU; a picture pandoc put at the old half frame moves into its column and scales to its
width, its aspect kept; a {.wide} slide's box starts at geometry.wide-margin, its Title and Content
body too; every offset, extent and size is an integer EMU. Under ncar and nasa-jsc-eg (another
canvas, a dark livery). Needs pandoc ($QUARTO_PANDOC).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

import pytest

from conftest import ROOT

ENGINE = ROOT / "_extensions" / "engine"
IMAGE = ROOT / "decks" / "quickstart" / "images" / "example.jpg"
WIDE = "\n::: notes\nengine-layout: wide\n:::\n"
MD = ('## Split\n\n:::: {.columns}\n::: {.column width="55%"}\n- One\n- Two\n:::\n::: {.column}\n![](p.jpg)\n:::\n::::\n\n'
      '## Wide\n\n:::: {.columns}\n::: {.column}\nLeft\n:::\n::: {.column}\nRight\n:::\n::::\n' + WIDE + '\n'
      '## Wide text\n\nA paragraph.\n' + WIDE)
STEP = """
import sys
from pathlib import Path
from pptx import Presentation
from pptx_steps import columns, slide_layout
p = Path(sys.argv[1]); prs = Presentation(p)
slide_layout.run(prs, p); columns.run(prs, p.name); prs.save(p)
"""   # the driver's order


@pytest.fixture(scope="module", params=["ncar", "nasa-jsc-eg"])
def deck(request, tmp_path_factory):
    name = request.param
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not pandoc:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")
    tmp = tmp_path_factory.mktemp(f"grid-{name}")
    shutil.copy(IMAGE, tmp / "p.jpg")
    d = ROOT / "liveries" / name
    out = tmp / "t.pptx"
    subprocess.run([pandoc, "--lua-filter", str(ENGINE / "grid-pptx.lua"), "--reference-doc", str(d / "template.pptx"),
                    "-o", str(out)], input=MD, text=True, cwd=tmp, check=True, capture_output=True)
    env = {**os.environ, "LIVERY_DIR": str(d), "PYTHONPATH": str(ENGINE)}
    subprocess.run([sys.executable, "-c", STEP, str(out)], env=env, check=True, capture_output=True)
    from pptx import Presentation
    return json.loads((d / "build" / "livery.json").read_text()), Presentation(str(out)), out


def boxes(livery, width, shares, wide=False):
    g = livery["geometry"]
    m, gap = g["wide-margin" if wide else "margin"], livery["boxes"]["columns"]["gap"]
    room, x, out = 1 - 2 * m - gap * (len(shares) - 1), m, []
    for s in shares:
        out.append((x * width, room * s * width))
        x += room * s + gap
    return out


def body_placeholders(slide):
    return {sh.placeholder_format.idx: sh for sh in slide.placeholders if sh.placeholder_format.idx in (1, 2)}


def test_shares(deck):
    livery, prs, _ = deck
    slide = prs.slides[0]
    (x1, w1), (x2, w2) = boxes(livery, prs.slide_width, [0.55, 0.45])
    ph = body_placeholders(slide)
    assert abs(ph[1].left - x1) <= 1 and abs(ph[1].width - w1) <= 1, f"left column {ph[1].left, ph[1].width}, want {x1, w1}"
    pic = next(sh for sh in slide.shapes if sh.shape_type == 13)
    assert abs(pic.width - w2) <= 1 and abs(pic.left - x2) <= 1, f"the picture {pic.left, pic.width}, want {x2, w2}"
    from PIL import Image
    iw, ih = Image.open(IMAGE).size
    assert abs(pic.height / pic.width - ih / iw) < 0.01, "the picture's aspect"
    assert not slide.notes_slide.notes_text_frame.text.strip().startswith("engine-columns"), "the line left in the notes"


def test_wide(deck):
    livery, prs, _ = deck
    (x1, w1), (x2, w2) = boxes(livery, prs.slide_width, [0.5, 0.5], wide=True)
    ph = body_placeholders(prs.slides[1])
    assert abs(ph[1].left - x1) <= 1 and abs(ph[2].left - x2) <= 1 and abs(ph[2].width - w2) <= 1, \
        f"wide columns {[(p.left, p.width) for p in ph.values()]}, want {x1, x2, w2}"
    m = livery["geometry"]["wide-margin"]
    body = body_placeholders(prs.slides[2])[1]
    assert abs(body.left - m * prs.slide_width) <= 1 and abs(body.width - (1 - 2 * m) * prs.slide_width) <= 1, \
        "a wide Title and Content body"
    assert body.top > 0 and body.height > 0, "the body's top and height kept (all four fields set)"


def test_integers(deck):
    *_, out = deck
    with zipfile.ZipFile(out) as z:
        xml = "".join(z.read(n).decode() for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n))
    floats = re.findall(r'\b(x|y|cx|cy|w|h|sz|marL|indent|adj)="-?[0-9]+\.[0-9]+"', xml)
    assert not floats, f"non-integer EMUs: {floats[:5]}"
