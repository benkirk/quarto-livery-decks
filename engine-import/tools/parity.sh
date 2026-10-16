#!/usr/bin/env bash
# Parity check for the engine refactor (docs/design/engine-and-liveries.md, section 8).
#
#   tools/parity.sh baseline   build every deck and snapshot it into _baseline/
#   tools/parity.sh check      rebuild, snapshot into _check/, diff against _baseline/
#
# Decks: make default quarto html examples variants. A snapshot holds, per PDF, its
# `pdftotext -layout` and every page rendered at 40 dpi (pdftoppm), and per HTML deck the
# file itself. NORMALIZE (a sed program) is applied to the text snapshots of both sides, so a
# rename can be checked with its nouns folded: NORMALIZE='s/ncar/X/g; s/engine/X/g'.
# Text differences fail; a page whose pixels differ is listed with the changed box.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
verb=${1:-}
case "$verb" in baseline|check) ;; *) sed -n '2,11p' "$0"; exit 2;; esac
: "${NORMALIZE:=}"

snapshot() {   # <out dir>
  local out=$1
  rm -rf "$out"; mkdir -p "$out/pages"
  make -C "$ROOT" clean default quarto html examples variants >"$out/build.log" 2>&1 || { tail -30 "$out/build.log"; return 1; }
  for pdf in "$ROOT"/talk.pdf "$ROOT"/talk-quarto.pdf "$ROOT"/examples/*.pdf; do
    local name; name=$(basename "$pdf" .pdf)
    pdftotext -layout "$pdf" - | sed -E "$NORMALIZE" >"$out/$name.txt"
    pdftoppm -r 40 -png "$pdf" "$out/pages/$name"
  done
  for html in "$ROOT"/talk-quarto.html "$ROOT"/examples/quarto-demo.html; do
    sed -E "$NORMALIZE" "$html" >"$out/$(basename "$html")"
  done
}

if [ "$verb" = baseline ]; then
  snapshot "$ROOT/_baseline" && echo "baseline: $(ls "$ROOT"/_baseline/*.txt | wc -l | tr -d ' ') PDFs, 2 HTML decks"
  exit 0
fi
[ -d "$ROOT/_baseline" ] || { echo "no baseline: run 'tools/parity.sh baseline' first"; exit 2; }
snapshot "$ROOT/_check"
bad=0
if diff -r -q --exclude=build.log --exclude=pages "$ROOT/_baseline" "$ROOT/_check" >"$ROOT/_check.diff"; then
  echo "parity: text and HTML unchanged"
else
  echo "PARITY BROKEN (text):"; sed 's/^/  /' "$ROOT/_check.diff"; bad=1
fi
python3 - "$ROOT/_baseline/pages" "$ROOT/_check/pages" <<'PY' || bad=1
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
