# quarto-livery-decks

A [Quarto](https://quarto.org) framework for documentation decks in any brand: one Markdown
file becomes a branded PowerPoint (`.pptx`, the first-class output), a revealjs HTML deck and
a beamer PDF. The brand is a **livery**, a directory of data and assets, and
`make pptx LIVERY=cu` is the whole switch. Three brand families ship here: NCAR, the
University of Colorado and NASA ("The liveries" below). Clone, set up the conda env, copy the
quickstart deck, write Markdown. What each release changed is in [`CHANGELOG.md`](CHANGELOG.md).

![Four slides of the quickstart deck: the title slide, the MPAS-A governing equations, a two-column slide with a table, and a mermaid diagram](decks/quickstart/screenshots/hero.png)

The same quickstart deck under each livery (title, divider, content, closing):

![The quickstart deck under the ncar, cu, nsi, nasa, nasa-dark and nasa-jsc-eg liveries](decks/quickstart/screenshots/liveries.png)

Two example decks ship with the framework:

- **`decks/quickstart/`** is thirteen slides, one of each headline feature. It is the deck to
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

Open `quickstart.pptx` (or `quickstart.html` in a browser), then copy `quickstart.qmd` into a
new deck directory and edit it ([docs/authoring.md "Adding a new deck"](docs/authoring.md#adding-a-new-deck)).
When you need a pattern the quickstart deck lacks, `decks/sample/sample.qmd` probably has it.

**Behind a restrictive proxy** (some cloud containers): if `quarto install
tinytex` cannot download, a system TeX Live works instead (`apt-get install
texlive-xetex texlive-latex-extra texlive-fonts-extra`). If `quarto install
chrome-headless-shell` cannot download, point Quarto at any Chromium with
`export QUARTO_CHROMIUM=/path/to/chrome`, and `make qa` at it with `CHROME`.

**No conda at hand?** With Docker, Podman or Apptainer installed, the same `make pptx` builds in
the published image, which carries the whole environment: a deck's make runs the container
itself when `quarto` is not on your PATH, or when `DECKS_RUNTIME` says so
([docs/container.md "From your deck's Makefile"](docs/container.md#from-your-decks-makefile)).
A directory of `.qmd` files with no Makefile builds with `docker run` alone
([`docs/container.md`](docs/container.md)).

**Nothing to install at all?** [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/benkirk/quarto-livery-decks?quickstart=1)
opens the repository in GitHub Codespaces on the same image, VS Code in the browser or
`gh codespace ssh` from your laptop, inside a personal account's free quota
([docs/container.md "In GitHub Codespaces"](docs/container.md#in-github-codespaces)).
A repository of your own decks can build them on every push instead
([docs/other-repos.md "Building in GitHub Actions"](docs/other-repos.md#building-in-github-actions)).

## What you get

Every slide of `decks/quickstart/quickstart.qmd`, in the HTML deck under the default `ncar`
livery:

![All thirteen slides of the quickstart deck in the HTML format](decks/quickstart/screenshots/overview.png)

| Slide | The Markdown behind it |
|---|---|
| [Title](decks/quickstart/screenshots/01-title.png) | the front matter: `title`, `subtitle`, `author`, `date`; the photo is the livery's default, `titlegraphic:` sets your own |
| [Section divider](decks/quickstart/screenshots/02-divider.png) | `# Write Markdown`, then a paragraph: the subtitle |
| [Bullets and a footnote](decks/quickstart/screenshots/03-text.png) | a list, then a paragraph starting with `†`; `{.vcenter scale="1.2"}` on the heading |
| [Columns](decks/quickstart/screenshots/04-columns.png) | `:::: {.columns}` with a list in one `.column` and a table in the other |
| [Cards](decks/quickstart/screenshots/12-cards.png) | `.card` on each `.column`: a `###` title, a `[...]{.sub}` line, a `[...]{.label}`, a `[...]{.big}` number, `- [x]`/`- [-]`/`- [!]` status items; `.pick` outlines one |
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
above) and `make gallery` (the livery rows); both need everything `make qa` does
([docs/authoring.md "Checking a deck"](docs/authoring.md#checking-a-deck)).

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
| **NASA** | `nasa` (external communication, on white); `nasa-dark` (`extends: nasa`, on black); `nasa-jsc-eg`, the JSC Aeroscience and Flight Mechanics Division's template (`extends: nasa-dark`); program liveries belong here too | NASA's digital faces, bundled: Inter headings, Public Sans body, DM Mono code; `nasa-jsc-eg`: Arial, Liberation Sans standing in | the insignia top right and the agency name at the foot, the brand's preferred identifier; `nasa-jsc-eg`: the division bar at the foot, the division and group patches on the cover | NASA Blue fields with the white-rule insignia; `nasa-dark`: content on black over a faint deep field, cover and closing on black; `nasa-jsc-eg`: a starfield, the yellow cover band and lab photo |

`make <format> LIVERY=<name>` picks one of `liveries/` (`ncar` is the default);
`LIVERY_DIR=<path>` takes a livery from anywhere (a repo's own, say). Each livery's
`reference/notes.md` records its sources and every judgement call, and CI builds the
quickstart deck under each one.

## Adding a livery

A livery is a brand as a directory of data and assets, made and checked with the `livery`
command: `livery new`, edit, `make livery LIVERY=<name>`, look. [`liveries/README.md`](liveries/README.md)
walks through it; [`liveries/REFERENCE.md`](liveries/REFERENCE.md) is every `livery.yml` key.

## Where next

| You want to | Read |
|---|---|
| write a deck: a new directory, the front matter and slide kinds, linked images, centering and scaling a slide, shell chunks, text sizes, `make qa` | [`docs/authoring.md`](docs/authoring.md) |
| know what each format does: the layout tree, the build pipeline, the fonts, the template's constraints, what is beamer's and what is revealjs's | [`docs/formats.md`](docs/formats.md) |
| put a plot on a slide in the livery's colors | [`decks/plots/README.md`](decks/plots/README.md) |
| make or change a livery | [`liveries/README.md`](liveries/README.md), [`liveries/REFERENCE.md`](liveries/REFERENCE.md) |
| write slides in LaTeX, on Overleaf or with XeLaTeX alone | [`latex/README.md`](latex/README.md) |
| build with Docker, Podman or Apptainer, nothing installed | [`docs/container.md`](docs/container.md) |
| build in GitHub Codespaces, nothing installed at all | [docs/container.md "In GitHub Codespaces"](docs/container.md#in-github-codespaces) |
| keep your decks in another repository, build them on every push, or publish the HTML decks | [`docs/other-repos.md`](docs/other-repos.md) |
| see what changed in a release | [`CHANGELOG.md`](CHANGELOG.md) |
| see how the engine and the liveries are designed | [`design/engine-and-liveries.md`](design/engine-and-liveries.md) |

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
