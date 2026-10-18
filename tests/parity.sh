#!/usr/bin/env bash
# Parity check for the de-branding refactor (docs/design/engine-and-liveries.md, section 8).
#
#   utils/parity.sh baseline [deck dir...]   build the decks and snapshot them into _baseline/
#   utils/parity.sh check    [deck dir...]   rebuild, snapshot into _check/, diff against _baseline/
#
# Default deck dirs: docs/quickstart docs/sample docs/fixtures, relative to the repository root,
# each built under every livery in PARITY_LIVERIES (default "ncar cu nsi"; ncar's snapshots keep
# the deck's name, the others get a -<livery> suffix and guard the engine against regressions).
# Every deck of a directory (its Makefile's DECKS) gets a snapshot, which
# holds: every XML part of the unzipped pptx (zip timestamps live only in the zip directory;
# docProps/core.xml carries the render time and custom.xml pandoc's dump of the YAML metadata,
# so both are skipped), the pptx member list, `pdftotext -layout` of the PDF and its pages at
# 40 dpi (a differing page fails), the HTML file (Jupyter's random cell ids normalized), three
# greps (media count, divider labels, embedded fonts), and for docs/quickstart the README
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
dirs=("$@"); [ ${#dirs[@]} -gt 0 ] || dirs=(docs/quickstart docs/sample docs/fixtures)
# every deck under every livery: ncar is the parity fixture (snapshots keep their names), the
# others (cu) have no upstream to match and serve as the regression check for engine changes
liveries=(${PARITY_LIVERIES:-ncar cu nsi})

decks_of() {   # <deck dir>: the deck names, Make.common's DECKS
  make -s -C "$ROOT/$1" --eval 'parity-decks: ; @echo $(DECKS)' parity-decks
}

build() {   # <deck dir> <log> <livery>
  make -C "$ROOT/$1" clean all LIVERY="$3" >"$2" 2>&1 || { tail -20 "$2"; return 1; }
}

snapshot() {   # <deck dir> <deck name> <out dir> <livery>, after build
  local dir=$1 name=$2 out=$3 livery=$4
  rm -rf "$out"; mkdir -p "$out/pptx"
  unzip -q -o "$ROOT/$dir/$name.pptx" -d "$out/pptx" -x docProps/core.xml docProps/custom.xml
  unzip -l "$ROOT/$dir/$name.pptx" | awk 'NR>3 {print $NF}' | sort >"$out/pptx-members.txt"
  pdftotext -layout "$ROOT/$dir/$name.pdf" "$out/pdf.txt"
  mkdir -p "$out/pages"; pdftoppm -r 40 -png "$ROOT/$dir/$name.pdf" "$out/pages/p"
  sed -E 's/id="[0-9a-f]{8}" class="cell"/id="CELL" class="cell"/' "$ROOT/$dir/$name.html" | sed -E "${NORMALIZE:-;}" >"$out/deck.html"
  if [ -f "$ROOT/$dir/screenshots.py" ]; then
    make -C "$ROOT/$dir" screenshots LIVERY="$livery" >"$out/screenshots.log" 2>&1 || { tail -20 "$out/screenshots.log"; return 1; }
    cp -R "$ROOT/$dir/screenshots" "$out/screenshots"
    git -C "$ROOT" checkout -q -- "$dir/screenshots"
  fi
  {
    grep -c 'ppt/media/image' "$out/pptx-members.txt" || true
    cat "$out"/pptx/ppt/slides/*.xml | grep -o 'engine-section-label' | wc -l | tr -d ' '
    grep -c 'embeddedFontLst' "$out/pptx/ppt/presentation.xml" || true
  } >"$out/greps.txt"
  # after the greps, which read the engine's own names
  # sed -i with a backup suffix works on both GNU and BSD sed (GNU rejects -i '')
  [ -z "$NORMALIZE" ] || { find "$out/pptx" \( -name '*.xml' -o -name '*.rels' \) -exec sed -i.orig -E "$NORMALIZE" {} + &&
    find "$out/pptx" -name '*.orig' -delete; }
}

bad=0
side=_baseline; [ "$verb" = baseline ] || side=_check
for dir in "${dirs[@]}"; do for livery in "${liveries[@]}"; do
  mkdir -p "$ROOT/$side"
  build "$dir" "$ROOT/$side/build-$(basename "$dir")-$livery.log" "$livery"
  for deck in $(decks_of "$dir"); do
  name=$deck; [ "$livery" = ncar ] || name="$name-$livery"
  if [ "$verb" = baseline ]; then
    snapshot "$dir" "$deck" "$ROOT/_baseline/$name" "$livery" && echo "baseline: $dir/$deck ($livery)"
  else
    [ -d "$ROOT/_baseline/$name" ] || { echo "no baseline for $dir/$deck ($livery): run 'parity.sh baseline' first"; exit 2; }
    snapshot "$dir" "$deck" "$ROOT/_check/$name" "$livery"
    if diff -r -q --exclude=build.log --exclude=screenshots.log --exclude=screenshots --exclude=pages \
         "$ROOT/_baseline/$name" "$ROOT/_check/$name" >"$ROOT/_check/$name.diff"; then
      echo "parity: $dir/$deck ($livery) unchanged"
    else
      echo "PARITY BROKEN: $dir/$deck ($livery)"; sed 's/^/  /' "$ROOT/_check/$name.diff"; bad=1
    fi
    python3 - "$ROOT/_baseline/$name/pages" "$ROOT/_check/$name/pages" <<'PY' || bad=1
import glob, os, sys
from PIL import Image, ImageChops
a_pages, b_pages = (sorted(map(os.path.basename, glob.glob(d + "/*.png"))) for d in sys.argv[1:3])
bad = a_pages != b_pages
if bad: print(f"PARITY BROKEN (PDF pages): {len(a_pages)} pages, now {len(b_pages)}")
for n in sorted(set(a_pages) & set(b_pages)):
    A, B = (Image.open(os.path.join(d, n)).convert("RGB") for d in sys.argv[1:3])
    box = (0, 0) + A.size if A.size != B.size else ImageChops.difference(A, B).getbbox()
    if box: print(f"PARITY BROKEN (PDF pages): {n} differs in {box}"); bad = True
sys.exit(1 if bad else 0)
PY
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
done; done

exit $bad
