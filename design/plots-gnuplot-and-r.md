# gnuplot and R from the livery

Two more drawers for the chart colors, explored 2026-10-24 with Ben: **gnuplot** as a small
addition to the base image, and **R** (ggplot2 through Quarto's knitr engine) as a derived image
built when someone asks for it. The principle is `design/charts-and-plots.md`'s: the livery is the
source and the engine generates every chart file at build time, beside `build/livery.{css,sty,
theme,mplstyle}`; a plotting tool gets one generated file and one small runtime helper, and
nothing else in the framework learns its name. Section 6 holds the steps; sections 2 to 5 the
facts and decisions they rest on. Issues: gnuplot #153, R #154.

## 1. Why

Plots are the one place an author's code meets the brand, and matplotlib proved the shape: a
style file the build writes (`emit_mplstyle()` in `livery_build.py`), an environment variable
`Make.common` exports (`MATPLOTLIBRC`), a helper that reads `build/livery.json` for what a style
file cannot hold (fonts, colormaps, `figsize()`, `dark()`), and text drawn as outlines so a figure
needs no font on the viewing machine (`svg.fonttype: path`, `pdf.fonttype` 42 or 3). Every
format then shows the plot at its natural canvas inches (`engine-plots.lua`) and the text measures
the slide's. gnuplot and ggplot2 have the same four hooks, under other names; the table in
section 3.2 and the list in section 4.2 are the whole of each port.

What the two share with matplotlib, and must keep sharing: `charts.<mode>` (categorical, families,
sequential, diverging, status, muted, surface), `charts.chrome.<mode>` (text, spine, grid),
`charts.figsize`, `typography.fonts` for the files and `type` for the points. A number drawn by
one tool and not the others is the drift the design rule forbids.

## 2. Facts (2026-10-24)

- **The image** (`Dockerfile`: `ubuntu:24.04`, apt TeX Live, LibreOffice Impress, ~200 MB of
  fonts, the conda env with Quarto and the matplotlib stack, one Playwright Chromium) is **8.2 GB
  on disk and 2.3 GB compressed** per platform (`docker images`; the merge job's step summary
  carries the compressed size). The repo sets no size budget; `image.yaml` waits for 15 GB of free
  disk before building and sizes its registry cache for "two ~4 GB platforms". Nothing in the tree
  mentions R, knitr, rmarkdown or gnuplot.
- **Fonts reach cairo already.** `Dockerfile` links `/usr/local/share/fonts/liveries` to the
  image's `liveries/`, so both fontconfigs (the system's, which cairo, Chromium and LibreOffice
  use, and the conda env's) index every livery's `fonts/`. gnuplot's cairo terminals and R's
  `ragg`/`systemfonts` find Poppins by name in the image with no work. A livery mounted from the
  host is not indexed (the same gap `make measure` has); a helper that names the files cures it
  (section 3.4).
- **gnuplot, the package.** conda-forge's `gnuplot` 6.0.5 is 1.2 MB but depends on `qt-main`
  (its interactive terminal), hundreds of MB the decks never draw. Ubuntu's `gnuplot-nox` (cairo,
  gd, lua; no Qt, no X) is about 10 MB installed: apt, in the toolchain block, not
  `conda-env.yaml`.
- **gnuplot, the hooks.** `set linetype N lc rgb '#…' lw …` and `set linetype cycle N` define the
  color sequence every `plot` walks; `set border`, `set tics textcolor`, `set grid` and `set key`
  take the chrome; `set termoption font "Family,pt"` the face and size. `load 'file'` searches
  `loadpath`, which `$GNUPLOT_LIB` extends (its documented purpose). The `svg` terminal writes
  text as text: a viewer without the face falls back silently. `pdfcairo` embeds the subset, and
  `pdftocairo -svg` (poppler-utils, in the image and the conda env) rewrites the PDF's glyphs as
  paths, the matplotlib `svg.fonttype: path` look. `gnuplot -d` skips the user's `~/.gnuplot`
  and `$XDG_CONFIG_HOME/gnuplot/gnuplotrc`, so a render is the same on every machine.
- **R, the package.** conda-forge's `r-base` 4.6.1 is 27 MB and depends on `gcc_impl`,
  `gfortran_impl` and `gxx_impl` (CRAN packages are built from source there): the compilers, not
  R, are the weight. Ubuntu's `r-base` with prebuilt `r-cran-*` binaries (noble's R 4.3.3, or r2u
  for current CRAN as apt packages) is a few hundred MB installed, 5 to 8 % of the image: apt,
  with no compiler.
