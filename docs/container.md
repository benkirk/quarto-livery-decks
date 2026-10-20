# Building in the container

The published image `ghcr.io/benkirk/quarto-livery-decks` is the whole build
environment (the conda env, Quarto, XeLaTeX from TeX Live, LibreOffice, a headless
Chromium, a broad set of fonts) with this framework at `/opt/quarto-livery-decks`, for
linux/amd64 and linux/arm64. Nothing to install but Docker (or Podman, or Apptainer):
bind-mount a directory of decks on `/work` and run make.

```bash
cd my-decks            # roadmap.qmd, status.qmd, images/ ...
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" \
  ghcr.io/benkirk/quarto-livery-decks make pptx             # or html, pdf, all, qa
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" \
  ghcr.io/benkirk/quarto-livery-decks make pptx LIVERY=cu
```

- **A directory of `.qmd` files needs no Makefile**: every `<name>.qmd` not starting
  with `_` builds `<name>.{pptx,html,pdf}` (the entrypoint supplies the framework's
  `Make.common` and `DECKS`). A directory with a Makefile runs plain make, so a repo that
  has the framework as a submodule mounts its tree and points `-w` at the deck
  directory; the deck's `include ../framework/Make.common` then drives the image's
  toolchain with the *mounted* framework's recipes:
  `docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work/docs/presentations/roadmap ghcr.io/benkirk/quarto-livery-decks make pptx`.
- **Make variables pass through**: `LIVERY=cu`, `DECKS="a b"`, and a livery of your own
  inside the mount, `LIVERY_DIR=/work/mylivery` (build it once with `docker run ...
  python3 /opt/quarto-livery-decks/_extensions/engine/livery.py all
  /work/mylivery`). `make qa`, `make measure`, `make overleaf` and `make site` work;
  `make publish` wants your git credentials, so run it on the host.
- **Any user.** The image runs as root unless told otherwise; `--user "$(id -u):$(id -g)"`
  makes the outputs yours, and the entrypoint gives that uid a HOME under `/tmp`.
  Rootless Podman needs no flag (`podman run --rm -v "$PWD:/work:Z" ...`; add
  `--userns=keep-id` if the files come out owned by a subuid).
- **On an HPC system (Apptainer)**, change into the decks and run with `--cleanenv`; Apptainer
  binds the directory, scratch and project spaces included, and the outputs are yours:
  `cd my-decks && apptainer run --cleanenv docker://ghcr.io/benkirk/quarto-livery-decks make pptx`.
  The first run converts the image (a few minutes) and caches it; `apptainer pull qld.sif
  docker://ghcr.io/benkirk/quarto-livery-decks` keeps a SIF to run instead.
  `apptainer exec --cleanenv` skips the entrypoint: pass
  `make -f /opt/quarto-livery-decks/Make.common DECKS=roadmap pptx` yourself. `--cleanenv` keeps
  your profile's variables outside (a module's `PYTHONPATH` or `TEXINPUTS`, a `TMPDIR` the
  container cannot see, a locale it lacks); set one deliberately with `APPTAINERENV_<NAME>`. Your
  real HOME is used (the caches land in `~/.cache`), and the image ignores what it holds for your
  own Python: `pip --user` packages and Jupyter kernels registered with it. To keep the rest of
  your HOME out too (Jupyter and IPython settings, TeX trees, personal fonts), add `--home` and a
  directory of the container's own, as a deck's make does.
- **What the build writes** into the directory: the `_quarto.yml`, `_extensions`
  and `_livery` links, the `.livery` stamp, `.quarto/`, `<deck>_files/` and the
  outputs (gitignore them, as a submodule consumer does). The links point into
  `/opt/quarto-livery-decks`, which the host cannot see; a host build re-points them and
  the container re-points the host's, so the two can alternate in one directory.
