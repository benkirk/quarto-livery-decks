#!/usr/bin/env python3
"""Check livery_build.py's type scale: sizes in whole or half points on the livery's pptx canvas.

    tools/test_type.py [<framework liveries dir>]

For every engine livery and, when present, the framework's (benkirk/quarto-livery-decks
docs/common/liveries, or the argument): every role and list level is a multiple of 0.5 pt, the
template's slide size is the canvas, and every size in its master and layouts is a role's. Then
the rules on made-up liveries: the defaults, a canvas alone scaling them, a body alone carrying
the body roles and the levels, an explicit size winning, a flavor inheriting.
"""

import importlib.util
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "_extensions" / "engine"
spec = importlib.util.spec_from_file_location("livery_build", ENGINE / "livery_build.py")
lb = importlib.util.module_from_spec(spec); spec.loader.exec_module(lb)
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def check_livery(d: Path, template: bool):
    L, _ = lb.resolve(d)
    t = L["type"]
    sizes = {k: v["pt"] for k, v in t["roles"].items()} | {f"levels[{i}]": v for i, v in enumerate(t["levels"])}
    for k, v in sizes.items():
        check(v * 2 == int(v * 2), f"{d.name}: type {k} {v} is not a whole or half point")
    check(t["levels"][0] == t["roles"]["body"]["pt"], f"{d.name}: levels[0] is not the body")
    tmpl = d / L["pptx"].get("template", "template.pptx")
    if not template or not tmpl.exists():   # the framework's are rebuilt when it vendors the engine
        return
    with zipfile.ZipFile(tmpl) as z:
        sld = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', z.read("ppt/presentation.xml").decode())
        check((int(sld[1]), int(sld[2])) == (t["canvas"]["w"] * 12700, t["canvas"]["h"] * 12700),
              f"{d.name}: template slide {sld[1]} x {sld[2]} EMU is not the canvas {t['canvas']}")
        xml = "".join(z.read(n).decode() for n in z.namelist() if re.match(r"ppt/slide(Master|Layout)s/[^/]+\.xml$", n))
    known = {round(v * 100) for v in sizes.values()}
    for sz in sorted({int(s) for s in re.findall(r'<a:defRPr[^>]* sz="(\d+)"', xml)} - known):
        fails.append(f"{d.name}: template size {sz / 100} pt is no type role's")


def resolve(knobs: dict, parent: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, k in (("base", parent), ("x", knobs)):
            if k is None:
                continue
            (root / name).mkdir()
            (root / name / "_brand.yml").write_text("color: {palette: {blue: '#003366'}, primary: blue}\n")
            (root / name / "livery.yml").write_text(json.dumps(k))
        return lb.type_scale("x", lb.read(root / "x"))


def rules():
    t = resolve({})
    check(t["canvas"] == {"w": 960, "h": 540}, f"default canvas {t['canvas']}")
    check({k: v["pt"] for k, v in t["roles"].items()} == {k: p for k, (p, _) in lb.TYPE.items()}, "defaults changed")
    check(t["levels"] == list(lb.LEVELS), f"default levels {t['levels']}")
    t = resolve({"pptx": {"size": [10, 5.625]}})   # the NSF NCAR template's canvas, nothing else
    check(t["canvas"] == {"w": 720, "h": 405}, f"10 x 5.625 in canvas {t['canvas']}")
    # the defaults x 0.75, to the half point (halves up): the guide's own numbers are ncar's type:
    check(t["roles"]["body"]["pt"] == 12 and t["roles"]["frametitle"]["pt"] == 20.5 and t["roles"]["title"]["pt"] == 22,
          f"canvas-scaled body/frametitle/title {[t['roles'][k]['pt'] for k in ('body', 'frametitle', 'title')]}")
    check(t["levels"] == [12, 11.5, 10, 9, 8.5], f"canvas-scaled levels {t['levels']}")
    t = resolve({"type": {"body": 20}})   # the body alone: body roles and levels follow, titles stay
    check(t["roles"]["table"]["pt"] == 16.5 and t["roles"]["frametitle"]["pt"] == 27, "body-only override")
    check(t["levels"] == [20, 19, 16.5, 15, 14], f"body-only levels {t['levels']}")
    t = resolve({"type": {"frametitle": 32, "levels": [16, 14, 13, 12, 11]}})
    check(t["roles"]["frametitle"]["pt"] == 32 and t["levels"][1] == 14, "explicit sizes")
    check(abs(t["roles"]["frametitle"]["size"] - 2) < 1e-9, "a role's ratio to the body")
    t = resolve({"extends": "base"}, {"pptx": {"size": [10, 5.625]}, "type": {"subhead": 15}})
    check(t["canvas"]["h"] == 405 and t["roles"]["subhead"]["pt"] == 15, "a flavor inherits canvas and sizes")


def main():
    fw = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "quarto-livery-decks" / "docs" / "common" / "liveries"
    dirs = sorted(p for p in (ENGINE / "liveries").iterdir() if (p / "livery.yml").exists())
    if fw.is_dir():
        dirs += sorted(p for p in fw.iterdir() if (p / "livery.yml").exists() and not p.is_symlink())
    for d in dirs:
        check_livery(d, ENGINE in d.parents)
    rules()
    for f in fails:
        print("FAIL", f)
    print(f"type: {len(dirs)} liveries, {'all whole or half points' if not fails else f'{len(fails)} failures'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
