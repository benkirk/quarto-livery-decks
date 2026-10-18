#!/usr/bin/env bash
# Parity check for the engine refactor (design/engine-and-liveries.md, section 8).
#
#   tests/parity-latex.sh baseline   build every deck and snapshot it into _baseline/latex/
#   tests/parity-latex.sh check      rebuild, snapshot into _check/latex/, diff against the baseline
#
# Decks: latex/'s make default html examples variants. A snapshot holds, per PDF, its
# `pdftotext -layout` and every page rendered at 40 dpi (pdftoppm), and per HTML deck the
# file itself. NORMALIZE (a sed program) is applied to the text snapshots of both sides, so a
# rename can be checked with its nouns folded: NORMALIZE='s/ncar/X/g; s/engine/X/g'.
# Text differences fail; a page whose pixels differ is listed with the changed box.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LATEX=$ROOT/latex
BASE=$ROOT/_baseline/latex CHECK=$ROOT/_check/latex
verb=${1:-}
case "$verb" in baseline|check) ;; *) sed -n '2,11p' "$0"; exit 2;; esac
: "${NORMALIZE:=}"

snapshot() {   # <out dir>
  local out=$1
  rm -rf "$out"; mkdir -p "$out/pages"
  make -C "$LATEX" clean default html examples variants >"$out/build.log" 2>&1 || { tail -30 "$out/build.log"; return 1; }
  for pdf in "$LATEX"/talk.pdf "$LATEX"/examples/*.pdf; do
    local name; name=$(basename "$pdf" .pdf)
    pdftotext -layout "$pdf" - | sed -E "$NORMALIZE" >"$out/$name.txt"
    pdftoppm -r 40 -png "$pdf" "$out/pages/$name"
  done
  for html in "$LATEX"/examples/quarto-demo.html; do
    sed -E "$NORMALIZE" "$html" >"$out/$(basename "$html")"
  done
}

if [ "$verb" = baseline ]; then
  snapshot "$BASE" && echo "baseline: $(ls "$BASE"/*.txt | wc -l | tr -d ' ') PDFs, 1 HTML deck"
  exit 0
fi
[ -d "$BASE" ] || { echo "no baseline: run 'tests/parity-latex.sh baseline' first"; exit 2; }
snapshot "$CHECK"
bad=0
if diff -r -q --exclude=build.log --exclude=pages "$BASE" "$CHECK" >"$CHECK.diff"; then
  echo "parity: text and HTML unchanged"
else
  echo "PARITY BROKEN (text):"; sed 's/^/  /' "$CHECK.diff"; bad=1
fi
python3 - "$BASE/pages" "$CHECK/pages" <<'PY' || bad=1
import glob, os, sys
from PIL import Image, ImageChops
a_dir, b_dir, bad = sys.argv[1], sys.argv[2], 0
pages = sorted(glob.glob(a_dir + "/*.png"))
for a in pages:
    b = os.path.join(b_dir, os.path.basename(a))
    if not os.path.exists(b):
        print(f"PARITY BROKEN (pages): {os.path.basename(a)} missing"); bad = 1; continue
    A, B = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    box = (0, 0) + A.size if A.size != B.size else ImageChops.difference(A, B).getbbox()
    if box:
        print(f"PARITY BROKEN (pages): {os.path.basename(a)} differs in {box}"); bad = 1
extra = set(map(os.path.basename, glob.glob(b_dir + "/*.png"))) - set(map(os.path.basename, pages))
for e in sorted(extra): print(f"PARITY BROKEN (pages): {e} is new"); bad = 1
if not bad: print(f"parity: {len(pages)} PDF pages pixel-identical")
sys.exit(bad)
PY
exit $bad
