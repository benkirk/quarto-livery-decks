# Sweep handoff: unplanned-city window #105–#126

**For a fresh session.** One PR against `main` (branch `sweep/105-126` from `origin/main` at
`ba36ec5`, the #126 squash), a commit per finding in the order below, squash-merged once, no
version bump (the 26.10.7 release is its own small PR after; ask before any tag). Start by
reading `CLAUDE.md` whole, `.claude/skills/unplanned-city-sweep/SKILL.md` (steps 6–7 are the
work and the close-out), `design/unplanned-city-ledger.md`, and this file. Then
`source etc/config_env.sh`, `git checkout -b sweep/105-126 origin/main`, and take the parity
baselines (Verification, step 1) before the first commit. Report at the end of each commit:
what moved, what the tests assert, what parity named.

House rules that bind here: roles only (no palette name or hex in a theme file); a number every
format draws lives in `livery.json` and one drawer per format reads it; no compatibility shims
(Ben is the only consumer: a rename moves every caller in the same commit, keeps no alias);
`template.pptx` and `liveries/*/build/` are generated (`livery build liveries/*/`, `make livery`),
never edited; integer EMUs in the pptx; set all four of a shape's left/top/width/height together;
American spelling; a user-visible change gets a `CHANGELOG.md` `[Unreleased]` line in its commit;
a `livery.yml` key is renamed only with Ben's agreement (none is renamed here); a test writes only
under `tmp_path`; the house commit message (one-line title, a body with the mechanism and the fix,
the session's attribution lines). A sweep removes code more often than it adds it. When a finding
turns out wrong against the code, say so in the commit message and the ledger rather than bending
the code to the plan; a refactor that costs more than it saves is dropped and recorded with its
numbers.

## Context

The window is nineteen squash commits, `62d6568..ba36ec5`: #105 consumer friction, #108 the first
sweep, #109–#121 (Google Slides waves, notes under figures, SVG plots, Keynote notes, pytest,
captions, app-open, Codespaces, tables), #123 nasa-jsc-eg and its engine sprint, #126 columns,
cards and the #124 livery knobs (reviewed 2026-10-21; its review comment names F3/F4 below).
Three area readings (engine-py; Lua and themes; docs, design, CI and make) produced 24 findings;
Ben picked 1–14 and 17 (2026-10-21), the rest go to the ledger's Untriaged list. Two are defects
(1, 2), one a CI path that cannot reach its fallback (3); the rest are records that stopped
agreeing and the window's new paradigms (the card/grid machinery, the boxes block, the Lua
common module) applied once instead of twice.

Line numbers are on `ba36ec5`; re-grep before editing.

## The commits, in order

### 1. ncar's pptx card head is rounded at the bottom

- `_extensions/engine/pptx_steps/grid.py:230` `_shape(..., top_only=False)` draws
  `ROUND_2_SAME_RECTANGLE` when asked; the one head call at `:386` ("rounded at the top only,
  square where the body starts") never passes `top_only=True`. ncar sets `boxes.card.radius`
  0.012 (`liveries/ncar/livery.yml:101`), so every ncar card head (and ucar/ucp/ncarucar's, which
  inherit) is a fully rounded rectangle: the card fill shows at the band's lower corners.
  Confirmed by eye on the sample's "Options side by side" (LibreOffice render); HTML clips the
  head square (`engine-revealjs.scss:428` `overflow: hidden`), beamer's tcolorbox title is square.
- Fix: `top_only=True` at the head call. A test in `tests/test_grid.py::test_cards`: the head's
  `prstGeom prst` is `round2SameRect` when `card.radius > 0` (ncar) and `rect` when 0
  (nasa-jsc-eg); the fill stays `roundRect`.
- CHANGELOG Decks: "pptx: a card's head band is square at its foot on a livery with rounded
  cards (ncar); it was rounded all round."
- Parity names the sample's and quickstart's card slides under ncar (intended).

### 2. The consumer workflow example pins a release without the workflow

- `docs/other-repos.md:102` `uses: benkirk/quarto-livery-decks/.github/workflows/build-decks.yaml@v26.10.5`;
  the file arrived in #119, released in 26.10.6 (`git cat-file -e v26.10.5:.github/workflows/build-decks.yaml`
  fails). `:113-115` tells the reader to pin `image:` to the submodule's version but the example has
  no `image:` line, so the run takes `:latest` (`build-decks.yaml:24-27`).