- **Fonts.** The image ships metric-compatible stand-ins for the Office and PostScript
  families (Liberation, Carlito and Caladea, URW), TeX Gyre, DejaVu, Noto (core, mono,
  emoji) and the common web families (Roboto, Open Sans, Lato, Inter, IBM Plex, ...):
  `docker run --rm ghcr.io/benkirk/quarto-livery-decks fc-list : family | sort -u`. CJK
  is left out. The liveries' bundled fonts are registered too, so LibreOffice renders a
  pptx with its real faces when `make measure` shoots it. Your own licensed faces (a
  livery's `installed-fonts`, PDF `fonts=brand`) mount read-only on `/opt/fonts`, which
  fontconfig is told about, so XeLaTeX, Chromium and LibreOffice all see them:
  `-v "$PWD/fonts:/opt/fonts:ro"`. matplotlib's font cache is built into the image and
  copied into HOME, so a deck's first plot does not rescan every font; with `/opt/fonts`
  mounted, matplotlib builds its own cache once instead, so that it sees your faces.
- **Tags**: `latest` and `main` (the main branch), `sha-<short>` (every commit), `26.10.0` (a
  release, `YY.MM.N`) and `26.10` (the month's newest release), `pr-N` (a pull request). The mount path may not contain
  spaces, `%` or `#` (LaTeX's `\input@path`).
- **The image itself**: `Dockerfile` at the repo root; `make image` builds it locally and
  `.github/scripts/smoke-test.sh <image>` runs what CI runs on it. `.github/workflows/image.yaml`
  builds it natively on an amd64 and an arm64 runner, smoke-tests each as the runner's
  own unprivileged user, and merges one manifest list. `.github/workflows/runtimes.yaml` runs the same smoke
  test under Apptainer (both architectures, unprivileged) and rootless Podman, plus the
  Apptainer forms above and a "lived-in" HOME, on every pull request and weekly against
  `latest`. Quarto's conda activation is baked
  as `ENV` (asserted against conda-forge's `activate.d` at build time), so the image also
  works as a GitHub Actions `container:`, which is how this repo's own CI (`ci.yaml`)
  builds its decks.

## From your deck's Makefile

A deck whose Makefile includes `Make.common` (this repository's decks, a submodule consumer's,
a deck beside a framework checkout) runs the container itself. With no conda env on your PATH,
`make` builds in the image, so the host needs only make (macOS's own will do) and a runtime:

```bash
cd my-repo/docs/talks/roadmap      # its Makefile: include ../framework/Make.common
make qa                            # quarto is not on PATH: the image, through docker
make pptx DECKS_RUNTIME=apptainer  # or name the runtime
```

- **`DECKS_RUNTIME`**: `auto`, the default, is `native` when `quarto` is on your PATH (the
  activated env) and otherwise the first of `apptainer`, `docker`, `podman` installed; any of
  the four names one. Set it on the command line, in your environment (a shell profile's
  `export DECKS_RUNTIME=docker`), or in the deck Makefile before its `include`.
- **One container run per make.** Your repository (its git toplevel), the framework checkout and
  a `LIVERY_DIR` outside them are mounted at their own paths: the recipes are your checkout's,
  the toolchain the image's, and the links the build makes resolve on both sides, so native and
  container builds alternate in one directory. Variables on the command line pass through
  (`make pptx LIVERY=cu DECKS="a b"`); ones only in your environment do not, under any runtime,
  but for `QUARTO_DECKS`, which new-deck's Makefile reads ("Sharing an installation").
- **The container has its own HOME**, `~/.cache/quarto-livery-decks/home-<release>` on the host
  (`DECKS_HOME`), a few MB. What your own tools keep in your HOME (a conda env's Jupyter and
  IPython settings, matplotlib's font list, TeX trees, personal fonts) never reaches the build,
  and the build's caches never touch yours; they persist there, so later builds are quicker.
  Delete an old release's directory freely.
- **A deck's own targets**: a rule of your own in the deck Makefile (`make ingest`, `make test`)
  must run only where the deck builds. Under a container runtime, Make.container forwards every
  goal into the image and leaves the goal an empty recipe on the host; a recipe of yours replaces
  it ("overriding recipe" warnings), so it runs again on the host after the image's run, with the
  host's tools. Define your rules on the native side only:

  ```make
  include $(QUARTO_DECKS)/Make.common

  ifeq ($(DECKS_RUNTIME_USED),native)   # in the image, or an activated env; never the host's
  ingest:
  	python3 -m mypackage.ingest
  endif
  ```

  Extra prerequisites need no guard (`$(OUT).pptx: data.csv` only adds to Make.common's rules),
  and `pytest` is in the image for a deck's own Python tests.
- **More of the host**: `DECKS_BINDS` lists directories the container also sees at their own
  paths, those that exist (a site's file systems; an installation's `site.mk` sets them, below).
  A symlink in the deck directory, an image linked in from elsewhere, works too: its target is
  mounted when nothing above already covers it. Anything else outside these is not visible.
- **Which image**: `DECKS_IMAGE_TAG` defaults to the release your checkout carries (the
  `version:` in `_extensions/engine/_extension.yml`). Set any published tag (`26.10`, `latest`,
  `pr-95`), or `sha` for the image of your checkout's own commit. `DECKS_IMAGE` replaces the
  repository (a fork, or a local `make image` build), `DECKS_CONTAINER_IMAGE` the whole reference
  (a digest too), and `APPTAINER_SIF` runs a pulled SIF instead of converting `docker://` again.
  The build prints the image it uses.
- **Per runtime**: Docker runs as your uid; Podman rootless, with SELinux labelling off for the
  run rather than relabelling your tree; Apptainer as you, with `--cleanenv`, so your profile's
  variables (a `TMPDIR`, a locale, a module's paths) stay outside. `FONTS_DIR=path` mounts
  your licensed fonts on `/opt/fonts`.
- **`make publish`** builds the site in the container and pushes from the host, with your git
  credentials.
- **Paths** may not contain spaces (make splits on them), `%` or `#`.

## Sharing an installation

One framework checkout and one SIF serve everyone on an HPC system: users build with Apptainer
and need no Quarto, conda env or image pull of their own. On NCAR's Casper and Derecho:

```bash
module load apptainer
export QUARTO_DECKS=/glade/work/benkirk/repos/quarto-livery-decks   # the installation
$QUARTO_DECKS/bin/new-deck ~/my-talk       # a deck started from the quickstart
cd ~/my-talk && make pptx                  # or html, pdf, all, qa
```

- **`bin/new-deck DIR`** starts a deck from the installation's quickstart: `DIR/<name>.qmd` and
  its `images/`, a `.gitignore`, and a Makefile that names the installation as a default,
  `QUARTO_DECKS ?= <its path>`, then includes `$(QUARTO_DECKS)/Make.common`. So the deck needs no
  setting to build, and `make QUARTO_DECKS=<checkout>` (or the variable in your environment) builds
  it on another framework checkout, such as one on your laptop. It refuses a directory that is not
  empty.
- **`bin/new-deck --bare DIR`** adds only the Makefile and `.gitignore`, for decks a repository
  already holds (`DIR/<DIR's name>.qmd`, or `DECKS := a b` above the include for several). It
  refuses an existing Makefile, and adds to an existing `.gitignore` only the lines it lacks.
- **The SIF is found by its name.** When the installation holds
  `sif/quarto-livery-decks_<release>.sif`, the SIF of the release it carries, an Apptainer build
  runs it rather than converting `docker://` again. `APPTAINER_SIF`, `DECKS_IMAGE` or
  `DECKS_CONTAINER_IMAGE` set by a user names another image instead.
- **Maintaining it**: clone the framework where everyone can read it, then pull the SIF, best in
  a batch job, with Apptainer's cache and temporary directory on scratch:

  ```bash
  git clone https://github.com/benkirk/quarto-livery-decks.git && cd quarto-livery-decks
  module load apptainer
  make sif        # sif/quarto-livery-decks_<release>.sif, readable by everyone
  ```

  To update: `git pull`, then `make sif` again. Until the new release's SIF is there, builds
  convert `docker://` as before, never running another release's toolchain. `make clobber`
  leaves `sif/` and `site.mk` alone; delete an old release's SIF when no one needs it.
- **The installation's `site.mk`** (beside `Make.common`, untracked) holds what every user of it
  should get, with `?=`, so a user's own setting wins. Mostly the site's file systems, so that
  decks and the images they link resolve; NCAR's, for Casper and Derecho, where the same file
  systems also appear under `/lustre` and `/gpfs`:

  ```make
  DECKS_BINDS ?= /glade /lustre/desc1 /gpfs/csfs1 /local_scratch
  ```
- **Nothing is written into the installation** by a user's build: the links, `.quarto/` and the
  outputs land in the deck's own directory.
