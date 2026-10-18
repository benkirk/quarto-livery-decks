#!/usr/bin/env python3
"""Check a livery directory before decks are built from it (design section 6, step 3).

    livery_check.py <livery dir>... [--qa]

Runs the engine's livery_check.py (build/ fresh, every file the data names, template.pptx
pandoc-compliant and rebuilding byte-identically, contrast warnings, the chart colors' checks), then
with --qa the chart contact sheet into decks/quickstart/_qa/charts-<name>.png and the quickstart
deck's `make qa LIVERY=<name>` for each livery that passed. Exit 1 on any failure."""

import argparse
import subprocess
import sys
from pathlib import Path

UTILS = Path(__file__).resolve().parent
ENGINE_CHECK = UTILS.parents[1] / "_extensions" / "engine" / "livery_check.py"
QUICKSTART = UTILS.parents[1] / "decks" / "quickstart"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("liveries", nargs="+", type=Path)
    ap.add_argument("--qa", action="store_true", help="then run the quickstart deck's make qa under the livery")
    a = ap.parse_args()
    bad = 0
    for d in a.liveries:
        swatch = ["--swatch", str(QUICKSTART / "_qa")] if a.qa else []   # the chart contact sheet, beside the QA
        ok = subprocess.run([sys.executable, str(ENGINE_CHECK), str(d), *swatch]).returncode == 0
        if ok and a.qa:
            ok = subprocess.run(["make", "-C", str(QUICKSTART), "qa", f"LIVERY={d.resolve().name}"]).returncode == 0
            print(f"{d.resolve().name}: {'ok   ' if ok else 'FAIL '} make -C decks/quickstart qa")
        bad |= not ok
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
