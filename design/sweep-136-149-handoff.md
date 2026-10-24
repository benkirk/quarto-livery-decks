# Sweep handoff: unplanned-city window #136–#149

**State (2026-10-24):** landed as #150 (open for `/pr-review 150`, then the squash merge and the
release 26.10.12): Tier 1 and 2 a commit per finding, nothing dropped, and finding 9 (the table
rules, `boxes.table`) picked by Ben after them; findings 26–31 on the ledger's Untriaged list.
Departures: `DARK_BOXES` stays in `livery_build.py` (its values are css selectors), beamer's swap
keeps `primary` out (a card head would turn secondary) and the dark boxes need no `BrandText`
snapshot (`\engine@lightcolors` restores beamer's own); `comp_of()` lives in `livery.py` (common.py
loads a livery at import, which the template builder cannot); the step-list diagram is the
quickstart's `09-full.png`, not `07-mermaid`; `QA_PPTX_FAIL=1` waits on the caution glyph's hint
(ledger); the PDF's table rules thin (1.5 to 0.85 pt, 0.6 to 0.28 pt), the pptx's by 1%.

**For a fresh session.** One PR against `main` (branch `sweep/136-149` from `origin/main` at
`de1ce55`, the #149 squash), a commit per picked finding in the order below, staged by file,
squash-merged once, no version bump: the release (26.10.12) is the PR after this one. The skill
is `.claude/skills/unplanned-city-sweep/SKILL.md` (section 6 for the method: parity baselines on
`origin/main` first, `tests/parity.sh` and `tests/parity-latex.sh`, worktrees for disjoint
files); the ledger `design/unplanned-city-ledger.md` gets the entry at the end, and the unpicked
findings go to its Untriaged list.

## The window

`f493a70..de1ce55`: #136 (the sweep of #127–#135) and #138 (the "one look, one key" themes
sweep) and #139 (the docs sweep), which were sweeps themselves; the four sprints #145
(consumer friction), #146 (nasa-ccp, named marking strips, cover fine print, `frametitle.color`),
#148 (pictures and tables in grid cells, the dark slide) and #149 (corner marks, the watermark,
`livery_mpl` from pip); the releases 26.10.9, 26.10.10 and 26.10.11. Read on 2026-10-24 in four
area passes (engine Python; the Lua filters; the beamer and revealjs themes with the emitters;
records, docs, CI, make, tests and liveries), each lead checked against the code at `de1ce55`;
the claims that move a render were verified by hand (a one-frame XeLaTeX build for 1, the ten
`livery.json`s for 9, the four `_qa/report.txt`s for 2). The baseline is 521 tests passing.

**What held:** the window's three new concepts are data read once per format: the content
furniture (`livery_build.furniture()`, read by the template master and `draw_dark`), the corner
marks (`corner_marks()`, `furniture.marks`, the three loops) and the watermark (`watermark_text()`,
one gate: every slide in all three, the same ink rule); the marking strips and the card border
read their boxes alike; `livery.mark()`, `take_marker`, `caption_para`, `fit_picture`,
`is_dark`/`palette` have no hand-rolled twin left; no `geometry.logo`/`signoff` reader, no
`\engine@logo@*`, no content-slide `::after` survives; the ten liveries, the schema and
`REFERENCE.md` are on the new keys; the white/hex/`!important` ratchet is unchanged (3/4/0/0);
the release pins hold at 26.10.11; CI's livery matrix is `ls liveries/*/`, so nasa-ccp is in it;
no test writes outside `tmp_path`.

**What crept:** three defects at the edges of the dark slide and the strips (1, 3, 4, 5); the
dark slide's swapped-role set as three hand lists (6); the fine print decided per drawer where
the strips and watermark have one reader (7); `make qa`'s new pptx path drowned by the slide
number (2); the table rules on different roles and units per format, pre-window but now visible
(9); the records of sprint B and the roadmap still saying "awaiting review" (12); and the usual
small lifts.

## Findings, ranked (value over cost)

**RENDER** marks a change to what a deck renders. Lines are `main` at `de1ce55`.

### Tier 1: defects and the records, before the release

