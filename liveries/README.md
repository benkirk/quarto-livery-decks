# Liveries

A livery is a brand as a directory of data and assets: `_brand.yml` (the colors, fonts and logos,
in Quarto's [brand.yml](https://quarto.org/docs/authoring/brand.html) form), `livery.yml`
(everything else; every key in [REFERENCE.md](REFERENCE.md)), `fonts/`, `logos/`, optionally
`art/`, `reference/notes.md` (the decisions taken), and two generated, committed things:
`build/` (what the formats read) and `template.pptx`. `cu/` and `nasa/` are worked examples, their
`reference/notes.md` the decisions they took; the design is `design/engine-and-liveries.md`,
sections 4 and 6.

## The `livery` command

Everything a livery owner does is one command, `livery`: `bin/livery`, on your PATH after
`source etc/config_env.sh` (README "Quick start") and in the container. From a repository that
has this framework as a submodule it is `<framework>/bin/livery`, which a link in `~/bin` can
make plain `livery` too. `livery check` prints only warnings, failures and one summary line per
livery; `-v` prints every check.

| command | what it does |
|---|---|
| `livery new <dir> [--from <deck.pptx>] [--extends <name>]` | scaffolds a livery that builds as it stands: a palette on PowerPoint's theme slots, the roles on them, Public Sans as a stand-in face, a placeholder mark from the livery's name, the default geometry, `reference/notes.md`. `--from` takes the reference deck's colors, fonts and slide size and writes `reference/report.md`; `--extends` makes a flavor of a livery beside it (with `--from`, the report only) |
| `livery inspect <deck.pptx> [-o report.md] [--media DIR]` | reports on a reference deck (to the terminal, or to `-o`'s file): slide size, theme slots, fonts, layouts and placeholders, colors by frequency, media |
| `livery build <dir>... [--check]` | validates `livery.yml` and `_brand.yml` against the schema and resolves them into `build/livery.{json,sty,css,theme,mplstyle}`; `--check` fails on a stale `build/` |
| `livery template <dir> [-o FILE]` | generates `template.pptx` from `build/livery.json` (never edit it by hand) |
| `livery check <dir>... [--swatch DIR] [--qa]` | build freshness, every file the data names, the template's pandoc compliance and that it rebuilds from the data, contrast warnings, the chart colors' checks (`--swatch`: their contact sheet `DIR/charts-<name>.png`); `--qa` then runs the quickstart deck's `make qa` under the livery |
| `livery all <dir>... [--qa]` | build, template, check: the loop to rerun after every edit |
| `livery zip <dir> -o <zip> [--starter FILE] [--photo FILE]` | the Overleaf project: the theme, the livery, the starter deck and the LaTeX cookbook |
| `livery zip --charts <dir> -o <zip>` | the charts bundle: the plot style and helper for matplotlib outside the decks |
| `livery schema --doc [--check]` | regenerates [REFERENCE.md](REFERENCE.md) from the schema |

`make livery LIVERY=<name>` at the top of the repository runs `livery all liveries/<name>`, and
`make livery LIVERY_DIR=<dir>` a livery anywhere. A deck directory's `make overleaf` and
`make charts-zip` run the two `zip`s for the deck's livery.

## Adding a livery

From a reference PowerPoint, or a brand guide alone, to a deck in the new brand:

1. **Scaffold it.** `livery new liveries/<name> --from <deck.pptx>` (or without `--from`, from a
   brand guide). The deck stays out of git; `reference/report.md` is its reading.
2. **Decide the data**, writing the judgement calls into `reference/notes.md` as you make them.
   The build refuses a key or a value the schema does not allow, naming its path;
   [REFERENCE.md](REFERENCE.md) says what each key does on the slide.
   - **Palette and roles.** `_brand.yml`: the palette under the brand's own names (the scaffold
     names the colors after the theme slots) and `primary`/`secondary`/`foreground`/`background`.
     `livery.yml` `roles`: `primary-text`, `primary-contrast`, `accent`, `highlight`, `muted`,
     `surface`, `warning`, `dark`, and `code-text` when code should not be the `dark` role. A
     background darker than the foreground makes a dark livery ("Dark liveries" below).
   - **Fonts.** The brand's font files in `_brand.yml` in place of the stand-in (free,
     bundleable; a proprietary face is named in the pptx and stood in for elsewhere),
     `typography.monospace` for a code face, `installed-fonts` for a proprietary face to prefer
     where installed, and `pptx.typeface` (and `heading-typeface`, and `code-typeface` for the
     pptx's code when the brand template names an installed one).
   - **Marks.** The brand's logos in `_brand.yml` in place of the placeholder (an RGB PNG for
     the web, the same name as `.pdf` for LaTeX), a `signoff` lockup if the brand wants one at
     the foot, and `marks` when a field needs another mark than the defaults (`background` wears
     `logo.medium.light`, `primary` the dark one, every other field primary's). One composed slide
     wears a given image with `compositions.<name>.mark.image` or `.signoff.image` (a
     `logo.images` name); its light variant keeps it.
   - **Geometry.** The scaffold's fractions are ncar's; set the lockup's `geometry.logo.aspect`,
     the marks' corners, and `logo.inset` to put the content mark nearer the paper's edge.
     `geometry.wide-margin` is a `{.wide}` slide's side margin (default half the margin),
     `geometry.body-bottom` the content body's foot.
   - **Boxes.** `boxes:` holds the numbers every format draws its columns and boxes with: the
     column gap and an optional rule between columns, the caution box's bar and pads, the
     feature panel's pads, the lead box, cards (fill, corner radius, a picked card's outline),
     strips (their tint), the status glyphs' colors, the steps' rail, the agenda's colors, and the quote block (its
     bar, and a face of its own: `boxes.quote.family`, a bundled family, and `style`). Set only
     what differs from the engine's
     (REFERENCE.md has every key): ncar rounds its cards and keeps its warn and fail glyphs off
     its yellow, which is unreadable as text on white; nasa-jsc-eg rules its columns.
   - **Slide styles.** `frametitle` for the content titles (`align`, the accent `tab`, the
     hairline `rule`); `title: {style: band, ...}` for a band title instead of the cover (nsi);
     `feature.style`; `compositions` to move any box of the composed slides.
   - **Bullets.** `bullets:` (`glyphs` per level, `color`) when the brand's template draws its own
     list glyphs; the glyphs must exist in `pptx.typeface`.
   - **Art.** `art`: wave curves (`common/utils/fit-waves.py` fits them to the brand's cover
     art), or a picture per slide kind, or nothing; `titlegraphic` for a default title photo,
     `title-light` for the light cover's own picture.
   - **Type.** `type:` in points and `pptx.size`, the brand template's canvas (docs/authoring.md "Text
     sizes and the slide size").
   - **Chart colors.** A brand guide's published data palette goes in `charts:` (`ramps`,
     `sets`, or `extended` for secondary colors), its source in `reference/notes.md`; with
     nothing, the engine generates one from the brand's own colors. Look at the swatch sheet
     (step 3) and record the result in the notes.
   - **Flavors.** `extends:` makes a livery a flavor of another, naming only what differs
     (`livery new liveries/<name> --extends <parent>`). `null` unsets what the parent sets: an
     `art` picture (`art: {titlegraphic: null}`), or the code face in the flavor's `_brand.yml`
     (`typography: {monospace: null}`; the parent's font list still comes whole, its code-face
     files with it).
