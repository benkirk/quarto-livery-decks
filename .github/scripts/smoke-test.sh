#!/bin/bash
# docs/container.md's use case, run on this host as a plain user:
# a bare directory of .qmd files, then this repo's decks/quickstart (real Makefiles, committed
# relative links), both bind-mounted into the image given as $1. Run by image.yaml on each
# native build leg, as the runner's own unprivileged user; also runs locally after
# `make image`: .github/scripts/smoke-test.sh ghcr.io/benkirk/quarto-livery-decks:dev
# RUNTIME=podman (rootless: no --user, `:Z` mounts) or RUNTIME=apptainer ($1 a SIF; `run`, so
# the entrypoint runs) run the same checks the way those users do (runtimes.yaml).
set -euo pipefail
img=$1
RUNTIME=${RUNTIME:-docker}
u="$(id -u):$(id -g)"
# c=(the $RUNTIME command line) from docker-style options: [-v host:ctr]... [-w dir] IMAGE cmd...
argv() {
  local w=
  case $RUNTIME in
    docker) c=(docker run --rm --user "$u") ;;
    podman) c=(podman run --rm) ;;                       # rootless: the container's root is this user
    apptainer) c=(apptainer run) ;;                      # runs as this user, HOME is this user's
    *) echo "RUNTIME=$RUNTIME: docker, podman or apptainer" >&2; exit 2 ;;
  esac
  while :; do
    case $1 in
      -v) case $RUNTIME in docker) c+=(-v "$2") ;; podman) c+=(-v "$2:Z") ;; apptainer) c+=(--bind "$2") ;; esac; shift 2 ;;
      -w) w=$2; shift 2 ;;
      *) break ;;
    esac
  done
  case $RUNTIME in
    apptainer) c+=(--pwd "${w:-/work}") ;;               # Apptainer ignores WORKDIR
    *) [ -z "$w" ] || c+=(-w "$w") ;;
  esac
  c+=("$@")
}
run() { argv "$@"; "${c[@]}"; }
build() { argv "$@"; timeout 900 "${c[@]}"; }   # timeout cannot wrap a shell function
tmp=${RUNNER_TEMP:-${TMPDIR:-/tmp}}

echo "== $img runs natively under $RUNTIME, as uid $u, with its environment"
host=$(uname -m); [ "$host" != arm64 ] || host=aarch64   # macOS names it arm64, Linux aarch64
test "$(run "$img" uname -m)" = "$host"
run "$img" --help
run "$img" quarto --version
run "$img" bash -c 'echo "QUARTO_CHROMIUM=$QUARTO_CHROMIUM"; "$QUARTO_CHROMIUM" --version'
run "$img" bash -c 'echo "font families: $(/usr/bin/fc-list : family | sort -u | wc -l), the liveries'"'"' Poppins: $(/usr/bin/fc-list : family | grep -c Poppins)"'
run "$img" bash -c 'test "$(/usr/bin/fc-list : family | grep -c Poppins)" -gt 0'   # LibreOffice's fontconfig sees them
run "$img" python -c "from matplotlib import font_manager as fm; print('matplotlib Poppins:', fm.findfont('Poppins', fallback_to_default=False))"

echo "== 1. a bare directory: no Makefile; mermaid exercises QUARTO_CHROMIUM, the PDF XeLaTeX, a plot matplotlib"
work=$(mktemp -d "$tmp/hello.XXXXXX")   # no spaces: Quarto's \input@path cannot take them
cat > "$work/hello.qmd" <<'QMD'
---
title: "Hello"
subtitle: "Built in the container"
author: "CI"
date: last-modified
---

# Section

The deck lives in a bind-mounted directory.

## A table

| Format | Built by |
|--------|----------|
| pptx | pandoc and the post-render steps |
| HTML | the engine revealjs theme |
| PDF | the engine beamer theme |

## A diagram

