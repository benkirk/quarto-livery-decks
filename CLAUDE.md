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
`ucp`, `ncarucar`, `cu`, `nsi`, `nasa`, `nasa-dark`), built by the engine's `livery_build.py`
into `build/livery.{json,sty,css,theme}` (an unknown `livery.yml` key is warned about).
`design/engine-and-liveries.md` is the roadmap; its section 10 logs progress and names the
next step (#57 Phase B: the pptx format moves into the engine; then #58, the customer surface).

The engine also holds the json reader (`livery.py`), the template builder
(`livery_template.py`), the wave shapes (`pptx_waves.py`) and the livery checks
(`livery_check.py`): `utils/livery.py` is a shim that loads the engine's reader by path (both
are named `livery`; `engine_module()` loads any engine module the same way) and adds
`livery.py deps <dir>`, and `utils/livery_check.py` wraps the engine's checks and adds `--qa`.
Onboarding a brand from a reference PowerPoint (design section 6):
`utils/livery_inspect.py` writes a livery's `reference/report.md` from the deck, the engine's
`livery_template.py` builds its `template.pptx` from the data, and the decisions go in
`reference/notes.md`. `nsi` (the CU Center for National Security Initiatives) is `cu`'s
flavor (`extends: cu`) on the band title style (`title: {style: band}`); `nasa` (NASA general,
external communication; no official template, so the Brand Center's rules and NASA Science's
public-engagement deck) and its flavor `nasa-dark` (content on black) are the first dark
livery (see "Dark liveries" below). The reference decks themselves live on Drive or a laptop,
not in git. A livery without `pptx.fonts` embeds nothing (`embed_fonts.py` says so and leaves
the deck alone); a livery without `art.waves` gets straight-edged title fields in every format.

`latex/` is the engine's pure-LaTeX side (the starter `talk.tex`, a link to the
extension's copy; `examples/` and their variants; `make latex`), and `tests/` holds the
engine's tests (`make test`) and both parity harnesses ("The engine" below).

Decks live under `decks/<deck>/` as a `.qmd` plus a 1-line Makefile
(`include ../../Make.common`). The shared machinery sits at the top since the flatten
(2026-10-18): `Make.common`, the engine in `_extensions/engine/`, the liveries (each with its
`template.pptx`) in `liveries/`, and `common/` (`_quarto.yml`, the Lua filters, the
post-render utilities); `latex/`, `design/` and `tests/` beside them. No `_quarto.yml` at the
root: each deck is its own Quarto project through its linked one.
`decks/quickstart/quickstart.qmd` is the short exemplar to copy for new decks;
`decks/sample/sample.qmd` is the cookbook of every pattern. The README covers
layout, template constraints, and font embedding.

- **README images** are `decks/quickstart/screenshots/*.png`, committed. After
  editing the quickstart deck run `make screenshots` there, look at them, and
  commit them. Slides are found by title (`SLIDES` in `screenshots.py`), so a
  renamed slide needs that list updated. `make gallery` (`gallery.py`) writes
  `liveries.png`, the deck under every livery (title, divider, content, closing),
  rebuilding the HTML per `LIVERY`; `screenshots.py` leaves that file alone. Where the MathJax CDN is blocked, set
  `MATHJAX` to a local MathJax 2.7 (the npm tarball from registry.npmjs.org),
  or the equations shoot as raw TeX.

