# Sprint handoff: the quote block, the agenda, and section progress

**For a fresh session.** The third of three sprints planned on 2026-10-22 after #129
(`citations-handoff.md`, `steps-timelines-handoff.md`, then this). One PR against `main` (branch
`decks/agenda-quote` from `origin/main` once the steps PR is merged), a commit per item in the
order below, squash-merged once, no version bump (ask before any tag). Start by reading
`CLAUDE.md` whole ("Divider subtitles", "Compositions", "The engine", "pandoc pptx gotchas",
"revealjs (HTML) theme"), `design/latex-first-class-handoff.md` (the shape and the house rules),
`design/citations-handoff.md` "The goal, stated", `latex/authoring.md`, and the section machinery
named under Context. Then `source etc/config_env.sh`, branch, parity baselines (Verification,
step 1), this file as commit 0 at `design/agenda-quote-handoff.md`. Report at the end of each
commit: what moved, what the tests assert, what parity named.

House rules: roles only in theme files; every number from `livery.json`, one drawer per format;
**no compatibility shims**; `liveries/*/build/` generated; American spelling; a CHANGELOG line per
user-visible change; tests under `tmp_path`; the house commit message. Every name below is Ben's
pick (2026-10-22); do not rename one without asking. Line numbers are on #129's tip; re-grep.

**Two independent elements in one sprint, because each is small.** The quote is a general
slide-body block (Ben, 2026-10-22): `::: {.quote}` or a bare `> ` blockquote anywhere in a slide's
body, as a lead or a strip is, inside a column or a card too; nothing about it is the agenda's.
The quote comes first (commits 2-3), the agenda after (4), the progress mark last (6).

## Context

Decks have numbered section dividers in every format (eyebrow "SECTION n", title, subtitle) but
no slide that lists them, and no quotation block: pandoc's `> ` is beamer's unstyled `quote`,
reveal's muted left-border paragraph (`engine-revealjs.scss:299-308`, `:1023`), and in pptx an
indented paragraph at a smaller size. No deck uses one. `toc: false` everywhere
(`_extension.yml:72`, `common/_quarto.yml:21,26`), so pandoc's own TOC slide never appears, and
nothing uses beamer's `\tableofcontents` (templates at inner :191, colors :37-38, fonts :59-60).

Two defects found while reading, both fixed by commit 1:

- **pptx numbers every divider** (`pptx_steps/section_subtitle.py:267`, `len(dressed) + 1`);
  HTML (`engine-revealjs.lua:642-645`) and the beamer filter (`engine-beamer.lua:738`) skip
  `.unnumbered`. pandoc's pptx writer drops the class, so the step cannot know on its own.
- **beamer's `\section*` still steps the section counter** (`beamerbasesection.sty`,
  `\refstepcounter{section}` in both branches), and pandoc writes `.unnumbered` as `\section*{..}`.
  So an unnumbered divider after section 2 draws the eyebrow "SECTION 3" (`\engine@sectionstack`,
  inner :105-107), the next numbered one "SECTION 4" while HTML says 3, and the filter's
  `\enginesectionsubtitle{3}{..}` (keyed by its own count) lands on the wrong divider. Verify with
  the fixture in commit 1 before fixing; expected to reproduce.

The "paragraphs alone between a divider and the next slide" rule is written twice
(`engine-revealjs.lua:650-658`, `engine-beamer.lua:739-744`); the agenda needs it a third time
(pptx), so it moves to `engine-common.lua`. The section machinery: inner theme :94-131
(`\sectionsubtitle`, `\enginesectionsubtitle{n}{..}`, the section page, `\AtBeginSection[]`);
`section_subtitle.py` `run()` :234-310 and `_dress()` :180-231; `livery_build.py`
`compositions()` section entry :540-551 (column, eyebrow `{label, color}`); the schema's `section`
node :247-262; css `--engine-cmp-eyebrow*` :1303-1306, sty `eyebrow@label` :951-953. Type roles
(`TYPE` :80-85): body 16, subhead 20, sectionsubtitle 20, eyebrow 11, caption 11; no quote role.
The boxes pattern for a block: `BOXES` :102-112, `emit_sty_boxes` :864-884, `emit_css_boxes`
:1103-1125; the lead's drawers (`\engine@barbox` inner :304-323, `enginelead` :326-331; pptx
`draw_lead` grid.py:149-164; HTML `lead_boxes` engine-revealjs.lua:223-231, scss :410-418).

