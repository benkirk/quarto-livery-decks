# Changelog

What each release changes for the people who use it, newest first, in the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) shape: **Decks** (what a deck author
sees), **Liveries** (what a livery owner must do), **Plots** (what a plot author sees) and
**LaTeX** (the theme's options and commands). The engineering narrative is
`design/engine-and-liveries.md`, section 10.

The version is the engine's, `version:` in `_extensions/engine/_extension.yml`; a release is the
tag `v<version>`, and tags are never moved: a fix is a new patch release. A release's entry is
written here before its tag is pushed, and becomes its notes on GitHub.

## [Unreleased]

The customer surface (#58): a schema for `livery.yml`, one `livery` command, immutable releases
and this changelog. Breaking: every livery needs `schema: 1` and the renamed keys below, and every
script below is now a `livery` subcommand.

### Liveries
- **`livery.yml` has a schema** (`_extensions/engine/livery.schema.json`), and the build checks
  every livery against it: an unknown or misspelt key, a wrong type or an out-of-range value fails
  with its path, e.g. `livery.yml: geometry.logo.corne: unknown key`. Every key is described in
  [`liveries/REFERENCE.md`](liveries/REFERENCE.md), generated from the schema.
- **`schema: 1` is required**, first in the file, under the editor line
  `# yaml-language-server: $schema=../../_extensions/engine/livery.schema.json`.
- **Renamed keys**: `divider:` is `section:`; `geometry.divider` is `geometry.section`;
  `geometry.tab` is `geometry.tab-width`; `geometry.logo.title`, `.section`, `.closing` are
  `.title-height`, `.section-height`, `.closing-height`; `geometry.full.floor` is
  `geometry.full.footline`; `derived:` is `blends:`; `charts.sequential` is `charts.default-map`.
  `build/livery.json` follows (`blends`, `section`, `geometry.tab-width`, ...,
  `charts.<mode>.default-map`), and `livery.derived()` is `livery.blend()`.
- **Removed keys**: `aspect:` (the slide's shape comes from `pptx.size`) and `overrides:`, which
  nothing read (the `overrides/` directory is unchanged). The `title.logo`/`title.signoff`
  alias is gone: write `marks: {<title.field>: {logo, signoff}}`.
- **The `livery` command** (`_extensions/engine/livery.py`) replaces the scripts:
  `livery_inspect.py` is `livery inspect`, `livery_build.py` `livery build`, `livery_template.py`
  `livery template`, both `livery_check.py`s `livery check [--qa]`, `overleaf_zip.py` `livery zip`
  and `mpl_zip.py` `livery zip --charts`. New: `livery new <dir> [--from <deck.pptx>]
  [--extends <name>]` scaffolds a livery that builds as it stands, `livery all` is build,
  template and check, and `make livery LIVERY=<name>` (or `LIVERY_DIR=`) runs it.
  [`liveries/README.md`](liveries/README.md) is the guide.
- **`build/livery.json` records `engine` and `schema`**, and a deck build warns when a livery was
  built by another engine version: rebuild it with `livery build <dir>`.
- **ncar's 2020-brand color names are gone** (`overrides/livery-extra.sty`: `CoolGray11`,
  `DeepBlue`, `HilightGreen`, ...); use the 2026 palette names.

### Decks
- `make clean` no longer removes the `_engine` link of decks from before 1.1.0.
- A deck's own Sass sees the ncar defaults as `$engine-<role>` (`$engine-primary`,
  `$engine-foreground`, ...), not `$ncar-*`.
- A Quarto deck picks a bundled livery with the `livery:` key (`livery: liveries/ucar`), not
  `themeoptions: [brand=ucar]`.

### Plots
- `livery_mpl` has a stated, stable API: `__all__` (`use`, `colors`, `cycle`, `families`,
  `status`, `muted`, `figsize()`, `shade_family()`, `dark()`) and the `livery`, `livery_r`,
  `livery_div` and `livery_seq_*` colormaps with their `_dark` twins, listed in
  `decks/plots/README.md`; a change to them is an entry here.
- `livery_mpl.__version__` is the engine's version (a charts bundle's: the engine that packed it).
  A bundle's `livery.json` carries the `engine` and `schema` stamp, and its README names the
  version and its release.
- A livery's default color map is `charts.default-map` (was `charts.sequential`), and
  `livery.json` `charts.<mode>.default-map` (was `sequential-default`).

