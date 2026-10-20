# Changelog

What each release changes for the people who use it, newest first, in the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) shape: **Decks** (what a deck author
sees), **Liveries** (what a livery owner must do), **Plots** (what a plot author sees) and
**LaTeX** (the theme's options and commands). The engineering narrative is
`design/engine-and-liveries.md`, section 10.

**Versions are calendar versions, `YY.MM.N`**: the year and month of the release, the month
unpadded, and `N`, from 0, the month's release count (`26.10.0`, `26.10.1`, ..., `26.11.0`). The
version is the engine's, `version:` in `_extensions/engine/_extension.yml`, and a release is the
tag `v<version>`. Tags are never moved: another release in the month is the next `N`. The
month's newest release is also `YY.MM` where a tool supports a moving name: the container image
(`ghcr.io/benkirk/quarto-livery-decks:26.10`). Compatibility is not in the number: a livery's
contract is its `schema:` (1), and what a release asks of you is in its *Liveries* section here.
A release's entry is written here before its tag is pushed, and becomes its notes on GitHub.

## [Unreleased]

### Decks
- `pytest` is in the image and the conda env, for a deck's own Python tests.
- A deck Makefile's own targets (an ingest step, its tests) are documented to go inside
  `ifeq ($(DECKS_RUNTIME_USED),native)`: under a container runtime a recipe of the deck's replaced
  Make.container's forwarding stub and ran a second time on the host, with the host's tools
  (`docs/container.md` "From your deck's Makefile").
- `bin/new-deck`'s Makefile names the framework as a default, `QUARTO_DECKS ?= <checkout>`, and
  includes `$(QUARTO_DECKS)/Make.common`, so `make QUARTO_DECKS=<checkout>` builds the deck on
  another checkout; an environment `QUARTO_DECKS` reaches the container's make too. It shows the
  native-side guard, commented.
- `bin/new-deck --bare DIR`: only the Makefile and `.gitignore`, beside a repository's own decks.
  It refuses an existing Makefile and adds only the `.gitignore` lines that are missing.
- new-deck's `.gitignore` uses Quarto's own spellings (`/.quarto/`, `**/*.quarto_ipynb`), so Quarto
  no longer appends them on the first render.

### Plots
- `livery_mpl.dense(scale=0.65)`: every text size scaled together inside the block, to the half
  point, for small multiples (a 3 x 4 grid at the slide's sizes crowds out its data).
- `livery_mpl.mix` and `livery_mpl.surface` are public (`__all__`): a color moved toward another
  in OKLab, and the background the plot sits on, the dark one inside `dark()`.
- `shade_family` tints toward the dark surface inside `dark()` on a light livery (it tinted toward
  white there).

## [26.10.2] - 2026-10-19

### Decks
- A first build can no longer hang at its first diagram, however slowly the browser starts: the
  image's Quarto waits 30 s for its headless Chromium instead of 3 s, after which it waited for good.
  26.10.1's font index removed the largest delay but not the race: a new account's first build on a
  busy Casper login node still drew a 5 s start and hung.

## [26.10.1] - 2026-10-19

### Decks
- The README is a short front page for deck authors, the details in companion guides:
  `docs/authoring.md` (a new deck, the front matter and slide kinds, linked images, centering
  and scaling a slide, shell chunks, text sizes, autofit, `make qa`); `latex/README.md` (LaTeX and Overleaf: the Overleaf projects, the starter and the examples,
  writing slides in LaTeX, the theme options, math fonts, colors); `docs/formats.md` (the
  repository's layout, the build pipeline, the fonts, the template's constraints, the beamer and
  revealjs formats); `docs/container.md` (building in the container); `docs/other-repos.md` (the
  framework as a submodule, publishing the HTML decks); `decks/plots/README.md` takes the plots
  summary and `liveries/README.md` the dark liveries.
- A pptx with a table opens in PowerPoint without the "Repair?" prompt: the table rules'
  widths are whole EMUs (`style_tables.py` wrote `w="5715.0"`).
- A deck's `make` builds in the published image when no toolchain is activated, so a host
  needs only make and Docker, Podman or Apptainer. `DECKS_RUNTIME` (`auto`, `native`, `docker`,
  `podman`, `apptainer`) picks where the toolchain comes from; `auto` is native when `quarto` is
  on PATH. The deck's repository and the framework are mounted at their own paths, and
  `DECKS_IMAGE_TAG` picks the image: the release the framework checkout carries by default, `sha`
  for its own commit. docs/container.md "From your deck's Makefile".
- The image carries Chromium's own font index: a new user's first build no longer hangs at its
  first diagram. Chromium bundles a fontconfig whose index the system's does not write, so every new
  HOME indexed all the image's fonts first; on a busy login node that outlasted Quarto's 3 s wait for
  the browser, after which Quarto waits forever (a first build on Casper hung after `Cell 1/1 ...Done`).
- A container build has its own HOME, `~/.cache/quarto-livery-decks/home-<release>` (`DECKS_HOME`),
  under every runtime: what your own tools keep in your HOME (a conda env's Jupyter and IPython
  settings, matplotlib's font list, TeX trees, personal fonts) no longer reaches the build, and its
  caches persist between builds. `DECKS_BINDS` mounts more of the host, those directories that exist;
  an installation sets its site's in an untracked `site.mk` beside `Make.common`. A symlink in the deck
  directory resolves in the container: its target is mounted when nothing else covers it.
- One installation serves everyone on an HPC system (docs/container.md "Sharing an installation"):
  `make sif` pulls the SIF of the release a checkout carries into its `sif/`, an Apptainer build runs
  that SIF when it is there, and `bin/new-deck DIR` starts a deck from the quickstart, its Makefile
  including the installation's `Make.common` by absolute path. A user needs `module load apptainer`
  and nothing else installed.
- Apptainer runs with `--cleanenv`, the image's environment alone, as under Docker and Podman: in
  a deck's make (`DECKS_RUNTIME=apptainer`) and in docs/container.md's `apptainer run` and `exec`
  forms. A Casper profile's `TMPDIR=$SCRATCH/tmp` named a directory the container lacked and
  stopped Quarto (`No such file or directory: tmpdir`). Only command-line variables reach a deck's
  build, under every runtime. The image no longer blanks `PYTHONPATH`, `PYTHONHOME` and
  `TEXINPUTS`, which `--cleanenv` keeps out; it still ignores `pip --user` packages and Jupyter
  kernels in your HOME.

### Liveries
- `livery` is a command on your PATH: `bin/livery`, after `source etc/config_env.sh` and in the
  container (`<framework>/bin/livery` from a consumer repository).
- `livery check` prints warnings, failures and one summary line per livery; `-v` prints every
  check. `livery all` no longer warns about the template it is about to build.
- A color that is neither a palette name nor a hex names its key, as the schema's errors do:
  `livery.yml: roles.accent: 'orang' is neither a palette name nor a hex value`.
- `livery new` writes the editor's schema line by the schema's real path, so a livery outside
  this repository is checked as you type too.

## [26.10.0] - 2026-10-18

The first release: one Markdown file becomes a branded PowerPoint (`.pptx`, the first-class
output), a revealjs HTML deck and a beamer PDF, in any brand. The brand is a **livery**, a
directory of data and assets, and `make pptx LIVERY=<name>` switches it.

It comes from `benkirk/NCAR_beamer_template` (the NSF NCAR beamer theme), generalized into an
engine for any brand in `benkirk/beamer-livery-theme` (its 3.x line, through v3.8.0; now
archived), which merged here with its history (#57) beside the framework that had grown around
it (`benkirk/quarto-docs-framework`). Two releases of the merged repository during its first
sprint, v1.0.0 and v1.1.0, were withdrawn when the versions became calendar ones.

### Decks
- Three formats from one `.qmd`: `--to engine-pptx`, `engine-revealjs` and `engine-beamer`, each
  drawing the livery's title, section, closing, feature and full-figure slides from one set of
  compositions, with text sizes in points on the livery's canvas and a deck's size step
  (`type-body:`, `type-scale:`).
- `make qa` (overflow, slide counts, contact sheets), `make measure` (the composed slides against
  their boxes), `make site` and `make publish` (the HTML decks as a static site), and the
  framework as a submodule of another repository (`docs/other-repos.md`); a multi-platform container image with the whole toolchain.

### Liveries
- Eight: `ncar`, `ucar`, `ucp`, `ncarucar` (the NSF NCAR family), `cu` and its flavor `nsi`
  (University of Colorado), `nasa` and `nasa-dark` (the first dark livery). The README's
  gallery shows the quickstart deck under each.
- A livery is `_brand.yml` (colors, fonts, logos; Quarto's brand.yml) and `livery.yml`
  (everything else), which starts with `schema: 1` and is checked against the schema: an
  unknown key or an out-of-range value fails the build with its path. Every key is described in
  [`liveries/REFERENCE.md`](liveries/REFERENCE.md), generated from the schema.
- The `livery` command (`_extensions/engine/livery.py`): `new` (a scaffold that builds as it
  stands, `--from` a reference deck, `--extends` a parent), `inspect`, `build`, `template`,
  `check [--qa]`, `all` (`make livery LIVERY=<name>`), `zip` (the Overleaf project) and
  `zip --charts` (the charts bundle). [`liveries/README.md`](liveries/README.md) is the guide.
- `build/livery.json` records the engine and the schema it was built with, and a deck build
  warns when a livery was built by another engine version.

### Plots
- Every livery has chart colors per mode, light and dark, generated to pass the dataviz checks
  or taken from a brand's published palette (`charts:`), drawn in every format: matplotlib's
  style, `--engine-data-*` in HTML, `EngineData*` and a pgfplots cycle in LaTeX, and a Custom
  Colors row in PowerPoint.
- `livery_mpl`, the helper for plots in the livery, with a stable API: `__all__` (`use`,
  `colors`, `cycle`, `families`, `status`, `muted`, `figsize()`, `shade_family()`, `dark()`,
  `__version__`) and the `livery`, `livery_r`, `livery_div` and `livery_seq_*` colormaps with
  their `_dark` twins (`decks/plots/README.md`). Outside the decks, each release attaches one
  charts bundle per livery.

### LaTeX
- Every livery is a pure-LaTeX beamer theme too, `\usetheme[livery=liveries/<name>]{Engine}`
  (`liveries/ncar` by default), with `fonts=brand|bundled|helvetica`, `mathfont=`, `title=`,
  `footer=`, `typescale=` and the rest (latex/README.md "Theme options"); each release attaches an
  Overleaf project per livery.

[Unreleased]: https://github.com/benkirk/quarto-livery-decks/compare/v26.10.2...HEAD
[26.10.2]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.2
[26.10.1]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.1
[26.10.0]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.0
