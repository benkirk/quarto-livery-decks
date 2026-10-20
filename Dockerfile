# syntax=docker/dockerfile:1
# The framework with its whole build environment: ghcr.io/benkirk/quarto-livery-decks
# (docs/container.md). A deck directory bind-mounted on /work builds with
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

# 2. Fonts, a rich but bounded set (~200 MB; CJK left out, docs/container.md says how to add it). A
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
# conda-forge's linux-aarch64 quarto bakes its BUILD machine's path into QUARTO_DENO_DOM
# (/home/conda/feedstock_root/.../_build_env/lib/deno_dom.so): find the plugin the deno-dom
# package really installed when the activation's path is not there.
if [ ! -f "$dom" ]; then
  echo "activation's QUARTO_DENO_DOM does not exist ('$dom'); searching $CONDA_PREFIX/lib" >&2
  dom=$(find "$CONDA_PREFIX/lib" -maxdepth 2 \( -name 'deno_dom*.so' -o -name 'libplugin*.so' -o -name '*deno*dom*' \) -type f | head -1)
fi
test -n "$dom" && test -f "$dom" || { echo "deno-dom plugin not found" >&2; ls "$CONDA_PREFIX/lib" | grep -i deno >&2 || true; exit 1; }
echo "deno-dom plugin: $dom"
ln -s "$dom" "$QUARTO_DENO_DOM"
bad=0
while IFS== read -r k v; do
  [ "$k" = QUARTO_DENO_DOM ] && continue
  [ "$(printenv "$k")" = "$v" ] || { echo "ENV $k=$(printenv "$k") but activation says $v" >&2; bad=1; }
done <<<"$want"
test "$bad" -eq 0
quarto --version
rsvg-convert --version   # pptx_steps/svg_fallback.py: an SVG plot's PNG fallback
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
# Playwright >= 1.49 ships Chrome for Testing's shell, `chrome-headless-shell`; older ones `headless_shell`
shell=$(find "$PLAYWRIGHT_BROWSERS_PATH" -type f \( -name chrome-headless-shell -o -name headless_shell \) | head -1)
test -n "$shell" || { echo "no headless shell under $PLAYWRIGHT_BROWSERS_PATH:" >&2; find "$PLAYWRIGHT_BROWSERS_PATH" -maxdepth 3 >&2; exit 1; }
echo "headless shell: $shell"
ln -s "$shell" "$QUARTO_CHROMIUM"
chmod -R a+rX "$PLAYWRIGHT_BROWSERS_PATH"   # the zip carries 600 on a few files (deb.deps); any uid runs this
"$QUARTO_CHROMIUM" --version
# Quarto's wait for that browser. It gives the browser 3 s to answer, then waits for it to exit,
# which a healthy browser never does: the render hangs for good (quarto src/core/cri/cri.ts,
# waitForServer). A first start on a busy login node, through Apptainer's FUSE, took 5 s (a new
# user's first build on Casper hung so). 30 s here. The exact line must be there, or the build
# stops: a new Quarto has changed it, and this needs another look.
q="$(dirname "$(readlink -f "$(command -v quarto)")")/quarto.js"
n=$(grep -c -F 'async function waitForServer(port, timeout = 3e3)' "$q" || true)
test "$n" = 1 || { echo "Quarto's waitForServer is not the one patched here: $(grep -n -o 'async function waitForServer([^)]*)' "$q")" >&2; exit 1; }
sed -i 's/async function waitForServer(port, timeout = 3e3)/async function waitForServer(port, timeout = 3e4)/' "$q"
echo "quarto $(quarto --version): $(grep -o 'async function waitForServer([^)]*)' "$q")"
EOS

# 6. Fonts beyond the system's: /opt/fonts, an empty mount point for the host's own (a
#    brand's licensed faces: `-v "$PWD/fonts:/opt/fonts:ro"`), and the liveries' bundled
#    fonts in the framework copied below, so LibreOffice renders a pptx with its real faces
#    when `make measure` shoots it (a livery mounted from the host is not covered: /opt/fonts).
#    Linked under /usr/local/share/fonts, a directory every fontconfig scans: the SYSTEM one
#    (/etc/fonts), which the apt XeLaTeX, Chromium and LibreOffice use, and the conda env's
#    own (first on PATH as fc-cache/fc-list, with its own fonts.conf), which never read a
#    file dropped into /etc/fonts/conf.d.
RUN mkdir -p /opt/fonts /usr/local/share/fonts && ln -s /opt/fonts /usr/local/share/fonts/host

