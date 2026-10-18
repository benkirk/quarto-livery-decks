# Handoff: the post-NSI refactor

Written 2026-10-16 after the retrospective on the two very different liveries (`cu`, then its
`nsi` flavor), for a fresh session. Read this, `CLAUDE.md`, and the newest entries of
`docs/design/engine-and-liveries.md` section 10. The repos, environment, conventions (one step
per PR, CI green, merge authorized, contact sheets before a PR, parity) are as in
`docs/design/nsi-handoff.md`, "The two repos and how work flows".

## Why

nsi went in as data, but it exposed frictions. Three are structural:

1. Every title composition is written four times (beamer, revealjs, the pptx template
   builder, `slide_layout.py`), in two repos, and the copies drift. **Deferred on purpose**:
   see the end of this file and design section 7.
2. The pptx template builder lives in the framework but writes files the engine owns (each
   reference livery's `template.pptx`): adding two layouts took an engine PR that only
   carried regenerated templates.
3. The marks assume one look for every colored field: nsi has gold dividers and a black band
   title, so it grew band-only keys (`title.logo`, `title.signoff`) and a separate dark
   default (`logo.medium.dark`) for gold.

The cheap ones: unknown livery keys are dropped silently; a livery change does not rebuild
decks; nothing automated renders a title photo or `title=light`; beamer prefixes absolute art
paths with the livery directory; a flavor drops its parent's `pptx.scheme` overrides.

This refactor does 2, 3 and the cheap ones, and adds one feature Ben asked for afterwards: a
livery may prefer an installed font (cu: Helvetica Neue) over its bundled stand-in. One engine
PR, then one framework PR.

## Engine PR (beamer-livery-theme, version 3.3.0)

### A. The template tooling moves into the engine (item 2)

Move from the framework's `docs/common/utils/` into `_extensions/engine/`, beside
`livery_build.py` (the vendoring copies only that directory):

- `livery_template.py` (the builder) and `pptx_waves.py` (the wave and cover shapes it shares
  with the framework's `slide_layout.py`);
- `livery.py`, the reader of `build/livery.json` (`load`, `color`, `scheme`, `derived`,
  `font_file`, `logo_path`, plus the marks accessor of B); the builder needs only `load` and
  `logo_path` today, but ten framework utilities use it, so it gets one home;
- the data and template checks of `livery_check.py` (`files_named`, `check_template`, build
  freshness, contrast). Its `--qa` flag (it runs the framework's `make qa`) stays in the
  framework.

Engine CI then checks its own templates: after `livery_build.py --check`, run
`livery_check.py _extensions/engine/liveries/*/` (`pip install pyyaml pillow`; the builder
writes raw XML with zipfile, Pillow only measures photos). A future template change is then
one engine PR (builder change plus the four regenerated templates), and the framework only
re-vendors.

### B. Marks by field (item 3)

A new `marks:` block in `livery.yml` names the mark and the sign-off for each field by its
role. The engine knows each field's role: content slides `background`; dividers, the cover
title and closing, feature covers `primary` (the cover title is `background` under
`title=light`); the band title and closing `title.field` (`dark` by default).

```yaml
marks:                                          # nsi, for example
  primary: {logo: nsi-black}                    # gold fields: the one-color black mark
  dark: {logo: nsi-white, signoff: rio-white}   # the band's black field
```

- `livery_build.py` resolves `out["marks"]` = {role: {logo, signoff}} for `background`,
  `primary` and every role a field uses. Defaults: `background` from `logo.medium.light` and
  `signoff.light`, `primary` from `logo.medium.dark` and `signoff.dark`, any other role from
  `primary`. The brand.yml standard keeps `logo.medium` as the source of those defaults.
  Written always (one shape for every consumer), so every committed `build/livery.json`
  changes once; nothing drawn changes.
- `title.logo` and `title.signoff` become deprecated aliases for `marks.<title.field>`
  (accepted, with a warning).
- Consumers read marks instead of the variants: the `.sty` emitter (keep
  `\engine@logo@light|dark`, `\engine@signoff@light|dark` as the background and primary
  marks, `\engine@title@logoimg|signoffimg` as the band's), the `.css` emitter's image rules,
  the Lua `add_dependency`, and in A's moved files the builder's `logo()`, `signoff_pic()` and
  `band_strip()`. Keeping the macro and variable names keeps the theme code nearly untouched.

### C. Cheap fixes in the engine

- **Unknown keys warn.** `livery_build.py` keeps a set of known top-level `livery.yml` keys
  (today's whitelist plus `name`, `extends`, `roles`, `derived`, `signoff`, `title`, `marks`)
  and prints a warning for any other, instead of dropping it silently.
- **Absolute art paths.** `emit_sty` writes `\engineliverydir <path>` only for relative paths;
  an absolute one goes in as is (the revealjs side already copies it).
- **Flavors inherit `pptx.scheme` overrides.** `read()` stops popping the parent's
  `pptx.scheme`. The raw data holds only explicit overrides (no reference livery has any), and
  `resolve()` recomputes every other slot from the flavor's own roles, so nothing changes for
  the reference liveries; nsi can then drop its restated `hlink`/`folHlink`.

### D. Prefer an installed font, fall back to the bundled one

For cu users who want the brand's real Helvetica Neue in HTML and PDF without anyone shipping
its files (Monotype's font: the repo and a published site may carry it only under a license;
cu bundles TeX Gyre Heros instead). A new `livery.yml` block names installed fonts to prefer;
the bundled `typography.fonts` stay the fallback:

```yaml
installed-fonts:          # cu, for example
  base: Helvetica Neue                        # the family, as fontconfig and CSS local() name it
  headings:                                   # a face of a family, by its full and PostScript names
    family: Helvetica Neue
    faces: {bold: [Helvetica Neue Condensed Bold, HelveticaNeue-CondensedBold],
            regular: [Helvetica Neue Condensed Bold, HelveticaNeue-CondensedBold]}
```

- **`livery_build.py`** validates it (C's known keys), passes it to `livery.json`, and emits:
  - in the `.sty`, `\engine@font@installed` (the base family) and the headings face names;
  - in the `.css`, each `@font-face` `src` with `local("<full name>"), local("<PostScript
    name>")` ahead of the bundled `url()` (the CSS spec matches local() by full or PostScript
    name, not by family), for the base family's four faces and the headings faces. A viewer
    with the font installed (Macs, iPhones) sees it; anyone else gets Heros; nothing is copied.
- **`engine_livery.sty`**: under `fonts=brand`, probe the installed family first
  (`\IfFontExistsTF{\engine@font@installed}`) and load it with fontspec (the headings by face
  name), else today's path (bundled copy, then an installed copy of the bundled family).
  `fonts=bundled` keeps ignoring installed fonts, so the shared `_quarto.yml`
  (`themeoptions: [fonts=bundled]`), CI and parity stay deterministic: a deck opts in with
  `themeoptions: [fonts=brand]`. A PDF built that way on a Mac embeds Helvetica Neue for every
  reader; built on Linux it falls back to Heros.
- pptx needs nothing: its theme already names Helvetica Neue (`pptx.typeface`).
- The licensing note goes in the README with the option: the engine never copies the font;
  embedding an installed font in a PDF you build is the builder's licence to check (macOS's
  terms do not cover redistributing the files, which this never does).

Parity (`tools/parity.sh`): every PDF page identical; HTML differs only by the version path.

## Framework PR (quarto-livery-decks)

1. Re-vendor 3.3.0 (`quarto update`; `make vendor-engine` while the engine PR is open).
2. Remove the moved files from `docs/common/utils/`. `utils/livery.py` becomes a short shim
   that loads the engine's reader from `../_extensions/benkirk/engine/` (by file path, with
   `importlib`, since both are named `livery`), so the ten utilities keep `import livery as
   livery_mod`; `slide_layout.py` imports `pptx_waves` the same way. `utils/livery_check.py`
   becomes a wrapper that runs the engine's checks and keeps `--qa`. Callers of
   `utils/livery_template.py` (README "Adding a livery", CLAUDE.md, the CI workflows, the
   design docs' commands) point at the engine's copy. This must hold for a consumer repo too
   (the framework as a submodule): every path stays relative to `docs/common/`.
3. Migrate cu and nsi to `marks` (nsi: the block above, its `title.logo`/`title.signoff` and
   `logo.medium.dark` removed, its restated `pptx.scheme` removed); rebuild and rerun the
   builder: both templates must come out byte-identical (the marks resolve to the same files).
4. **A livery change rebuilds the decks.** `utils/livery.py deps <livery dir>` prints the
   files a build reads: `build/livery.{json,sty,css,theme}`, `template.pptx`, and every font,
   logo (with its same-named `.pdf`, which LaTeX picks) and art file the json names, the
   parent's included. `docs/Make.common` adds them to `DEPS`
   (`LIVERY_FILES := $(shell python3 ... deps $(LIVERY_DIR))`). Today `DEPS` has only the
   `_livery` link, whose mtime does not change when a file in the livery does.
5. **A fixture deck in parity and CI.** `docs/fixtures/` with `DECKS := photo light`: the
   quickstart's slide types plus a `titlegraphic:` (photo) and `themeoptions: [fonts=bundled,
   title=light]` (light), a `.feature` and a `.closing` slide each. `parity.sh`'s default
   decks gain `docs/fixtures` (under `PARITY_LIVERIES`, nsi added there so the band is
   covered); `ci-build-sample.yaml` builds it under ncar. Small images only, from
   `docs/quickstart/images/`.
6. cu adopts D: the `installed-fonts` block above in `cu/livery.yml` (nsi inherits it). cu's
   committed outputs under `fonts=bundled` are unchanged; its `livery.css` gains the
   `local()` sources.
7. Docs: README (the option, how a deck opts in, the licensing note), CLAUDE.md (the
   utilities' list, the template builder's home, `marks`, the prerequisites, installed
   fonts), cu's notes (the open "pptx fonts" item gains the HTML and PDF side), nsi's notes,
   a log entry.

Parity (`docs/common/utils/parity.sh`, ncar, cu and nsi): pptx and PDF identical; templates
rebuild byte-identically; HTML differs only by the version path (and cu's and nsi's
`livery.css` by the `local()` sources).

## Verification

- Engine: `livery_build.py --check` and the moved `livery_check.py` on all four reference
  liveries, in CI too; `tools/parity.sh` clean.
- Framework: `livery_check.py` on ncar, cu, nsi; `parity.sh` clean; touching a livery's logo
  rebuilds a deck (`make -n` shows it); the fixture decks render in three formats; a consumer
  repo build (`ci-consumer.yaml`) still passes.
- A deliberate unknown key in a scratch livery prints the warning.
- Installed fonts, on a Mac: the quickstart under cu with `themeoptions: [fonts=brand]` gives
  a PDF whose `pdffonts` lists HelveticaNeue faces (and Heros under `fonts=bundled`); in the
  HTML, Playwright's CDP `CSS.getPlatformFontsForNode` on the title and a body paragraph
  reports Helvetica Neue (Condensed Bold for the title), and with the `local()` names
  misspelled on purpose it reports TeX Gyre Heros (the fallback works). CI (Linux) keeps
  passing on the fallback.
- Contact sheet: the fixture decks under ncar, cu and nsi (title, light title, photo title,
  closing, a divider) in pptx, HTML and PDF, sent before the framework PR.

## Deferred on purpose: one description of each title composition

The title (cover and band), closing and feature compositions are drawn by four
implementations in two languages each: beamer TikZ, revealjs Lua and scss, the template
builder, and `slide_layout.py`. They already drift (the cover's text order and vertical layout
differ by format; the light title's colors differed until 2026-10-16). The fix is a design
change, not a refactor: describe each composition once in `livery.json` as boxes in slide
fractions (field, band, photo box, text column, mark and sign-off boxes, the tab and rule),
emitted by `livery_build.py`, and have every format draw those boxes (pptx placeholders are
fixed boxes anyway; HTML and PDF would place the text column in its box and centre it there).
Write it up in design section 5 before the next new composition, and do it then.
