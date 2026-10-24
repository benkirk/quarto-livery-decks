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

## 2026-10-23: area docs (the user-facing docs after #138)

- Mode: area (`docs`, the user-facing part: README.md, docs/*.md, liveries/README.md,
  latex/README.md, latex/authoring.md, decks/plots/README.md, the quickstart's and sample's
  prose, the changelog's Unreleased section; CLAUDE.md, design/, the generated REFERENCE.md,
  code and tests out of scope), read against the code as it stands after #138; the Untriaged
  list held no docs item to start from
- Range: the area
- End commit: `c0ac0be` (#138, the branch point)
- Done (#139): American spelling (judgment, license, labeling, centered); the guides' intros
  listing the element sprints' patterns; liveries/README's ragged lines and the cookbook's
  filler typos; text on a field named by its role (a solid card's text, `.brand-dark`,
  title=light: "white" and "Space" gone); latex/README's roles (`BrandOnDark`) and exported
  palette names (one list per family, nasa-dark's and nasa-jsc-eg's extras); the sample's
  closing-in-pptx and SVG-in-pptx claims; livery-neutral prose for the caution slide's role and
  the text face; the quickstart's pipeline diagram with every filter and step; the README shots
  #138 moved (tracking, the gallery's dividers) reshot; `make previews` making `latex/preview.png`
  (shot by hand at the flatten until now, `sheet.py --pages`)
- Tried and dropped: none
- Open: `decks/plots/screenshots/liveries.png` (shot at #70) sees only #138's 1 → 1.4 px
  hairline, not worth six HTML builds until the plots change; `01-title.png` and `pdf.png` carry
  `date: last-modified`, so every reshoot after an edit churns them by the date alone (the
  screenshot recipe could pin the date); CLAUDE.md "The engine" names `sample.png` as what `make
  previews` makes, now three images (out of this sweep's scope); the Unreleased section's "white
  as before on every bundled livery" wording is right but the README's livery table still says
  "the white-rule insignia" for nasa's mark (a mark's own color, left)

## 2026-10-22: area themes (the "one look, one key" sprint)

- Mode: area (`themes`: the beamer `*.sty`, the revealjs `*.scss`, the pptx steps that draw the same
  looks, and `livery_build.py`'s emitters), from the window #127–#135 entry's deferred list and
  the Untriaged piles of the same kind; the plan is `design/one-look-one-key-handoff.md`
- Range: the area
- End commit: `81a3c9d` (release 26.10.9, the branch point)
- Done (#138): the content title band from `frametitle.top/height/rule-y` (the pptx title centered
  in the band as HTML and beamer, the PDF's tab the band's height; Ben's pick); the hairline from
  `frametitle.rule-width/rule-color` (the `rule` blend at beamer's 0.4 pt, pick C; the dark PDF's
  hairline was near-black on black); the theme's `ex` gaps as em of their element from
  `boxes.note.gap`, `boxes.quote.attribution-gap`, `section.eyebrow-gap`, `section.subtitle-gap`
  (the PDF's gaps as keys, HTML shrinks to them; the pptx divider's pixel copies and the
  attribution's missing gap went with them); `boxes.footnote` (hang 0.9, gap 0.55, step 0.3, the
  `rule` blend; the pptx hangs the marker, spaces by gap and step, sets the mark bold);
  `boxes.strip.gap`; `type.tracking` (0.08: at 0.1 pdftotext splits the PDF's tracked words);
  the derived `on-dark` role for every white written by hand (the scss's four Sass defaults
  stay; the ratchet's ceilings fell to 4 and 0). Each change of look judged on a before/after
  contact sheet in all three formats under ncar, cu and nasa-dark; parity named every page and
  slide that moved, in each commit
- Tried and dropped: none
- Open: the pptx footnote rule (a shape drawn at style time is orphaned when `grid.py` or
  `columns.py` moves the paragraph; a late step would need the paragraph's rendered position,
  which nothing knows before PowerPoint opens the file); HTML's title hairline fixed at `rule-y`
  where beamer's follows a two-line title (pptx's cannot: a static layout); the pptx `::: note`
  keeps its measured placement, not `boxes.note.gap`; the four Sass defaults (`$body-bg`,
  `$dark-bg-text-color`, the mermaid pair) stay compile-time whites overridden at runtime; the
  feature panel's heading is `secondary` in HTML and the PDF but the panel's text color (white)
  in the pptx (`slide_layout.py` recolors every run), and on cu the secondary gray reads muted on
  the dark panel: a known look, left alone (Ben, 2026-10-23)

## 2026-10-22: window #127–#135

- Mode: window
- Range: `ba36ec5..f493a70` (#127 the sweep of #105–#126, #129 the LaTeX authors' layer, #131
  citations and footnotes, #132 the rail, #134 sections, quotes, the agenda and the progress mark,
  #135 image galleries; releases 26.10.7 and 26.10.8); read in four area passes (engine Python; the
  Lua filters; the beamer and revealjs themes; docs, design, CI and make), 54 leads, 26 findings,
  Ben picked the recommendation (`design/sweep-129-135-handoff.md`)
- End commit: `f493a70`
- Done (#136): a vcentered table centered on the height style_tables gives it (the untriaged
  `CELL_PAD` vs `CELL_MAR` item was a defect: 1.6 pt a row short; the one output change, named);
  the pptx steps coloring by role, not theme slot; a gallery drawn on a content slide only in every
  format (`composed_kind()`, `unwrap_galleries()`: HTML skipped one on a closing or feature slide,
  PDF and pptx drew it); the beamer `.full` reader run once; `boxes.references {hang, gap}`,
  `boxes.agenda {gap, number-width}`, `boxes.rail {ring, role}` for numbers three drawers wrote by
  hand (HTML's agenda title now hangs at the number column as PDF and pptx: its extra 0.9 em
  column gap dropped, the one look change); `--engine-leading-<role>` from `livery.css`, 16 scss
  `line-height` literals reading it (21 → 3); the Lua scaffolding (`slide_from`, `split_notes`,
  `is_notes`, `slide_level`, `warn`, `top_level`, `holds_shape`, one loader line, the small filters
  on common, dead code); the pptx idioms (`em`, `inset`, `slide_title`, `space_before`,
  `shape(preset=)`, `ooxml.py`, every Presentation step on `path`, `measure.block_height`); the
  beamer cell box, share width and share error lifted; the scss caption and trim mixins; the tests'
  harness in conftest; the records (six handoff state lines, the changelog's gaps, the Overleaf
  zip's contents named once, the grid-slide definition as `is_grid()`'s list, the small prose); CI
  checking the rendered sample's elements; two ratchets (the theme literal piles may only fall,
  `svg_fallback.DPI` = `fig-dpi`); the skill's gate-drift heuristic and its staging and worktree
  notes
- Tried and dropped: none
- Open (this window's, deferred as a "one look, one key" area sprint over the themes after the
  release, each moving a render): the slide footnotes' numbers (hang 1.1 em beamer / 0.9 em HTML /
  1.2 em beamer's own `\footnote`; rule 12mm×0.6pt vs 120px×2px; gap 0.8ex vs 0.55em; color
  `BrandText!30!BrandBackground` vs muted at 0.6 opacity) → `boxes.footnote`; the beamer's new gaps
  in `ex` where HTML's are `em` (`\enginenote` 0.4ex/0.4em, the quote attribution 0.6ex/.6em, the
  footnotes; Poppins' ex ≈ 0.55 em, so the PDF's are half); the content title band in four copies
  (beamer 0.0489/0.0778/0.1444 with `\ifdefined\engine@ft@bodytop` fallbacks twice, scss
  44px/70px/130px, `livery_template.py`'s `title_top`/`rule_y`) → `geometry.frametitle`; the title
  hairline's three blends (PDF ≈ #DCE3EA, HTML the `rule` blend #A9B8CB, pptx tx1 at 30 % ≈
  #B3C3D7; 0.4pt / 1px / 9525 EMU). Also: `grid.py` (676 lines) into `rail.py`, `agenda.py`,
  `quote.py`; `grid-pptx.lua`'s marker writer composing key=value tails; "of" ×3 →
  `section.progress-label`; `--engine-logo-aspect` and `--engine-full-footline` emitted and unread
  (delete, or HTML's full figure reads the footline and moves 60 px up to the PDF's place); the
  rails-before-status order in `grid-pptx.lua` holding only because the pptx's `fn` is identity;
  the agenda subtitle's 0.15 em gap in HTML and PDF (pptx has none); a both-filters `local function`
  whitelist as an equality pin, if the regrowth guard is wanted

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
  the picture recipes as new public helpers there (`contain_box`, `cover_crop`, `fit_picture`,
  which `slide_layout.py` and `gallery.py` import); `svg_fallback.py`'s rasterizer public as `rasterize_svg(svg, dpi)` (it stays
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
- `build-decks.yaml`: a `framework:` input picking the submodule's tag, so a consumer pins one thing.
- `deck_qa.py`'s `h * 0.16` for the title line (nsi and nasa-jsc-eg sit lower).
- `livery.canvas_scale()` bypassed by `livery_template.py`'s own `self.k`; `livery_build.half` beside
  `livery.half_pt`.
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
  of unequal size (spans or weights). (A picture or table inside a grid-slide column is done: the
  cells-dark sprint, `design/cells-dark-handoff.md`; vector pictures there are rasterized too.)
- From the agenda-quote sprint (#134): pptx draws a quote in a plain column of a grid slide but
  still flattens a strip there to its text (`grid.py` `_flat()`; `_plain_column()` could take the
  strip too); `measure.py` measures an italic quote face upright (`font()` takes a weight, no
  style); the pptx agenda's number sits on its title's line by a hand constant (0.8 of the two
  sizes' difference).
- A citation in a `::: note` is lost in the PDF: `engine-beamer.lua`'s `note_frames()` writes the
  note as raw LaTeX (`pandoc.write`), so citeproc never sees it; the footnote hoist moved to pandoc
  inlines between raw wrappers in the citations sprint, and the note could take the same shape.
- A long reference list in HTML (30 entries on one slide) shrinks to the autofit floor, then
  scrolls under Quarto's `scrollable` and runs over the slide number; the PDF breaks the frame.
- Quarto's `.reveal .slide .columns:nth-child(3) { margin-block-start: 0.8em }` counts a slide's
  children, so a body that starts with columns sits 0.8em lower under cu and nsi (heading, marks
  box, columns) than under ncar, whose content waves add a child (found by the corner-marks
  sprint's parity, 2026-10-24: one marks box per slide keeps it as it was). A theme rule zeroing
  that margin, or pinning it, would make it livery-independent; it moves pixels, so a sweep pick.
- Deferred by the corner-marks sprint (2026-10-24, `design/marks-watermark-mpl-handoff.md` open
  question 2): composed slides taking named corners (their mark and sign-off slots and the logo
  entry's `*-height` keys stay as they were).
