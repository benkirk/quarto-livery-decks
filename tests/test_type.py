"""Check livery_build.py's type scale: sizes in whole or half points on the livery's pptx canvas.

    python3 -m pytest tests/test_type.py

For every bundled livery: every role and list level is a multiple of 0.5 pt, the template's
slide size is the canvas, and every size in its master and layouts is a role's. Then the rules
on made-up liveries: the defaults, a canvas alone scaling them, a body alone carrying the body
roles and the levels, an explicit size winning, a flavor inheriting.
"""

import json
import re
import zipfile
from pathlib import Path

import livery_build as lb


def sizes_of(d: Path) -> tuple[dict, dict]:
    L, _ = lb.resolve(d)
    t = L["type"]
    return L, {k: v["pt"] for k, v in t["roles"].items()} | {f"levels[{i}]": v for i, v in enumerate(t["levels"])}


def test_sizes_whole_or_half_points(livery: Path):
    d = livery
    L, sizes = sizes_of(d)
    for k, v in sizes.items():
        assert v * 2 == int(v * 2), f"{d.name}: type {k} {v} is not a whole or half point"
    assert L["type"]["levels"][0] == L["type"]["roles"]["body"]["pt"], f"{d.name}: levels[0] is not the body"


def test_template_sizes_are_roles(livery: Path):
    d = livery
    L, sizes = sizes_of(d)
    t = L["type"]
    tmpl = d / L["pptx"].get("template", "template.pptx")
    assert tmpl.exists(), f"{d.name}: no {tmpl.name}"
    with zipfile.ZipFile(tmpl) as z:
        sld = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', z.read("ppt/presentation.xml").decode())
        assert (int(sld[1]), int(sld[2])) == (t["canvas"]["w"] * 12700, t["canvas"]["h"] * 12700), \
            f"{d.name}: template slide {sld[1]} x {sld[2]} EMU is not the canvas {t['canvas']}"
        xml = "".join(z.read(n).decode() for n in z.namelist() if re.match(r"ppt/slide(Master|Layout)s/[^/]+\.xml$", n))
    known = {round(v * 100) for v in sizes.values()}
    unknown = sorted({int(s) for s in re.findall(r'<a:defRPr[^>]* sz="(\d+)"', xml)} - known)
    assert not unknown, f"{d.name}: template sizes {[sz / 100 for sz in unknown]} pt are no type role's"


def resolve(tmp: Path, knobs: dict, parent: dict | None = None) -> dict:
    """The type scale of a made-up livery `x` of knobs, under a parent `base` when given."""
    for name, k in (("base", parent), ("x", knobs)):
        if k is None:
            continue
        (tmp / name).mkdir()
        (tmp / name / "_brand.yml").write_text("color: {palette: {blue: '#003366'}, primary: blue}\n")
        (tmp / name / "livery.yml").write_text(json.dumps({"schema": 1, "name": name, **k}))
    return lb.type_scale("x", lb.read(tmp / "x"))


def test_defaults(tmp_path):
    t = resolve(tmp_path, {})
    assert t["canvas"] == {"w": 960, "h": 540}, f"default canvas {t['canvas']}"
    assert {k: v["pt"] for k, v in t["roles"].items()} == {k: p for k, (p, _) in lb.TYPE.items()}, "defaults changed"
    assert t["levels"] == list(lb.LEVELS), f"default levels {t['levels']}"


def test_canvas_alone_scales(tmp_path):
    t = resolve(tmp_path, {"pptx": {"size": [10, 5.625]}})   # the NSF NCAR template's canvas, nothing else
    assert t["canvas"] == {"w": 720, "h": 405}, f"10 x 5.625 in canvas {t['canvas']}"
    # the defaults x 0.75, to the half point (halves up): the guide's own numbers are ncar's type:
    assert t["roles"]["body"]["pt"] == 12 and t["roles"]["frametitle"]["pt"] == 20.5 and t["roles"]["title"]["pt"] == 22, \
        f"canvas-scaled body/frametitle/title {[t['roles'][k]['pt'] for k in ('body', 'frametitle', 'title')]}"
    assert t["levels"] == [12, 11.5, 10, 9, 8.5], f"canvas-scaled levels {t['levels']}"


def test_body_alone_carries_body_roles(tmp_path):
    t = resolve(tmp_path, {"type": {"body": 20}})   # the body alone: body roles and levels follow, titles stay
    assert t["roles"]["table"]["pt"] == 16.5 and t["roles"]["frametitle"]["pt"] == 27, "body-only override"
    assert t["levels"] == [20, 19, 16.5, 15, 14], f"body-only levels {t['levels']}"


def test_explicit_size_wins(tmp_path):
    t = resolve(tmp_path, {"type": {"frametitle": 32, "levels": [16, 14, 13, 12, 11]}})
    assert t["roles"]["frametitle"]["pt"] == 32 and t["levels"][1] == 14, "explicit sizes"
    assert abs(t["roles"]["frametitle"]["size"] - 2) < 1e-9, "a role's ratio to the body"


def test_flavor_inherits(tmp_path):
    t = resolve(tmp_path, {"extends": "base"}, {"pptx": {"size": [10, 5.625]}, "type": {"subhead": 15}})
    assert t["canvas"]["h"] == 405 and t["roles"]["subhead"]["pt"] == 15, "a flavor inherits canvas and sizes"