3. **Build and check.** `make livery LIVERY=<name>` after every change; `livery check
   liveries/<name> --qa` adds the quickstart deck's `make qa` and the chart colors' contact sheet
   in `decks/quickstart/_qa/`. `make -C decks/plots qa LIVERY=<name>` shows the plots in it,
   `make -C decks/quickstart measure LIVERY=<name>` checks the composed slides.
4. **Look.** `make -C decks/quickstart pptx html pdf LIVERY=<name>`; open the pptx in PowerPoint
   (the "Repair?" prompt cannot be automated), the HTML in a browser, the PDF.
   `make -C decks/quickstart overleaf LIVERY=<name>`, unzip it somewhere clean and
   `latexmk -xelatex talk.tex`: the pure-LaTeX path. Commit `build/`, `template.pptx`, the assets
   and the notes. CI builds the quickstart under every livery directory and compiles its
   Overleaf zip, so the new one is checked from its first push.
5. **Release.** Add the livery's row to latex/README.md "Overleaf" and README "The liveries", `make
   gallery` it into the README, and its entry to [`CHANGELOG.md`](../CHANGELOG.md) under
   *Liveries*. A release is the engine's version, a calendar version `YY.MM.N` (the month
   unpadded, `N` the month's release count from 0, CHANGELOG.md's preamble): set `version:` in
   `_extensions/engine/_extension.yml` (the revealjs filter reads it there to name the HTML
   dependency), `livery build liveries/*/` (each `build/livery.json` records the version), bump the
   consumer example's `@v<version>` and image tag in docs/other-repos.md (`make test` holds them
   to the version), rename the changelog's `[Unreleased]` to `[<version>] - <date>`, merge, then
   tag `v<version>`.
   Tags are never moved: another release in the month is the next `N`. The release workflow
   refuses a tag that is not the version or not `YY.MM.N`, a month still to come, one that was
   released before and one without a changelog entry; it
   attaches one Overleaf zip and one charts bundle per livery, with the entry as the notes, and
   the Overleaf links serve the latest.

A livery outside this repository ([docs/other-repos.md](../docs/other-repos.md)) is the same
directory anywhere: `livery new path/to/mybrand`, `make livery LIVERY_DIR=path/to/mybrand` in the
framework, and `make pptx LIVERY_DIR=path/to/mybrand` in a deck.

## Dark liveries

A livery whose background role is darker than its foreground (`nasa-dark`)
sets its content slides light on dark, and everything follows: code gets its own `code-text`
role (the `dark` role stays a field color), tints mix toward the background, callouts and
tables take dark shades, and the mermaid and Graphviz diagrams, which Quarto renders as dark
on white, are turned to the dark with their hues kept (`diagram-dark.lua`).
