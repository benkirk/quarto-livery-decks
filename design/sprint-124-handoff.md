# Sprint handoff: #124's open items, the card framework, and the liveries off their workarounds

**For a fresh session.** One PR against `main` (branch `sprint/124`), a commit per item in the
order below, squash-merged once, no version bump (the release is its own small PR after; ask
before any tag). Start by reading `CLAUDE.md` whole ("pandoc pptx gotchas" and "revealjs"
twice), `design/engine-and-liveries.md` section 6, `liveries/nasa-jsc-eg/reference/notes.md`
("What the engine cannot do yet"), GitHub issues #124 and #125, and this file. Then
`source etc/config_env.sh`, `git checkout -b sprint/124 origin/main`, and take the parity
baselines (Verification, step 1) before the first commit. Report at the end of each commit:
what moved, what the tests assert, what parity named.

House rules that bind here: roles only (no palette name or hex in a theme file; a new number
goes into `livery.json` and every format reads it); a knob is drawn by all three formats or by
none; no compatibility shims (Ben is the only consumer; a rename moves every caller in the same
commit); `template.pptx` is generated (`make livery`), never edited; integer EMUs in the pptx (a
float in `x/y/cx/cy/sz/adj/w` makes PowerPoint prompt "Repair?"); set all four of a shape's
left/top/width/height together; American spelling; every user-visible change gets a
`CHANGELOG.md` `[Unreleased]` line in its commit (Decks / Liveries / LaTeX); a `livery.yml` key
is renamed only with Ben's agreement; a test writes only under `tmp_path`; the house commit
message (one-line title, a body with the mechanism and the fix, the session's attribution
lines). When something here turns out wrong against the code, say so and fix the plan in the
commit message rather than bending the code to the plan.

## Context

PR #123 (squash `b66739c`, 2026-10-21) added the `nasa-jsc-eg` livery and the engine features it
needed, and filed the rest as #124 (engine improvements) and #125 (bugs). Ben's sequence: this
sprint (every open item of #124, #125's two, and a card/grid framework he sketched from two NCAR
brand slides), then a release, a window sweep later. The livery changes that drop the
workarounds land in this PR, so nasa-jsc-eg ends the sprint with no "surface role to get a mark"
tricks.

