# quarto-livery-decks

A [Quarto](https://quarto.org) framework for documentation decks in any brand: one Markdown
file becomes a branded PowerPoint (`.pptx`, the first-class output), a revealjs HTML deck and
a beamer PDF. The brand is a **livery**, a directory of data and assets, and
`make pptx LIVERY=cu` is the whole switch. Three brand families ship here: NCAR, the
University of Colorado and NASA ("The liveries" below). Clone, set up the conda env, copy the
quickstart deck, write Markdown. What each release changed is in [`CHANGELOG.md`](CHANGELOG.md).

![Four slides of the quickstart deck: the title slide, the MPAS-A governing equations, a two-column slide with a table, and a mermaid diagram](decks/quickstart/screenshots/hero.png)

The same quickstart deck under each livery (title, divider, content, closing):

![The quickstart deck under the ncar, cu, nsi, nasa and nasa-dark liveries](decks/quickstart/screenshots/liveries.png)

Two example decks ship with the framework:

- **`decks/quickstart/`** is twelve slides, one of each headline feature. It is the deck to
  copy when you start your own (see "What you get" below).
- **`decks/sample/`** is a **cookbook** showing one example of every capability you're
  likely to need: text formatting, math, tables, two-column layouts, image embeds,
  syntax-highlighted code, auto-captured shell output, mermaid and Graphviz diagrams,
  speaker notes, and the `{{< include >}}` shortcode. `decks/sample/old.qmd` is a longer
  real-world example (database schema, REST API and deployment diagrams).

## Quick start

```bash
git clone https://github.com/benkirk/quarto-livery-decks.git
cd quarto-livery-decks

# 1. Build the conda env (also installs + registers the bash Jupyter
#    kernel so executable {bash} chunks work).
make conda-env
conda activate ./conda-env

# 2. Render the quickstart deck.
cd decks/quickstart
make pptx              # → quickstart.pptx (the default livery, ncar)
make html              # → quickstart.html (revealjs)
make pdf               # → quickstart.pdf  (beamer; needs TeX)
make pptx LIVERY=cu    # the same deck in another livery (any directory under liveries/)
```

Open `quickstart.pptx` (or `quickstart.html` in a browser), then copy
`quickstart.qmd` into a new deck directory and edit it (see "Adding a new deck"
below). When you need a pattern the quickstart deck lacks, `decks/sample/sample.qmd`
probably has it.

**Behind a restrictive proxy** (some cloud containers): if `quarto install
tinytex` cannot download, a system TeX Live works instead (`apt-get install
texlive-xetex texlive-latex-extra texlive-fonts-extra`). If `quarto install
chrome-headless-shell` cannot download, point Quarto at any Chromium with
`export QUARTO_CHROMIUM=/path/to/chrome`, and `make qa` at it with `CHROME`.

**No conda at hand?** The published image carries the whole environment:
`docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work/decks/quickstart
ghcr.io/benkirk/quarto-livery-decks make pptx` builds the quickstart deck, and any
directory of `.qmd` files mounted on `/work` builds the same way
([`docs/container.md`](docs/container.md)).

## What you get

Every slide of `decks/quickstart/quickstart.qmd`, in the HTML deck under the default `ncar`
livery:

![All twelve slides of the quickstart deck in the HTML format](decks/quickstart/screenshots/overview.png)

| Slide | The Markdown behind it |
|---|---|
| [Title](decks/quickstart/screenshots/01-title.png) | the front matter: `title`, `subtitle`, `author`, `date`; the photo is the livery's default, `titlegraphic:` sets your own |
| [Section divider](decks/quickstart/screenshots/02-divider.png) | `# Write Markdown`, then a paragraph: the subtitle |
| [Bullets and a footnote](decks/quickstart/screenshots/03-text.png) | a list, then a paragraph starting with `†`; `{.vcenter scale="1.2"}` on the heading |
| [Columns](decks/quickstart/screenshots/04-columns.png) | `:::: {.columns}` with a list in one `.column` and a table in the other |
| [Equations](decks/quickstart/screenshots/05-math.png) | LaTeX between `$$`: OMML in pptx, MathJax in HTML, real TeX in the PDF |
| [Code, static and live](decks/quickstart/screenshots/06-code.png) | a ` ```bash ` block, and a ` ```{bash} ` cell run at render time |
| [Diagram](decks/quickstart/screenshots/07-mermaid.png) | a ` ```{mermaid} ` cell (Graphviz ` ```{dot} ` works the same way) |
| [Photo slide](decks/quickstart/screenshots/08-feature.png) | `{.feature background-image="..."}`, the text in a `###` block |
| [Full-slide diagram](decks/quickstart/screenshots/09-full.png) | `{.full}` on the heading: one diagram or image, then an optional caption paragraph |
| [Short slide](decks/quickstart/screenshots/10-short.png) | `{.center scale="1.4"}` on the heading |
| [Closing](decks/quickstart/screenshots/11-closing.png) | `## Thank you! {.closing}` |

