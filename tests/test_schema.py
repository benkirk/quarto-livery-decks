"""Check livery.yml's schema (_extensions/engine/livery.schema.json).

    python3 -m pytest tests/test_schema.py

Every bundled livery passes as written; the schema names exactly the engine's own sets (type roles,
compositions and their parts, theme slots, blends, roles, installed faces, art kinds); a livery
without `schema:`, with an unknown schema number, a misspelt key or an out-of-range fraction is
refused with the path and the reason, by the schema and by `livery build` itself; the committed
liveries/REFERENCE.md is the schema's (so `make test` needs no `livery schema --doc --check`).
"""

import copy
import shutil
from pathlib import Path

import pytest
import yaml

import livery_build as lb

from conftest import ROOT, run

S = lb.schema()


def files(d: Path):
    return (yaml.safe_load((d / "livery.yml").read_text()) or {}, yaml.safe_load((d / "_brand.yml").read_text()) or {})


def test_livery_valid(livery: Path):
    d = livery
    errors = S.check(*files(d), d)
    assert not errors, f"{d.name}: {errors}"
    assert (d / "livery.yml").read_text().startswith("# yaml-language-server: $schema=../../_extensions/engine/livery.schema.json\nschema: 1\n"), \
        f"{d.name}: livery.yml does not start with the editor line and schema: 1"


def test_sets_are_the_engines():
    P = S.load()["properties"]
    assert set(P["type"]["properties"]) == set(lb.TYPE) | {"levels", "tracking"}, "type roles differ from TYPE"
    assert P["type"]["properties"]["tracking"]["default"] == lb.TRACKING, "type.tracking's default is not TRACKING"
    assert set(P["compositions"]["properties"]) == set(lb.COMPOSITIONS), "compositions differ from COMPOSITIONS"
    for name, c in P["compositions"]["properties"].items():
        assert c["$ref"] == "#/$defs/composition", f"compositions.{name} is not a $defs.composition"
    assert set(S.load()["$defs"]["composition"]["properties"]) == set(lb.COMP_KEYS), "composition parts differ from COMP_KEYS"
    assert set(P["pptx"]["properties"]["scheme"]["properties"]) == set(lb.SLOT_ROLES), "pptx.scheme slots differ from SLOT_ROLES"
    assert set(P["blends"]["properties"]) == {k for k, *_ in lb.BLENDS}, "blends differ from BLENDS"
    assert set(P["roles"]["properties"]) >= set(lb.ROLE_TEX), "a ROLE_TEX role is missing from roles"
    assert set(P["art"]["properties"]) == set(lb.ART_KINDS) | {"waves"}, "art differs from ART_KINDS"
    assert set(P["feature"]["properties"]["style"]["enum"]) == set(lb.FEATURE_STYLES), "feature.style differs from FEATURE_STYLES"
    assert set(P["frametitle"]["properties"]) == set(lb.FRAMETITLE), "frametitle differs from FRAMETITLE"
    for k, v in lb.FRAMETITLE.items():
        assert P["frametitle"]["properties"][k].get("default") == v, f"frametitle.{k}'s default is not FRAMETITLE's {v}"
    for k, v in lb.SECTION.items():
        assert P["section"]["properties"][k].get("default") == v, f"section.{k}'s default is not SECTION's {v}"
    assert set(P["boxes"]["properties"]) == set(lb.BOXES), "boxes differ from BOXES"
    for box, keys in lb.BOXES.items():
        B = P["boxes"]["properties"][box]["properties"]
        assert set(B) == set(keys), f"boxes.{box} differs from BOXES"
        for k, v in keys.items():
            assert B[k].get("default") == v, f"boxes.{box}.{k}'s default is not BOXES' {v}"
    faces = P["installed-fonts"]["properties"]["base"]["oneOf"][1]["properties"]["faces"]["properties"]
    assert set(faces) == set(lb.FACE_KEYS), "installed-fonts faces differ from FACE_KEYS"
    assert set(lb.BAND) <= set(P["title"]["properties"]), "a BAND key is missing from title"
    for k, v in lb.BAND.items():
        assert P["title"]["properties"][k].get("default") == v, f"title.{k}'s default is not BAND's {v}"


# refusals, each with its path and reason, on ncar's files
NCAR = ROOT / "liveries" / "ncar"
CASES = {
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


@pytest.mark.parametrize("what", list(CASES))
def test_refusal(what):
    change, expect = CASES[what]
    knobs, brand = files(NCAR)
    k = copy.deepcopy(knobs)
    change(k)
    errs = S.check(k, brand, NCAR)
    assert any(expect in e for e in errs), f"{what}: expected {expect!r}, got {errs}"


def test_build_refuses_with_path(tmp_path):
    """`livery build` refuses one too, naming the file, path and reason."""
    t = tmp_path / "liveries"
    for name in ("ncar", "ucar"):
        shutil.copytree(ROOT / "liveries" / name, t / name, ignore=shutil.ignore_patterns("build", "*.pptx", "reference"))
    y = t / "ucar" / "livery.yml"
    y.write_text(y.read_text().replace("\nsection:", "\nsection:\n  lable: Part", 1))
    r = run("build", t / "ucar")
    assert r.returncode != 0 and f"{t / 'ucar' / 'livery.yml'}: section.lable: unknown key" in r.stderr, \
        f"livery build on a misspelt key: rc {r.returncode}, {r.stderr.strip()!r}"


def test_reference_is_current():
    assert (ROOT / "liveries" / "REFERENCE.md").read_text() == S.doc(), "liveries/REFERENCE.md is stale (livery schema --doc)"


def test_flavor_unsets_with_null(tmp_path):
    """A flavor unsets an inherited key with null (art.*, typography.monospace): it builds, its json
    has null where the parent had a file, and livery check passes."""
    t = tmp_path / "liveries"
    for name in ("nasa", "nasa-dark"):   # nasa-dark extends nasa; nasa has the Earth limb and DM Mono
        shutil.copytree(ROOT / "liveries" / name, t / name, ignore=shutil.ignore_patterns("build", "reference"))
    d = t / "unset"; d.mkdir()
    (d / "_brand.yml").write_text("typography:\n  monospace: null\n")
    (d / "livery.yml").write_text("schema: 1\nname: unset\nextends: nasa-dark\nart:\n  titlegraphic: null\n")
    r = run("all", d)
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    import json
    j = json.loads((d / "build" / "livery.json").read_text())
    assert j["art"]["titlegraphic"] is None and j["typography"]["monospace"] is None, "null did not reach the json"
    assert "--r-code-font" not in (d / "build" / "livery.css").read_text(), "the parent's code face kept"


def test_latex_roles(livery: Path):
    """build/livery.json `latex.roles` names the TeX color of every role and blend (the beamer filter's
    one table for a card's or strip's role=): ROLE_TEX for the roles the livery has, Brand<Camel> for
    its blends."""
    import json
    j = json.loads((livery / "build" / "livery.json").read_text())
    want = {**{r: t for r, t in lb.ROLE_TEX.items() if r in j["roles"]},
            **{b: lb.tex_name("brand-" + b, {}) for b in j["blends"]}}
    assert j["latex"]["roles"] == want, f"{livery.name}: latex.roles differ from ROLE_TEX and the blends"
