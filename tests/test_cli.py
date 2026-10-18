#!/usr/bin/env python3
"""Check the `livery` command (_extensions/engine/livery.py) on fresh scaffolds.

    tests/test_cli.py

`livery new` without a deck, with one (`--from` a bundled template.pptx: its slots, fonts and
slide size reach the livery), and a flavor (`--extends`) each pass `livery all` (build, template,
check) as they stand; `new` refuses a non-empty directory and a parent that is not beside it;
`zip` packs both bundles. The decks under a scaffold are CI's and liveries/README.md's
acceptance, not this test's.
"""

import json
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

if fails:
    print("cli:", *fails, sep="\n  ")
    sys.exit(1)
print("cli: three scaffolds pass livery all, the refusals hold, both zips pack")