Ben's decisions (2026-10-22, final): the agenda highlights **by position**, no `current=`
override; the divider's **progress mark is in**, as the last separable commit, a livery knob
default off; the quote is **a bar in the role** on the lead's machinery with a new **`quote` type
role** (the glyph deferred); **a bare `> ` blockquote is the same box**, inside a column or card
as well; the LaTeX names as below.

## The interface, as agreed

```markdown
## A pull quote

::: {.quote role="accent"}
The best way to predict the weather is to compute it.
— L. F. Richardson, 1922
:::

> A bare blockquote on a slide is the same box, in the default role, without an attribution.

## Agenda {.agenda}                 <!-- empty body; the engine fills it. Again anywhere: that section is current -->

# Backup {.unnumbered}              <!-- no eyebrow, not in the agenda, in every format -->
```

The last line of a `.quote` that starts with `—`, `–` or `--` (pandoc's smart quotes turn `--`
into an en dash before the filter sees it) is the attribution; `role=` colors the bar (default
`secondary`); the text is set in the `quote` type role, the attribution at `caption`, muted, with
"— " before it. An `.agenda` slide's body must be empty (anything else warns and is dropped); it
lists the numbered sections in order (number, title, the divider's subtitle under it when it has
one); up front none is current (all upcoming); placed first in a section, that section is
current, the earlier ones muted as done, the later ones plain.

```latex
\begin{enginequote}[role=accent]{L. F. Richardson, 1922}   % {}: no attribution
  The best way to predict the weather is to compute it.
\end{enginequote}

\begin{frame}{Agenda}\engineagenda\end{frame}              % sections from \section; subtitles from \sectionsubtitle
\enginesectionunnumbered{Backup}{A subtitle}               % a divider outside the count; {} for no subtitle
\enginesectiontotal{5}                                     % preamble, with section.progress (commit 6)
```

`livery.json`: `boxes.quote {bar: 0.0089, bar-color: secondary, pad: [0.3, 1.0]}`
(`BOX_COLORS` `quote: (bar-color,)`); `type.quote` (24 pt on 960x540, leading 1.3, in
`BODY_ROLES` so it scales with the body); `compositions.section.eyebrow.progress` (bool, from
`section.progress`, default false).

## The commits, in order

### 0. This handoff

### 1. Sections are counted alike in every format

- `engine-common.lua` after `is_slide_break`: `divider_subtitle(blocks, i, level)` → the subtitle
  paragraphs and the index after them (the rule at `engine-revealjs.lua:650-658`), and
  `sections(blocks, level)` → `{ {number|nil, title (inlines), sub (Blocks|nil), unnumbered, at} }`
  in one pass, `.unnumbered` unnumbered. `engine-revealjs.lua:650-658` and
  `engine-beamer.lua:739-744` call `divider_subtitle`.