### LaTeX
- **`brand=` is gone**: `livery=` is the one option, a bundled livery being
  `\usetheme[livery=liveries/ucar]{Engine}`; with none, `liveries/ncar`.
- `fonts=` takes `brand`, `bundled` or `helvetica`, and anything else is an error: the
  `fonts=poppins` spelling and the `brandedfonts` option are gone.
- The 2020-brand theme's compatibility is gone: `NCARprettyframe`, `NCARtitleframe`,
  `\titlebackground`, `\nobackground`, `\defaultbackground`, the `ncar` listings style (the style
  is `engine`, and the default) and the 2020 color names.

## [1.1.0] - 2026-10-18

Charts and plots in every format, and the pptx pipeline moved into the engine (#57 Phase B).

### Plots
- Every livery has chart colors per mode, light and dark (`livery.json` `charts`: categorical,
  families, sequential, diverging, status, muted), generated to pass the dataviz checks or taken
  from a brand's published palette.
- Plots in a deck draw in them: `build/livery.mplstyle` (matplotlib's style, sizes from the type
  roles), the `livery_mpl` helper (`colors`, `cycle`, `families`, `status`, `muted`, `figsize()`,
  `shade_family()`, `dark()`, the `livery`, `livery_r`, `livery_div` and `livery_seq_*` colormaps
  with `_dark` twins), figures at the canvas scale in every format, and the plots deck.
- `make charts-zip` packs a livery's style, helper, fonts and contact sheet for matplotlib outside
  the decks; each release carries one per livery.

### Decks
- pptx is the engine's own format, `--to engine-pptx`, with its filters; the eight post-render
  steps run in one pass (`pptx_post.py`).
- pptx boxes that hold text (caution slides, feature panels, centred tables, the band title) are
  cut to their measured text: caution boxes come out tighter, feature panels a line taller.
- HTML has the chart colors as `--engine-data-*` properties, PowerPoint as a Custom Colors row.

### Liveries
- `charts:` in `livery.yml`: `anchors`, `extended`, `avoid`, `chroma`, a brand's published
  `ramps` and `sets`, extra color `maps`, the default map, and pinned `categorical`, `diverging`,
  `status`, `muted` (and `dark:` versions). `livery_check.py --swatch DIR` draws the contact sheet.

### LaTeX
- `EngineData1`... and `EngineStatus*` colors, and a `livery` pgfplots cycle list, the default
  once pgfplots is loaded.

## [1.0.0] - 2026-10-18

The first release of this repository as one: the multi-brand framework and the engine that draws
its decks, merged with the engine's history (#57 Phase A), its layout flattened, one version.

The engine was `benkirk/beamer-livery-theme` (now archived; its last release v3.8.0), itself the
generalization of `benkirk/NCAR_beamer_template`. Its 3.x line made the NCAR theme an engine for any
brand: 3.0.0 renamed it (`engine-beamer`, `engine-revealjs`, `\usetheme{Engine}`) and read the
brand from a livery's generated files; 3.1 and 3.2 added the band title and the closing and light
title layouts in pptx; 3.3 chose marks by field and preferred a brand's installed fonts; 3.5 drew
the title, section, closing and feature slides from one set of compositions in every format; 3.6
and 3.7 set type in points on each livery's canvas, with a deck's size step (`type-body:`,
`type-scale:`); 3.8 added the NASA liveries. Version numbers restarted at 1.0.0 with the merge.

### Decks
- One Markdown file, three branded decks: `.pptx` (primary), `.html` (revealjs) and `.pdf`
  (beamer), under any livery (`make pptx LIVERY=<name>`), with `make qa`, `make measure`,
  `make site` and `make publish`.

### Liveries
- Eight: `ncar`, `ucar`, `ucp`, `ncarucar` (the NSF NCAR family), `cu` and its flavor `nsi`
  (University of Colorado), `nasa` and `nasa-dark`. A livery is `_brand.yml` and `livery.yml`,
  built into `build/` and a generated `template.pptx`.

### LaTeX
- Every livery is a pure-LaTeX beamer theme too (`\usetheme[livery=<dir>]{Engine}`), and each
  release carries an Overleaf project per livery.

[Unreleased]: https://github.com/benkirk/quarto-livery-decks/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/benkirk/quarto-livery-decks/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v1.0.0
