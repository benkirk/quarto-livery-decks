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
- **On an HPC system (Apptainer)**, change into the decks and run; Apptainer binds the
  directory, scratch and project spaces included, and the outputs are yours:
  `cd my-decks && apptainer run docker://ghcr.io/benkirk/quarto-livery-decks make pptx`.
  The first run converts the image (a few minutes) and caches it; `apptainer pull qld.sif
  docker://ghcr.io/benkirk/quarto-livery-decks` keeps a SIF to run instead.
  `apptainer exec` skips the entrypoint: pass
  `make -f /opt/quarto-livery-decks/Make.common DECKS=roadmap pptx` yourself. Your real HOME
  is used (the caches land in `~/.cache`), and your environment passes in, except what would
  break the build: the image ignores a module's `PYTHONPATH` and `TEXINPUTS`, `pip --user`
  packages, and Jupyter kernels registered with your own Python (set one deliberately with
  `APPTAINERENV_<NAME>`). If a build still behaves differently than in Docker, try
  `apptainer run --cleanenv` first.
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
  (`make pptx LIVERY=cu DECKS="a b"`); ones only in your environment reach Apptainer alone.
- **Which image**: `DECKS_IMAGE_TAG` defaults to the release your checkout carries (the
  `version:` in `_extensions/engine/_extension.yml`). Set any published tag (`26.10`, `latest`,
  `pr-95`), or `sha` for the image of your checkout's own commit. `DECKS_IMAGE` replaces the
  repository (a fork, or a local `make image` build), `DECKS_CONTAINER_IMAGE` the whole reference
  (a digest too), and `APPTAINER_SIF` runs a pulled SIF instead of converting `docker://` again.
  The build prints the image it uses.
- **Per runtime**: Docker runs as your uid; Podman rootless, with SELinux labelling off for the
  run rather than relabelling your tree; Apptainer as you, with your HOME, your environment and
  your `TMPDIR` (bound in), in the image's locale. `FONTS_DIR=path` mounts
  your licensed fonts on `/opt/fonts`.
- **`make publish`** builds the site in the container and pushes from the host, with your git
  credentials.
- **Paths** may not contain spaces (make splits on them), `%` or `#`.
