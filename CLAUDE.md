# CLAUDE.md

Guidance for working in this repository. Keep it accurate — update it when the
structure or conventions below change.

## What this is

A [Quarto](https://quarto.org) framework for documentation decks (`.pptx`
primary; `.html`/revealjs and `.pdf`/beamer secondary), and the **multi-brand
successor** of `benkirk/quarto-docs-framework` (the `upstream` remote), which
stays the NCAR framework. `docs/design/engine-and-liveries.md` is the roadmap (next: NASA; the compositions and the
type scale are done, 2026-10-17):
a generalized **engine** (the vendored theme, forked as
`benkirk/beamer-livery-theme`) plus per-brand **livery** directories under
`docs/common/liveries/`; its section 10 logs progress and names the next step.
Phase 1 (the framework reads the livery) is done and Phase 2 (the engine) is under
way: the theme is renamed and reads a livery. The reference liveries live in the engine
(`_extensions/benkirk/engine/liveries/`; `docs/common/liveries/ncar` is a link to its
`ncar`), built by the engine's `livery_build.py` into `build/livery.{json,sty,css}`
(an unknown `livery.yml` key is warned about). The engine also holds the json reader
(`livery.py`), the template builder (`livery_template.py`), the wave shapes
(`pptx_waves.py`) and the livery checks (`livery_check.py`), since engine 3.3.0:
`utils/livery.py` is a shim that loads the vendored reader by path (both are named
`livery`; `engine_module()` loads any engine module the same way) and adds
`livery.py deps <dir>`, and `utils/livery_check.py` wraps the engine's checks and adds
`--qa`. NCAR PDF and HTML decks
still build byte-identically to upstream; the pptx template is generated. Phase 3
(onboarding a brand from a reference PowerPoint, design section 6) is under way:
`utils/livery_inspect.py` writes a livery's `reference/report.md` from the deck,
the engine's `livery_template.py` builds its `template.pptx` from the data, and the first
non-NCAR livery, `cu` (CU Boulder), is a real directory under `docs/common/liveries/`
with its decisions in `reference/notes.md`; `nsi` (the CU Center for National Security
Initiatives) is its first flavor (`extends: cu`), on the engine's band title style
(`title: {style: band}`, engine >= 3.1.0). The reference decks themselves live on
Drive or a laptop, not in git. A livery without `pptx.fonts` embeds nothing
(`embed_fonts.py` says so and leaves the deck alone); a livery without `art.waves`
gets straight-edged title fields in every format.

Decks live under `docs/<deck>/` as a `.qmd` plus a 1-line Makefile; shared
machinery is in `docs/common/` (the brand `template.pptx`, `_quarto.yml`, Lua
filters, post-render utilities) and `docs/Make.common`.
`docs/quickstart/quickstart.qmd` is the short exemplar to copy for new decks;
`docs/sample/sample.qmd` is the cookbook of every pattern. The README covers
layout, template constraints, and font embedding.

- **README images** are `docs/quickstart/screenshots/*.png`, committed. After
  editing the quickstart deck run `make screenshots` there, look at them, and
  commit them. Slides are found by title (`SLIDES` in `screenshots.py`), so a
  renamed slide needs that list updated. `make gallery` (`gallery.py`) writes
  `liveries.png`, the deck under every livery (title, divider, content, closing),
  rebuilding the HTML per `LIVERY`; `screenshots.py` leaves that file alone. Where the MathJax CDN is blocked, set
  `MATHJAX` to a local MathJax 2.7 (the npm tarball from registry.npmjs.org),
  or the equations shoot as raw TeX.

