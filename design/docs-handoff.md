# Handoff: the READMEs, and LaTeX/Overleaf for any livery

**State:** done (this repo #28–#32, engine 3.4.0).

Written 2026-10-17, after the post-NSI refactor (engine 3.3.0, this repo #27), for a fresh
session. Read this, `CLAUDE.md`, and the newest entries of `docs/design/engine-and-liveries.md`
section 10. The repos, environment and conventions (one step per PR, CI green, merge
authorized, contact sheets before a PR, parity, a layman's summary before any questions) are
as in `docs/design/nsi-handoff.md`, "The two repos and how work flows". One trap there is
missing: in the engine checkout `gh` resolves to the `upstream` remote (NCAR_beamer_template),
so every `gh pr` command there needs `--repo benkirk/beamer-livery-theme`.

## Why

Both READMEs still describe the single-brand world they were forked from:

- **Engine** (`beamer-livery-theme/README.md`): titled "NSF NCAR / UCAR Beamer Template"; its
  banner says the refactor is "under way" and that "the brand data still lives in the theme";
  the intro, fonts, colors and brand-rules sections are NCAR's (Poppins, the palette, "the NCAR
  logo is always locked up with the NSF logo"); liveries get one line (`livery=`); `brand=`
  lists ncar, ucar, ncarucar (not ucp); the previews are NCAR only. Its
  `docs/design/engine-and-liveries.md` is a stale copy (about 280 lines behind this repo's).
- **Framework** (`README.md`): opens "NCAR-branded Quarto template"; the clone path is
  `quarto-docs-framework`; the Layout tree shows only `liveries/ncar` and half the utilities;
  "NCAR web theme" in the quick start; every screenshot is NCAR.

Ben wants both rewritten **at about today's length** (engine about 435 lines, framework about
570), keeping the quick start and the Overleaf link, updated for liveries, with **an NCAR and a
CU example rendered**.

And a gap he asked to close: **pure LaTeX and Overleaf for any livery in the framework**, not
only the engine's reference ones. Today a LaTeX user who clones the engine gets ncar, ucar, ucp
and ncarucar; cu and nsi live here. `\usetheme[livery=<dir>]{Engine}` already takes any
directory with a `build/livery.sty` (absolute, or relative to TeX's search path:
`engine_livery.sty`), so the theme can do it; what is missing is packaging. The engine's
`make overleaf` zips `talk.tex`, `latexmkrc`, two NCAR photos, the `*.sty` and only
`liveries/*/fonts/*.ttf` and `liveries/*/logos/*.pdf`: cu's fonts are `.otf`, nsi's logos PNG,
and a flavor needs its parent's files too.

## Step 1: an Overleaf/LaTeX bundle for any livery (engine PR, 3.4.0)

A new engine tool beside `livery_build.py`, so this repo and any consumer repo can call it:

    overleaf_zip.py <livery dir> -o <zip> [--starter talk.tex] [--photo <file>]

It writes a project that compiles with nothing but XeLaTeX:

- the engine's `*.sty` under `_extensions/engine/` (no Quarto, revealjs or Python files);
- `liveries/<name>/` with `build/livery.sty` and every file LaTeX reads, from `livery.files()`
  (engine `livery.py`): fonts of any extension, each logo as its `.pdf` when there is one, else
  its image, and the art files. A flavor's ancestors go in too (`livery_build.ancestors()`), so
  nsi's `../cu/...` paths resolve;
- a `latexmkrc` like the engine's, with TEXINPUTS and TTFONTS covering `./_extensions/engine//`
  and `./liveries//`;
- the starter (default: the engine's `talk.tex`) with its `\usetheme[...]` line rewritten to
  `\usetheme[livery=liveries/<name>, fonts=bundled]{Engine}`.

Then `make overleaf` in the engine uses it for ncar. The release asset keeps its name,
`engine-beamer-overleaf.zip`, because the engine README's Overleaf link and earlier releases
point at it.

Traps:

- **`fonts=bundled` in the starter, always.** Under `fonts=brand` (also the default, `auto`,
  under XeLaTeX) a livery with `installed-fonts` (cu, nsi) probes fontconfig by name, which on
  Overleaf's cold font cache takes longer than a free-plan compile may (the comment in
  `engine_livery.sty` records the same trap for Poppins).
- **The starter's photos are NCAR's** (`images/wallpaper/mesa_lab*.jpg`). For another livery use
  its `art.titlegraphic` when it has one, else drop `\titlegraphic`; `--photo` overrides.
- **nsi's band title** needs `art.title` and `art.titlegraphic` packed; check the PDF, not just
  the compile.

Check: engine CI already unzips the zip into `/tmp/overleaf` and compiles it with
`env -u TEXINPUTS -u TTFONTS latexmk -xelatex talk.tex`, then greps `pdffonts`; keep that step.
`tools/parity.sh` must stay clean (the decks themselves do not change).

## Step 2: this repo packs and releases a zip per livery (framework PR)

- `make overleaf LIVERY=<name>` (in `docs/Make.common`, so it works in a consumer repo for its
  own liveries too) writes `<name>-overleaf.zip` with the engine's tool.
- A new `.github/workflows/release.yml`: on a `v*` tag, build the zip of every directory under
  `docs/common/liveries/` and attach them to a GitHub Release (copy the engine's `release.yml`,
  minus its check that the tag equals the extension's `version:`: this repo has none).
- The README gets one **Open in Overleaf** link per livery:
  `https://www.overleaf.com/docs?snip_uri=https://github.com/benkirk/quarto-livery-decks/releases/latest/download/<name>-overleaf.zip&engine=xelatex`.
  The same zip, downloaded and unzipped, is the local pure-LaTeX path (`latexmk -xelatex talk.tex`).
- `ci-liveries.yaml` gains the clean-directory compile of each livery's zip. That job has no TeX
  yet: install TinyTeX as `ci-build-sample.yaml` does.
- **The first tag is outward-facing**: ask Ben before pushing it. After the release, Ben opens
  each link once to confirm Overleaf compiles it on the free plan (it cannot be automated).

## Step 3: the engine README (engine PR)

Same length and skeleton, rewritten for liveries:

- **Title and intro**: one layout engine, many brand liveries; slides in LaTeX beamer or Quarto
  (PDF, and revealjs HTML from the same Markdown). Reference liveries: NSF NCAR, UCAR, UCP,
  NSF NCAR-UCAR. Others (CU Boulder, CU NSI) come from quarto-livery-decks, with their own
  Overleaf links. The banner shrinks to two lines on the relationship to NCAR_beamer_template.
- **Preview**: NCAR and CU side by side, PDF and HTML (replace `docs/preview.png` and
  `docs/preview-html.png`). Build CU with `livery=` pointing at this repo's
  `docs/common/liveries/cu`, or from its Overleaf zip.
- **Keep**, trimmed where they say "Poppins" for "the livery's font": Quick Start, Overleaf (the
  NCAR link, plus "other liveries: quarto-livery-decks releases"), "Already have a project?"
  (`livery=` first, `brand=` as the bundled shorthand), the cheat sheet, HTML slides, math
  fonts, the v1 migration and the 2020-brand note.
- **Fix**: the theme-options table (`brand` lists ucp; `title`; `fonts` with installed fonts in
  one line, the long paragraph moved under Liveries); Colors becomes roles first, the palette
  names per livery; "What's in the repository"; Releasing (the tool); License (each livery's
  marks are its owner's).
- **New "Liveries" section**: what a livery folder holds (`_brand.yml`, `livery.yml`, fonts,
  logos, art, `template.pptx`, `build/`); a short table of the knobs (roles, geometry and the
  marks' corners, `signoff`, `marks`, `title.style` cover or band, `art` waves, pictures and
  `titlegraphic`, `installed-fonts`, `extends`, `pptx`); the three tools (`livery_build.py`,
  `livery_check.py`, `livery_template.py`); pointers to design section 4 and this repo's
  "Adding a livery".
- **Brand rules** become "the ncar livery follows the 2026 Brand Guide" (short); every other
  livery's decisions live in its `reference/notes.md`.
- The stale `docs/design/engine-and-liveries.md` becomes a short pointer to this repo's copy.
- The engine's `CLAUDE.md` opening paragraph (one 40-line sentence chain) becomes a short
  structured list.

## Step 4: the framework README (framework PR)

- **Title and intro**: a multi-brand Quarto deck framework, pptx first, HTML and PDF from the
  same Markdown; liveries ncar, cu and nsi. Trim the banner the same way.
- **Images**: keep the NCAR quickstart shots (`make screenshots`, `screenshots.py`). Add one
  gallery, `docs/quickstart/screenshots/liveries.png`: rows ncar, cu, nsi; columns title,
  divider, a content slide, closing (HTML). A `make gallery` target that builds the quickstart
  under each `LIVERY` and reuses `screenshots.py`'s `serve()` and `grid()`. (Switching `LIVERY`
  is now safe without `make clean`: `Make.common` drops the stale HTML dependency first.)
- **Quick start** gains `make pptx LIVERY=cu` and the gallery.
- **New "LaTeX and Overleaf" section**: the per-livery links (Step 2) and the local zip.
- **Fix**: the Layout tree (repo name, `liveries/{ncar,cu,nsi}`, the utilities, `fixtures/`);
  "Adding a livery" (marks, `title.style`, installed fonts, its Overleaf zip); "Using the
  framework from another repo" (their liveries' zips); License (CU's and NSI's marks are
  theirs). Remove "NCAR-branded", "NCAR web theme" and the `quarto-docs-framework` clone path.
  Update `CLAUDE.md` to match.

## Step 5: GitHub "About" (apply after Ben approves the text)

With `gh repo edit <repo> --description ... --add-topic ...`:

- **engine**: "Beamer and Quarto revealjs theme engine with brand liveries (NSF NCAR, UCAR,
  UCP): LaTeX, Overleaf and Quarto slides". Topics: beamer, latex, overleaf, quarto, revealjs,
  xelatex, slides, presentation-template.
- **framework**: "Quarto deck framework: one Markdown file to branded PowerPoint, revealjs HTML
  and beamer PDF, per brand livery (NCAR, CU Boulder, ...)". Topics: quarto, pptx, powerpoint,
  revealjs, beamer, overleaf, slides, documentation.

## Open questions for Ben (a layman's summary first)

1. **CU images in public READMEs.** cu's content background (`art/content-flatirons.jpg`) has
   unverified rights (cu `reference/notes.md`). Swap it for a CU-owned photo first, render the
   CU examples without it, or accept it?
2. **The framework's Overleaf starter.** The engine's `talk.tex` (its text is generic, its
   photos NCAR's), or a short starter of its own?
3. **Release cadence.** Tag this repo after each livery change, or by hand?

## Verification

- Each livery's zip compiles in a clean directory with TeX's paths unset: in CI, and locally
  for ncar, cu and nsi; `pdffonts` lists the bundled faces (Poppins, TeX Gyre Heros), never
  Helvetica Neue; the nsi PDF shows the band, the constellation and the campus photo.
- After the first release, every README Overleaf link downloads its zip (Ben compiles them).
- Parity: Step 1 leaves `tools/parity.sh` clean; Steps 3 and 4 change no deck output
  (`docs/common/utils/parity.sh` clean, or skip it when only Markdown and images changed).
- A contact sheet of the new README images goes to Ben before each README PR; the README
  renders on GitHub (check the PR's file view: images, links, tables).