Other repos can take the framework as a submodule and keep their decks in their
own tree (README "Using the framework from another repo"); the deck Makefile
includes `../framework/Make.common`. So nothing may assume a deck sits in
`decks/<deck>/`: the shared `_quarto.yml` reaches `common/` as `_engine/`, a link
Make creates in each deck directory. `ci.yaml`'s `consumer` job builds a deck that way,
and the image's smoke test a bare directory with no Makefile at all (`make -f
<framework>/Make.common DECKS=...`, which the entrypoint supplies).

## Environment & build

- **Env**: `source etc/config_env.sh` (or `conda activate ./conda-env`; build it
  with `make conda-env`). Quarto **requires real conda activation** — the
  `activate.d` scripts export `QUARTO_DENO`, `QUARTO_PANDOC`, etc.; merely
  putting `conda-env/bin` on `PATH` fails with a missing-deno error.
- **Container**: `ghcr.io/benkirk/quarto-livery-decks` (root `Dockerfile`; `make image` builds it
  locally, `.github/workflows/image.yaml` publishes it for amd64 and arm64, README "Building in the
  container") carries the conda env, apt TeX Live, LibreOffice, a broad font set and ONE Playwright
  headless Chromium that both Quarto (`QUARTO_CHROMIUM`) and `make qa` (`CHROME`) use, at
  `/opt/pw-browsers/headless_shell`; the framework is at `/opt/quarto-livery-decks`. The activation
  is baked as Dockerfile `ENV` and asserted against conda-forge's `activate.d/quarto.sh` at build
  time, so `docker run`, any `--user` and GitHub `container:` jobs (which bypass the entrypoint) see
  the same environment. `etc/entrypoint.sh` only gives an arbitrary uid a writable HOME and turns
  `make` in a Makefile-less directory into `make -f /opt/quarto-livery-decks/Make.common
  DECKS=<its qmds>`. `/opt/fonts`, an empty mount point for a host's licensed fonts
  (`-v "$PWD/fonts:/opt/fonts:ro"`), and the image's liveries' `fonts/` are linked under
  `/usr/local/share/fonts`, so LibreOffice renders a pptx with its real faces when `make measure`
  shoots it (a livery mounted from the host is not covered). Two fontconfigs live in the image:
  the conda env's (`fc-cache`/`fc-list` on PATH, its own `fonts.conf`) and the system's
  (`/usr/bin/fc-*`, `/etc/fonts`), which the apt XeLaTeX, Chromium and LibreOffice use; a file in
  `/etc/fonts/conf.d` reaches only the second, a directory under `/usr/local/share/fonts` both.
  Everything under `/opt` must stay world-readable (asserted). The three
  `_quarto.yml`/`_extensions`/`_engine` links are `ln -sfn`, so a dangling link left by the other
  side (host or container) is re-pointed; a real file or a resolving link is never touched.
- **Build**: `make pptx` (also `html`, `pdf`) inside the deck directory.
  `Make.common` names the output after the directory (`OUT`) and auto-symlinks
  `_quarto.yml` and `_extensions`. The pptx recipe post-processes with
  `section_subtitle.py`, `enable_autofit.py`, `embed_fonts.py`,
  `style_footnotes.py`, `link_captions.py`, `slide_layout.py`,
  `style_tables.py` (tables drawn as in the HTML theme), and `type_step.py` (a deck's
  `type-body:`/`type-scale:`). pandoc gets `-M monofont=<family>` when the livery bundles a
  code face (`typography.monospace`, `livery.py mono`), and the pptx format takes the
  livery's highlight theme (`_livery/build/livery.theme`) like HTML and PDF.
- **Publishing**: `make site` gathers the HTML decks into `_site/` (one shared
  `libs/`, `images/`, `SITE_EXTRA` directories, an index from `site_index.py` in
  the livery's colors with its fonts copied to `fonts/`;
  `SITE_NOINDEX=1` marks every page noindex) and `make publish` force-pushes it
  as the one commit on `PUBLISH_BRANCH` (gh-pages) under `PUBLISH_PREFIX`.
  README "Publishing the HTML decks".
- **Overleaf**: `make overleaf LIVERY=<name>` (any deck directory; `LIVERY_DIR=` for a consumer's
  own livery) writes `<name>-overleaf.zip` with the engine's `overleaf_zip.py`: the theme's `.sty`,
  the livery's `build/livery.sty`, fonts, logos and art (a flavor's parent files beside it), a
  `latexmkrc` and a starter on `livery=liveries/<name>, fonts=bundled`; it compiles with
  `latexmk -xelatex talk.tex` alone. `release.yml` attaches one per livery to a GitHub Release
  on a `v*` tag (cut by hand, asked first: the README's Overleaf links serve `releases/latest`).
- **Slide footnotes** (a paragraph starting with `†`, or `‡` for a second): the
  theme lifts every one on a slide, columns included, to the slide's
  foot in HTML and PDF, under a short muted rule with the marker in the accent
  orange; pptx can't move content, so `style_footnotes.py` mutes them in place
  in the same colors. `*† text*` works too.
- **Linked images** (`[![](x.png)](url)`): the picture is the link in every
  format, and each shows the URL: the HTML footer and a PDF foot line come from
  `common/linked-images.lua`, the pptx caption box from `link_captions.py`
  (after pandoc, because anything after an image splits a pptx slide). A deck
  should not hand-roll footers for this. README "Linked images".
- **Short slides** (`{.hcenter}`, `{.vcenter}`, `{.center}`, `scale="S"`,
  `{.fill}`, each independent): the theme centers and scales the
  body in HTML and PDF. pptx drops slide classes, so `common/slide-layout.lua`
  writes them as a notes line, `engine-layout: vcenter scale=1.4`, which
  `slide_layout.py` applies and deletes; it can't do `hcenter` or `fill`, and
  centers a table by an estimated height. `.center` is the theme's, not
  Quarto's (which moves the title). README "Centering and scaling a short slide".
- **Warning slides** (`{.caution}`): the body on a soft yellow
  field with a brand-yellow bar; footnotes stay below it in HTML and PDF. pptx:
  `slide_layout.py` fills the body text box, adds the bar, and cuts the box to an
  estimate of its text (pandoc gives it the whole content area). Set all four of
  a placeholder's left/top/width/height together: it inherits its frame, and
  setting one leaves the others at 0 (the text vanishes).
- **Full-slide figures** (`{.full}`): one diagram or image fills
  the slide, the paragraph after it is a one-line caption. HTML and PDF are the
  theme's (PDF frame key `ncarfull=`). pptx: `slide-layout.lua` writes
  `engine-layout: full`, and `slide_layout.py` sets the slide's `showMasterSp="0"`
  (hiding the master's logo, tab, rule and waves), deletes the title, fits the
  one picture to the slide and centers pandoc's caption box under it. Any other
  body is left alone with a warning. `make qa` fails a caption that wraps.
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
  shapes, so a pptx cover redraws its field, waves and marks on the slide. **`make measure`**
  (`comp_measure.py`; `MEASURE_FAIL` the formats whose deltas fail, CI report-only) shoots the
  four slides in every format and measures them against the boxes: `_qa/measure.tsv` and the
  contact sheet `_qa/compositions-<livery>.png`; `design/compositions-baseline.md` is the
  before-picture. The pptx can't flow a stack: `band_stack()` centres a band's date, title,
  rule and subtitle on the column from estimates of their text (the rule moves onto the slide),
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
  (beamer `typescale=`, HTML `--engine-type-scale`; pptx `type_step.py`, last in the recipe,
  reads it from `docProps/custom.xml`); `decks/fixtures/small.qmd` is `type-body: 10`.
- **Dark liveries**: `livery.json` `mode` is `dark` when the background is
  darker than the foreground (nasa-dark). The `code-text` role (default: `dark`) colors code,
  since a dark livery's `dark` stays a field color; beamer mixes its tints toward
  `BrandBackground`, not white; `livery.css` gains callout title tints and a lightness flip
  (CSS filter) for inline Graphviz. Quarto bakes mermaid and dot cells to PNG before any Lua
  filter runs (even `at: pre-ast`), so `common/diagram-dark.lua` swaps each baked picture for
  a copy from `utils/diagram_dark.py` (HLS lightness flipped, hues kept, white to the
  background, black to the foreground): Image elements in pptx, and in beamer the raw LaTeX
  and the `enginefull=` frame option the engine filter already wrote. HTML mermaid is live in
  the roles. A light livery is untouched. The pptx theme slots follow the roles, so `dk1`
  holds white (a native `clrMap` swap is a follow-up).
- **Content title**: `livery.yml` `frametitle: {align: left|center, tab, rule}`
  (nsi: centred, no tab, no hairline, as the NSI master deck's slide 20; its mark at the paper's
  edge, `geometry.logo.inset: 0.015`); the body starts below
  a mark taller than ncar's (`livery.json` `frametitle.body`). Beamer centres the title in the
  same band as HTML and pptx (it sat higher before).
- **Code face**: `typography.monospace` (brand.yml) with files of its own replaces LM Mono in
  beamer (at 1.0: a mono advancing 0.6 em is HTML's width), `--r-code-font` in HTML and
  pandoc's `monofont` in pptx (nasa: DM Mono). The other liveries keep the defaults.
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
  theme's tint ladders; nasa: NASA's Horizon Design System). `livery_check.py` prints the checks
  (a generated palette must pass, a published one only warns), and `--swatch DIR` draws a
  contact sheet; `tests/test_charts.py`. No format draws them yet.
- **Marks and numbers** are livery parameters (`signoff`, `geometry.logo.corner`,
  `geometry.pagenumber.corner`; defaults are NCAR's layout) that the three themes
  and `livery_template.py` all honor. Which mark and sign-off a field wears goes by
  its role (`marks:`; `livery.json` always has `marks`, read with
  `livery.mark(livery, role, "logo"|"signoff")`): content slides `background`,
  dividers, covers and the cover closing `primary`, the band title and closing
  `title.field`. Defaults: background `logo.medium.light`/`signoff.light`, primary the
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
  paragraphs qualify; anything else after a divider stays a slide of its own.
  In pptx the blue field, logo and waves are the template's Section Header
  layout, which the engine's `livery_template.py` generates with the rest of the
  template from the livery's data (rerun it after a livery change, never edit
  `template.pptx` by hand); `section_subtitle.py` adds "SECTION n", the tab and
  placement.
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
  pptx already names `pptx.typeface`. README "Installed brand fonts".
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
  `_extensions` (the shape of an Overleaf zip). LaTeX finds `brand=<name>`'s
  `liveries/<name>/` through `TEXINPUTS` (`_extensions/engine//`, `liveries//` and the root
  itself, as an Overleaf zip's `latexmkrc`; never the root's `//`, which reaches `conda-env/`).
  `TTFONTS` needs the root too: the theme looks the bundled fonts up as files,
  `liveries/<name>/fonts/...`, and a miss falls back to an installed face by name silently (the
  image's Poppins then sets bold in SemiBold; a Mac with Poppins installed hides the miss).
- **Roles only**: no palette name is read outside `build/livery.sty`; the Sass sets every color
  as `var(--engine-*)` (its `$ncar-*` variables are compile-time defaults for Quarto's own
  rules, restated with the roles at the end of the file); the highlight theme is generated per
  livery from `engine.theme`.
- **Geometry**: margin, tab, logo box (height per slide kind, top, aspect, corner, `inset`), the
  page number's corner, divider block and full-figure lengths are the livery's `geometry`
  fractions: `engine@geom@*` in the `.sty`, `--engine-*` pixels in the css (ncar's are the
  HTML/PDF numbers, not the pptx template's tighter ones).
- **Art**: `art.waves` (control points and per-kind shifts, drawn in the roles' colors; the pptx
  divider layout from the same numbers; `common/utils/fit-waves.py` fits them to a brand's
  cover art), or a static picture per slide kind (`art.title|section|closing|content`).
- **Title styles**: `title.style` `cover` (default) or `band` (a field in a role with
  `art.title` over it, a band holding the text left of `split` and the photo right of it, the
  marks centred in the strip below; nsi). `title=light` follows the brand's own light cover
  (UCAR Communications' template, slide 4).
- **Templates**: `livery_template.py` generates each `template.pptx` with `Closing` and
  `Title Slide (light)` layouts pandoc never picks; the theme1.xml slots follow the roles
  (`SLOT_ROLES`); the web logos are the brand kit's RGB PNGs (see each `reference/notes.md`).
- **LaTeX**: `latex/Makefile` (`default` talk.pdf, `examples`, `variants`, `html`,
  `previews`, `diagrams`, `overleaf`) sets `TEXINPUTS`/`TTFONTS` (above); its
  `latexmkrc` does the same for a bare `latexmk`. `variants` are `examples/template.tex` under
  the `\enginethemeoptions`/`\engineaspectratio` hooks.
- **Checking a change**: `make test` (`livery_build.py --check` and `livery_check.py` on every
  livery, `tests/test_compositions.py`, whose `EXPECTED_DELTAS` names every decided change of a
  box, and `tests/test_type.py`). For anything that can move pixels, `tests/parity.sh baseline`
  before and `check` after (every deck of quickstart, sample and fixtures under
  `PARITY_LIVERIES`, default `ncar cu nsi`; under `nasa` and `nasa-dark` the quickstart's
  screenshot step stops it, no PDF page reads "MPAS-A") and `tests/parity-latex.sh
  baseline|check` (latex's PDFs page by page, the demo's HTML), same checkout, same day. A
  Sass change is checked by screenshotting every slide before and after (Playwright).
- **Version**: one number, `version:` in `_extension.yml`; a `v*` tag must equal it
  (`release.yml` checks). `VERSION` in `engine-revealjs.lua` names the HTML dependency
  (`engine-revealjs-<VERSION>`), so changing it changes every HTML deck's paths. Ask Ben
  before any tag.

## pandoc pptx gotchas (hard-won — read before restructuring slides)

- **Content after a table or image splits the slide** into an untitled
  continuation. `common/single-body.lua` (shared `_quarto.yml`,
  pptx-only) moves the paragraphs after one table or image (a † footnote, a
  remark) into its caption, which pandoc draws at the slide's foot;
  `style_footnotes.py` then styles a footnote there, left-aligned. Anything
  else after it (a list, code, a second table) still splits, on purpose. Never
  wrap such a body in a 100% column: pandoc gives the table the whole
  placeholder and silently drops the text after it (the slide count doesn't
  change, so `make qa` can't see it). Content *after* `.columns` still splits,
  so put it inside the last column. Code blocks are text and never split.
- **Speaker notes can go anywhere.** Pandoc only picks Two Content when the
  body *starts* with the columns div, so notes written before columns split the
  slide; `common/notes-last.lua` (shared `_quarto.yml`, pptx-only) moves
  every slide's notes to its end. Notes after an image or table do not split.
- **Raw-HTML `<figure>` wrappers demote columns slides to the Comparison
  layout**: quarto wraps rendered diagrams in `` `<figure>`{=html} `` inlines,
  pandoc's layout chooser counts them as text, and the other column's text gets
  stuffed into Comparison's tiny per-column heading box.
  `common/strip-raw-figure.lua` (wired into the shared `_quarto.yml`,
  pptx-only) strips them; don't remove it.
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
  `slideLayout1` placeholders) — see README "Template constraints" and its
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
- **`hash-type: number` strips `#title-slide`**: target `.ncar-title`.
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
- **`make qa` first** (README "Checking a deck"): it does the screenshots,
  overflow and slide-count checks below. Load the `deck-polish` skill for a
  format pass.
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
owned by that user), pushed by digest, merged into one tagged manifest list (`main`, `latest`,
`sha-`, `pr-N`, semver on a tag) and pulled again on both platforms. Build cache: a registry
cache, `ghcr.io/<repo>:buildcache-<arch>`. The merge job's step summary carries the per-platform
size (`render_build_summary.py`, from sam-queries). The deck jobs then run INSIDE that image at
its digest (`container:`, as root, GitHub's default `bash -eo pipefail`; the entrypoint is
bypassed, which is why the activation is `ENV`): `sample` (front matter on line 1,
`livery_build.py --check`, the sample deck in every format with its theme greps, quickstart and
fixtures `all`), `consumer` (the submodule layout, README "Using the framework from another
repo", plus `make site`), `latex` (the engine's `tests/`, then `latex`'s starter, examples,
variants and the demo's HTML, with the Poppins and math-font `pdffonts` checks), and `livery`,
one per directory under `liveries/` (a new
livery joins by existing): `utils/livery_check.py --qa` (the engine's checks, then
`make -C decks/quickstart qa LIVERY=<name>`: all three formats and `deck_qa.py`), the
livery-applied greps, the Overleaf zip compiled in a clean directory with TeX's paths unset and
`pdffonts` showing its bundled family, and `make measure` report-only (`MEASURE_FAIL=`). A
fork's PR has no `packages: write`: its image is built and smoke-tested, nothing is pushed, and
the deck jobs are skipped. Nothing installs conda, TeX, Chrome or LibreOffice on a runner any
more; a tool the decks need goes into the Dockerfile. The package must be public on ghcr for
anonymous pulls (a first push makes it private). `cron-clean-action-log.yaml` prunes old runs
and untagged image versions monthly with the workflow's own token; `release.yml` refuses a tag
that is not `v` + `_extension.yml`'s `version:`, attaches the Overleaf zips and names the image
tags.

## Git

- Standalone repo (often checked out nested inside `hpc-scheduling-tools/docs/`,
  which git-ignores it). Default branch `main`; branch + PR to merge, as merge commits (a
  squash would flatten the engine's imported history out of `git log --follow`).
- `upstream` is `quarto-docs-framework`. The engine's old repo and `NCAR_beamer_template` are
  not remotes here; a fix wanted from the NCAR theme is ported by hand.
- Generated outputs (`*.pptx`, `~$*` lock files, `*_files/`) stay untracked.
