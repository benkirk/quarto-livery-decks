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
copy). Phase 2 of that design is under way. Done: the rename, from
NCAR_beamer_template v2.8.0, to `_extensions/engine/`, the formats
`engine-beamer` / `engine-revealjs`, `\usetheme{Engine}`, `engine_livery.sty`
and the `engine@` namespace (brand things keep their names: the palette colors,
`brand=ncar|ucar|ncarucar`, `ncar-assets/`). Still to do: `livery=` with the
generated `build/livery.sty`, every color read moved to a role, geometry from
the livery, backgrounds from `art/`, the reference liveries under
`_extensions/engine/liveries/`.

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