```{mermaid}
%%| fig-width: 6
flowchart LR
  A[hello.qmd] --> B[hello.pptx]
  A --> C[hello.html]
  A --> D[hello.pdf]
```

## A plot

```{python}
#| echo: false
import livery_mpl, matplotlib.pyplot as plt
fig, ax = plt.subplots()
for i in range(3):
    ax.plot([0, 1, 2], [i, i + 1, i + 3], label=f"Series {i + 1}")
ax.set_xlabel("x")
ax.legend()
plt.show()
```
QMD
build -v "$work:/work" "$img" make pptx html pdf LIVERY=cu 2>&1 | tee "$tmp/hello.log"
ls -la "$work"
# the plot: matplotlib found the livery's font in the seeded cache, rebuilt nothing
if grep -q 'building the font cache' "$tmp/hello.log"; then echo "matplotlib rebuilt its font cache" >&2; exit 1; fi
if grep -q 'findfont: Font family' "$tmp/hello.log"; then grep 'findfont' "$tmp/hello.log" >&2; exit 1; fi
ls "$work"/hello_files/figure-revealjs/*.svg
test "$(unzip -l "$work/hello.pptx" | grep -c 'ppt/media/image')" -ge 2   # mermaid and the plot
run -v "$work:/work" "$img" pdffonts /work/hello.pdf | grep -c TeXGyreHeros >/dev/null   # poppler is in the image, not on the host
for f in hello.pptx hello.html hello.pdf; do
  test -s "$work/$f"
  test "$(stat -c %u "$work/$f" 2>/dev/null || stat -f %u "$work/$f")" = "$(id -u)"   # GNU, then BSD stat
done
readlink "$work/_quarto.yml" | grep -c '^/opt/quarto-livery-decks/' >/dev/null
case "$(cat "$work/.livery")" in */liveries/cu) ;; *) echo "stamp: $(cat "$work/.livery")"; exit 1;; esac   # the livery directory
unzip -p "$work/hello.pptx" 'ppt/slides/*.xml' | grep -c 'engine-section-label' >/dev/null
# (a negated command never fails under set -e, so the absence is an explicit if)
if unzip -p "$work/hello.pptx" 'ppt/slides/*.xml' | grep -c '<a:t>last-modified</a:t>' >/dev/null; then
  echo "hello.pptx has a literal last-modified date (#7)" >&2; exit 1
fi
unzip -l "$work/hello.pptx" | grep -c 'ppt/media/image' >/dev/null       # the mermaid PNG
grep -q 'livery.css' "$work/hello.html"

echo "== 2. a tree with Makefiles (a submodule consumer's layout): the quickstart deck"
# its Makefile includes ../../Make.common, so the mounted framework's recipes drive the image's
# toolchain; the deck has a {bash} cell (the kernel), mermaid and the committed relative links
build -v "$PWD:/work" -w /work/decks/quickstart "$img" make pptx html pdf
for f in quickstart.pptx quickstart.html quickstart.pdf; do
  test -s "decks/quickstart/$f"
  test "$(stat -c %u "decks/quickstart/$f" 2>/dev/null || stat -f %u "decks/quickstart/$f")" = "$(id -u)"
done
# the host can go on working there: no tracked file (the links) was re-pointed
test -z "$(git status --short decks/quickstart | grep -v '^??')"

[ "$RUNTIME" = docker ] || { echo "smoke test passed ($RUNTIME)"; exit 0; }

echo "== 3. root works too (what GitHub container: jobs are)"
docker run --rm -v "$work:/work" "$img" make clean
test ! -e "$work/hello.pptx"

echo "== size"
docker image inspect --format 'uncompressed: {{.Size}} bytes' "$img"
docker history --no-trunc --format 'table {{.Size}}\t{{.CreatedBy}}' "$img" > "$tmp/history.txt"   # no pipe: pipefail + head
cut -c1-160 "$tmp/history.txt" | grep -v '^0B' | head -40
echo "smoke test passed"
