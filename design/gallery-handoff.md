# Sprint handoff: image galleries

**State (2026-10-22):** landed as #135, squash `f493a70`. Departures: `svg_fallback.py`'s rasterizer became the public `rasterize_svg()` but stays there (common.py loads a livery at import, which that step must not); `boxes.gallery` is `gap: 0.006`, `pad: [0.15, 0.15]` (Ben's pick from the first ncar render, the tighter of three walls); a paragraph of several images is accepted, one item each (pandoc reads consecutive lines as one paragraph); HTML's `galleries()` runs after `rails()`, not innermost; `unwrap_layout` is recursive; a refused gallery or one in a column is unwrapped into its paragraphs, since pandoc's pptx writer draws no picture held in a Div; the review's four fixes (6d2a28c, 44de156, 69bf5f2, fe6e176). The open questions below are answered: those numbers, the names kept, no quickstart gallery.

**For a fresh session.** The fourth sprint after #129 (`citations-handoff.md` #131,
`steps-timelines-handoff.md` #132, `agenda-quote-handoff.md`, then this). One PR against `main`
(branch `decks/gallery` from `origin/main` **after the agenda-quote PR merges**: commit 1 moves
`grid.py` helpers that sprint's `draw_quote` and `draw_agenda` also use, so landing the lift second
means one rebase, not two), a commit per item in the order below, squash-merged once, no version
bump (ask before any tag). Start by reading `CLAUDE.md` whole ("What this is", "pandoc pptx
gotchas" with "Columns: two tiers", "Cards and boxes" and "Steps and timelines, the rail",
"Full-slide figures", "Short slides", "Plots", "The engine", "revealjs (HTML) theme"),
`design/latex-first-class-handoff.md` (the shape and the house rules), `design/citations-handoff.md`
"The goal, stated" (the three rules an element meets), `design/steps-timelines-handoff.md` (the
model for this handoff; the rail is the nearest drawer in every format), `docs/authoring.md` "Steps
and timelines" and "Front matter and slide kinds" (the `.full` paragraph), and the machinery named
under Context. Then `source etc/config_env.sh`, branch, parity baselines (Verification, step 1),
this file as commit 0 at `design/gallery-handoff.md`. Report at the end of each commit: what moved,
what the tests assert, what parity named.