- `grid-pptx.lua` `Pandoc` (plain pandoc, testable): `doc.meta["engine-unnumbered"] =
  MetaString("2 4")` (1-based positions among the deck's dividers) from `C.sections`; pandoc
  writes it to `docProps/custom.xml` as it writes `engine-title: light` (`slide-layout.lua:9`).
- `pptx_steps/docprops.py` `props(part)` → `props_of(blob)` plus `props(part)` over it, so
  `section_subtitle.run` (on zip parts) reads `parts.get("docProps/custom.xml")`; :263-268 number
  only the numbered dividers; `_dress(root, layout_root, number)` with `number=None` appends no
  label and lays the block out without `label_h`.
- Inner theme :124-131: `\newcommand\enginesectionunnumbered[2]` draws the plain divider frame
  as `\AtBeginSection` does (the stack with the title `#1`, no eyebrow, the subtitle `#2`), with
  no `\section`: no counter step, no toc line, no bookmark (said in the guide).
  `engine-beamer.lua:736-758`: an unnumbered divider is `latex("\\enginesectionunnumbered{..}{..}")`.
- `decks/fixtures/_body.qmd` gains, before the closing: `# Backup {.unnumbered}`, a subtitle
  paragraph, one `## A backup slide`; the four fixture decks carry it.
- Tests: `tests/test_section_subtitle.py` (new, on `pandoc_deck`): md with front matter
  `engine-unnumbered: "2"` and three dividers → after `run`, slides 1 and 3 carry
  `engine-section-label` "SECTION 1"/"SECTION 2", slide 2 none. `tests/test_grid_pptx.py`: the
  meta line from `.unnumbered`. `tests/test_latex.py`'s deck gains `\enginesectionunnumbered`.
- Proof: `make -C decks/fixtures all`: the Backup divider without a number in pptx, HTML and PDF,
  the next numbers agreeing. `tests/parity.sh check`: the fixtures gain pages, nothing else
  moves. CHANGELOG Decks (pptx and PDF skip `.unnumbered` as HTML did) and LaTeX.

### 2. The quote's numbers: a box and a type role

- `livery_build.py` `BOXES += "quote"`, `BOX_COLORS += "quote": ("bar-color",)`; `TYPE +=
  "quote": (24, 1.3)`, `BODY_ROLES += "quote"`. `emit_sty_boxes` emits it unchanged
  (`\engine@boxes@quote@bar/@padx/@pady`, `EngineBoxesQuoteBarColor`); `emit_css_boxes` +=
  `--engine-quote-bar`, `--engine-quote-bar-color`, `--engine-quote-pad`; the type role by the
  existing loops (`\engine@type@quote`, `--engine-type-quote`, the pptx `type_pt`).
- `livery.schema.json`: `boxes.quote` beside `lead`; `type.quote` (`tests/test_schema.py` holds it
  to `TYPE`). `beamerfontthemeEngine.sty`: `\setbeamerfont{quote}{size=\engine@fs{quote}}`.
  `livery build liveries/*/` (every `build/`, `REFERENCE.md` regenerated), committed.
- Tests: `test_boxes.py::test_every_key` tables gain `quote`; `test_type.py` follows `TYPE`.
- Proof: parity identical (nothing reads the keys yet). CHANGELOG Liveries.

### 3. The quote block in three formats

- `engine-common.lua`: `quote_parts(div, livery, who)` → `{ role (C.box_role, default
  secondary), body (split_lines, the last line removed when it starts with —/–/--), attribution
  (inlines|nil) }`; a `BlockQuote` block is read the same way (no role attribute, so the default).
- pptx: `grid-pptx.lua` `flow()` and `mark()` add `.quote` and `BlockQuote` beside `.lead` and
  `.strip` (in a column or card too, as a strip): `⟦engine:quote role=..⟧`, the lines, an
  `⟦engine:attribution⟧`-prefixed last line (`PREFIX`), `⟦engine:end⟧`. `grid.py` `parse` learns
  `quote` as `lead`; `lay_out` → `draw_quote(slide, x, y, w, room, paras, role, slide_height)`
  beside `draw_lead`: a `body_box` padded by `pads("quote")`, each paragraph `_style`d at the
  quote pt, the attribution at `caption` pt in `muted`, a bar `rect` in the role at the left, no
  fill; group "Quote" of "Quote bar", "Quote text".
- HTML: `engine-revealjs.lua` `quote_boxes` beside `lead_boxes` (Div `.quote` and `BlockQuote`):
  `<div class="engine-quote" style="--engine-quote-role: var(--engine-<role>)">`, the lines,
  `<p class="engine-attribution">— ..</p>`; scss beside `.engine-lead`: `border-left:
  var(--engine-quote-bar) solid var(--engine-quote-role)`, `padding: var(--engine-quote-pad)`,
  `font-size: calc(var(--engine-type-quote) * 1em)`, the attribution `--engine-type-caption`,
  muted; the `.reveal blockquote` rules (:299-308, :1023) go (a blockquote is this box now).
- beamer: inner theme beside `enginelead`: `\pgfkeys{/engine/quote/.cd, role/.store in=..}`,
  `\newenvironment{enginequote}[2][]`: `\engine@rolecolor{..}{secondary}`,
  `\engine@barbox{quote}` with `\usebeamerfont{quote}`, at the end the attribution
  `{\usebeamerfont{caption}\color{BrandMuted}— #2\par}` when `#2` is not empty, then
  `\endengine@barbox{BrandBackground}{<role>}`. `engine-beamer.lua` `quote_boxes` beside
  `lead_boxes` (Div and BlockQuote); `opens_paragraph` matches it.
- Deck and docs: `decks/sample/sample.qmd` a `## A pull quote` slide after Math;
  `docs/authoring.md` a section "Quotes" after "Cards and lead boxes"; `latex/authoring.md` a
  row; `latex/examples/sample.tex` the frame after Math (the sheet's four pages untouched).
- Tests: `tests/test_grid.py::test_quote` on the `deck` fixture (add the slide to its md): the
  group, the bar's color and width, the text size, the attribution muted, no marker left; a quote
  inside a card; `test_grid_pptx.py`: the markers and the attribution split; `test_latex.py`: an
  `enginequote` frame.
- Proof: the slide in all three formats under ncar, cu, nasa-dark (the bar on the dark field);
  `make -C decks/sample qa`. Parity: the sample gains a page. CHANGELOG Decks, LaTeX.

### 4. The agenda

- HTML: `engine-revealjs.lua` Pandoc loop, a branch before the general case: a `##` with
  `.agenda` and an empty body → the heading, then raw `<ol class="engine-agenda">` with one
  `<li data-engine-state="done|current|next">` per numbered section of `C.sections`,
  `<span class="engine-agenda-number">n</span>`, `<span class="engine-agenda-title">`,
  `<span class="engine-agenda-sub">` (the state from the loop's `section` counter: `<` current
  done, `==` current, else next). scss after the lead block: a two-column row (the number in the
  eyebrow size, bold, in `--engine-agenda-number`; the title at `subhead`; the sub at `caption`,
  muted), done muted, current in `--engine-primary` bold. `emit_css` sets
  `--engine-agenda-number` from `compositions.section.eyebrow.color` (secondary when null).
- beamer: inner :191 replaced by `\defbeamertemplate*{section in toc}{Engine}` and `{section in
  toc shaded}{Engine}`: a row with `\inserttocsectionnumber` in the `eyebrow` font and the
  eyebrow color, `\inserttocsection` in `subhead`, and `\csname engine@secsub@
  \inserttocsectionnumber\endcsname` under it when defined; shaded: `\ifnum\inserttocsectionnumber
  <\thesection` muted (done) else the text color (next). `\newcommand\engineagenda{
  \tableofcontents[currentsection,hideallsubsections]}`. Color theme :37-38 and font theme
  :59-60 take the roles. `engine-beamer.lua`: a `.agenda` slide with an empty body gets
  `latex("\\engineagenda")`. Quarto's PDF build must re-run xelatex when the `.toc` changes:
  verify on the sample's first clean build; the fallback is the filter writing the list itself as
  `\engineagendaitem{n}{Title}` lines in header-includes and the theme drawing from them.
- pptx: `grid-pptx.lua` `mark()`: the `.agenda` heading (take the class off) with an empty body
  gets `⟦engine:agenda current=<n>⟧`, per section `⟦engine:item n=k state=..⟧`, a
  `⟦engine:title⟧`-prefixed title, `⟦engine:sub⟧`-prefixed sub lines, `⟦engine:end⟧`, a closing
  `⟦engine:end⟧` (so pandoc picks Title and Content, which `grid.py` `is_body` needs). `grid.py`
  `parse` learns `agenda`/`item`; `lay_out` → `draw_agenda(slide, x, y, w, room, items,
  slide_height)`: per row a number box (2 em wide, eyebrow pt bold, the eyebrow hex: lift
  `section_subtitle._eyebrow_hex` to `common.py`) and a text box (title at subhead pt, current
  bold in `primary`, done `muted`; sub at caption pt muted), rows stacked by `text_height`, the
  subs dropped when the stack exceeds the room; group "Agenda" of "Agenda k number"/"Agenda k text".
- Deck and docs: `sample.qmd` `## Agenda {.agenda}` after the front matter and `## Where we are
  {.agenda}` first under `# Wrap-up`; `docs/authoring.md` "Agenda"; `latex/authoring.md` rows;
  the cookbook an Agenda frame after the title. `engine-revealjs.js` needs nothing.
- Tests: `test_grid.py::test_agenda` (states by slide position, the number color, no marker),
  `test_grid_pptx.py` (the markers, `.unnumbered` absent), `test_latex.py` (an `\engineagenda`
  frame; `pdftotext` shows every section title once, the Backup not at all).
- Proof: the two agenda slides in three formats under ncar and nasa-dark; `make -C decks/sample
  qa` (counts agree). Parity: the sample gains two pages. CHANGELOG Decks, LaTeX.

### 5. CLAUDE.md and the ledger

"Divider subtitles" bullet: the counting rule and `engine-unnumbered`; "Cards and boxes": the
quote and agenda markers, `draw_quote`, `draw_agenda`; "LaTeX authoring": `enginequote`,
`\engineagenda`, `\enginesectionunnumbered`; the test list names `test_section_subtitle.py`.
`design/unplanned-city-ledger.md`: the two divider-subtitle copies retired (commit 1).

### 6. The progress mark

`livery_build.py` the section entry's `eyebrow` gains `"progress": bool(dv.get("progress",
False))`; the schema's `section.progress`; `REFERENCE.md`; `livery build liveries/*/`. pptx
`section_subtitle._dress`: `f'{label} {n} of {total}'` (the numbered dividers counted first).
HTML: `data-engine-section-total` on the heading, `::before` content `.. attr(data-engine-section)
" of " attr(data-engine-section-total)` under a `--engine-cmp-eyebrow-progress` switch. beamer:
`\enginesectiontotal{n}` from the filter's header-includes, `\insertsectionnumberlabel` reads it
when defined and the livery's `\engine@section@progress` is true. One test per format on the
fixtures. CHANGELOG Liveries, LaTeX.

## Verification

1. Before commit 1, on `origin/main`: `tests/parity.sh baseline` and `tests/parity-latex.sh
   baseline`.
2. Every commit: `make test`; `livery build liveries/*/` committed in 2 and 6.
3. `tests/parity.sh check` after 1 (the fixtures' extra pages), 2 (identical), 3 and 4 (the
   sample's new pages; nothing else moves); `parity-latex check` after 3 and 4 (the cookbook's
   new frames only).
4. The pages looked at: the Backup divider in three formats (1); the quote under ncar, cu,
   nasa-dark (3); both agenda slides, the "current" state right in each format (4). `make -C
   decks/sample qa` and `make -C decks/fixtures qa` clean. `tests/app-open.sh` on the sample's
   pptx (new native shapes: Keynote must open it).
5. The PR body: a section per commit, the parity results, a contact sheet of the quote and
   agenda slides; `/pr-review N` before Ben merges; the release PR after.

## Risks

- beamer's `\tableofcontents` needs the `.toc` from an earlier pass: a clean Quarto build may
  show an empty agenda on the first run if Quarto's rerun check does not trigger (the fallback
  above).
- An author's body under `{.agenda}` is refused with a warning in the first cut.
- A long agenda (eight sections with subtitles) overflows the pptx body (no autofit on native
  boxes): `draw_agenda` drops the subs past the room.
- `\enginesectionunnumbered` loses the PDF bookmark for the appendix: acceptable, said in the
  guide.
- The attribution rule eats a last line that begins with a dash for another reason: documented,
  and `--` only counts at the start of the last line.

## Memory for the fresh session

`no-compat-shims.md`, `minimal-prs-versions.md`, `approval-text-in-chat.md`,
`american-spelling.md`, `sprint-tags-recut.md`, `latex-first-class.md`,
`design-framework-goal.md`, `next-sprints-after-129.md`. After the PR opens, update
`next-sprints-after-129.md`.
