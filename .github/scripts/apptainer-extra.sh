#!/bin/bash
# The Apptainer forms smoke-test.sh does not cover, against the SIF given as $1 (runtimes.yaml,
# after `RUNTIME=apptainer smoke-test.sh`): the native HPC form (cd and run, no bind, no --pwd),
# `apptainer exec`, --cleanenv and --containall, the read-only image; then a "lived-in" HOME:
# the things a long-used HPC account carries (a host matplotlib cache, Jupyter kernels and
# pip --user packages from the host's Python, module-set TEXINPUTS and PYTHONPATH), one at a
# time, each row OK or what broke, into $GITHUB_STEP_SUMMARY. A row that is not OK fails the
# script when it is `gate` (it worked, or was fixed: the Dockerfile's host isolation); a new
# row starts `report`, which never fails, until it is fixed.
# SCRATCH: a directory outside HOME and /tmp (an HPC scratch or project space); default $tmp.
set -euo pipefail
sif=$1
tmp=${RUNNER_TEMP:-${TMPDIR:-/tmp}}
scratch=${SCRATCH:-$tmp}
summary=${GITHUB_STEP_SUMMARY:-/dev/null}
owned() { for f; do test -s "$f"; test "$(stat -c %u "$f")" = "$(id -u)"; done; }

# three small decks: no code, a matplotlib plot (python3 kernel), a {bash} cell (bash kernel)
decks() {
  cat > "$1/plain.qmd" <<'QMD'
---
title: "Plain"
date: last-modified
---

## A diagram

```{mermaid}
%%| fig-width: 5
flowchart LR
  A[plain.qmd] --> B[plain.pptx]
```
QMD
  cat > "$1/plot.qmd" <<'QMD'
---
title: "Plot"
---

## A plot

```{python}
#| echo: false
import livery_mpl, numpy as np, matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot(np.arange(5), np.arange(5) ** 2, label="squares")
ax.legend()
plt.show()
```
QMD
  cat > "$1/shell.qmd" <<'QMD'
---
title: "Shell"
engine: jupyter
jupyter: bash
---

## A shell cell

```{bash}
echo "built on $(uname -m)"
```
QMD
}

echo "== 1. the native HPC form: cd into the decks and run, no bind, no --pwd ($scratch)"
work=$(mktemp -d "$scratch/native.XXXXXX")
decks "$work"
(cd "$work" && timeout 900 apptainer run "$sif" make pptx)
owned "$work"/plain.pptx "$work"/plot.pptx "$work"/shell.pptx
readlink "$work/_quarto.yml" | grep -c '^/opt/quarto-livery-decks/' >/dev/null

echo "== 2. apptainer exec: no entrypoint, so Make.common and DECKS by hand"
work=$(mktemp -d "$tmp/exec.XXXXXX")
decks "$work"
timeout 900 apptainer exec --bind "$work:/work" --pwd /work "$sif" \
  make -f /opt/quarto-livery-decks/Make.common DECKS="plain plot" pptx
owned "$work"/plain.pptx "$work"/plot.pptx

for opt in --cleanenv --containall; do
  echo "== 3. apptainer run $opt"
  work=$(mktemp -d "$tmp/clean.XXXXXX")
  decks "$work"; rm "$work/shell.qmd"
  timeout 900 apptainer run "$opt" --bind "$work:/work" --pwd /work "$sif" make pptx html 2>&1 | tee "$tmp/clean.log"
  owned "$work"/plain.pptx "$work"/plot.pptx "$work"/plain.html "$work"/plot.html
  # --containall's HOME is an empty tmpfs: the entrypoint seeds matplotlib's cache there too
  if grep -q 'building the font cache' "$tmp/clean.log"; then echo "matplotlib rebuilt its font cache under $opt" >&2; exit 1; fi
done

echo "== 4. the image is read-only (so every check above ran against it as a SIF)"
if apptainer exec "$sif" touch /opt/quarto-livery-decks/x 2>/dev/null; then echo "/opt is writable" >&2; exit 1; fi

