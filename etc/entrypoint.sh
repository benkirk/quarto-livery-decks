#!/bin/bash
# The image's entrypoint (Dockerfile). Two jobs, neither needed by GitHub `container:` jobs,
# which bypass the entrypoint and run as root: PATH and the QUARTO_* activation are
# Dockerfile ENV, not set here.
set -euo pipefail
FW=${FRAMEWORK:-/opt/quarto-livery-decks}

# 1. A writable HOME for any --user. Under `--user uid:gid` HOME is unset, /, or a host
#    path that is not mounted, and everything that writes a per-user cache derives from it:
#    deno (~/.cache/deno; quarto sets no DENO_DIR), jupyter's runtime dir, fontconfig's
#    cache, TeX's TEXMFVAR. Playwright finds its browser through PLAYWRIGHT_BROWSERS_PATH
#    and LibreOffice gets its profile from comp_measure.py, so nothing else moves.
if [ -z "${HOME:-}" ] || [ ! -d "$HOME" ] || [ ! -w "$HOME" ]; then
  export HOME="/tmp/home-$(id -u)"
  mkdir -p "$HOME"
fi
# a uid without a passwd entry: getpass.getuser() (jupyter_client) wants one of these
export USER="${USER:-$(id -un 2>/dev/null || echo user)}"
export LOGNAME="${LOGNAME:-$USER}"

usage() {
  cat <<USAGE
quarto-livery-decks: build Quarto decks (pptx, html, pdf) with the framework at $FW
${GIT_SHA:+  framework commit $GIT_SHA}${BUILD_DATE:+, built $BUILD_DATE}

  docker run --rm --user "\$(id -u):\$(id -g)" -v "\$PWD:/work" IMAGE make pptx

A directory of .qmd files needs no Makefile: every <name>.qmd not starting with _ builds
<name>.{pptx,html,pdf}. A directory with a Makefile runs plain make. Make variables pass
through: make pptx LIVERY=cu, LIVERY_DIR=/work/mylivery, DECKS="a b"; also make qa, measure,
overleaf, site. Your own fonts: -v "\$PWD/fonts:/opt/fonts:ro". README "Building in the container".
USAGE
}

case "${1:-}" in ""|-h|--help|help) usage; exit 0 ;; esac

# 2. `make` in a bare deck directory: supply the framework's Make.common and DECKS. It
#    reads its own location from MAKEFILE_LIST, so -f is all it needs (Make.common).
if [ "$1" = make ] && [ ! -e Makefile ] && [ ! -e makefile ] && [ ! -e GNUmakefile ]; then
  explicit=0
  for a in "$@"; do
    case "$a" in -f|--file|--file=*|--makefile|--makefile=*|-C|--directory|--directory=*) explicit=1 ;; esac
  done
  if [ "$explicit" -eq 0 ]; then
    decks=
    for f in *.qmd; do
      [ -e "$f" ] || continue
      case "$f" in _*) ;; *) decks="$decks ${f%.qmd}" ;; esac
    done
    if [ -z "$decks" ]; then
      echo "no Makefile and no *.qmd in $PWD: is the deck directory mounted on /work?" >&2
      usage >&2
      exit 2
    fi
    shift
    set -- make -f "$FW/Make.common" DECKS="${decks# }" "$@"
  fi
fi
exec "$@"
