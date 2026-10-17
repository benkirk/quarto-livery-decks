# CLAUDE.md

Guidance for working in this repository. Keep it accurate.

## What this is

The **engine** of a multi-brand beamer + revealjs theme: the layout machinery that is
the same whoever's logo is on the slide, plus reference **liveries** (brand data and
assets per directory). It forks `benkirk/NCAR_beamer_template`, which stays the NCAR
theme for `\usetheme{NCAR}` users; fixes to the NCAR theme land there first and are
cherry-picked here (`upstream` remote), renaming the nouns on the way. The design is
`docs/design/engine-and-liveries.md` in `benkirk/quarto-livery-decks` (the framework
that consumes this engine, vendored there under `docs/common/_extensions/`; the copy
here is a pointer); its section 5 is the engine contract, section 10 the progress log.
Phases 1 and 2 are complete, Phase 3 (templates and new brands) is under way. What the
engine does today, by area:

- **Names**: `_extensions/engine/`, the formats `engine-beamer` / `engine-revealjs`,
  `\usetheme{Engine}`, the `engine@` namespace (renamed from NCAR_beamer_template v2.8.0).
- **Liveries**: `_extensions/engine/liveries/` holds `ncar`, `ucar` and `ncarucar` (which
  extend it) and `ucp` (extends ucar). `livery_build.py` writes each one's
  `build/livery.{json,sty,css,theme}` (committed; `--check` in CI; an unknown `livery.yml`
  key is warned about, `KNOWN`). `engine_livery.sty` inputs the `.sty`; both Lua filters
  take the directory from the `livery:` metadata key, else `liveries/<brand>`.
- **Roles only**: no palette name is read outside `build/livery.sty`; the Sass sets every
  color as `var(--engine-*)` (its `$ncar-*` variables are compile-time defaults for Quarto's
  own rules, restated with the roles at the end of the file); the highlight theme is
  generated per livery from `engine.theme`.
- **Geometry**: margin, tab, logo box (height per slide kind, top, aspect, corner on content
  slides: top-right, top-left, none), the page number's corner, divider block and
  full-figure lengths are the livery's `geometry` fractions: `engine@geom@*` in the `.sty`,
  `--engine-*` pixels in the css (ncar's are the HTML/PDF numbers, not the pptx template's
  tighter ones). `signoff`: a second lockup at the foot (light/dark images, aspect, height,
  bottom, corner), on every slide but feature and full, the dark variant on fields.
- **Art**: `art.waves` (control points and per-kind shifts, drawn by the engine in the
  roles' colors; the pptx divider layout from the same numbers); a livery without them
  draws plain fields, or names a static picture per slide kind
  (`art.title|section|closing|content`), and `art.titlegraphic` is the default title photo.
- **Title styles**: `title.style` is `cover` (default) or `band` (`title: {style: band, top,
  bottom, split, band, field, field-text, logo-height, signoff-height}`: a field in a role
  with `art.title` over it, a band holding the text left of `split` and the photo right of
  it, the mark and sign-off centred in the strip below; the closing slide wears the field,
  `art.closing` or the title's art, and the strip's images; CU NSI uses it). `title=light`
  follows the brand's own light cover (UCAR Communications' template, slide 4): white
  field, text in the foreground role, the wave lines alone.
- **Compositions** (3.5.0): `livery_build.py compositions()` writes the title (`title`,
  `title-photo`, `title-light`, `title-photo-light`, `title-band`), closing (`closing`,
  `closing-light`, `closing-band`), `section` and `feature` slides into `livery.json` as boxes
  (`[x, y, w, h]` slide fractions, y down; every key present, null when absent), derived from the
  knobs; `livery.yml` `compositions:` overrides (one on `title` reaches its variants) and
  `feature.style` (bar | cover) picks the feature look. One drawer per format: beamer
  `\engine@drawcomp` (`\engine@c@<comp>@<key>@*` macros), revealjs the `--engine-cmp-*`
  properties per composition selector and `comp_art()`, the template builder `field_layout()`
  (with `pptx_waves.comp_shapes`). `tools/test_compositions.py` (CI) restates 3.4.0's HTML numbers
  and the decided changes (`EXPECTED_DELTAS`); a changed box is named there or fails.
