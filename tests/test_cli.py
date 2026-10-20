#!/usr/bin/env python3
"""Check the `livery` command (_extensions/engine/livery.py) on fresh scaffolds.

    tests/test_cli.py

`livery new` without a deck, with one (`--from` a bundled template.pptx: its slots, fonts and slide
size reach the livery), and a flavor (`--extends`) each pass `livery all` (build, template, check)
as they stand; `new` refuses a non-empty directory and a parent that is not beside it; `zip` packs
both bundles; every bundled build/livery.json records the engine's version and its schema, and
`deps` warns when a build records another; `livery_mpl.__version__` is the engine's, in the engine
and in an unpacked charts bundle, and its `dense()` halves the type and restores it, `raster()` is a no-op outside a kernel; and the
first-use fixes (#87): `bin/livery` runs the command (through a link too), `all` does not warn of
the template it builds, `check` is quiet but for warnings, failures and a summary (`-v` for all), a
bad palette name names its key, and a scaffold outside the repo points its editor at the real
schema. The decks under a scaffold are CI's and liveries/README.md's acceptance, not this test's.
"""

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVERY = [sys.executable, str(ROOT / "_extensions" / "engine" / "livery.py")]
fails = []


def check(ok, what):
    if not ok:
        fails.append(what)


def run(*args):
    return subprocess.run([*LIVERY, *map(str, args)], capture_output=True, text=True)


with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    for name, extra in (("plain", []), ("fromdeck", ["--from", ROOT / "liveries" / "nasa" / "template.pptx"])):
        r = run("new", t / name, *extra)
        check(r.returncode == 0, f"new {name}: {r.stderr.strip()}")
        r = run("all", t / name)
        check(r.returncode == 0, f"all {name}: {(r.stdout + r.stderr).strip()[-400:]}")
    lv = json.loads((t / "fromdeck" / "build" / "livery.json").read_text())
    nasa = json.loads((ROOT / "liveries" / "nasa" / "build" / "livery.json").read_text())
    check(lv["type"]["canvas"] == nasa["type"]["canvas"], "--from: the deck's slide size is not the canvas")
    check(lv["pptx"]["scheme"]["dk2"] == nasa["pptx"]["scheme"]["dk2"], "--from: the deck's dk2 is not the livery's")
    check(lv["pptx"]["typeface"] == nasa["pptx"]["typeface"], "--from: the deck's minor font is not the typeface")
    check((t / "fromdeck" / "reference" / "report.md").exists(), "--from wrote no reference/report.md")
    r = run("new", t / "plain-red", "--extends", "plain")
    check(r.returncode == 0, f"new --extends: {r.stderr.strip()}")
    (t / "plain-red" / "livery.yml").write_text((t / "plain-red" / "livery.yml").read_text() + 'roles:\n  accent: "#C8102E"\n')
    r = run("all", t / "plain-red")
    check(r.returncode == 0, f"all plain-red: {(r.stdout + r.stderr).strip()[-400:]}")
    red = json.loads((t / "plain-red" / "build" / "livery.json").read_text())
    check(red["roles"]["accent"] == "#C8102E", "the flavor's own accent did not win")
    check(run("new", t / "plain").returncode != 0, "new on a non-empty directory succeeded")
    check(run("new", t / "orphan", "--extends", "nope").returncode != 0, "new --extends of a missing parent succeeded")
    for args, member in ((["zip", t / "plain", "-o", t / "o.zip"], "talk.tex"),
                         (["zip", "--charts", t / "plain", "-o", t / "c.zip"], "livery_mpl.py")):
        r = run(*args)
        ok = r.returncode == 0 and member in zipfile.ZipFile(args[-1]).namelist()
        check(ok, f"{' '.join(map(str, args[:2]))}: {r.stderr.strip()}")

