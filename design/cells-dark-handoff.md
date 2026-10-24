# Sprint handoff: pictures and tables in grid columns and cards; the inverted content slide in every format

**State (2026-10-24):** designed, not started; planned by the reviewing session after #146 and release 26.10.11, from three code explorations and two design passes. Ben's picks of 2026-10-24 are marked where they fall.

**For a fresh session.** One PR against `main` (branch `decks/cells-dark` from `origin/main` at
`2a1cf0a`), a commit per item in the order below, squash-merged once, no version bump. Read
`CLAUDE.md` whole ("pandoc pptx gotchas": "Columns: two tiers", "Cards and boxes", "Galleries";
"Dark liveries"; "Marks and numbers"; "Compositions"; "The engine"), `design/gallery-handoff.md`
(the shape and the nearest precedent: the gallery reads image files from disk and places them with
`common.fit_picture()`), then the machinery under Context. Then `source etc/config_env.sh`,
branch, parity baselines (Verification 1), this file as commit 0 at
`design/cells-dark-handoff.md`. Report at the end of each commit: what moved, what the tests
assert, what parity named.

House rules: one reader in `engine-common.lua`, one drawer per format, every number from
`livery.json`, roles only, no compatibility shims, a step imports no other step's private name
(`tests/test_cli.py` greps), tests under `tmp_path`, American spelling, a CHANGELOG line per
user-visible change, the house commit message with the session's attribution lines.

## Context (verified anchors, on `2a1cf0a`)

**Item 1.**
- `engine-common.lua`: `holds_shape()` :53-57, `latex_figure()` :362-380 (Quarto's raw
  `\begin{figure}` Div; not exported at :1026-1042), `is_figure()` :384-400, `is_grid()`
  :575-590, `card_attrs()` :632-647, `para_images()` :868-877, `gallery_items()` :879-938
  (refuses `figure-*/` and `*_files/` srcs at :899-901: pptx_post runs after Quarto deleted
  `figure-pptx/`; `decks/plots/plots_files/` holds no such directory).
- `grid-pptx.lua`: `encode()` :85-88, `is_shape()` :99-101, `flow()` :122-147 (the warning
  :137-139 leaves the shape in the flow: pandoc draws it as its own shape and splits the slide,
  orphan markers on an untitled continuation), `flatten()` :149-170, `mark()` :194-271.
- pandoc 3.8.3 draws a picture or table ONLY bare or inside a two-column `.column`; inside any
  other Div it is dropped silently; a bare image right after the header joins the slide and ends
  it; elsewhere it starts its own slide. pandoc's flow cannot carry a picture on a grid slide.
