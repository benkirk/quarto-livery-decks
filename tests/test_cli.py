"""Check the `livery` command (_extensions/engine/livery.py) on fresh scaffolds.

    python3 -m pytest tests/test_cli.py

`livery new` without a deck, with one (`--from` a bundled template.pptx: its slots, fonts and slide
size reach the livery), and a flavor (`--extends`) each pass `livery all` (build, template, check)
as they stand; `new` refuses a non-empty directory and a parent that is not beside it; `zip` packs
both bundles; every bundled build/livery.json records the engine's version and its schema, and
`deps` warns when a build records another; `livery_mpl.__version__` is the engine's, in the engine
and in an unpacked charts bundle, and its `dense()` halves the type and restores it, `raster()` is
a no-op outside a kernel; and the first-use fixes (#87): `bin/livery` runs the command (through a
link too), `all` does not warn of the template it builds, `check` is quiet but for warnings,
failures and a summary (`-v` for all), a bad palette name names its key, and a scaffold outside
the repo points its editor at the real schema. The decks under a scaffold are CI's and
liveries/README.md's acceptance, not this test's. The scaffolds are built once per module (the
`livery all` runs are the cost); the one test that breaks a livery builds its own.
"""

import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from conftest import ENGINE, ROOT, run

VERSION = re.search(r"^version:\s*(\S+)", (ENGINE / "_extension.yml").read_text(), re.M)[1]


@pytest.fixture(scope="module")
def scaffolds(tmp_path_factory):
    """plain (`new`) and fromdeck (`new --from` nasa's template), through `all`; the dir and all's stderr by name."""
    t = tmp_path_factory.mktemp("scaffolds")
    stderr = {}
    for name, extra in (("plain", []), ("fromdeck", ["--from", ROOT / "liveries" / "nasa" / "template.pptx"])):
        r = run("new", t / name, *extra)
        assert r.returncode == 0, f"new {name}: {r.stderr.strip()}"
        r = run("all", t / name)
        assert r.returncode == 0, f"all {name}: {(r.stdout + r.stderr).strip()[-400:]}"
        stderr[name] = r.stderr
    return t, stderr


def test_from_deck_reaches_livery(scaffolds):
    t, _ = scaffolds
    lv = json.loads((t / "fromdeck" / "build" / "livery.json").read_text())
    nasa = json.loads((ROOT / "liveries" / "nasa" / "build" / "livery.json").read_text())
    assert lv["type"]["canvas"] == nasa["type"]["canvas"], "--from: the deck's slide size is not the canvas"
    assert lv["pptx"]["scheme"]["dk2"] == nasa["pptx"]["scheme"]["dk2"], "--from: the deck's dk2 is not the livery's"
    assert lv["pptx"]["typeface"] == nasa["pptx"]["typeface"], "--from: the deck's minor font is not the typeface"
    assert (t / "fromdeck" / "reference" / "report.md").exists(), "--from wrote no reference/report.md"


def test_flavor_own_accent_wins(scaffolds):
    t, _ = scaffolds
    r = run("new", t / "plain-red", "--extends", "plain")
    assert r.returncode == 0, f"new --extends: {r.stderr.strip()}"
    (t / "plain-red" / "livery.yml").write_text((t / "plain-red" / "livery.yml").read_text() + 'roles:\n  accent: "#C8102E"\n')
    r = run("all", t / "plain-red")
    assert r.returncode == 0, f"all plain-red: {(r.stdout + r.stderr).strip()[-400:]}"
    red = json.loads((t / "plain-red" / "build" / "livery.json").read_text())
    assert red["roles"]["accent"] == "#C8102E", "the flavor's own accent did not win"


def test_inspect_prints_without_o(tmp_path):
    r = run("inspect", ROOT / "liveries" / "nasa" / "template.pptx", cwd=tmp_path)
    assert r.returncode == 0 and "# Reference deck" in r.stdout, "inspect without -o did not print the report"
    assert not list(tmp_path.iterdir()), "inspect without -o wrote a file"