Other repos can take the framework as a submodule and keep their decks in their
own tree (README "Using the framework from another repo"); the deck Makefile
includes `../framework/docs/Make.common`. So nothing may assume a deck sits in
`docs/<deck>/`: the shared `_quarto.yml` reaches `common/` as `_engine/`, a link
Make creates in each deck directory. `ci.yaml`'s `consumer` job builds a deck that way,
and the image's smoke test a bare directory with no Makefile at all (`make -f
<framework>/docs/Make.common DECKS=...`, which the entrypoint supplies).

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
  `make` in a Makefile-less directory into `make -f /opt/quarto-livery-decks/docs/Make.common
  DECKS=<its qmds>`. Everything under `/opt` must stay world-readable (asserted). The three
  `_quarto.yml`/`_extensions`/`_engine` links are `ln -sfn`, so a dangling link left by the other
  side (host or container) is re-pointed; a real file or a resolving link is never touched.
- **Build**: `make pptx` (also `html`, `pdf`) inside the deck directory.
  `Make.common` names the output after the directory (`OUT`) and auto-symlinks
  `_quarto.yml` and `_extensions`. The pptx recipe post-processes with
  `section_subtitle.py`, `enable_autofit.py`, `embed_fonts.py`,
  `style_footnotes.py`, `link_captions.py`, `slide_layout.py`,
  `style_tables.py` (tables drawn as in the HTML theme), and `type_step.py` (a deck's
  `type-body:`/`type-scale:`).
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
  theme (>= 2.4.0) lifts every one on a slide, columns included, to the slide's
  foot in HTML and PDF, under a short muted rule with the marker in the accent
  orange; pptx can't move content, so `style_footnotes.py` mutes them in place
  in the same colors. `*† text*` works too.
- **Linked images** (`[![](x.png)](url)`): the picture is the link in every
  format, and each shows the URL: the HTML footer and a PDF foot line come from
  `docs/common/linked-images.lua`, the pptx caption box from `link_captions.py`
  (after pandoc, because anything after an image splits a pptx slide). A deck
  should not hand-roll footers for this. README "Linked images".
- **Short slides** (`{.hcenter}`, `{.vcenter}`, `{.center}`, `scale="S"`,
  `{.fill}`, each independent): the theme (>= 2.5.0) centers and scales the
  body in HTML and PDF. pptx drops slide classes, so `common/slide-layout.lua`
  writes them as a notes line, `engine-layout: vcenter scale=1.4`, which
  `slide_layout.py` applies and deletes; it can't do `hcenter` or `fill`, and
  centers a table by an estimated height. `.center` is the theme's, not
  Quarto's (which moves the title). README "Centering and scaling a short slide".
- **Warning slides** (`{.caution}`, theme >= 2.8.0): the body on a soft yellow
  field with a brand-yellow bar; footnotes stay below it in HTML and PDF. pptx:
  `slide_layout.py` fills the body text box, adds the bar, and cuts the box to an
  estimate of its text (pandoc gives it the whole content area). Set all four of
  a placeholder's left/top/width/height together: it inherits its frame, and
  setting one leaves the others at 0 (the text vanishes).
- **Full-slide figures** (`{.full}`, theme >= 2.7.0): one diagram or image fills
  the slide, the paragraph after it is a one-line caption. HTML and PDF are the
  theme's (PDF frame key `ncarfull=`). pptx: `slide-layout.lua` writes
  `engine-layout: full`, and `slide_layout.py` sets the slide's `showMasterSp="0"`
  (hiding the master's logo, tab, rule and waves), deletes the title, fits the
  one picture to the slide and centers pandoc's caption box under it. Any other
  body is left alone with a warning. `make qa` fails a caption that wraps.
- **Compositions** (engine >= 3.5.0): the title (`title`, `title-photo`, `title-light`,
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
  contact sheet `_qa/compositions-<livery>.png`; `docs/design/compositions-baseline.md` is the
  before-picture. The pptx can't flow a stack: `band_stack()` centres a band's date, title,
  rule and subtitle on the column from estimates of their text (the rule moves onto the slide),
  a closing splits its column at the middle. Over art, a mark's box is the eroded mask's core
  widened along its rows (`widened()`), so thin type ("Office") is not lost.
- **Type** (engine >= 3.6.0): text sizes are **points on the livery's pptx canvas**, whole or
  half points (a pasted slide carries round numbers): `livery.yml` `type:` (role -> pt, `levels`)
  and `pptx.size` (inches, default 13.333 x 7.5), defaulting to the engine's `TYPE` (the NSF NCAR
  template's guidance carried onto 540 pt). ncar is on the brand template's own canvas, 10 x
  5.625 in, at its guidance (body 12, titles 20; its family inherits); cu's are the NSI master
  deck's (body 16, titles 32, cover 48, dividers 60). HTML and beamer take the same sizes as fractions of the slide height, so
  the formats fit and overflow alike; the post-processors read `livery.type_pt()` and scale their
  absolute pads by `livery.canvas_scale()`; `scale=` rounds a pptx size to the half point.
  A deck's size step: front matter `type-body: <pt>` or `type-scale: <factor>` (engine >= 3.7.0:
  beamer `typescale=`, HTML `--engine-type-scale`; pptx `type_step.py`, last in the recipe,
  reads it from `docProps/custom.xml`); `docs/fixtures/small.qmd` is `type-body: 10`.
- **Marks and numbers** are livery parameters (`signoff`, `geometry.logo.corner`,
  `geometry.pagenumber.corner`; defaults are NCAR's layout) that the three themes
  and `livery_template.py` all honor. Which mark and sign-off a field wears goes by
  its role (`marks:`, engine >= 3.3.0; `livery.json` always has `marks`, read with
  `livery.mark(livery, role, "logo"|"signoff")`): content slides `background`,
  dividers, covers and the cover closing `primary`, the band title and closing
  `title.field`. Defaults: background `logo.medium.light`/`signoff.light`, primary the
  dark ones, any other role primary's (nsi: black mark on gold, white on the band). pandoc writes no slide-number box, so
  `slide_layout.py` copies the layout's placeholder onto every slide; a livery's
  `typography.headings` may be a second font family (cu: TeX Gyre Heros Cn).
- **PDF** is `--to engine-beamer`: the engine beamer theme, vendored from
  `benkirk/beamer-livery-theme` into `docs/common/_extensions/benkirk/engine/`.
  Don't edit the vendored copy. Change the theme repo, then re-vendor with
  `cd docs/common && quarto update benkirk/beamer-livery-theme` (the
  vendored `_extension.yml` records no source, so the bare `quarto update`
  fails). To build against an engine branch before it is merged, `make
  vendor-engine` (root Makefile, `ENGINE=../beamer-livery-theme`) syncs that
  checkout in; the `quarto update` after the merge must then show no diff. The extension's Lua filter loads the theme in place
  through `\input@path`, so nothing is copied into deck directories. Needs
  XeLaTeX (TinyTeX or TeX Live) and Quarto >= 1.6 (`quarto-required` in the
  shared `_quarto.yml`; `conda-env.yaml` pins it). Beamer has no autofit: dense slides
  overflow silently, so render the PDF and look at it, then trim the content
  or add `{.shrink}` to the heading. A full-width 16:9 screenshot is taller than
  the frame's content area; cap it with `{height="72%" fig-align="center"}`
  (pptx ignores the attribute and fits the placeholder anyway).
- **HTML** is `--to engine-revealjs`, from the same vendored extension (see
  "revealjs (HTML) theme" below).
- **Theme options** (`themeoptions:` in a deck's front matter) replace the
  shared list in `docs/common/_quarto.yml`, so a deck that sets any must
  repeat `fonts=bundled`. Theme 2.3: `mathfont=` (default a serif math font,
  NewCM Book scaled to Poppins; `stix`, `lm`, `pagella`, `sans`, `fira`,
  `poppins` for the old Poppins-letter look, `keep`, or a font name; Quarto's
  own `mathfont:` key still wins) and `waves=false` (drops the faint wave
  lines behind content slides in PDF and HTML; pptx has them on the master).
  The waves are fitted to the brand's cover art by `tools/fit-waves.py` in
  the theme repo, which prints the TikZ and Lua blocks to paste.
- **Format conditionals**: `when-format="beamer"` matches the custom
  `engine-beamer` format; `when-format="engine-beamer"` matches nothing. Always
  write `beamer`.
- **Poppins has no arrows or ⚠**: theme 2.6 borrows ⚠ → ← ↔ ⇒ from DejaVu
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
  prerequisite. The HTML recipe deletes `<deck>_files/libs/quarto-contrib/engine-revealjs-*`
  before rendering: that dependency is named for the engine version, and quarto keeps a
  copied file newer than its source, so a livery switch kept the old livery's css. A file included from anywhere else (e.g. `../other_deck/_x.qmd`) is invisible
  to make; `touch <deck>.qmd` after editing one.
- **`LIVERY=` on the command line always wins**: `Make.common` exports `LIVERY_DIR`, which
  a sub-make would otherwise keep (`?=`) over its own `LIVERY=cu` (the gallery once stamped
  cu and linked ncar); `override LIVERY_DIR` when `LIVERY` is command-line.
- **Several decks in one directory**: set `DECKS := a b c` before the include;
  each `<name>.qmd` builds `<name>.{pptx,html,pdf}`. They share one `.quarto/`
  cache, so `Make.common` is `.NOTPARALLEL`. `docs/fixtures/` is such a directory:
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

## pandoc pptx gotchas (hard-won — read before restructuring slides)

- **Content after a table or image splits the slide** into an untitled
  continuation. `docs/common/single-body.lua` (shared `_quarto.yml`,
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
  slide; `docs/common/notes-last.lua` (shared `_quarto.yml`, pptx-only) moves
  every slide's notes to its end. Notes after an image or table do not split.
- **Raw-HTML `<figure>` wrappers demote columns slides to the Comparison
  layout**: quarto wraps rendered diagrams in `` `<figure>`{=html} `` inlines,
  pandoc's layout chooser counts them as text, and the other column's text gets
  stuffed into Comparison's tiny per-column heading box.
  `docs/common/strip-raw-figure.lua` (wired into the shared `_quarto.yml`,
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

Lives in the vendored extension (`engine-revealjs.{scss,css,js,lua}`,
`title-slide.html`); change it in the theme repo, like beamer. Things that
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
  script renders in mermaid's own scratch element instead (theme 2.2.0).
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
  guarantees no crossings. `docs/sam_and_pbs/sam_and_pbs.qmd`'s "SAM to PBS
  Schematic" is the worked example — it took four renders to learn this.
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
- `docs/sam_and_pbs/tree2mermaid.py` converts PBS `resource_group` trees into
  styled mermaid; its frozen inputs/fragments regenerate via `refresh_data.sh`
  (needs the `hpc-scheduling-tools` checkout four levels up + SAM credentials;
  rendering the deck itself never does).

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
mermaid block, then `docs/quickstart` through its real Makefile, both bind-mounted, outputs
owned by that user), pushed by digest, merged into one tagged manifest list (`main`, `latest`,
`sha-`, `pr-N`, semver on a tag) and pulled again on both platforms. Build cache: a registry
cache, `ghcr.io/<repo>:buildcache-<arch>`. The merge job's step summary carries the per-platform
size (`render_build_summary.py`, from sam-queries). The deck jobs then run INSIDE that image at
its digest (`container:`, as root, GitHub's default `bash -eo pipefail`; the entrypoint is
bypassed, which is why the activation is `ENV`): `sample` (front matter on line 1,
`livery_build.py --check`, the sample deck in every format with its theme greps, quickstart and
fixtures `all`), `consumer` (the submodule layout, README "Using the framework from another
repo", plus `make site`), and `livery`, one per directory under `docs/common/liveries/` (a new
livery joins by existing): `utils/livery_check.py --qa` (the engine's checks, then
`make -C docs/quickstart qa LIVERY=<name>`: all three formats and `deck_qa.py`), the
livery-applied greps, the Overleaf zip compiled in a clean directory with TeX's paths unset and
`pdffonts` showing its bundled family, and `make measure` report-only (`MEASURE_FAIL=`). A
fork's PR has no `packages: write`: its image is built and smoke-tested, nothing is pushed, and
the deck jobs are skipped. Nothing installs conda, TeX, Chrome or LibreOffice on a runner any
more; a tool the decks need goes into the Dockerfile. The package must be public on ghcr for
anonymous pulls (a first push makes it private). `cron-clean-action-log.yaml` prunes old runs
and untagged image versions monthly with the workflow's own token; `release.yml` attaches the
Overleaf zips and names the image tags.

## Git

- Standalone repo (often checked out nested inside `hpc-scheduling-tools/docs/`,
  which git-ignores it). Default branch `main`; branch + PR to merge.
- Generated outputs (`*.pptx`, `~$*` lock files, `*_files/`) stay untracked.
