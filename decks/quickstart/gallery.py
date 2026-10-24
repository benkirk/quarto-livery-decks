#!/usr/bin/env python3
"""The README's livery gallery: `make gallery` in decks/quickstart/ writes screenshots/liveries.png.

One row per livery in LIVERIES (built with `make html LIVERY=<name>`, which is safe to switch:
Make drops the stale HTML dependency first), four HTML slides across: the title, a divider, a
content slide, the closing. A livery with default markings or a cover notice (nasa-ccp's CUI
banner, legend and rights notice) is shot under `livery placeholders`' sample text (DECK_META), so
no image of ours reads as a real restricted deck. Reuses screenshots.py's shooter and grid, so it
needs what `make screenshots` does. Leaves the directory built under the first livery (the default)."""

import os
import subprocess
import sys
import tempfile

import screenshots

LIVERIES = ["ncar", "cu", "nsi", "nasa", "nasa-dark", "nasa-jsc-eg", "nasa-ccp"]
LIVERY_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_extensions", "engine", "livery.py")
COLUMNS = ["01-title", "02-divider", "03-text", "11-closing"]


def main():
    cells = []
    with tempfile.TemporaryDirectory() as tmp:
        for livery in LIVERIES:
            meta = subprocess.run([sys.executable, LIVERY_PY, "placeholders", os.path.join("..", "..", "liveries", livery)],
                                  check=True, capture_output=True, text=True).stdout
            args = ["make", "html", f"LIVERY={livery}"]
            if meta:   # its sample markings: a prerequisite, so the deck rebuilds under them
                path = os.path.join(tmp, f"{livery}-placeholders.yml")
                with open(path, "w") as f:
                    f.write(meta)
                args.append(f"DECK_META={path}")
            subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
            os.mkdir(os.path.join(tmp, livery))
            shots = screenshots.html_shots(os.path.join(tmp, livery))
            cells += [shots[name] for name in COLUMNS]
        screenshots.grid(cells, os.path.join(screenshots.OUT, "liveries.png"), len(COLUMNS), 400)
    if LIVERIES[-1] != LIVERIES[0]:
        subprocess.run(["make", "html", f"LIVERY={LIVERIES[0]}"], check=True, stdout=subprocess.DEVNULL)
    print(f"{screenshots.OUT}/liveries.png: {' | '.join(LIVERIES)}")


if __name__ == "__main__":
    main()