The same source as a beamer PDF (`make pdf`):

![Four pages of the quickstart deck as a beamer PDF](decks/quickstart/screenshots/pdf.png)

The pptx is the same deck again, on the livery's PowerPoint template. To refresh these
images after editing the deck, run `make screenshots` in `decks/quickstart/` (the shots
above) and `make gallery` (the livery rows); both need everything `make qa` does (see
"Checking a deck").

## The liveries

A livery is a brand as data: a palette and fonts (`_brand.yml`, Quarto's brand.yml
standard), the engine's knobs (`livery.yml`: roles, geometry, marks, art, type sizes), and
its fonts, logos and pictures. From that one directory the engine draws the HTML and PDF
themes and generates the PowerPoint template, so the three formats wear the same brand. A
livery can be a *flavor* of another (`extends:`), naming only what differs.

| Family | Liveries | Faces | Marks | Look |
|---|---|---|---|---|
| **NCAR** | `ncar` (NSF NCAR, the default); `ucar`, `ucp` and `ncarucar`, the brand guide's other lockups | Poppins, bundled, embedded in the pptx | each member's lockup top right | the 2026 brand palette; deep-blue fields and the wave super-graphic; the Mesa Lab on the cover |
| **University of Colorado** | `cu` (CU Boulder); `nsi`, the Center for National Security Initiatives (`extends: cu`) | Helvetica Neue where installed; TeX Gyre Heros, Condensed for headings, standing in | `cu`: the CU Boulder lockup as a sign-off, bottom left; `nsi`: the center's mark top left, the Research & Innovation Office lockup as its sign-off | gold fields, a faded Flatirons photo behind content; `nsi`: its master deck's band title, a satellite photo behind content, centred titles |
| **NASA** | `nasa` (external communication, on white); `nasa-dark` (`extends: nasa`, on black); program liveries belong here too | NASA's digital faces, bundled: Inter headings, Public Sans body, DM Mono code | the insignia top right and the agency name at the foot, the brand's preferred identifier | NASA Blue fields with the white-rule insignia; `nasa-dark`: content on black over a faint deep field, cover and closing on black |

