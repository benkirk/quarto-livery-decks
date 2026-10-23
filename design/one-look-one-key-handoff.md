# Sprint handoff: one look, one key (the themes' hand numbers)

**For a fresh session.** One PR against `main` from `origin/main` after the release that follows
#136 (branch `themes/one-look-one-key`), a commit per item in the order below, squash-merged once,
no version bump. Planned 2026-10-22 from the #127–#135 sweep's deferred list
(`design/sweep-129-135-handoff.md`, `design/unplanned-city-ledger.md` "2026-10-22: window
#127–#135", Open) and the older Untriaged items of the same kind. Every item here **changes what a
deck renders** in at least one format, so this is not a sweep: the proof is before/after
screenshots judged by eye, with parity naming every page and slide that moved, and each number
that changes is Ben's pick from a side-by-side.

## The goal

The design framework's rule (`design/engine-and-liveries.md`, the head): an element is one reader,
one drawer per format, every number from the livery. The element series kept it for the new
elements; the furniture that predates it did not. Four looks are drawn per format on hand numbers
that have drifted apart, and three smaller piles are of the same kind. After this sprint a livery
owner changes a content title's band, a hairline's color or a footnote's rule in `livery.yml`,
once, and the three formats follow.

## The numbers, side by side (read 2026-10-22 after #136)

### 1. The content title band

| quantity | beamer (`beamerouterthemeEngine.sty:117-143`, inner `:860`) | HTML (`engine-revealjs.scss` ~181-193) | pptx template (`livery_template.py:169,203-208`) | `livery_build.py` |
|---|---|---|---|---|
| title top | `0.0489\paperheight` | `top: 44px` (= 0.0489 × 900) | `title_top = 0.049` | — |
| band height | `0.0778\paperheight` (`\@tempdimc`) | `min-height: 70px` (= 0.0778) | the title box runs to `rule_y` | — |
| hairline y | `0.1444\paperheight` | `top: 130px` (= 0.1444) | `rule_y = 0.1444` | — |
| hairline thickness | `0.4pt` | `1px` (= 0.6 pt on the 540 pt canvas) | `9525` EMU (0.75 pt) | — |
| min gap title→rule | `0.0178\paperheight` | — | — | — |
| body top | rule + `0.0222` = 0.1667, or `\engine@ft@bodytop` | `150px` fallback, or `--engine-body-top` | the layout's body placeholder | `BODY_TOP = 0.1667`; `frametitle.body = max(BODY_TOP, below the mark)`, **emitted only when it differs** (`:838-844`, `:1093-1094`), so both themes carry an `\ifdefined`/fallback copy of 0.1667 |

The numbers agree today (ncar's by construction); the drift is four copies and two fallbacks.
**Proposal:** `livery.json` `frametitle` gains `top`, `height`, `rule-y` (fractions of the height;
defaults 0.0489, 0.0778, 0.1444) beside its `body`, all four **always emitted**
(`\engine@ft@top/height/ruley/bodytop`, `--engine-title-top/-height/-rule-y/--engine-body-top`),
and the template builder reads the same (`field_layout`'s content layout). The `\ifdefined` and
the px fallbacks go. **Flat by construction**; `make measure` does not cover the content title, so
the proof is parity (PDF pages, the quickstart's screenshots) and a content slide shot per format.
Pick for Ben: the key names (a `livery.yml` key needs his agreement; `frametitle.rule` is already
the boolean "draw it", so the y needs another name: `rule-y`, or `frametitle.band: [top, height,
rule]`).

### 2. The title hairline: three blends and three weights

| | beamer (`beamercolorthemeEngine.sty:18`) | HTML (`scss` ~193, `livery_build.py` BLENDS `rule`) | pptx template (`livery_template.py:207`) |
|---|---|---|---|
| color | `BrandSurface!70!BrandText!40!BrandBackground` ≈ #DCE3EA on ncar | `var(--engine-rule)`: foreground 30 % over surface ≈ #A9B8CB | `tx1` at 30 % alpha over the background ≈ #B3C3D7 |
| weight | 0.4 pt | 1 px (0.6 pt) | 0.75 pt |

Predates the window. **Proposal:** one color key, `frametitle.rule-color` (a role or blend; default
the `rule` blend, HTML's), and the weight from item 1's `rule-y`'s companion `rule-width` (a
fraction of the height, 1/900 = 0.0011) in all three. **Visible:** the PDF's hairline darkens
from #DCE3EA to #A9B8CB; the pptx barely. Pick for Ben: which blend wins, the `rule` blend (HTML
and the table rules already use it) or a new lighter `hairline` blend at the PDF's value for all
three. Side-by-side: a content slide per format under ncar, cu and nasa-dark.

### 3. ex where HTML has em

Poppins' ex is about 0.55 em, so the PDF's gap is about half the HTML's under the same digit.

| gap | beamer | HTML |
|---|---|---|
| `::: note` under a figure | `\enginenote`: `\vskip0.4ex` (inner `:364`) | `margin-top: 0.4em` (`scss:334`) |
| quote attribution | `\vskip0.6ex` (`:567`) | `margin-top: 0.6em` (`:439`) |
| footnotes, under the rule | `\vskip0.8ex` (`:350`) | `padding-top: 0.55em` |
| footnotes, between | `\vskip0.4ex` (`:354`) | `margin: 0.3em 0 0` |
| divider eyebrow → title | `\vskip0.8ex` (`:123`), `0.6ex` (`:107`) | the composition's boxes (no gap of its own) |
| block title | `0.6ex` / `0.3ex` (`:308-310`) | beamer only |

**Proposal:** write them as shares of the body (`\engine@typebody`, the house idiom; `\engine@agendarow`
already does) or as the element's key (`boxes.quote.attribution-gap`, the note's gap under
`boxes.note`?), at HTML's values. **Moves the PDF** by 0.1–0.2 em per gap. The footnote rows go
with item 4. Pick for Ben: HTML's values win (the proposal), or the PDF's (then HTML shrinks).

### 4. The slide footnotes

| | beamer (inner `:344-354`, `:995`) | HTML (`scss` `.engine-footnotes`) | pptx (`style_footnotes.py`) |
|---|---|---|---|
| rule | `\rule{12mm}{0.6pt}` = 0.075 of the 160 mm paper × 0.0024 of its height | `120px × 2px` = 0.075 × 0.0022 | none |
| rule color | `BrandText!30!BrandBackground` (foreground 30 % over the background) | `currentColor` (muted) at opacity 0.6 | — |
| rule → text | 0.8 ex | 0.55 em | `FOOT_BEFORE` 10 pt × K above the paragraph |
| width | `0.6\textwidth` | `max-width: 60%` | in place |
| hang | `1.1em` (`\enginefootnote`); `1.2em` in beamer's own `\footnote` template (`:995` area, `\hbox to 1.2em`) | `0.9em` (`padding-left`, `text-indent`, the dagger's width) | none |
| between entries | 0.4 ex | 0.3 em | — |
| mark | `BrandAccent`, bold | `--engine-accent`, bold | accent, bold (`MARK_COLOR`) |
| text | `BrandMuted`, footnote size | muted, footnote size, leading 1.35 (now the role's) | muted, footnote size |
| place | the frame's foot (`\enginefootnotespring`) | `bottom: 70px` | in place (pptx cannot move content) |

The rule's size already agrees as fractions; everything else is three hands. **Proposal:**
`boxes.footnote: {rule: [0.075, 0.0022], rule-color: <blend>, width: 0.6, gap: <em>, hang: <em>,
step: <em>}` (fractions of the width and height, em of the footnote type), read by both themes;
beamer's own `\footnote` template takes the same hang; `style_footnotes.py` sets the hang on the
paragraph (`marL`/`indent`) and may draw the rule above the first footnote (a new shape: a
`cxnSp` the width of `rule[0]`, placed above the paragraph it styles in place). **Moves both PDF
and HTML**, and pptx if it draws the rule. Picks for Ben: hang 0.9 / 1.1 / 1.2 em; gap 0.55 em
(HTML) or 0.44 em (the PDF's 0.8 ex); step 0.3 or 0.22 em; the rule color, one blend for both
(foreground 30 % over background, the PDF's, or muted at 60 %, HTML's); whether pptx draws the
rule. Side-by-side: the sample's "Footnotes" slide in all three formats under ncar and nasa-dark
(the dark livery is where `BrandText!30!BrandBackground` and muted-at-60 % part most).

### 5–7. The smaller piles of the same kind (the ledger's Untriaged, optional here)

5. **Strip spacing per format**: the scss, `grid.py` and the inner theme each set the gap above and
   below a strip on their own numbers (`--engine-strip-gap` is the pad's vertical; the pptx and
   the theme their own). One `boxes.strip.gap`.
6. **Small-caps tracking**: HTML 0.1em / 0.08 / 0.04 by element, beamer `LetterSpace=4`, pptx
   `spc="100"` (`grid.py`), 0.1em (`section_subtitle.py`) and none (`style_tables.py`). One
   `type.tracking` (em) for every small-caps run.
7. **White by hand on dark fields**: 16 `#fff`/`white` in the scss, 7 `white` in the beamer themes,
   `RGBColor(0xFF, 0xFF, 0xFF)` in `slide_layout.py` (the feature bar's number and panel text),
   where the composition's column role already reaches every format. `tests/test_cli.py`'s
   ratchet (`test_theme_literal_counts_only_fall`) holds the counts; each one taken off lowers its
   ceiling.

## Commits, in order

0. This handoff, with Ben's picks written in.
1. **The content title band** (item 1): the keys, emitted always, the four drawers reading them, the
   fallbacks gone; schema and `REFERENCE.md`; every livery's `build/` and `template.pptx`
   regenerated (`make livery` per livery). Flat: parity and a content slide per format.
2. **The hairline** (item 2): the color key and the width, all three the same. Visible in the PDF.
3. **ex → em** (item 3, less the footnotes). Moves the PDF.
4. **`boxes.footnote`** (item 4). Moves both; pptx may gain the rule.
5–7. The piles, one commit each, if picked.
8. The changelog (Decks: what looks different, per format; Liveries: the new keys, defaults, nothing
   to do), `docs/formats.md` and `liveries/README.md`'s boxes paragraph, CLAUDE.md's bullets, the
   ledger (the items off Untriaged, the entry).

## Verification

- `tests/parity.sh baseline` and `tests/parity-latex.sh baseline` on `origin/main` the same day;
  `check` after each commit: every moved page and slide named in the commit, none unexplained.
- Before/after screenshots of the affected slides in all three formats under ncar, cu and nasa-dark
  (Playwright for HTML, `pdftoppm` for the PDF, LibreOffice for the pptx; `make measure`'s shooters
  and `deck_qa.py`'s serve), compared by eye, a contact sheet per item for the PR.
- `make test` after every commit; `make -C decks/sample qa`; the literal ratchet's ceilings lowered
  as the piles shrink.
- `tests/app-open.sh` if pptx gains a shape (the footnote rule).

## Open picks for Ben (answer before the fresh session starts)

1. Key names for the title band (`frametitle.top/height/rule-y`, or `frametitle.band`).
2. The hairline's blend: `rule` (HTML's, darker in the PDF) or a new lighter blend for all three.
3. ex → em: HTML's values win (the PDF grows), or the PDF's (HTML shrinks).
4. The footnotes: hang (0.9 / 1.1 / 1.2 em), gap, step, the rule's blend, and whether pptx draws
   the rule.
5. Which of items 5–7 ride along.

## Memory for the fresh session

`no-compat-shims.md`, `minimal-prs-versions.md`, `approval-text-in-chat.md`, `american-spelling.md`,
`options-by-slide-role.md` (confirm visible-default changes by the slide they land on),
`compare-against-reference-slides.md`, `design-framework-goal.md`, `sweep-127-135.md`.