# 7. The framework itself, last: it changes most often (.dockerignore keeps outputs and the
#    host's conda-env/ out). A mounted tree belongs to whoever mounted it: let git act in it.
#    matplotlib's font cache is built here too, after the liveries' fonts are linked.
COPY . /opt/quarto-livery-decks
COPY --chmod=755 etc/entrypoint.sh /usr/local/bin/entrypoint.sh
# the framework's own commands (bin/livery) on PATH, after the conda env's; DECKS_RUNTIME: this
# is the toolchain, so Make.common never dispatches to a container from inside one (the host's
# make also says so on the inner command line)
ENV FRAMEWORK=/opt/quarto-livery-decks \
    PATH=/opt/quarto-livery-decks/bin:$PATH \
    DECKS_RUNTIME=native
RUN <<'EOS'
set -eo pipefail
git config --system safe.directory '*'
# the liveries' fonts (step 6): the system fontconfig must see them, the conda one should
ln -s /opt/quarto-livery-decks/liveries /usr/local/share/fonts/liveries
/usr/bin/fc-cache -f
fc-cache -f || true
echo "system fontconfig: $(/usr/bin/fc-list : family | sort -u | wc -l) families, Poppins $(/usr/bin/fc-list : family | grep -c Poppins)"
echo "conda fontconfig:  $(fc-list : family | sort -u | wc -l) families, Poppins $(fc-list : family | grep -c Poppins || true)"
test "$(/usr/bin/fc-list : family | grep -c Poppins)" -gt 0 || { /usr/bin/fc-cache -fv 2>&1 | grep -E 'local/share|liveries' >&2; exit 1; }
# Chromium's own font index. The headless shell (step 5) bundles a fontconfig whose index format
# the system's does not write, so without this every new HOME indexes all the fonts above on its
# first diagram: ~5 s on a busy login node, and an index of 88 files in every HOME. Before step 5
# lengthened Quarto's wait, that alone lost the race and hung a new user's first build. Built here,
# as root, into /var/cache/fontconfig, beside the system's; then a fresh HOME must get no index.
fonts_page='data:text/html,<p style="font-family:sans-serif">fonts</p><p style="font-family:serif">fonts</p>'
"$QUARTO_CHROMIUM" --headless --no-sandbox --disable-gpu --screenshot=/tmp/fonts.png "$fonts_page" >/dev/null 2>&1
rm -f /tmp/fonts.png
probe=$(mktemp -d)
HOME=$probe "$QUARTO_CHROMIUM" --headless --no-sandbox --disable-gpu --screenshot="$probe/fonts.png" "$fonts_page" >/dev/null 2>&1
test ! -e "$probe/.cache/fontconfig" || { echo "Chromium still indexes fonts into HOME: $(ls "$probe/.cache/fontconfig" | wc -l) files" >&2; exit 1; }
rm -rf "$probe"
echo "font indexes in /var/cache/fontconfig: $(ls /var/cache/fontconfig | sed -E 's/^[0-9a-f]+-//' | sort | uniq -c | tr '\n' ' ')"
# matplotlib's font cache, built once over every font above (the liveries' too) into /opt/matplotlib:
# the entrypoint seeds it into a user's HOME, so a deck's first plot does not rescan them all
MPLCONFIGDIR=/opt/matplotlib python - <<'PY'
from matplotlib import font_manager as fm
fm._load_fontmanager(try_read_cache=False)
for family in ("Poppins", "TeX Gyre Heros", "Public Sans"):
    path = fm.findfont(family, fallback_to_default=False)
    print(f"matplotlib: {family} -> {path}")
PY
ls /opt/matplotlib/fontlist-*.json
chmod -R a+rX /opt/matplotlib
# everything a plain user needs must be readable
bad=$(find /opt -not -perm -o=r); test -z "$bad" || { echo "$bad"; exit 1; }
EOS

# 8. Host isolation: the bound HOME. Apptainer runs `--cleanenv` (docs/container.md, Make.container),
#    so no host variable reaches the image's tools, but it still binds your HOME, and with it a
#    `pip --user` tree and kernels registered with the host's Python (~/.local/share/jupyter),
#    which the image's Python and Jupyter would otherwise prefer (runtimes.yaml's lived-in HOME
#    rows). Docker and Podman bind no HOME, so these change nothing there.
ENV PYTHONNOUSERSITE=1 \
    JUPYTER_PREFER_ENV_PATH=1

# Provenance, set by CI (--build-arg); empty locally. After everything, so a new SHA
# invalidates no layer above. The entrypoint's --help prints them.
ARG GIT_SHA=""
ARG BUILD_DATE=""
ENV GIT_SHA=${GIT_SHA} BUILD_DATE=${BUILD_DATE}

WORKDIR /work
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]