- **Type** (3.5.0): `livery_build.py` `TYPE`, the body as a fraction of the slide height (0.0311:
  HTML's 28 px of 900, the brand template's 12 pt of 405) and each text role's size and leading
  as a ratio to it (HTML's em sizes), in `livery.json` `type` and `\engine@type@*`. beamer
  rescales LaTeX's size commands onto it (whatever the class's size option) and sets each font
  role, code, tables and list spacing from it; the template builder derives the master's ladder
  and the placeholders' sizes; `livery.type_pt()` gives a role in points. So text sits as large
  on the slide in every format, and they fit and overflow alike. HTML is the reference: change a
  size there and in `TYPE` together.
- **Marks by field** (3.3.0): `marks: {<role>: {logo, signoff}}`; content slides wear
  `background`'s, dividers, the cover title, closing and feature covers `primary`'s, the band
  title and closing `title.field`'s. `livery_build.py` writes `marks` for every livery
  (`background` defaults to `logo.medium.light` and `signoff.light`, `primary` to the dark
  ones, any other role to primary's; `title.logo`/`title.signoff` are deprecated aliases).
- **Fonts**: `installed-fonts` names installed faces that `fonts=brand` and the css
  `local()` sources prefer over the bundled files; `fonts=bundled` never probes.
- **Templates** (Phase 3): each livery's `template.pptx` is generated by
  `livery_template.py` from its data (never by hand; `livery_check.py` fails one that does
  not rebuild byte-identically, in CI too), with `Closing` and `Title Slide (light)` layouts
  pandoc never picks and the framework's `slide_layout.py` points slides at; the theme1.xml
  slots follow the roles (`SLOT_ROLES`); the web logos are the brand kit's RGB PNGs (Canto;
  see each livery's `reference/notes.md`). The framework loads `livery.py` and
  `pptx_waves.py` from the vendored copy.
- **Overleaf** (3.4.0): `overleaf_zip.py` packs any livery with the theme's `.sty` and the
  starter (`_extensions/engine/talk.tex`, linked at the root) as a pure-XeLaTeX project.

Checking a change: `tools/parity.sh baseline` on main, then `check` (every PDF
page's pixels, pdftotext, the HTML). HTML colors live in the compiled theme and
the livery's css, so a Sass change is checked by screenshotting every slide of
`talk-quarto.html` and `examples/quarto-demo.html` before and after (Playwright,
serve the repo root) and diffing the pixels above the progress bar.

## Build

- `make` → `talk.pdf` (XeLaTeX via latexmk); `make quarto` → `talk-quarto.pdf`;
  `make html` → `talk-quarto.html` and `examples/quarto-demo.html`;
  `make examples variants` → every example and brand/aspect/engine variant.
- LaTeX finds the theme through `TEXINPUTS=$THEME//:` and the bundled Poppins
  through `TTFONTS=$THEME//:` (`Makefile`; `latexmkrc` does the same for
  Overleaf). Quarto needs >= 1.6 (`\pandocbounded`).
- `make overleaf` builds `engine-beamer-overleaf.zip` with `overleaf_zip.py <livery> -o <zip>
  [--starter] [--photo]` (the theme's `.sty`, the livery's `build/livery.sty`, fonts, logos and
  art under `liveries/<name>/`, a flavor's parent files beside it, a `latexmkrc`, and `talk.tex`
  on `livery=liveries/<name>, fonts=bundled`); the framework packs cu and nsi the same way.
  **Releases**: pushing a
  tag `v<version>` runs `release.yml`, which requires the tag to equal
  `version:` in `_extensions/engine/_extension.yml`. No tags were carried over
  from upstream; do not push upstream's tags here.
- Generated outputs (`*.pdf`, `*_files/`, `.quarto/`, the zip) stay untracked.

## CI

`.github/workflows/ci.yml` installs TeX Live, builds the starter decks, the
examples, the Overleaf zip (unpacked flat, no `TEXINPUTS`) and the HTML decks,
and checks Poppins is embedded and the math font is the serif one. Before the
builds it runs `livery_build.py --check` and `livery_check.py` on every reference
livery (pyyaml and Pillow), and `tools/test_compositions.py`. The runner's
system Chrome can wedge quarto's mermaid handshake: keep the
`chrome-headless-shell` install step.

## Git

Default branch `main`; branch + PR to merge. Remotes: `origin` is this repo,
`upstream` is NCAR_beamer_template.
