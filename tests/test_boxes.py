"""Check the boxes (livery.yml boxes:, livery_build.py BOXES): one set of numbers every format draws.

    python3 -m pytest tests/test_boxes.py

Every bundled livery's build/livery.json carries every box and key of BOXES, its fractions in
[0, 1], its pads two non-negative numbers, its colors hex; the css and the sty carry them too. A
livery's block merges over the defaults box by box; a color resolves from a role, a palette name or
a hex, and a name that is none of them, or an unknown key, fails with its path. The pptx caution
box takes its bar and pads from them (pptx_steps/slide_layout.py, in a subprocess under the
livery's LIVERY_DIR). Needs pandoc ($QUARTO_PANDOC) for that one.
"""

import json
import os
import re
import shutil
import subprocess
import sys

import pytest

import livery_build as lb

from conftest import ROOT, run

ENGINE = ROOT / "_extensions" / "engine"
HEX = re.compile(r"^#[0-9A-F]{6}$")
FRACTIONS = ("gap", "rule", "bar", "outline", "radius", "tint")


def test_every_key(livery):
    b = json.loads((livery / "build" / "livery.json").read_text())["boxes"]
    assert set(b) == set(lb.BOXES), f"{livery.name}: boxes {sorted(b)} are not BOXES'"
    for box, keys in lb.BOXES.items():
        assert set(b[box]) == set(keys), f"{livery.name}: boxes.{box} keys {sorted(b[box])}"
        for k, v in b[box].items():
            where = f"{livery.name}: boxes.{box}.{k} = {v!r}"
            if k == "roles":
                assert v and all(r in json.loads((livery / "build" / "livery.json").read_text())["roles"] for r in v), f"{where}: not roles"
            elif k in lb.BOX_COLORS.get(box, ()):
                assert HEX.match(v), f"{where} is not #RRGGBB"
            elif k in FRACTIONS:
                assert isinstance(v, (int, float)) and 0 <= v <= 1, f"{where} is not a fraction"
            else:
                assert k.endswith("pad") and len(v) == 2 and all(x >= 0 for x in v), f"{where} is not two pads"
    css = (livery / "build" / "livery.css").read_text()
    sty = (livery / "build" / "livery.sty").read_text()
    assert f"--engine-caution-pad: {b['caution']['pad'][0]:g}em {b['caution']['pad'][1]:g}em;" in css
    assert f"--engine-status-done: {b['status']['done']};" in css
    assert f"\\def\\engine@boxes@caution@padx{{{b['caution']['pad'][1]}}}" in sty
    assert f"\\definecolor{{EngineBoxesCardOutlineColor}}{{HTML}}{{{b['card']['outline-color'][1:]}}}" in sty
    assert "\\def\\engine@type@display{" in sty and "--engine-type-display:" in css


def test_merge_box_by_box():
    hexof = lambda c, k: c if c.startswith("#") else {"surface": "#F1F0EE"}.get(c, "#000000")
    b = lb.boxes({"card": {"radius": 0.012}, "lead": {"bar-color": "#123456"}}, hexof)
    assert b["card"]["radius"] == 0.012 and b["card"]["pad"] == lb.BOXES["card"]["pad"], "a key merges into its box"
    assert b["lead"]["bar-color"] == "#123456" and b["lead"]["fill"] == "#F1F0EE", "the box's other keys keep their defaults"
    assert b["caution"] == lb.BOXES["caution"], "an untouched box is the default"


def tmp_livery(tmp_path, boxes: str):
    """ncar copied into tmp_path with a boxes: block, built: (return code, stderr, livery.json)."""
    d = tmp_path / "liveries" / "ncar"
    shutil.copytree(ROOT / "liveries" / "ncar", d, ignore=shutil.ignore_patterns("build", "*.pptx", "reference"))
    y = d / "livery.yml"
    text = re.sub(r"\nboxes:.*?\n\n", "\n", y.read_text(), flags=re.S)   # ncar's own block out
    y.write_text(text.replace("\npptx:", f"\nboxes:\n{boxes}\npptx:", 1))
    r = run("build", d)
    j = json.loads((d / "build" / "livery.json").read_text()) if r.returncode == 0 else None
    return r.returncode, r.stderr, j


def test_colors_resolve(tmp_path):
    rc, err, j = tmp_livery(tmp_path, "  lead: {fill: secondary, bar-color: orange}\n  card: {outline-color: \"#6840f0\"}\n")
    assert rc == 0, err
    assert j["boxes"]["lead"]["fill"] == j["roles"]["secondary"], "a role"
    assert j["boxes"]["lead"]["bar-color"] == j["palette"]["orange"], "a palette name"
    assert j["boxes"]["card"]["outline-color"] == "#6840F0", "a hex, upper-cased"
    assert j["boxes"]["status"]["done"] == j["roles"]["highlight"], "the default, a role"


@pytest.mark.parametrize("boxes, expect", [
    ("  card: {radiuss: 0.01}\n", "boxes.card.radiuss: unknown key"),
    ("  grid: {gap: 0.01}\n", "boxes.grid: unknown key"),
    ("  lead: {fill: nope}\n", "boxes.lead.fill: 'nope' is neither a palette name nor a hex value"),
    ("  columns: {gap: 1.5}\n", "boxes.columns.gap: 1.5 is greater than the maximum of 1"),
    ("  caution: {pad: [0.5]}\n", "boxes.caution.pad: "),
    ("  card: {roles: [primary, nope]}\n", "boxes.card.roles[1]: 'nope' is neither"),
])
def test_refused_with_path(tmp_path, boxes, expect):
    rc, err, _ = tmp_livery(tmp_path, boxes)
    assert rc != 0 and expect in err, f"rc {rc}: {err.strip()!r}"


STEP = """
import sys
from pathlib import Path
from pptx import Presentation
from pptx_steps import slide_layout
prs = Presentation(sys.argv[1]); slide_layout.run(prs, Path(sys.argv[1])); prs.save(sys.argv[1])
"""


@pytest.mark.parametrize("name", ["ncar", "nasa-jsc-eg"])
def test_pptx_caution(pandoc_deck, tmp_path, name):
    """The caution box's bar is boxes.caution.bar of the canvas height, its pads em of the body."""
    md = "## Careful\n\nA warning.\n\n::: notes\nengine-layout: caution\n:::\n"
    pandoc_deck(tmp_path, md, "t.pptx")
    env = {**os.environ, "LIVERY_DIR": str(ROOT / "liveries" / name), "PYTHONPATH": str(ENGINE)}
    subprocess.run([sys.executable, "-c", STEP, str(tmp_path / "t.pptx")], env=env, check=True, capture_output=True)
    from pptx import Presentation
    from pptx.util import Pt
    j = json.loads((ROOT / "liveries" / name / "build" / "livery.json").read_text())
    body, c = j["type"]["roles"]["body"]["pt"], j["boxes"]["caution"]
    slide = Presentation(str(tmp_path / "t.pptx")).slides[0]
    bars = [sh for sh in slide.shapes if not sh.is_placeholder and sh.shape_type == 1]   # autoshapes
    assert [b.width for b in bars] == [round(c["bar"] * Pt(j["type"]["canvas"]["h"]))], "one bar, its width the fraction"
    tf = next(sh for sh in slide.placeholders if sh.has_text_frame and "warning" in sh.text_frame.text).text_frame
    assert (tf.margin_top, tf.margin_left) == (round(c["pad"][0] * body * 12700), round(c["pad"][1] * body * 12700)), \
        "pads in em of the body"