`make <format> LIVERY=<name>` picks one of `liveries/` (`ncar` is the default);
`LIVERY_DIR=<path>` takes a livery from anywhere (a repo's own, say). Each livery's
`reference/notes.md` records its sources and every judgement call, and CI builds the
quickstart deck under each one.

## Text sizes and the slide size

Each livery states its text sizes in whole or half points on its PowerPoint canvas, from the
brand's own template or deck. ncar uses the NSF NCAR template's 10 x 5.625 in slide, with a 12 pt
body, 12/11/10/9/8 pt list levels, 20 pt slide titles and a 22 pt cover title. cu and nsi use
the NSI deck's 13.33 x 7.5 in slide, with a 16 pt body, 32 pt titles and 60 pt dividers. nasa
and nasa-dark use the NASA Science public-engagement deck's 10 x 5.625 in slide, with a 12 pt
body and 22 pt titles. So a slide copied from a built pptx into a hand-made deck on that
template keeps its geometry and its round sizes. HTML and PDF set the same sizes as the same
share of the slide, so a slide fits, or overflows, alike in all three. `scale="S"` on a slide
sizes it in every format, and PowerPoint's sizes round to the half point.

A whole deck can step its sizes down (or up) from the livery's, in all three formats:

```yaml
type-body: 10      # the body in points; every size scales by 10/12 under ncar
# type-scale: 0.85 # or a plain factor (type-body wins if both are set)
```

The NSF NCAR guide's "10 pts for three and four column layouts" is `type-body: 10`. PowerPoint
gets every size rounded to the half point (`type_step.py`), and a slide's `scale=` multiplies
on top. In plain LaTeX or Overleaf, the theme option `typescale=0.85` does the same. A livery's
sizes live in its `livery.yml` (`type:`, `pptx.size`; `livery_build.py`'s `TYPE` lists the roles).

## About text autofit

Pandoc's PPTX writer emits empty `<a:bodyPr/>` on every placeholder,
which corresponds to PowerPoint's "Do not Autofit": long text overflows
the placeholder visually. `enable_autofit.py` rewrites these to
`<a:bodyPr><a:normAutofit/></a:bodyPr>`, which sets the dropdown to
"Shrink text on overflow."

PowerPoint computes the actual `fontScale` only on edit, not on load, so the file opens with
overflowing text; a click into any overflowing cell triggers the recompute and the text
shrinks permanently. Author-side discipline (split walls of text, use columns) beats driving
PowerPoint externally, so nothing is wired up for that.

The HTML deck fits itself: a content slide that runs past the bottom margin
shrinks its body text (down to 65%) until it fits, keeping the title size.
`{.smaller}` sets a slide smaller from the start:

```markdown
## Wall of text {.smaller}
```

PPTX silently ignores `{.smaller}`; revealjs honors it. Opt a slide out of
the HTML autofit with `{.no-autofit}` (or `{.scrollable}`), or a whole deck
with `themeoptions: [autofit=false]`. Beamer never shrinks overflowing text: add
`{.shrink}` to a dense slide's heading to scale that one slide down (pptx ignores the
class), or check it with `make qa`.


## Checking a deck

`make qa` builds every format, then checks the outputs (`common/utils/deck_qa.py`):

- **Failures:**
  - slide counts that differ between pptx, PDF and HTML;
  - PDF text past the right margin, into the footer, overlapping other text, or running into
    the next table column;
  - HTML content past the right edge;
  - a bare `<word>` in the sources, outside code and backticks: revealjs reads it as a tag
    (reported as `file:line`).
- **Hints:**
  - short slides, with the share of the body they use;
  - `.smaller` without `.fill`;
  - slides the HTML autofit had to shrink.
- **Plain names:** list names that belong in backticks in `qa-names.txt` (one per line) in
  the deck directory, and every plain-text use is reported.

Everything lands in `_qa/` (gitignored): `report.txt`, `usage.tsv`, a contact sheet per
format, and per-slide PNGs. In a directory with several decks, `make qa DECKS=name`
checks one.

`make measure` checks the slides a livery composes, the title, divider, feature and closing
slides, against their **compositions**: the boxes in the livery's `build/livery.json` that
say where each one's field, photo, marks and text go, which every format draws from. It
shoots those slides in all three formats, measures every edge against its box and writes
`_qa/measure.tsv` and a contact sheet, `_qa/compositions-<livery>.png`; `MEASURE_FAIL` names
the formats whose misses fail the run.

The checks need poppler, Pillow and Playwright, which are all in `conda-env.yaml`
(`make measure` also LibreOffice, to shoot the pptx). `make conda-env` installs Playwright's
headless Chromium; set `CHROME` to use another build. Without Playwright the HTML checks are
skipped and the rest run. For Claude Code, the `deck-polish` skill (`.claude/skills/`)
covers what to do with the findings.

## Adding a new deck

```bash
cd decks
mkdir roadmap && cd roadmap

cat > Makefile <<'EOF'
include ../../Make.common
EOF

# then author roadmap.qmd. _quarto.yml is auto-symlinked from
# ../../common/_quarto.yml on first `make` invocation.
make pptx
```

`Make.common` infers the deck name from `$(notdir $(CURDIR))`, so the
output file is `<dirname>.pptx`. Override with `OUT=foo` if needed.

A directory can hold several decks that share images and fragments, e.g. a
full deck plus one deck per part:

```make
DECKS := roadmap 1-intro 2-details
include ../../Make.common
```

Each `<name>.qmd` builds `<name>.pptx` / `.html` / `.pdf`, and `make pptx`
builds all of them. Put shared slide bodies in `_*.qmd` fragments and pull
them in with `{{< include _1-intro.qmd >}}`; quarto skips underscore files
when rendering, and make treats every `_*.qmd` and `data/*` in the directory
as a prerequisite of every deck, so editing one rebuilds them all.

A deck that needs custom Quarto config (a different reference template,
extra extensions, etc.) can replace the symlinked `_quarto.yml` with a
real file: `make` sees the file already exists and skips the symlink
recipe.

### Linked images

Wrap an image in a link and the picture opens that page, in every format:

```markdown
[![](images/dashboard.png){height="72%" fig-align="center"}](https://example.org/dashboard)
```

Each format also shows the URL, small and muted, so a reader knows the
picture is live: the slide footer in HTML, a line at the foot of the PDF page
(the engine's `linked-images.lua`), and a caption box in pptx (`link_captions.py`;
pandoc can't add one without splitting the slide). One line per slide, from
its first linked image. `{height="72%"}` is the full-width screenshot recipe
and fits all three.

### Centering and scaling a short slide

Six per-slide controls on the heading, each independent, act on the body
(everything but the title, speaker notes and footnotes). The engine's themes draw them
in HTML and PDF; pptx gets them through `slide_layout.py` (step 7 of
[docs/formats.md "Build pipeline"](docs/formats.md#build-pipeline)).

```markdown
## Who's still on legacy {.center scale="1.4"}
## A short script {.hcenter .fill}
```

| Control | HTML | PDF | pptx |
|---|---|---|---|
| `.hcenter`: center the body across as a block | yes | prose, lists, plain code (a table centers anyway) | no |
| `.vcenter`: center it between the title and the floor | yes | yes | text yes; a table to its measured center |
| `.center`: both (the theme's, not Quarto's) | yes | yes | as `.vcenter` |
| `scale="S"`: text, tables and code × S | yes (autofit shrinks an overshoot) | yes (no autofit: check the page) | yes |
| `.fill`: grow until it just fits, up to 3× | yes | no; add `scale=` | no; add `scale=` |
| `.caution`: the body on a soft field with a bar in the warning color, for warning slides | yes | yes | yes; the box cut to its measured text, footnotes inside it |

### Executable shell chunks

Quarto can capture the live output of a shell command at render time:

````markdown
```{bash}
#| echo: true
which mpicxx && mpicxx --version
```
````

Both the command and its captured stdout land on the slide. This needs
the Jupyter `bash` kernel, which `make conda-env` installs and registers
into the env (`bash_kernel` pip package + `python -m bash_kernel.install
--sys-prefix`). The deck's frontmatter must opt in:

```yaml
engine: jupyter
jupyter: bash
```

Code runs on the build host, not the viewer's machine: output is baked
into the .pptx.

## Adding a livery

A livery is a brand as a directory of data and assets, made and checked with the `livery`
command: `livery new`, edit, `make livery LIVERY=<name>`, look. [`liveries/README.md`](liveries/README.md)
walks through it; [`liveries/REFERENCE.md`](liveries/REFERENCE.md) is every `livery.yml` key.

## License

Copyright © 2026 University Corporation for Atmospheric Research.

The framework, its engine, its tools and the example decks are licensed under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (Creative
Commons Attribution-ShareAlike 4.0 International); the full text is in
[`LICENSE.txt`](LICENSE.txt). You may share and adapt them with attribution,
provided you distribute your changes under the same license. They are freely
available to anyone who wants to build decks, or a livery, of their own.

**Each livery's marks and pictures belong to their owner** and are not covered by that
license:

- **The NSF, NCAR, UCAR and UCP logos and brand marks** (`liveries/ncar/`,
  `ucar/`, `ucp/` and `ncarucar/`) are trademarks used under the
  [UCAR brand guidelines](https://ucar.canto.com/v/branding); the NCAR family's cover photo
  of the Mesa Lab is NCAR's.
- **The CU Boulder lockups, the NSI and Research & Innovation Office lockups, and the
  photographs** of the `cu` and `nsi` liveries are the University of Colorado's and its
  units', reproduced here as the livery's reference assets; see each livery's
  `reference/notes.md` for their sources.
- **The NASA insignia** (`liveries/nasa/logos/`) is NASA's; it is not in the
  public domain and its use is restricted by the
  [NASA brand guidelines](https://www.nasa.gov/nasa-brand-center/brand-guidelines/). The
  `nasa` liveries' photographs are NASA's (images.nasa.gov); see their `reference/notes.md`.
- **The Poppins font** (`liveries/ncar/fonts/`)
  is licensed under the [SIL Open Font License](https://openfontlicense.org); **TeX Gyre
  Heros** (`liveries/cu/fonts/`) under the GUST Font License; **Inter, Public
  Sans and DM Mono** (`liveries/nasa/fonts/`) under the SIL Open Font License.
- **The photographs in `latex/images/wallpaper/`** come from the NCAR beamer template
  as example imagery for the LaTeX examples. Replace them with your own.

## Origins

This framework generalizes [`benkirk/quarto-docs-framework`](https://github.com/benkirk/quarto-docs-framework),
which remains NCAR's single-brand deck framework, to any brand through liveries. Its engine
generalizes [`benkirk/NCAR_beamer_template`](https://github.com/benkirk/NCAR_beamer_template),
which remains the single-brand NCAR beamer theme (a fix wanted from it is ported by hand). The
engine was [`benkirk/beamer-livery-theme`](https://github.com/benkirk/beamer-livery-theme) until
2026-10, when it merged into this repository with its history (#57). The design
is [`design/engine-and-liveries.md`](design/engine-and-liveries.md).