def test_flavor_first_all_passes(tmp_path):
    # a flavor of a parent naming its own pptx.template (nasa-dark, of nasa), with --from: its first
    # `all` passes every check (the build once named the parent's template), and the report is written
    for name in ("nasa", "nasa-dark"):
        (tmp_path / name).symlink_to(ROOT / "liveries" / name)
    r = run("new", tmp_path / "fl", "--extends", "nasa-dark", "--from", ROOT / "liveries" / "nasa" / "template.pptx")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "fl" / "reference" / "report.md").exists(), "new --from --extends wrote no report"
    r = run("all", tmp_path / "fl")
    assert r.returncode == 0 and "FAIL" not in r.stdout, f"a new flavor's first all: {r.stdout.strip()[-400:]}"


def test_new_refuses_nonempty(scaffolds):
    t, _ = scaffolds
    assert run("new", t / "plain").returncode != 0, "new on a non-empty directory succeeded"


def test_extends_missing_parent(tmp_path):
    assert run("new", tmp_path / "orphan", "--extends", "nope").returncode != 0, "new --extends of a missing parent succeeded"


@pytest.mark.parametrize("flags, member", [((), "talk.tex"), ((), "sample.tex"), ((), "diagrams/render.pdf"),
                                           ((), "references.bib"), (("--charts",), "livery_mpl.py")],
                         ids=["overleaf", "cookbook", "cookbook-diagram", "cookbook-bib", "charts"])
def test_zip_packs(scaffolds, tmp_path, flags, member):
    t, _ = scaffolds
    out = tmp_path / "o.zip"
    r = run("zip", *flags, t / "plain", "-o", out)
    assert r.returncode == 0 and member in zipfile.ZipFile(out).namelist(), f"zip {' '.join(flags)}: {r.stderr.strip()}"


# the version stamp: every bundled build names this engine and its schema; deps warns on another
def test_version_is_calver():
    assert re.fullmatch(r"\d{2}\.([1-9]|1[0-2])\.(0|[1-9]\d*)", VERSION), f"_extension.yml's version {VERSION} is not YY.MM.N"


def test_revealjs_reads_extension_yml():
    lua = (ENGINE / "engine-revealjs.lua").read_text()
    assert 'VERSION = "' not in lua and "_extension.yml" in lua, \
        "engine-revealjs.lua carries a version of its own instead of reading _extension.yml"


def test_build_is_stamped(livery: Path):
    lv = json.loads((livery / "build" / "livery.json").read_text())
    assert lv.get("engine") == VERSION and lv.get("schema") == 1, \
        f"{livery.name}: livery.json engine/schema {lv.get('engine')}/{lv.get('schema')}"


def test_deps_warns_on_another_engine(tmp_path):
    d = tmp_path / "plain"
    run("new", d)
    run("build", d)
    assert "warning" not in run("deps", d).stderr, "deps warns on a current build"
    j = d / "build" / "livery.json"
    j.write_text(json.dumps({**json.loads(j.read_text()), "engine": "0.0.1"}))
    assert "written by engine 0.0.1" in run("deps", d).stderr, "deps does not warn on another engine's build"


