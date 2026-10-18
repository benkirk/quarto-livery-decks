#!/bin/bash
# The README's use case ("Building in the container"), run on this host as a plain user:
# a bare directory of .qmd files, then this repo's decks/quickstart (real Makefiles, committed
# relative links), both bind-mounted into the image given as $1. Run by image.yaml on each
# native build leg, as the runner's own unprivileged user; also runs locally after
# `make image`: .github/scripts/smoke-test.sh ghcr.io/benkirk/quarto-livery-decks:dev
set -euo pipefail
img=$1
u="$(id -u):$(id -g)"
run() { docker run --rm --user "$u" "$@"; }
build() { timeout 900 docker run --rm --user "$u" "$@"; }   # timeout cannot wrap a shell function
tmp=${RUNNER_TEMP:-${TMPDIR:-/tmp}}

echo "== $img runs natively, as uid $u, with its environment"
test "$(run "$img" uname -m)" = "$(uname -m)"
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
  test "$(stat -c %u "$work/$f")" = "$(id -u)"
done
readlink "$work/_quarto.yml" | grep -c '^/opt/quarto-livery-decks/' >/dev/null
case "$(cat "$work/.livery")" in */liveries/cu) ;; *) echo "stamp: $(cat "$work/.livery")"; exit 1;; esac   # the livery directory
unzip -p "$work/hello.pptx" 'ppt/slides/*.xml' | grep -c 'engine-section-label' >/dev/null
! unzip -p "$work/hello.pptx" 'ppt/slides/*.xml' | grep -c '<a:t>last-modified</a:t>' >/dev/null
unzip -l "$work/hello.pptx" | grep -c 'ppt/media/image' >/dev/null       # the mermaid PNG
grep -q 'livery.css' "$work/hello.html"

echo "== 2. a tree with Makefiles (a submodule consumer's layout): the quickstart deck"
# its Makefile includes ../../Make.common, so the mounted framework's recipes drive the image's
# toolchain; the deck has a {bash} cell (the kernel), mermaid and the committed relative links
build -v "$PWD:/work" -w /work/decks/quickstart "$img" make pptx html pdf
for f in quickstart.pptx quickstart.html quickstart.pdf; do
  test -s "decks/quickstart/$f"
  test "$(stat -c %u "decks/quickstart/$f")" = "$(id -u)"
done
# the host can go on working there: no tracked file (the links) was re-pointed
test -z "$(git status --short decks/quickstart | grep -v '^??')"

echo "== 3. root works too (what GitHub container: jobs are)"
docker run --rm -v "$work:/work" "$img" make clean
test ! -e "$work/hello.pptx"

echo "== size"
docker image inspect --format 'uncompressed: {{.Size}} bytes' "$img"
docker history --no-trunc --format 'table {{.Size}}\t{{.CreatedBy}}' "$img" > "$tmp/history.txt"   # no pipe: pipefail + head
cut -c1-160 "$tmp/history.txt" | grep -v '^0B' | head -40
echo "smoke test passed"