- Fix: `@v26.10.6` and `image: ghcr.io/benkirk/quarto-livery-decks:26.10.6` in the example.
  Ratchet in `tests/test_docs.py`: the `@vX` pin and the `image:` tag in docs/other-repos.md equal
  `_extension.yml`'s `version:` (the release PR, which bumps the version, then bumps the example
  too: say so in CLAUDE.md "Version", one clause, and in `liveries/README.md`'s release step).
  `livery.engine_version()` reads the version.

### 3. runtimes.yaml: the PPA add is outside its own retry

- `.github/workflows/runtimes.yaml:82` `sudo add-apt-repository -y ppa:apptainer/ppa` runs once,
  before the `for i in 1 2 3` loop at `:83-86`; the step is GitHub's `bash -eo pipefail`, so a
  Launchpad 503 there ends the step and never reaches the `.deb` fallback or the `::error` at `:93`.
- Fix: the add inside the loop (`sudo add-apt-repository -y ... && sudo apt-get install -y -q apptainer && break`),
  or `if sudo add-apt-repository ...; then <loop>; fi` so a failed add falls through to the `.deb`.
  No test (a workflow); trace it under `-e` by reading.

### 4. CHANGELOG's link block stopped at 26.10.3

- `CHANGELOG.md:332-336`: `[Unreleased]: .../compare/v26.10.3...HEAD`; no `[26.10.4]`, `[26.10.5]`,
  `[26.10.6]` definitions though the sections exist (`:130,157,165`); #112, #114, #122 renamed the
  section and never added the link. Also two #123 fixes have no `[Unreleased]` line: "a photo cover
  may have `field: null` (it crashed pptx and HTML)" (Liveries) and "`make measure` skips an empty
  box" (Decks).
- Fix: the three links, the compare base `v26.10.6...HEAD`, the two lines. Ratchet in
  `tests/test_docs.py`: every `## [x.y.z]` heading has a `[x.y.z]: .../releases/tag/vx.y.z` line
  and `[Unreleased]` compares from the newest heading's version. `release.yml:46-48` reads only the
  entry; leave it.

### 5. `pptx_steps/common.py`: the steps' shared names, once

The window wrote `grid.py` and `columns.py` against `slide_layout.py`'s private names and
re-wrote its helpers. One module the steps import, `slide_layout` included:

- Constants: `LIVERY` (today nine modules call `livery_mod.load()` themselves: embed_fonts:26,
  link_captions:21, marking:17, measure:19, section_subtitle:36, slide_layout:49,
  style_footnotes:22, style_tables:18, type_step:21; three import `slide_layout.LIVERY`:
  grid:36, columns:29, status_glyphs:18), `K`, `BOXES`, `GEOM`, `BODY_PT`, `SLACK` (named at
  `grid.py:40`, bare `1.1` at `slide_layout.py:231,353,730`).
- Helpers moved and made public: `is_body` (`slide_layout.py:135`), `text_height` (`:170`),
  `take_marker` (`:73`), `fit_table` (`:208`), `pads` (`:214`).