def test_livery_mpl_version(tmp_path):
    """livery_mpl's version: the engine's in the engine, the packing engine's in a bundle."""
    run("zip", "--charts", ROOT / "liveries" / "ncar", "-o", tmp_path / "c.zip")
    zipfile.ZipFile(tmp_path / "c.zip").extractall(tmp_path / "bundle")
    probe = ("import livery_mpl as m, matplotlib.pyplot as plt; print(m.__version__); "
             "assert all(hasattr(m, n) for n in m.__all__); f = plt.rcParams['font.size']\n"
             "with m.dense(0.5): assert plt.rcParams['font.size'] == round(f) / 2, 'dense'\n"
             "assert plt.rcParams['font.size'] == f and m.surface and m.mix('#000000', '#FFFFFF', 0) == '#000000'\n"
             "with m.raster(): pass   # outside a kernel: nothing to switch")
    env = {k: v for k, v in os.environ.items() if k not in ("LIVERY_DIR", "PYTHONPATH", "MATPLOTLIBRC")}
    for where, kw in (("engine", {"env": {**env, "LIVERY_DIR": str(ROOT / "liveries" / "ncar"),
                                          "PYTHONPATH": str(ENGINE / "mpl")}}),
                      ("bundle", {"env": env, "cwd": tmp_path / "bundle"})):
        r = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, **kw)
        assert r.returncode == 0 and r.stdout.strip() == VERSION, \
            f"livery_mpl in the {where}: {r.stdout.strip()!r} {r.stderr.strip()[-200:]}"


# the first-use fixes (#87)
BIN = ROOT / "bin" / "livery"


def test_bin_launcher_and_link(tmp_path):
    (tmp_path / "link").symlink_to(BIN)
    for exe in (BIN, tmp_path / "link"):   # the launcher, and a link to it elsewhere
        r = subprocess.run([str(exe), "figsize", str(ROOT / "liveries" / "ncar")], capture_output=True, text=True)
        assert r.returncode == 0 and len(r.stdout.split()) == 2, f"{exe.name}: {r.stderr.strip()[-200:]}"


def test_all_does_not_warn_of_its_template(scaffolds):
    _, stderr = scaffolds
    assert "template" not in stderr["plain"], f"all warns of its own template: {stderr['plain'].strip()[-200:]}"


def test_check_is_quiet(scaffolds):
    t, _ = scaffolds
    lines = run("check", t / "plain").stdout.splitlines()
    assert lines and lines[-1].startswith("plain: ok (") and not any(": ok    " in l for l in lines), \
        f"check is not quiet with a summary: {lines[-3:]}"


def test_check_verbose_prints_every_check(scaffolds):
    t, _ = scaffolds
    assert sum(": ok    " in l for l in run("check", "-v", t / "plain").stdout.splitlines()) > 10, \
        "check -v does not print every check"


def test_editor_line_reaches_schema(scaffolds):
    t, _ = scaffolds
    schema_line = (t / "plain" / "livery.yml").read_text().splitlines()[0]
    target = schema_line.split("$schema=", 1)[1]
    assert (t / "plain" / target).resolve() == (ENGINE / "livery.schema.json").resolve(), \
        f"the editor line does not reach the schema: {schema_line}"


def test_bad_palette_names_its_key(tmp_path):
    d = tmp_path / "fresh"
    run("new", d)
    y = d / "livery.yml"
    y.write_text(y.read_text().replace("  accent: accent4", "  accent: orang"))
    r = run("build", d)
    assert r.returncode != 0 and "livery.yml: roles.accent: 'orang' is neither" in r.stderr, \
        f"a bad palette name without its key: {r.stderr.strip()[-200:]}"


def test_mono_code_typeface(tmp_path):
    """livery mono: pptx.code-typeface when a livery names one, else the bundled code face (nasa's DM
    Mono), else nothing (ncar bundles none)."""
    import shutil
    t = tmp_path / "liveries"
    for name in ("nasa",):
        shutil.copytree(ROOT / "liveries" / name, t / name, ignore=shutil.ignore_patterns("reference"))
    d = t / "courier"; d.mkdir()
    (d / "_brand.yml").write_text("{}\n")
    (d / "livery.yml").write_text("schema: 1\nname: courier\nextends: nasa\npptx:\n  code-typeface: Courier New\n")
    assert run("build", d).returncode == 0
    assert run("mono", d).stdout.strip() == "Courier New", "code-typeface not taken"
    assert run("mono", t / "nasa").stdout.strip() == "DM Mono", "the bundled code face"
    assert run("mono", ROOT / "liveries" / "ncar").stdout.strip() == "", "a livery without a code face"


