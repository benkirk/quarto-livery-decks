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
│   └── nasa/  nasa-dark/
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
│   │   ├── gallery.py      (make gallery: the livery rows above)
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
├── tests/                 # the engine's tests (`make test`) and the parity harnesses:
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
     demoting or splitting slides (raw `<figure>` wrappers, notes before columns, text
     after a table or image);
   - `slide-layout.lua` carries a slide's layout classes over as a notes line for `slide_layout`;
   - `linked-images.lua` writes a linked picture's URL (HTML and PDF too; see [authoring.md "Linked images"](authoring.md#linked-images));
   - `diagram-dark.lua` turns the diagram pictures to the dark under a dark livery (PDF too).
2. `python3 _extensions/engine/pptx_post.py <deck>.pptx`, the engine's post-render steps
   (`_extensions/engine/pptx_steps/`). It opens the deck once, runs them in this order and
   saves once:
   - `section_subtitle`: merges the paragraph after a `#` section heading back onto the
     Section Header slide as its subtitle (pandoc drops it onto a separate untitled slide),
     then dresses every divider as the HTML and PDF decks draw it: the livery's "SECTION n"
     label, its tab, the block centered and measured in the livery's fonts. The field, logo
     and art come from the template's Section Header layout (see "Template constraints").
   - `enable_autofit`: flips every body placeholder from "Do not Autofit" to "Shrink text
     on overflow" (see [authoring.md "About text autofit"](authoring.md#about-text-autofit)).
   - `embed_fonts`: re-injects the livery's font variants as `<p:embeddedFont>` entries,
     which pandoc strips, so the font travels with the file (see "About the fonts").
   - `style_footnotes`: restyles body paragraphs that start with `†` or `‡` as footnotes
     (smaller, the livery's muted color, the marker in its accent), since pandoc ignores
     inline size and color. HTML and PDF go further: the theme moves them to the slide's foot.
   - `link_captions`: captions each linked picture (see [authoring.md "Linked images"](authoring.md#linked-images)) with its URL,
     bottom center, muted; the caption box is itself the link.
   - `slide_layout`: applies a slide's layout controls (see [authoring.md "Centering and scaling a short slide"](authoring.md#centering-and-scaling-a-short-slide)); builds the photo covers and feature slides; points closing and light
     title slides at the template's extra layouts; copies the slide number onto every slide.
   - `style_tables`: styles every table as the HTML theme does (a bold capitalized header
     over a rule in the primary color, thin rules between rows, every second row banded, the
     blends from `livery_build.py`); pandoc always writes "Medium Style 2", so the look is set
     cell by cell, and evenly split columns are re-split by content.
   - `type_step`: applies a deck's `type-body:` or `type-scale:` (see [authoring.md "Text sizes and the slide size"](authoring.md#text-sizes-and-the-slide-size)).

`make html` (revealjs) and `make pdf` (beamer) run step 1 with the engine's own format and
filters, which draw everything step 2 adds to the pptx.

## About the fonts

Every livery bundles the fonts its HTML and PDF decks use (the brand's own when they are
free, a free stand-in otherwise), so there is nothing to install. The pptx template's font
scheme names the livery's typeface (`pptx.typeface`, and `pptx.heading-typeface` for a second
headings face), so slide masters and layouts all dereference to it:

- **ncar** names Poppins and embeds it (`pptx.fonts`, four `.fntdata` blobs), so the file
  carries its font to any machine.
- **cu** and **nsi** name Helvetica Neue, a commercial face, and embed nothing: Macs have it,
  Windows substitutes Arial. HTML and PDF use it where it is installed (below).
- **nasa** and **nasa-dark** name Public Sans and Inter. They embed once the livery carries
  PowerPoint's `.fntdata` blobs (made by one PowerPoint save with "Embed fonts" on); until
  then a viewer without the faces sees PowerPoint's substitute.

A livery's code face (`typography.monospace` in `_brand.yml`, with files of its own: nasa's
DM Mono) sets code in all three formats: pandoc's `monofont` in pptx, the code font in HTML
and the PDF. The other liveries use each format's default code fonts.

Embedding is only needed when the `.pptx` will be opened on a machine without the font;
without it, PowerPoint substitutes (typically Calibri). If every viewer has the font, drop
the `embed_fonts.py` step from `Make.common`.

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
question for that font's licence: macOS's covers using its fonts, not redistributing the
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
  on Overleaf: [`latex/README.md`](../latex/README.md).)
- **No fonts to install** (see "About the fonts").
- **Theme options** go in a deck's front matter:
  `themeoptions: [title=light, fonts=bundled]`. A deck-level
  list replaces the shared one, so keep `fonts=bundled` (from the shared
  `_quarto.yml`): it pins the livery's bundled fonts and never probes for a
  system copy (`fonts=brand` uses an installed brand face instead; see
  "Installed brand fonts").
  - `titlegraphic: images/photo.jpg` puts a photo on the title slide, in every
    format, where the livery's title composition places it. Without one the livery's
    default appears (`art.titlegraphic`: ncar's Mesa Lab, nsi's campus, nasa's Earth
    limb); `titlegraphic: none` keeps the plain cover.
  - `fineprint: "..."` adds small print under the title block.
  - `mathfont=stix` (or `lm`, `pagella`, `sans`, `fira`, `poppins`, any
    OpenType math font) changes the math font; the default is New Computer
    Modern Math, scaled to sit with the text font. Quarto's own `mathfont:` key
    also works. [latex/README.md "Math fonts"](../latex/README.md#math-fonts) shows every preset on one slide.
  - `waves=false` removes the faint wave lines behind content slides of a
    livery that has them (they are on the pptx master too).
- **Markdown extras:**
  - `## Title {.feature background-image="images/photo.jpg"}` makes a
    full-bleed photo slide (`background=` also works; `background-image=`
    doubles as the revealjs background). Its look is the livery's `feature.style`:
    `bar` (the title on a dark bar, the text on a translucent panel; the default) or
    `cover` (the title cover's field and waves, the photo beside them), in every format.
  - `## Title {.full}` gives one diagram or image the whole slide: no title,
    logo or rule, and the paragraph after it becomes a one-line caption. The
    title stays in the source for navigation and `make qa`. pptx gets it
    from `slide_layout.py`.
  - `## Thank you! {.closing}` makes a closing slide.
  - `### Heading {.example}` / `{.alert}` give block variants.
  - `[text]{.alert}` emphasizes text.
- **Dense slides**: beamer has no autofit; see [authoring.md "About text autofit"](authoring.md#about-text-autofit).

## HTML (revealjs)

`make html` renders with `--to engine-revealjs`, the web format from the same
extension. The deck looks like the PDF: title slide with the livery's
art (or `titlegraphic:`), section dividers with subtitles, content slides
with the livery's title and marks, `.feature` and `.closing` slides. The same
`themeoptions:` apply (`title=`, `waves=`; math in the browser is
MathJax's, so `mathfont=` does not). Open `<deck>.html` in a browser
and keep `<deck>_files/` beside it.

- **Presenting:** `s` speaker view (notes), `m` slide menu, `b`/`c`
  whiteboard / draw on the slide, `f` full screen.
- **HTML-only extras:**
  - `## Title {.brand-dark}` puts a content slide on the livery's dark color with
    white text (under a dark livery, every content slide already is); pptx and PDF
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
- **PDF from the browser:** open `<deck>.html?print-pdf` in Chrome and print
  with background graphics. `make pdf` is usually the better handout.