1. **gate / silent path — the PDF's lead, strip and caution body on a dark frame draw on-dark
   text on their light fills (invisible).** `beamerinnerthemeEngine.sty:390-403`
   (`\engine@barbox` sets no text color), `:404` (`enginecaution`), `:410-411` (`enginelead`),
   `:544-558` (`enginestrip`: only a solid card's sets one); `beamerouterthemeEngine.sty:537-554`
   (`\engine@darkcolors` → `\engine@fieldcolors{BrandOnDark}`; the comment at `:525-530` says a
   card keeps its colors, and only the card does, `:612`). HTML restores the roles in the box
   (`livery_build.py:1522` `DARK_BOXES`, `:1537` the caution body), pptx keeps them
   (`grid.py:768-771`, `slide_layout.py:719`); `CHANGELOG.md:38` promises it in every format.
   Verified: a one-frame ncar deck with `[enginedark]` holding `enginelead`, `enginestrip` and
   `enginecaution` renders three empty light bands. No bundled deck has one (the sample's and the
   cookbook's dark slides hold lists and cards), so no test reaches it. *Proposal:* the barbox
   environments set their text from a `BrandText` snapshot (add it to `\engine@darkswapped`, as
   `BrandMuted` is), and `tests/test_latex.py`'s dark frame gains a lead and a strip. *Cost:* 2
   theme files + the test; parity flat. *Risk:* **RENDER** for a consumer deck with one of them on
   a dark frame (a fix).

2. **silent path — `make qa`'s pptx path reports the slide number as "past the right margin" on
   every slide of a bottom-right livery.** `common/utils/deck_qa.py:236-240` (the edge loop over
   every word) runs before `frame_number()` is taken at `:243` (`:161-165` already finds it in
   either bottom corner). Under nsi today: sample 47 of 48 `hint pptx` lines, quickstart 13 of 13,
   plots 14 of 15; cu, nasa, nasa-jsc-eg and nasa-ccp share the corner. With a hint per slide
   nobody reads the real ones (the sample's s27 footer collision, the caution slides' `⚠︎`/`A`
   overlap), and `QA_PPTX_FAIL=1` (the step's stated goal, `pptx_pdf.py:8-9`) can never be
   switched on. *Proposal:* take `n = frame_number(...)` first and skip it in the edge loop; re-read
   the four reports, and if they go quiet run CI's sample `make qa` with `QA_PPTX_FAIL=1`.
   *Cost:* deck_qa.py, a case in `tests/test_deck_qa.py`, maybe ci.yaml. *Risk:* none to a render;
   a CI failure becomes possible, which is the point.

3. **gate — HTML's marking strips skip a slide opened by `---` or by blocks before the first
   heading; PDF and pptx draw them on every slide.** `engine-revealjs.lua:439-449` (`add_marking`
   inserts after a Header of level 1 or `slide_level` only) against `beamerouterthemeEngine.sty:377-385`
   (every frame's background), `marking.py:36` and `watermark.py:53` (`for slide in prs.slides`);
   HTML's own `add_watermark` (`:455-467`) walks `HorizontalRule` breaks. The one input: an
   untitled slide under nasa-ccp or nasa-jsc-eg has no CUI banner in HTML alone. *Proposal:* one
   per-slide tail walk (the watermark's) appends both strips and watermark; the marks box stays
   heading-gated (the `.columns:nth-child(3)` count, untriaged). *Cost:* engine-revealjs.lua + a
   test in `test_marking.py`. *Risk:* **RENDER** on untitled HTML slides only (a fix).

4. **gate — `## X {.full .brand-dark}` parts the formats.** beamer's `CONTENT_KINDS`
   (`engine-beamer.lua:86,157-160`) lets a `.full` frame take `enginedark`; HTML
   (`engine-revealjs.lua:160`, `SLIDE_KINDS`) and pptx (`slide_layout.py:779-795`: the `full`
   branch returns before `draw_dark`, and `full_slide` `:296` colors its caption with the static
   `CAP_COLOR`) ignore it. *Proposal:* gate alike, the cheap way: a `.full` or `.feature` slide
   ignores `.brand-dark` in beamer too (the picture fills it; `take_layout()` warns once). *Cost:*
   engine-beamer.lua or engine-common.lua. *Risk:* **RENDER** only for a deck that combines them.

5. **gate — an HTML dark slide's inline code in a caution body.** `engine-revealjs.scss:1100`'s
   `:not(:is(.engine-card, .engine-lead, .engine-strip, .callout) *)` is a hand copy of
   `DARK_BOXES` that lacks the caution body `emit_css_dark_slide` restores (`livery_build.py:1537`):
   `code` there takes the `dark-code` field and `warning` text on the pale-yellow fill. Folds into
   6. *Risk:* **RENDER** (HTML, a fix).

12. **retire — four records of sprint B and the roadmap still say "awaiting review".**
    `design/roadmap-catalogue.md:3` (sprint B "awaiting `/pr-review`; the sweep and the release
    not started"); `design/marks-watermark-mpl-handoff.md:3` (no review, squash or merge) and
    `:337-349` ("Open questions for Ben" lists 1, 3, 4, 5, 6 as open while the State line at `:3`
    records his picks on each; Q2 alone is open, in the ledger); `design/cells-dark-handoff.md:3`
    (never says merged) and `:313` ("capped at 8 MB" where the State line and CLAUDE.md say 6 MB);
    `design/consumer-friction-handoff.md:3` (no #145, no `7685f59`, no "released in 26.10.11");
    `design/engine-and-liveries.md:375-380` (the dated-handoff list stops at `gallery-handoff.md`
    #135: five handoffs since). *Proposal:* one commit of State lines (PR, squash SHA, release),
    the open-questions block marked answered, the roadmap's State, the design log's list through
    #149. *Cost:* 5 files, prose. *Risk:* none.

13. **prose — the quickstart's pipeline diagram and `docs/formats.md`'s step list miss the
    window's two changes.** `decks/quickstart/quickstart.qmd:183,185` (`diagram-dark` after
    `grid-pptx`; the steps end `marking, type_step`) and `docs/formats.md:129-133`, against
    `_extension.yml:79-86` (`diagram-dark` before `grid-pptx` since #148) and `pptx_post.py:67-69`
    (`watermark` between `marking` and `type_step` since #149). The diagram is a README hero image
    (`07-mermaid.png`, `screenshots.py:37,44`) that #139 made "list every filter and step".
    *Proposal:* fix both lists; `make screenshots` and commit the PNG. *Cost:* 2 files + a committed
    image. *Risk:* none to a deck.

14. **prose — `CHANGELOG.md:84` "Nothing to do." under the mandatory marks reshape.** The
    Unreleased Liveries section's first bullet (`:52-70`) says every livery of your own moves its
    keys with no alias; the derived-furniture bullet then opens "Nothing to do", the phrase the
    26.10.10 and 26.10.11 sections use as a section's verdict (`:168,258,264`). The release PR
    turns this section into the notes. *Proposal:* "`livery.json` gains `furniture` … (derived;
    nothing to do for them)". *Cost:* one line.

### Tier 2: consolidations and lifts that measure flat

6. **consolidate — the dark slide's swapped-role set is three hand lists.** `livery_build.py:1520-1522`
   (`DARK_SWAP`, `DARK_BOXES`: HTML), `pptx_steps/common.py:119-123` (`DARK_INK`: the same six
   pairs retyped with a comment naming `DARK_SWAP`, plus background→dark), `beamerouterthemeEngine.sty:484`
   (`\engine@darkswapped`: four names) and `:552-553` (the colorlet pairs; beamer swaps the same
   set minus `primary`, harmless today), and the scss copy of `DARK_BOXES` at `:1100` (finding 5).
   No test pins them. *Proposal:* `DARK_SWAP` and `DARK_BOXES` into `livery.py` (the reader both
   Python drawers import; `BrandText` added for 1), `common.DARK_INK` built from it, `emit_sty`
   writing `\engine@darkswapped` and the colorlet pairs, `emit_css_dark_slide` emitting the
   code-on-field rule through a `--engine-code-field` property so the scss `:1100` goes. *Cost:*
   5 files, every `build/livery.{sty,css}` regenerated (`livery build --check`). *Risk:* flat but
   for 5.

7. **consolidate — the cover fine print is decided per drawer.** `engine-revealjs.lua:766-773`
   (reads `tcomp.fineprint.paragraphs`, handles `none`), `engine-beamer.lua:752-767` (writes
   `\titlefineprint{}` only when the deck sets it; the `.sty` holds the default,
   `beamerouterthemeEngine.sty:352-354`), `slide-layout.lua:73-96` (`fineprint_meta`: the deck's
   text as written, `none` passed through), `slide_layout.py:524-536` (`cover_fineprint` decides
   again). The `stringify(fp) == "none"` test is in three files; two `docProps/custom.xml` idioms
   result (`engine-fineprint` absent-means-default; `engine-marking-*`/`engine-watermark` always
   written, `none` for none). The strips and the watermark have one reader (`marking_texts()`,
   `watermark_text()`, `engine-common.lua:482-511`); #146 landed the three elements in two shapes.
   *Proposal:* `C.fineprint_paragraphs(meta, comp)` in engine-common (the deck's, `none`, else the
   composition's), each drawer drawing what it returns; slide-layout.lua always writes
   `engine-fineprint` with the `none` sentinel; `cover_fineprint()` reads the string only. *Cost:*
   5 files + `tests/test_fineprint.py`; flat (the same text in the same box); `make measure` does
   not read the box. *Risk:* none intended.

8. **consolidate — a pptx layout's composition is named in three places.** `livery_template.py:49-51`
   (`FIELD_LAYOUTS`, `Builder.comp_name()` `:322-324`), `pptx_steps/watermark.py:29-34` (`BAND`,
   `LAYOUT_COMP`: the window's copy), `slide_layout.py:803` (its own `BAND` at `:72`); the feature
   slide recognized by the shape name `"Photo"` at `watermark.py:42`, set at `slide_layout.py:442,642`.
   *Proposal:* one `comp_of(layout_name, band)` in `pptx_steps/common.py` (or `livery_template`),
   `PHOTO = "Photo"` named once. *Cost:* 3 files; flat.

10. **lift — Lua helpers copied by #148.** `engine-common.lua:1037` and `grid-pptx.lua:138` (the
    rendered-source test `figure%-[%w%-]+/` or `_files/`), `engine-common.lua:1086` and
    `grid-pptx.lua:139` (the percent-decoder), `grid-pptx.lua:203-204` (`C.simple_table(b)` parsed
    in the `elseif` and again in its body). *Proposal:* `C.is_rendered(src)`, `C.decode_src(src)`;
    `flow()` keeps the parsed table in a local. *Cost:* 2 files; flat.

11. **bypassed helper — `cell_figure()` says "as every format draws it" and only pptx reads it.**
    `engine-common.lua:957-963`; the one caller `grid-pptx.lua:184`; beamer's `card_body`
    (`engine-beamer.lua:268-295`) keeps its two-call walk (`C.latex_figure`, `C.para_images` with
    its own one-image rule, a `.cell` Div left to pandoc). *Proposal:* `card_body` reads
    `cell_figure()` for the picture cases, or the docstring says pptx's. *Cost:* engine-beamer.lua;
    parity on the sample's "Pictures in cards" and the plots' "Plots in cards" PDF pages. *Risk:*
    possible **RENDER** in the PDF if an executed plot's `.cell` Div in a card newly takes the card
    picture's width; parity decides, and the docstring fix is the fallback.

15. **lift — `table_height` lives in the 806-line step and two leaves import it.** `figures.py:38`,
    `grid.py:57` (`from .slide_layout import ... table_height`); the measuring code
    `slide_layout.py:86-116` reads only `measure.para_lines`, `measure.LINE`, `other_size`,
    `style_tables.CELL_MAR`. *Proposal:* `measure.table_height()` with `CELL_MAR` moved to
    `common.py` (measure cannot import style_tables, which imports measure). *Cost:* 5 files; a move.

16. **drift — `common.is_dark()` hand-parses the notes line `take_marker()` owns.**
    `pptx_steps/common.py:126-141` (`startswith("engine-layout:")` at `:138`), `slide_layout.py:56`
    (`MARKER`), `common.take_marker()` `:97-114`. *Proposal:* `LAYOUT_KEY` in common and a
    non-consuming `peek_marker(slide, key)` sharing `take_marker`'s loop. *Cost:* 2 files; flat.

17. **drift / ratchet — the HTML furniture list kept twice by hand.** `engine-revealjs.js:35` (the
    autofit's skip list) and `common/utils/deck_qa.py:79` (`MEASURE_JS`'s, the same plus three
    QA extras); the window added `.engine-marks, .engine-marking, .engine-watermark` to both in
    lockstep, nothing pins them (`test_slide_kinds_agree` pins `NEVER`, not this). *Proposal:* the
    JS exposes its selector and `MEASURE_JS` reads it, or a `test_cli` pin that the JS list is a
    subset of deck_qa's. *Cost:* 2 files; flat.

18. **drift (roles only) — `linked-images.lua` loads the livery for one hex it writes by hand.**
    `:60` (`load_livery(...).roles.muted`), `:44` (`color:#..` on the HTML link), `:52`
    (`\textcolor[HTML]{..}`); the only hand hex in the Lua layer, and a second `load_livery` per
    HTML and PDF render for it. Pre-window. *Proposal:* a class on `var(--engine-muted)` and
    `\textcolor{BrandMuted}`; the loader goes. *Cost:* linked-images.lua + one scss rule; flat.

19. **delete — keyword defaults no caller uses, and pyflakes trivia.** `style_footnotes.py:73`
    `color=None` with `FOOT_COLOR` `:34` as the fallback (both callers pass one, `:123`,
    `slide_layout.py:206`); `style_tables.py:93` `ink=LIGHT_INK` (the one caller passes
    `palette(slide)`); `common.py:307` `caption_para(p, color=None)` (three callers pass none;
    `grid.darken()` recolors). Unused: `livery_template.py:19-20` `json`, `sys`; `:363`
    `body_bottom`; `livery_schema.py:13` `sys`; `comp_measure.py:17` `glob`. *Cost:* 6 files; flat.

20. **lift — the pptx-step harness written four times across the window's tests.**
    `tests/test_watermark.py:91-114`, `test_fineprint.py:25-33,86-92`, `test_marking.py:26-31,65-72`,
    `test_boxes.py:167-182` (the same `STEP` + env + `subprocess.run` triple), `test_dark_slide.py:79-83`;
    `flavor()` twice (`test_marks.py:32-46`, `test_fineprint.py:34-42`) beside `conftest.tmp_livery`;
    the title-placeholder lookup at `test_marks.py:76`, `test_frametitle.py:52,83`; the env scrub at
    `test_cli.py:152,189`; `test_watermark.py:105-109`'s in-function imports. *Proposal:* conftest
    gains `run_steps(tmp, pptx, steps, livery_dir)` and `flavor(tmp, block, parent)`; two one-line
    helpers for the rest. *Cost:* conftest + 6 test files.

21. **lift — "placeholders to a file, then `DECK_META=`" hand-rolled three times.**
    `_extensions/engine/livery.py:262-266` (`check --qa`), `decks/quickstart/gallery.py:27-34`,
    `.github/workflows/ci.yaml:567-569`; each re-derives "nothing printed means no DECK_META" and
    picks its own path. *Proposal:* `livery placeholders <dir> -o FILE` printing `DECK_META=FILE` or
    nothing, each caller one `$(…)`. *Cost:* livery.py + 3 callers; flat.

22. **consolidate — CI's pip probe re-tests half of `test_use_zip`.** `ci.yaml:368-401` (venv,
    pip install, a heredoc probe: the unpack, the cache path by its own formula, the fonts, the
    cycle, a PDF plot, `pdffonts`) against `tests/test_cli.py:167-196` (`test_use_zip`: the unpack,
    cache, fonts and cycle on the engine's module) and `:135-164`; `make test` runs one step earlier
    (`:365`). What only the step proves: the real hatchling wheel and the PDF's embedded family.
    *Proposal:* trim the probe to those. *Cost:* ci.yaml.

23. **drift — the lead-after-figure gaps.** `grid.py:744,777` (`em(0.5)`: the flow's start under
    pandoc's caption box, the table under the flow) and `:745` (`em(1)`, the "beside" test) are
    neither `NOTE_GAP` (`slide_layout.py:62`) nor `boxes.note.gap` (what `figures._caption_box`
    `:117-118` and the `::: note` use), so a lead under a figure sits at a third gap. `grid.py`
    went 654 → 785 lines in the window (its `rail.py`/`agenda.py`/`quote.py` split is untriaged)
    and `run()` `:739-779` now does slide-layout work after `lay_out()`. *Proposal:* name the 0.5 em
    once beside `NOTE_GAP` (flat), or take `boxes.note.gap` (**RENDER**: the lead moves by the
    difference); the split stays the ledger's. *Cost:* 1 file.

24. **prose — comments describing the pre-window behavior.** `engine-common.lua:51-52`
    (`holds_shape`: "a card … or a grid column cannot hold one": they can since #148),
    `:155-157` (`take_layout`'s list omits `dark`), `:744-746` (the `status_item` docstring stranded
    above `DASHES`), `:1-9` (the header names the markings, not the watermark, cell figures or
    base64); `slide-layout.lua:1-2,8-13`; `engine-revealjs.scss:81-84,195` (`--engine-logo-*`);
    `liveries/cu/reference/notes.md:65-69` and `liveries/nsi/reference/notes.md:32-34,75-76`
    (`geometry.logo.corner`, a top-level `signoff`: keys the schema now refuses, in the recipe a new
    owner copies); `diagram-dark.lua:36` warns by `io.stderr:write` where every other filter uses
    `C.warn`. *Cost:* comments and prose.

25. **ratchet — `slide-layout.lua:23`'s `WORDS` is a hand copy of `LAYOUT_CLASSES`**
    (`engine-common.lua:142-143`); `tests/test_cli.py:290-293` pins `SLIDE_KINDS` into the JS and
    css but nothing pins this (the window added `dark` by hand, correctly). *Proposal:* extend the
    test. *Cost:* tests/test_cli.py.

### Tier 3: Ben's picks (each moves a render, or is a decision)

9. **consolidate — the table rules: the head rule's role differs PDF vs HTML/pptx on seven of
   ten liveries, the widths in three units.** `engine-revealjs.scss:297` (`3px solid
   var(--engine-primary)`), `:301` (`1px` table-rule); `beamerinnerthemeEngine.sty:996`
   (`\midrule`: `BrandPrimaryContrast`, `1.5pt`, a `0.3ex` gap), `:997` (`\bottomrule` 0.6pt);
   `style_tables.py:24-25` (`3*PX`, `1*PX`), `:111` (`ink["primary"]`). Primary and
   primary-contrast differ on cu, nsi (CFB87C vs 8D7334), ucar, ucp, nasa-dark, nasa-jsc-eg and
   nasa-ccp; 3 px of 900 vs 1.5 pt of 256 pt (≈5.3 px) vs 3 px; the bottom rule 1 px vs 0.6 pt
   (≈2.1 px). On a dark slide all three agree (secondary) by the swap. Pre-window; the dark slide
   made it visible. *Proposal:* `boxes.table {head-rule, head-rule-color, rule}` (fractions of the
   height, a role; `primary-contrast` the recommendation: a thin rule must read on the background,
   the rail's reasoning) read by the three drawers. *Cost:* 4 files + schema + REFERENCE + every
   livery rebuilt. *Risk:* **RENDER**: the PDF's rules thinner, HTML's and pptx's head rule darker
   on the gold and NASA liveries; parity moves every table page.

26. **drift — six `ex` gaps the beamer theme still sets** (CLAUDE.md "Divider subtitles": every
    gap `em`, never `ex`). `beamerouterthemeEngine.sty:133` (title→subtitle `-0.25ex`),
    `beamerinnerthemeEngine.sty:271` (`block begin` `-0.2ex`), `:318` vs `:324` (the feature
    subtitle's gap: `0.3ex` under the bar style, `0.5ex` under cover: two numbers for one gap),
    `:996` (`\midrule`'s `0.3ex`, folds into 9), `:125` (subsection page `0.8ex`). *Proposal:* `em`
    of the element (×0.55 keeps the look, or round to a clean number), the feature subtitle one
    number. *Cost:* 2 files. *Risk:* **RENDER**, sub-point.

27. **consolidate — inline code on a field: four tints in HTML, three of them hand numbers.**
    `engine-revealjs.scss:981` (section subtitle, on-dark 16%), `:1011` (closing, 16%), `:1090`
    (feature panel, 14%), `:1100` (the dark slide: the `dark-code` blend, 12%). Beamer and pptx
    draw no inline-code tint on a field. *Proposal:* the composed fields read `--engine-dark-code`
    through the `--engine-code-field` property of 6. *Cost:* scss only. *Risk:* **RENDER** (HTML
    code tints on fields, slightly lighter).

28. **drift — the cover fine print's `opacity: 0.85` is HTML's alone.** `engine-revealjs.scss:931`;
    beamer (`:359-360`) and pptx (`cover_fineprint`) draw the role's color. *Proposal:* drop it (the
    role carries the intent), or a `fineprint.opacity` key all three read. *Cost:* one line.
    *Risk:* **RENDER** (HTML fine print 15% darker).

29. **bypassed helper / delete — `emit_css` restates `corner_room()`; beamer measures the room
    itself; `aspect` is emitted for it and never read.** `livery_build.py:1283,1298` (the css's own
    inset + 40px + width, never clamped at 0 as `title_room()` `:382-405` is; the docstring at
    `:386` names `emit_css` a reader), `beamerouterthemeEngine.sty:86-110` (`\engine@measureroom`,
    the same formula on the image's measured width, light and dark passes), `livery_build.py:964`
    (`\engine@corner@<c>@aspect` emitted; no `.sty` reads it). *Proposal:* the css reads
    `title_room()` (flat on every bundled livery); beamer either takes the emitted room per role
    (and the 25 measuring lines go; `logo=false` then needs per-corner rooms) or the dead `aspect`
    emit goes. *Cost:* 2–3 files + livery rebuild. *Risk:* flat if the yml aspects match the PDF
    lockups (they are the same images); a decision on beamer's measuring.

30. **first run — an absolute `DECK_META` (or `LIVERY_DIR`) under a host symlink crosses into the
    container unresolved.** `common/Make.container:31-34` realpaths the mounts (`/tmp` →
    `/private/tmp` on macOS, HPC's linked project directories); `:107` passes the variables as
    typed through MAKEFLAGS; `Make.common:126,134` lists `$(DECK_META)` as a prerequisite. Concrete
    input, CI's own idiom (`ci.yaml:567`) on a Mac without quarto: `make pptx DECK_META=/tmp/p.yml`
    stops with "No rule to make target '/tmp/p.yml'" (the image's `/tmp` is its own). `LIVERY_DIR=`
    fails alike at the `.livery` rule (pre-window). A relative path is fine. *Proposal:* the inner
    command line restates both as real paths (check under make 3.81 that a later command-line
    definition wins over the MAKEFLAGS copy, else an override name `Make.common` reads).
    *Cost:* Make.container (+ Make.common); `smoke-test.sh` per runtime is the proof. *Risk:* no
    render; a consumer's Makefile unchanged.

31. **consolidate — the page number's place: three hand numbers** (`beamerouterthemeEngine.sty:182-199`
    `0.075\paperheight` ×2 and `0.035`, also a twin of `geometry.full-footline` `:440`;
    `engine-revealjs.scss:1174-1176` `50px`/`14px`; `livery_build.py:1302-1303` `'50px'`;
    `livery_template.py:128-132`). Pre-window, low rank. *Proposal:* `geometry.pagenumber.{inset,
    bottom}` beside `corner`, or the Untriaged list.

## Already in the ledger, touched by the window (one line each, no new work)

- `grid-pptx.lua`'s hand-composed marker tails: two more (`picture src=..[ data=..][ size=..]`
  `:137-155`, `table cols=n[ header][ align=..]` `:165-167`).
- `grid.py`'s size and split (finding 23 names what grew).
- The version line's readers: `livery_mpl._engine_version()` `:72-88` now has three sources and
  `pyproject.toml:21-24` is a fourth reader of `version:`; the ledger's line still holds.
- The scss mixin candidates: the composed-slide selector group is a new ×2 (`:188-191` the
  watermark's ink, `:790-793` the marks).
- The docs entry's open item "README's white-rule insignia" is right (`liveries/nasa/_brand.yml:80-88`):
  drop it from the entry. CLAUDE.md "The engine" naming `sample.png` for `make previews` (three
  images now) stays open.

## Recommendation

Before the release, one sweep PR of Tier 1 and Tier 2 (1–8, 10–25, with 11 by parity and 23 at
the flat option), about 24 commits: the three defects at the dark slide's and strips' edges, the
qa gate made usable, the dark swap and the fine print behind one reader each, the lifts, and the
records brought current. Tier 3 (9, 26–31) each moves a render or is a decision on an idiom:
pick any now for the same PR with side-by-side shots, or defer to the ledger; 9 is the one worth
a look before the release, since the dark slide's secondary-colored head rule now sits beside a
light slide's differently-colored one in the same deck on seven liveries.

## Ben's picks (2026-10-24): "Tier 1 and 2"

Picked: 1–8, 10–25 (11 by parity, with the docstring fix as its fallback; 23 at the flat
option, the number named, not moved). Deferred to the ledger's Untriaged list: 9, 26–31 (each
moves a render or decides an idiom; 9 is flagged there as the one to look at first). A finding
that measures flat where it should move, or costs more than it saves, is dropped and recorded
with its numbers, not shipped.

## Commits, in order

1. deck_qa: the frame number taken before the edge loop (2); `QA_PPTX_FAIL=1` on CI's sample if
   the reports go quiet
2. beamer: a dark frame's lead, strip and caution body keep their text color (1), the latex test's
   dark frame holding them
3. `DARK_SWAP`/`DARK_BOXES` into `livery.py`, `DARK_INK` and `\engine@darkswapped` from it, the
   code-on-field rule emitted (5, 6); every livery rebuilt
4. HTML: strips and watermark on every slide by one walk (3)
5. `.full`/`.feature` ignore `.brand-dark` alike (4)
6. `fineprint_paragraphs()` the one reader (7)
7. `comp_of()` and `PHOTO` named once (8)
8. Lua: `is_rendered`, `decode_src`, the table parsed once (10)
9. beamer's `card_body` on `cell_figure()`, or the docstring (11; parity decides)
10. `measure.table_height()`, `CELL_MAR` in common (15)
11. `peek_marker` and `LAYOUT_KEY` (16)
12. the furniture selector shared or pinned (17)
13. linked-images.lua on the muted role (18)
14. the dead keyword defaults and names (19)
15. the lead-after-figure gap named once (23, flat)
16. conftest's `run_steps` and `flavor` (20)
17. `livery placeholders -o` (21)
18. CI's pip probe trimmed (22)
19. the `WORDS` pin (25)
20. comments and reference notes (24)
21. the pipeline diagram and formats.md step list, `07-mermaid.png` reshot (13)
22. CHANGELOG wording (14)
23. the records: State lines, the roadmap, the design log (12)
24. the ledger entry (below); this handoff committed with its State line final; the skill's
    growth rule if a new class was met (none this window: every finding is a listed heuristic)

Commits 2–5 and 7–13 touch disjoint files from 16–23 and can go to agents in worktrees (the
skill, section 6: each cut from the branch tip named in its brief, each taking its own baseline
there and proving its commits flat before the lead cherry-picks them). Stage by file, never
`-a`. Each commit's message names the finding number and, for 1–5, the input it fixes.

## The ledger entry (commit 24)

```
## 2026-10-24: window #136–#149

- Mode: window
- Range: `f493a70..de1ce55` (#136 the sweep of #127–#135, #138 the themes sweep, #139 the docs
  sweep, #145 consumer friction, #146 nasa-ccp and the named strips, #148 cells and the dark
  slide, #149 corner marks, the watermark and livery_mpl on pip; releases 26.10.9–26.10.11);
  read in four area passes, 31 findings, Ben picked Tier 1 and 2
  (`design/sweep-136-149-handoff.md`)
- End commit: `de1ce55`
- Done (#PR): <each landed finding in a clause, the render-moving fixes named as such: the
  dark frame's lead/strip/caution text, the untitled HTML slide's strips, `.full .brand-dark`,
  the caution body's code on an HTML dark slide>
- Tried and dropped: <any, with numbers>
- Open: <any picked finding not landed, with why>
```

Then move Tier 3 to **Untriaged** as one bullet each (9 first, flagged "look before a release
that ships a dark slide beside a table": the head rule's role differs on seven liveries), and
drop the docs entry's "README's white-rule insignia" item (it is right: nasa's `logo.dark` is
`meatball-rule`, `liveries/nasa/_brand.yml:80-88`).

## Verification

`make test` at every commit; parity baselines (`tests/parity.sh baseline` under ncar, cu, nsi and
`tests/parity-latex.sh baseline`) on `origin/main` at `de1ce55` before commit 1 and `check` after
the last; commits 2, 4 and 5 are fixes on inputs no bundled deck has, so each is proven by a
scratch deck shot before and after and the test it adds; commit 3's livery rebuild is
`livery build --check` and every `template.pptx` byte-identical; `make -C decks/sample qa` and
`make -C decks/fixtures qa` under nsi after commit 1 to read the quiet reports. `CHANGELOG.md`
Unreleased gets a line per user-visible change (the four fixes; the qa gate; nothing for a
pure lift). The PR body: what a deck author sees (the four fixes, with a before/after shot of
the dark frame's boxes and the untitled slide's strips), the consolidations in a list, the
parity and measure numbers, `make test`'s count, and "app-open not run: nothing changes a pptx's
shape beyond colors" or the run if a step's XML changed. Open the PR against `main`, do not
merge: post its number for the review.

## Follow-on prompt: finding 9, the table rules (if Ben picks it)

> When the Tier 1 and 2 commits are done (before opening the PR, or as one more commit pushed
> to the open one), add finding 9 from `design/sweep-136-149-handoff.md` as its own commit,
> and move it from the ledger entry's Untriaged bullet to its Done list. The table's rules
> become livery data: `boxes.table` with `head-rule` (the head's rule width, a fraction of
> the slide height like `boxes.card.border`; today 3 px of 900 in HTML and pptx, 1.5 pt of
> beamer's 256 pt paper), `head-rule-color` (a role; `primary-contrast`, Ben's pick: a thin
> rule must read on the background, as the rail's marks do) and `rule` (the row rule; today
> 1 px in HTML and pptx, 0.6 pt in beamer), in the schema, `BOXES`, `REFERENCE.md` and every
> livery rebuilt (`livery build --check`; every `template.pptx` must stay byte-identical,
> since the template draws no table). The three drawers read it: `engine-revealjs.scss:297,301`
> (`th`/`td` `border-bottom`, through `--engine-boxes-table-*` properties `emit_css` writes),
> `beamerinnerthemeEngine.sty:996-997` (`\midrule`/`\bottomrule`: `\arrayrulecolor` from the
> role, `\specialrule` from the fraction in `\paperheight`; its `0.3ex` gap becomes `em` of the
> cell's font, finding 26's rule), `pptx_steps/style_tables.py:24-25,111` (`HEAD_RULE`,
> `ROW_RULE`, `ink["primary"]` → the role through `palette()`, so a dark slide's swap still
> lands on secondary). Pick the one width per rule for all three (3 px and 1 px of 900 as the
> recommendation: HTML and pptx stay, the PDF thins) and name the departure. It moves a render,
> so parity cannot prove it: shoot a table slide (the sample's "Tables" and the dark slide's
> table) before and after under ncar, cu and nsi in all three formats, review by eye, and put the
> cu or nsi pair in the PR body; the parity run's table-page deltas are listed, not explained
> away. `tests/test_boxes.py` gains the key, `tests/test_tables.py` (or the step's test) reads
> the role from the livery; CHANGELOG under Decks: "a table's head rule is primary-contrast in
> every format, its widths one number (the PDF's thinner); `boxes.table` under Liveries". No
> version bump; the PR stays unmerged for the review.

## Prompt for the peer session

> Read `design/sweep-136-149-handoff.md` in `/Users/benkirk/Documents/quarto-livery-decks`
> and do its picked work: branch `sweep/136-149` from `origin/main` at `de1ce55`, the commits
> in its "Commits, in order" list (Tier 1 and 2 only; Tier 3 goes to the ledger's Untriaged
> list as the entry section says), each staged by file and passing `make test`, the
> verification section's parity baselines taken on `origin/main` first. The skill is
> `.claude/skills/unplanned-city-sweep/SKILL.md`, section 6 the method; CLAUDE.md has the
> architecture. Agents in worktrees for the disjoint groups the handoff names, if you like.
> Finish with the ledger entry, this handoff's State line brought to "landed as #N", the
> CHANGELOG lines and the PR opened against `main`, not merged. Report the PR number, the
> parity deltas, and anything you dropped with its numbers.