def test_no_private_imports():
    """A step or tool imports no other module's `_private` name: what two modules need is public in
    pptx_steps/common.py, measure.py or livery.py (the #126 sweep found grid.py and columns.py on
    slide_layout's)."""
    hits = []
    for f in sorted((ENGINE).rglob("*.py")):
        for n, line in enumerate(f.read_text().splitlines(), 1):
            if re.match(r"\s*from \S+ import .*\b_[a-z]", line):
                hits.append(f"{f.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not hits, "\n".join(hits)


def test_slide_kinds_agree():
    """The slide kinds a composition draws (feature, closing, full) are named once in Lua
    (engine-common.lua SLIDE_KINDS) and must appear in the two lists that cannot read it: the HTML
    autofit's NEVER selector (engine-revealjs.js) and livery_build's content-art selector."""
    lua = (ENGINE / "engine-common.lua").read_text()
    kinds = set(re.findall(r"(\w+) = true", re.search(r"SLIDE_KINDS = \{([^}]*)\}", lua).group(1)))
    assert kinds == {"feature", "closing", "full"}, kinds
    js = (ENGINE / "engine-revealjs.js").read_text()
    never = set(re.findall(r"\.([\w-]+)", re.search(r'NEVER = "([^"]*)"', js).group(1)))
    assert kinds <= never, f"engine-revealjs.js NEVER lacks {kinds - never}"
    py = (ENGINE / "livery_build.py").read_text()
    sel = set(re.findall(r":not\(\.([\w-]+)\)", re.search(r'sel = "([^"]*level2[^"]*)"', py).group(1)))
    assert kinds <= sel, f"livery_build's content-art selector lacks {kinds - sel}"


def test_theme_literal_counts_only_fall():
    """The themes' hand literals the sweeps count (design/unplanned-city-ledger.md): a scss line-height
    not read from --engine-leading-<role>, a white by hand (#fff, white) and a letter-spacing in the
    scss, a `white` in the beamer themes. Each count may only go down: a new element reads the
    livery's number (type.roles.*.leading, a role, roles.on-dark for text on a dark field) instead
    of restating one. The four scss whites left are Quarto's compile-time Sass defaults ($body-bg,
    $dark-bg-text-color, the two mermaid colors), overridden at runtime by the roles."""
    scss = re.sub(r"//[^\n]*", "", (ENGINE / "engine-revealjs.scss").read_text())   # comments out
    sty = re.sub(r"(?<!\\)%[^\n]*", "", "".join(f.read_text() for f in sorted(ENGINE.glob("beamer*themeEngine.sty"))))
    counts = {
        "scss line-height literals": len(re.findall(r"line-height:\s*[0-9.]+\s*;", scss)),
        "scss #fff/white": len(re.findall(r"#fff\b|\bwhite\b", scss)) - len(re.findall(r"white-space", scss)),
        "scss letter-spacing literals": len(re.findall(r"letter-spacing:\s*[0-9.]+em", scss)),
        "beamer white": len(re.findall(r"\bwhite\b", sty)),
    }
    ceiling = {"scss line-height literals": 3, "scss #fff/white": 4, "scss letter-spacing literals": 0, "beamer white": 0}
    over = {k: (v, ceiling[k]) for k, v in counts.items() if v > ceiling[k]}
    assert not over, f"a theme literal pile grew (now, ceiling): {over}"


def test_svg_dpi_is_the_quarto_fig_dpi():
    """svg_fallback.DPI (the PNG twin of an SVG plot) equals common/_quarto.yml's fig-dpi for the
    pptx format, which it hand-copies."""
    yml = (ROOT / "common" / "_quarto.yml").read_text()
    dpi = int(re.search(r"fig-dpi:\s*(\d+)", yml).group(1))
    src = (ENGINE / "pptx_steps" / "svg_fallback.py").read_text()
    assert int(re.search(r"^DPI\s*=\s*(\d+)", src, re.M).group(1)) == dpi
