# Unplanned-city ledger

The record of the `unplanned-city-sweep` skill (`.claude/skills/unplanned-city-sweep/SKILL.md`):
each sweep over a window of merged PRs or an area of the tree adds an entry, newest first, and
the findings nobody picked wait in **Untriaged** until a later sweep takes them up or drops them.
Window mode starts from the newest window entry's end commit (an area entry records where it
branched from, not a window read).

## Entry format

```
## <date>: <window #a–#b | area <name>>

- Mode: window | area
- Range: <end of the previous entry>..<end commit> (window), or the area name
- End commit: <sha> (the `origin/main` commit the sweep read up to, or branched from)
- Done: <finding> (#PR), ...
- Tried and dropped: <finding>: <the numbers that said no>, ...
- Open: <finding>, ...
```

## Entries

## 2026-10-22: sprint `decks/agenda-quote` (not a sweep)

- Mode: a sprint's own record (`design/agenda-quote-handoff.md`)
- Done: the divider-subtitle rule, written twice (`engine-revealjs.lua`, `engine-beamer.lua`),
  is `engine-common.lua`'s `divider_subtitle()`, and pptx reads the dividers through `sections()`
- Open: pptx draws a quote in a plain column of a grid slide but still flattens a strip there to
  its text (`grid.py` `_flat()`; `_plain_column()` could take the strip too); `measure.py` measures
  an italic quote face upright (`font()` takes a weight, no style); the pptx agenda's number sits
  on its title's line by a hand constant (0.8 of the two sizes' difference)

## 2026-10-21: window #105–#126

- Mode: window
- Range: `62d6568..ba36ec5` (#105 consumer friction, #108 the first sweep, #109–#121 the Google
  Slides waves, notes under figures, SVG plots, Keynote notes, pytest, captions, app-open,
  Codespaces and tables, #123 nasa-jsc-eg and its engine sprint, #126 columns and cards); read in
  three area passes (engine-py; Lua and themes; docs, design, CI and make), 24 findings, Ben picked
  1–14 and 17 (`design/sweep-105-126-handoff.md`)
- End commit: `ba36ec5`
- Done (#127): ncar's pptx card head square at its foot (`top_only` never passed: a defect); the
  consumer workflow example pinned to a release that has the workflow, with `tests/test_docs.py`
  holding its pins to `_extension.yml`; runtimes.yaml's PPA add inside its own fallback; the
  changelog's link block caught up, with a ratchet; `pptx_steps/common.py` (the livery once, the
  shape and run helpers, the shape tests; `text_height` into measure.py; `livery.hex()`; a
  private-import ratchet); `livery.json latex.roles` and one unknown-`role=` check for all three
  formats (`C.box_role`, `grid._pick_role`; blends now reach the pptx); the Lua lifts
  (`is_slide_break`, `split_full`, `take_layout`, `LAYOUT_CLASSES`/`SLIDE_KINDS`/`content_heading`,
  `theme_options`, `take_footnotes`, `load_livery`; a test holds the JS and css kind lists to the
  Lua table); the glyph colors renamed `--engine-glyph-*`/`EngineGlyph*` (the `boxes.status` key
  stays); `section.label-color` resolved to a hex at build (untriaged item c); `geometry.body` and
  `geometry.half` derived once; dead code (four TeX macros, `engine-sub`, two parameters); the TeX
  requirements stated (`\NeedsTeXFormat` 2022-06-01, tcolorbox); the pptx text-height estimate on
  the template's own paragraph spacing (`livery.SPC_BEFORE`; the caution, lead, panel and note
  boxes grow 2–9 pt, nsi's band title stack moves 2 pt; shipped on the contact sheet); the
  prose batch; a state line on each finished `design/` handoff; the two heuristics below
- Done after (#129, the LaTeX-first-class sprint, 2026-10-21): `\cmark`/`\xmark`/`\pmark` and pifont
  retired from `engine_livery.sty`; `enginestatus` and `\engineglyph` are the one status idiom
- Done after (the gallery sprint, `design/gallery-handoff.md` commit 1, 2026-10-22): the lift the
  steps handoff asked for once `grid.py` passed ~600 lines (753 after the quote and the agenda):
  `body_box`, `group`, `shape`, `style_runs` and `para_text` moved to `pptx_steps/common.py`, with
  the picture recipes `slide_layout.py` kept privately (`contain_box`, `cover_crop`,
  `fit_picture`); `svg_fallback.py`'s rasterizer public as `rasterize_svg(svg, dpi)` (it stays
  there: that step reads no livery, and common.py loads one); `grid.run()` takes the deck's path
- Tried and dropped: none
- Open (this window's): the `.full` divergence (revealjs leaves a `.full` slide out of
  `wrap_layout` and `hoist_footnotes`, beamer does not: a `.full` frame with `scale=` is scaled in
  the PDF only; `CONTENT_KINDS` in engine-beamer.lua marks it); `notes-last.lua` and
  `linked-images.lua` keep their own one-line slide-break test (neither loads engine-common);
  the sprint-124 handoff's three follow-ups (a status-color contrast warning in `livery check`,
  `a:latin` on the ⚠ run if PowerPoint draws an emoji, the pptx box pads `type_step` does not
  scale); stress-test-findings' measuring scripts as a `utils/` tool; the unpicked findings, now
  under Untriaged

