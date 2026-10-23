# CLAUDE.md

Guidance for working in this repository. Keep it accurate — update it when the
structure or conventions below change.

## What this is

A [Quarto](https://quarto.org) framework for documentation decks (`.pptx`
primary; `.html`/revealjs and `.pdf`/beamer secondary) and the engine that draws them, in one
repository. It is the **multi-brand successor** of `benkirk/quarto-docs-framework` (the
`upstream` remote), which stays the NCAR framework. The **engine**
(`_extensions/engine/`: the beamer and revealjs themes, the livery tools, the
Overleaf packer) was `benkirk/beamer-livery-theme` until 2026-10, when it merged here with its
history (#57; `git log --follow` reaches back through it); it generalizes
`benkirk/NCAR_beamer_template`, which is untouched and no longer cherry-picked from (port a fix
by hand). Each brand is a **livery** directory under `liveries/` (`ncar`, `ucar`,
`ucp`, `ncarucar`, `cu`, `nsi`, `nasa`, `nasa-dark`, `nasa-jsc-eg`), built by `livery build`
into `build/livery.{json,sty,css,theme,mplstyle}`. `livery.yml` starts with `schema: 1` and is
validated against `_extensions/engine/livery.schema.json` (`livery_schema.py`; an unknown key or an
out-of-range value fails the build with its path); `liveries/REFERENCE.md` is generated from the
schema (`livery schema --doc`; `tests/test_schema.py` holds it current). A key is renamed only with Ben's
agreement.

The engine is a design framework for technical presentations: an element is one reader, one
drawer per format, every number from the livery (`design/engine-and-liveries.md`, the head).

**The `livery` command** is `_extensions/engine/livery.py` (argparse subcommands; README for
owners: `liveries/README.md`), launched as `bin/livery` (on PATH after `source etc/config_env.sh`
and in the image; it follows links to itself; the Makefiles call `python3 $(LIVERY_PY)` and need
no PATH). `check` is quiet (warnings, failures, a summary line; `-v` for all); a palette name
that is not one fails with its key (`roles.accent: ...`): `new` (`livery_new.py`: a scaffold that builds as it stands, Public
Sans from `liveries/nasa` as its stand-in face, a placeholder mark; `--from <deck>`, `--extends`),
`inspect` (`livery_inspect.py`), `build [--check]` (`livery_build.py`), `template`
(`livery_template.py`), `check [--swatch] [--qa]` (`livery_check.py`; `--qa` runs the quickstart's
`make qa` with `LIVERY=` for a bundled livery, else `LIVERY_DIR=`), `all` (build, template,
check; the root `make livery LIVERY=|LIVERY_DIR=`), `zip [--charts]` (`overleaf_zip.py`,
`mpl_zip.py`), `schema --doc`, and `deps|mono|figsize` for `Make.common`. The modules have no
entry points of their own; `livery.py` imports each only when its subcommand runs, so `zip`
needs nothing beyond Python (the release job).
`design/engine-and-liveries.md` is the roadmap; its section 10 logged progress up to the first
release (26.10.0), since when `CHANGELOG.md` is the record of what ships and
`design/unplanned-city-ledger.md` of what the sweeps find.

The engine also holds the json reader (`livery.py`, also the command), the wave shapes
(`pptx_waves.py`) and the pptx post-render steps (`pptx_post.py` over `pptx_steps/`);
`utils/comp_measure.py`, `deck_qa.py` and `site_index.py` append the engine's directory to
`sys.path` to import the reader. Onboarding a brand from a reference PowerPoint (design section
6): `livery new liveries/<name> --from <deck>` writes `reference/report.md` and the scaffold,
`make livery` builds and checks it, and the decisions go in `reference/notes.md`. `nsi` (the CU Center for National Security Initiatives) is `cu`'s
flavor (`extends: cu`) on the band title style (`title: {style: band}`); `nasa` (NASA general,
external communication; no official template, so the Brand Center's rules and NASA Science's
public-engagement deck) and its flavor `nasa-dark` (content on black) are the first dark
livery (see "Dark liveries" below); `nasa-jsc-eg` (the JSC Aeroscience and Flight Mechanics
Division's template) is `nasa-dark`'s flavor with the template's furniture as art rendered from its
layouts (`reference/eg_art.py`) and a group's patch as a mark a group's own flavor swaps. The reference decks themselves live on Drive or a laptop,
not in git. A livery without `pptx.fonts` embeds nothing (`embed_fonts.py` says so and leaves
the deck alone); a livery without `art.waves` gets straight-edged title fields in every format.

`latex/` is the engine's pure-LaTeX side (the starter `talk.tex`, a link to the
extension's copy; the cookbook `examples/sample.tex`, the sample deck's twin, and the guide
`latex/authoring.md`; `examples/` and their variants; `make latex`), and `tests/` holds the
engine's tests (`make test`), both parity harnesses ("The engine" below) and `app-open.sh`,
the release's check in Keynote and PowerPoint ("Version" below).

Decks live under `decks/<deck>/` as a `.qmd` plus a 1-line Makefile
(`include ../../Make.common`). The shared machinery sits at the top since the flatten
(2026-10-18): `Make.common`, the engine in `_extensions/engine/`, the liveries (each with its
`template.pptx`) in `liveries/`, and `common/` (`_quarto.yml`, the
post-render utilities); `latex/`, `design/` and `tests/` beside them. No `_quarto.yml` at the
root: each deck is its own Quarto project through its linked one.
`decks/quickstart/quickstart.qmd` is the short exemplar to copy for new decks;
`decks/sample/sample.qmd` is the cookbook of every pattern, `decks/plots/plots.qmd` that of
plots (`jupyter: python3`; `decks/plots/README.md`). `docs/formats.md` covers the layout tree, the
build pipeline, template constraints and font embedding; `docs/container.md` the image's use;
`docs/other-repos.md` the submodule layout and publishing.

- **README images** are `decks/quickstart/screenshots/*.png`, committed. After
  editing the quickstart deck run `make screenshots` there, look at them, and
  commit them. Slides are found by title (`SLIDES` in `screenshots.py`), so a
  renamed slide needs that list updated. `make gallery` (`gallery.py`) writes
  `liveries.png`, the deck under every livery (title, divider, content, closing),
  rebuilding the HTML per `LIVERY`; `screenshots.py` leaves that file alone. Where the MathJax CDN is blocked, set
  `MATHJAX` to a local MathJax 2.7 (the npm tarball from registry.npmjs.org),
  or the equations shoot as raw TeX.

Other repos can take the framework as a submodule and keep their decks in their
own tree (`docs/other-repos.md`); the deck Makefile
includes `../framework/Make.common`. So nothing may assume a deck sits in
`decks/<deck>/`: the shared `_quarto.yml` and the engine (`_extensions`, whose formats carry
their Lua filters) are links Make creates in each deck directory. `ci.yaml`'s `consumer` job builds a deck that way,
and the image's smoke test a bare directory with no Makefile at all (`make -f
<framework>/Make.common DECKS=...`, which the entrypoint supplies).

## Environment & build

- **Env**: `source etc/config_env.sh` (or `conda activate ./conda-env`; build it
  with `make conda-env`). Quarto **requires real conda activation** — the
  `activate.d` scripts export `QUARTO_DENO`, `QUARTO_PANDOC`, etc.; merely
  putting `conda-env/bin` on `PATH` fails with a missing-deno error.
- **Container**: `ghcr.io/benkirk/quarto-livery-decks` (root `Dockerfile`; `make image` builds it
  locally, `.github/workflows/image.yaml` publishes it for amd64 and arm64, `docs/container.md`) carries the conda env, apt TeX Live, LibreOffice, a broad font set and ONE Playwright
  headless Chromium that both Quarto (`QUARTO_CHROMIUM`) and `make qa` (`CHROME`) use, at
  `/opt/pw-browsers/headless_shell`; the framework is at `/opt/quarto-livery-decks`. The activation
  is baked as Dockerfile `ENV` and asserted against conda-forge's `activate.d/quarto.sh` at build
  time, so `docker run`, any `--user` and GitHub `container:` jobs (which bypass the entrypoint) see
  the same environment. `etc/entrypoint.sh` only gives an arbitrary uid a writable HOME and turns
  `make` in a Makefile-less directory into `make -f /opt/quarto-livery-decks/Make.common
  DECKS=<its qmds>`, and seeds matplotlib's font cache (built into `/opt/matplotlib` over every
  font, the liveries' too) into HOME unless `/opt/fonts` has files (a cache never rescans);
  `container:` jobs bypass it and build their own on the first plot. `/opt/fonts`, an empty mount point for a host's licensed fonts
  (`-v "$PWD/fonts:/opt/fonts:ro"`), and the image's liveries' `fonts/` are linked under
  `/usr/local/share/fonts`, so LibreOffice renders a pptx with its real faces when `make measure`
  shoots it (a livery mounted from the host is not covered). Two fontconfigs live in the image:
  the conda env's (`fc-cache`/`fc-list` on PATH, its own `fonts.conf`) and the system's
  (`/usr/bin/fc-*`, `/etc/fonts`), which the apt XeLaTeX, Chromium and LibreOffice use; a file in
  `/etc/fonts/conf.d` reaches only the second, a directory under `/usr/local/share/fonts` both.
  Everything under `/opt` must stay world-readable (asserted). Chromium (the headless shell) bundles
  its own fontconfig, whose index format the system's 2.15 does not write: step 7 builds it into
  `/var/cache/fontconfig` and asserts an empty HOME gets none. Without it a new HOME indexes every
  font on its first diagram (~5 s on a busy login node). The root was Quarto's `waitForServer`: it
  gives up after 3 s and then awaits the healthy browser's exit forever, so any slow start hung a
  render; step 5 patches it to 30 s in the bundled `quarto.js`, asserting the exact line (a new
  Quarto that changes it stops the build). The font index stays: 5 s and 88 files per new HOME. Apptainer runs `--cleanenv` in every documented form (the
  host's variables stay outside: a Casper profile's `TMPDIR` stopped Quarto), and it still binds
  HOME, so the last `ENV` guards against what HOME holds: `PYTHONNOUSERSITE=1` (`pip --user`) and
  `JUPYTER_PREFER_ENV_PATH=1` (the image's kernels over `~/.local/share/jupyter`). `smoke-test.sh` takes `RUNTIME=docker|podman|apptainer` (default
  docker, as `image.yaml` calls it); its container calls go through one adapter (`argv`). The two
  `_quarto.yml`/`_extensions` links are `ln -sfn`, so a dangling link left by the other
  side (host or container) is re-pointed; a real file or a resolving link is never touched.
- **Runtime**: `DECKS_RUNTIME` (`auto` default: native when `quarto` is on PATH, else the first
  of apptainer, docker, podman) at the top of `Make.common`; anything but native includes
  `common/Make.container`, which runs the goals as ONE `make ... DECKS_RUNTIME=native` in the image,
  the deck's git toplevel, the framework, an outside `LIVERY_DIR`, the existing `DECKS_BINDS` and
  uncovered symlink targets in the deck directory mounted at their real paths, with its own HOME
  (`DECKS_HOME`, `~/.cache/quarto-livery-decks/home-<tag>`: the user's HOME, an `npl` env's Jupyter
  and IPython settings and the rest, never reaches the image's tools; a `$(shell)` with a `case`
  needs `(pattern)`, or its `)` ends the function)
  (command-line variables ride MAKEFLAGS, under Apptainer as APPTAINERENV_MAKEFLAGS since it runs
  `--cleanenv`: a Casper profile's TMPDIR leaked in and stopped Quarto; `publish` pushes from the host via the shared
  `publish_push`). The header and `Make.container` must parse under GNU make 3.81, since macOS's
  `/usr/bin/make` has to reach the dispatch; the native body runs under the env's make. Image:
  `DECKS_IMAGE`:`DECKS_IMAGE_TAG` (default `_extension.yml`'s version; `sha` the checkout's), or
  `DECKS_CONTAINER_IMAGE`, `APPTAINER_SIF` (all in `common/image.mk`, which the top Makefile's
  `make sif` shares). The image's ENV says native. smoke-test.sh step 3 runs it per runtime.
- **A shared installation** (docs/container.md "Sharing an installation"; NCAR HPC:
  `/glade/work/benkirk/repos/quarto-livery-decks`): `make sif` pulls the checkout's release into
  `sif/quarto-livery-decks_<tag>.sif` (gitignored, kept by `clobber`), which Make.container runs
  when no image is named; `bin/new-deck DIR` starts a deck from the quickstart with an absolute
  `include` of this checkout's Make.common. Its untracked `site.mk` (read by Make.common and the
  top Makefile, kept by `clobber`) holds `DECKS_BINDS ?= /glade /lustre/desc1 /gpfs/csfs1
  /local_scratch` (NCAR's file systems appear under two names). Lmod module support is deferred.
- **Cloud**: `.devcontainer/devcontainer.json` runs the image in GitHub Codespaces (`:main`, the
  image of main's head whatever branch is opened; the `sshd` feature layered at creation for `gh codespace ssh`, nothing
  added to the Dockerfile; `postCreateCommand` calls the entrypoint with `true` for the matplotlib
  seed, since dev containers replace the entrypoint, and writes a `profile.d` line putting the
  checkout's `bin/` first on PATH (`remoteEnv` reaches VS Code's shells, not an ssh login); docs/container.md "In GitHub Codespaces":
  the custom image counts against the free storage quota, so one codespace at a time). The
  reusable `build-decks.yaml` (`workflow_call`) is a consumer's cloud build: `make` per deck
  directory in the image (`:latest`, the newest release), the outputs as the `decks` artifact,
  `pages:` one directory's site to GitHub Pages; its env names avoid `DECKS`/`LIVERY`, which
  make would take over `?=`; ci.yaml's `reusable` job calls it on the quickstart;
  docs/other-repos.md "Building in GitHub Actions". Phase 2, a template repository, is #118.
- **Build**: `make pptx` (also `html`, `pdf`) inside the deck directory; pptx is
  `--to engine-pptx`, the engine's format (`_extension.yml`: the template default, `slide-level`,
  `toc` and the eight pptx filters in order; a project's `reference-doc:` wins).
  `Make.common` names the output after the directory (`OUT`) and auto-symlinks
  `_quarto.yml` and `_extensions`. The pptx recipe then runs the engine's `pptx_post.py`,
  which opens the deck once, runs the steps of `pptx_steps/` in order and saves once:
  `svg_fallback` (a PNG for each SVG plot, the SVG on Office's `svgBlip` extension, by
  `rsvg-convert`: conda-forge librsvg), `notes_clrmap` (each notes slide's `p:clrMapOvr`,
  which pandoc omits and Keynote requires), `section_subtitle`, `enable_autofit`, `embed_fonts`
  (on the zip's parts), then
  `style_footnotes`, `link_captions`, `slide_layout`, `columns` (a two-column slide at its
  widths and the livery's gap, from `grid-pptx.lua`'s notes line), `grid` (a grid slide from its
  marker paragraphs), `status_glyphs` (a ✓ ⚠ ✗ item's glyph as its bullet), `style_tables` (tables drawn as in the
  HTML theme), `marking` (the marking strip, before the size step so a deck's type step scales it
  as HTML and PDF do) and `type_step` (a deck's `type-body:`/`type-scale:`, last) on one
  python-pptx Presentation; each is a module with a `run()`, the order's reasons are in the driver; `pptx_steps/common.py` reads the livery once and holds what the
  steps share (`LIVERY`, `K`, `BOXES`, `SLACK`, `rect`, `rpr`, `set_fill`, `take_marker`, the shape tests), `measure.py` the text
  measuring (`text_height`); a step imports no other step's private name (`tests/test_cli.py` greps for it). Text
  that sizes a box (dividers, caution boxes, feature panels, centered tables, the band title) is
  measured by `pptx_steps/measure.py`: PIL on the livery's bundled faces, each run in the face
  the pptx shows (the pptx typeface as its stand-in, titles in the headings family only with a
  `pptx.heading-typeface`, Courier and other unbundled faces at 0.6 em a character). pandoc gets `-M monofont=<family>` when the livery bundles a
  code face (`typography.monospace`) or names `pptx.code-typeface` (`livery.py mono`), and the pptx format takes the
  livery's highlight theme (`_livery/build/livery.theme`) like HTML and PDF.
- **Publishing**: `make site` gathers the HTML decks into `_site/` (one shared
  `libs/`, `images/`, `SITE_EXTRA` directories, an index from `site_index.py` in
  the livery's colors with its fonts copied to `fonts/`;
  `SITE_NOINDEX=1` marks every page noindex) and `make publish` force-pushes it
  as the one commit on `PUBLISH_BRANCH` (gh-pages) under `PUBLISH_PREFIX`.
  docs/other-repos.md "Publishing the HTML decks".
- **Overleaf**: `make overleaf LIVERY=<name>` (any deck directory; `LIVERY_DIR=` for a consumer's
  own livery) writes `<name>-overleaf.zip` with `livery zip`: the theme's `.sty`,
  the livery's `build/livery.sty`, fonts, logos and art (a flavor's parent files beside it), a
  `latexmkrc`, a starter on `livery=liveries/<name>, fonts=bundled`, and the cookbook
  `sample.tex` with the files it needs (`overleaf_zip.py`'s `COOKBOOK_FILES`); each compiles
  with `latexmk -xelatex <deck>.tex` alone. `release.yml` attaches one per livery to a GitHub Release
  on a `v*` tag (cut by hand, asked first, never moved: latex/README.md's Overleaf links serve
  `releases/latest`).
- **Slide footnotes** (a paragraph starting with `†`, `‡`, `§` or `¶`, the printer's order,
  `engine-common.lua` `MARKERS`): the theme lifts every one on a slide, columns included, to the
  slide's foot in HTML and PDF, under a short muted rule with the marker in the accent orange;
  pptx can't move content, so `style_footnotes.py` mutes them in place in the same colors.
  `*† text*` works too. A `^[...]` note is one: `lift_footnotes()` (called by `take_footnotes()`,
  so both hoists; in pptx by `inline-footnotes.lua`, which puts it in a plain two-column slide's
  last column) makes it a superscript mark (`.engine-noteref`) and a paragraph led by the next
  marker after the slide's dagger lines; one in the speaker notes, a fifth, or one holding a list
  stays pandoc's (warned). Beamer's hoist keeps the text as pandoc inlines between raw
  `\enginefootnote{m}{` and `}`, so citeproc (which runs after the filters) reaches a citation in
  it; beamer's own `\footnote`/`\footcite` take the same look (`\footnoterule`, the footnote mark
  color).
- **Citations** (`bibliography:`, `[@key]`; docs/authoring.md "Citations and footnotes"): Quarto
  appends citeproc after the extension's filters, so they see `Cite` inlines and the author's empty
  `::: {#refs}`; the entries exist only for the pptx steps, the beamer theme (Quarto's
  `CSLReferences` partial, which the inner theme takes over: 1.5 em hang, 0.4 em steps, beamer's
  `\bibitem` strut dropped) and the css. `engine-common.lua`'s `has_cites()`, `refs_div()`,
  `refs_heading()`, `ensure_refs()` (a References slide last, warned, when a deck cites without
  one): the slide holding `#refs` is `engine-references` (HTML), `allowframebreaks` (PDF; the
  continuation count only past one page), `engine-layout: references` (pptx,
  `slide_layout.py`'s `references_style()`), every one in the footnote size. Author-year styles
  only: a note style needs citeproc in the filter. The LaTeX cookbook cites with biblatex on
  bibtex (the image's `texlive-bibtex-extra`; biber is not installed); the theme's `bibliography
  item` must not assume `\insertbiblabel` (biblatex defines none).
- **Notes under a figure** (`::: note` right after a slide's figure or table): its
  caption, as the `.full` caption looks (caption role, muted, centered, just under it). HTML
  `.engine-note`, PDF `\enginenote` (both after the † lift, which reaches into it; after a
  table the filter writes `\vskip-\LTpost` first). pptx: `single-body.lua` folds it into the
  caption box and writes `engine-layout: note`; `slide_layout.py` splits the box at its line
  breaks (a † line keeps `style_footnotes.style()`'s left alignment), styles it and moves it up
  under the picture or measured table. A figure's or table's own caption takes the same look,
  note or not: HTML centers a lone image's `p.caption` and every table with its caption (under
  it), the PDF's caption is its text alone (no "Figure 1:", the theme's caption template and,
  since Quarto loads it first, the caption package's `labelformat=empty`; a table's stays above
  its centered longtable, beamer's place), and `single-body.lua` marks a captioned figure's or
  table's slide `note` too (pptx tables keep pandoc's full width). `make qa` fails a note
  paragraph that wraps in HTML; CI
  checks the sample's notes and captions in every format, and runs its `make qa`.
  docs/authoring.md "Notes under a figure".
- **Linked images** (`[![](x.png)](url)`): the picture is the link in every
  format, and each shows the URL: the HTML footer and a PDF foot line come from
  the engine's `linked-images.lua`, the pptx caption box from `link_captions.py`
  (after pandoc, because anything after an image splits a pptx slide). A deck
  should not hand-roll footers for this. docs/authoring.md "Linked images".
- **Short slides** (`{.hcenter}`, `{.vcenter}`, `{.center}`, `scale="S"`,
  `{.fill}`, `{.wide}`, each independent): the theme centers and scales the
  body in HTML and PDF; `.wide` widens it to the slide less `geometry.wide-margin` a side in every
  format (pptx: the body placeholders, a columns slide's columns). pptx drops slide classes, so the engine's `slide-layout.lua`
  writes them as a notes line, `engine-layout: vcenter scale=1.4`, which
  `slide_layout.py` applies and deletes; it can't do `hcenter` or `fill`, and
  centers a table by its measured height (rows in PowerPoint's own sizing can still differ). `.center` is the theme's, not
  Quarto's (which moves the title). docs/authoring.md "Centering and scaling a short slide".
- **Warning slides** (`{.caution}`): the body on a soft yellow
  field with a brand-yellow bar; footnotes stay below it in HTML and PDF. pptx:
  `slide_layout.py` fills the body text box, adds the bar, and cuts the box to its
  text, measured (pandoc gives it the whole content area). Set all four of
  a placeholder's left/top/width/height together: it inherits its frame, and
  setting one leaves the others at 0 (the text vanishes).
- **Full-slide figures** (`{.full}`): one diagram or image fills
  the slide, the paragraph (or `::: note`) after it is a one-line caption. HTML and PDF are the
  theme's (PDF frame key `enginefull=`). pptx: `slide-layout.lua` writes
  `engine-layout: full`, and `slide_layout.py` sets the slide's `showMasterSp="0"`
  (hiding the master's logo, tab, rule and waves), deletes the title, fits the
  one picture to the slide and centers pandoc's caption box under it. Any other
  body is left alone with a warning. `make qa` fails a caption that wraps. A `.gallery` may be
  the figure ("Galleries" below): HTML puts its grid in `.engine-full-figure`, beamer writes the
  bare `[enginefull]` key and the background draws the stored cells, and pptx's `slide_layout.py`
  only hides the furniture (`hide_furniture()`, for a body holding the gallery marker) and leaves
  the slide to `grid.py`.
- **Compositions**: the title (`title`, `title-photo`, `title-light`,
  `title-photo-light`, `title-band`), closing (`closing`, `closing-light`, `closing-band`),
  `section` and `feature` slides are boxes in `build/livery.json` `compositions` (`[x, y, w, h]`
  slide fractions, y down; every key, null when absent), derived by the engine's
  `livery_build.py` from the livery's knobs; `livery.yml` `compositions:` overrides a box (one on
  `title` reaches its variants; ncar's lowers the cover title to the brand template's 0.375) and
  `feature.style: bar | cover` picks the photo slide's look. One drawer per format reads them:
  beamer `\engine@drawcomp`, the revealjs `--engine-cmp-*` properties and `comp_art()`, the
  template builder's `field_layout()` (Title Slide, Title Slide (light), Section Header, Closing,
  Closing (light)), and `slide_layout.py`'s `draw_cover()` (the title photo, cropped into its
  box under the field and waves) and `draw_feature()`. Slide shapes always draw above layout
  shapes, so a pptx cover redraws its field, waves and marks on the slide. A cover's text is
  parts, each a stack in a box: the column (`column.elements`, the title always its) and an
  optional `byline` (`role`, `box`, `anchor`, `align`, `elements`: author, institute, date by
  default), drawn by beamer's `\engine@textstack` in `\engine@pnode`, `title-slide.html`'s second
  stack shown by the `--engine-cmp-<element>-*` properties, and `slide_layout.py`'s
  `cover_byline()` (the institute's first appearance in the pptx); `column.align: center` centers
  a composed slide's text and rule in all three. **`make measure`**
  (`comp_measure.py`; `MEASURE_FAIL` the formats whose deltas fail, CI report-only) shoots the
  four slides in every format and measures them against the boxes: `_qa/measure.tsv` and the
  contact sheet `_qa/compositions-<livery>.png`; `design/compositions-baseline.md` is the
  before-picture. The pptx can't flow a stack: `band_stack()` centers a band's date, title,
  rule and subtitle on the column from their text, measured (the rule moves onto the slide),
  a closing splits its column at the middle. Over art, a mark's box is the eroded mask's core
  widened along its rows (`widened()`), so thin type ("Office") is not lost.
- **Type**: text sizes are **points on the livery's pptx canvas**, whole or
  half points (a pasted slide carries round numbers; nasa: the reference deck's 10 x 5.625 in,
  body 12, titles 22): `livery.yml` `type:` (role -> pt, `levels`)
  and `pptx.size` (inches, default 13.333 x 7.5), defaulting to the engine's `TYPE` (the NSF NCAR
  template's guidance carried onto 540 pt). ncar is on the brand template's own canvas, 10 x
  5.625 in, at its guidance (body 12, titles 20; its family inherits); cu's are the NSI master
  deck's (body 16, titles 32, cover 48, dividers 60). HTML and beamer take the same sizes as fractions of the slide height, so
  the formats fit and overflow alike; the post-processors read `livery.type_pt()` and scale their
  absolute pads by `livery.canvas_scale()`; `scale=` rounds a pptx size to the half point.
  A deck's size step: front matter `type-body: <pt>` or `type-scale: <factor>`
  (beamer `typescale=`, HTML `--engine-type-scale`; pptx `type_step.py`, after every step that
  sets a size, reads it from `docProps/custom.xml`); `decks/fixtures/small.qmd` is `type-body: 10`.
- **Dark liveries**: `livery.json` `mode` is `dark` when the background is
  darker than the foreground (nasa-dark). The `code-text` role (default: `dark`) colors code,
  since a dark livery's `dark` stays a field color; beamer mixes its tints toward
  `BrandBackground`, not white; `livery.css` gains callout title tints and a lightness flip
  (CSS filter) for inline Graphviz. Quarto bakes mermaid and dot cells to PNG before any Lua
  filter runs (even `at: pre-ast`), so the engine's `diagram-dark.lua` swaps each baked picture for
  a copy from `diagram_dark.py` beside it (HLS lightness flipped, hues kept, white to the
  background, black to the foreground): Image elements in pptx, and in beamer the raw LaTeX
  and the `enginefull=` frame option the engine filter already wrote. HTML mermaid is live in
  the roles. A light livery is untouched. The pptx theme slots follow the roles, so `dk1`
  holds white (a native `clrMap` swap is a follow-up).
- **Content title**: `livery.yml` `frametitle: {align: left|center, tab, rule}`
  (nsi: centered, no tab, no hairline, as the NSI master deck's slide 20; its mark at the paper's
  edge, `geometry.logo.inset: 0.015`); the body starts below
  a mark taller than ncar's (`livery.json` `frametitle.body`). Beamer centers the title in the
  same band as HTML and pptx (it sat higher before).
- **Code face**: `typography.monospace` (brand.yml) with files of its own replaces LM Mono in
  beamer (at 1.0: a mono advancing 0.6 em is HTML's width), `--r-code-font` in HTML and
  pandoc's `monofont` in pptx (nasa: DM Mono); `pptx.code-typeface` overrides the pptx's with an
  installed face (nasa-jsc-eg: Courier New). The other liveries keep the defaults.
- **Title photo**: a deck's `titlegraphic:`, else the livery's `art.titlegraphic` (ncar: the
  Mesa Lab, inherited by its family; nsi: the campus; nasa: the Earth limb); `titlegraphic:
  none` keeps the plain cover (both engine filters and `slide_layout.py`; beamer
  `\enginenotitlegraphic`). `decks/fixtures/light.qmd` opts out, so the plain light cover stays
  in CI and parity. The quickstart sets none, so the gallery shows each livery's own.
- **Chart colors** (`design/charts-and-plots.md`): `livery.json` `charts` holds every livery's chart
  colors per mode, `light` and `dark` (categorical, families, sequential, diverging, status,
  muted), and `figsize`, the content area in canvas inches. The engine's `livery_charts.py`
  generates them at build time by the dataviz checks, or takes a brand's published palette from
  `livery.yml` `charts:` as given (ncar and ucar: sam-queries' validated sets and the UCAR web
  theme's tint ladders; nasa: NASA's Horizon Design System). `livery check` prints the checks
  (a generated palette must pass, a published one only warns), and `--swatch DIR` draws a
  contact sheet; `tests/test_charts.py`. `charts.chrome` is a plot's non-data ink per mode.
  `charts.maps` adds color maps without constraining the slots (`ramps` do), and `default-map` may
  name one: ncar's and ucar's vivid brand-blue maps, cu's campus map (its roof tile and sandstone
  sampled from nsi's campus photo). `decks/plots/README.md` shows the plots and palettes of every
  livery; `make gallery` there rebuilds its committed images.
- **Plots**: every format draws the chart colors. `build/livery.mplstyle` (`emit_mplstyle()`: the
  livery mode's chrome and cycle, transparent figures, the base family over DejaVu Sans, sizes
  from the type roles, `pdf.fonttype` 3 for a CFF `.otf` base family, cu/nsi, else 42; SVG text
  as paths); `livery.css` `--engine-data-*`/`--engine-status-*` (the dark set on `.brand-dark`);
  `livery.sty` `EngineData*` and a pgfplots `livery` cycle list (the default once pgfplots is
  loaded); `template.pptx` the mode's slots as a named `<a:custClrLst>` (PowerPoint's Custom
  Colors row, at most eight; `livery check` checks it). `Make.common` exports `MATPLOTLIBRC`
  (the style), prepends `_extensions/engine/mpl` to `PYTHONPATH` (`livery_mpl.py`: fonts by
  `addfont()`, colormaps with `_dark` twins, `figsize()`, `shade_family()`, `mix()`, `dark()`, `dense()`, `raster()`), passes
  `charts.figsize.full` as `-M fig-width/fig-height` to pptx and HTML (`livery.py figsize`; a
  cell's own wins; not to beamer, whose fig-width is paper inches and sizes its baked diagrams:
  4.25 in pushed the sample's Graphviz off the frame; `livery_mpl` sets PDF plots' size)
  and `ENGINE_FORMAT` per recipe (`dark()` applies only where the slide is dark: HTML, a dark
  livery). `common/_quarto.yml`: pptx svg (with `svg_fallback`'s PNG at its 200 dpi; PowerPoint
  draws the SVG, Google Slides' import the PNG), revealjs svg; beamer keeps Quarto's pdf at 300.
  Keynote 15.4 opens the deck too, since `notes_clrmap`.
  `engine-plots.lua` (dofile'd by both filters) shows a figure in Quarto's `figure-<format>/` at
  its natural inches over the canvas width: HTML `width: calc(<px> * var(--engine-fit))` with
  `.engine-plot` (out of reveal's auto-stretch, which sized a lone plot to the free height and
  left its text at 92%; no block margin; max-width 100%), beamer `\pandocbounded{\includegraphics
  [width=<f>\paperwidth]}`; pptx needs nothing (pandoc places a picture at its natural size, fit
  to the placeholder). Plot text then measures the slide's (HTML 1.00, PDF 1.00, pptx 1.01).
  `livery zip --charts` (`make charts-zip`) packs the style, the helper, `livery.json`, the fonts and
  licenses and the swatch sheet; `release.yml` attaches one per livery.
- **Marks and numbers** are livery parameters (`signoff`, `geometry.logo.corner`,
  `geometry.pagenumber.corner`; defaults are NCAR's layout) that the three themes
  and `livery_template.py` all honor. Which mark and sign-off a field wears goes by
  its role (`marks:`; `livery.json` always has `marks`, read with
  `livery.mark(livery, role, "logo"|"signoff")`): content slides `background`,
  dividers, covers and the cover closing `primary`, the band title and closing
  `title.field`. A composed slide's are its composition's: `compositions.<name>.mark|signoff`
  resolve to files (`img`, `img-print`), by `image:` (a `logo.images` name; a light variant keeps
  it) else the role's, and every drawer reads those (nasa-jsc-eg names its patches so). Defaults: background `logo.medium.light`/`signoff.light`, primary the
  dark ones, any other role primary's (nsi: black mark on gold, white on the band). pandoc writes no slide-number box, so
  `slide_layout.py` copies the layout's placeholder onto every slide; a livery's
  `typography.headings` may be a second font family (cu: TeX Gyre Heros Cn).
- **PDF** is `--to engine-beamer`: the engine beamer theme in
  `_extensions/engine/`, edited in place like everything else. Its
  pure-LaTeX side (the starter `talk.tex`, the examples and their variants) builds
  in `latex/` (`make latex`); the engine's tests are `make test`. The extension's Lua filter loads the theme in place
  through `\input@path`, so nothing is copied into deck directories. Needs
  XeLaTeX (TinyTeX or TeX Live) and Quarto >= 1.6 (`quarto-required` in the
  shared `_quarto.yml`; `conda-env.yaml` pins it). Beamer has no autofit: dense slides
  overflow silently, so render the PDF and look at it, then trim the content
  or add `{.shrink}` to the heading. A full-width 16:9 screenshot is taller than
  the frame's content area; cap it with `{height="72%" fig-align="center"}`
  (pptx ignores the attribute and fits the placeholder anyway).
- **HTML** is `--to engine-revealjs`, from the same extension (see
  "revealjs (HTML) theme" below).
- **Theme options** (`themeoptions:` in a deck's front matter) replace the
  shared list in `common/_quarto.yml`, so a deck that sets any must
  repeat `fonts=bundled`. `mathfont=` (default a serif math font,
  NewCM Book scaled to Poppins; `stix`, `lm`, `pagella`, `sans`, `fira`,
  `poppins` for the old Poppins-letter look, `keep`, or a font name; Quarto's
  own `mathfont:` key still wins) and `waves=false` (drops the faint wave
  lines behind content slides in PDF and HTML; pptx has them on the master).
  The waves are fitted to the brand's cover art by `common/utils/fit-waves.py`,
  which prints the livery's `art.waves` block to paste.
- **Format conditionals**: `when-format="beamer"` matches the custom
  `engine-beamer` format; `when-format="engine-beamer"` matches nothing. Always
  write `beamer`.
- **Poppins has no arrows or ⚠**: the theme borrows ⚠ → ← ↔ ⇒ from DejaVu
  Sans in the PDF, so `## ⚠︎ Title` and `A → B` work in every format. Any other
  missing symbol still drops out of the PDF, with a warning in the log.
- **Divider subtitles**: a paragraph right after a `#` divider becomes that
  divider's subtitle in every format: `section_subtitle.py` for pptx, the
  theme's `\sectionsubtitle` (via its Lua filter) for beamer, and
  `engine-revealjs.lua` for HTML. Only plain
  paragraphs qualify; anything else after a divider stays a slide of its own (one rule,
  `engine-common.lua`'s `divider_subtitle()`; `sections()` lists the dividers for every format).
  Sections are counted alike: a `{.unnumbered}` divider has no "SECTION n" and leaves the count
  alone. pptx drops the class, so `grid-pptx.lua` writes the unnumbered ones' places among the
  dividers into the metadata (`engine-unnumbered: 2 4`, `docProps/custom.xml`) for
  `section_subtitle.py`; beamer's `\section*` steps the counter like `\section`, so the filter
  opens a plain frame (an empty-titled slide heading: a raw block between slides lands in the
  slide before) holding the theme's `\enginesectionunnumbered{Title}{Sub}` (no `\section`, no toc
  line, no bookmark; its state global until shipout, where the background draws the stack).
  `section.progress` (default off) reads "SECTION 3 of 5": pptx counts the numbered dividers,
  HTML's filter writes `data-engine-section-total`, beamer's writes `\enginesectiontotal{n}`.
  In pptx the blue field, logo and waves are the template's Section Header
  layout, which `livery template` generates with the rest of the
  template from the livery's data (`make livery` after a livery change, never edit
  `template.pptx` by hand); `section_subtitle.py` adds "SECTION n" (none under
  `section.label: null`), the tab and placement.
- **Front matter must be line 1** of every deck `.qmd`: anything above the
  opening `---` (an editor mode-line, a comment) hides it from Quarto, and
  `date: last-modified` renders literally (#7). CI checks this; set editor
  modes in the editor config, not in the file.
- **Fragments are prerequisites**: every deck in a directory depends on its
  `_*.qmd` fragments, `data/*`, `images/*` and deck-local `*.lua` filters, so editing any of
  them rebuilds all of them, and on the livery's files (`livery.py deps`: `build/`, the
  template, fonts, logos and their `.pdf`s, art, the parent's too), so a livery change
  rebuilds the decks. The `_livery` link is order-only (make stats a link's target, the
  directory, which would look stale forever after a switch); the `.livery` stamp is the
  prerequisite, and holds the livery's directory, so a `LIVERY_DIR` switch under one name rebuilds too. The HTML recipe deletes `<deck>_files/libs/quarto-contrib/engine-revealjs-*`
  before rendering: that dependency is named for the engine version, and quarto keeps a
  copied file newer than its source, so a livery switch kept the old livery's css. A file included from anywhere else (e.g. `../other_deck/_x.qmd`) is invisible
  to make; `touch <deck>.qmd` after editing one.
- **`LIVERY=` on the command line always wins**: `Make.common` exports `LIVERY_DIR`, which
  a sub-make would otherwise keep (`?=`) over its own `LIVERY=cu` (the gallery once stamped
  cu and linked ncar); `override LIVERY_DIR` when `LIVERY` is command-line.
- **Several decks in one directory**: set `DECKS := a b c` before the include;
  each `<name>.qmd` builds `<name>.{pptx,html,pdf}`. They share one `.quarto/`
  cache, so `Make.common` is `.NOTPARALLEL`. `decks/fixtures/` is such a directory:
  `photo` (a `titlegraphic:` title) and `light` (`title=light`) on one `_body.qmd`, in
  CI and in `parity.sh` (which snapshots every deck of `DECKS`, PDF pages included, under
  ncar, cu and nsi).
- **Installed brand fonts**: a livery may name a proprietary face (`installed-fonts`, cu:
  Helvetica Neue) over its bundled stand-in. HTML lists it as `local()` sources in each
  `@font-face`; PDF uses it only under `themeoptions: [fonts=brand]` when the building
  machine has it (the shared `fonts=bundled` never does, so CI and parity are unaffected);
  pptx already names `pptx.typeface`. docs/formats.md "Installed brand fonts".
- Executable ```{bash} cells run at render time via the jupyter `bash` kernel
  (deck frontmatter: `engine: jupyter`, `jupyter: bash`). Keep them
  deterministic — CI renders the sample deck.

## The engine

`_extensions/engine/` is the source, edited in place (no vendoring since #57). What
it does, by area, beyond the format notes above:

- **Names**: the formats `engine-beamer` / `engine-revealjs`, `\usetheme{Engine}`, the
  `engine@` namespace, `\engine*` commands, `engine*` frame keys, `engine-*` classes and
  properties (renamed from NCAR_beamer_template v2.8.0).
- **Finding the livery**: `engine_livery.sty` inputs `<livery>/build/livery.sty`. Both Lua
  filters take the directory from the `livery:` key (this framework: `_livery`), else
  `liveries/<brand>` beside the `_extensions/` that holds the extension, found from the
  extension's real directory (a deck reaches it through a linked `_extensions/`, and Lua does
  not resolve links; changing into the directory does). `_extension.yml`'s default
  `highlight-style` is `../../liveries/ncar/build/livery.theme`, which Quarto resolves
  lexically through the link, so `latex/examples/` links `liveries` beside its
  `_extensions` (the shape of an Overleaf zip). LaTeX finds `livery=liveries/<name>`
  through `TEXINPUTS` (`_extensions/engine//`, `liveries//` and the root
  itself, as an Overleaf zip's `latexmkrc`; never the root's `//`, which reaches `conda-env/`).
  `TTFONTS` needs the root too: the theme looks the bundled fonts up as files,
  `liveries/<name>/fonts/...`, and a miss falls back to an installed face by name silently (the
  image's Poppins then sets bold in SemiBold; a Mac with Poppins installed hides the miss).
- **Roles only**: no palette name is read outside `build/livery.sty`; the Sass sets every color
  as `var(--engine-*)` (its `$engine-<role>` variables hold ncar's values as compile-time
  defaults for Quarto's own rules, restated with the roles at the end of the file); the
  highlight theme is generated per livery from `engine.theme`.
- **Shared Lua**: `engine-common.lua` holds what both format filters read alike (`has_class`, the
  deck's type step, the default livery, the slide-footnote markers, the one-figure test), `dofile`'d
  by each like `engine-plots.lua`; what a format does with the result stays in its filter.
- **Geometry**: margin, tab, logo box (height per slide kind, top, aspect, corner, `inset`), the
  page number's corner, divider block and full-figure lengths are the livery's `geometry`
  fractions: `engine@geom@*` in the `.sty`, `--engine-*` pixels in the css (ncar's are the
  HTML/PDF numbers, not the pptx template's tighter ones).
- **Art**: `art.waves` (control points and per-kind shifts, drawn in the roles' colors; the pptx
  divider layout from the same numbers; `common/utils/fit-waves.py` fits them to a brand's
  cover art), or a static picture per slide kind (`art.title|section|closing|content`).
- **Title styles**: `title.style` `cover` (default) or `band` (a field in a role with
  `art.title` over it, a band holding the text left of `split` and the photo right of it, the
  marks centered in the strip below; nsi). `title=light` follows the brand's own light cover
  (UCAR Communications' template, slide 4).
- **Templates**: `livery_template.py` generates each `template.pptx` with `Closing` and
  `Title Slide (light)` layouts pandoc never picks; the theme1.xml slots follow the roles
  (`SLOT_ROLES`); the web logos are the brand kit's RGB PNGs (see each `reference/notes.md`).
- **LaTeX**: `latex/Makefile` (`default` talk.pdf, `examples`, `variants`, `html`,
  `previews`, `diagrams`, `overleaf`) sets `TEXINPUTS`/`TTFONTS` (above); its
  `latexmkrc` does the same for a bare `latexmk`. `variants` are `examples/template.tex` under
  the `\enginethemeoptions`/`\engineaspectratio` hooks, and `examples/sample.tex` under cu,
  nasa-dark and 4:3.
- **LaTeX authoring** (`latex/authoring.md`): the inner theme's layer is what a hand author
  writes and what the filter writes through, no private macro in a preamble: `enginecolumns{2,1}`
  with `\enginecolumn` (over `\enginecolshare`/`\enginecolrule`, which the filter keeps for
  pandoc's columns), `enginelead`, `enginecards{<shares>}` holding `enginecard[role=,pick,
  pick=<spec>,solid,plain]{Title}{Sub}` (the shares: a count or weights, `\engine@shares`; a
  `role=` resolves through livery.sty's `\engine@role@<name>`, else a defined color, else a
  `Package Engine Warning` and the default by place in `\engine@boxes@card@roles`),
  `enginestrip[role=]`, `enginestatus` with `\done`/`\warn`/`\fail` (local to it) and
  `\engineglyph`, `enginecaution`, `\enginenote`, `enginescale{S}`, `\enginemarking{}`,
  `enginequote[role=]{Attribution}`, `\engineagenda`, `\enginesectionunnumbered{Title}{Sub}`,
  `enginegallery[cols=,rows=,fit=,height=]` with `\engineimage[Caption]{file}` (and the bare
  `[enginefull]` frame key, which a gallery fills). The
  cookbook `latex/examples/sample.tex` is the sample deck slide for slide plus three frames on
  overlays (a moving pick, steps inside cards, a stepped status list); `make variants` builds it
  under cu, nasa-dark and 4:3, `make previews` the committed `latex/sample.png` (`sheet.py`:
  rebuild and commit it when those slides change); CI fails on an Overfull line in `sample.log`
  under every variant. `tests/test_latex.py` compiles a deck on
  the layer; every livery's Overleaf zip carries `sample.tex` with the files it needs
  (`COOKBOOK_FILES`), and CI builds it there; `parity-latex` snapshots the four cookbook PDFs.
- **Checking a change**: `make test` (`livery build --check` and `livery check` on every
  livery, then pytest over `tests/`, `-n auto --dist loadfile`: `test_compositions.py`, whose
  `EXPECTED_DELTAS` names every decided change of a box, `test_schema.py` (the generated
  `REFERENCE.md` current too), `test_docs.py` (every relative link and `#anchor` in the tracked
  `*.md` files resolves, every `README "X"` or `<guide>.md "X"` pointer in a tracked file names a
  heading that exists, `design/` exempt; the consumer example's release pins and the changelog's
  link block), `test_latex.py` (a deck on the theme's LaTeX layer compiled with XeLaTeX: no
  Overfull, a moving pick's pages, the `role=` warning, the share error, and a deck citing with
  biblatex; skipped without TeX), `test_footnotes.py` (engine-common.lua under `pandoc lua` with a
  `quarto` shim: the lift's markers and warnings, `ensure_refs`; the pptx filter and steps; the
  same harness in `test_rail.py`, `test_quote.py`, `test_gallery.py` and
  `test_section_subtitle.py`, which also checks the pptx dividers' numbers),
  and the rest of `tests/test_*.py`, one per pptx step or engine area). pytest's
  discovery is the one list of tests, and CI's latex job runs `make test`. One test:
  `python3 -m pytest tests -k <name>` (serial, plain output). A test writes only under
  `tmp_path`, never the tree, and never changes directory or the environment in-process
  (`tests/conftest.py` has the harness: `ROOT`, `ENGINE`, the per-livery `livery` argument, `run`
  for the livery command, `pandoc_exe`, `lua_common` for engine-common.lua under `pandoc lua`
  with the `quarto` shim, `pandoc_deck`, `tmp_livery`, `flat`); expensive setup is a module-scoped fixture, which
  `loadfile` keeps on one worker. For anything that can move pixels, `tests/parity.sh baseline`
  before and `check` after (every deck of quickstart, sample, fixtures and plots under
  `PARITY_LIVERIES`, default `ncar cu nsi`; under `nasa` and `nasa-dark` the quickstart's
  screenshot step stops it, no PDF page reads "MPAS-A") and `tests/parity-latex.sh
  baseline|check` (latex's PDFs page by page, the demo's HTML), same checkout, same day. A
  Sass change is checked by screenshotting every slide before and after (Playwright).
- **Version**: one calendar version, `YY.MM.N` (Ben, 2026-10-18: the month unpadded, `N` the
  month's release count from 0; the container image also gets `YY.MM`, the month's newest; the
  first release is 26.10.0, and v1.0.0/v1.1.0 were withdrawn), `version:` in `_extension.yml`;
  a `v*` tag must equal it
  (`release.yml` checks). `engine-revealjs.lua` reads it from there and names the HTML dependency
  by it (`engine-revealjs-<version>`), so a bump changes every HTML deck's paths. `livery build`
  stamps it (and the livery's `schema`) into `build/livery.json`, so a bump means `livery build
  liveries/*/` in the same PR (CI's `--check`) and the consumer example's `@v<version>` and
  image tag in docs/other-repos.md (`tests/test_docs.py` holds them to it), and `livery deps`
  warns a deck build when a livery's stamp is another version. **Tags are immutable**: another release in the month is
  the next `N`; `release.yml` refuses a tag whose release exists, that is not `YY.MM.N`, or whose
  month is still to come. `CHANGELOG.md` (Decks, Liveries, Plots,
  LaTeX; Keep a Changelog) gets every user-visible change under `[Unreleased]` in the PR that
  makes it; a release renames that section to `[x.y.z] - date` before its tag, and the entry
  becomes the release's notes. Ask Ben before any tag. Before it, on a Mac with Keynote and
  PowerPoint, build the decks (`make all` in quickstart, sample, fixtures and plots) and run
  `tests/app-open.sh`: it opens each `decks/*/*.pptx` in both apps by their own AppleScript
  (no keystrokes; a refused import or a Repair? prompt is a FAIL), after controls that show its
  verdicts are real. No CI runner has either app (GitHub's macOS images: neither), so it is a
  manual step; it would have caught the notes slides Keynote refused (26.10.5).

## pandoc pptx gotchas (hard-won — read before restructuring slides)

- **Content after a table or image splits the slide** into an untitled
  continuation. `single-body.lua` (the engine-pptx
  format's) moves the paragraphs after one table or image (a † footnote, a
  remark, a `::: note`'s) into its caption, which pandoc draws at the slide's foot;
  `style_footnotes.py` then styles a footnote there, left-aligned. pandoc captions
  a figure from its image's text, not the Figure's caption, so the fold writes both
  (extending only the Figure's caption dropped the text silently). Anything
  else after it (a list, code, a second table) still splits, on purpose. Never
  wrap such a body in a 100% column: pandoc gives the table the whole
  placeholder and silently drops the text after it (the slide count doesn't
  change, so `make qa` can't see it). Content *after* `.columns` still splits,
  so put it inside the last column. Code blocks are text and never split.
- **Columns: two tiers.** pandoc keeps the first two `.column`s of a pptx slide and drops the
  rest, silently. Columns take their `width=` shares of the content box less `boxes.columns.gap`
  in every format. A *plain* slide (two columns, no card or lead) stays pandoc's Two Content:
  `grid-pptx.lua` writes the shares on a notes line (`engine-columns: 0.55 0.45`) and `columns.py`
  frames the placeholders, moving a column's picture or table with them. Never a marker paragraph
  there: beside a picture or table it demotes the slide. A *grid* slide (what `is_grid()` counts,
  the one list above it: more than two columns, a `.card`, a `.lead`, a `.strip`, a rail, a
  `.gallery`, a quote) is flattened on purpose into one
  placeholder with marker paragraphs (`⟦engine:columns widths=...⟧`, `⟦engine:column⟧`,
  `⟦engine:end⟧`), which `grid.py` redraws as text boxes carrying the master's body list style
  and deletes. First-cut limit: a
  picture or table in a grid column is not drawn in it (`grid-pptx.lua` warns; pandoc splits the
  slide, which `make qa`'s count catches). Text after a picture in a pandoc column is dropped by
  pandoc, silently, in either tier.
- **Cards and boxes** (`::: {.lead}`, `::: {.column .card role= .pick .solid}` with `###`,
  `[..]{.sub}`, `[..]{.label}`, `[..]{.big}`, `::: {.strip role=}`, status items `- [x]`/`[!]`/`[-]`
  in a card or `::: {.status}`): `engine-common.lua` reads them once (`card_attrs()`,
  `split_lines()`: in a lead or card a source line is a line, `status_lists()`), and every
  number is `livery.json` `boxes` (`livery.yml` `boxes:`, merged box by box over `BOXES`). pptx:
  a grid slide; `grid-pptx.lua` writes `⟦engine:lead⟧`, `⟦engine:column card role=... pick
  solid⟧`, `⟦engine:strip role=...⟧` (each closed by `⟦engine:end⟧`) and prefix markers
  `⟦engine:title⟧`/`sub`/`label`/`big`; `grid.py` draws native shapes ("Card n fill", "Card n head",
  "Lead fill", "Card n strip k"...), one group per card, lead or strip ("Card n", "Lead", "Strip": a
  click selects it whole; tests look inside groups), under text boxes whose `lstStyle` is the master's body style
  (bullets and sizes as the placeholder's), each head its own height, a row's cards one height;
  `status_glyphs.py` makes a glyph the bullet (`a:buChar`). HTML: raw tags (a Div opening with a
  heading would become a `<section>`), the role a custom property (`role` is ARIA's attribute).
  PDF: `\engine@barbox` (caution, lead, strip), tcolorbox cards set in one run (bodies boxed
  first, the feature panel's pattern), a status list beamer's itemize with `\item[✓]`. PDF frames
  are top-aligned (`t`, without beamer's 0.2 cm; a paragraph-first body cancels its `\parskip`).
- **Steps and timelines, the rail** (`::: {.steps role=}` round an ordered list, `::: {.timeline}`
  round a bullet list, `- [x]` a done milestone; at most six items, text only, at a slide's top
  level: `top_rails()` warns of one in a column and leaves its list):
  `engine-common.lua`'s `rail_kind()`/`rail_items()` read them once (an item's first bold run its
  title or date, the rest its text, split_lines()), each filter's `rails()` first in its chain (a
  literal ✓ in a milestone is its status), every number `boxes.rail` (`line`, `line-color`, the
  `rule` blend by default, `badge`, `dot`, a nullable `fill`, `pad`). The marks default to
  `primary-contrast` (a dark livery's primary vanishes on its background) and a badge's number is
  knocked out in the background color, so a visible mark has a readable number. HTML: a grid whose
  items are `display: contents`, so a row's parts line up. pptx: a grid slide, `⟦engine:rail
  kind=steps role=...⟧`, `⟦engine:item⟧`/`⟦engine:item done⟧` ... `⟦engine:end⟧`; `grid.py`'s
  `draw_rail()` draws an `MSO_SHAPE.OVAL` badge with its own text frame (Keynote and PowerPoint
  open it) or dot, a rail rectangle and `body_box` texts, one group ("Steps", "Timeline"). PDF:
  `enginesteps`/`enginestep`, `enginetimeline`/`\enginemilestone[done]` on the cards' six save
  boxes, drawn by one tikzpicture at `\end`.
- **Galleries** (`::: {.gallery cols= rows= fit=contain|cover height=}` of image paragraphs; at most
  twelve, file images only, at a slide's top level): `engine-common.lua`'s `gallery_items()` reads
  one (cols `ceil(sqrt(n))` and rows `ceil(n/cols)` by default, a caption from a Figure or the alt
  text, several images on consecutive lines an item each; a src under `figure-*/` or `*_files/`,
  an executed cell's plot or a baked diagram, is refused: pptx reads the files from disk after the
  render, where those are not), `top_galleries()` the one walk, `is_grid()` counts it,
  `split_full()` takes it as a `.full` slide's figure; every number `boxes.gallery` (`gap` of the
  width, `pad`, a nullable `fill`). HTML: `galleries()` after `rails()` wraps a gallery slide's
  body in `.engine-gallery-body`, the body box in slide pixels (`--engine-body-top` to
  `--engine-body-bottom`, which also sets the slide's foot padding), a flex column, so text above
  takes its height and the grid the rest; the `<img>` is pandoc's (embed-resources inlines it).
  pptx: a grid slide, `⟦engine:gallery cols= rows= fit=[ height=][ full]⟧`, per image
  `⟦engine:item src=<path, white space, = and ⟦⟧ percent-encoded>⟧`, its caption, `⟦engine:end⟧`;
  `pptx_steps/gallery.py` reads the files from the deck's directory (`grid.run(prs, path)`), an
  .svg through `svg_fallback.rasterize_svg()`, and places each with `common.fit_picture()`
  (`contain_box()`, `cover_crop()`: an `a:srcRect`), one group ("Gallery"). pandoc's pptx writer
  draws no picture held in a Div, so a refused gallery or one in a column is unwrapped into its
  paragraphs (on the slide itself pandoc splits the slide, which `make qa`'s count catches; in a
  column it keeps the first picture and drops the rest silently, so only the warning tells). PDF: `enginegallery` stores
  its images and draws the cells at `\end` in one tikzpicture, at `height=` of the body box capped
  at `\engine@bodyroom` (beamer sets `\beamer@frametextheight` only after the body; a fragile
  frame reads 0); `engine-beamer.lua` writes it before `bound_sized_images()`.
- **Quotes** (`::: {.quote role=}` or a bare `>`, anywhere in a slide's body but the notes, a lead
  or a strip, where it warns and stays its lines): `engine-common.lua`'s `quote_parts()` (a last
  line led by —, – or -- the attribution) and `quote_blocks()`, the one walk every format uses;
  `boxes.quote` (`bar`, `bar-color` primary-contrast by default, `pad`, `family`: a bundled
  `typography.fonts` family or null, `style`) and the `quote` type role; `pptx.quote-typeface`
  names PowerPoint's face. pptx: `⟦engine:quote role=⟧` ... `⟦engine:attribution⟧` ...
  `⟦engine:end⟧` in a `.engine-quote-marks` Div; a quote in a column makes a grid slide
  (`is_grid()`, unless a column holds a picture or table: pandoc's slide and blockquote then, warned);
  `grid.py`'s `draw_quote()` (group "Quote"; in a card inside its pads, in a plain
  column between its text boxes, `_plain_column()`/`_place()`). HTML: `.engine-quote`, the pads on
  the box, the sizes on its paragraphs. PDF: `enginequote` on `\engine@barbox` with an empty fill,
  the theme's own `engine quote` font (beamer's `quote` untouched: a hand `quote` environment).
- **Agenda** (`## Agenda {.agenda}`, an empty body; by position, no `current=`):
  `engine-common.lua`'s `agenda_rows()` over `sections()` (the numbered ones; done, current,
  next by the section the slide sits in), `agenda_notes()` (notes kept, a body warned and
  dropped); `boxes.agenda` (`number-color`, `current-color`, both primary-contrast: text on the
  content background). HTML: an `<ol class="engine-agenda">` grid. pptx: `⟦engine:agenda
  current=n⟧`, `⟦engine:item n=k state=..⟧` with `title`/`sub` prefixes; `grid.py`'s
  `draw_agenda()` (group "Agenda": a number box beside a text box per row, subtitles dropped
  past the room). PDF: `\engineagenda`, beamer's table of contents at tocdepth 1 in a `\vbox`
  (`hideallsubsections` would add 1.5em a row) through the theme's `section in toc` templates
  (a plain `\tableofcontents` draws the same rows, none current); a clean Quarto build reruns for
  the `.toc`; `\AtBeginSection` copies each subtitle's text to the aux file for an agenda before it.
- **Speaker notes can go anywhere.** Pandoc only picks Two Content when the
  body *starts* with the columns div, so notes written before columns split the
  slide; `notes-last.lua` (engine-pptx) moves
  every slide's notes to its end. Notes after an image or table do not split.
- **Keynote refuses a notes slide without `<p:clrMapOvr>`** ("The file format is invalid",
  for the whole deck), which pandoc never writes; PowerPoint and Google Slides don't mind.
  `notes_clrmap.py` adds PowerPoint's own. pandoc's notes placeholders also name indexes its
  notes master lacks (0, 1, 10 for 2, 3, 5): harmless, Keynote included.
- **Raw-HTML `<figure>` wrappers demote columns slides to the Comparison
  layout**: quarto wraps rendered diagrams in `` `<figure>`{=html} `` inlines,
  pandoc's layout chooser counts them as text, and the other column's text gets
  stuffed into Comparison's tiny per-column heading box.
  `strip-raw-figure.lua` (an engine-pptx
  filter) strips them; don't remove it.
- **A lead paragraph before a table demotes the slide** to Content with
  Caption: the title moves into a small side caption and the title bar stays
  empty. Put the lead in the slide title (or the notes) and start the body
  with the table. Text followed by an image lands in Two Content the same
  way, so a wide chart shrinks to half width; bake a chart's footnote into the
  PNG instead.
- **Diagnosing layout problems**: `unzip -p deck.pptx
  ppt/slides/_rels/slideN.xml.rels` — in a generated template, layout2 = Title and
  Content, 4 = Two Content, 5 = Comparison (the `LAYOUTS` order in `livery_template.py`). Hunt for orphan slides by
  extracting each slide's title and looking for "(no title)".
- **"Why is my line spacing 0.8?"**: `enable_autofit.py` turns on PowerPoint's
  shrink-on-overflow; when a box overflows, PowerPoint squeezes line spacing to
  its 0.8 floor on recompute. The master's body sizes (ncar 12/11/10/9/8 pt on its
  10 x 5.625 in, cu 16/14/13/12/11 on 13.33 x 7.5) are the livery's type (`livery.json` `type`, which HTML and beamer follow as
  fractions of the slide height), chosen so the three formats fit
  alike and autofit rarely fires — don't bump them back up.
- Template edits must stay pandoc-compliant (layout names, the five
  `slideLayout1` placeholders) — see docs/formats.md "Template constraints" and its
  verification one-liner.
- **Extra layouts ride along**: pandoc copies every layout of the reference doc into
  the deck but picks only by its seven names (two layouts of one name: pandoc 3.8.3
  took the later, undocumented). So the template's `Closing` and `Title Slide (light)`
  are reached by `slide_layout.py`, which re-points the slide's layout relationship
  and deletes the placeholders' `a:xfrm` (pandoc copies the old layout's frames onto
  the slide). python-pptx caches `target_part` on the relationship: drop it too, or
  `slide.slide_layout` still answers with the old layout. `title=light` reaches the
  pptx as `engine-title: light` (slide-layout.lua): pandoc writes list metadata into
  `docProps/custom.xml` as empty strings.

## revealjs (HTML) theme

Lives in the engine extension (`engine-revealjs.{scss,css,js,lua}`,
`title-slide.html`), beside the beamer theme. Things that
bit while building it:

- **The slide is 1600x900 slide pixels** (`width`/`height`, `margin: 0`);
  every length in the scss is in those units and reveal scales the whole
  slide. The waves are inline SVG in slide pixels, drawn by the Lua filter.
- **`url()`s go in the livery's generated `build/livery.css`, never the scss.** The
  scss compiles into `libs/revealjs/dist/theme/`, where relative URLs break; the
  livery's css is an HTML dependency whose resources (its fonts and logos) are
  copied beside it and inlined under `embed-resources`. Web logos are
  separate RGB files: the PDF lockups are CMYK and convert off-color.
- **`hash-type: number` strips `#title-slide`**: target `.engine-title`.
- **`?print-pdf` moves slides into `.pdf-page` and forces `padding: 0
  !important`**: use descendant selectors (`section.slide`, not
  `.slides > section`), restate padding under `html.reveal-print`, and keep
  `isolation: isolate` so the `z-index:-1` waves stay above the background.
- **A pandoc `Div` whose first block is a heading becomes a `<section>`**,
  which reveal counts as an extra slide (wrong numbering, a vanished slide).
  Wrap slide content in raw `<div>` tags from the filter instead.
- **pandoc's embed-resources inlines `<img src>`, not SVG `<image href>`**:
  the title photo is an `<img>` behind the wave SVG.
- **Mermaid pins its SVG to its natural width** (tiny labels); the scss
  lets it fill the column, capped by `calc(600px * var(--engine-fit))`. The
  autofit script (`engine-revealjs.js`) sets `--engine-fit` when it shrinks a
  slide; `em` does not work there (mermaid sets `font-size: 16px`). Graphviz
  SVGs get the same cap.
- **Mermaid must render unscaled.** Quarto renders each diagram inside its
  slide, which reveal has scaled to the window, and mermaid measured labels at
  that scale (0.8 at 1280 px): boxes 20% small, labels clipped. The theme's
  script renders in mermaid's own scratch element instead.
- **A percentage image height resolves against the whole slide**, so the
  beamer screenshot recipe `{height="72%"}` overflowed; the theme's Lua filter
  maps it onto the content height (2.2.0): 72% is the full cap, a smaller
  percentage is proportionally smaller.
- **`chalkboard` blocks `embed-resources`**, and `-M chalkboard:false` does
  not override a format option; set it in the deck's `format:` block.
- **`make qa` first** (docs/authoring.md "Checking a deck"): it does the screenshots,
  overflow and slide-count checks below. Load the `deck-polish` skill for a
  format pass, `pr-review` to review a PR by number (`/pr-review N`), and
  `unplanned-city-sweep` after a run of merges or for one area of the tree (its ledger is
  `design/unplanned-city-ledger.md`).
- **Check it in a browser, not the source**: serve the deck directory
  (`python3 -m http.server`; Playwright blocks `file://`) and screenshot each
  slide type, at 16:9 and a letterboxed size, plus `?print-pdf`. Run
  `Reveal.configure({transition: 'none'})` first or shots catch a fade, and walk
  `Reveal.getSlides()` with `Reveal.getIndices()`: the `##` slides nest
  vertically under their `#` divider, so `Reveal.slide(n)` stays on the divider.

## Mermaid diagrams

- ```{mermaid} blocks render to PNG at build time through a headless browser
  (pptx and PDF; the HTML deck draws them live, in brand colors and Poppins);
  size with `%%| fig-width` (≈10 full-bleed, ≈5 in a column). Labels render in
  Trebuchet MS (mermaid's default theme font), not Poppins — diagrams are baked
  images, outside the template's font machinery.
- **Install Chrome Headless Shell once** (`quarto install chrome-headless-shell`).
  With only the system Chrome, quarto's handshake can wedge and a render hangs
  with no output (CI hit it; so did a local `make all`, for 29 minutes). In the
  container `QUARTO_CHROMIUM` already points at Playwright's headless shell.
- Layout tricks that work: subgraphs with `direction TB` + invisible `~~~`
  links to stack wide fan-outs vertically; an invisible `~~~` edge plus the
  real edge to force a child *below* its parent while the arrow points up.
  Avoid self-loops (sprawling arc, detached label) and `<br/>` in subgraph
  titles (clipped — a long title truncates mid-word rather than wrapping).
  Reversed arrow syntax (`A <-. l .- B`) silently renders the head on the
  wrong end — don't use it.
- **Subgraphs constrain layout hard; for multi-lane flows prefer node classes.**
  A subgraph's contents are kept contiguous, so two zones with edges between
  them land diagonally (wasting a quadrant) and the connecting edges cross —
  and a crossing edge that passes *behind* a node reads as an edge that does
  not exist. `direction` inside a subgraph is silently **ignored** whenever an
  edge crosses the subgraph boundary, which is exactly when you want it. Moving
  nodes between/inside the subgraphs does not help. If parallel lanes must stay
  readable, drop the boxes and mark the grouping with `classDef` fills plus a
  prefix in the node label (`CSG · …`, `HSG · …`); plain rank ordering then
  guarantees no crossings. The worked example was the "SAM to PBS Schematic" of the
  `sam_and_pbs` deck (in this repo's history before the flatten; it now belongs with
  hpc-scheduling-tools) — it took four renders to learn this.
- **Look at the rendered PNG, not the source.** Every mermaid failure above is
  silent: no warning, no error, just a diagram that is wrong or unreadable.
  Extract it from the deck and view it:
  `unzip -p deck.pptx ppt/slides/_rels/slideN.xml.rels` for the media id, then
  pull `ppt/media/imageM.png`. Check the aspect ratio too — a 16:9 content area
  is ≈2.4:1, so a much wider diagram scales down until the labels are unusable.
  The same goes for tall ones: a hub with five outputs as `flowchart LR` came
  out 1.4:1 with its right and bottom labels clipped (the renderer mis-measures
  wrapped `<br/>` lines). As `flowchart TB` with one short line per label, it
  was 2.7:1 and clean.

## Graphviz diagrams

- ```{dot} cells render like mermaid (a PNG in pptx and PDF, live in revealjs) through
  Quarto's bundled Graphviz (WASM): nothing to install. Size them with `//| fig-width`.
- Use Graphviz where mermaid's layout fails: its clusters really cluster, and `rankdir`,
  `rank=same` and compass ports (`node:port:e`) steer the routing. Keep mermaid for
  simple flows and sequence diagrams.
- **Set `fontname` on `graph`, `node` and `edge`** ("Helvetica" renders as the WASM
  sans). Unset, it falls back to Times, so cluster labels come out serif. The WASM
  build cannot load Poppins.
- HTML-like labels (tables, ER boxes) have two silent traps:
  - an empty `<font></font>` makes Graphviz drop the whole label to plain text; emit an
    empty `<td></td>` instead;
  - a colon in a `port` name reads as `port:compass`, so name ports `col__out`, not
    `col:out`.
- As with mermaid: look at the rendered image, and keep it near 2.4:1.

## CI

One workflow, `.github/workflows/ci.yaml`, on pushes to main, `v*` tags and PRs. Its `image`
job calls `image.yaml` (reusable): the image is built natively on `ubuntu-24.04` and
`ubuntu-24.04-arm` (no QEMU), each leg smoke-tested on its host as the runner's own
unprivileged user (`.github/scripts/smoke-test.sh`: a bare directory of `.qmd` files with a
mermaid block, then `decks/quickstart` through its real Makefile, both bind-mounted, outputs
owned by that user), pushed by digest, merged into one tagged manifest list (`main`,
`sha-`, `pr-N`; `YY.MM.N`, `YY.MM` and `latest`, the newest release, on a tag) and pulled again on both platforms. Build cache: a registry
cache, `ghcr.io/<repo>:buildcache-<arch>`. The merge job's step summary carries the per-platform
size (`render_build_summary.py`, from sam-queries). The deck jobs then run INSIDE that image at
its digest (`container:`, as root, GitHub's default `bash -eo pipefail`; the entrypoint is
bypassed, which is why the activation is `ENV`): `sample` (front matter on line 1,
`livery build --check`, the sample deck in every format with its theme greps and its notes and
captions check, the sample's `make qa`, quickstart and fixtures `all` with every notes slide's
`clrMapOvr` checked, the plots deck's `qa` with its SVG, pptx-media and `pdffonts` greps), `consumer` (the submodule layout, `docs/other-repos.md`, plus `make site`), `reusable`
(`build-decks.yaml` on the quickstart), `latex` (the engine's `tests/`, then `latex`'s starter, examples,
variants and the demo's HTML, with the Poppins and math-font `pdffonts` checks), and `livery`,
one per directory under `liveries/` (a new
livery joins by existing): `livery check --qa` (the engine's checks, then
`make -C decks/quickstart qa LIVERY=<name>`: all three formats and `deck_qa.py`), the
livery-applied greps, the Overleaf zip compiled in a clean directory with TeX's paths unset and
`pdffonts` showing its bundled family, the charts bundle unpacked and tried, and `make measure`
report-only (`MEASURE_FAIL=`). A
fork's PR has no `packages: write`: its image is built and smoke-tested, nothing is pushed, and
the deck jobs are skipped. Nothing installs conda, TeX, Chrome or LibreOffice on a runner any
more; a tool the decks need goes into the Dockerfile. `runtimes` (`runtimes.yaml`, reusable, also weekly and on
demand against `:latest`, the newest release) runs the image as HPC users do, pulled anonymously and doing nothing
special for them: Apptainer in unprivileged user-namespace mode (no setuid) on both
architectures, from the PPA or else the release .deb (the runner's userns sysctl is never
weakened), and rootless Podman on amd64, each through `smoke-test.sh` with `RUNTIME=apptainer`
(`$1` a SIF) or `RUNTIME=podman`; Apptainer then runs `apptainer-extra.sh`, every form
`--cleanenv` (the native cd-and-run form from a scratch directory outside HOME, `exec`,
`--containall`, the read-only image) and its "lived-in HOME" table in the step summary (a host
matplotlib cache, host Jupyter kernels, `pip --user` packages, a module's `PYTHONPATH` and
`TEXINPUTS`, a profile's `TMPDIR` and `LC_ALL`, one per row): a `gate` row fails the job, a new row starts `report` until it is fixed. Not a required
check. The package must be public on ghcr for
anonymous pulls (a first push makes it private). `cron-clean-action-log.yaml` prunes old runs
and untagged image versions monthly with the workflow's own token; `release.yml` refuses a tag
that is not `v` + `_extension.yml`'s `version:`, one whose release exists, or one without a
`CHANGELOG.md` entry, then attaches the Overleaf zips and charts bundles with the entry and the
image tags as its notes.

## Git

- Standalone repo (often checked out nested inside `hpc-scheduling-tools/docs/`,
  which git-ignores it). Default branch `main`, protected since 2026-10-18: PRs only (no
  approval needed), linear history, required checks (the image's manifest merge, the LaTeX and
  engine tests, the consumer and sample jobs, every `Check livery <name>`: a new or renamed
  livery means updating the list), no force push; the owner can bypass. PRs land as **squash**
  merges (the only method enabled; title and body from the PR) and the branch is deleted. The
  engine's imported history stays reachable through #57's merge commit. A stacked PR: retarget
  the child to `main` before merging its parent, then `git rebase --onto origin/main <old parent
  tip> <child>` and force-push it, so its PR holds only its own commits.
- `upstream` is `quarto-docs-framework`. The engine's old repo and `NCAR_beamer_template` are
  not remotes here; a fix wanted from the NCAR theme is ported by hand.
- Generated outputs (`*.pptx`, `~$*` lock files, `*_files/`) stay untracked.
