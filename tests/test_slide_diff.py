"""Check slide_diff.py, the per-slide pixel comparison of two builds (a Quarto bump's proof).

    python3 -m pytest tests/test_slide_diff.py

compare() counts the pixels that differ and boxes them, past a tolerance; the command compares two
directories' decks page by page (PDFs made here with Pillow, so no deck is built), says which slide
differs, writes its picture and fails; alike builds pass. The PDF leg needs poppler (pdftoppm).
"""

import importlib.util
import shutil
import subprocess
import sys

import pytest
from PIL import Image, ImageDraw

from conftest import ROOT

TOOL = ROOT / "common" / "utils" / "slide_diff.py"


@pytest.fixture(scope="module")
def slide_diff():
    spec = importlib.util.spec_from_file_location("slide_diff", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def page(mark=None, size=(320, 180)):
    im = Image.new("RGB", size, "#FFFFFF")
    ImageDraw.Draw(im).rectangle([20, 20, 120, 60], fill="#0057C2")
    if mark:
        ImageDraw.Draw(im).rectangle(mark, fill="#000000")
    return im


def test_compare_counts_and_boxes(slide_diff, tmp_path):
    faint = page()
    faint.putpixel((5, 5), (253, 255, 255))
    for name, im in (("a", page()), ("same", page()), ("b", page(mark=[200, 100, 209, 104])),
                     ("faint", faint), ("big", page(size=(322, 180)))):
        im.save(tmp_path / f"{name}.png")
    cmp = lambda x, **kw: slide_diff.compare(tmp_path / "a.png", tmp_path / f"{x}.png", **kw)
    assert cmp("same") == (0, None)
    assert cmp("b") == (50, (200, 100, 210, 105))
    assert cmp("faint") == (1, (5, 5, 6, 6)) and cmp("faint", tolerance=2) == (0, None)
    assert cmp("big") == (-1, None)


@pytest.mark.skipif(shutil.which("pdftoppm") is None, reason="needs poppler")
def test_the_command_names_the_slide_that_differs(tmp_path):
    a, b, c = (tmp_path / n for n in "abc")
    for d, second in ((a, page()), (b, page(mark=[200, 100, 209, 104])), (c, page())):
        d.mkdir()
        page().save(d / "deck.pdf", save_all=True, append_images=[second], resolution=72)
    page().save(c / "deck.pdf", save_all=True, append_images=[page(), page()], resolution=72)
    run = lambda *args: subprocess.run([sys.executable, str(TOOL), *map(str, args), "--format", "pdf"],
                                       capture_output=True, text=True)
    same = run(a, a)
    assert same.returncode == 0 and "deck pdf: 2 slides, alike" in same.stdout, same.stdout + same.stderr
    diff = run(a, b, "--out", tmp_path / "out")
    assert diff.returncode == 1 and "deck pdf slide 2:" in diff.stdout and "deck pdf: 2 slides, 1 differ" in diff.stdout, diff.stdout
    assert (tmp_path / "out" / "deck-pdf-s002.png").exists() and not (tmp_path / "out" / "deck-pdf-s001.png").exists()
    assert run(a, b, "--min-pixels", 10000).returncode == 0
    count = run(a, c)
    assert count.returncode == 1 and "deck pdf: 2 slides against 3" in count.stdout, count.stdout
    assert run(a, b, "nope").returncode == 1
