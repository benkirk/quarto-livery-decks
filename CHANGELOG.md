# Changelog

What each release changes for the people who use it, newest first, in the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) shape: **Decks** (what a deck author
sees), **Liveries** (what a livery owner must do), **Plots** (what a plot author sees) and
**LaTeX** (the theme's options and commands). The engineering narrative up to the first release
is `design/engine-and-liveries.md`, section 10; since then the PR bodies and
`design/unplanned-city-ledger.md`.

**Versions are calendar versions, `YY.MM.N`**: the year and month of the release, the month
unpadded, and `N`, from 0, the month's release count (`26.10.0`, `26.10.1`, ..., `26.11.0`). The
version is the engine's, `version:` in `_extensions/engine/_extension.yml`, and a release is the
tag `v<version>`. Tags are never moved: another release in the month is the next `N`. The
month's newest release is also `YY.MM` where a tool supports a moving name: the container image
(`ghcr.io/benkirk/quarto-livery-decks:26.10`). Compatibility is not in the number: a livery's
contract is its `schema:` (1), and what a release asks of you is in its *Liveries* section here.
A release's entry is written here before its tag is pushed, and becomes its notes on GitHub.

## [Unreleased]

### LaTeX
- `build/livery.sty` carries the livery's roles and blends by name (`\engine@role@<name>`, the
  color each stands for) and the card roles by place in a row (`\engine@boxes@card@roles`), so the
  theme resolves a `role=` itself.
