# CLAUDE.md

Guidance for working in this repository. Keep it accurate.

## What this is

The **engine** of a multi-brand beamer + revealjs theme: the layout machinery
that is the same whoever's logo is on the slide, plus reference **liveries**
(brand data and assets per directory). It forks `benkirk/NCAR_beamer_template`,
which stays the NCAR theme for `\usetheme{NCAR}` users; fixes to the NCAR theme
land there first and are cherry-picked here (`upstream` remote) until Phase 2.

The founding design is `docs/design/engine-and-liveries.md` (the engine
contract is its section 5; the progress log lives in the `quarto-livery-decks`
copy). **Until Phase 2 of that design lands, this repo is byte-identical to
NCAR_beamer_template v2.8.0**: the extension is still `_extensions/ncar/`, the
formats `ncar-beamer` / `ncar-revealjs`, the theme `\usetheme{NCAR}`. Phase 2
renames them to `_extensions/engine/`, `engine-beamer` / `engine-revealjs` and
`\usetheme[livery=<dir>]{Engine}` with `engine_livery.sty`, moves every color
read to a role, takes geometry from the livery and backgrounds from `art/`.

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
- `make overleaf` builds `ncar-beamer-overleaf.zip`. **Releases**: pushing a
  tag `v<version>` runs `release.yml`, which requires the tag to equal
  `version:` in `_extensions/ncar/_extension.yml`. No tags were carried over
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