House rules: roles only in theme files; every number from `livery.json`, one reader in
`engine-common.lua`, one drawer per format, the Quarto filter writing through the same LaTeX
environments a hand author writes; **no compatibility shims**; `liveries/*/build/` generated;
American spelling; a CHANGELOG line per user-visible change; tests under `tmp_path`; a step imports
no other step's private name (`tests/test_cli.py` greps); the house commit message. Every name
below is Ben's pick (2026-10-22) or follows from one; do not rename one without asking. Line numbers
are on `c55c2f5` (#132's reviewed tip); the agenda-quote PR moves them, so re-grep.

## Context

The rail (#132) is the newest element and settled the pattern this one follows; the `.full` slide
and the picture steps hold the rest of what a gallery needs. Nothing in the pattern changes:

- **One reader in Lua.** `engine-common.lua`: `rail_kind`/`rail_items`/`top_rails` :501-582 (the
  refusals with one warning each, the div left as it is; top-level only, a nested one warned of);
  `is_figure` :279-295 (a Figure, a `cell`/`quarto-figure` Div, a Para of one Image or a Link round
  one), `is_note` :299, `split_full` :305-322 (one figure, then caption paragraphs or a `::: note`,
  the rest), `is_grid` :378-388 (a lead, steps or a timeline make a grid slide), `take_layout`
  :66-93 (`wide` among `LAYOUT_CLASSES` :51), `SLIDE_KINDS` :50 (`full` is a slide kind, not a
  layout class: HTML's `wrap_layout` and beamer's `CONTENT_KINDS` :82 treat it apart).
- **The three placements exist for one figure.** `.full`: HTML `engine-revealjs.lua` :742-770
  (`C.split_full`, raw `engine-full-figure`/`engine-full-caption` wrappers, `engine-captioned`;
  scss :987-1032: the figure box absolute, inset `--engine-full-pad`, `object-fit: contain`, the
  caption `--engine-full-caption` high; `engine-revealjs.js` `NEVER` :28 skips it); beamer
  `full_frames` :593-630 writes the frame key `enginefull=<src>` and `\enginefullcaption{}`, and
  `beamerouterthemeEngine.sty` `\engine@drawfullbg` :387-398 draws the picture (`\includegraphics
  [width, height, keepaspectratio]` centered between `fullpad` and the raised floor) from the
  **background template** :364, which runs after the body (the caption is a `\gdef` for that
  reason); the key :448-449 takes a value, where `engineclosing` :453 has a keyval default `[true]`;
  pptx `slide-layout.lua` writes `engine-layout: full` and `slide_layout.py` `full_slide` :267-296
  hides the furniture (`showMasterSp="0"` :274, the title deleted), frames pandoc's caption box
  (`FULL_PAD/FULL_FLOOR/FULL_CAP/CAP_SIZE/CAP_COLOR` :56-60) and fits the **one** picture pandoc
  embedded (`pic.image.size`, `k = min(bw/iw, bh/ih)`, centered :290-295), else `run()` :709 warns.
  `.wide`: a layout class every format applies to the body frame (`wrap_layout` :150-176 and scss
  :378-381; `enginewide` inner :369; `slide_layout.lay_out` :129-135 reframes the body placeholders
  at `wide-margin`, which `grid.py` `lay_out` :489-491 inherits through `ph.left/width`).
- **pptx cannot draw a picture in a grid slide today.** `grid-pptx.lua` `flow` :101 warns ("a
  picture/table in a card or a 3+ column slide is not drawn in pptx"); `is_shape` :71-78. A gallery
  is the first grid segment made of pictures, and its images never reach pandoc: the pptx filters
  run strip-raw-figure, slide-layout, inline-footnotes, **grid-pptx, notes-last, single-body**
  (`_extension.yml:76-84`), so grid-pptx.lua turns the div into marker paragraphs (text: no slide
  split, Title and Content stays) and a post step reads the files from disk. `pptx_post.py` runs in
  the deck directory with the pptx's relative path (`Make.common:212-214`); `slide_layout.run` gets
  `path.resolve()` :58 and reads the deck's `titlegraphic:` against `pptx.parent`
  (`_title_graphic` :299-303): the one disk read in the steps, the precedent; `grid.run(prs, name)`
  :547 gets only the name (:60). **Executed-cell plots and baked diagrams are not on disk after a
  pptx render** (`figure-pptx/` lives only under `.quarto/_freeze`), so a plot in a gallery is
  refused in every format, as a picture in a rail is (`rail_items` :522-528).
- **Picture fitting lives in `slide_layout.py` as private recipes.** `_back_picture` :342-353
  (`add_picture(io.BytesIO(photo), x, y, w, h)`, then symmetric `crop_left/right` or
  `crop_top/bottom`: the cover crop, `a:srcRect`, which the title photo already carries into Keynote
  and PowerPoint) and `full_slide`'s contain math :290-295; `_box_picture` :429-433 is
  `add_picture(str(path), ...)` with no fit. `svg_fallback._rasterize` :36-42 runs `rsvg-convert`
  at `DPI` :29 on SVG bytes. These, with `grid.py`'s `_para_text` :47, `body_box` :109-143 (a text
  box in the master's body list style), `group` :146-156, `_style` :196-207 and `_shape` :210-232,
  are the lift the steps handoff asked for once `grid.py` passed ~600 lines (566 now, 135 in
  `common.py`; the agenda-quote sprint adds two drawers).
- **The nearest drawers.** HTML `rails` :287-307 (raw tags, the numbers as custom properties on the
  opening tag, `inline_html` :242 for the inlines); scss `.engine-rail` :489-560; pptx markers
  `⟦engine:rail …⟧`/`⟦engine:item⟧`/`⟦engine:end⟧` parsed by `grid.py` `parse` :60-105 (a nesting
  stack; `MARK`/`PREFIX` :41-42, `_attrs` :51) and dispatched by `lay_out` :489-544 (segments
  stacked from the placeholder's top to `GEOM["body-bottom"]`); `draw_rail` :422-487 (one group,
  measured text boxes); beamer the rail block inner :614-732 (items stored first, one tikzpicture
  at `\end`, `\engine@railpt` :684, the `\loop`, `\ifcsname\string\color@EngineBoxesRailFill` :704
  for a null fill), `\engine@fs{caption}` (`beamerfontthemeEngine.sty:16`), `\enginenote` inner
  :313, the caption template :194.
- **Numbers.** `livery_build.py` `BOXES` :103-116, `BOX_COLORS` :118, `boxes()` :296 (a null
  color stays `None`), `emit_sty_boxes` :870 (generic: any key becomes
  `\engine@boxes@<box>@<key>`, a pad `@pady`/`@padx`, a null color skipped), `emit_css_boxes` :1111
  (hand-written per box; the rail's lines :1133-1138), geometry `resolve()` :224-258
  (`wide-margin` :226, `body-bottom` :227 default `BODY_BOTTOM` 0.9222 :68, the derived
  `geometry.body = [m, top, w, h]` :257, not a yml key), the css geometry :1000-1004 (margin,
  tab-width, wide-margin, the `full` keys; **no `--engine-body-bottom`**: the scss hard-codes the
  70 px foot at :96 and :1062, `70 = 900 × (1 − 0.9222)`), the sty geometry loop :825-827 (dicts and
  scalars; the `body` list is skipped). `geometry.full {pad, footline, caption}` is set in every
  livery.yml (schema :220). Tests: `tests/test_boxes.py` `FRACTIONS` :28 and `test_every_key`
  :31-62 (a key is a role list, a `BOX_COLORS` color, a fraction or a `*pad`; the null case is
  hard-wired to `("rail", "fill")` :41), `test_schema.py::test_sets_are_the_engines` :38 holds the
  schema to `BOXES`; `test_boxes.py:101` uses `boxes.grid` as its unknown-key case, so the box is
  **not** named `grid`.
- **HTML height.** The slide is 1600×900 with `padding: var(--engine-body-top,150px)
  var(--engine-margin) 70px` (scss :96; restated under `html.reveal-print` :1062); the body is
  normal flow under an absolute `h2`; reveal sets `display: block` on each visible `section` by
  inline style, so a flex rule on the section itself would not take. `engine-revealjs.js` `fit()`
  :52 sets `--engine-fit` from `contentBottom` :31 (the children's `offsetTop + offsetHeight`).
- **Fixtures.** `decks/sample/images/example.jpg` (1752×1093) is the sample's only image; the
  quickstart screenshots `decks/quickstart/screenshots/*.png` are 960×540 slide shots (committed,
  the README's images); the cookbook's photo is `latex/images/wallpaper/mesa_lab.jpg`, packed into
  every Overleaf zip by `overleaf_zip.py` `COOKBOOK_FILES` :30. `tests/conftest.py` `pandoc_deck`
  renders plain pandoc in a tmp directory (a test copies `example.jpg` in as `p.jpg`,
  `test_grid.py:27`; `test_grid_pptx.py:40` copies `hero.png`); `tests/test_svg_fallback.py` has an
  inline SVG fixture. `Make.common` `FRAGMENTS` :108 is `$(wildcard images/*)` (flat files: the new
  images go in `images/` directly, not a subdirectory, or a change to them would not rebuild).
- **Already decided elsewhere.** The citations handoff's deferred list (:253) names "an image grid
  with captions (after the grid step's picture limit)": this sprint retires it (the ledger's copy
  :123 too). The ledger's open `.full` + `scale=` divergence (:52-54) is **not** touched: no format
  scales a `.full` gallery (the cells fill the box).

**The look** (Ben, 2026-10-22): a dense grid of equal cells, no chrome by default (a livery may
fill the cells), the whole image in its cell (`contain`) unless the slide says `cover`, a one-line
caption under each picture in the caption look (caption size, muted, centered), the row's cells
one height and the captions on one line across the row. Three placements: in the body under the
title (text above it allowed, as a lead), on a `.wide` slide (the wider body frame), on a `.full`
slide (the cells fill the slide less `geometry.full` pads, furniture hidden, the slide caption line
as `.full` has today).

Ben's decisions (2026-10-22, final): the element is **`.gallery`** (`grid` collides with the
engine's grid-slide term); **`fit=contain`** by default, `fit=cover` opts into cropping; with no
`cols`/`rows` the grid is **square-ish** (`cols = ⌈√n⌉`, `rows = ⌈n/cols⌉`, either overrides, a cap
of **12**); **file images only** (a plot or diagram cell is refused in every format alike); **text
above a gallery is allowed and `height=` is honored** in all three formats (pptx and HTML take the
remaining height; the PDF needs `height=` under text, since TeX cannot measure what is above); the
sample's images come from **the quickstart screenshots, one of them also rotated 90°** so a
portrait image sits in a landscape cell and `contain` shows its letterboxing beside `cover`'s crop.
Not picks: the bare `[enginefull]` frame key for a full-screen gallery (one key with a default, no
second name), captions under the picture (not over), equal cells (no spans or weights: the shares
machinery is there if a later ask wants them), links round gallery images deferred, the quickstart
deck untouched (its README screenshots stay), the sample deck carrying the slides as before.

## The interface, as agreed

```markdown
## Six views of the quickstart

A line above a gallery takes its own height; the cells share what is left (PDF: give height=).

::: {.gallery cols=3 rows=2 height=0.75}
![The cover](images/gallery-1.png)
![A divider](images/gallery-2.png)
![Text, rotated](images/gallery-3.png)
![Columns](images/gallery-4.png)
![Cards](images/gallery-5.png)
![Cards, rotated](images/gallery-6.png)
:::

## A strip of six {.wide}

::: {.gallery cols=6 rows=1 fit=cover}
![](images/gallery-1.png)
… six images, no captions …
:::

## The quickstart, six ways {.full}

::: {.gallery cols=3 rows=2 fit=cover}
… six images …
:::

With `{.full}` the cells fill the slide, and this line is the caption.
```

Rules: a `.gallery` div holds **only** images, each its own paragraph (`![Caption](path)` is a
pandoc `Figure` with the caption; `![](path)` a `Para` of one `Image`), **file images only**
(`png`, `jpg`, `svg`, relative to the deck as every image is; an executed-cell plot or a baked
diagram, anything whose `src` lies under a `figure-*/` or `*_files/` directory, or a `cell`/
`quarto-figure` Div, is refused: pptx cannot reach it from disk), at most **12**, never nested,
never inside a column or card (`top_rails`-style: warned of and left as it is). `cols` defaults
to ⌈√n⌉, `rows` to ⌈n/cols⌉ (only `rows` given: `cols` = ⌈n/rows⌉); given both, n must fit or the
div is refused with a warning. `fit=contain` (default: the whole image, centered in its picture
box) or `fit=cover` (cropped to fill it); anything else warns and takes `contain`. A gallery in
which **any** image has a caption reserves the caption line in **every** cell, so the pictures of
a row stay aligned; a caption is one line (`make qa` fails one that wraps in HTML). `height=` (a
share of the body box's height, in `(0, 1]`) sizes the rows; without it the cells take the body
height left under whatever is above (pptx, HTML) and the whole body height in the PDF (Risks).
Per-image `width=`/`height=` attributes are dropped (the cell sizes the picture). A link round an
image is refused (deferred). A refused gallery stays a div of pictures, so pandoc shows the author
something in every format; in pptx that splits the slide into n (the warning names the slide,
`make qa`'s count catches it).

```latex
\begin{enginegallery}[cols=3,rows=2,fit=cover]          % the div's keys; height=0.6 of the body box
  \engineimage[The cover]{images/gallery-1.png}         % [caption] optional
  \engineimage{images/gallery-2.png}
  …
\end{enginegallery}

\begin{frame}[enginefull]                                 % bare: the full style, no background picture
  \enginefullcaption{The cells fill the slide; this line is the caption.}
  \begin{enginegallery}[cols=3,rows=2,fit=cover] … \end{enginegallery}   % drawn by the background, as the picture is
\end{frame}
```

`livery.json` `boxes`, one new block (defaults in `BOXES`; every livery keeps its look with no
`livery.yml` change):

```python
"gallery": {"gap": 0.012, "pad": [0.3, 0.3], "fill": None},
# gap: between cells, both ways, of the slide's width (the columns' 0.03 is too loose for a photo wall);
# pad: em of the body, [vertical, horizontal]: the cell's inset, and the caption's gap under its picture;
# fill: a cell background behind picture and caption, null for none (a livery's tile look)
```

`BOX_COLORS` gains `"gallery": ("fill",)` (nullable, as `rail.fill`). `cols`, `rows`, `fit` and
`height` are slide attributes, not livery keys: they describe the content, and a livery `fit` would
be the first string-valued box key `test_every_key` admits. The caption is the `caption` type role,
muted: no new type role. Two geometry emissions join: css `--engine-body-bottom` (px of
`geometry.body-bottom`) and sty `\engine@geom@bodyheight` (`geometry.body[3]`, the body box's
height as a fraction of the paper): HTML needs the body box to size the rows, beamer the body
height for the default `height=`.

## The reader's shape (engine-common.lua)

```lua
local GALLERY_MAX = 12
local function is_gallery(b)   -- a Div .gallery
-- gallery_items(div, who) -> { cols, rows, fit, height = number|nil,
--   items = { { src = string, caption = inlines|nil }, ... }, captioned = bool } or nil, warned of
-- top_galleries(blocks, who, draw) -> blocks: each top-level gallery becomes draw(g); one inside
--   another div warned of and left (top_rails' shape; no livery, no role: a gallery has none)
```

Per item: a `Figure` holding one `Plain`/`Para` of one `Image` (caption =
`pandoc.utils.blocks_to_inlines(fig.caption.long)`, else the image's alt inlines), or a
`Para`/`Plain` of one `Image` (caption = its alt inlines; `![](x)` has none). Refused with one
warning each: any other block ("a gallery holds image files; a plot or diagram is not drawn"), a
`src` matching `figure%-[%w%-]+/` or `_files/`, a `Link` round an image, a nested `.gallery`, more
than 12, more than `cols*rows`, a `cols`/`rows` that is not a positive integer, a `height` outside
`(0, 1]`. `is_grid` :378-388 gains `gallery` beside `lead`/`steps`/`timeline` (a two-column slide
beside a gallery flattens, as beside a rail). `split_full` :305-322 accepts `is_gallery(b)` as the
figure (`is_figure` itself unchanged: `grid-pptx.lua`'s `is_shape` uses it). `GALLERY_MAX`
exported like `RAIL_MAX`.

## The commits, in order

### 0. This handoff

### 1. The common.py lift (the sweep the steps handoff asked for; no behavior change)

- `pptx_steps/common.py` gains, moved not copied: `para_text` (grid's `_para_text` :47),
  `body_box` :109, `group` :146, `shape` (grid's `_shape` :210), `style_runs` (grid's `_style`
  :196); and new `contain_box(iw, ih, x, y, w, h) -> (x, y, w, h)` (the largest box of the image's
  aspect inside, centered: `full_slide` :290-295's math), `cover_crop(iw, ih, w, h) -> (lr, tb)`
  (`_back_picture` :347-350's symmetric fractions), `fit_picture(slide, src, x, y, w, h, fit,
  name=None)` (`src` a path or bytes: `add_picture`, then `contain_box` on the frame or
  `cover_crop` on the crops; returns the picture), and `rasterize_svg(svg: bytes, dpi: int) ->
  bytes` (svg_fallback's `_rasterize` :36-42, its "rsvg-convert not found" message kept, reworded
  for both callers).
- `grid.py` imports them back (`_close`, `_card_height`, `_prefix`, `_pick_role`, `_oval`, `_badge`
  stay: the gallery needs none). `slide_layout.py`: `_back_picture` becomes `fit_picture(...,
  "cover")` plus its move to the back of the tree; `full_slide` uses `contain_box`; `_box_picture`
  stays (no fit). `svg_fallback.py`: `_rasterize(svg)` → `rasterize_svg(svg, DPI)`.
- `grid.run(prs, name)` :547 becomes `grid.run(prs, path: Path)` (`path.name` for its messages,
  `path.parent` for the gallery's files in 4); `pptx_post.py:60` passes `path.resolve()` as
  `slide_layout` gets; `tests/test_grid.py` `STEP` :49 and `test_card_type_step` call
  `grid.run(prs, p)`.
- Tests: the existing suites pass unchanged (`test_grid.py`, `test_svg_fallback.py`,
  `test_boxes.py`, `test_compositions.py`); `test_cli.py`'s private-import ratchet holds (nothing
  imports a `_name` across steps).
- Proof: `tests/parity.sh check` **identical** (the pptx XML byte for byte: shape names and order
  untouched). Ledger: the lift recorded under the #105–#126 window entry.

### 2. Livery data

- `livery_build.py`: `BOXES["gallery"]`, `BOX_COLORS["gallery"]` as above; `emit_css_boxes` adds
  `--engine-gallery-gap` (px of the width), `--engine-gallery-pad` (`v h` em),
  `--engine-gallery-pad-y`, `--engine-gallery-fill` (`transparent` when null); `emit_css` adds
  `--engine-body-bottom: <px>;` beside `margin`/`wide-margin` (:1000-1002); `emit_sty` adds
  `\def\engine@geom@bodyheight{<geometry.body[3]>}` after the geometry loop (:825-827 skips the
  list). `emit_sty_boxes` needs nothing (generic; the null fill skipped).
- `engine-revealjs.scss:96` and `:1062`: the foot becomes `calc(900px - var(--engine-body-bottom,
  830px))` (identical pixels for every bundled livery; the one number now comes from the livery).
- `livery.schema.json`: a `gallery` node under `boxes` after `rail` (:611 is the model; `fill`
  `oneOf null | color-or-role`); `livery schema --doc` regenerates `liveries/REFERENCE.md`;
  `livery build liveries/*/`, committed.
- Tests: `test_boxes.py:41` generalizes the null case to `lb.BOXES[box][k] is None` (so
  `rail.fill` and `gallery.fill` both pass); `test_every_key` adds the four css lines and the sty's
  `\engine@boxes@gallery@gap`; a null-fill and a set-fill case in `test_colors_resolve`'s pattern
  (:85); `test_schema.py` holds by itself.
- Proof: `tests/parity.sh check` identical (nothing reads the keys; the padding is the same 70 px).
  CHANGELOG Liveries: one line, nothing to do.

### 3. The reader, HTML, and the sample deck

- `engine-common.lua`: `is_gallery`, `gallery_items`, `top_galleries`, `GALLERY_MAX` after
  `top_rails`; `is_grid` and `split_full` as above.
- `engine-revealjs.lua`: `gallery_html(g)` → raw blocks: `<div class="engine-gallery[
  engine-gallery-sized]" style="--engine-gallery-cols: 3; --engine-gallery-rows: 2;
  --engine-gallery-fit: cover[; --engine-gallery-height: 0.6]">`, per item `<figure
  class="engine-gallery-item">` + the `Image` itself (its `width`/`height` attributes dropped, so
  pandoc writes the `<img>`, escapes it and `embed-resources` inlines it: CLAUDE.md's "pandoc's
  embed-resources inlines `<img src>`") + `<figcaption>…</figcaption>` (a `figcaption` in every
  item when `g.captioned`, an empty one holding `&nbsp;` where the image has none) + `</figure>`,
  then `</div>`. `galleries(blocks)` walks content slides as `wrap_layout` :150 does
  (`C.content_heading`, so `.full` is not its business): each top-level gallery through
  `top_galleries`, and a slide holding one gets its body (less notes) in a `Div
  .engine-gallery-body`, which `unwrap_layout` :309 turns into raw tags as it does `.engine-body`.
  Into the chain at :673 innermost: `…status_items(rails(galleries(doc.blocks), livery))…`, so
  `.engine-body` wraps outside it on a `.wide` slide. The `.full` branch :754: when
  `C.is_gallery(fig)`, `out:extend(gallery_html(C.gallery_items(fig, "engine-revealjs")))` inside
  `.engine-full-figure` (a refused gallery falls to the existing warning, its text extended "one
  figure or a gallery").
- `engine-revealjs.scss`, after `.engine-rail`: `.engine-gallery-body { display: flex;
  flex-direction: column; height: calc(var(--engine-body-bottom) - var(--engine-body-top, 150px));
  > * { flex: none; } > .engine-gallery { flex: 1 1 0; min-height: 0; } > .engine-gallery-sized {
  flex: none; height: calc(var(--engine-gallery-height) * (var(--engine-body-bottom) -
  var(--engine-body-top, 150px))); } }` (the wrapper is the body box in slide pixels, which is why
  `--engine-body-bottom` exists; a fixed-height box also keeps the autofit script idle:
  `contentBottom` never passes the floor). `.engine-gallery { display: grid; grid-template-columns:
  repeat(var(--engine-gallery-cols), minmax(0, 1fr)); grid-template-rows:
  repeat(var(--engine-gallery-rows), minmax(0, 1fr)); gap: var(--engine-gallery-gap); margin: 0; }`;
  `.engine-gallery-item { display: flex; flex-direction: column; min-width: 0; min-height: 0;
  margin: 0; padding: var(--engine-gallery-pad); box-sizing: border-box; background:
  var(--engine-gallery-fill); }`; `.engine-gallery-item img { flex: 1 1 0; min-height: 0; width:
  100%; height: auto; max-width: none; max-height: none; margin: 0; object-fit:
  var(--engine-gallery-fit, contain); }` (reveal's img margins and 95% caps overridden);
  `figcaption { flex: none; margin-top: var(--engine-gallery-pad-y); color: var(--engine-muted);
  font-size: calc(var(--engine-type-caption, 0.7) * 1em); line-height: 1.3; text-align: center;
  white-space: nowrap; overflow: hidden; }` (the look of `figcaption` :309 and `.engine-note`).
  Full: `.engine-full-figure > .engine-gallery { width: 100%; height: 100%; }`, and the generic
  `.engine-full-figure` rules at :1000-1016 scoped `:not(.engine-gallery *)` so they neither hide
  the figures nor force `object-fit: contain` on a cover gallery.
- `common/utils/deck_qa.py` `MEASURE_JS` :38: `galleryCapOver` (any `.engine-gallery-item
  figcaption` with `scrollWidth > clientWidth + 1`), on `.full` slides too; `html_findings` :323
  fails it: "a gallery caption runs past its cell; shorten it".
- `decks/sample/sample.qmd`: the three slides above after "A timeline" (:233). Images: six PNGs
  `decks/sample/images/gallery-1.png … gallery-6.png`, made once with PIL from the quickstart
  screenshots (`01-title`, `02-divider`, `03-text`, `04-columns`, `12-cards`, downscaled to 640 px
  on the long side; `03-text` and `12-cards` **also rotated 90°** as `gallery-3` and `gallery-6`,
  the portrait pair that letterboxes under `contain` on the first slide and crops under `cover` on
  the other two), the one-liner in the commit message, no script kept; flat in `images/` because
  `FRAGMENTS` is `images/*`. The quickstart and its README screenshots are untouched.
- Tests: `tests/test_gallery.py` (new; the `pandoc lua` harness of `tests/test_rail.py` :28-58 with
  a `gallery` mode): defaults (`n=5` → 3×2; `rows=2` alone → `cols=3`), the caption from a Figure
  and from alt text, `captioned`, `fit` and `height` parsing, each refusal's warning (seven on 3×2,
  a paragraph, a `figure-revealjs/` plot, a Link, a nested gallery, 13 images), `top_galleries`
  leaving one in a column with the warning; `tests/test_deck_qa.py` a `galleryCapOver` finding.
- Proof: `make -C decks/sample html`, the three slides screenshotted under ncar and nasa-dark (the
  dark cells), at 16:9 and letterboxed, and `?print-pdf`; `make qa` (the pptx and PDF come in 4 and
  5; until then the count check names the three slides, expected: pandoc's pptx splits each image
  onto its own slide). CHANGELOG Decks.

### 4. pptx

- `grid-pptx.lua`: `is_wide` :52-60 becomes `layout_words(blocks)` (the notes line's words as a
  set; `mark` reads `wide` and `full` from it); `mark()` :136 gains, beside the rail: a top-level
  `.gallery` whose `C.gallery_items` reads → `marker("gallery cols=3 rows=2 fit=cover[ height=0.6]
  [ full]")`, per item `marker("item src=<src, percent-encoded: spaces, ⟧, =>")`, its caption a
  `pandoc.Para(caption)`, `marker("end")`, a last `marker("end")`; a refused div is inserted as it
  is (pandoc draws the pictures; the slide splits; the warning said so). `flow()` :88 warns of a
  `.gallery` inside a column or card in the rail's words (:98) and leaves it. The docstring.
- `grid.py` `parse` :60: `gallery` opens a segment at the top level; `item` nests under `rail`
  **or** `gallery`. `lay_out` :489: `if seg[0] == "gallery"`: when the marker says `full` and the
  next segment is text, that text is the slide caption and is consumed; `y +=
  gallery.draw_gallery(slide, (left, y, width, max(bottom - y, 0)), seg[1], seg[2], caption,
  slide_width, slide_height, deck_dir)`. `run(prs, path)` passes `path.parent`.
- `pptx_steps/gallery.py` (new, ~120 lines; imports only `common` and `measure`): `cells(x, y, w,
  h, cols, rows, gap)` (row-major integer EMU frames, `column_frames`' rounding both ways);
  `draw_gallery(...)`: `gap = round(BOXES["gallery"]["gap"] * slide_width)`, `vpad, hpad =
  pads("gallery")`; the box is the one given, or with `height=` `min(room, round(height *
  body_h))` where `body_h = round(GEOM["body"][3] * slide_height)`, or on `full` `(pad, pad, W -
  2pad, H - pad - floor[ - cap])` from `GEOM["full"]` with the slide caption a `body_box` at `(pad,
  H - floor - cap, W - 2pad, cap)`, anchor middle, each paragraph `algn="ctr"` and
  `style_runs(p, caption_pt, color=muted)`, named "Gallery caption" (the look `note_style` :203 and
  `full_slide` :283-288 give pandoc's box); per item a caption `body_box` (`"Gallery k caption"`,
  margins `vpad` above, `hpad` sides, centered, caption pt, muted) measured by `text_height` ×
  `SLACK`, the tallest the gallery's one caption height `cap_h` (0 when no item has a caption); the
  picture box `(cx + hpad, cy + vpad, cw - 2hpad, ch - 2vpad - cap_h)`; the file `deck_dir /
  unquote(src)` read as bytes (a missing file warns with the slide title and leaves the cell empty),
  an `.svg` through `rasterize_svg(data, 200)`, then `fit_picture(slide, data, *box, fit,
  name=f"Gallery {k} picture")`; a `rect` `"Gallery k cell"` in `fill` behind when set; the caption
  box placed at `(cx + hpad, cy + ch - vpad - cap_h, cw - 2hpad, cap_h)`; one `group(slide, shapes,
  "Gallery")`; returns the height taken plus `vpad` (not on `full`). The marker grammar and the
  shape names in the docstring.
- `slide_layout.py`: `full_slide` :267 splits into `hide_furniture(slide)` (:274-277) and the
  picture fit; `run()` :709: `if has_gallery(slide): hide_furniture(slide)` (a body paragraph whose
  `para_text` starts with `⟦engine:gallery`, left for grid.py) `elif not full_slide(...)`: the
  warning. The `wide` reframe :130-135 needs nothing: grid.py inherits the placeholder's frame.
- Tests: `test_grid_pptx.py::test_gallery_marked` (the markers, the encoded `src`, a caption
  paragraph between `item` and `end`, `full` from the notes line, a refused gallery left as pictures
  with its warning); `test_gallery.py`'s pptx half on its own module fixture (the `deck` pattern of
  `test_grid.py` :60-74, so `test_column_rules`' indices do not move; `p.jpg`, a `hero.png`, the
  SVG fixture): the group, six pictures (`shape_type == 13`) each inside its cell frame from the
  formula (`cells` recomputed in the test from `livery.json`), contain: the picture's aspect the
  file's and centered in its box; cover: the frame equal to the picture box and `crop_left ==
  crop_right > 0` for a landscape file in a tall cell; captions one height and one top per row,
  caption pt, muted, centered; an item without a caption still reserving the line; `.wide`: the
  first cell's left at `wide-margin`; `.full`: `showMasterSp="0"`, no title, the cells inside `(pad,
  pad, W-2pad, H-pad-footline-cap)`, "Gallery caption" at `H - footline - cap`; the SVG item a PNG
  blob (`pic.image.content_type`); `height=0.5` halving the rows; no marker left; `test_integers`'
  check on the new slides; a missing file's warning.
- Proof: `make -C decks/sample pptx`; **PowerPoint and Keynote open it** (`tests/app-open.sh`'s
  pair; new here: pictures with `srcRect` crops inside a group, twelve-plus pictures on one slide,
  a text box grouped with pictures; do it now, not at the release). CHANGELOG Decks (the same line
  as 3, extended).

### 5. beamer and the LaTeX twin

- `beamerinnerthemeEngine.sty` after the rails (:732): `\pgfkeys{/engine/gallery/.cd, cols/.store
  in=, rows/.store in=, fit/.store in=, height/.store in=}`; `\newenvironment{enginegallery}[1][]`
  resets the keys (`fit` `contain`, `height` `1`, `cols`/`rows` 0 = derive), `\global\engine@galn=
  \z@`, `\global\engine@galcapfalse`; `\newcommand\engineimage[2][]` stores `\engine@gal@src@k` and
  `\engine@gal@cap@k` globally (`\gdef`), sets `\engine@galcaptrue` on a non-empty caption, errors
  past 12 ("enginegallery: more than twelve images", the share-error pattern :641). At `\end`:
  `cols = \fpeval{ceil(sqrt(n))}` when 0, `rows = ceil(n/cols)`, an error when `n > cols*rows`;
  then, unless the frame style is `full` (`\engine@framestyle`), `\hbox{\begin{tikzpicture}[x=1pt,
  y=1pt]\useasboundingbox …; \engine@gallerycells{0pt}{0pt}{\linewidth}{\engine@galheight\dimexpr
  \engine@geom@bodyheight\paperheight}\end{tikzpicture}}\par`. `\engine@gallerycells{x}{y}{w}{h}`
  (tikz commands only, y up, top-left origin as the rail's `\engine@railpt` :684, which it reuses):
  `gap = \engine@boxes@gallery@gap\paperwidth`, `cw = (w - gap(cols-1))/cols`, `ch = (h -
  gap(rows-1))/rows`, the caption line `\engine@galcaph` = the height plus depth of `\strut` in
  `\engine@fs{caption}` plus `pady` when `\ifengine@galcap`; per k (`\loop`): column `(k-1) mod
  cols`, row `(k-1) div cols`; a `\fill[EngineBoxesGalleryFill]` cell when the color exists
  (`\ifcsname\string\color@…`, :704); `\sbox\@tempboxa{\includegraphics{src}}` for the natural size;
  contain: `\node[anchor=center, inner sep=0pt] at (center) {\includegraphics[width=pw, height=ph,
  keepaspectratio]{src}}`; cover: `\begin{scope}\clip (px,py) rectangle (px+pw, py-ph);
  \node[anchor=center, inner sep=0pt] at (center) {\includegraphics[height=ph]{src}}\end{scope}`,
  `width=pw` instead when the image is taller than the box (`\fpeval{\strip@pt\wd\@tempboxa * ph <
  \strip@pt\ht\@tempboxa * pw}`); the caption `\node[anchor=north, inner sep=0pt, text width=pw,
  align=center, font=\engine@fs{caption}\selectfont, text=BrandMuted]` at `(cx + cw/2, py - ph -
  pady)`.
- `beamerouterthemeEngine.sty`: `\define@key{beamerframe}{enginefull}[]{…}` (:448: the `[]` default
  makes a bare `[enginefull]` legal, the full style with no background picture, so no second key);
  `\engine@drawfullbg` :387: when `\engine@fullimage` is empty, `\engine@gallerycells
  {\engine@fullpad}{\paperheight-\engine@fullpad}{\paperwidth-2\engine@fullpad}{\paperheight-
  \engine@fullpad-\engine@fullfloor}` (after the caption node has raised `\engine@fullfloor`, as the
  picture branch does) instead of the `\includegraphics` node; `\engine@resetframe` :429 zeroes
  `\engine@galn` globally. Check: the background template is drawn after the body (the `\gdef`
  caption proves the order), so the stored items are there; pandoc writes `\begin{frame}{}` for the
  emptied title, which draws nothing under the full style.
- `engine-beamer.lua`: `galleries(blocks)` beside `rails` :380 through `C.top_galleries`:
  `\begin{enginegallery}[cols=,rows=,fit=[,height=]]`, per item `\engineimage[<inlines_to_latex
  (caption)>]{<src>}`, `\end{enginegallery}`; into the chain at :808 beside `rails`. `full_frames`
  :593 (its local `split_full` :584 takes the first `Image` src, which would be a gallery's first
  picture): when `C.is_gallery(fig)`, `add_frameoption(blk, "enginefull")` (bare), the title
  emptied, `\enginefullcaption{…}` as today, and the gallery div kept for `galleries()` to write.
  `opens_paragraph` :418 needs nothing (`\begin{enginegallery}` is a raw block, not a paragraph).
- `latex/examples/sample.tex`: the three frames after "A timeline" (:332), the full one
  `\begin{frame}[enginefull]` with `\enginefullcaption`; the images as `latex/images/gallery-k.png`,
  **symlinks** to `../../decks/sample/images/gallery-k.png` (one source of truth; `latex/talk.tex`
  is the precedent for a link; `zipfile` follows them), listed in `overleaf_zip.py` `COOKBOOK_FILES`
  :30 (every Overleaf zip grows by the six images: Risks). `latex/authoring.md` "The patterns" rows
  (:13) and a section "Galleries" after "Steps and timelines" (:119); `latex/sheet.py` unchanged.
- Tests: `tests/test_latex.py` `DECK` :30 gains a frame with `enginegallery[cols=3]` of three
  `\engineimage` (one captioned; the images: three small PNGs written with PIL into the module's
  tmp directory, as `refs.bib` is) and a `\begin{frame}[enginefull]` gallery frame;
  `test_pick_moves`' page count 7 → 9 (:179) with `pdftotext` showing the caption;
  `test_compiles_clean` covers both; `TOO_MANY_IMAGES` (four on `cols=3,rows=1`) and the
  thirteen-image error on the `TOO_MANY_STEPS` pattern (:95, :204). CI's Overfull ratchet covers
  the cookbook variants.
- Proof: `pdftoppm -r 60` of the three frames under ncar, cu, nasa-dark and 4:3 (`make -C latex
  examples variants`); `tests/parity-latex.sh check`: the cookbook gains three pages, nothing else
  moves; `make -C decks/sample pdf && make -C decks/sample qa`: counts agree in all three formats.
  CHANGELOG LaTeX.

(The full and wide placements are inside 3, 4 and 5: each format's commit lands all three.)

### 6. Documentation and records

- `docs/authoring.md`: a section "Image galleries" after "Steps and timelines" (:183): the snippet,
  the rules, `fit`, captions one line, `height=` and why the PDF needs it under text, the three
  placements, the pptx group names ("Gallery", "Gallery 1 picture", "Gallery 1 caption", "Gallery 1
  cell"), the plot refusal and why, the LaTeX pointer; the "Front matter and slide kinds" `.full`
  paragraph names the gallery case.
- `CLAUDE.md`: "Full-slide figures" names the gallery case in all three formats; a "Galleries"
  bullet after "Steps and timelines, the rail" names the reader, the markers, `gallery.py`, the
  disk read and its limit, `hide_furniture`, the `common.py` helpers, the HTML body-box wrapper and
  `--engine-body-bottom`, `enginegallery`/`\engineimage`/bare `[enginefull]`; "LaTeX authoring"
  lists the environment. `tests/test_docs.py` resolves the pointers.
- CHANGELOG: Decks (the element in three formats, the limits, the doc pointer), Liveries
  (`boxes.gallery`, nothing to do), LaTeX. `design/unplanned-city-ledger.md`: the lift done and the
  deferred item retired. Memory: `next-sprints-after-129.md`.

## Verification

1. Before the first commit, on `origin/main` (after the agenda-quote PR merged): `tests/parity.sh
   baseline` (ncar cu nsi) and `tests/parity-latex.sh baseline`, same checkout, same day.
2. Every commit: `make test` (`livery build --check`, pytest with the new tests, the docs gate).
3. `tests/parity.sh check` after 1 and 2 (identical) and at the end: the sample's three new slides
   are the only extra pages in every format, the quickstart untouched; `parity-latex check` after
   5: the cookbook's three pages.
4. `make -C decks/sample all && make -C decks/sample qa`: counts agree, no overflow, no caption
   wrap at ncar and nasa-dark (`make qa LIVERY=nasa-dark`); the pages looked at: `contain`
   letterboxing the two rotated shots, `cover` cropping them, the captions on one line across a
   row, the `.full` cells inside the pads with the caption line, the `.wide` strip at the wide
   margin.
5. PowerPoint and Keynote open `decks/sample/sample.pptx` (commit 4, not the release).
6. The PR body: a section per commit, the parity results, a contact sheet of the three slides in
   three formats; `/pr-review N`.

## Risks

- **Many pictures per slide in Keynote and PowerPoint**: twelve pictures, each with `srcRect`
  crops, inside one group is new; the title photo proves a cropped picture alone opens. If Keynote
  balks at the group, draw the gallery ungrouped (one line) and say so in the docs.
- **An SVG item in pptx** is rasterized to a PNG (no `svgBlip` twin: that would mean a relationship
  of its own per picture, `svg_fallback`'s zip-level surgery, which the Presentation stage cannot
  do). Vector galleries in pptx are deferred; the guide says so.
- **The beamer default height.** TeX cannot measure what stands above the gallery inside a frame,
  so a PDF gallery under a paragraph takes the whole body height by default and runs past the foot
  unless the author gives `height=` (which pptx and HTML also honor). The docs say: a gallery alone,
  on a `.full` slide, or with `height=`; `make qa`'s PDF checks catch the caption text past the
  footer, not a bare picture.
- **HTML**: the body-box wrapper is a fixed height, so a `†` footnote on a gallery slide (absolute at
  the floor) overlaps the last row; documented (use the caption). The autofit never fires on a
  gallery slide (the wrapper ends at the floor); long text above a gallery squeezes the rows
  instead, visible, not hidden. Reveal's inline `display: block` on sections is why the wrapper,
  not the section, is the flex box.
- **pandoc placeholder interplay**: the gallery reaches pandoc as paragraphs, so Title and Content
  holds and nothing splits; a *refused* gallery reaches pandoc as pictures and splits its slide into
  n (visible; `make qa`'s count catches it; the warning names the slide).
- **Beamer memory**: twelve `\includegraphics` per frame, each boxed once for its size and drawn
  once; XeLaTeX embeds a repeated file once. A gallery is not pausable (nothing to pause).
- **The Overleaf zips** each grow by the six images; keep them PNG at 640 px (slide shots compress
  well) and check the zip sizes in the release job's summary.
- **The `.full` + `scale=` divergence** (ledger :52-54) stays as it is: no format scales a `.full`
  gallery.
- **Filenames**: a `src` with a space, `=` or `⟧` is percent-encoded into the marker and decoded in
  `gallery.py`; the docstring says so.

## Open questions for Ben

1. `boxes.gallery.gap` 0.012 and `pad` [0.3, 0.3]: look at the ncar render before the data commit
   is squashed; a tighter or looser wall is one number.
2. The HTML class names `engine-gallery*` and the pptx group name "Gallery" (the rail's names were
   taken as given; these follow the same shape).
3. Whether the quickstart deck also gets a gallery slide (this handoff assumes not: its README
   screenshots and `screenshots.py`'s `SLIDES` stay).

## Memory for the fresh session

`no-compat-shims.md`, `minimal-prs-versions.md`, `approval-text-in-chat.md`, `american-spelling.md`,
`sprint-tags-recut.md`, `latex-first-class.md`, `design-framework-goal.md`,
`next-sprints-after-129.md`, `pr-132-review.md`. After the PR opens, update
`next-sprints-after-129.md`.