- A strip inside a card no longer sets an overfull line (6 pt at ncar's body): the strip widened
  its line by the card's pad and took back only the left one. Nothing moves on the page; the
  `Overfull \hbox` goes from the log.
- Cards and strips take keys: `\begin{enginecards}{3}` (or weights, `{2,1,1}`) holds
  `\begin{enginecard}[role=secondary, pick, solid]{Title}{Sub}` (`{}` for no sub-line; `plain` for
  a column beside cards), and `\begin{enginestrip}[role=accent]`. A `role=` is a role or blend of
  the livery by name, else any defined color, else a warning and the default (a card's place in
  the row; a strip's accent). `pick=<2>` draws the outline on those steps only, its width kept on
  every step. The old positional form (`{<TeX color>}{<share>}{<n>}`) is gone; the Quarto filter
  writes the new one.
- Status lists: `\begin{enginestatus}` with `\done`, `\warn` and `\fail` items (an overlay spec as
  on `\item`: `\warn<2->`) and plain `\item`s, ✓ ⚠ ✗ as the bullets in the livery's status
  colors, a failed item muted to its end; `\engineglyph{done|warn|fail}` is the glyph anywhere.
  The three names exist only inside the environment. `\cmark`, `\xmark` and `\pmark` (and the
  pifont they loaded) are retired.
- Columns for a hand author: `\begin{enginecolumns}{2,1}` with `\enginecolumn` opening each column
  at its share of the text width less the livery's gap (and its rule, when it draws one), over
  beamer's `columns`; `\enginecolshare` and `\enginecolrule` stay as the primitives.
- `\begin{enginescale}{1.4}` scales a body (its lists, tables and code with it), and
  `\enginemarking{CUI}` in the preamble sets the marking strip's text (`{}` for none): the
  filter's private preamble macros for `scale=` and `marking:` are theme commands.

## [26.10.7] - 2026-10-21

### Decks
- A `{.shrink}` slide keeps its text color in the PDF. Beamer's shrink box reset it to black,
  so a dark livery's shrunk slide (the quickstart's equations) was black on black, and a light
  livery's shrunk text black instead of the brand's.
- A marking strip on every slide (`marking: "CUI"` in the front matter), in every format, for a
  restriction or distribution marking: the livery places and colors it, and may set default text
  (`marking: none` turns that off). nasa-jsc-eg shows a demo where its template has the strip.
- pptx: a closing slide or divider whose column hangs from its top (`anchor: top`) does so, as in
  HTML and PDF: the closing's body follows its measured headline, a divider's block starts at the
  column's top. Both were centered on the column before, whatever the anchor.
- A section divider can go without its "SECTION n" label (`section.label: null`) in every
  format; the PDF stopped on it before, and the pptx ignored it. The PDF now sets the livery's
  label word (it always said "Section"), and the pptx its label color.

- PDF: a `{.full}` slide's caption is set at the caption size; it was the body's (the node's
  font never selected the size).

- pptx: a slide of three or more columns shows them all, at the same widths and gap as HTML and
  PDF (pandoc's pptx kept the first two and dropped the rest without a word). A picture or table
  in such a column is not drawn in it yet: the render warns, naming the slide.
- A `{.caution}` slide's bar and pads, and a feature slide's panel pads, are the same in every
  format: the livery's `boxes:`, HTML's numbers. The pptx bar is a little thinner (ncar 4.5 to
  3.6 pt) and its pads follow the body type; the PDF bar is thinner (3 to 2.3 pt) and its text
  sits 0.9 em from the sides, as HTML's (0.55 em before), so a long caution line can wrap sooner.
- Columns are laid out alike in every format: each its `width=` share of the text width less the
  livery's gap (a column without a width shares what is left equally). pptx two-column slides
  take their widths (pandoc wrote two halves), a picture or table in a column moving with it;
  HTML columns get the gap in place of Quarto's small side margins; PDF columns keep to the text
  width (they reached into the margins).
- `{.wide}` on a slide's heading widens its body to the slide less a narrower margin
  (`geometry.wide-margin`), in every format: room for three or four columns, or a wide table.
- A rule between columns where the livery sets `boxes.columns.rule` (nasa-jsc-eg's hairline), in
  every format, centered in each gap and as tall as the row's tallest column.
- PDF: a cover whose field is the whole slide shows its photo, as HTML and pptx do; the field was
  painted over it (#125). Covers with a partial field (ncar, cu, nsi) are unchanged.
- PDF: a slide's body starts at the top, under its title, as in HTML and pptx; beamer centered
  it vertically. `{.vcenter}` (or `{.center}`) still centers a slide in every format.
- A lead box, `::: {.lead}`, before a slide's columns or alone: its lines on the livery's lead
  fill with an accent bar at its left, in every format (pptx: native shapes and a text box). In a
  lead each source line is a line: a bold headline over a plain line needs no blank line.
- Cards: `::: {.column .card}` with a `###` title and an optional `[...]{.sub}` line draws a head
  band over a body, in its `role=` or else the livery's `boxes.card.roles` by its place in the row
  (primary, secondary, accent), so a row's cards differ; `.pick` outlines the chosen card, `.solid`
  fills the whole card with the role; `[LOCAL INVESTMENT]{.label}` and `[$20M]{.big}` are a small
  caps label and a big number. A row's cards are one height, in every format; pptx draws them as
  native shapes and text boxes, editable in PowerPoint, each card (and a lead box, a strip) one
  group: a click selects the card, a second its text. A picture or table in a card is not drawn
  in it yet (a warning; the PDF draws a row with a table as plain columns).
- A strip, `::: {.strip role="accent"}`, in a card or on its own: a band tinted in its role
  (`boxes.strip.tint` over the background) at the card's full width; on a solid card the role
  itself. Every format.
- A card's or strip's `role=` may be a role or a blend of the livery (`table-band`, `rule`); a
  name that is neither warns once per format, naming the slide, and takes the default (the
  card's place in its row, a strip's accent). Before, HTML drew the name as given, the PDF
  failed on an undefined color, and the pptx fell to primary without a word.
- Status items: in a card or a `::: {.status}` list, `- [x]`, `- [!]` and `- [-]` show ✓, ⚠ and ✗
  in the livery's status colors (`boxes.status`), where the bullet was, a failed item's text
  muted; a literal ✓ ⚠ ✗ first in an item works anywhere. `- [ ]` stays a task list's box.
- The sample deck shows each of these (a 2/3 and 1/3 split, three plain columns, four on a wide
  slide, option cards with a lead, a strip and status items, solid cards), and the quickstart a
  card slide, in the README. docs/authoring.md "Columns" and "Cards and lead boxes".
- `make measure` skips a composition's empty box instead of stopping on it.
- pptx: a card's head band is square at its foot on a livery with rounded cards (ncar and its
  family); it was rounded all round, so the card's fill showed at the band's lower corners.
- pptx: a box cut to its text (caution, lead, the feature panel, a note under a figure) is sized
  with the template's own paragraph spacing; it was a little short, and the slack covered it.

### Liveries
- The `livery` command: `inspect` without `-o` prints its report; `new --from <deck> --extends
  <parent>` keeps the deck's report too; a new flavor's first `all` passes its checks (its build
  had named the parent's template).
- `marking:` (`edge`, `offset`, `width`, `height`, `align`, `fill` and `color`, each a role or a
  hex, `bold`, `text`) and
  `type.marking`: the marking strip's look and a default text.
- A cover's text in two parts: `compositions.title.byline` (`role`, `box`, `anchor`, `align`,
  `elements`) takes the author, institute and date (by default) apart from the title and subtitle,
  in its own color and, with a box, its own stack; `column.elements` orders the column's. Without a
  byline every cover is as before. The pptx draws the byline as a text box, the institute
  included (pandoc's pptx never showed it).
- `compositions.<name>.column.align: center` centers a composed slide's text (the closing's
  "Thank you!", a divider, the cover, the feature title) and its rule, in every format. Each
  composition part's keys now have their own table in `liveries/REFERENCE.md`.
- `section.label: null` drops the divider's eyebrow in every format;
  `section.label-color` now reaches the pptx too.
- `nasa-jsc-eg`: the NASA JSC Aeroscience and Flight Mechanics Division's template, dark, a
  flavor of `nasa-dark`: a starfield behind every slide, the division bar along the foot, the
  cover's yellow band, lab photo and the division's and a group's patches (the title on the band,
  the byline below it), the closing's centered patch and text, the template's marking strip with
  demo text, Arial (Liberation Sans standing in). A group in the division puts its own patch on
  the cover with a one-key flavor (`liveries/nasa-jsc-eg/reference/notes.md`).
- `boxes:`: one set of numbers for the columns and boxes every format draws (`columns`,
  `caution`, `panel`, `lead`, `card`, `strip`, `status`): gaps, bars, outlines and radii as
  fractions of the slide, pads in em of the body type, colors a role, a palette name or a hex. A
  livery sets only what differs (`liveries/REFERENCE.md`); ncar rounds its cards' corners and
  keeps its status glyphs off yellow, nasa-jsc-eg rules its columns. `type.display`: the size of
  a card's big number (default as the closing's headline).
- `bullets:` (`glyphs`, one per list level, the last repeating; `color`, a role, a palette name or
  a hex): a livery's own list glyphs in every format, in place of the dot, ring and bar. Without
  it nothing changes. nasa-jsc-eg uses its template's white square, dash and dot.
- `compositions.<name>.mark.image` and `.signoff.image` (a `logo.images` name) put a given
  image on one composed slide, in place of its field role's; a light variant keeps it. nasa-jsc-eg
  names its group patch and the NASA wordmark this way; its light title and closing showed the
  division bar in the patch's box.
- A flavor unsets an inherited `art` picture (`art: {titlegraphic: null}`) or code face
  (`typography: {monospace: null}` in its `_brand.yml`) with `null`. nasa-jsc-eg's cover no
  longer doubles as its default title photo: it is the title composition's art.
- `pptx.code-typeface`: the font the pptx sets code in, an installed face as a brand template
  names it (nasa-jsc-eg: Courier New); HTML and PDF keep `typography.monospace`.
- `art.title-light`: a picture covering the light cover's field (`themeoptions: [title=light]`),
  in every format; without it the light cover has none, as before.
- nasa-jsc-eg's light title (`themeoptions: [title=light]`) is its template's light cover: the
  band, lab photo and patches on white, the text black.
- `geometry.wide-margin` (default half the margin), a `{.wide}` slide's side margin, and
  `geometry.body-bottom`, the content body's foot, which the template and the plots' size read.
- A photo cover may have `field: null` (no field under the text); it stopped the pptx and HTML
  renders before.

### LaTeX
- The theme states its requirements: a LaTeX kernel of 2022-06-01 or later (`\NeedsTeXFormat`
  in `engine_livery.sty`, which every theme file loads through) and `tcolorbox` with `skins` and
  `breakable`, which the cards made unconditional. latex/README.md names both.
- Frames are top-aligned (the class option `t`, without beamer's 0.2 cm under the title); give a
  frame `[c]` to center it.

## [26.10.6] - 2026-10-20

### Decks
- A figure's caption looks the same in every format: the caption size, the livery's muted
  color, centered, just under the picture. HTML centered a lone image's caption (it sat at the
  left); the PDF drops its "Figure 1:" / "Table 1:" label and sets the caption muted; pptx gives a
  figure's own caption that look without a `::: note` too (it kept the layout's size and the body
  color).
