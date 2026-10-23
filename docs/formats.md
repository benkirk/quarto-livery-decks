# The formats

What `make pptx`, `make html` and `make pdf` do with a deck: the repository's layout, the build
pipeline, the fonts, the PowerPoint template's constraints, and the beamer and revealjs formats.

## Layout

```
quarto-livery-decks/
├── bin/livery             # the livery command (liveries/README.md), on PATH after config_env.sh
├── Make.common            # shared per-deck recipes (pptx/html/pdf/qa/measure/site/publish/overleaf/charts-zip/clean)
├── _extensions/engine/    # the engine (symlinked into decks): the pptx, beamer and revealjs
│                          #   formats and their Lua filters, pptx_post.py and its steps
│                          #   ("Build pipeline" below), livery.py (the `livery` command and reader), the livery tools, the chart colors (livery_charts.py), the
│                          #   Overleaf and charts packers, mpl/livery_mpl.py (plots)
├── liveries/              # one directory per livery (`make LIVERY=<name>`; README.md, REFERENCE.md):
│   ├── ncar/  ucar/       #   _brand.yml, livery.yml, fonts/, logos/, art/,
│   ├── ucp/  ncarucar/    #     template.pptx and build/ (both generated, committed),
│   ├── cu/  nsi/          #     reference/notes.md
│   └── nasa/  nasa-dark/  nasa-jsc-eg/
├── common/                # what decks share:
│   ├── _quarto.yml        #   the Quarto config (symlinked into decks)
│   └── utils/
│       ├── deck_qa.py          # `make qa`: overflow, slide counts, contact sheets
│       ├── comp_measure.py     # `make measure`: the drawn slides against their compositions
│       ├── site_index.py       # `make site`: the index page
│       └── fit-waves.py        # fits a brand's wave curves to its cover art (art.waves)
├── decks/
│   ├── quickstart/        # the short exemplar deck: copy this one
│   │   ├── quickstart.qmd
│   │   ├── screenshots.py  (make screenshots: the README images)
│   │   ├── gallery.py      (make gallery: the README's livery gallery)
│   │   └── screenshots/    (those images, committed)
│   ├── fixtures/          # small decks for the title variants and type steps,
│   │                      #   for parity.sh and CI
│   ├── plots/             # the plots cookbook (jupyter: python3, matplotlib, seaborn);
│   │                      #   its README.md, gallery.py (make gallery) and screenshots/
│   └── sample/            # the cookbook deck
│       ├── Makefile        (one line: include ../../Make.common)
│       ├── _quarto.yml     (symlink → ../../common/_quarto.yml)
│       ├── _extensions     (symlink → ../../_extensions, made by make)
│       ├── _livery         (symlink → the livery in use, made by make)
│       ├── sample.qmd      (the cookbook)
│       ├── old.qmd         (a longer real-world example)
│       └── images/         (drop your PNGs / JPGs here)
├── latex/                 # the engine's pure-LaTeX side: talk.tex (the starter),
│                          #   examples/ and their variants (`make latex`)
├── design/                # the design (engine-and-liveries.md) and the sprint handoffs
├── tests/                 # the engine's tests (pytest, `make test`) and the parity harnesses:
│                          #   parity.sh (every deck, every livery), parity-latex.sh (latex/)
├── Makefile               # top-level: `make conda-env`, env mgmt, `make latex`, `make test`
├── conda-env.yaml         # quarto + jupyter + bash_kernel + the scientific stack + helpers
├── Dockerfile             # the build-environment image (docs/container.md)
├── etc/                   # config_env.sh, the image's entrypoint
└── conda-env/             # local conda prefix, gitignored
```

## Build pipeline

Per deck, `make pptx` runs:

1. `quarto render <deck>.qmd --to engine-pptx -o <deck>.pptx`, the engine's pptx format,
   with `reference-doc: _livery/template.pptx` from the deck's `_quarto.yml`, so the output
   inherits the livery's theme colors, layouts and masters. Code is highlighted in the
   livery's colors (`_livery/build/livery.theme`, as in HTML and PDF), set in its code face
   when it has one, and the format's Lua filters (in `_extensions/engine/`) prepare the
   document for pandoc's pptx writer:
   - `strip-raw-figure.lua`, `notes-last.lua` and `single-body.lua` keep pandoc from
     demoting or splitting slides (raw `<figure>` wrappers, notes before columns, text or a
     `::: note` after a table or image, which joins its caption box);
   - `slide-layout.lua` carries a slide's layout classes (and the references slide) over as a
     notes line for `slide_layout`;
   - `inline-footnotes.lua` makes a slide's `^[...]` notes slide footnotes (a mark in the text, a
     paragraph led by its marker) in place of pandoc's "Notes" slide;
   - `grid-pptx.lua` carries a two-column slide's widths over as a notes line for `columns`, and
     flattens a grid slide (what `engine-common.lua`'s `is_grid()` counts: more than two columns,
     since pandoc's pptx keeps the first two, cards, a lead box, a strip, a rail, a gallery, a
     quote, an agenda) into one text flow with marker paragraphs for `grid`;
   - `linked-images.lua` writes a linked picture's URL (HTML and PDF too; see [authoring.md "Linked images"](authoring.md#linked-images));
   - `diagram-dark.lua` turns the diagram pictures to the dark under a dark livery (PDF too).