- New shared helpers replacing copies: `rect(slide, x, y, w, h, hex, name, behind=None)` for the
  five filled-rectangle drawers (`slide_layout._rect:675`, `caution_box`'s bar `:240-244`,
  `grid.rect:161`, `grid._shape:230` keeps the rounded/outline logic on top of it,
  `columns.rules:43`); `rpr(run)` for the five "ensure an a:rPr" copies (`slide_layout.py:266-268,281-283`,
  `grid.py:212-214`, `status_glyphs.py:82-84`, `style_tables.py:65-68`); `set_fill(rpr, hex)` for
  `grid._style`'s and `status_glyphs._color`'s solidFill insertion; `ppr_place(ppr, el)` with
  `status_glyphs.PPR_ORDER` for `grid._close`'s hand-ordered insert (`grid.py:257-265`);
  `is_table(sh)`/`is_picture(sh)` for the three idioms (`getattr(sh, "has_table", False)` ×5,
  `columns.py:95-96`'s redundant `and sh.has_table` and magic `shape_type == 13`,
  `MSO_SHAPE_TYPE.PICTURE` ×3, `link_captions.py:31` `hasattr(shape, "image")`).
- `livery.hex(livery, role_or_hex) -> "RRGGBB"` in `livery.py` replaces `marking._hex:22`,
  `grid._hex:190` (and its `[1:]` strips at `:164,225,240,244`), `section_subtitle._eyebrow_hex:177`
  (see commit 10), `slide_layout._role:528`'s own conversion; `status_glyphs.py:22`'s no-op
  `.lstrip("#")` goes. The same-name clashes go with them (`_role` means a color in
  `slide_layout:528` and an attribute picker in `grid:324`; `_text` a shape in `slide_layout:679`
  and a paragraph in `grid:45`).
- `PX`/`PT_PX` once in `measure.py:21-22` (copies: `section_subtitle.py:39-40`,
  `style_tables.py:20`); `slide_layout.FOOTNOTES:51` reads `style_footnotes.MARKERS:23`.
- Ratchet: `tests/test_cli.py` (or a new `tests/test_engine_imports.py`) fails when
  `grep -rnE 'from \S+ import .*\b_[a-z]' _extensions/engine --include='*.py'` finds a line (today
  two: `grid.py:36`, `columns.py:29`; `livery_build.py:152`'s `import livery_schema as _schema` is
  local, allow it or rename it).
- Nothing renders differently: parity identical. `pptx_post.py`'s import list and CLAUDE.md's
  step sentence ("each is a module with a `run()`") gain one clause naming `common.py`.

### 6. `role_tex()` is a third role-to-TeX table; an unknown `role=` fails three ways

- `engine-beamer.lua:276-279` capitalizes a role into `Brand<Role>` (special-casing `foreground`
  → `BrandText`), used at `:321` (cards) and `:385` (strips); `livery_build.ROLE_TEX:47-51` and
  `tex_name('brand-'+key)` for the blends (`:717`) are the other two. They agree on the 13 roles
  and 5 blends; for any other `role=` (say `data-1`) HTML writes `var(--engine-data-1)` (defined),
  beamer writes `BrandData1` (undefined: a LaTeX error), pptx's `grid._role:324` falls back to
  `primary` silently.