- Tables and their captions are centered in every format. HTML centers a table in the body (or
  its column) with its caption under it (both sat at the left); pptx sets a table's caption in
  the caption look just under the table (it sat at the slide's foot, in body size); the PDF
  already centered both, the caption above the table.
- `make qa` no longer reads a table's caption (or a note under it) as a cell running into the
  next column; the sample deck's qa passes, and CI runs it.
- Decks in the cloud, nothing installed. `.devcontainer/` opens the repository in GitHub
  Codespaces on the published image (the README's badge, or `gh codespace create` and `ssh`
  from a laptop), within a personal account's free quota one codespace at a time
  (docs/container.md "In GitHub Codespaces"). A repository of your own decks builds them on
  every push with the reusable workflow `build-decks.yaml`: the pptx, PDF and HTML attached
  to the run, one directory's site deployed to GitHub Pages (docs/other-repos.md "Building
  in GitHub Actions").
- The image tag `latest` is the newest release, as an anonymous pull expects; `main` names
  the main branch's head as before.

### LaTeX
- A beamer caption is its text alone, muted and centered: no "Figure n:" / "Table n:" label.

## [26.10.5] - 2026-10-20

### Decks
- A pptx opens in Keynote. pandoc writes speaker notes without the color map PowerPoint
  gives every notes slide, and Keynote 15.4 refuses the whole file for it ("The file format is
  invalid"), so any deck with notes, the quickstart included, failed to import. The new pptx
  step `notes_clrmap` adds it, in PowerPoint's own form; PowerPoint opens the deck as before.

## [26.10.4] - 2026-10-20

### Decks
- A pptx imports into Google Slides. The wave bands and cover fields marked their path
  `stroke="0"`, which PowerPoint accepts and Google Slides' import refuses ("Upload failed") for
  the whole file. Their outline is already off through `a:ln`, so the mark is gone, from the
  templates (ncar, ncarucar, ucar, ucp regenerated) and the covers `slide_layout.py` draws;
  nothing looks different. `livery check` fails a template that has it.
- `::: note` after a slide's figure or table: a remark drawn as its caption in every format, the
  caption size in the livery's muted color, centred, just under the figure (as a `{.full}`
  slide's caption). In pptx it joins pandoc's caption box, which moves up under the picture or
  table; a `†` line in it stays a footnote. Opt-in: a paragraph without the div looks as before.
  `make qa` fails a note paragraph that wraps in HTML. docs/authoring.md "Notes under a figure".
- pptx: a paragraph after a captioned figure is kept. It vanished (the sample's "Image embed"
  lost its remark): pandoc captions a picture from its image's text, which the fold now fills.
- HTML: a table's caption is set at the caption size, as a figure's is; it was 0.8 of the
  table's text, a little larger.

### Plots
- pptx plots are vector. Each is an SVG with a 200 dpi PNG beside it, as PowerPoint saves one:
  PowerPoint draws the SVG, sharp at any zoom, and Google Slides' import shows the PNG. A deck
  grows: this plots deck 1.9 to 2.2 MB, a 33-plot report 7.5 to 10.4 MB. `livery_mpl.raster()`
  now makes a plot PNG in pptx too. The image and the conda env gain `librsvg` (`rsvg-convert`).

## [26.10.3] - 2026-10-20

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
- A deck can draw its HTML plots as PNG, `format: engine-revealjs: fig-format: png` in its front
  matter, when its SVGs are heavy (`docs/formats.md` "HTML (revealjs)").
- `livery_mpl.dense(scale=0.65)`: every text size scaled together inside the block, to the half
  point, for small multiples (a 3 x 4 grid at the slide's sizes crowds out its data).
- `livery_mpl.mix` and `livery_mpl.surface` are public (`__all__`): a color moved toward another
  in OKLab, and the background the plot sits on, the dark one inside `dark()`.
- `shade_family` tints toward the dark surface inside `dark()` on a light livery (it tinted toward
  white there).
- `with livery_mpl.raster():` shows the figures inside as PNG where the deck draws vector (HTML's
  SVG, the PDF's PDF): one heavy time series goes PNG, the rest of the deck stays vector. A cell's
  own `fig-format` is not honored by the Jupyter engine, so this is the per-plot form.

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

[Unreleased]: https://github.com/benkirk/quarto-livery-decks/compare/v26.10.7...HEAD
[26.10.7]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.7
[26.10.6]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.6
[26.10.5]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.5
[26.10.4]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.4
[26.10.3]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.3
[26.10.2]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.2
[26.10.1]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.1
[26.10.0]: https://github.com/benkirk/quarto-livery-decks/releases/tag/v26.10.0