The reference slides (Ben's screenshots, 2026-10-21): **(A)** a gray lead box with an orange
accent bar at its left (a bold headline line, a plain line); three equal cards, each a colored
header band ("OPTION 1" + a subtitle line in white), a white body (a bold "Total Cost" line, a
small-caps label "LOCAL INVESTMENT", a huge "$20M"), a tinted orange strip ("→ **$15M** to
consortium system"), a label "SCIENCE ENABLED" over a list whose items carry ✓ (green) ⚠ (amber)
✗ (red, the item's text muted); the chosen card outlined green. **(B)** a one-line lead and three
solid rounded cards (blue, light blue, orange) with white bold titles and white body text.

### Decided with Ben (2026-10-21) — do not re-ask

- The first cut covers cards + lead box + strip + status glyphs; pptx cards are native,
  editable shapes (rectangles + text boxes), not fill-on-placeholder.
- The `boxes:` defaults keep the HTML's numbers; pptx and PDF move a few points toward it
  (parity deltas named in the commit).
- PDF columns match HTML and pptx (`[T,onlytextwidth]`, the gap from `boxes.columns.gap`);
  `{.wide}` is the deliberate way to a wider body on one slide, in every format.
- Bullets change only when a livery sets `bullets:`; ncar/cu/nsi/nasa keep their current look.
- The sample deck gets a slide per pattern; the quickstart one card slide in the README
  screenshots; no fifth gallery column.
- The Apptainer arm64 runtime job (Launchpad 503 + no arm64 `.deb` upstream) is left alone
  unless it fails again.

## The commits, in order

Sizes are rough. "Parity" = `tests/parity.sh check` and `tests/parity-latex.sh check` against
the baselines taken on `origin/main` (same checkout, same day); a commit that changes looks on
purpose names every departure in its message. Part A (1–9) is the column/card machinery, Part
B (10–17) the rest of #124/#125 and the livery; if the sprint drags, Part A alone is a
coherent PR and Ben decides whether to split — ask, do not split on your own.

### Part A — columns and cards

#### 1. `boxes:` and the `display` type role — one set of box numbers for every format

Today the caution bar is 6 pt·K (pptx, `slide_layout.py:203-223` `CAUTION_W`) / 8 px (HTML,
`engine-revealjs.scss:369-375`) / 3 pt (PDF, `beamerinnerthemeEngine.sty:300-311`); the caution
pads 14/8 pt·K / 0.55em 0.9em / `\fboxsep` 0.55em; the feature panel pads 14/10 pt·K
(`slide_layout.py:674-722`) / 0.6em 0.9em (scss 676-731) / `\engine@panelpad` 0.6em (inner
220-246, outer 318-327); the column gap 0.03 of the width in the pptx template only
(`livery_template.py:356`). Consolidate onto `livery.json` `boxes`, a top-level `livery.yml`
block (it mixes slide fractions, em pads and colors, so not under `geometry`), with `BOXES`
defaults in `livery_build.py`, merged per sub-block in `resolve()`, colors resolved to hex by the
same `hexof` lambda `marking()` uses (a role, a palette name or a hex in `livery.yml`; hex in
the json — the house idiom chosen in #123's review). Units: `gap` of the width; `bar`, `rule`,
`outline`, `radius` of the height; `pad` = `[vertical, horizontal]` in em of the body type (two
of three formats already pad in em; the pads then follow `type-body:` in HTML and PDF).

```yaml
boxes:
  columns: { gap: 0.03, rule: 0 }               # rule: a width; 0 = no rule between columns
  caution: { bar: 0.0089, pad: [0.55, 0.9] }     # 8 px of 900; HTML keeps its pixels
  panel:   { pad: [0.6, 0.9] }                   # the feature panel
  lead:    { fill: surface, bar: 0.0089, bar-color: accent, pad: [0.55, 0.9] }
  card:    { fill: background, radius: 0, outline: 0.0033, outline-color: highlight,
             pad: [0.5, 0.8], head-pad: [0.35, 0.8] }
  strip:   { tint: 0.18, pad: [0.3, 0.8] }       # 0.18 = caution-fill's share (BLENDS): one tint recipe
  status:  { done: highlight, warn: warning, fail: accent }
```

- What moves (ncar: 720×405 pt canvas, body 12): pptx caution bar 4.5 → 3.6 pt, pads 10.5/6 →
  10.8/6.6 pt; PDF caution bar 3 → 2.3 pt; pptx panel pads 10.5/7.5 → 10.8/7.2 pt. HTML and PDF
  pads keep. `caution-fill` stays a blend (fixed role); strips tint at draw time (the role varies
  per slide) with `livery_mod.mix()` / `color-mix()` / `!…!` — the three mixers already exist.
- New `TYPE` role `display: (40, 1.08)` (the `.big` number; 30 pt on ncar, 36 on nasa-jsc-eg,
  as `closing`) — reaches the css (`--engine-type-display`) and sty (`\engine@type@display`,
  a `\setbeamerfont{display}`) through the existing loops; `livery_template.py` needs nothing.
- Emitted: css `--engine-column-gap` (px), `--engine-column-rule`, `--engine-caution-bar`,
  `--engine-caution-pad: 0.55em 0.9em` (a two-value string `padding:` takes directly),
  `--engine-panel-pad`, `--engine-lead-{fill,bar,bar-color,pad}`,
  `--engine-card-{fill,radius,outline,outline-color,pad,head-pad}`, `--engine-strip-{tint,pad}`,
  `--engine-status-{done,warn,fail}` (hex, as `--engine-marking-*`); sty
  `\engine@boxes@columns@gap`, `…@rule`, `\engine@boxes@<box>@bar/@padx/@pady` (em) and
  `\definecolor{EngineBoxes<Box><Key>}` / `EngineStatus{Done,Warn,Fail}` (hex, as
  `EngineMarkingText`).
- The caution box, feature panel and pptx gap read them: `slide_layout.py` (`CAUTION_W`, the pt
  pads → `BOXES` × `type_pt(LIVERY, "body")` for em, × slide height for fractions, `int()`),
  scss, inner/outer sty, `livery_template.py:356`.
- Livery examples: ncar `card.radius: 0.012` (slide B's rounded boxes), `status: {warn: accent,
  fail: <the dark orange alert-text uses>}` (ncar's `warning` yellow is unreadable as text on
  white — check `livery check`'s contrast warnings; a status-color contrast warning in
  `livery_check.py` is a follow-up, not now); nasa-jsc-eg `columns.rule: 0.0022`, `card: {fill:
  surface, outline-color: eg-green}`, `strip.tint: 0.3` (tints need more share on black),
  `status: {done: eg-green, warn: warning, fail: accent}`.
- Schema (`boxes` object, `additionalProperties: false`, `$defs/color-or-role` for the colors,
  `type.display`), `livery schema --doc` → REFERENCE.md, every `liveries/*/build/` rebuilt,
  `tests/test_schema.py::test_sets_are_the_engines` + `set(P["boxes"]["properties"]) ==
  set(lb.BOXES)`; new `tests/test_boxes.py` (per-`livery`: every key present, fractions in
  [0, 1], pads two positive numbers, colors `#RRGGBB`; tmp liveries: a role, a palette name and a
  hex resolve, an unknown key fails with its path, as `test_marking.test_box`).
- ~250 lines. `make test`; parity: the pptx caution/feature slides and the PDF caution bar move
  as listed; HTML unchanged.

#### 2. Column widths, the gap, and `{.wide}`

pandoc's pptx writes two `sz="half"` placeholders and drops `width=` (`livery_template.py:
350-361`); HTML has no engine `.columns` rule (Quarto's 0.25/0.5rem side margins are the only
gutter); beamer `\begin{columns}[T]` without `onlytextwidth` spreads columns into the margins.

- **Lua.** `columns-pptx.lua` becomes `grid-pptx.lua` (every caller: `_extension.yml`,
  `tests/test_columns_pptx.py` → `test_grid_pptx.py`, CLAUDE.md, docs/formats.md), order in
  `_extension.yml`: after `slide-layout`, before `notes-last` (its notes Div then rides to the
  slide's end). It keeps the `FORMAT == "pptx"` guard and no `quarto.*` so plain pandoc runs it
  in tests. For a *plain columns slide* (two columns, no card, no lead — `is_grid()` false,
  commit 3) it appends a `notes` Div `engine-columns: 0.55 0.45` after the columns div (after,
  so the body still starts with the div; the shares from `column_shares()` in
  `engine-common.lua`: missing widths take equal shares of what is left, in every format).
  **Never put a marker paragraph in a plain columns slide**: a probe showed a marker beside a
  picture or table demotes the slide to a Comparison-style layout. The 3+ column warning stays
  for now (commit 3 replaces it).
- **`{.wide}` (Ben's ask):** a per-slide class on the `##` header that widens the body to the
  slide less `geometry.wide-margin` (new key, default `margin / 2`), in every format, so N
  columns can take the room deliberately. It rides the existing class channel
  (`slide-layout.lua` `CLASSES`/`take_layout` `:15-48` write `wide` on the `engine-layout:` line;
  `engine-common.lua`'s class list and both format filters' `LAYOUT_CLASSES`). HTML:
  `.engine-wide > .engine-body` gets the slide's padding at `--engine-wide-margin`; PDF: the Lua
  wraps the body in `\begin{enginewide}…` (inner theme: a minipage `\paperwidth − 2·wide-margin`
  wide, `\hspace*` left by `margin − wide-margin`; `boxable()` stays false for columns — the wide
  box holds the columns); pptx: `lay_out()` re-frames the body placeholder(s) (all four fields)
  to the wide content box, and the column frames use the same box. `deck_qa.py`'s overflow edge
  is `1 − margin` (`liveries/ncar/livery.yml:43`): read the slide's class and use `1 −
  wide-margin` on a wide slide, or qa flags every wide slide.
- **pptx `columns.py`** (new step, `run(prs, name)`; `pptx_post.py` order: after
  `slide_layout.run`, before `style_tables.run` — style_tables re-splits a table's columns inside
  its final frame; both before `type_step`): on a "Two Content" slide, `m = margin` (or
  `wide-margin`), `g = BOXES["columns"]["gap"]`, shares from the notes line (`_take_marker` in
  `slide_layout.py:71-88` becomes `take_marker(slide, key)`, one line, so each step reads its own
  key): `w_i = (1−2m−g)·s_i`, `x_1 = m`, `x_2 = m+w_1+g`; set all four fields of placeholders idx
  1 and 2 (top/height the inherited ones, from `_inherited`'s layout lookup). A `p:pic` or
  `graphicFrame` whose `left` equals the template's half frame (±1 EMU; `half = (1−2m−0.03)/2`)
  moves to `x_i`; one as wide as the old frame scales to `w_i` (a picture keeps its aspect).
  ncar: 55/45 → 4,274,820 / 3,497,580 EMU; three equal → 2,499,360 each at x 548,640 /
  3,322,320 / 6,096,000. `geometry.body-bottom` lifts `livery_template.py:352`'s `1 − 0.0778`
  into the json while here.
- **HTML scss:** `.columns { display: flex; gap: var(--engine-column-gap); align-items:
  stretch }`, `.column { min-width: 0; flex: 1 1 auto; position: relative }` (Quarto's inline
  width is the basis), `.column > :not(ul, ol) { margin-left: 0; margin-right: 0 }` (the gap
  replaces Quarto's 0.25/0.5rem).
- **PDF:** `engine-beamer.lua` replaces the `.columns` Div by raw `\begin{columns}
  [T,onlytextwidth]` and `\begin{column}{\enginecolwidth{0.55}{2}}` (`\dimexpr share ·
  (\textwidth − (n−1)·gap·\paperwidth)`), the content kept as AST blocks between the raw
  blocks. **Verify once** with `pdftotext -layout` x-positions that beamer spreads the leftover
  width between columns under `onlytextwidth` (the manual says `\hfill`s); if it centers the
  group, emit an explicit `\hfill` between columns.
- Tests: `test_grid_pptx.py` (plain pandoc + `--lua-filter grid-pptx.lua`, read the slide XML
  and the notes): a 55/45 slide keeps `idx="1"`/`idx="2"` and its notes carry `engine-columns:
  0.55 0.45`; a `wide` case on the layout line. New `tests/test_grid.py` (test_marking.py's
  shape: pandoc with the filter, then the steps in a subprocess under `LIVERY_DIR`, ncar and
  nasa-jsc-eg): 55/45 frames equal the formula within 1 EMU; a picture at the old half frame
  moved and scaled; on a wide slide the content box starts at `wide-margin`; every
  `a:off`/`a:ext`/`sz` matches `^\d+$`. `deck_qa.py`'s `COLS_EDGE` tightens to `EDGE` (it
  assumed beamer's overhang).
- ~370 lines. `make test`, `make -C decks/sample qa`; parity: every two-column HTML and PDF slide
  moves (the gap, no overhang), the pptx 55/45 frames change — intended.

#### 3. Three or more columns in pptx (the grid tier)

pandoc keeps the first two `.column`s and drops the rest (`test_pandoc_still_drops_the_third`
pins it; when that test fails, pandoc fixed it and the fold can go).

- `is_grid(columns_div)` in `engine-common.lua`: a slide is a *grid slide* when a column has
  `.card`, or the slide has a `.lead`, or there are more than two columns. A probe showed a lead
  before `.columns` already makes pandoc flatten the body into ONE Title-and-Content placeholder
  (the body no longer starts with the columns div), divs flattened, so the grid tier flattens on
  purpose and the post-step redraws from markers.
- `grid-pptx.lua`, grid slide: replace the `.columns` Div (and any `.lead`) by a flat text flow
  with marker paragraphs (a `Para` of one `Str`; `⟦ ⟧` never occur in prose; the post-step
  deletes them; a leftover `⟦` is visible in PowerPoint — the test forbids it):
  `⟦engine:columns widths=0.333,0.333,0.333⟧`, `⟦engine:column⟧` (plain) /
  `⟦engine:column card pick role=primary⟧` / `… card solid role=secondary`, `⟦engine:end⟧` (closes
  a column; the last closes the columns), `⟦engine:lead⟧ … ⟦engine:end⟧`, `⟦engine:strip
  role=accent⟧ … ⟦engine:end⟧`, and prefix markers on a paragraph's first Str: `⟦engine:title⟧`
  (the card's `###`, so pandoc writes no `spcBef 3000` heading), `⟦engine:sub⟧`, `⟦engine:label⟧`,
  `⟦engine:big⟧`. **First-cut limit, stated loudly:** a picture, table or code block inside a
  flattened column → `grid-pptx.lua: WARNING: slide "X": a picture/table in a card or a 3+
  column slide is not drawn in pptx; left in the flow` — it stays, pandoc splits the slide
  visibly, `make qa`'s slide count fails. Text after a picture in a column is silently dropped
  by pandoc today anyway (probe) — a CLAUDE.md line.
- `grid.py` (new step, after `columns.py`): parse the body placeholder's `a:p` elements into
  segments `Text | Lead | Columns(shares, [Column(kind, role, pick, solid, [Text | Strip])]) |
  Text`; lay the stack top-down from the placeholder's inherited frame (`frametitle.body` top to
  `geometry.body-bottom`). Primitives from `slide_layout`: `_rect` (fills, bars, the pick
  outline as `line` on the card rect), `_text_height` (works on any shape: `_inherited` falls
  back to the master's body size), `K`. One new helper `_body_box(slide, box, pad)`:
  `add_textbox`, insets from `pad` (em × `type_pt(LIVERY, "body")`), `word_wrap`,
  `<a:normAutofit/>` by hand (`enable_autofit` ran before), and its `a:lstStyle` replaced by a
  deep copy of the master `p:bodyStyle`'s `lvlNpPr` children, so pandoc's list paragraphs
  (`lvl="0"`, no `buNone`) keep the template's bullets and sizes — the one way a free text box
  renders like a body placeholder without a duplicate `p:ph idx`. The parsed `a:p` elements are
  *moved* into these boxes (pandoc's `pPr` kept), prefix markers stripped from the first run,
  marker paragraphs dropped, the emptied placeholder removed from `spTree` (unless `Text`
  segments remain: it keeps them, cut to their measured height, as `caution_box` cuts). This
  commit: `Text` and plain `Columns` only (cards in 6, lead in 5, strip in 7). Column frames as
  commit 2's formula for n. Shapes named `Column 2`, `Column 3` for tests. A grid slide ignores
  the body-layout classes (`.caution`, `.vcenter`; `scale=` still applies, it runs first) — say
  so in docs.
- Tests: `test_grid_pptx.py`: three columns → `AAA BBB CCC` and `⟦engine:columns widths=` in
  one placeholder; `test_grid.py`: three shapes with the formula's frames, no `⟦` in any
  `a:t`, the placeholder gone. CLAUDE.md "Two columns at most" rewritten; `_extension.yml`'s
  comment.
- ~300 lines. `make test`, sample qa (a three-column slide lands in commit 9's deck work, but
  add the fixture slide here if qa needs it).

#### 4. A rule between columns — `boxes.columns.rule`

A livery knob (#124's wording), drawn when its width is > 0: pptx `columns.py` and `grid.py`
draw `_rect(... blend("rule") ..., name="Column rule")` centered in each gap, the content
area's height; HTML `.columns > .column + .column::before` (absolute, `left: calc(-0.5 *
var(--engine-column-gap))`, `translateX(-50%)`, `width: var(--engine-column-rule)`, `background:
var(--engine-rule)`); PDF `\engine@colrule{x}` nodes in the frame's background TikZ picture
(`beamerouterthemeEngine.sty`, `current page` coordinates, from `frametitle.body` to the
footline), triggered by a `\gdef` the filter emits for the slide. nasa-jsc-eg sets `0.0022`.
Tests: `test_grid.py` counts "Column rule" under nasa-jsc-eg, none under ncar. ~60 lines;
parity under `PARITY_LIVERIES="ncar cu nsi nasa-jsc-eg"`.

#### 5. The lead box — `::: {.lead}`

- Authoring: `::: {.lead}` before the columns (or alone); **in `.lead` and `.card`, a source
  line is a line**: `split_lines()` in `engine-common.lua` splits a Para at `SoftBreak`/
  `LineBreak` into Paras, so the "bold headline / plain line" stack needs no blank lines; lists
  untouched.
- pptx: `⟦engine:lead⟧ … ⟦engine:end⟧`; `grid.py` `Lead`: `_rect` fill (`lead.fill`), `_rect`
  bar (`lead.bar·H` wide, `bar-color`), a `_body_box` over them with `lead.pad`; height =
  `_text_height · 1.1`.
- HTML: raw `<div class="engine-lead">` (raw tags, as the feature does: a Div whose first block
  is a heading becomes a `<section>`); scss `.engine-lead { background: var(--engine-lead-fill);
  border-left: var(--engine-lead-bar) solid var(--engine-lead-bar-color); padding:
  var(--engine-lead-pad); margin-bottom: 0.6em }`.
- PDF: generalize `enginecaution`'s shape into `\engine@barbox{fill}{bar color}{bar
  width}{padx}{pady}` (a `\vbox` with explicit pads inside a `\colorbox` with `\fboxsep=0`, the
  `\vrule` bar beside it); `enginecaution`, `enginelead` (and `enginestrip` in 7) are two-line
  definitions on it, fed by `\engine@boxes@*`.
- Tests: `test_grid.py` `Lead` and its bar present, fill = the livery's hex; `test_grid_pptx.py`
  the markers. ~150 lines.

#### 6. Cards — `::: {.column .card role=… .pick .solid}` with `###`, `.sub`, `.label`, `.big`

Authoring (final):

```markdown
:::: {.columns}
::: {.column .card .pick role="primary"}
### OPTION 1
[Procure a modern GPU system]{.sub}

**Total Cost = $30M**
[LOCAL INVESTMENT]{.label}
[$20M]{.big}

::: {.strip role="accent"}
→ **$15M** to consortium system
:::

[SCIENCE ENABLED]{.label}

- [x] GDEX expansion
- [!] High-resolution model runs
- [-] Interactive analysis at scale
:::
::: {.column .card role="primary-contrast"} … :::
::: {.column .card role="secondary"} … :::
::::
```

Slide B: `::: {.column .card .solid role="primary"}` with `### Option A` and body; the whole card
is the role's fill, text `primary-text`.

Rules (enforced once in `engine-common.lua` — `card_attrs()` — so the three filters agree):
`.card` on a `.column`; `role=<livery role>` names the band's fill (with `.solid`, the card's);
text on a role fill is `primary-text`; `.pick` draws the outline; the `###` is the band's title
(pandoc's beamer writer would otherwise make it a `block`, revealjs a bare `<h3>`); a paragraph
that is one `[…]{.sub}` span right after it is the band's second line (explicit — the AST cannot
tell "the next line" from any paragraph); `[…]{.label}` (eyebrow size, caps, muted) and
`[…]{.big}` (the `display` role, bold, `primary-contrast`; on a solid card `primary-text`) stand
alone in their line. `role` is ARIA's attribute in HTML: every raw div the filter emits drops
it and carries the role as a custom property.

- pptx `grid.py` `Column(card)`: the card rect (`card.fill`; `MSO_SHAPE.ROUNDED_RECTANGLE` with
  `adjustments[0] = radius·H / min(w, h)` when `radius > 0`, else `RECTANGLE`; `.pick`:
  `line.color` = `outline-color`, `line.width = int(outline·H)`; `.solid`: fill = the role); the
  head band: with radius 0 a rect inside the card; with a radius a second rounded rect whose
  bottom corners sit under the body rect (as PowerPoint users build it); head text box: the
  title run `Pt(type_pt("subhead"))` bold `primary-text`, the sub run body size regular; body
  `_body_box`es and strips stacked; label paragraphs `Pt(type_pt("eyebrow"))`, `cap="all"`,
  `spc="400"`, muted; big `Pt(type_pt("display"))` bold `primary-contrast`. Heights: each card =
  head + Σ segments + pads, the row's cards all take the max (equalized), capped at the body
  bottom; text boxes top-anchored. Shapes `Card 1`, `Card 1 head`, `Card 1 body`.
- HTML `engine-revealjs.lua` (in `Pandoc`, before `wrap_layout`): `.column.card` keeps its Div
  (Quarto's `style="width:…"`) but its content becomes raw `<div class="engine-card [engine-pick]
  [engine-solid]" style="--engine-card-role: var(--engine-primary)">` + `<div
  class="engine-card-head"><div class="engine-card-title">…</div><div class="engine-card-sub">…
  </div></div>` (inlines through `pandoc.write(…, "html")`) + `<div class="engine-card-body">` +
  blocks + closers — the Div's first block is a RawBlock, not a Header, so reveal counts no
  section. `.label/.big/.sub` spans → `engine-label/big/sub` (display block). scss: `.engine-card
  { display: flex; flex-direction: column; height: 100%; background: var(--engine-card-fill);
  border-radius: var(--engine-card-radius); overflow: hidden }`, `.engine-pick { box-shadow:
  inset 0 0 0 var(--engine-card-outline) var(--engine-card-outline-color) }` (inset: no layout
  shift, follows the radius), `.engine-card-head { background: var(--engine-card-role); color:
  var(--engine-primary-text); padding: var(--engine-card-head-pad) }`, `.engine-card-title {
  font-weight: 700; font-size: calc(var(--engine-type-subhead) * 1em) }`, `.engine-card-body {
  flex: 1; padding: var(--engine-card-pad) }`, `.engine-solid { background:
  var(--engine-card-role); &, p, li, strong { color: var(--engine-primary-text) }
  .engine-card-head { background: none } }`, `.engine-label`, `.engine-big` (the `display` size,
  `line-height: 1.08`). Equal heights: flex `align-items: stretch` (commit 2) + `height: 100%`.
- PDF: **tcolorbox** for the card (title band, pads, rounded corners with the band clipped to
  them, outline, a fixed `height=`, text color — all options; hand TikZ would need the band
  clipped to the corner by hand). Quarto already loads tcolorbox for callouts; the standalone
  `latex/` path gets `\RequirePackage{tcolorbox}\tcbuselibrary{skins}` in
  `beamerinnerthemeEngine.sty` — check `kpsewhich tcolorbox.sty` in the image first. **Not**
  tcolorbox's `equal height group` (aux-based, two runs): heights equalize in one run by the
  feature panel's own pattern (`\global\setbox…=\vbox\bgroup … \egroup`,
  `beamerinnerthemeEngine.sty:224-238`, which accepts verbatim): `\begin{enginecards}` …
  `\begin{enginecard}[pick,solid]{BrandPrimary}{0.333}{OPTION 1}{sub}` sets its body into
  `\engine@cardbox<n>` at `\hsize = share·(\textwidth − (n−1)·gap·\paperwidth) − 2·padx`
  (`\textwidth`/`\linewidth`/`\columnwidth` set, as the panel does); `\end{enginecards}` takes
  the max height and sets the row as an `\hbox` of `\begin{tcolorbox}[enhanced, nobeforeafter,
  box align=top, width=w_i, height=max + head + pads, arc=\engine@boxes@card@radius\paperheight,
  boxrule=0pt, colback=EngineBoxesCardFill, colbacktitle=<role>, coltitle=BrandPrimaryText,
  fonttitle=\usebeamerfont{block title}, title={…\\ {\usebeamerfont{normal text}sub}},
  left/right/top/bottom=pads]\box\engine@cardbox<i>\end{tcolorbox}` separated by
  `\hskip\engine@boxes@columns@gap\paperwidth`; `pick` adds `boxrule=…outline…\paperheight,
  colframe=EngineBoxesCardOutline`; `solid` sets `colback=<role>, coltext=BrandPrimaryText`. A
  too-tall row overflows the frame like any overflow (deck_qa reports it). `engine-beamer.lua`:
  the `###` becomes the environment's title argument (no `\begin{block}`), `.sub` its last
  argument, `.label` → `{\usebeamerfont{eyebrow}\color{BrandMuted}\MakeUppercase{…}}`, `.big` →
  `{\usebeamerfont{display}\color{BrandPrimaryContrast}…}`; a table or code block inside a card:
  warn (`engine-beamer: slide "X": a table in a card is drawn as a plain column`) and emit the
  column without the card environment (longtable cannot sit in a box; `boxable()`
  `engine-beamer.lua:192`); add `enginecards` RawBlocks to `boxable()`'s refusals.
- Docs: `docs/authoring.md` "Cards and lead boxes"; the sample's slides A and B (commit 9 may
  hold the deck work, but the card slide is this commit's proof: add it here).
- Tests: `test_grid.py` three `Card n` with the formula's frames and equal heights, the pick's
  `line` color = `outline-color`, under `type-body: 10` the big run is `half_pt(display·10/12)`
  (type_step runs after); `test_grid_pptx.py` the `###` is `⟦engine:title⟧…`.
- ~450 lines — the big one. `tests/app-open.sh` is **Ben's** after it (rounded rects, text boxes
  with a copied `lstStyle`: new XML for Keynote and PowerPoint).

#### 7. The strip — `::: {.strip role=…}` inside a card (or alone)

`⟦engine:strip role=accent⟧ … ⟦engine:end⟧`; pptx `_rect` with `livery_mod.mix(role,
background, strip.tint)` at the card's full width, a `_body_box` with `strip.pad`; `.solid`
the role and `primary-text`. HTML raw `<div class="engine-strip" style="--engine-strip-role:
var(--engine-accent)">`, scss `margin: 0.4em calc(-1 * <card pad x>)`, `padding:
var(--engine-strip-pad)`, `background: color-mix(in srgb, var(--engine-strip-role)
var(--engine-strip-tint), var(--engine-background))` (`emit_css_dark`'s precedent). PDF
`\begin{enginestrip}{Brand<Role>}` on `\engine@barbox` with no bar, `\colorlet{engine@strip}
{Brand<Role>!<tint %>!BrandBackground}`. Tests: `Strip` fill = `livery_mod.mix(...)`. ~80 lines.

#### 8. Status glyphs — `- [x]` ✓, `- [!]` ⚠, `- [-]` ✗

Inside a `.card` or a `::: {.status}` list wrapper (outside them, task lists stay Quarto's
checkboxes; `- [ ]` is always Quarto's unchecked box — an unchecked task is not a failure); a
literal `✓ ⚠ ✗` first in an item works anywhere. pandoc gives `[x]` as `Str "☒"`, `[ ]` as
`"☐"`, `[!]` and `[-]` as literal text; `status_item()` in `engine-common.lua` normalizes once to
`✓ `/`⚠ `/`✗ ` text so every drawer sees one thing. pptx `status_glyphs.py` (after `grid.py`;
every text frame on every slide): a paragraph whose first run starts with a glyph → split the
run (`copy.deepcopy` the `a:r`, two `a:t`s), the glyph run colored `status.done/warn/fail` and
bold, ✗'s remaining runs muted, `pPr` given `buNone`, `marL=0`, `indent=0` so the glyph stands
where the bullet was; idempotent. HTML: `Plain[Span(.engine-status-done)[✓], …]` (`U+FE0E` after
⚠ keeps browsers off the emoji), ✗ items wrap the rest in `Span(.engine-status-text)`; scss
`li:has(> .engine-status-*) { list-style: none; &::before { content: none } }`, the glyph bold in
its color, `.engine-status-fail ~ .engine-status-text { color: var(--engine-muted) }` (`:has()`
needs Chromium ≥ 105: fine). PDF: `engine_livery.sty:186-190` gains `\newunicodechar` lines for
`^^^^2713` and `^^^^2717` beside `^^^^26a0` (DejaVu Sans has all three); a list whose items are
all status items becomes raw `\begin{itemize}\item[{\textcolor{EngineStatusDone}{\bfseries
✓}}] …` through `inlines_to_latex` (pandoc's own `\item[$\boxtimes$]` idiom), ✗'s text in
`\textcolor{BrandMuted}`; a mixed list keeps its bullets with the colored glyph inline. On a Mac
PowerPoint may draw ⚠ as an emoji — if `app-open.sh` shows it, setting the glyph run's `a:latin`
to the livery's face is a follow-up. Tests: `status_glyphs.py` three items → first run text,
the livery's hex, `buNone`, ✗'s second run muted; run twice, unchanged. ~150 lines.

#### 9. Decks and docs for Part A

`decks/sample/sample.qmd` (the cookbook): slide A (lead, three cards, strip, glyphs, a pick),
slide B (solid cards), three plain columns, a 2/3–1/3 split with a picture, a `{.wide}` three-
column slide, the rule shows under nasa-jsc-eg; `make -C decks/sample qa` in all three formats;
a Playwright shot of the new HTML slides at 16:9 and `?print-pdf`. `decks/quickstart/
quickstart.qmd`: one three-card slide; `screenshots.py` `SLIDES` gains it; `make screenshots`
there, look at them, commit the PNGs; `make gallery` rebuilds `liveries.png` (four columns, as
before). `docs/authoring.md` ("Cards and lead boxes", "Columns": widths in pptx, 3+ columns and
the first-cut limit, `{.wide}`, the rule); `docs/formats.md` (the three new steps, `boxes`);
`liveries/README.md` (`boxes`, `geometry.wide-margin`, `body-bottom`); CLAUDE.md (the Build
bullet's step list and order, a "Cards and columns" bullet with the marker protocol and the
first-cut limits, "Two columns at most" rewritten, "Short slides" gains `.wide`); REFERENCE.md
regenerated; CHANGELOG. `tests/test_docs.py` gates the pointers.

### Part B — the rest of #124, #125, and the livery

#### 10. Bullet glyphs per level — `bullets:`

Today: pptx `livery_template.py:179` fixes `• § o – »` (Wingdings § = small square) per level in
the master; HTML draws shapes (`engine-revealjs.scss:217-244`: dot, ring, bar via `li::before`,
color `--engine-primary-contrast`); PDF draws TikZ shapes (`beamerinnerthemeEngine.sty:172-177`).
Knob: top-level `bullets:` (not under `type:` — `type_scale()` rejects unknown keys and the
schema is closed): `glyphs: [▪, –, •]` (per level, the last repeating) and `color: <role>`
(default `primary-contrast`). Absent: every format keeps today's look (decided). Set: the pptx
writes `<a:buFont typeface="<pptx.typeface>"/>` + `<a:buChar char=…/>` + `<a:buClr>` per level
(docs: the glyphs must exist in the pptx typeface); HTML switches `li::before` to `content:
"<glyph>"` in the role's color; PDF `\setbeamertemplate{itemize item}{\color{…}<glyph>}` per
level (the DejaVu borrow for symbols Poppins lacks: `engine_livery.sty:186-190`). `livery.json`
`bullets` (null when unset); nasa-jsc-eg `[▪, –, •]`, white. Tests: schema/REFERENCE; the json
holds the glyphs (absent → null); the template's master XML holds the `buChar`s (`livery
template` into `tmp_path`, unzip, as `test_type.py` reads a template). ~100 lines.

#### 11. Marks per composition — `compositions.<name>.mark|signoff.image`

Today `marks:` is keyed by field role (`livery_build.marks():313-345`); three readers redo the
role → file lookup: `emit_sty_compositions:847-852` (with the `-print` sibling),
`emit_css_compositions:1172-1176`, `livery.mark()` for the template (`livery_template.py:330-343`,
media named `mark-<role>`; `path_of():410-416` splits on `-`) and `slide_layout.title_cover()`
`:536-543`; `engine-revealjs.lua:520-529` copies only `marks` images as HTML resources. **Bug
on the way:** `light()` (`:448-456`) resets every mark's role to `background`, so nasa-jsc-eg's
`title-light`/`closing-light` put `eg-footer` (26:1) into the group-patch box.
Design: `mark`/`signoff` accept `image: <logo.images name>` (schema `:1214-1240` is closed
today); `compositions()` resolves every mark and signoff to `{role, box, img, img-print}` —
**file paths in the json** — through one resolver (`marks()` → `mark_files(name)` with the
`-print` sibling), by `image` when set, else the role's `marks` entry, else `primary`'s; the three
drawers read `img`/`img-print` from the composition and the role lookups go (the `marks` block
stays for the content-slide marks: `\engine@logo@light/dark`, css `:969-979`, the template
master `:216-222`). Template media named `mark-<comp>`/`signoff-<comp>` (dedup by path stays,
`:417-424`); `engine-revealjs.lua`'s resource list: every `img` under `compositions` plus
`marks`; `comp_measure.py` reads boxes only — unchanged. nasa-jsc-eg: `field: {role: dark}` on
title, closing and section; `signoff: {image: group-patch}` on `title`, `{image:
nasa-name-2line}` on `closing` and `section`; `marks:` loses its `surface` row; `make livery
LIVERY=nasa-jsc-eg`. Tests: `test_compositions.py` (`image:` reaches `img`; the light variant
keeps it; an unknown name fails with its path; `EXPECTED_DELTAS` unchanged). Parity: ncar/cu/nsi
unchanged; nasa-jsc-eg's light covers change (the bug) — name it. ~120 lines.

#### 12. A flavor unsets an inherited key — `null`

`merge()` (`livery_build.py:100-106`) already lets a child's `null` override (`merge(x, None)`
is `None`); only the schema refuses it: `art.titlegraphic` is `$ref path` (`minLength 1`,
`:264-267`, `:985`), `typography.monospace` `oneOf [string, {family}]` (`:1016-1024`); precedent
`section.label` `["string","null"]` (`:240`). Allow `null` per key (not on the shared `path`
def): `art.*` and `typography.monospace`. Every consumer already guards on `str` (sty
`:755-757`, css `:981-982`, `engine-revealjs.lua:530-531`, `:598`, `livery_template.py:86/326/346`,
`slide_layout.py:752-755`, `comp_measure.py:79`, `overleaf_zip.py:80-81`, `livery.py:137`;
`mono_font():609-623` handles `""`); check how Quarto's JSON decoder gives `null` in
`engine-revealjs.lua:513-514` (nil or a sentinel) and guard with `type(...) == "string"`. Trap:
`typography.fonts` is a list and inherits whole, so a nulled `monospace` leaves the mono files
in `livery.files()` — accept, say so in REFERENCE.md. nasa-jsc-eg: `art.titlegraphic: null`
(its cover is the `title` composition's art; a deck's own `titlegraphic:` gets `title-photo`,
kept full-bleed with `field: null`); drop the "cover art doubles as the photo" note. Tests: a
tmp flavor with `art: {titlegraphic: null}` builds, its json has `null`, `livery check` passes;
`test_schema.py:48` holds. ~40 lines + REFERENCE.md.

#### 13. `pptx.code-typeface`

`livery.py mono` (`:169-174`) → `Make.common:113` `LIVERY_MONO` → `-M monofont=` (`:213`):
pandoc writes `<a:latin typeface>` on every code run; the theme has no code slot;
`embed_fonts.py` embeds only `pptx.typeface`; `measure.py` measures Courier and other unbundled
faces at 0.6 em. Schema `pptx.code-typeface` (string); `livery.py mono` returns it when set,
else the bundled family (the pptx is `mono`'s only consumer; HTML's `--r-code-font` and the
sty's `\engine@monofont@*` read `typography.monospace` — unchanged). `liveries/README.md`,
REFERENCE.md. nasa-jsc-eg: `code-typeface: Courier New`; verify a pptx's code run names it
(`unzip -p … | grep -o 'typeface="Courier New"'`), HTML and PDF still Liberation Mono. Tests:
`test_cli.py` `livery mono` on a tmp flavor with and without the key. ~25 lines.

#### 14. `art.title-light`

`ART_KINDS` (`:54`) feeds `rebase()` and the sty loop (`:755-757`); `light()` sets `art=None` for
every light variant; seams: the template's art tuple (`livery_template.py:86`),
`engine-revealjs.lua:530`'s resource list, schema `art` (`:252-268`), `test_schema.py:48`.
**Trap:** the sty loop would emit `\def\engine@art@title-light` — strip the hyphen
(`titlelight`), as the composition emitter does (`:809`). `light(c, art=None)`: `title-light`
takes `art.title-light` when set (else none); `title-photo-light` stays art-less. Add an enum of
the kinds to the composition `art:` schema (any string passes today, then KeyErrors at sty
`:854` / template `:416`). nasa-jsc-eg: its template's "EG - Title Slide- Light" rendered by
`reference/eg_art.py` (extend `ART`) — **needs the reference deck on Ben's laptop**: the engine
commit lands with a tmp-livery test; the livery's light art is Ben's run after the PR. ~50
lines.

#### 15. #125: a full-slide field over a cover photo (beamer)

The model (schema: "the colored field behind everything"; `design/composition-handoff.md:
232-234`: field → art → photo): pptx (`pptx_waves.comp_shapes():78-85`: a rect only when
`field.box[2] < 1`) and HTML (`engine-revealjs.lua:482`, the same test) treat a full-width field
as the slide background under the photo; beamer `\engine@rectfield` (`beamerouterthemeEngine.sty:
262-266`) fills it over the photo (after `\engine@cphoto`, `:253-255`). All three draw a
*partial* field over the photo (ncar's 0.48–0.5 overlap). Fix beamer to the same rule: skip
the rect when the field's width is 1 (the frame's background is the field's role already); note
the shared blind spot (the test ignores height) in a comment, do not widen it. Tests:
`parity-latex.sh` (no page changes for ncar/cu/nsi: half-width fields); a tmp livery with
`title-photo: {field: {box: [0,0,1,1]}}` renders `decks/fixtures/photo.qmd` to PDF and the page's
center pixel is the photo, not the field color (`pdftoppm` + PIL, as `comp_measure.py` reads
pages). ~15 lines.

#### 16. `tests/app-open.sh`: a settled Keynote before the first deck; close documents on exit

`quit_app` (`:53-56`) pkills Keynote after the refused-notes control; the first deck's `tell
application "Keynote"` relaunches it and `open` → `count of slides` (`:86-99`) runs before it is
ready → "`every slide … doesn't understand count`". The `EXIT` trap (`:39`) deletes the tmp
copies but closes no documents, so an interrupted run leaves the control's "template" document
open on a deleted file; the next run's `docs_open` times out (5 s) and the guard (`:76`) and
`settle` (`:63`) read "no answer" as "nothing open" → the 60 + 90 s hang after "== Keynote"
(exit 144 = killed in that hang). Fix: a `ready_app` after any `quit_app` (`activate`, then poll
`count windows` until it answers) before the next `try`; the `EXIT` trap closes every open
document `saving no` in both apps (best effort, with a timeout) before `rm -rf`; a pre-flight at
the top of each app's section that quits an instance holding documents. Verification is
**Ben's** (two consecutive runs, the second after a deliberately interrupted one). ~30 lines;
no pytest.

#### 17. nasa-jsc-eg tidy-up and the Part B docs

The livery's uses of 10–13 landed in their commits (as #123 did). Here: `reference/notes.md`
"What the engine cannot do yet" rewritten to what remains (the light title art pending Ben's
render; pictures/tables in cards and 3+ columns), the `marks:` table and the cover paragraph;
`make livery LIVERY=nasa-jsc-eg`; `livery check --qa`; `make -C decks/quickstart measure
LIVERY=nasa-jsc-eg` (the known art-ink `OVER` rows, the same in all three formats; byline rows
`ok`). Docs: `liveries/README.md` (`bullets`, `image:`, `null`, `code-typeface`, `title-light`),
CLAUDE.md (Compositions: marks by image; Marks and numbers; the livery list), REFERENCE.md,
CHANGELOG (Liveries, LaTeX). `design/unplanned-city-ledger.md`: nothing (the sweep is later).

## Verification, end to end

1. Before the first commit, on `origin/main`: `tests/parity.sh baseline` (`PARITY_LIVERIES="ncar
   cu nsi nasa-jsc-eg"`) and `tests/parity-latex.sh baseline`.
2. Per commit: `make test`; the tests named with it; `make -C decks/sample qa` from commit 2 on;
   `parity.sh check` / `parity-latex.sh check` for 1, 2, 4, 6, 11, 15 — every difference named
   in the commit message as intended, or fixed.
3. After 17: `livery check --qa` on nasa-jsc-eg and ncar; `make all` in quickstart, sample,
   fixtures and plots under ncar and nasa-jsc-eg; the integer scan on each pptx:
   `unzip -p x.pptx 'ppt/slides/*.xml' | grep -oE '\b(x|y|cx|cy|w|h|sz|marL|indent|adj)="[0-9]+\.[0-9]+"'`
   → empty; `make -C decks/quickstart measure` under ncar (0 OVER) and nasa-jsc-eg (the known
   art rows only); no `⟦` in any slide XML.
4. **Ben's runs** (ask, do not assume): `tests/app-open.sh` on the Mac after commit 6 and at the
   end (a "Repair?" on a card slide is a FAIL); a look at the sample's card slides in PowerPoint
   (editability is the point); the EG light-title art render; `app-open.sh`'s own fix (16).
5. CI: every `Check livery`, the sample, consumer and reusable jobs, `livery build --check`.
6. PR body: a section per commit (what it adds, the parity departures, Ben's manual steps),
   the CHANGELOG section as its skeleton; "Closes" the ticked items of #124 and #125 (leave the
   issues open for what remains).

## Risks and traps (from the design pass)

- Marker paragraphs demote a slide holding a picture or table (probe): the grid tier is
  text-only and says so; the plain tier never carries markers.
- A `.lead` beside a table turns the slide into a grid slide and the table splits it: the doc
  says "a lead beside a table goes in the title or the notes".
- pads in pptx are insets, which `type_step` does not scale (it scales `sz`/`spcPts`): under
  `type-body:` the pptx pads stay while HTML/PDF em pads shrink — a stated, small delta.
- `ROUNDED_RECTANGLE` `adj` and `a:ln w=` must be ints; `normAutofit` in free text boxes is
  legal; Keynote is the judge (app-open).
- `?print-pdf` forces `padding: 0 !important` on `section` only (the cards' own padding is safe).
- beamer's leftover-width behavior under `onlytextwidth` is verified once (commit 2); tcolorbox
  inside the `\vbox\bgroup` pattern keeps verbatim working; longtable cannot sit in a box.
- ncar's `warning` yellow as ⚠ text is unreadable: its `boxes.status.warn: accent`; a contrast
  warning in `livery check` is a follow-up.
- `deck_qa.py`'s PDF column edge assumed beamer's overhang: tighten in commit 2.