- `pptx_steps/grid.py`: `parse()` :68-118 (`strip`/`quote` nest in a column :109-115),
  `_card_text()` :167-193 (a tuple passes only when `p[0] == "quote"` :176), `_flat()` :195-200,
  `_plain_column()` :332-354, `_column_height()` :357-359, `_place()` :362-374, `draw_cards()`
  :391-467 (parts `(kind, tb, r, h)` :418/:426/:431, one row height :440, placement :457-464,
  the group :466), `lay_out()` :558-633, `run()` :636-700. `common.py`: `column_frames()`
  :117-126, `fit_table()` :163-170, `body_box()` :239-273 (the master's `bodyStyle`,
  `fill("tx1")`), `group()` :276-286, `contain_box()` :316-321, `cover_crop()` :324-329,
  `fit_picture()` :332-348 (bytes or path). `gallery.py`: `_caption()` :48-55 (private),
  `draw_gallery()` :58-112 (`deck_dir / unquote(src)`, `.svg` through `rasterize_svg(data, DPI)`
  :102-103). `svg_fallback.py`: `rasterize_svg()` :30-38, the svgBlip twin :59-72 (zip-level; a
  step's `add_picture` gets none). `slide_layout.py`: `_table_height()` :86-104, `table_height()`
  :107-111, `use_layout()` :310-326. `style_tables.py`: `style_table()` :94-115, `run()` :118-127
  over top-level shapes. `pptx_post.py` :58-66 the order (grid before status_glyphs,
  style_tables).
- HTML: `engine-revealjs.lua` `card_columns()` :264-295 (the body passed through); scss
  `.engine-card` :472-520, tables :268-271, `img.engine-plot` :344-350. PDF: `engine-beamer.lua`
  `card_body()` :253-267, `card_rows()` :269-320 (`tabled` :278-284: the row stays pandoc's
  columns, warned), `size_plots()` :499-511, `bound_sized_images()` :695-705;
  `beamerinnerthemeEngine.sty` `\engine@hsize` :294 (sets `\linewidth`), `\engine@cellbox`
  :627-631 (a `\vbox`: a `figure` float inside it is "Not in outer par mode").
- Fixtures: `decks/sample/images/gallery-1..6.jpg` + `CREDITS.md`; `decks/sample/sample.qmd`
  cards :200-261, three plain columns :160; `decks/plots/plots.qmd` the dark plot slide :159-171;
  `tests/test_grid.py` `MD` :55-60, `STEP` :61-68, `deck` :71-84, `test_cards` :236-271;
  `tests/test_grid_pptx.py` `PIC` :26, `rendered` :34-50; `tests/test_gallery.py` `pptx_deck`
  :238-256; `tests/conftest.py` `lua_common` :72-79, `flat` :82, `slide_layout_shim`.
- Docs: `docs/authoring.md` :201-202; CLAUDE.md "Columns: two tiers" (the first-cut limit);
  `design/unplanned-city-ledger.md` :230-233 (the deferred item this sprint retires). Issue
  #124's "2×2 quadrant layout" stays open: out of scope.

**Item 2.**
- Today: `engine-common.lua` `LAYOUT_CLASSES` :135, `take_layout()` :150-177. HTML
  `engine-revealjs.lua` :864-868 (`data-background-color = c.dark`, class `engine-field`, no
  content art, no waves); `wrap_layout()` :150-174. scss `.brand-dark` :1064-1081 (literal 25%,
  6%, 12% tints), the hairline :220, `.engine-field` :976-980, `has-dark-background` :1162,
  :1212-1213, `pre` :1214-1216. `livery_build.py`: `MARK_ROLES` :80, `marks()` :442-475 (`dark`
  present only when named: nsi, nasa-dark), css marks :1222-1232 (`.engine-field::after` gets
  **primary's** mark: nsi's black lockup on black, `liveries/nsi/build/livery.css:236-237`), the
  art exclusion :1218, `emit_css_charts()` :1300-1311 (dark set on `.brand-dark` only for light
  liveries), `emit_css_dark()` :1400-1410 (dark liveries only), sty marks :833-842, `ROLE_TEX`
  :48-52, on-dark :240-244, `geometry.body` :257, `frametitle.body` :280. `livery.py` `mark()`
  :136-141. `engine_livery.sty` `\enginelogo{light|dark}` :342-343. `livery_template.py`
  `master()` :167-252 (tab :206-208, rule :209-212, title :213-218, logo :227-228, sign-off
  :229-233 boxes computed locally from `geometry`/`frametitle`), `chrome()` :120-139.
  `pptx_waves.ROLE_SLOT` :10-12.
- PDF: `beamerouterthemeEngine.sty` `\engine@framestyle`/`\engine@ifstyle` :26-33,
  `\engine@framelogo` :55, `\engine@logowidth` :70-74, frametitle :103-108, tab :129-136, rule
  :144-148, footline :159-164, background :353-378, `\engine@touchedcolors` :448-451,
  `\engine@resetframe` :461-466, keys :481-487, `\engine@fieldcolors` :491-504.
  `beamercolorthemeEngine.sty` whole. Inner: `\engine@featureblocks` :274-280,
  `enginecautionfill` :380, the strip tint :549, `enginetableband`/`enginetablerule` :977-978.
  `engine-beamer.lua` `add_frameoption()` :85-88, `wrap_layout()` :147-169, `.feature`/`.closing`
  :775-816.
- pptx: `slide-layout.lua` `WORDS` :23, `take_layout()` :25-43; `slide_layout.py`
  `hide_furniture()` :263-269, `_rgb()` :424-426, `_box_picture()` :429-433, `draw_cover()`
  :436-454, `_recolor()` :612-618, `_rect()` :621-629, `draw_feature()` :632-680 (the slide number
  recolored :646-649), `add_slide_number()` :683-695, `run()` :698-763; `common.take_marker()`
  :97-114. Module-level colors: `style_tables.py` :24-26, `status_glyphs.py` :24,
  `style_footnotes.py` :33-35, `link_captions.py` :27, `grid.py` :185-187, :488, :550.
- `comp_measure.py` `KINDS` :35; `tests/test_cli.py` :243-256 (whites ratchet: scss 4, beamer
  0); `deck_qa.py` :379; `livery_mpl.py` `dark()` :230-240; docs saying HTML-only:
  `docs/formats.md` :264-266, `latex/authoring.md` :208, `decks/sample/sample.qmd` :377-386,
  `decks/plots/plots.qmd` :159-163, `decks/plots/README.md` :50, `engine-revealjs.lua` :29-30,
  CLAUDE.md :331, :380.

## Decisions (2 and 3 are Ben's picks, 2026-10-24; the rest open questions below if he disagrees)

1. A picture in a grid column or card is drawn in all three formats at the column's width, aspect
   kept, a caption line under it in the caption look; a sized image keeps pandoc's size. An
   executed plot or baked diagram counts: the pptx filter carries its bytes base64 in the marker.
2. A table in a plain grid column is drawn natively in pptx when simple (no spans, inline-only
   cells); a complex one warns and is left as today. A table in a card is not a card in any
   format: the row is drawn as plain columns, warned (the PDF's rule today; pptx and HTML join).
3. `.brand-dark` is a layout class, one definition: the content slide on the `dark` role; title
   and text `on-dark`; accents (h3, links, bullets, alerts, big number) `secondary`; the `dark`
   role's mark and sign-off; no content art, no waves; the hairline at the `dark-rule` blend; the
   tab accent; tables, inline code and muted text on the dark blends; the chart colors' dark set;
   code blocks keep the surface; a box with a fill of its own keeps its colors. On a livery whose
   `mode` is `dark` the class is a no-op in all three.
4. Four blends in `livery_build.BLENDS`: `dark-rule` (on-dark 25% toward dark), `dark-band` (6%),
   `dark-code` (12%), `dark-muted` (70%), through the existing blend emitters.
5. `livery.json` `furniture` = `{tab, rule, title, marks: {top-right|top-left: box, bottom-left|
   bottom-right: box}}` as `[x, y, w, h]` fractions (null where none), derived in `livery_build`
   from `frametitle` and `geometry` exactly as `livery_template.master()` computes them; the
   template builder and `slide_layout.draw_dark()` read the same boxes. **Keyed by corner** (the
   cross-sprint rule). Not a `livery.yml` key.
6. Marks emitted per role, looping over `marks[role]`'s keys: `\engine@mark@<role>@<name>` and
   `--engine-mark-<role>-<name>` (sprint B keeps this scheme); `\enginelogo{light|dark}` stays
   the author's command over them; `\engine@logo@light|dark` and `\engine@signoff@light|dark`
   deleted, not aliased.

## The commits

### 0. This handoff

### 1. The reader and the pptx picture marker (`engine-common.lua`, `grid-pptx.lua`)
- `engine-common.lua`: `cell_figure(b)` after `para_images()` → `{src, caption, image, sized}`
  for a Figure of one Image, a Para/Plain of one Image, a cell/quarto-figure Div holding one
  Image, a `latex_figure()` Div; nil otherwise, nil + warning for a Link round an image. Export
  `latex_figure`. `holds_table(blk)` beside `holds_shape()`. `base64()` (~20 lines: pandoc's Lua
  has none; `quarto.base64` is Quarto-only and the tests run plain pandoc).
- `grid-pptx.lua` `flow(blocks, title, out, cell)`: `cell` true from `flatten()` only. Before
  `is_shape(b)`: `fig = cell and C.cell_figure(b)` → `⟦engine:picture src=<encoded>[ data=<b64>]
  [ size=<w>]⟧`, the caption paragraph, `⟦engine:end⟧`. `data=` when the src matches
  `figure%-[%w%-]+/` or `_files/`: the filter reads the file now (`io.open`, relative to
  `pandoc.system.get_working_directory()` as `engine-plots.lua` `figure_path()`); over 8 MB or
  missing: warned, left in the flow as today. Why base64 over a kept copy: self-contained, no
  path contract between filter and step, nothing to mount or clean; one long `a:t` run in the
  intermediate pptx that the step deletes.
- Tests, `tests/test_grid_pptx.py`: `test_picture_marked` (markers in their column spans, the
  caption between `picture` and `end`, no `<p:pic>`, one slide; old code: a `p:pic` and a second
  untitled slide), `test_plot_bytes_carried` (a `figure-pptx/x.png` in tmp, `data=` decodes to its
  bytes), a Link warned; `lua_common` tests of `cell_figure` (five shapes). Parity identical.

### 2. pptx draws the picture (`pptx_steps/figures.py` new, `grid.py`, `common.py`)
- `common.caption_para()` lifted from `gallery._caption()` (moved; gallery imports it).
  `figures.py` (~90 lines; imports `common`, `measure`, `svg_fallback.rasterize_svg`):
  `draw_picture(slide, x, y, w, room, attrs, caption, deck_dir, name)`: bytes from `data=` else
  `deck_dir / unquote(src)` (missing: warned, nothing drawn), `.svg` rasterized, `ph = min(round(w
  * ih / iw), room - cap_h)`, `fit_picture(..., "contain", name)`, the caption a `body_box` under
  it (`f"{name} caption"`); returns `(pic, cb, height)`.
- `grid.py`: `parse()` admits `picture` in a column; `_card_text()` passes `("picture", ...)`
  through as a quote; `_plain_column()` takes the parts path for a picture, part `("picture", pic,
  cb)`; `_column_height()` and `_place()` get the branch; `draw_cards()` draws it inside the pads
  (as the quote), part `("picture", pic, cb, h)`, the placement loop's branch, `mine` gathers it
  into "Card n". `lay_out()` passes `deck_dir`.
- Tests, `tests/test_grid.py`: `MD` gains "Pictured cards" and "Pictured column"; `Card 1
  picture` inside group `Card 1`, width = card width − 2·pad, aspect ±0.01, caption top ==
  picture bottom, caption pt and muted, cards one height, no marker left, integers; the plain
  column's picture between its text boxes. Keynote and PowerPoint open it. Parity identical.

### 3. A table in a grid column, and the table-in-card rule (three formats)
- `engine-common.lua`: `simple_table(tbl)` → `{cols, header, rows = {{inlines,...}}, caption}` or
  nil (spans, multi-block cells); `tabled_row(div)`: a `.columns` div with a `.card` holding a
  Table, the one test the three formats share.
- `grid-pptx.lua` `flatten()`: a `tabled_row` writes every column plain, warned "a table in a
  card: the row is drawn as plain columns". `flow()` (cell only): a simple Table →
  `⟦engine:table cols=n[ header]⟧`, per row `⟦engine:row⟧` with cells joined by `⟦engine:cell⟧`,
  the caption, `⟦engine:end⟧`; else the warning as today. HTML `card_columns()`: a `tabled_row`
  skipped (warned) so the row falls to plain columns. Beamer `card_rows()` reads `C.tabled_row`
  instead of its own walk.
- `figures.py` `draw_table(slide, x, y, w, room, attrs, rows, name)`: `add_table`, equal widths,
  each cell's runs from the row's inlines, runs at `type_pt(LIVERY, "table")`, `firstRow` when
  header, height `table_height()`; `style_tables.run` styles it (top level: no table ever sits
  in a group, since the card case is refused). `grid.py`: `parse()` admits `table`;
  `_plain_column` part `("table", shape, cb)`.
- Tests: `test_grid_pptx.py::test_table_marked` (markers; a colspan table warned and left; a
  card row demoted, warned); `test_grid.py` "Tabled columns" (3 columns, a 3×3 header table in
  the middle): `Column 2 table` `has_table`, 3 columns, the middle frame, header bold after
  `style_tables` (add it to `STEP`); `lua_common` tests of `simple_table`/`tabled_row`. Parity
  identical.

### 4. HTML bounds and the PDF card figure
- scss after `.engine-card`: `.engine-card-body img, .columns .column img { max-width: 100%;
  height: auto; display: block; margin: 0 auto }`, `figure { margin: 0 }`, `figcaption` through
  the caption mixin (:90-98), `.columns .column table { max-width: 100% }`.
- `engine-beamer.lua` `card_body()`: a `latex_figure` Div inside a card is rewritten (the
  `figure` raw blocks dropped, the image kept, `\caption{}` → `\enginenote{}`); an unsized Image
  in a card gets `width = "100%"` (pandoc writes `width=1\linewidth`, the card's). `latex/
  examples/sample.tex` gains the "Pictured cards" twin frame.
- Tests: `tests/test_latex.py` `DECK` gains a card with `\includegraphics[width=\linewidth]` +
  `\enginenote{A caption.}`; `test_compiles_clean`; `pdftotext` shows the caption. HTML:
  screenshots of the two new sample slides (after 5) at 16:9 and letterboxed under ncar and
  nasa-dark. `parity-latex check`: the cookbook gains one page.

### 5. The sample slides, the plots slide, docs and records
- `decks/sample/sample.qmd` after "Solid cards": "Pictures in cards" (three `.card`s each with a
  `gallery-k.jpg` and one line) and "A table between two columns"; `decks/plots/plots.qmd`:
  "Plots in cards" (two `.card`s with `figsize("half")` plots: the base64 path in CI's plots
  `qa`). `docs/authoring.md` :201-202 rewritten; CLAUDE.md "Columns: two tiers" (the limit
  paragraph gone), "Cards and boxes" (the markers, `figures.py`, the base64 carry, the card
  rule); ledger :230-233 retired; CHANGELOG Decks and Plots.
- Proof: `make -C decks/sample all qa`, `make -C decks/plots all qa`, `make qa LIVERY=nasa-dark`;
  Keynote and PowerPoint open both pptx. Parity: the sample's two new pages, the plots' one.

### 6. Livery data for the dark slide (`livery_build.py`, `livery_template.py`, `liveries/*/build/`)
- `BLENDS` gains the four dark blends (decision 4). `furniture` (decision 5) derived in
  `resolve()` beside `geometry.body` from `master()`'s arithmetic; `master()` reads
  `self.L["furniture"]` and loses it. Marks per role (decision 6): `emit_sty` and `emit_css`
  loop `livery["marks"]`; `\enginelogo` maps light→background, dark→primary, any other word a
  role; `\engine@logowidth` measured for the background mark and the dark role's; `emit_css`
  gives `.engine-dark::after`/`.engine-dark .engine-signoff` the dark role's files; the art
  exclusion names `.engine-dark`. `livery build liveries/*/`, `livery template` each, committed.
- Tests: `tests/test_boxes.py`'s css pattern for the blends and nsi's `.engine-dark::after`
  naming `nsi-lockup-white.png` (**pins the mark fix**; old: black under `.engine-field`);
  `tests/test_frametitle.py` a `furniture` case (ncar's tab box; nsi's null tab and rule).
- Proof: every `template.pptx` master and layouts byte-identical before and after; parity
  identical.

### 7. The definition and HTML (`engine-common.lua`, `engine-revealjs.lua`, scss, `deck_qa.py`)
- `LAYOUT_CLASSES` gains `brand-dark`; `take_layout()` returns `dark`. `wrap_layout()`: `lay.dark`
  and `livery.mode ~= "dark"` → class `engine-dark`, `data-background-color = roles.dark`; the
  :864-868 branch goes; content art skipped on an `engine-dark` heading. scss `.brand-dark` →
  `.engine-dark` reading `var(--engine-dark-rule|band|code|muted)`; `emit_css_charts()` →
  `.engine-dark`; the Graphviz filter rules also emitted for light liveries scoped `.engine-dark`.
  `deck_qa.py` → `engine-dark`. Live mermaid on a dark slide reads `:root`: deferred, documented.
- Tests: `lua_common` `take_layout` returns `dark` and strips the class. Screenshots of the
  sample's dark slide under ncar, nsi (the white lockup), nasa-dark (a no-op). Parity: the
  sample's dark HTML page moves under nsi only.

### 8. pptx (`slide-layout.lua`, `slide_layout.py`, `common.py`, the steps)
- `slide-layout.lua` `WORDS` gains `dark`. `slide_layout.draw_dark(slide, w, h)` when `"dark"` in
  the words and `LIVERY["mode"] != "dark"`: `showMasterSp="0"`, `slide.background.fill.solid()`
  dark role, from `LIVERY["furniture"]`: "Dark tab" (`_rect`, accent) unless null, "Dark rule"
  (`dark-rule`), the marks by corner (`_box_picture` of `livery_mod.mark(LIVERY, "dark", kind)`),
  the slide number and title `on-dark`, every body placeholder's runs `on-dark`.
  `common.is_dark(slide)`: the slide's `<p:bg>` is a solid fill of the dark hex. `common.palette
  (slide)`: the role/blend hexes a step draws with (`foreground`, `muted`, `primary-contrast`,
  `primary`, `table-rule`, `table-band`, `background`), swapped on a dark slide to `on-dark`,
  `dark-muted`, `secondary`, `secondary`, `dark-rule`, `dark-band`, `dark`.
- The steps read `palette(slide)` instead of module constants: `style_tables.py` (and every
  table run on a dark slide colored the palette's foreground), `status_glyphs.py`,
  `style_footnotes.py`, `link_captions.py`, `grid.py` (plain text boxes' runs on-dark after
  `body_box`; cards/leads/strips/caution unchanged).
- Tests: `tests/test_dark_slide.py` (new; a module fixture: a dark text slide, a dark grid slide,
  a dark table slide with a footnote, under ncar and nsi, through the steps): the background
  fill; `showMasterSp == "0"`; the dark mark's blob (nsi white; primary's under ncar); the title's
  and `Column 1`'s runs on-dark, `Card 1 body` not; the table's rule secondary; the footnote
  `dark-muted`; the furniture frames; under nasa-dark a no-op. Keynote and PowerPoint open it
  (a slide-level `p:bg` is new). Parity: the sample's and plots' dark pptx slide.

### 9. PDF (`beamerouterthemeEngine.sty`, color theme, inner, `engine-beamer.lua`)
- `\newif\ifengine@darkframe` reset in `\engine@resetframe`; key `enginedark[true]` beside
  `engineclosing`: `\engine@atframe{\engine@darkcolors}` (`background canvas` BrandDark,
  `\engine@fieldcolors{BrandOnDark}`, `alerted text`/`framesubtitle`/`structure` BrandSecondary,
  `frametitle rule` BrandDarkRule, `page number in head/foot` and `footline` BrandOnDark,
  `caption`/`footnote` BrandDarkMuted, `\colorlet{enginetableband}{BrandDarkBand}`,
  `enginetablerule`); `\engine@touchedcolors` gains those beamer colors; the two colorlets
  snapshotted at `\AtBeginDocument` and restored in `\engine@resetframe`. Background: inside the
  `normal` branch `\ifengine@darkframe` skips art and waves and draws the dark role's marks;
  frametitle reads the dark mark's width. `engine-beamer.lua` `wrap_layout()`: `lay.dark` and
  `LIVERY.mode ~= "dark"` → `add_frameoption(blk, "enginedark")`. `latex/examples/sample.tex`
  the twin frame; `latex/authoring.md` :208 and a "patterns" row.
- Tests: `tests/test_latex.py` `DECK` gains `\begin{frame}[enginedark]{Dark}` (a list, inline
  code, `enginestatus`, `\enginefootnote`), a light frame after it; `test_compiles_clean`; page
  ratchets +1; the whites ratchet at zero. `parity-latex check` one page; `parity.sh check` the
  dark PDF pages.

### 10. Plots, decks' text, docs and records
- `livery_mpl.dark()`'s gate becomes unconditional (dark in every format); its docstring,
  `plots.qmd` :159-163, `plots/README.md` :50. `sample.qmd` :377-386; `docs/formats.md` :264-266
  moves to `docs/authoring.md` "Slide kinds" (the definition, the dark-livery no-op, the
  baked-diagram and live-mermaid limits); `engine-revealjs.lua` :29-30; scss :1062; CLAUDE.md
  "Dark liveries" and a bullet for the dark slide (the class, `engine-dark`, `enginedark`,
  `draw_dark`, `is_dark`/`palette`, `furniture`, marks per role, the four blends); CHANGELOG
  Decks, Liveries, Plots, LaTeX.

## Deferred, named
- svgBlip twins for a picture the step places (rasterized, as the gallery's).
- Quadrants (#124).
- A baked mermaid/Graphviz PNG on a dark slide of a light livery (pptx, PDF) stays light;
  per-slide `diagram-dark.lua` is a sprint of its own. Live mermaid on an HTML dark slide reads
  `:root`.
- A box on a dark slide keeps its own colors; dark variants of `boxes.*` are a livery-data
  question.

## Verification
1. On `origin/main` before commit 1: `tests/parity.sh baseline` (ncar cu nsi), `tests/parity-latex.sh baseline`.
2. Every commit: `make test`.
3. `tests/parity.sh check` after 1-4 (identical), 5, 6-7, 8, 9; `parity-latex check` after 4 and 9.
4. `make -C decks/sample all qa`, `make -C decks/plots all qa`, `make qa LIVERY=nsi` and `nasa-dark`
   in the sample; look at the pages named in each commit.
5. Keynote and PowerPoint (`tests/app-open.sh`) after 2, 3 and 8.
6. After 6: each `template.pptx` master and layouts byte-identical.
7. The PR body: a section per commit, parity results, screenshots of the four new slides under
   ncar and nsi; then `/pr-review N`.

## Open questions for Ben
1. Names: `cell_figure`/`simple_table`/`tabled_row`, markers `picture`/`table`/`row`/`cell`,
   `pptx_steps/figures.py`, `livery.json` `furniture`, the blends, `\engine@mark@<role>@<kind>`,
   `engine-dark`, `enginedark`, `common.palette()`/`is_dark()`.
2. Plot bytes base64 in the marker over a kept copy under `.quarto/`.
3. A box on a dark slide keeps its light colors, or dark `boxes.*` variants.
4. `livery_mpl.dark()` always on.

Decided by Ben (2026-10-24): `.brand-dark` is a no-op on a dark livery; a table in a card
demotes the row to plain columns in all three formats. Answered by Ben at the start of the sprint
(2026-10-24): 1 the names as listed; 2 base64; 3 a box keeps its own colors (dark `boxes.*`
variants deferred); 4 `livery_mpl.dark()` on in every format.

## Risks
- A plot's base64 in the intermediate pptx: capped at 8 MB, warned.
- A native `add_table` in LibreOffice and Keynote: `style_tables` restyles it as pandoc's.
- The dark frame's colors leaking into the next frame: the restore list; look at the page.
- `showMasterSp="0"` and the marking strips: the strips are slide shapes (`marking.py`), kept;
  the slide number is a slide placeholder, kept and recolored.