- Fix: `livery.json` carries `latex.roles` (each role and blend to its TeX name, from `ROLE_TEX`
  and the blends' `tex_name`) beside `latex.colors`; `engine-beamer.lua` looks names up there and
  `role_tex()` goes. One `C.box_role(livery, role, default, who)` in `engine-common.lua`, used by
  both filters' card and strip paths and mirrored by `grid._role`: a name that is not a role or a
  blend warns ("slide X: role=... is not a role; primary") and falls back, the same in all three.
  `livery_build.py:46`'s comment ("six, plus the four new") says 13.
- `livery build liveries/*/` regenerates every `build/livery.json`; `tests/test_schema.py`
  pins `latex.roles` keys = `ROLE_TEX` ∪ blends. No pixel change.

### 7. Lua: the copies the window multiplied

Into `engine-common.lua` (each already has the loader; `slide-layout.lua` gains it the way
`grid-pptx.lua:30-33` does, with the plain-pandoc fallback):

- `is_slide_break(blk, level)`: identical in `engine-revealjs.lua:138` and `engine-beamer.lua:84`,
  inline in `notes-last.lua:23`, `linked-images.lua:76`, `grid-pptx.lua:160`, `single-body.lua:202`,
  `slide-layout.lua:98`.
- `split_full`: identical bodies (`engine-revealjs.lua:414-431`, `engine-beamer.lua:615-635`);
  common returns `fig, caption, rest`, beamer derives `src` itself (`:631-633`).
- `take_layout(blk, who)`: `engine-revealjs.lua:177-204` and `engine-beamer.lua:140-166` differ
  only in beamer dropping `fill` and the warning prefix; `slide-layout.lua:18-50` adds its kind
  words on top (and today drops a bad `scale=` without warning: warn as the others do).
- `C.LAYOUT_CLASSES` (the three tables: `engine-revealjs.lua:174`, `engine-beamer.lua:136`,
  `slide-layout.lua:15`, the last adding `full`, `feature`, `closing`) and `C.SLIDE_KINDS`, with
  `C.is_content_slide(blk)` for the hand lists at `engine-revealjs.lua:213-214,359-360,387-389`,
  `engine-beamer.lua:104,175`. `engine-revealjs.js:28` (`NEVER`) and `livery_build.py:1059` (a
  `:not(...)` selector) keep their lists; a test (`tests/test_cli.py`) asserts the three name the
  same kinds (read the Lua table with a regex).
- `C.theme_options(meta)`: parsed three times (`engine-revealjs.lua:466-477`,
  `engine-beamer.lua:493-500`, `slide-layout.lua:52-61`).
- `C.load_livery(meta, extdir, who)`: lift `engine-revealjs.lua:115-132`; `engine-beamer.lua:845`
  reads `LIVERY.boxes.card.roles` unguarded while `:470` and `:527-534` still allow a missing
  file (a nil index instead of revealjs's clear message). The dead guards go.
- Stay per format (the ledger's verdict, recorded): `unwrap_layout`, `size_plots`,
  `hoist_footnotes` (lift only `take_footnotes`, `engine-revealjs.lua:147-161` vs
  `engine-beamer.lua:105-117`, if it stays under 30 lines; else ledger), `wrap_layout`,
  `lead_boxes`, `strips`, `status_items`.
- Known divergence to leave and ledger: revealjs leaves `.full` slides out of `wrap_layout` and
  `hoist_footnotes`, beamer does not (a `.full` frame with `scale=` is scaled in the PDF only).
- Parity identical; the quickstart renders in all three formats after the commit (the Lua
  filters have no unit tests beyond `test_grid_pptx.py` and `test_status.py`).

### 8. The status glyphs' names leave `--engine-status-*` to the charts

- Glyphs `done|warn|fail`: `livery_build.py:110,112` (`BOXES["status"]`, `BOX_COLORS`), emitted at
  `:861` (`EngineStatus<Key>`) and `:1110` (`--engine-status-<k>`); read by `status_glyphs.py:20-21,75`,
  `engine-beamer.lua:348` (`STATUS_TEX`), `engine-revealjs.scss:493-495`. Charts
  `good|warning|serious|critical`: `livery_charts.py:468`, emitted at `livery_build.py:881,1121`;
  the `.brand-dark` override (`:1123-1124`) re-sets only the charts'. `tests/test_boxes.py:49`
  pins the CSS name.
- Fix (Ben's pick): the glyph set becomes `--engine-glyph-done|warn|fail` and
  `EngineGlyphDone|Warn|Fail`; the `livery.yml` key `boxes.status` is NOT renamed (a key rename
  needs Ben's agreement; the schema and REFERENCE.md stay). Sites: `livery_build.py:861,1110`,
  the scss `:493-496` (and the `.engine-status-*` classes may stay, they are HTML class names
  the Lua writes at `engine-revealjs.lua:272-275`; rename them `engine-glyph-*` too for one
  vocabulary), `engine-beamer.lua:348`, `tests/test_boxes.py:49`, CLAUDE.md "Cards and boxes"
  and docs/authoring.md if either names the property. `livery build liveries/*/`. Screenshots of
  the quickstart's card slide before and after: identical.

### 9. `section.label-color` resolved to a hex at build (ledger's idiom c)

- Four drawers resolve it themselves: `section_subtitle._eyebrow_hex:177-180` (restating the
  default `"secondary"` at `:179`), `emit_sty_compositions` (`livery_build.py:937-940`: hex →
  `\definecolor`, role → `\colorlet` via `ROLE_TEX`), `emit_css_compositions`'s `role()`
  (`:1245,1290`), `comp_measure.py:338-340`. `marking()` and `boxes()` resolve theirs at build.
  Only ucar sets it (`liveries/ucar/livery.yml:19`).
- Fix: `compositions()` resolves `eyebrow.color` to a hex as `marking()` does (`out["roles"]`
  is in scope); every drawer reads a hex; the schema keeps `role-or-hex` for the yml. Every
  `build/` changes (json hex, `.sty` `\colorlet` → `\definecolor`, `.css` `var()` → hex); the
  rendered output is identical (parity, `make measure` on ucar unchanged).

### 10. Geometry with several homes

- `columns.frames` (`columns.py:36-43`) and `grid.column_frames` (`grid.py:100-108`) are the
  same formula rounding differently; `columns._old` (`:61-65`), `livery_template.py:363` and
  `livery_charts.py:573` each write the Two Content half `(1-2m-gap)/2`; the body box is computed
  at `livery_template.py:170,213` and `:358-365` and `livery_charts.py:569-574`; dead fallbacks
  `.get("body", 0.1667)` at `livery_template.py:170,358`, `livery_charts.py:570`,
  `livery_build.py:770,1011` (`resolve()` always writes `frametitle.body`, `:216,222`); `margin`
  defaulted at `livery_build.py:214,272,418`, `livery_charts.py:569` but hard-indexed at
  `livery_template.py:168,357`, `columns.py:38,63`.
- Fix: `resolve()` sets the margin default once and writes `geometry.body` `[x, y, w, h]` and
  `geometry.half` (the Two Content column width) into `livery.json`; the template, `figsize`,
  `columns._old` read them; `columns.frames` calls `column_frames` (one rounding); the dead
  fallbacks go. Schema: `geometry.body`/`half` are derived, not yml keys (as `wide-margin`'s
  default is), so no schema change unless `livery_schema` validates the json. At most 1 EMU
  moves in column frames: `tests/test_grid.py` tolerances cover it; parity names nothing.

### 11. Dead code

- `\engine@cardval` (`beamerinnerthemeEngine.sty:402`, added in #126, never called),
  `\engine@accentbar` (`:29-34`), `\engine@titlepageframe` (`:97-98`), `\engine@ifplainstyle`
  (`beamerouterthemeEngine.sty:34-35`); `SPANS.sub` → `engine-sub` (`engine-revealjs.lua:303`:
  emitted, nothing styles it, the other formats draw nothing for a `.sub` in a body);
  `pptx_waves.wave_shapes`'s `bands` (never read) and `line_px` (never passed) (`:100`);
  `livery_template.sz(scale=)` (`:91`). Grep each name across the tree and `latex/` before
  deleting; `parity-latex` identical.

### 12. The TeX requirements, stated

- `\fpeval` (`beamerfontthemeEngine.sty:15`, inner `:348,370,485`, `engine-beamer.lua:442-443`)
  needs the 2022-06-01 kernel; `\AddToHook` 2020-10; `tcolorbox` with `skins,breakable` is
  unconditional since #126 (inner `:390`), so every `latex/` deck and Overleaf zip needs it;
  `latex/README.md:58-63` names only TeX Live, XeLaTeX, latexmk, `fontawesome5`.
- Fix: `\NeedsTeXFormat{LaTeX2e}[2022-06-01]` in `engine_livery.sty` (the one every theme file
  loads through); a sentence in latex/README.md naming `tcolorbox` (`texlive-latex-extra` on
  Debian/Ubuntu) and the kernel date. CHANGELOG LaTeX: one line.

### 13. The pptx text-height estimate's paragraph gap (pixels move)

- `slide_layout._text_height:170-180` adds `Pt(6 * K)` per paragraph ("the body's 6 pt on the
  default canvas"); the template writes `spcBef` = 0.5 × body at level 1 and 0.3 × body below
  (`livery_template.py:189`): on the default canvas 8 pt real vs 6 estimated, on ncar 6 vs 4.5.
  `grid.BODY_GAP:42` restates the 0.5 correctly. Caution boxes, notes placement, leads, grid
  columns and cards are all cut to this estimate (`SLACK` 1.1 then covers the shortfall by luck).
- Fix: `livery.SPC_BEFORE = (0.5, 0.3)` (the one home; `livery_template.py:189` and the steps
  read it); `text_height` adds `Pt(BODY_PT * SPC_BEFORE[0 if p.level == 0 else 1])` per paragraph
  unless `gap` is given; `grid.BODY_GAP` derives from it. `NOTE_GAP` (`:62`) is a different thing
  (the space between a picture and its note) and stays.
- Proof: `tests/parity.sh check` names the pptx slides whose boxes grew (sample caution, notes,
  cards; quickstart cards); shoot those slides before and after through LibreOffice (as the
  #126 review did: `soffice --headless --convert-to pdf`, `pdftoppm`) and put the contact sheet
  in front of Ben. Drop the commit and ledger it with the numbers if the boxes come out worse.
  CHANGELOG Decks: "pptx: a box cut to its text (caution, lead, cards) is sized with the
  template's own paragraph spacing; it was a little short."

### 14. Prose describing an earlier step (one commit)

Each a line or a clause; verify each against the code before editing:

- `liveries/README.md:103`: drop "and `VERSION` in `engine-revealjs.lua`" (#108 reads
  `_extension.yml`).
- `docs/formats.md:259-268`: pptx is SVG with a PNG fallback since #111, not "pptx's PNGs";
  `:145-147` "drop `embed_fonts.py` from `Make.common`" → "drop the livery's `pptx.fonts`";
  `:141-143` and `CLAUDE.md:178-179,293-295`: the code face: `pptx.code-typeface` overrides
  the pptx's (nasa-jsc-eg: Courier New).
- `CLAUDE.md:466-471`: the test list names 9 of 16 modules; keep the three with an explanation
  (`test_compositions` `EXPECTED_DELTAS`, `test_schema`, `test_docs`) and "and the rest of
  `tests/test_*.py`". `CLAUDE.md:709-718`: the `sample` job also runs the sample's `make qa`,
  the notes/captions check and the notes-slide `clrMapOvr` check; the `livery` job the
  charts-bundle step. `CLAUDE.md:148-149` and `docs/container.md:189-190`: the Codespaces image
  is main's head, whatever branch is opened.
- `.claude/skills/deck-polish/SKILL.md:65-67,79-80`: delete "Sample deck overflows" and "Not in
  CI" (CI runs the sample's, plots' and every livery's quickstart qa since #116/#123); add the
  known fix "pptx count +1 on a grid or card slide holding a picture or table → a two-column
  slide". `.claude/skills/pr-review/SKILL.md:85-90`: name `tests/app-open.sh` (Keynote and
  PowerPoint, Ben's Mac) as the proof for `pptx_steps/` and template changes.
- `liveries/nasa-jsc-eg/reference/notes.md:124-127`: add #124's two other open items (the 2×2
  quadrant layout, the deck-level mark-swap key). `docs/formats.md:16-20,133-139` and
  `docs/authoring.md:262-267`: nasa-jsc-eg (Arial / Liberation Sans, embeds nothing, its sizes).
  `docs/authoring.md:3-4` and `README.md:129`: the intros name "Columns" and "Cards and lead boxes".
- Engine headers: `_extension.yml:54-55` ("Make.common's post-render scripts (common/utils/)" →
  `pptx_post.py` and `pptx_steps/`), `:59-61` (a grid slide is also a `.card` or a `.lead`);
  `engine-common.lua:1-5` (loaded by `resolve_path` or `PANDOC_SCRIPT_FILE`; `split_full` no
  longer differs, after commit 7); `engine-revealjs.lua:67-68` and `engine-beamer.lua:65-66`
  (the shared-helper lists); `engine-revealjs.lua:349-351` (a stray paragraph); both filter
  headers (`.wide`, columns, cards, `.lead`, `.strip`, status items, marking);
  `beamerouterthemeEngine.sty:9-14` (`enginefull=`); `engine_livery.sty`'s header (values come
  from the livery, not the NCAR guide); `pptx_post.py:31-34` (`notes_clrmap` runs second) and
  `:47-51` (name `columns`, `grid`, `status_glyphs`); `section_subtitle.py:8,10` ("first";
  "accent1" → `section.label-color`); `grid.py:1` ("cards later"); `enable_autofit.py:9-15`
  (names `autofit_powerpoint.applescript`, not in the tree); inner `:423` and `grid.py:41`
  both cite HTML for the 0.25 card line gap, which the scss does not set: say "beamer's and the
  pptx's; HTML uses reveal's block margin".
- `.claude/skills/unplanned-city-sweep/SKILL.md:23` and the ledger's `:6`: "the newest *window*
  entry's end commit" (the newest entry is an area one; this sweep rightly started at `62d6568`).
- `CHANGELOG.md:6-7` vs `design/engine-and-liveries.md:397-400`: the narrative is §10 up to
  26.10.0, the PR bodies and the ledger since; §10's "recorded elsewhere" list becomes generic.
- `make test` (the docs gate reads every link and pointer).

### 15. design/ plans: a state line each

- `design/sprint-124-handoff.md:3`: a state line under the title ("Landed as #126, squash
  `ba36ec5`, 2026-10-21; open in #124: the quadrant layout, a picture or table in a grid column,
  the deck-level mark key"); its three follow-ups nobody tracks (`:111-113,579` a contrast warning
  in `livery check` for status colors; `:399-400` `a:latin` on the ⚠ run if PowerPoint draws an
  emoji; `:573-575` pptx box pads `type_step` does not scale) go to the ledger's Untriaged list.
- State lines on `phase-b-handoff.md` (done; its `:88-95` "Open after Phase B" is stale: v1.1.0
  withdrawn, `VERSION` gone, #58 closed, #66 open), `composition-handoff.md` (done, engine 3.5.0),
  `refactor-handoff.md` (done, 3.3.0), `nsi-handoff.md`, `docs-handoff.md`, `readme-handoff.md`
  (done in 26.10.1); `charts-and-plots.md:328` (`common/diagram-dark.lua` → `_extensions/engine/`)
  and `:394` ("the pptx PNGs" → SVG); `stress-test-findings.md:226-233`'s open items 1–2 to the
  ledger or dropped with a word. `compositions-baseline.md` and `stress-test-handoff.md` are dated
  records: untouched. The 20 stale `docs/design/…` paths across `design/*.md`: fix with one `sed`
  if the docs gate's exemption of `design/` is lifted (optional; say so in the commit).

### 16. The ledger, and the skill's growth rule

- `design/unplanned-city-ledger.md`: a new entry (mode window, range `62d6568..ba36ec5`, end
  commit `ba36ec5`, done with the PR number, tried and dropped with numbers, open). Untriaged
  gains the unpicked findings: scss mixins (the flex block ×3 `:707,752,808` + its print rules
  `:974-976,836-838`, the title tab ×2 `:659-668,729-738`, the field-code rule ×2 `:744,774`);
  white by hand on dark fields (scss `:849,853,744,774,868-870,860,867,960`; inner `:218-223,238`;
  outer `:158,442`; `slide_layout.py:717,733`: the composition's column role already reaches
  every format); small-caps tracking per format (HTML 0.1em `:447,719`, 0.08 `:649`, 0.04 `:256`;
  beamer `LetterSpace=4` inner `:487`; pptx `spc="100"` `grid.py:220`, 0.1em
  `section_subtitle.py:219`, none `style_tables.py:74`); strip spacing per format (scss `:469`,
  `grid.py:433`, inner `:368-375`); the title-stack fractions in `livery_template.py:273-276,287`
  and `slide_layout.py:479-480,739-749`; scss line-heights as literals (16 sites) vs
  `livery.json` leading; `build-decks.yaml` a `framework:` input picking the submodule's tag;
  `\cmark/\xmark/\pmark` (`engine_livery.sty:333-335`) a second status-mark idiom off
  `EngineStatus*`; the `.full`+`scale=` divergence (commit 7); `deck_qa.py:171`'s `h * 0.16` for
  the title line (nsi and nasa-jsc-eg sit lower); `CELL_PAD` vs `2*CELL_MAR` for a table's height
  (`slide_layout.py:289` vs `:356-357`); `canvas_scale` bypassed by `livery_template.py:94`'s own
  `self.k`; `livery_build.half` vs `livery.half_pt`; `PX`/namespace/serialize copies not taken in
  commit 5; the sprint handoff's three follow-ups (commit 15); the old untriaged items that
  remain (the version's three shell readers). Remove the items this PR did.
- Skill growth (SKILL.md step 4, same PR): two new classes met here: **a parameter with a
  comment and no caller** (`top_only`: a comment claiming behavior at the one call site that
  never asks for it; grep each keyword parameter's call sites), and **a doc example pinned to a
  release** (a `@vX` or image tag in prose: ratchet it to `_extension.yml`). Add them as one
  line each under "Delete" and "Ratchet".

## Verification

1. Before the first commit, on `origin/main`: `tests/parity.sh baseline` (ncar, cu, nsi;
   quickstart, sample, fixtures, plots) and `tests/parity-latex.sh baseline`. Same checkout,
   same day.
2. Every commit: `make test` (`livery build --check` on every livery, pytest; the docs gate
   reads every link and pointer); `livery build liveries/*/` whenever `livery_build.py` changes
   (commits 6, 8, 9, 10), committed in the same commit.
3. `tests/parity.sh check` after commits 1 and 13 (expected departures: ncar's card slides; the
   pptx boxes that grew) and after the last commit (nothing else); `tests/parity-latex.sh check`
   after 6, 9, 11, 12 (identical).
4. Commit 8's scss edit and commit 7's Lua: the quickstart's card slide and a columns slide
   screenshotted before and after (`make -C decks/quickstart qa`, `_qa/`), identical.
5. Commit 13: the LibreOffice contact sheet of the grown boxes for Ben; his verdict decides
   whether it ships.
6. `make -C decks/sample qa` and `make -C decks/quickstart qa` at the end; `tests/app-open.sh`
   is the release's step, not this PR's (nothing here changes the pptx's XML shapes beyond
   commit 1's `prstGeom`, which Keynote and PowerPoint both draw).
7. The PR body: a section per commit, the parity and screenshot results, the ledger entry
   quoted; the review (`/pr-review N`) before Ben merges; then the release PR.

## Memory for the fresh session

`~/.claude/projects/-Users-benkirk-Documents-quarto-livery-decks/memory/`: `pr-126-review.md`
(the review that queued F3/F4 = commits 8 and 5), `next-after-123.md` (the sequence: sweep,
then release), `minimal-prs-versions.md`, `no-compat-shims.md`, `sprint-tags-recut.md`. After the
PR opens, write `sweep-105-126.md` (what landed, what was dropped with numbers, the squash SHA
when Ben merges) and an index line.