echo "== 5. a lived-in HOME (gated rows fail, report rows only report)"
set +e
pyver=$(apptainer exec "$sif" python -c 'import sys; print("%d.%d" % sys.version_info[:2])')
mplver=$(apptainer exec "$sif" python -c 'from matplotlib import font_manager as fm; print(fm.FontManager.__version__)')
# one row per item: a fresh HOME holding just that item, one deck built, the outcome classified
gfail=0
row() {   # row gate|report LABEL DECK TARGET SETUP [VAR=value, @HOME@ the row's HOME]
  local mode=$1 label=$2 deck=$3 target=$4 setup=$5; shift 5
  local home work log rc out vars=() v
  home=$(mktemp -d "$tmp/home.XXXXXX"); work=$(mktemp -d "$tmp/lived.XXXXXX"); log=$work/build.log
  decks "$work"
  (cd "$home" && eval "$setup")
  for v; do vars+=("${v//@HOME@/$home}"); done
  env ${vars[@]+"${vars[@]}"} timeout 900 apptainer run --home "$home" --bind "$work:/work" --pwd /work "$sif" \
    make -f /opt/quarto-livery-decks/Make.common DECKS="$deck" "$target" >"$log" 2>&1
  rc=$?
  if [ "$rc" -ne 0 ] || [ ! -s "$work/$deck.$target" ]; then
    out="breaks (exit $rc): $(grep -m1 -iE 'error|not found|no such|traceback|cannot|failed' "$log" | cut -c1-160)"
  elif grep -q 'findfont: Font family' "$log"; then
    out="falls back: $(grep -m1 'findfont' "$log" | cut -c1-160)"
  elif grep -q 'building the font cache' "$log"; then
    out="OK, but rebuilds matplotlib's font cache (slow)"
  else
    out=OK
  fi
  printf '%-58s %-6s %s\n' "$label" "$mode" "$out"
  printf '| %s | `%s` | %s | %s |\n' "$label" "$deck.$target" "$mode" "${out//|/\\|}" >> "$summary"
  if [ "$out" != OK ]; then
    tail -25 "$log" | sed 's/^/    /'
    if [ "$mode" = gate ]; then gfail=1; echo "::error::lived-in HOME: $label: $out"; fi
  fi
}
kernel() {   # a kernel spec as `jupyter kernelspec install --user` writes it, for the host's Python
  mkdir -p ".local/share/jupyter/kernels/$1"
  printf '{"argv": ["/glade/u/apps/opt/conda/bin/python", "-m", "%s", "-f", "{connection_file}"], "display_name": "%s", "language": "%s"}\n' \
    "$2" "$1" "$3" > ".local/share/jupyter/kernels/$1/kernel.json"
}
shadow() {   # a host-built numpy on a path the container's python reads
  mkdir -p "$1/numpy"
  echo 'raise ImportError("numpy built for the host Python (simulated)")' > "$1/numpy/__init__.py"
}
export -f kernel shadow

{ echo "### A lived-in HPC HOME under Apptainer"; echo
  echo "Each row: a fresh HOME holding one item a long-used account carries, one deck built. Python $pyver, matplotlib font cache v$mplver. A \`gate\` row fails the job; a \`report\` row only reports."; echo
  echo "| HOME or environment holds | builds | mode | outcome |"; echo "|---|---|---|---|"; } >> "$summary"
row gate "nothing (the baseline)"                                    plot  pptx ':'
row gate "a host matplotlib cache, same version, other fonts"        plot  pptx "mkdir -p .cache/matplotlib && apptainer exec '$sif' python -c \"import json,glob; d=json.load(open(glob.glob('/opt/matplotlib/fontlist-*.json')[0])); d['ttflist']=[]; d['afmlist']=[]; json.dump(d, open('.cache/matplotlib/fontlist-v$mplver.json','w'))\""
row gate "a host matplotlib cache of another version"                plot  pptx 'mkdir -p .cache/matplotlib && echo "{}" > .cache/matplotlib/fontlist-v330.json'
row gate "a host python3 kernel (ipykernel install --user)"          plot  pptx 'kernel python3 ipykernel_launcher python'
row gate "a host bash kernel (bash_kernel install --user)"           shell pptx 'kernel bash bash_kernel bash'
row gate "pip install --user packages for python$pyver"              plot  pptx "shadow .local/lib/python$pyver/site-packages"
row gate "PYTHONPATH from a module (host site-packages)"             plot  pptx 'shadow site' PYTHONPATH=@HOME@/site
row gate "TEXINPUTS from a module, no trailing colon"                plain pdf  ':' TEXINPUTS=/glade/u/apps/tex/inputs
echo "lived-in report written; gated rows $( [ "$gfail" = 0 ] && echo OK || echo FAILED)"
exit "$gfail"
