#!/usr/bin/env bash
# Parity check for the de-branding refactor (docs/design/engine-and-liveries.md, section 8).
#
#   utils/parity.sh baseline [deck dir...]   build the decks and snapshot them into _baseline/
#   utils/parity.sh check    [deck dir...]   rebuild, snapshot into _check/, diff against _baseline/
#
# Default decks: docs/quickstart docs/sample, relative to the repository root. A snapshot
# holds, per deck: every XML part of the unzipped pptx (zip timestamps live only in the
# zip directory; docProps/core.xml carries the render time and custom.xml pandoc's dump of
# the YAML metadata, so both are skipped), the pptx
# member list, `pdftotext -layout` of the PDF, the HTML file (Jupyter's random cell ids
# normalized), three greps (media count, divider labels, embedded fonts), and for docs/quickstart the README
# screenshots, reshot into the snapshot (the committed PNGs are restored afterwards: they
# were shot on another machine and differ in rasterization and date). Screenshot
# differences are reported as hints, not failures: reveal's transition timing leaves a
# few-pixel sliver between two shoots of the same deck.
#
# NORMALIZE (a sed program) is applied to the XML parts and the HTML of a snapshot, so a
# rename can be checked with its nouns folded; apply it to an existing _baseline/ by hand.
#
# TRAP: `date: last-modified` renders the .qmd's mtime, so baseline and check must run on
# the same checkout on the same day, or the title slide differs for that reason alone.
set -euo pipefail
: "${NORMALIZE:=}"

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
verb=${1:-}; shift || true
case "$verb" in baseline|check) ;; *) sed -n '2,13p' "$0"; exit 2;; esac
decks=("$@"); [ ${#decks[@]} -gt 0 ] || decks=(docs/quickstart docs/sample)

snapshot() {   # <deck dir> <out dir>
  local dir=$1 out=$2 name; name=$(basename "$dir")
  rm -rf "$out"; mkdir -p "$out/pptx"
  make -C "$ROOT/$dir" clean all >"$out/build.log" 2>&1 || { tail -20 "$out/build.log"; return 1; }
  unzip -q -o "$ROOT/$dir/$name.pptx" -d "$out/pptx" -x docProps/core.xml docProps/custom.xml
  unzip -l "$ROOT/$dir/$name.pptx" | awk 'NR>3 {print $NF}' | sort >"$out/pptx-members.txt"
  pdftotext -layout "$ROOT/$dir/$name.pdf" "$out/pdf.txt"
  sed -E 's/id="[0-9a-f]{8}" class="cell"/id="CELL" class="cell"/' "$ROOT/$dir/$name.html" | sed -E "${NORMALIZE:-;}" >"$out/deck.html"
  if [ -f "$ROOT/$dir/screenshots.py" ]; then
    make -C "$ROOT/$dir" screenshots >"$out/screenshots.log" 2>&1 || { tail -20 "$out/screenshots.log"; return 1; }
    cp -R "$ROOT/$dir/screenshots" "$out/screenshots"
    git -C "$ROOT" checkout -q -- "$dir/screenshots"
  fi
  {
    grep -c 'ppt/media/image' "$out/pptx-members.txt" || true
    cat "$out"/pptx/ppt/slides/*.xml | grep -o 'engine-section-label' | wc -l | tr -d ' '
    grep -c 'embeddedFontLst' "$out/pptx/ppt/presentation.xml" || true
  } >"$out/greps.txt"
  # after the greps, which read the engine's own names
  [ -z "$NORMALIZE" ] || find "$out/pptx" \( -name '*.xml' -o -name '*.rels' \) -exec sed -i '' -E "$NORMALIZE" {} +
}

bad=0
for dir in "${decks[@]}"; do
  name=$(basename "$dir")
  if [ "$verb" = baseline ]; then
    snapshot "$dir" "$ROOT/_baseline/$name" && echo "baseline: $dir"
  else
    [ -d "$ROOT/_baseline/$name" ] || { echo "no baseline for $dir: run 'parity.sh baseline' first"; exit 2; }
    snapshot "$dir" "$ROOT/_check/$name"
    if diff -r -q --exclude=build.log --exclude=screenshots.log --exclude=screenshots \
         "$ROOT/_baseline/$name" "$ROOT/_check/$name" >"$ROOT/_check/$name.diff"; then
      echo "parity: $dir unchanged"
    else
      echo "PARITY BROKEN: $dir"; sed 's/^/  /' "$ROOT/_check/$name.diff"; bad=1
    fi
    [ -d "$ROOT/_check/$name/screenshots" ] && python3 - "$ROOT/_baseline/$name/screenshots" "$ROOT/_check/$name/screenshots" <<'PY'
import glob, os, sys
from PIL import Image, ImageChops
for a in sorted(glob.glob(sys.argv[1] + "/*.png")):
    b = os.path.join(sys.argv[2], os.path.basename(a))
    A, B = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    box = None if A.size == B.size and (box := ImageChops.difference(A, B).getbbox()) is None else (box or A.size)
    if box: print(f"hint: screenshot {os.path.basename(a)} differs in {box}")
PY
  fi
done

exit $bad
