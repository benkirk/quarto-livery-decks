"""Check a cover's full-width field in the PDF: the background under the photo, as HTML and pptx (#125).

    python3 -m pytest tests/test_cover_field.py

A tmp flavor of ncar gives its photo cover a field the slide's full size; the photo fixture
(decks/fixtures/photo.qmd, a titlegraphic: cover) rendered to PDF under it shows the photo at the
slide's center, not the field's color (beamer drew the field over the photo). ncar's own half
field keeps its order (parity-latex). Renders a deck: needs Quarto and XeLaTeX (the env).
"""

import os
import shutil
import subprocess

from conftest import ROOT, run

NAME = "fullfield"


def test_full_field_under_photo(tmp_path):
    liv = tmp_path / "liveries"
    shutil.copytree(ROOT / "liveries" / "ncar", liv / "ncar", ignore=shutil.ignore_patterns("reference"))
    d = liv / NAME; d.mkdir()
    (d / "_brand.yml").write_text("{}\n")
    (d / "livery.yml").write_text(f"schema: 1\nname: {NAME}\nextends: ncar\n"
                                  "compositions:\n  title-photo:\n    field: {box: [0, 0, 1, 1]}\n")
    assert run("build", d).returncode == 0
    deck = tmp_path / "deck"; deck.mkdir()
    src = ROOT / "decks" / "fixtures"
    for f in ("photo.qmd", "_body.qmd"):
        shutil.copy(src / f, deck / f)
    shutil.copytree(src / "images", deck / "images")
    (deck / "Makefile").write_text(f"DECKS := photo\ninclude {ROOT / 'Make.common'}\n")
    env = {k: v for k, v in os.environ.items() if k not in ("LIVERY", "LIVERY_DIR")}
    r = subprocess.run(["make", "-C", str(deck), "pdf", f"LIVERY_DIR={d}"], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    subprocess.run(["pdftoppm", "-r", "30", "-png", "-f", "1", "-l", "1", str(deck / "photo.pdf"), str(tmp_path / "p")], check=True)
    from PIL import Image
    im = Image.open(next(tmp_path.glob("p*.png"))).convert("RGB")
    field = tuple(bytes.fromhex(__import__("json").loads((d / "build" / "livery.json").read_text())["roles"]["primary"][1:]))
    px = im.getpixel((im.width // 2 + im.width // 8, im.height // 2))   # inside the photo's box (x 0.48-1)
    assert max(abs(a - b) for a, b in zip(px, field)) > 40, f"the field {field} over the photo at the center: {px}"
