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

[Unreleased]: https://github.com/benkirk/quarto-livery-decks/compare/v26.10.0...HEAD
[26.10.0]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.0