2. `python3 _extensions/engine/pptx_post.py <deck>.pptx`, the engine's post-render steps
   (`_extensions/engine/pptx_steps/`). It opens the deck once, runs them in this order and
   saves once:
   - `svg_fallback`: gives each SVG picture (the plots, `fig-format: svg`) a PNG at the deck's
     `fig-dpi`, by `rsvg-convert`, the way PowerPoint saves one: the picture is the PNG and the
     SVG rides on Office's `svgBlip` extension, so PowerPoint draws vector and an app that
     ignores the extension (Google Slides' import) the PNG. First, so every later step sees a
     PNG picture.
   - `notes_clrmap`: gives each notes slide the `<p:clrMapOvr>` PowerPoint writes (the notes
     master's colors), which pandoc leaves out. Keynote refuses a deck with one notes slide
     that lacks it, as an invalid file; PowerPoint and Google Slides open it either way.
   - `section_subtitle`: merges the paragraph after a `#` section heading back onto the
     Section Header slide as its subtitle (pandoc drops it onto a separate untitled slide),
     then dresses every divider as the HTML and PDF decks draw it: the livery's "SECTION n"
     label, its tab, the block centered and measured in the livery's fonts. The field, logo
     and art come from the template's Section Header layout (see "Template constraints").
   - `enable_autofit`: flips every body placeholder from "Do not Autofit" to "Shrink text
     on overflow" (see [authoring.md "About text autofit"](authoring.md#about-text-autofit)).
   - `embed_fonts`: re-injects the livery's font variants as `<p:embeddedFont>` entries,
     which pandoc strips, so the font travels with the file (see "About the fonts").
   - `style_footnotes`: restyles body paragraphs that start with `†`, `‡`, `§` or `¶` (a
     `^[...]` note too, which `inline-footnotes.lua` writes as one) as footnotes from the livery's
     `boxes.footnote` (the footnote size, the muted color, the marker bold in the accent and
     hanging by `hang`, `gap` above the first and `step` above each following one), since pandoc
     ignores inline size and color. HTML and PDF go further: the theme moves them to the slide's
     foot under a short rule (`rule`, `rule-length`, `rule-color`, `width`), which pptx cannot
     draw where the paragraph will land.
   - `link_captions`: captions each linked picture (see [authoring.md "Linked images"](authoring.md#linked-images)) with its URL,
     bottom center, muted; the caption box is itself the link.
   - `slide_layout`: applies a slide's layout controls (see [authoring.md "Centering and scaling a short slide"](authoring.md#centering-and-scaling-a-short-slide)); builds the photo covers and feature slides; points closing and light
     title slides at the template's extra layouts; sets a `::: note` in the caption's look
     under its figure (see [authoring.md "Notes under a figure"](authoring.md#notes-under-a-figure)); copies the slide number onto every slide.
   - `columns`: sets a two-column slide's columns at their widths, the livery's gap between them
     (`boxes.columns.gap`), as HTML and PDF lay them out; pandoc's are the template's two halves.
     A picture or table in a column moves and scales with it.
   - `grid`: draws a grid slide (what `is_grid()` counts: three or more columns, cards, a lead
     box, a strip, a rail, a quote, an agenda) from `grid-pptx.lua`'s markers: native shapes
     (fills, bars, rounded cards, outlines, badges) and text boxes in the body placeholder's look,
     at the same widths, gap and pads as HTML and PDF (the livery's `boxes`), each element one
     group; `gallery.py`, which it calls, places a gallery's pictures from the deck's directory.
     A picture or table in such a column is not drawn in it yet (a warning at render time).
   - `status_glyphs`: makes a status item's ✓ ⚠ ✗ its bullet, in the livery's status color.
   - `style_tables`: styles every table as the HTML theme does (a bold capitalized header
     over a rule in the primary color, thin rules between rows, every second row banded, the
     blends from `livery_build.py`); pandoc always writes "Medium Style 2", so the look is set
     cell by cell, and evenly split columns are re-split by content.
   - `marking`: the marking strip on every slide (a deck's `marking:`, else the livery's
     default text; see [authoring.md "Front matter and slide kinds"](authoring.md#front-matter-and-slide-kinds)).
   - `type_step`: applies a deck's `type-body:` or `type-scale:` (see [authoring.md "Text sizes and the slide size"](authoring.md#text-sizes-and-the-slide-size)),
     last, to every size the steps before it set (the strip's too, as HTML and PDF scale it).

`make html` (revealjs) and `make pdf` (beamer) run step 1 with the engine's own format and
filters, which draw everything step 2 adds to the pptx.

## About the fonts

Every livery bundles the fonts its HTML and PDF decks use (the brand's own when they are
free, a free stand-in otherwise), so there is nothing to install. The pptx template's font
scheme names the livery's typeface (`pptx.typeface`, and `pptx.heading-typeface` for a second
headings face), so slide masters and layouts all dereference to it:

- **ncar** and its family (`ucar`, `ucp`, `ncarucar`) name Poppins and embed it (`pptx.fonts`,
  four `.fntdata` blobs), so the file carries its font to any machine.
- **cu** and **nsi** name Helvetica Neue, a commercial face, and embed nothing: Macs have it,
  Windows substitutes Arial. HTML and PDF use it where it is installed (below).
- **nasa** and **nasa-dark** name Public Sans and Inter. They embed once the livery carries
  PowerPoint's `.fntdata` blobs (made by one PowerPoint save with "Embed fonts" on); until
  then a viewer without the faces sees PowerPoint's substitute.
- **nasa-jsc-eg** names Arial, its template's face, and embeds nothing (every Office has it);
  HTML and PDF set Liberation Sans, its metric twin, where Arial is not installed.

A livery's code face (`typography.monospace` in `_brand.yml`, with files of its own: nasa's
DM Mono) sets code in all three formats: pandoc's `monofont` in pptx, the code font in HTML
and the PDF. `pptx.code-typeface` names an installed face for the pptx alone, as a brand
template does (nasa-jsc-eg: Courier New). The other liveries use each format's default code fonts.

Embedding is only needed when the `.pptx` will be opened on a machine without the font;
without it, PowerPoint substitutes (typically Calibri). If every viewer has the font, drop
the livery's `pptx.fonts` (`embed_fonts.py` then leaves the deck alone).

## Installed brand fonts

Some brand faces are commercial and cannot ship in the repo or a published site: cu's
Helvetica Neue is Monotype's, so cu bundles TeX Gyre Heros (and Heros Condensed for
headings) and names the real face in `livery.yml`:

```yaml
installed-fonts:
  base: Helvetica Neue                  # a family: its four faces by the usual names
  headings:                             # or faces by full and PostScript name
    family: Helvetica Neue
    faces: {bold: [Helvetica Neue Condensed Bold, HelveticaNeue-CondensedBold],
            regular: [Helvetica Neue Condensed Bold, HelveticaNeue-CondensedBold]}
```

- **HTML**: each `@font-face` lists the installed face as `local()` sources ahead of the
  bundled file, so a viewer who has it (every Mac and iPhone) sees Helvetica Neue and anyone
  else Heros. Nothing is copied.
- **PDF**: a deck opts in with `themeoptions: [fonts=brand]`; the theme then loads the
  installed faces when the machine building the PDF has them and embeds them for every
  reader (built on Linux, it falls back to Heros). The shared `fonts=bundled`, CI, parity
  and the Overleaf zips ignore installed fonts, so their output never depends on the machine.
- **pptx**: nothing to do; the theme names `pptx.typeface` (Helvetica Neue) already.

The framework never copies the font. Embedding an installed font in a PDF you hand out is a
question for that font's license: macOS's covers using its fonts, not redistributing the
files, which this never does; check before you publish a PDF built this way.

## Template constraints

Each livery's `template.pptx` is generated by `livery template`
(`_extensions/engine/livery_template.py`) from the livery's data (`build/livery.json`:
theme slots, typeface, marks, geometry, art); never edit it by hand, change the
livery and rerun `make livery`. It keeps the things pandoc is strict about:

- **`slideLayout1` placeholders**: must include all five of `ctrTitle`,
  `subTitle`, `dt`, `ftr`, `sldNum`. Pandoc emits empty `<p:sp/>` stubs
  for any missing placeholder, which PowerPoint then flags as corrupt
  ("Repair?" prompt on open).
- **Layout names**: pandoc looks up layouts by display name. The title
  slide layout must be named exactly `Title Slide`; other layouts pandoc
  knows about are `Title and Content`, `Section Header`, `Two Content`,
  `Comparison`, `Content with Caption`, `Blank`. Missing names don't
  break the build but trigger a `Couldn't find layout named …` warning
  and fall back to pandoc's bundled layout (losing the brand's styling for that
  slide).
- **Placeholder indices**: pandoc matches content boxes by `idx` as well as
  type, so the date, footer and slide-number placeholders carry indices (20-22)
  no content box uses; a collision drops a column into the footer's box.
- **Two more layouts pandoc never picks**: `Closing` and `Title Slide (light)`.
  Pandoc copies every layout of the reference doc into the deck but chooses only
  by the names above (its choice between two layouts of one name is undocumented,
  so every name is unique). `slide_layout.py` points a `{.closing}` slide at
  `Closing`, and the title slide at `Title Slide (light)` when the deck's front
  matter sets `themeoptions: [..., title=light]`; in PowerPoint both are in the
  layout menu for slides added by hand.

Verify after any template change:

```bash
unzip -p liveries/ncar/template.pptx \
  ppt/slideLayouts/slideLayout1.xml | grep -oE '<p:ph[^/]*/>'
# expect 5 matches
```

## PDF (beamer)

`make pdf` renders with `--to engine-beamer`. That format comes from the engine's
beamer theme in `_extensions/engine/` (until 2026-10 its own repository,
[benkirk/beamer-livery-theme](https://github.com/benkirk/beamer-livery-theme)). Make symlinks
`_extensions` into each deck directory, just as it does for `_quarto.yml`.

- **You need Quarto 1.6 or newer** (the conda env pins it): the theme's Lua
  filter uses a pandoc macro that older Quarto releases lack.
- **You need TeX with XeLaTeX.** Quarto's own TinyTeX (`quarto install
  tinytex`) works and installs missing LaTeX packages on the fly. So does a
  system TeX Live. (Plain-LaTeX decks, not Quarto ones, can also be written
  on Overleaf: [`latex/README.md`](../latex/README.md); the same slide patterns by hand:
  [`latex/authoring.md`](../latex/authoring.md).)
- **No fonts to install** (see "About the fonts").
- **Theme options and slide kinds** are the deck's, in every format: [authoring.md "Front matter and
  slide kinds"](authoring.md#front-matter-and-slide-kinds).
- **Dense slides**: beamer has no autofit; see [authoring.md "About text autofit"](authoring.md#about-text-autofit).

## HTML (revealjs)

`make html` renders with `--to engine-revealjs`, the web format from the same
extension. The deck looks like the PDF: title slide with the livery's
art (or `titlegraphic:`), section dividers with subtitles, content slides
with the livery's title and marks, `.feature` and `.closing` slides. The same
`themeoptions:` apply ([authoring.md "Front matter and slide kinds"](authoring.md#front-matter-and-slide-kinds):
`title=`, `waves=`; math in the browser is MathJax's, so `mathfont=` does not). Open `<deck>.html` in a browser
and keep `<deck>_files/` beside it.

- **Presenting:** `s` speaker view (notes), `m` slide menu, `b`/`c`
  whiteboard / draw on the slide, `f` full screen.
- **HTML-only extras:**
  - `## Title {.brand-dark}` puts a content slide on the livery's dark role, its text in
    the `on-dark` role (under a dark livery, every content slide already is); pptx and PDF
    draw an ordinary slide.
  - Overflowing content slides shrink to fit (see [authoring.md "About text autofit"](authoring.md#about-text-autofit)).
  - Mermaid and Graphviz draw live in the browser; mermaid uses the livery's
    colors and font where pptx and PDF carry a picture of it.
- **One file to share:** in a deck's front matter,
  ```yaml
  format:
    engine-revealjs:
      embed-resources: true
      chalkboard: false     # the whiteboard can't be embedded
  ```
  gives a single self-contained `.html`.
- **PNG plots:** HTML draws plots as SVG. A plot with many marks (thousands of bars, a dense
  scatter) makes a heavy SVG that is slow to page through; in that deck's front matter,
  ```yaml
  format:
    engine-revealjs:
      fig-format: png
      fig-dpi: 200          # pptx's
  ```
  draws them as PNGs instead (pptx carries an SVG with a PNG fallback at that dpi), at the same
  size on the slide. For one plot rather than the
  deck, draw it inside `with livery_mpl.raster():` (a cell's own `fig-format` is not honored by the
  Jupyter engine; `decks/plots/README.md`).
- **PDF from the browser:** open `<deck>.html?print-pdf` in Chrome and print
  with background graphics. `make pdf` is usually the better handout.