## 2026-10-20: area tests

- Mode: area
- Range: `tests/`, `make test` and CI's engine-test step, read after #113 landed the ninth script
- End commit: `4ab788f`
- Done (#115): the nine scripts as pytest modules, discovery the one list of tests (the
  Makefile's and CI's hand-kept lists had drifted: `test_charts.py` never ran in CI); CI's step
  calls `make test`; the duplicated `livery schema --doc --check` dropped (test_schema holds the
  reference current); the harness once in `tests/conftest.py` (ROOT, the per-livery argument, the
  pandoc deck helper the two pptx-step tests each carried, the livery subprocess); pytest-xdist
  from the start, `-n auto --dist loadfile`, with the rules that keep the suite parallel
- Tried and dropped: none
- Open: none

## 2026-10-20: window #95–#103

- Mode: window
- Range: `113892d..62d6568` (#95–#103: the runtime sprint, the shared installation, the first-run
  fixes, releases 26.10.1 and 26.10.2); read in #106's dry run, done after 26.10.3
- End commit: `62d6568`
- Done (#108): engine-common.lua for the six functions both filters carried; the version read from
  `_extension.yml` by the revealjs filter, with a test pin; luminance, contrast and mix once in
  `livery.py`, the tools importing each other by name (the tests' by-path loading and
  `_sibling()` gone); the roadmap's log closed at 26.10.0; CLAUDE.md's test list
- Tried and dropped: none
- Open: the `version:` line's three shell readers (`image.mk`, `release.yml`, `ci.yaml`), which must
  stay shell since the host side runs without Python; `livery_mpl.py` keeps its own reader because
  it ships alone in the charts zip

## Untriaged

- `engine-revealjs.scss` mixin candidates: the section, closing and feature-cover slides' identical
  flex-column block (×3, with its `html.reveal-print` restatements), the title tab (×2) and the
  field-code rule (×2); cosmetic.
- White by hand on dark fields: `#fff`/`white` literals in the scss (the feature bar's number, the
  closing, the band), the inner and outer beamer themes and `slide_layout.py` (the feature bar's
  number and panel text), where the composition's column role already reaches every format.
- Small-caps tracking per format: HTML 0.1em/0.08/0.04 by element, beamer `LetterSpace=4`, pptx
  `spc="100"` (grid.py), 0.1em (section_subtitle.py) and none (style_tables.py); one `livery.json`
  number would do.
- Strip spacing per format: the scss, `grid.py` and the inner theme each set the gap above and
  below a strip on their own numbers.
- The title-stack fractions (`livery_template.py`'s band stack and `slide_layout.py`'s
  `band_stack`/`draw_feature`): hand numbers (0.04, 0.01, 0.015, 0.02, 0.16, 0.185, 0.21) beside
  the compositions' boxes.
- scss line-heights as literals (some 16 sites) against `livery.json`'s leading.
- `build-decks.yaml`: a `framework:` input picking the submodule's tag, so a consumer pins one thing.
- `deck_qa.py`'s `h * 0.16` for the title line (nsi and nasa-jsc-eg sit lower).
- A table's height: `CELL_PAD` in one estimate, `2 * CELL_MAR` in the other (`slide_layout.py`).
- `livery.canvas_scale()` bypassed by `livery_template.py`'s own `self.k`; `livery_build.half` beside
  `livery.half_pt`.
- The `PX`, namespace and serialize copies the common.py commit did not take (section_subtitle's
  own namespace strings, svg_fallback's).
- The sprint-124 handoff's three follow-ups and the stress-test measuring scripts (this window's
  open list).
- The `version:` line's three shell readers (`image.mk`, `release.yml`, `ci.yaml`), which must
  stay shell since the host side runs without Python; `livery_mpl.py` keeps its own reader because
  it ships alone in the charts zip.
- Deferred by the three element sprints of 2026-10-22 (`design/citations-handoff.md`, "Deferred"):
  chevron steps (`style="chevron"`), alternating timeline labels, subsections in the agenda,
  `agenda: each`, the quote's quotation-mark glyph, `current=` on the agenda, a note-style CSL
  (needs citeproc in the filter), callouts reaching pptx as a native shape, stat tiles as a card
  preset, editable pptx charts from data, icons in pptx. (The image grid with captions on that list
  is done: the gallery sprint, `design/gallery-handoff.md`.)
- Deferred by the gallery sprint (2026-10-22): links round gallery images; vector (SVG) gallery
  images in pptx (rasterized now: an svgBlip twin per picture is svg_fallback's zip surgery); cells
  of unequal size (spans or weights); a picture or table inside a grid-slide column, which the
  gallery's disk read could now reach.
- A citation in a `::: note` is lost in the PDF: `engine-beamer.lua`'s `note_frames()` writes the
  note as raw LaTeX (`pandoc.write`), so citeproc never sees it; the footnote hoist moved to pandoc
  inlines between raw wrappers in the citations sprint, and the note could take the same shape.
- A long reference list in HTML (30 entries on one slide) shrinks to the autofit floor, then
  scrolls under Quarto's `scrollable` and runs over the slide number; the PDF breaks the frame.
