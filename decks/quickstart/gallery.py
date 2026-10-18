#!/usr/bin/env python3
"""The README's livery gallery: `make gallery` in decks/quickstart/ writes screenshots/liveries.png.

One row per livery in LIVERIES (built with `make html LIVERY=<name>`, which is safe to switch:
Make drops the stale HTML dependency first), four HTML slides across: the title, a divider, a
content slide, the closing. Reuses screenshots.py's shooter and grid, so it needs what `make
screenshots` does. Leaves the directory built under the first livery (the default)."""

import os
import subprocess
import sys
import tempfile

import screenshots

LIVERIES = ["ncar", "cu", "nsi", "nasa", "nasa-dark"]
COLUMNS = ["01-title", "02-divider", "03-text", "11-closing"]


def main():
    cells = []
    with tempfile.TemporaryDirectory() as tmp:
        for livery in LIVERIES:
            subprocess.run(["make", "html", f"LIVERY={livery}"], check=True, stdout=subprocess.DEVNULL)
            os.mkdir(os.path.join(tmp, livery))
            shots = screenshots.html_shots(os.path.join(tmp, livery))
            cells += [shots[name] for name in COLUMNS]
        screenshots.grid(cells, os.path.join(screenshots.OUT, "liveries.png"), len(COLUMNS), 400)
    if LIVERIES[-1] != LIVERIES[0]:
        subprocess.run(["make", "html", f"LIVERY={LIVERIES[0]}"], check=True, stdout=subprocess.DEVNULL)
    print(f"{screenshots.OUT}/liveries.png: {' | '.join(LIVERIES)}")


if __name__ == "__main__":
    main()
