#!/bin/bash
# The README's use case ("Building in the container"), run on this host as a plain user:
# a bare directory of .qmd files, then this repo's docs/ tree (real Makefiles, committed
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
run "$img" bash -c 'echo "font families: $(fc-list : family | sort -u | wc -l)"'

echo "== 1. a bare directory: no Makefile; mermaid exercises QUARTO_CHROMIUM, the PDF XeLaTeX"
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
QMD
build -v "$work:/work" "$img" make pptx html pdf LIVERY=cu
ls -la "$work"
for f in hello.pptx hello.html hello.pdf; do
  test -s "$work/$f"
  test "$(stat -c %u "$work/$f")" = "$(id -u)"
done
readlink "$work/_quarto.yml" | grep -q '^/opt/quarto-livery-decks/'
test "$(cat "$work/.livery")" = cu
unzip -p "$work/hello.pptx" 'ppt/slides/*.xml' | grep -q 'engine-section-label'
! unzip -p "$work/hello.pptx" 'ppt/slides/*.xml' | grep -q '<a:t>last-modified</a:t>'
unzip -l "$work/hello.pptx" | grep -q 'ppt/media/image'       # the mermaid PNG
grep -q 'livery.css' "$work/hello.html"

echo "== 2. a tree with Makefiles (a submodule consumer's layout): the quickstart deck"
# its Makefile includes ../Make.common, so the mounted framework's recipes drive the image's
# toolchain; the deck has a {bash} cell (the kernel), mermaid and the committed relative links
build -v "$PWD/docs:/work" -w /work/quickstart "$img" make pptx html pdf
for f in quickstart.pptx quickstart.html quickstart.pdf; do
  test -s "docs/quickstart/$f"
  test "$(stat -c %u "docs/quickstart/$f")" = "$(id -u)"
done
# the host can go on working there: no tracked file (the links) was re-pointed
test -z "$(git -C docs status --short quickstart | grep -v '^??')"

echo "== 3. root works too (what GitHub container: jobs are)"
docker run --rm -v "$work:/work" "$img" make clean
test ! -e "$work/hello.pptx"

echo "== size"
docker image inspect --format 'uncompressed: {{.Size}} bytes' "$img"
docker history --no-trunc --format 'table {{.Size}}\t{{.CreatedBy}}' "$img" > "$tmp/history.txt"   # no pipe: pipefail + head
cut -c1-160 "$tmp/history.txt" | grep -v '^0B' | head -40
echo "smoke test passed"
