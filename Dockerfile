# syntax=docker/dockerfile:1
# The framework with its whole build environment: ghcr.io/benkirk/quarto-livery-decks
# (README "Building in the container"). A deck directory bind-mounted on /work builds with
# `make pptx|html|pdf`; a bare directory of .qmd files needs no Makefile (etc/entrypoint.sh).
#
# Runs as root by default and works as ANY uid (`--user "$(id -u):$(id -g)"`, rootless
# podman, apptainer): everything below is world-readable and nothing lives under /root;
# the entrypoint gives a uid without a writable HOME one under /tmp. GitHub `container:`
# jobs bypass the entrypoint, so PATH and the QUARTO_* activation are Dockerfile ENV, not
# shell profile. Multi-platform (linux/amd64, linux/arm64): .github/workflows/image.yaml.
FROM ubuntu:24.04
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]
ARG DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# 1. The toolchain the recipes call, TeX Live (the list the former ci-liveries workflow proved, the
#    engine's own CI list: quarto's XeLaTeX render AND the Overleaf zip's bare latexmk, which
#    cannot install packages the way TinyTeX does), LibreOffice Impress for `make measure`'s
#    pptx leg. TinyTeX is per-user ($HOME) and needs the network at render time: not here.
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
      ca-certificates curl git rsync unzip zip jq make \
      latexmk texlive-xetex texlive-latex-recommended texlive-latex-extra \
      texlive-fonts-recommended texlive-fonts-extra lmodern fonts-lmodern fonts-texgyre-math \
      poppler-utils libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

# 2. Fonts, a rich but bounded set (~200 MB; CJK left out, README says how to add it). A
#    customer's livery may name an installed face (installed-fonts, PDF fonts=brand), mermaid
#    labels fall back to whatever fontconfig has, LibreOffice renders the pptx for `make
#    measure`. Metric-compatible stand-ins for the Office and PostScript families first.
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
      fonts-liberation fonts-liberation2 fonts-crosextra-carlito fonts-crosextra-caladea \
      fonts-urw-base35 fonts-freefont-otf fonts-texgyre \
      fonts-dejavu fonts-noto-core fonts-noto-mono fonts-noto-color-emoji \
      fonts-roboto fonts-open-sans fonts-lato fonts-inter fonts-ubuntu fonts-cantarell \
      fonts-ibm-plex fonts-ebgaramond fonts-sil-gentium-basic fonts-font-awesome \
      fonts-firacode fonts-hack fonts-jetbrains-mono \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -f && echo "font families: $(fc-list : family | sort -u | wc -l)"

# 3. The conda env, from the same conda-env.yaml the host uses (README "Quick start"), by
#    micromamba (one static binary, no base env to carry).
COPY --from=mambaorg/micromamba:2 /bin/micromamba /usr/local/bin/micromamba
ENV CONDA_PREFIX=/opt/conda-env MAMBA_ROOT_PREFIX=/opt/micromamba
COPY conda-env.yaml /tmp/conda-env.yaml
RUN micromamba create -y -p "$CONDA_PREFIX" -f /tmp/conda-env.yaml \
    && micromamba clean -a -y && rm -rf /tmp/conda-env.yaml "$MAMBA_ROOT_PREFIX"

# 4. Activation, baked. Quarto needs the variables conda-forge's activate.d/quarto.sh
#    exports (CLAUDE.md: PATH alone fails with a missing deno); as ENV they hold for
#    `docker run`, any --user, and GitHub container: steps alike. The values are the
#    feedstock's ($PREFIX-relative), asserted against the real script below so a feedstock
#    change fails this build instead of a render. QUARTO_DENO_DOM is the deno-dom package's
#    plugin, not $PREFIX-relative: it gets a stable name here.
ENV PATH=/opt/conda-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    QUARTO_DENO=/opt/conda-env/bin/deno \
    QUARTO_PANDOC=/opt/conda-env/bin/pandoc \
    QUARTO_ESBUILD=/opt/conda-env/bin/esbuild \
    QUARTO_TYPST=/opt/conda-env/bin/typst \
    QUARTO_DART_SASS=/opt/conda-env/bin/sass \
    QUARTO_SHARE_PATH=/opt/conda-env/share/quarto \
    QUARTO_CONDA_PREFIX=/opt/conda-env \
    QUARTO_DENO_DOM=/opt/conda-env/lib/quarto-deno-dom-plugin.so
RUN <<'EOS'
set -eo pipefail
want=$(env -i CONDA_PREFIX="$CONDA_PREFIX" PATH=/usr/bin:/bin bash -c \
  'for f in "$CONDA_PREFIX"/etc/conda/activate.d/*.sh; do . "$f"; done; env | grep ^QUARTO_')
echo "$want"
dom=$(sed -n 's/^QUARTO_DENO_DOM=//p' <<<"$want")
test -f "$dom" || { echo "deno-dom plugin not found: '$dom'" >&2; exit 1; }
ln -s "$dom" "$QUARTO_DENO_DOM"
bad=0
while IFS== read -r k v; do
  [ "$k" = QUARTO_DENO_DOM ] && continue
  [ "$(printenv "$k")" = "$v" ] || { echo "ENV $k=$(printenv "$k") but activation says $v" >&2; bad=1; }
done <<<"$want"
test "$bad" -eq 0
quarto --version
EOS

# 5. The bash kernel (executable {bash} cells) and ONE headless Chromium, shared by Quarto
#    (mermaid, through QUARTO_CHROMIUM, which it reads first) and Playwright (make qa,
#    measure, screenshots, through CHROME). Playwright's headless shell is what `quarto
#    install chrome-headless-shell` fetches too; the system Chrome wedged quarto's handshake
#    on the CI runners (ci history). --with-deps installs the shell's apt libraries.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
    QUARTO_CHROMIUM=/opt/pw-browsers/headless_shell \
    CHROME=/opt/pw-browsers/headless_shell
RUN <<'EOS'
set -eo pipefail
python -m bash_kernel.install --sys-prefix
apt-get update -qq
python -m playwright install --with-deps --only-shell chromium
rm -rf /var/lib/apt/lists/* /root/.cache
shell=$(find "$PLAYWRIGHT_BROWSERS_PATH" -type f -name headless_shell | head -1)
test -n "$shell" || { echo "no headless_shell under $PLAYWRIGHT_BROWSERS_PATH" >&2; exit 1; }
ln -s "$shell" "$QUARTO_CHROMIUM"
"$QUARTO_CHROMIUM" --version
EOS

# 6. The framework itself, last: it changes most often (.dockerignore keeps outputs and the
#    host's conda-env/ out). A mounted tree belongs to whoever mounted it: let git act in it.
COPY . /opt/quarto-livery-decks
COPY --chmod=755 etc/entrypoint.sh /usr/local/bin/entrypoint.sh
ENV FRAMEWORK=/opt/quarto-livery-decks
RUN git config --system safe.directory '*' \
    && test -z "$(find /opt -not -perm -o=r -print -quit)" || { find /opt -not -perm -o=r; exit 1; }

# Provenance, set by CI (--build-arg); empty locally. After everything, so a new SHA
# invalidates no layer above. The entrypoint's --help prints them.
ARG GIT_SHA=""
ARG BUILD_DATE=""
ENV GIT_SHA=${GIT_SHA} BUILD_DATE=${BUILD_DATE}

WORKDIR /work
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]
