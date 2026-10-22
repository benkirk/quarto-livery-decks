# Sprint handoff: process steps and milestone timelines

**State (2026-10-22):** landed as #132, squash `cc79d84`. Departures: the marks default to `primary-contrast` with the number knocked out in the background color (Ben's pick after a side-by-side; the handoff's `primary` all but vanished on nasa-dark and cu); `rails()` runs first in the HTML and beamer chains, so a literal ✓ in a milestone is its status; the rail starts at the first mark's middle; a rail is drawn at the slide's top level only, enforced (`top_rails()`); the review's fix, badges numbered from the list's start (c55c2f5).

**For a fresh session.** The second of three sprints planned on 2026-10-22 after #129
(`citations-handoff.md` first, this, then `agenda-quote-handoff.md`). One PR against `main`
(branch `rail/steps-timelines` from `origin/main` once the citations PR is merged), a commit per
item in the order below, squash-merged once, no version bump (ask before any tag). Start by
reading `CLAUDE.md` whole ("The engine", "pandoc pptx gotchas" with "Columns: two tiers" and
"Cards and boxes", "revealjs (HTML) theme"), `design/latex-first-class-handoff.md` (the shape and
the house rules), `design/citations-handoff.md` "The goal, stated" (the three rules an element
meets), `docs/authoring.md` "Cards and lead boxes", and the cards machinery named under Context.
Then `source etc/config_env.sh`, branch, parity baselines (Verification, step 1), this file as
commit 0 at `design/steps-timelines-handoff.md`. Report at the end of each commit: what moved,
what the tests assert, what parity named.

House rules: roles only in theme files; every number from `livery.json`, one drawer per format;
**no compatibility shims**; `liveries/*/build/` generated; American spelling; a CHANGELOG line per
user-visible change; tests under `tmp_path`; the house commit message. Every name below is Ben's
pick (2026-10-22); do not rename one without asking. Line numbers are on #129's tip; re-grep.

## Context

Cards (#126, #127, #129) settled the pattern a boxed element follows, and nothing in it changes
for these two elements:

- **One reader in Lua.** `engine-common.lua` reads the element once (`card_attrs` :312-327,
  `split_lines` :275-294, `lone_span` :297-303, `box_role` :332-337, `status_item` :349-363) and
  each format's filter writes its own form: HTML raw `<div class="engine-*">` with the role as a
  custom property (`engine-revealjs.lua` `card_columns` :243-274, pipeline :634); pptx marker
  paragraphs in one flattened placeholder (`grid-pptx.lua` `flow` :83-102, `flatten` :104-125,
  `mark` :128-150); LaTeX the theme's environments (`engine-beamer.lua` `card_rows` :269-320,
  pipeline :764).
- **One set of numbers.** `livery_build.py` `BOXES` :102-112 and `BOX_COLORS` :113 are the source;
  `boxes()` :290-303 resolves colors; `emit_sty_boxes` :864-884 is generic (any key becomes
  `\engine@boxes@<box>@<key>`, a color `EngineBoxes<Box><Key>`, a pad `@pady`/`@padx`);
  `emit_css_boxes` :1103-1125 is hand-written per box; the schema node `livery.schema.json`
  :536-611 is hand-maintained and held to `BOXES` by `tests/test_schema.py` :51-56;
  `tests/test_boxes.py::test_every_key` :31-58 accepts a key only as a role list, a `BOX_COLORS`
  color, a `FRACTIONS` member (`gap rule bar outline radius tint`) or a `*pad`: a new fraction
  key extends `FRACTIONS`.
