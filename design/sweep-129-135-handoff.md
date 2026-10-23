# Sweep handoff: unplanned-city window #127–#135

**State (2026-10-22):** landed as #136. Departures: the Lua scaffolding went in as seven commits (the walk, warn, top_level, holds_shape, the small filters, dead code, the head comments) and the pptx idioms as four; a gallery outside a content slide is unwrapped into its pictures with a warning in all three formats (not left wrapped: pandoc's pptx writer draws no picture in a Div); `boxes.agenda` took no `sub-gap` (pptx has none); the Python steps, the inner theme and the scss lifts were done by agents in worktrees and cherry-picked; the CI step was split out of a commit it had ridden into.

**For a fresh session.** One PR against `main` (branch `sweep/129-135` from `origin/main` at
`f493a70`, the #135 squash), a commit per finding in the order below, squash-merged once, no
version bump: the release is the PR after this one. The skill is
`.claude/skills/unplanned-city-sweep/SKILL.md`; the ledger `design/unplanned-city-ledger.md`
gets the entry at the end.

## The window

`ba36ec5..f493a70`: #127 (the sweep of #105–#126), #129 (LaTeX authors first-class), #131
(citations and footnotes), #132 (steps and timelines), #134 (sections, quotes, the agenda, the
progress mark), #135 (image galleries), with the two releases 26.10.7 and 26.10.8. Read on
2026-10-22 in four area passes (engine Python; the Lua filters; the beamer and revealjs themes;
docs, design, CI and make), 54 leads, each checked against the code; the baseline is 366 tests
passing on `main`.

**What held:** every element has one reader in `engine-common.lua` and one drawer per format;
the rail and the gallery read every size they draw from `boxes.rail` and `boxes.gallery` in all
three; the beamer layer's shared macros (`\engine@shares`, the role lookup, `\engine@barbox`, the
six save boxes, `\engine@footnoterule`) are one each; the quote's lead/strip rule holds in all
three; no new hex, `white` or palette name entered a theme file; the `.bib` prerequisites,
`parity.sh`'s sed, the Overleaf `latexmkrc` with bibtex, the gallery's disk read under the
container and the CI livery matrix are sound.

**What crept:** the scaffolding around the readers (slide walking, notes splitting, warnings,
the slide level), numbers each sprint invented alike in three places instead of a livery key
(the references hang, the agenda row, the rail ring, the footnotes, the leading), small pptx
idioms the five drawers each spelled their own way, and records that stopped agreeing.

## Ben's picks (2026-10-22): "proceed with the recommendation"

Picked: 1–7 (3 gated to content slides in every format), 12–16, 19–26. Deferred to the ledger:
8, 9, 10, 11 (each moves a render and wants its own side-by-side), 17, 18. A retrospective along
the way may reorder; a finding that measures flat or costs more than it saves is dropped and
recorded with its numbers.

## Commits, in order

0. **This handoff.**

### A. Defects and divergences