# the version stamp: every bundled build names this engine and its schema; deps warns on another
version = re.search(r"^version:\s*(\S+)", (ROOT / "_extensions" / "engine" / "_extension.yml").read_text(), re.M)[1]
check(re.fullmatch(r"\d{2}\.([1-9]|1[0-2])\.(0|[1-9]\d*)", version), f"_extension.yml's version {version} is not YY.MM.N")
lua = (ROOT / "_extensions" / "engine" / "engine-revealjs.lua").read_text()
check('VERSION = "' not in lua and "_extension.yml" in lua, "engine-revealjs.lua carries a version of its own instead of reading _extension.yml")
for j in sorted((ROOT / "liveries").glob("*/build/livery.json")):
    lv = json.loads(j.read_text())
    check(lv.get("engine") == version and lv.get("schema") == 1, f"{j.parent.parent.name}: livery.json engine/schema {lv.get('engine')}/{lv.get('schema')}")
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp) / "plain"
    run("new", d); run("build", d)
    check("warning" not in run("deps", d).stderr, "deps warns on a current build")
    j = d / "build" / "livery.json"
    j.write_text(json.dumps({**json.loads(j.read_text()), "engine": "0.0.1"}))
    check("written by engine 0.0.1" in run("deps", d).stderr, "deps does not warn on another engine's build")

# livery_mpl's version: the engine's in the engine, the packing engine's in a bundle
with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    run("zip", "--charts", ROOT / "liveries" / "ncar", "-o", t / "c.zip")
    zipfile.ZipFile(t / "c.zip").extractall(t / "bundle")
    probe = ("import livery_mpl as m, matplotlib.pyplot as plt; print(m.__version__); "
             "assert all(hasattr(m, n) for n in m.__all__); f = plt.rcParams['font.size']\n"
             "with m.dense(0.5): assert plt.rcParams['font.size'] == round(f) / 2, 'dense'\n"
             "assert plt.rcParams['font.size'] == f and m.surface and m.mix('#000000', '#FFFFFF', 0) == '#000000'\n"
             "with m.raster(): pass   # outside a kernel: nothing to switch")
    env = {k: v for k, v in __import__("os").environ.items() if k not in ("LIVERY_DIR", "PYTHONPATH", "MATPLOTLIBRC")}
    for where, kw in (("engine", {"env": {**env, "LIVERY_DIR": str(ROOT / "liveries" / "ncar"),
                                          "PYTHONPATH": str(ROOT / "_extensions" / "engine" / "mpl")}}),
                      ("bundle", {"env": env, "cwd": t / "bundle"})):
        r = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, **kw)
        check(r.returncode == 0 and r.stdout.strip() == version, f"livery_mpl in the {where}: {r.stdout.strip()!r} {r.stderr.strip()[-200:]}")

# the first-use fixes (#87)
BIN = ROOT / "bin" / "livery"
with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    (t / "link").symlink_to(BIN)
    for exe in (BIN, t / "link"):   # the launcher, and a link to it elsewhere
        r = subprocess.run([str(exe), "figsize", str(ROOT / "liveries" / "ncar")], capture_output=True, text=True)
        check(r.returncode == 0 and len(r.stdout.split()) == 2, f"{exe.name}: {r.stderr.strip()[-200:]}")
    d = t / "fresh"
    run("new", d)
    r = run("all", d)
    check(r.returncode == 0 and "template" not in r.stderr, f"all warns of its own template: {r.stderr.strip()[-200:]}")
    r = run("check", d)
    lines = r.stdout.splitlines()
    check(lines and lines[-1].startswith("fresh: ok (") and not any(": ok    " in l for l in lines),
          f"check is not quiet with a summary: {lines[-3:]}")
    r = run("check", "-v", d)
    check(sum(": ok    " in l for l in r.stdout.splitlines()) > 10, "check -v does not print every check")
    schema_line = (d / "livery.yml").read_text().splitlines()[0]
    target = schema_line.split("$schema=", 1)[1]
    check((d / target).resolve() == (ROOT / "_extensions" / "engine" / "livery.schema.json").resolve(),
          f"the editor line does not reach the schema: {schema_line}")
    y = d / "livery.yml"
    y.write_text(y.read_text().replace("  accent: accent4", "  accent: orang"))
    r = run("build", d)
    check(r.returncode != 0 and "livery.yml: roles.accent: 'orang' is neither" in r.stderr,
          f"a bad palette name without its key: {r.stderr.strip()[-200:]}")

if fails:
    print("cli:", *fails, sep="\n  ")
    sys.exit(1)
print("cli: three scaffolds pass livery all, the refusals hold, both zips pack, the builds and livery_mpl are stamped, "
      "the first-use fixes hold")
