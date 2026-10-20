#!/usr/bin/env python3
"""Check livery.yml's schema (_extensions/engine/livery.schema.json).

    tests/test_schema.py

Every bundled livery passes as written; the schema names exactly the engine's own sets (type roles,
compositions and their parts, theme slots, blends, roles, installed faces, art kinds); a livery
without `schema:`, with an unknown schema number, a misspelt key or an out-of-range fraction is
refused with the path and the reason, by the schema and by `livery build` itself; the committed
liveries/REFERENCE.md is the schema's.
"""

import copy
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "_extensions" / "engine"
sys.path.insert(0, str(ENGINE))
import livery_build as lb   # noqa: E402  (the engine's tools import each other by name)
S = lb.schema()
fails = []


def check(ok, what):
    if not ok:
        fails.append(what)


def files(d: Path):
    return (yaml.safe_load((d / "livery.yml").read_text()) or {}, yaml.safe_load((d / "_brand.yml").read_text()) or {})


# every bundled livery, as written
liveries = sorted(p.parent for p in (ROOT / "liveries").glob("*/livery.yml"))
for d in liveries:
    errors = S.check(*files(d), d)
    check(not errors, f"{d.name}: {errors}")
    check((d / "livery.yml").read_text().startswith("# yaml-language-server: $schema=../../_extensions/engine/livery.schema.json\nschema: 1\n"),
          f"{d.name}: livery.yml does not start with the editor line and schema: 1")

# the schema's sets are the engine's
sch = S.load()
P = sch["properties"]
check(set(P["type"]["properties"]) == set(lb.TYPE) | {"levels"}, "type roles differ from TYPE")
check(set(P["compositions"]["properties"]) == set(lb.COMPOSITIONS), "compositions differ from COMPOSITIONS")
for name, c in P["compositions"]["properties"].items():
    check(set(c["properties"]) == set(lb.COMP_KEYS), f"compositions.{name} parts differ from COMP_KEYS")
check(set(P["pptx"]["properties"]["scheme"]["properties"]) == set(lb.SLOT_ROLES), "pptx.scheme slots differ from SLOT_ROLES")
check(set(P["blends"]["properties"]) == {k for k, *_ in lb.BLENDS}, "blends differ from BLENDS")
check(set(P["roles"]["properties"]) >= set(lb.ROLE_TEX), "a ROLE_TEX role is missing from roles")
check(set(P["art"]["properties"]) == set(lb.ART_KINDS) | {"waves"}, "art differs from ART_KINDS")
check(set(P["feature"]["properties"]["style"]["enum"]) == set(lb.FEATURE_STYLES), "feature.style differs from FEATURE_STYLES")
check(set(P["frametitle"]["properties"]) == set(lb.FRAMETITLE), "frametitle differs from FRAMETITLE")
faces = P["installed-fonts"]["properties"]["base"]["oneOf"][1]["properties"]["faces"]["properties"]
check(set(faces) == set(lb.FACE_KEYS), "installed-fonts faces differ from FACE_KEYS")
check(set(lb.BAND) <= set(P["title"]["properties"]), "a BAND key is missing from title")
for k, v in lb.BAND.items():
    check(P["title"]["properties"][k].get("default") == v, f"title.{k}'s default is not BAND's {v}")

# refusals, each with its path and reason
ncar = ROOT / "liveries" / "ncar"
knobs, brand = files(ncar)


def errors_for(change):
    k = copy.deepcopy(knobs)
    change(k)
    return S.check(k, brand, ncar)


cases = {
    "no schema": (lambda k: k.pop("schema"), "livery.yml: (top): 'schema' is required"),
    "schema 2": (lambda k: k.update(schema=2), "livery.yml: schema: 2 is not a schema this engine reads (1)"),
    "misspelt key": (lambda k: k["geometry"]["logo"].update(corne="top-left"), "livery.yml: geometry.logo.corne: unknown key"),
    "unknown top key": (lambda k: k.update(aspect="16:9"), "livery.yml: aspect: unknown key"),
    "fraction > 1": (lambda k: k["geometry"].update(margin=1.5), "livery.yml: geometry.margin: 1.5 is greater than the maximum of 1"),
    "bad corner": (lambda k: k["geometry"]["logo"].update(corner="middle"), "livery.yml: geometry.logo.corner: 'middle' is not one of"),
    "bad hex": (lambda k: k["roles"].update(accent="#FAA1"), "livery.yml: roles.accent: '#FAA1' is not"),
    "charts key": (lambda k: k["charts"].update(colours=[]), "livery.yml: charts.colours: unknown key"),
    "charts dark key": (lambda k: k["charts"].setdefault("dark", {}).update(cycle=[]), "livery.yml: charts.dark.cycle: unknown key"),
    "waves of two lines": (lambda k: k["art"]["waves"].update(lines=k["art"]["waves"]["lines"][:2]), "livery.yml: art.waves.lines: "),
    "type levels": (lambda k: k["type"].update(levels=[12, 11]), "livery.yml: type.levels: "),
}
for what, (change, expect) in cases.items():
    errs = errors_for(change)
    check(any(expect in e for e in errs), f"{what}: expected {expect!r}, got {errs}")

# `livery build` refuses one too, naming the file, path and reason
with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp) / "liveries"
    for name in ("ncar", "ucar"):
        shutil.copytree(ROOT / "liveries" / name, t / name, ignore=shutil.ignore_patterns("build", "*.pptx", "reference"))
    y = t / "ucar" / "livery.yml"
    y.write_text(y.read_text().replace("\nsection:", "\nsection:\n  lable: Part", 1))
    r = subprocess.run([sys.executable, str(ENGINE / "livery.py"), "build", str(t / "ucar")], capture_output=True, text=True)
    check(r.returncode != 0 and f"{t / 'ucar' / 'livery.yml'}: section.lable: unknown key" in r.stderr,
          f"livery build on a misspelt key: rc {r.returncode}, {r.stderr.strip()!r}")

# the reference is the schema's
check((ROOT / "liveries" / "REFERENCE.md").read_text() == S.doc(), "liveries/REFERENCE.md is stale (livery schema --doc)")

if fails:
    print("schema:", *fails, sep="\n  ")
    sys.exit(1)
print(f"schema: {len(liveries)} liveries valid, {len(cases) + 1} refusals with their paths, the reference current")
