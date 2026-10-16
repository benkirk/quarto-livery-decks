# CLAUDE.md

Guidance for working in this repository. Keep it accurate.

## What this is

The **engine** of a multi-brand beamer + revealjs theme: the layout machinery
that is the same whoever's logo is on the slide, plus reference **liveries**
(brand data and assets per directory). It forks `benkirk/NCAR_beamer_template`,
which stays the NCAR theme for `\usetheme{NCAR}` users; fixes to the NCAR theme
land there first and are cherry-picked here (`upstream` remote), renaming the
nouns on the way.

The founding design is `docs/design/engine-and-liveries.md` (the engine
contract is its section 5; the progress log lives in the `quarto-livery-decks`
copy). Phase 2 of that design is under way. Done: the rename (from
NCAR_beamer_template v2.8.0) to `_extensions/engine/`, `engine-beamer` /
`engine-revealjs`, `\usetheme{Engine}` and the `engine@` namespace; and
`livery=`: the reference liveries live in `_extensions/engine/liveries/`
(`ncar`; `ucar` and `ncarucar` extend it), `livery_build.py` writes each one's
`build/livery.{json,sty,css}` (committed, `--check` in CI), `engine_livery.sty`
inputs the `.sty` and both Lua filters take the directory from the `livery:`
metadata key (else `liveries/<brand>`); and roles only: no palette name is
read outside `build/livery.sty`, the Sass sets every color as `var(--engine-*)`
(its `$ncar-*` variables are compile-time defaults for Quarto's own rules, which
are restated with the roles at the end of the file), and the highlight theme is
generated per livery from `engine.theme`. Still to do: geometry from the
livery, backgrounds from `art/`.

Checking a change: `tools/parity.sh baseline` on main, then `check` (every PDF
page's pixels, pdftotext, the HTML). HTML colors live in the compiled theme and
the livery's css, so a Sass change is checked by screenshotting every slide of
`talk-quarto.html` and `examples/quarto-demo.html` before and after (Playwright,
serve the repo root) and diffing the pixels above the progress bar.

The framework that consumes this engine is `benkirk/quarto-livery-decks`
(vendored there under `docs/common/_extensions/`; re-vendor with
`quarto update`).

## Build

- `make` → `talk.pdf` (XeLaTeX via latexmk); `make quarto` → `talk-quarto.pdf`;
  `make html` → `talk-quarto.html` and `examples/quarto-demo.html`;
  `make examples variants` → every example and brand/aspect/engine variant.
- LaTeX finds the theme through `TEXINPUTS=$THEME//:` and the bundled Poppins
  through `TTFONTS=$THEME//:` (`Makefile`; `latexmkrc` does the same for
  Overleaf). Quarto needs >= 1.6 (`\pandocbounded`).
- `make overleaf` builds `engine-beamer-overleaf.zip`. **Releases**: pushing a
  tag `v<version>` runs `release.yml`, which requires the tag to equal
  `version:` in `_extensions/engine/_extension.yml`. No tags were carried over
  from upstream; do not push upstream's tags here.
- Generated outputs (`*.pdf`, `*_files/`, `.quarto/`, the zip) stay untracked.

## CI

`.github/workflows/ci.yml` installs TeX Live, builds the starter decks, the
examples, the Overleaf zip (unpacked flat, no `TEXINPUTS`) and the HTML decks,
and checks Poppins is embedded and the math font is the serif one. The runner's
system Chrome can wedge quarto's mermaid handshake: keep the
`chrome-headless-shell` install step.

## Git

Default branch `main`; branch + PR to merge. Remotes: `origin` is this repo,
`upstream` is NCAR_beamer_template.