- **pptx draws from markers after pandoc.** `pptx_steps/grid.py`: `parse` :57-96 nests
  `columns > column`, `lead`, `strip`; `lay_out` :382-433 dispatches by segment kind; the helpers
  to reuse are `body_box` :99-133 (the master's lstStyle), `group` :136-146, `_shape` :200-222,
  `_style` :186-197, `_close` :225-235, `_card_height` :238, `_pick_role` :294-303; `common.py`
  `rect` :78, `column_frames` :110, `pads` :122; `measure.py` `text_height` :191. Driver order
  (`pptx_post.py` :56-66) needs no change: a rail is a grid segment.
- **beamer boxes the body first, then draws.** `enginecard` :510-550 sets each body in a save box
  at `\begin` (overlays work: beamer re-runs the frame per step), `\engine@drawcards` :552-556
  draws the row one height; `\engine@shares{<set>}{<spec>}` :425-446 reads `{n}` or weights;
  `\engine@rolecolor` :395 resolves `role=`. TikZ is loaded (inner :12, `calc` in the outer theme)
  and unused by any box today; the rail, the circle and the dot are TikZ primitives.
- Nothing draws a circle, a line with ticks or a chevron natively in any format. python-pptx has
  `MSO_SHAPE.OVAL`; a thin `rect` is the line every other step draws. `rule` is a blend (not a
  role) available by name through `\engine@role@rule`, `--engine-rule` and `livery.blends`.

**The look** (Ben, 2026-10-22, after the frontend-design skill's guidance): a sequence is a line
through points, so both elements are one **rail** family, not another row of filled cells beside
the cards. A thin rail (the `rule` blend by default) runs the row's width; **steps** put numbered
circle badges on it (the role's fill, the number in primary-text), each step's title (subhead,
bold, the text color; no all-caps eyebrow) and its text below; a **timeline** puts dots on it, the
date above the dot (subhead, bold) and the label below (body). No cell fill by default (a livery
may set one). The boldness is the badges in the role; everything else is quiet. Chevrons are
deferred: the SmartArt default. One drawer per format serves both (`kind = steps | timeline`).

Ben's decisions (2026-10-22, final): the rail look; **one PR for both elements**; **milestone
status in this sprint** (`- [x]` a filled dot, a plain item a hollow dot in the role, over
`status_item()` with `marked = true`; `[!]` and `[-]` warn and draw as plain); the sample deck
only (no quickstart slide: the README images stay). Not picks: steps are equal (no shares; the
shares machinery is there if a later ask wants weights), one `role=` per element (default
`primary`; not cycling, which would make a process look like options), milestones at equal
spacing with labels below, the cookbook twins off the contact sheet (`latex/sheet.py` unchanged).

## The interface, as agreed

```markdown
## A process, step by step

::: {.steps role="secondary"}
1. **Propose** A one-page case; the review board reads it in a week.
2. **Pilot** Six weeks on the shared system.
   A second source line is a second line, as in a card.
3. **Scale** The allocation follows the pilot's numbers.
:::

## A timeline

::: {.timeline}
- [x] **Q1 2025** Proposal accepted
- [x] **Q3 2025** Pilot complete
- **2026** Full allocation
:::
```

The first bold run of an item is its title (steps) or its date (timeline); the rest of the item
is the text, source lines as lines (`split_lines`). A `.steps` div holds one ordered list, a
`.timeline` one bullet list (`- [x]` a done milestone); anything else warns and is left alone.
First-cut limits: text only (a list inside a step is fine; no picture or table), at most **6**
items (the theme's save boxes), never inside a card or a column; a rail slide is a grid slide in
pptx (text after a picture splits, as cards).

```latex
\begin{enginesteps}[role=secondary]{3}            % {3}: three equal steps; role= as a card's
  \begin{enginestep}{Propose} A one-page case; the review board reads it in a week. \end{enginestep}
  \begin{enginestep}{Pilot} Six weeks. \par A second line. \uncover<2->{Overlays work.} \end{enginestep}
  \begin{enginestep}{Scale} The allocation follows the pilot's numbers. \end{enginestep}
\end{enginesteps}

\begin{enginetimeline}[role=primary]{3}
  \enginemilestone[done]{Q1 2025}{Proposal accepted}   % [done]: a filled dot; default hollow
  \enginemilestone[done]{Q3 2025}{Pilot complete}
  \enginemilestone{2026}{Full allocation}
\end{enginetimeline}
```

`livery.json` `boxes`, one new block (defaults in `BOXES`; every livery keeps its look with no
`livery.yml` change):

```python
"rail": {"line": 0.004, "line-color": "rule", "badge": 0.05, "dot": 0.02, "fill": None, "pad": [0.4, 0.4]},
# line, badge, dot: of the slide height (the rail's thickness, the badge's and the dot's diameter);
# fill: a cell fill behind each item, null for none; pad: em of the body, around each item's text
```

`BOX_COLORS` gains `"rail": ("line-color", "fill")` with `fill` nullable (`boxes()` :290-303
resolves a color or keeps `None`; `emit_css_boxes` writes `transparent`, `emit_sty_boxes` skips a
null); `tests/test_boxes.py` `FRACTIONS` gains `badge`, `line`, `dot`. The gap between items is
`boxes.columns.gap` (as cards); the badge number, a step's title and a milestone's date are
`subhead` bold; the text is the body: no new type role.

## The commits, in order

### 0. This handoff

### 1. Livery data

- `livery_build.py` `BOXES` and `BOX_COLORS` as above; `emit_css_boxes` adds `--engine-rail-line`
  (px of the height), `--engine-rail-line-color`, `--engine-rail-badge`, `--engine-rail-dot`,
  `--engine-rail-fill`, `--engine-rail-pad`. `emit_sty_boxes` needs nothing but the null skip.
- `livery.schema.json`: a `rail` node with the defaults (`fill` role-or-hex-or-null); `livery
  schema --doc` regenerates `liveries/REFERENCE.md`; `livery build liveries/*/`, committed.
- Tests: `test_boxes.py` `FRACTIONS` and a null-fill case in `test_colors_resolve`;
  `test_schema.py` holds automatically.
- Proof: `tests/parity.sh check` identical (nothing reads the keys yet). CHANGELOG Liveries:
  one line, nothing to do.

### 2. The reader and HTML

- `engine-common.lua`: `rail_items(div, kind, livery, who)` after `card_attrs` →
  `{ role, items = { {title = inlines, body = blocks, done = bool|nil}, ... } }` or nil with a
  warning (the wrong list kind, more than 6 items, a picture or table inside): the first `Strong`
  of the item's first paragraph is the title (or date), the following `Space` dropped, the
  remainder the first body line; `split_lines` on the body; for a timeline, `status_item(item,
  true)` reads `[x]` as done (`[!]`/`[-]` warn, plain). `is_grid` :260-270 scans `blocks` for
  `.steps` and `.timeline` as it does `.lead`, so a two-column div beside a rail flattens too.
- `engine-revealjs.lua`: `rails(blocks, livery)` beside `lead_boxes` :223-231:
  `<div class="engine-rail engine-steps|engine-timeline" style="--engine-rail-role: var(--engine-<role>)">`,
  per item `<div class="engine-rail-item[ engine-done]">` holding `<div class="engine-rail-badge">k</div>`
  (steps) or `<div class="engine-rail-dot"></div>` (timeline), `<div class="engine-rail-title">`
  (a step's title below the badge; a milestone's date above the dot), `<div class="engine-rail-body">`
  + body blocks; the role through `C.box_role`; into the chain at :634 before `lead_boxes`.
- `engine-revealjs.scss` after `.engine-strip`: `.engine-rail` a flex row, `gap:
  var(--engine-column-gap)`, `position: relative`, a `::before` rail (`height:
  var(--engine-rail-line)`, `background: var(--engine-rail-line-color)`, at the badge's
  vertical center for steps, the dot's for a timeline); `.engine-rail-item { flex: 1 1 0;
  background: var(--engine-rail-fill); padding: var(--engine-rail-pad) }`; `.engine-rail-badge`
  a `var(--engine-rail-badge)` square, `border-radius: 50%`, `background:
  var(--engine-rail-role)`, `color: var(--engine-primary-text)`, centered subhead bold;
  `.engine-rail-dot` a `var(--engine-rail-dot)` circle, filled in the role when `.engine-done`,
  else the background with a role border (hollow); `.engine-rail-title` subhead bold; first and
  last children's margins zeroed as the card's :440-441.
- `decks/sample/sample.qmd`: "A process, step by step" and "A timeline" after "Solid cards".
- Proof: `make -C decks/sample html` and screenshots (ncar, nasa-dark) looked at; `make qa`
  (the pptx and PDF come in 3 and 4; until then the count check names the two slides, expected).
  CHANGELOG Decks.

### 3. pptx

- `grid-pptx.lua` `mark()`: a `.steps`/`.timeline` div (like `.lead`) → `marker("rail
  kind=steps|timeline role=<role>")`, per item `marker("item")` or `marker("item done")`,
  `prefixed("title", title)` (`PREFIX` :39 already has `title`), `flow(body)`, `marker("end")`,
  a closing `marker("end")`; the docstring.
- `grid.py`: `parse` nests `rail > item` as `columns > column`; `lay_out` dispatches `rail` to
  `draw_rail(slide, left, y, width, room, kind, items, role, slide_height)` beside `draw_lead`:
  frames from `column_frames(left, width, [1/n]*n, slide_width)`; the rail a `rect` the row's
  width at `line * slide_height` in `line-color`; per item a badge `slide.shapes.add_shape(
  MSO_SHAPE.OVAL, ...)` of `badge * slide_height` filled in the role with its own text frame "k"
  (`_style` subhead bold `primary-text`, `algn="ctr"`, `anchor="ctr"`) for steps, or a dot of
  `dot * slide_height` (filled in the role when done, else the background with a role line) for a
  timeline; a `body_box` of the title and text (`_prefix`, `_style` subhead bold on the title,
  `_close` on every paragraph), margins `pads("rail")`; a cell `rect` in `fill` behind the text
  when `fill` is set; one height, the tallest measured (`_card_height`) times `SLACK`, capped at
  the room (as `draw_cards` :354); shapes named "Step k badge"/"Milestone k dot", "… title",
  "… text", grouped as "Steps"/"Timeline" (`group`). Inside `grid.py` (it reuses six private
  helpers; a separate module would import them back); if the file passes ~600 lines, a sweep lifts
  `body_box`/`group`/`_shape` to `common.py` (ledger).
- Tests: `test_grid_pptx.py::test_rail_marked` beside `test_card_marked` (the markers, `done`,
  the titles as `⟦engine:title⟧` paragraphs); `test_grid.py` `MD` gains both slides,
  `test_rail` on the `test_cards` pattern: the groups, the badge's `prstGeom` `ellipse`, fill the
  role, text "1", the cells at `boxes(livery, width, [1/3]*3)`, one height, the rail's height
  `round(line * slide_height)`, a done dot filled and a pending one with a line, the title run
  bold at `half_pt(subhead)`, no marker left.
- Proof: `make -C decks/sample pptx`; open it in PowerPoint and Keynote (`tests/app-open.sh` is
  the release's step, but the deck's first OVAL with its own text is here: do it once now).
  CHANGELOG Decks (the same line as 2, extended).

### 4. beamer

- `beamerinnerthemeEngine.sty` after the cards: `\pgfkeys{/engine/rail/.cd, role/.store
  in=\engine@railrole}`; `\newenvironment{enginesteps}[2][]` and `\newenvironment{enginetimeline}
  [2][]` → `\engine@shares{rail}{#2}`, the role by `\engine@rolecolor{..}{primary}`, counters
  zeroed, the kind recorded; `\newenvironment{enginestep}[1]` → the card's pattern: width = share
  × (`\linewidth` − `gap\paperwidth` × (n−1)), the body in `\global\setbox\engine@cardbox{k}=
  \vbox\bgroup` at `\hsize` = width − 2 padx (the six save boxes: a rail never sits in a card, and
  6 is the limit), the title stored, the tallest tracked; the error past n as :512-515.
  `\newcommand\enginemilestone[3][]` → the same with `#1` = `done` recorded, `#2` the date, `#3`
  the label (a one-line body). `\engine@drawrail` at `\end`: one `tikzpicture` the row's width:
  the rail `\draw[line width=\engine@boxes@rail@line\paperheight, color=\engine@role@rule]`
  across; per item a `\node[circle, fill=<role>, text=BrandPrimaryText, minimum size=badge
  \paperheight, inner sep=0] {k}` (steps) or a dot `\fill`/`\draw` of `dot\paperheight` (done
  filled, pending hollow); the title node (subhead bold) under the badge or the date node above
  the dot; the boxed body in a node under; an optional cell fill rectangle behind. h = badge +
  title's height + the tallest body + 2 pady + the strip's gap below.
- `engine-beamer.lua`: `rails(blocks, livery)` beside `strips` writing `\begin{enginesteps}
  [role=<name>]{n}` / `\begin{enginestep}{<title>}` + `card_body(body)` + `\end{enginestep}`,
  and `\begin{enginetimeline}[role=]{n}` / `\enginemilestone[done]{<date>}{<label>}`; into the
  chain at :764 before `card_rows`.
- `latex/examples/sample.tex`: the twins after "Steps inside cards" (one `\uncover<2->` line in
  a step: the overlay proof); `latex/authoring.md` "The patterns" rows and a short section
  "Steps and timelines" after "Cards, strips and status lists".
- Tests: `tests/test_latex.py` `DECK` gains an `enginesteps{3}` row and an `enginetimeline{3}`;
  `test_compiles_clean` covers them; a `test_too_many_steps` on the share-error pattern. CI's
  Overfull ratchet covers `sample.tex` and its variants.
- Proof: `pdftoppm -r 60` of the two frames under ncar, cu, nasa-dark, 4:3 (`make -C latex
  variants`); `tests/parity-latex.sh check`: the cookbook gains two pages, nothing else moves.
  CHANGELOG LaTeX.

### 5. Documentation

`docs/authoring.md`: a section "Steps and timelines" after "Cards and lead boxes" (the snippets,
the bold-title rule, `[x]`, the limits, the pptx group names, the LaTeX pointer); `CLAUDE.md`
"Cards and boxes" names `.steps`/`.timeline`, the markers, `rail_items`, `draw_rail`, the OVAL;
`tests/test_docs.py` resolves the new pointers. CHANGELOG: Decks (the two elements in three
formats, the limits), Liveries (`boxes.rail`, nothing to do), LaTeX (`enginesteps`/`enginestep`,
`enginetimeline`/`\enginemilestone`).

## Verification

1. Before the first commit, on `origin/main`: `tests/parity.sh baseline` (ncar cu nsi) and
   `tests/parity-latex.sh baseline`, same checkout, same day.
2. Every commit: `make test` (`livery build --check`, pytest with the new tests, the docs gate).
3. `tests/parity.sh check` after 1 (identical) and at the end: the sample's two new slides are
   the only extra pages in every format; `parity-latex check` after 4: the cookbook's two pages.
4. `make -C decks/sample all && make -C decks/sample qa`: counts agree, no overflow on the new
   slides at ncar and nasa-dark (`make qa LIVERY=nasa-dark`); the pages looked at.
5. PowerPoint and Keynote open `decks/sample/sample.pptx` (commit 3).
6. The PR body: a section per commit, the parity results, the screenshots; `/pr-review N`.

## Risks

- A long step text collapses the row in pptx (the row is capped at the room, autofit shrinks)
  and beamer (an overfull vertical box, caught by the ratchet in the cookbook only). The docs say
  two or three lines a step.
- Keynote and a shape with its own text frame (the badge): if Keynote balks, draw the number as a
  `body_box` over the oval (one line changes).
- Six save boxes bound n in beamer; the Lua reader enforces 6 in every format so the three agree.
- TikZ inside a frame's overlay pass: the body box is set at `\begin{enginestep}`, the picture at
  `\end{enginesteps}`; a `\pause` in a step body redraws the row per step, which the card pattern
  already survives (the cookbook's "Steps inside cards"); the cookbook twin has one `\uncover`.
- `is_grid` widening moves a two-column slide beside a rail from Two Content to a grid slide:
  intended, and the pptx picture-in-column limit then applies to it.

## Memory for the fresh session

`no-compat-shims.md`, `minimal-prs-versions.md`, `approval-text-in-chat.md`,
`american-spelling.md`, `sprint-tags-recut.md`, `latex-first-class.md`,
`design-framework-goal.md`, `next-sprints-after-129.md`. After the PR opens, update
`next-sprints-after-129.md`.