1. **A vcentered table is centered on the wrong height.** `slide_layout.py:56` `CELL_PAD =
   Pt(7.2)` (PowerPoint's default 0.05 in margins) is `_table_height`'s default (`:86`) and what
   `vcenter` uses (`:169`), but `style_tables.py:27,110` sets every cell's `marT`/`marB` to
   `CELL_MAR` (0.4 of the table size), which `note_place` (`slide_layout.py:254`) already
   passes. On ncar (table 11 pt) the estimate is 1.6 pt per row short. `_table_height` defaults
   to `2 * style_tables.CELL_MAR`; `CELL_PAD` goes. **Moves pptx**: a vcentered table rises
   ~0.8 pt per row; parity shows which slides.
2. **The pptx steps read theme slots where HTML and PDF read roles.** `style_footnotes.py:29`
   (`accent4`, the mark; HTML `var(--engine-accent)`, beamer `BrandAccent`),
   `slide_layout.py:638,641` (`accent4` the feature tab, `accent1` its rule),
   `style_tables.py:22` (`dk2`, the head rule; its own comment says `--engine-primary`). A
   livery overriding a slot (`pptx.scheme`) would split pptx from HTML silently.
   `livery.hex(LIVERY, role)`; `scheme()` stays for the template and the `custClrLst` check.
   Flat on every bundled livery (their `scheme:` overrides touch only the link slots).
3. **A gallery on a `.closing` or `.feature` slide**: `engine-revealjs.lua:365` gates
   `galleries()` on `C.content_heading`, `engine-beamer.lua:433,721` and `grid-pptx.lua:229`
   run `top_galleries` on every slide. Gate all three on content slides (the pick); a gallery on
   a composed slide warns and stays its pictures, as a nested one does. Nothing in the decks
   hits it; a test holds the three to it.
4. **Beamer runs the `.full` reader twice.** `engine-beamer.lua:621-642`: the local
   `split_full` calls `C.split_full`, and `:642` calls `C.split_full` again on the same slide;
   `gallery_items` mutates image attrs, so the order is fragile. One call.

### B. One concept, one livery key (flat where the numbers are kept)

5. **`boxes.references {hang: 1.5, gap: 0.4}`.** Four hand copies: `beamerinnerthemeEngine.sty:250`
   (biblatex) and `:258-263` (CSLReferences), `engine-revealjs.scss:678`,
   `slide_layout.py:63-65` (`REF_HANG`, `REF_BEFORE`). `livery_build.BOXES`, the schema and
   `REFERENCE.md`, `emit_sty_boxes`/`emit_css_boxes`, every livery's `build/`, the three drawers,
   `test_boxes.py::test_every_key`. Flat.
6. **`boxes.agenda {gap: 0.55, number-width: 2}` and `boxes.rail {ring: 0.2, role:
   primary-contrast}`.** The agenda's row gap and number column by hand in `grid.py:294`,
   `engine-revealjs.scss:439-448`, `beamerinnerthemeEngine.sty:231`; the ring in `grid.py:573`,
   `scss:574`, `sty:792`; the rail's default role in `grid.py:527`, `engine-common.lua:674`,
   `sty:718`. HTML also adds `column-gap: 0.9em` (`scss:439`), so its title sits 2.9 em in where
   PDF and pptx sit at 2: drop it (HTML's agenda title moves 0.9 em left; name it). The pptx
   agenda's 0.8 ascent offset (`grid.py:326`) stays pptx's: HTML gets the same from its
   line-height calc. Flat but for the HTML column gap.
7. **Leading.** `livery.json type.roles.*.leading` is read by beamer (`\engine@fsof`) and
   ignored by HTML: `emit_css` (`livery_build.py:1060-1067`) writes `--engine-type-<role>` only,
   and the scss restates the leading as 21 `line-height` literals (16 at `ba36ec5`; the quote
   1.3, agenda title 1.2, rail badge 1, rail title 1.2, gallery caption 1.3 added this window).
   `emit_css` writes `--engine-leading-<role>` beside each size; the scss reads
   `var(--engine-leading-<role>)` where a literal equals a role's leading (quote 1.3, caption
   1.3, subhead 1.2, title 1.12, section/closing 1.08, footnote 1.35, fineprint 1.4, marking 1.2
   all match); the agenda number's calc, the badge's 1 and `$presentation-line-height` stay.
   Flat: screenshots prove. The remaining count is ratcheted (26).

### C. Lifts (mechanical, flat; `make test` and parity prove)

12. **Lua scaffolding.** (a) The slide walk and the body/notes split hand-written 13 times
    (`engine-beamer.lua:125-134,163-168,780-781,795-800,826-830`;
    `engine-revealjs.lua:165-170,366-375,437-448,805-810,820-825,858-859`;
    `inline-footnotes.lua:33-36,57-61`; `engine-common.lua:232-240,441-448`) → `C.slide_at` and
    `C.split_notes`. (b) `C.is_notes(b)` for the 17 sites in three spellings. (c)
    `C.slide_level()`: the level read seven ways (`slide-layout.lua:75`, `single-body.lua:188`,
    `inline-footnotes.lua:49-50`, `grid-pptx.lua:281-282`, `notes-last.lua:16`,
    `linked-images.lua:69`, the two filters' upvalues); the two `if level == 0` guards are dead
    (pandoc 3.8.3 gives nil, never 0) and the two `is_slide_break` wrappers
    (`engine-beamer.lua:97`, `engine-revealjs.lua:133`) go with the upvalue. (d) `C.warn`
    exported: four idioms (`engine-common.lua:179` local, `quarto.log.warning` direct at
    `:23,116,564` and in both filters, `grid-pptx.lua:70-72` its own stderr shape) and an
    inconsistent `who`. (e) `top_rails`/`top_galleries` (`engine-common.lua:728-745,859-875`)
    one `C.top_level`; the nested warning in one place (`grid-pptx.lua:140-145,211-216` restate
    it), and the warned Div loses its `role=` (today `role="primary"` reaches HTML as an invalid
    ARIA role; `card_attrs:545` and `rail_items:673` strip it for that reason). Test texts
    assert the warning sentence: keep it byte-identical. (f) `C.holds_shape` for the four
    spellings (`engine-common.lua:490-491,686-687`, `grid-pptx.lua:103-110`,
    `single-body.lua:28-53`; single-body is pandoc-sensitive: parity even though flat). (g) The
    three `here()` copies (`grid-pptx.lua:63-66`, `slide-layout.lua:16-19`,
    `inline-footnotes.lua:21-24`); `notes-last.lua:23` and `linked-images.lua:76` onto
    `C.is_slide_break`; `linked-images.lua:16-23` and `diagram-dark.lua:12-25` drop their
    unreachable env/`_livery` fallbacks for `C.load_livery` (diagram-dark keeps its `pcall`).
    (h) Delete: `engine-beamer.lua:590` `raw` (is `latex_inline`); `engine-revealjs.lua:691-692`
    the unread `c.primary`, `c.primary_text`, `c.secondary`; its second `local raw` (`:863`);
    common's unread exports (`default_livery`, `status_item`, `quote_parts`, `has_cites`,
    `RAIL_MAX`, `GALLERY_MAX`, `LAYOUT_CLASSES`) unless a test wants one. (i) The three filters'
    head comments and `_extension.yml`'s grid-pptx comment list what is shared: bring them up
    to the elements. One commit per letter where a letter stands alone, else grouped.
13. **pptx idioms the five drawers each rewrote.** (a) `common.slide_title(slide)` for the
    warning's title (`gallery.py:61-63`, `grid.py:335-336,395-396`,
    `slide_layout.py:716-718`); `common.space_before(p, pts)` (`grid.py:156-165` and
    `gallery.py:49-57`, the same seven lines); the four-margin inset ×8 (`grid.py:128,221,273,
    424-425,431-432,552`, `slide_layout.py:116,628`) as `common.inset(tf, v, h)` or a `pad=` on
    `body_box`; one vertical-anchor idiom (`tf.vertical_anchor`; raw `bodyPr.set("anchor")` at
    `grid.py:505,547`, `gallery.py:87`, `slide_layout.py:153`); `common.em(v, pt)` for the
    em→EMU by hand (`grid.py:294,326`, `slide_layout.py:227`, `style_tables.py:27`; `pads()`
    rounds correctly and says why); `grid._oval()` (`:483-495`) as `common.shape(...,
    kind=MSO_SHAPE.OVAL)`; `style_tables.py:120-122` is `measure.other_size()`;
    `livery.BODY_INDENT_PT = 18` beside `SPC_BEFORE` for `livery_template.py:179` (`228600 *
    k`) and `measure.py:198` (`Pt(18 * K)`). (b) A livery-free `pptx_steps/ooxml.py` (`NS`,
    `parse`, `serialize`) for the copies in `section_subtitle.py:27-32,62-67`,
    `svg_fallback.py:22-25,32`, `type_step.py:23-24,70`, `embed_fonts.py:39` (not common.py:
    it loads the livery at import, which svg_fallback must not). (c) Every Presentation-stage
    step takes `path` and prints `path.name` with `→` (`run(prs, name)` in 8 steps vs
    `run(prs, path)` in 3; `pptx_post.py:56-64`; `type_step.py:71`'s `->`). (d)
    `section_subtitle.py:52` `LINE = 1.4` beside `measure.LINE = 1.2`: `HEAD_LINE`, and
    `measure.block_height()` for its own text-height recipe (`:202-211`). Identical XML.
14. **Beamer inner theme.** The cell-box prelude written twice (`\enginecard` 630-635,
    `\engine@railbox` 737-741; `\enginefeaturepanel` 297 its width half) → `\engine@cellbox`;
    "share of the line less the gaps" three ways (410, 618-619, 731-732) →
    `\engine@sharewidth`; the "k has no share" error ×3 (434, 605, 728) → `\engine@noshare`;
    `\engine@railpt` renamed `\engine@pt` (the gallery's point macro too, 849-927). Identical
    expansions: `test_latex.py` and `parity-latex` prove.
15. **scss.** `.engine-card-title` (469) ≡ `.engine-rail-title` (577): one selector list; the
    trim pair ×5 (407, 473, 503, 585, 428) → a `%trim` placeholder; the caption look ×6
    (266-272, 300-322, 634-643, 1111-1125, 424) → `@mixin caption`; the body-height calc ×2 and
    the padding ×2 → Sass variables. The compiled css is identical, or screenshots prove.
16. **Tests.** `conftest.py` gets `ENGINE`, `pandoc_exe()` (the locator written 14 times),
    `lua_common(tmp_path, body)` (the `quarto` shim restated 6 times in three variants),
    `flat()` (`test_grid.py:94`, `test_gallery.py:251`) and `tmp_livery` as a fixture
    (`test_quote.py:29` imports it from `test_boxes`).

### D. Records and prose

19. **State lines** on `latex-first-class-handoff.md` (#129, `cedc348`),
    `citations-handoff.md` (#131, `3f20a94`), `steps-timelines-handoff.md` (#132, `cc79d84`),
    `agenda-quote-handoff.md` (#134, `87ebef1`), `gallery-handoff.md` (#135, `f493a70`; its three
    open questions answered: gap 0.006 and pad [0.15, 0.15], the names kept, no quickstart
    gallery) and `sweep-105-126-handoff.md` (#127, `f2fd66d`), each with the PR's departures;
    the citations handoff's deferred list (`:248-254`, stale: the image grid is done) becomes
    a pointer at the ledger.
20. **The ledger**: the sprint entry at its top (`:24-33`) is a third idiom for a sprint's own
    record; its three open items go to Untriaged and the entry goes (sprint records live in the
    handoff's state line). The "kept privately" line (`:64`) is wrong: `contain_box`,
    `cover_crop` and `fit_picture` are public in `pptx_steps/common.py`.
21. **CHANGELOG `[Unreleased]`**: the sample's new slides per element (35 → 43 over #131–#135;
    only the agenda's are recorded); `boxes.quote` entered twice (`:85-91` and `:95-98`); the
    biber sentence (`:98-99`) a fragment; `texlive-bibtex-extra` in the image unrecorded
    (decide once: the image's packages are a Decks-level fact when a deck needs them).
22. **The grid-slide definition** against `is_grid()` (`engine-common.lua:484-495`: more than
    two columns, a card, a lead, a strip, a quote in a column, a rail, a gallery) in
    `_extension.yml:63-66`, `docs/formats.md:75-77,111-116` (and `gallery.py` missing from the
    step list under `grid`), `pptx_post.py:60`, `CLAUDE.md:589-590`: state the list once above
    `is_grid()`, the prose says what it counts.
23. **The Overleaf zip's contents** in `CLAUDE.md:194-197` (the starter only), `:523-524` and
    `latex/README.md:10-13` (no bibliography, no images): "the cookbook and the files it needs
    (`overleaf_zip.py`'s `COOKBOOK_FILES`)".
24. **CI checks the rendered sample's elements**: after `ci.yaml:146-165`'s citations step, the
    HTML holds `engine-rail`, `engine-quote`, `engine-agenda`, `engine-gallery`; the pptx has
    groups named `Steps`, `Timeline`, `Quote`, `Agenda`, `Gallery` and no text frame holding
    `⟦engine:`; the PDF's text has an agenda row.
25. **Small prose**: `test_gallery.py` among the harness users (`CLAUDE.md:536-538`); ci.yaml's
    hand test summary (`:343-347`) cut to its last clause; `liveries/README.md:64-68` names
    `boxes.gallery`; `docs/authoring.md:424` "(1), (2)" only past one page; `centred`/`centres`
    in `CLAUDE.md:181,290,318,320,496` and `README.md:111` (released changelog sections stay the
    tag's); the roadmap's superseded vendoring sentence (`engine-and-liveries.md:349-351`) and
    a closing line on §7 pointing at the handoffs.
26. **Ratchets**: `tests/test_cli.py` style, going down only: scss `line-height` literals (after
    7), `#fff`/`white` (14), `letter-spacing` (4), `rgba(#fff` (7); beamer `white` (7);
    `svg_fallback.DPI` equal to `common/_quarto.yml`'s `fig-dpi`.

27. **The ledger entry** (window, range, end commit, done, dropped with numbers, open) and the
    deferred findings below onto Untriaged.

## Deferred (to the ledger)

- **8. Slide footnotes**: both themes invent every number and disagree (hang 1.1 em beamer /
  0.9 em HTML / 1.2 em beamer's own `\footnote` at `sty:990`; rule `12mm`×`0.6pt` vs
  `120px`×`2px`; gap 0.8 ex vs 0.55 em; color `BrandText!30!BrandBackground` vs muted at 0.6
  opacity; `sty:344-352,988-993`, `scss:688-720`) → `boxes.footnote {rule, rule-color, width,
  hang, gap}`, and `style_footnotes.py` could draw the rule. Moves both.
- **9. ex vs em**: the beamer's new gaps in `ex` where HTML's are `em` (`\enginenote` 0.4ex vs
  0.4em, attribution 0.6ex vs .6em, footnotes 0.8ex/0.4ex vs .55em/.3em; `sty:348,352,362,559`);
  Poppins' ex ≈ 0.55 em, so the PDF's gaps are half. Write them as `\engine@typebody` shares.
  Moves the PDF a few points.
- **10. The content title band** in four copies: beamer 0.0489/0.0778/0.1444/0.0222/0.0178
  (`outer:114-143`) and 0.1667 (`inner:858`) with `\ifdefined\engine@ft@bodytop` fallbacks
  twice; scss 44px/70px/130px (`:159-189`) and the 150px fallback; `livery_template.py:~205`
  `title_top`/`rule_y` → `geometry.frametitle {top, height, rule}` emitted always. Flat by
  construction; `make measure` proves.
- **11. The title hairline, three blends**: PDF `BrandSurface!70!BrandText!40!BrandBackground`
  ≈ #DCE3EA (`colortheme:18`), HTML the `rule` blend #A9B8CB (`scss:193`), pptx `tx1` at 30 %
  over the background ≈ #B3C3D7 (`livery_template.py:207`); thickness 0.4pt / 1px / 9525 EMU.
  Predates the window. All three the `rule` blend: the PDF's hairline darkens visibly.
- **17.** `grid.py` (676 lines) into `rail.py`, `agenda.py`, `quote.py` once 13 makes their
  shared privates public; it reads fine as one module.
- **18.** `grid-pptx.lua`'s marker writer composing key=value tails (today `marker()` and
  `prefixed()` both spell the brackets, the tails by hand ×7); "of" ×3 (`inner:119`,
  `scss:894`, `section_subtitle.py:223`) → `section.progress-label`; `--engine-logo-aspect`
  and `--engine-full-footline` emitted by `emit_css` and read by nothing (delete, or HTML's full
  figure reads the footline and moves 60 px up to match the PDF); the rails-before-status order
  in `grid-pptx.lua:280` holds only because the pptx's `fn` is identity (record the reason or
  move the pass).
- A both-filters `local function` whitelist (the 11 drawer names) as an equality pin in
  `test_cli.py`'s style, if the regrowth guard is wanted: the count is not going down.

## Verification

- `make test` after every commit (366 on `main`).
- `tests/parity.sh baseline` and `tests/parity-latex.sh baseline` taken on `main` before the
  first code commit; `check` after 1 (the vcentered tables' deltas, named in the commit), after
  2–4 (flat), after 5–7 (flat but 6's HTML agenda), after 12–16 (flat).
- 7 and 15: every slide of the sample screenshotted before and after (Playwright), compared.
- `make -C decks/sample qa`; `tests/app-open.sh` is the release's step.