- **R, the hooks.** Quarto's knitr engine needs `Rscript` on PATH and the `rmarkdown` package
  (knitr with it); a deck with `{r}` cells or `engine: knitr` runs through it, and the formats,
  filters and pptx steps see the same Figure the jupyter engine gives them. ggplot2: `theme_set()`
  for the chrome and sizes, `options(ggplot2.discrete.colour=, ggplot2.discrete.fill=)` for the
  cycle, `scale_*_gradientn()` for the ramps. Fonts: `systemfonts::register_font()` from files,
  `ragg` for raster, `svglite` for SVG (text as text), `showtext_auto()` to draw text as outlines
  in every device, matplotlib's path setting. `fig-format: svg` picks svglite when it is
  installed, `pdf` for beamer.
- **Running gnuplot in a deck.** Quarto has no gnuplot engine. The third-party `gnuplot_kernel`
  (0.4.1, on metakernel) exists but is dormant and would be a second kernel a deck cannot mix with
  Python. A `{bash}` cell writing a file and a `![](plot.svg)` works with no code, but a
  bash-kernel deck cannot also run Python. Ben's pick: a Python helper (section 3.3), so the
  plots deck mixes gnuplot and matplotlib slides.

## 3. gnuplot

### 3.1 Where it lives

`gnuplot-nox` in the Dockerfile's toolchain block (step 1), `gnuplot --version` in
`smoke-test.sh` beside `rsvg-convert`. Native users install it themselves (`brew install
gnuplot`, `conda install gnuplot` on a Mac is fine: the Qt weight is Linux's); the helper fails
with a plain message when it is missing, and `livery check` does not need it.

### 3.2 `build/livery.gp`, the emitter

`emit_gp(livery)` in `livery_build.py`, registered in `outputs()` beside `livery.mplstyle` and in
`livery.py deps`'s list (the two places the extensions are listed, plus the docstrings and
CLAUDE.md). It writes the livery's own mode as the defaults and the other mode as a macro, so a
dark slide is one `@livery_dark` after the load. Every value is a `livery.json` key:

| livery.json | livery.gp |
|---|---|
| `charts.<mode>.categorical[i]` | `set linetype i+1 lc rgb '#…' lw 2 pt 7 ps 0.8`; `set linetype cycle n` |
| `charts.chrome.<mode>.spine` | `set border lc rgb '#…' lw 0.8`; `set tics textcolor rgb <text>` |
| `charts.chrome.<mode>.grid` | `set grid lc rgb '#…' lw 0.5` |
| `charts.chrome.<mode>.text` | `set xlabel/ylabel/title/key textcolor rgb '#…'`; `set key noboxed top left` |
| `charts.<mode>.surface` | `set style fill solid border rgb <surface>` (bars' edges, as `patch.edgecolor`) |
| `charts.<mode>.status.*`, `muted` | string variables `livery_good`, `livery_warning`, `livery_serious`, `livery_critical`, `livery_muted` |
| `charts.<mode>.sequential[default-map]`, `diverging` | `set palette defined (…)` from the ramp's steps; `livery_div` as a macro |
| `typography.base` family, `type.roles.caption.pt` | `set termoption font "Poppins,10"` (the terminal's point size) |
| `charts.<mode>` for the other mode | macro `livery_dark` (or `livery_light`) restating the lines above |

No `set terminal`, `set output` or size in the file: the look is the livery's, the terminal is
the runner's, as `fig-format` is Quarto's and not the mplstyle's. `--check` compares it like the
others. The pgfplots cycle list in `livery.sty` is the model for the emitter's shape.

### 3.3 `livery_gp.py`, the runner

Beside `livery_mpl.py` in `_extensions/engine/mpl/` (on `PYTHONPATH` already; the directory's
name stays, the pip package may gain the module later). One call:

```python
#| include: false
import livery_gp
```
```python
livery_gp.plot("""
set xlabel 'Node count'; set ylabel 'Time to solution (s)'
plot 'data/scaling.tsv' using 1:2 with linespoints title 'MPAS-A'
""")
```

`plot(script, kind="full", height=1.0, dark=False)`:
1. finds the livery as `livery_mpl._find()` does (argument, `$LIVERY_DIR`, `_livery`) and reads
   `charts.figsize[kind]`, the content area in canvas inches;
2. writes a script: `load 'livery.gp'` (the build directory is `$GNUPLOT_LIB`, which `Make.common`
   exports; the helper sets it too when it is unset), `@livery_dark` when asked or when the
   format's slide is dark, `set terminal pdfcairo size <w>in,<h>in`, `set output '<tmp>.pdf'`,
   then the author's lines;
3. runs `gnuplot -d <script>`; an error is raised with gnuplot's message;
4. for `ENGINE_FORMAT=pdf` (beamer) returns the PDF as `IPython.display`'s `application/pdf`
   (Quarto's jupyter engine takes it, as matplotlib's pdf figures); for pptx and HTML runs
   `pdftocairo -svg` and returns `IPython.display.SVG`, the glyphs as paths (`svg_fallback.py`
   then makes the pptx's PNG with `rsvg-convert` as for any SVG plot).

`figsize()` and `output_format()` move to a tiny `livery_common.py` the two helpers import, or
`livery_gp` imports them from `livery_mpl` (which imports matplotlib: a cost the plots deck pays
anyway). Decide at implementation; the former if R's helper ever reads Python (it will not).

### 3.4 Fonts off the image

On a machine where the livery's family is not installed, cairo falls back by fontconfig's rules
and the SVG's outlines are the wrong face, silently (a Mac with Poppins installed hides the
miss, as `TTFONTS` does for TeX). The helper writes a `fonts.conf` beside its script that
`<include>`s the system configuration and adds `<dir>` for the livery's `fonts/` (its parent's
too, for a flavor; from `typography.fonts[].files[].path`), and runs gnuplot and `pdftocairo`
with `FONTCONFIG_FILE` set to it. The variable reaches only those two processes: Quarto's
Chromium and LibreOffice are untouched. A cache directory under `$XDG_CACHE_HOME` keeps the
rescan to the first call.

### 3.5 The deck and the tests

- One gnuplot slide in `decks/plots/plots.qmd` (a scaling curve from `data/`, the lines in the
  cycle; a second in a `.brand-dark` slide under `dark=True`), the README's table, `make
  gallery` there.
- `tests/test_charts.py`: `test_gp` builds the file for every livery and reads the hexes back;
  `test_gp_render` (skipped without gnuplot) draws a plot in each format and asserts the SVG has
  `<path` and no `<text`, the PDF's `pdffonts` the livery's family, the first line's `stroke` the
  first categorical color.
- `tests/test_cli.py`'s grep for the extension list; `test_schema.py` unchanged (no new key).
- The CHANGELOG under Plots; `decks/plots/README.md` and `design/charts-and-plots.md` section 6
  gain the file.

## 4. R

### 4.1 A derived image, `-r`

Ben's pick (2026-10-24): not the base image, not a second repository. `Dockerfile.r`:

```dockerfile
ARG BASE=ghcr.io/benkirk/quarto-livery-decks:latest
FROM ${BASE}
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
      r-base-core r-cran-ggplot2 r-cran-rmarkdown r-cran-knitr r-cran-ragg r-cran-svglite \
      r-cran-showtext r-cran-systemfonts r-cran-dplyr r-cran-tidyr r-cran-scales \
    && rm -rf /var/lib/apt/lists/*
```

(r2u's repository for current CRAN versions if noble's lag matters; `Rscript -e
'rmarkdown::pandoc_available()'` in the smoke test, with Quarto's own pandoc on PATH.) The
reusable `image.yaml` takes the Dockerfile and tag suffix as inputs, so `ci.yaml` calls it a
second time after the base manifest merges, with `BASE` the base's digest: tags `<ver>-r`,
`main-r`, `latest-r`, the same two platforms, the smoke test rendering a knitr deck. It rebuilds
when `Dockerfile.r` or the base changes. `DECKS_IMAGE_TAG=<ver>-r` selects it from a deck's
Makefile or `site.mk`; `common/image.mk` is unchanged. The devcontainer stays on the base.

The weight is not the bytes (5 to 8 %) but a second package world to keep current: the derived
image lets the base release alone and the `-r` tag lag or lead as its users need.

### 4.2 `build/livery.R`, the emitter

`emit_r(livery)` in `livery_build.py`, registered like `livery.gp`. It lands in the base repo and
sits inert until an R deck sources it; `--check` holds it current with the rest. Contents, every
value a `livery.json` key:

- `livery <- list(...)`: `colors` (categorical), `families`, `status`, `muted`, `surface`,
  `chrome`, `figsize`, `mode`, and the same for the other mode under `livery$dark`.
- `theme_livery(base_size = <body pt>)`: `theme_minimal()` with `text` in the base family and
  `chrome.text`, axis lines and ticks `chrome.spine` at 0.8, the grid `chrome.grid` at 0.5
  (major only), no panel or plot background (`fill = NA`: the plot sits on any field), legend
  without a box, titles `subhead` pt, axis text `levels[2]` pt, captions `caption` pt.
- `theme_set(theme_livery())`; `options(ggplot2.discrete.colour = livery$colors,
  ggplot2.discrete.fill = livery$colors)`; `scale_colour_livery_c()`/`scale_fill_livery_c()`
  over the default map's steps, `_div` over the diverging ramp, `scale_*_livery_seq("<name>")`.
- Fonts: `systemfonts::register_font()` from `typography.fonts[].files` with the paths resolved
  against the livery directory (the file's own `dirname`), `showtext::showtext_auto()` so every
  device outlines the text; `knitr::opts_chunk$set(fig.showtext = TRUE)`.
- `livery_dark()`: `theme_set()` with the dark chrome and the dark selections in the options,
  `livery_light()` back; a `.brand-dark` slide's cell calls it.
- `Sys.getenv("ENGINE_FORMAT")` for the one PDF difference matplotlib has: beamer's `fig-width`
  is paper inches, so under `pdf` the file sets `knitr::opts_chunk$set(fig.width=, fig.height=)`
  to `figsize.full`.

### 4.3 The deck's side

- `Make.common` exports `LIVERY_R := $(abspath $(LIVERY_DIR))/build/livery.R` beside
  `MATPLOTLIBRC`. A knitr deck's first chunk is `source(Sys.getenv("LIVERY_R"))`; a `.Rprofile`
  the Make writes was considered and dropped (it would shadow the author's and run for every
  `Rscript`). `FIG_SIZE` already reaches knitr as metadata.
- `common/_quarto.yml` is engine-agnostic (`fig-format` and `fig-dpi` per format); nothing
  changes. `svg_fallback.py` rasterizes svglite's SVG as any other.
- `decks/plots-r/plots-r.qmd` (`engine: knitr`), the plots deck's slides in ggplot2 where they
  translate (lines in the cycle, bars, a stacked area in `families`, a heatmap with the
  sequential map, a diverging field, two columns, a dark slide). It builds only where `Rscript`
  exists: its Makefile sets `DECKS_IMAGE_TAG` to the `-r` tag, and CI builds it in the `-r`
  image in a job of its own; the `livery` matrix stays on the base.
- `livery zip --charts` adds `livery.R` beside `livery.mplstyle` (the same fonts and `livery.json`
  are in the zip; the README gains the R lines).
- `tests/test_charts.py`: `test_r` builds the file and parses it (`Rscript` when present:
  `source()` it, print `livery$colors`, compare); the rest skipped without R.

## 5. Deferred, and why

- **R itself**, until a consumer asks (Ben, 2026-10-24: "someone might"). The emitter is cheap
  and may land with gnuplot's or on its own; the image, its CI leg and the deck wait.
- **`gnuplot_kernel`**: dormant, a second kernel. The helper covers it.
- **gnuplot's `svg` terminal** direct: text as text, so only in the image's HTML, where the css
  has the face anyway; `pdftocairo` costs one process and removes the font question everywhere.
- **A native PowerPoint chart** from a plot's data (a `c:chart` part): a different design, the
  `.crtx` note in `design/charts-and-plots.md` section 7.
- **A Plotly template or a Vega theme** from the same data: still "later and cheap".

## 6. Steps

**gnuplot, one PR** (the issue's list):
1. `gnuplot-nox` in `Dockerfile` step 1; `smoke-test.sh` asserts `gnuplot --version`.
2. `emit_gp()` and `outputs()`, the `deps` list, docstrings, CLAUDE.md; `livery build` for every
   livery (the generated files are committed, `--check` in CI).
3. `Make.common`: `export GNUPLOT_LIB`.
4. `livery_gp.py`: `plot()`, the fontconfig file, the format switch; `livery_mpl`'s `figsize()`
   and `output_format()` shared.
5. The plots deck's slides, README, gallery; tests; CHANGELOG; `design/charts-and-plots.md`
   section 6's list.
6. `tests/parity.sh` before and after (the plots deck's other slides must not move).

**R, when asked, two PRs**: (a) `emit_r()`, `LIVERY_R`, the charts zip, its test; (b)
`Dockerfile.r`, the second `image.yaml` call and tags, `decks/plots-r`, its CI job,
docs/container.md's "R" section and docs/other-repos.md's tag note.

## Sources

- gnuplot 6 documentation: startup files and `loadpath`/`GNUPLOT_LIB`
  (https://gnuplot.sourceforge.net/docs_6.1/loc4570.html), `set linetype`, `set termoption`.
- conda-forge package metadata for `gnuplot`, `r-base`, `r-ggplot2`, `r-rmarkdown`, `r-ragg`,
  `r-showtext` (`conda search --info`, 2026-10-24).
- Quarto: the knitr engine (https://quarto.org/docs/computations/r.html), rendering script files.
- `gnuplot_kernel` (https://github.com/has2k1/gnuplot_kernel), 0.4.1.
- r2u, CRAN as Ubuntu binaries (https://eddelbuettel.github.io/r2u/).
