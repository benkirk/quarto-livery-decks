# Sprint handoff: one look, one key (the themes' hand numbers)

**State (2026-10-23):** open as #138 (`themes/one-look-one-key`: the handoff, the seven items, the
records, the outline fix). Items 1–3 at Ben's picks from the sheets (the band, hairline C, the
PDF's gaps); items 4–7 committed with the proposal as the default by agreement overnight and
confirmed by him from the sheets on 2026-10-23 ("Picks" below). An eleventh commit fixes the
HTML pick outline he spotted on item 5's sheet (an overlay above the head and the strip). Departures from the plan: the hairline's weight is
beamer's 0.0016, not 1 px; the gaps are the PDF's old ex gaps as em, not HTML's; `type.tracking`
defaults to 0.08 because 0.1 makes pdftotext split the PDF's tracked words; the white pile became
a derived `on-dark` role rather than a panel text key; the pptx draws no footnote rule.

**For a fresh session.** One PR against `main` from `origin/main` after the release that follows
#136 (branch `themes/one-look-one-key` from `81a3c9d`, release 26.10.9), a commit per item in the
order below, squash-merged once, no version bump. Planned 2026-10-22 from the #127–#135 sweep's deferred list
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

The hairline and body agree today; the title does not quite (read at the sprint's start,
2026-10-22): the pptx title placeholder spans the whole band to the rule (0.049–0.1444,
`anchor="ctr"`, `livery_template.py:208`) where beamer and HTML center the title in the 0.0778
band (0.0489–0.1267), so the pptx title sits about 8 px of 900 lower; the accent tab is three
heights (beamer the title text's box, HTML the h2 at least 70 px, pptx the full band); HTML's
hairline is fixed at 130 px where beamer's follows a two-line title (pptx's cannot: a static
layout). The 0.0178 minimum gap is the band's own: `rule-y − (top + height)` = 0.0177. The 0.0222
(rule → body) is written in `resolve()` and again in the outer theme.
**Proposal:** `livery.json` `frametitle` gains `top`, `height`, `rule-y` (fractions of the height;
defaults 0.0489, 0.0778, 0.1444) beside its derived `body`, all four **always emitted**
(`\engine@ft@top/height/ruley/bodytop`, `--engine-title-top/-height/-rule-y/--engine-body-top`),
and the template builder reads the same (`master()`'s tab, rule and title placeholder). The
`\ifdefined` and the px fallbacks go; the 0.0178 becomes the band's difference; the 0.0222 is
derived once. `make measure` does not cover the content title, so the proof is parity (PDF pages
and HTML flat, the pptx master and layouts named) and a content slide shot per format.
**Picked (Ben, 2026-10-22, at planning):** flat keys, `frametitle.top/height/rule-y` beside
`align/tab/rule`; the boolean `rule` stays. **Open on the sheet:** the pptx title centered in the
0.0778 band as beamer and HTML (one look, the pptx title moves ~8 px up; the proposal) or left
spanning to the rule. HTML's fixed hairline on a two-line title stays as it is, recorded.

### 2. The title hairline: three blends and three weights

| | beamer (`beamercolorthemeEngine.sty:18`) | HTML (`scss` ~193, `livery_build.py` BLENDS `rule`) | pptx template (`livery_template.py:207`) |
|---|---|---|---|
| color | `BrandSurface!70!BrandText!40!BrandBackground`: xcolor mixes left to right, so (surface 70 % over text) 40 % over background: ncar #DDE3EA, cu #DDDCDA, **nasa-dark #262829** (near-black on black: no visible hairline in the dark PDF today) | `var(--engine-rule)`: foreground 30 % over surface: ncar #A9B8CB, nasa-dark #606367 | `tx1` at 30 % alpha over the background: ncar ≈ #B2C2D7, nasa-dark ≈ #4C4C4C |
| weight | 0.4 pt = 0.0016 of the height (the heaviest) | 1 px = 0.0011 | 9525 EMU = 0.75 pt = 0.0014 |

Predates the window. **Proposal:** one color key, `frametitle.rule-color` (a role, blend or hex,
resolved as `boxes.rail.line-color` is; default the `rule` blend, HTML's), and the weight
`frametitle.rule-width` (a fraction of the height, default 1/900 = 0.0011) in all three.
**Visible:** the PDF's hairline darkens from #DDE3EA to #A9B8CB and thins; on nasa-dark it
appears; the pptx barely changes. **Picked:** the two flat keys. **Open on the sheet:** A the
`rule` blend at 0.0011 (the proposal); B a new lighter `hairline` blend at the PDF's value for
all three (the closest two-color mix: foreground 14 % over background, ncar #DBE3EC; nasa-dark
#242424, so HTML and the pptx lose the hairline too); C A at beamer's weight 0.0016.
Side-by-side: a content slide per format under ncar, cu and nasa-dark.

### 3. ex where HTML has em

Poppins' ex is about 0.55 em, so the PDF's gap is about half the HTML's under the same digit.

| gap | beamer | HTML |
|---|---|---|
| `::: note` under a figure | `\enginenote`: `\vskip0.4ex` (inner `:364`) | `margin-top: 0.4em` (`scss:334`) |
| quote attribution | `\vskip0.6ex` (`:567`) | `margin-top: 0.6em` (`:439`) |
| footnotes, under the rule | `\vskip0.8ex` (`:350`) | `padding-top: 0.55em` |
| footnotes, between | `\vskip0.4ex` (`:354`) | `margin: 0.3em 0 0` |
| divider eyebrow → title | `\vskip0.6ex` (`:107`; `:123` is beamer's unused subsection page) | `margin-bottom: 0.5em` on the eyebrow (`scss:911`); pptx `section_subtitle.py:44` `LABEL_GAP = 10` px: three hands |
| divider title → subtitle | `\vskip1.2ex` (`:111`) | `margin-top: 0.7em` on the subtitle (`:931`); pptx `:45` `BODY_GAP = 22` px |
| block title (feature-panel blocks) | `0.6ex` / `0.3ex` / `0.6ex` (`:308-310`) | beamer only |

**Proposal:** beamer selects the element's font and then skips in `em` (the em HTML measures in,
no `\dimexpr`), the factor the element's key: `boxes.note: {gap: 0.4}` (em of the caption),
`boxes.quote.attribution-gap: 0.6` (em of the caption), `section.eyebrow-gap: 0.5` (em of the
eyebrow) and `section.subtitle-gap: 0.7` (em of the subtitle), read by all three formats
(`section_subtitle.py` drops its pixel copies); the plain block's three to 0.33/0.17/0.33 em of
the block title (no twin, no key). **Moves the PDF** by 0.1–0.2 em per gap. The footnote rows go
with item 4. **Picked:** the divider's gaps are in. **Open on the sheet:** HTML's values win (the
proposal), or the PDF's (0.22, 0.33, 0.28, 0.66 em; then HTML shrinks).

### 4. The slide footnotes

| | beamer (inner `:344-354`, `:995`) | HTML (`scss` `.engine-footnotes`) | pptx (`style_footnotes.py`) |
|---|---|---|---|
| rule | `\rule{12mm}{0.6pt}` = 0.075 of the 160 mm paper × 0.0024 of its height | `120px × 2px` = 0.075 × 0.0022 | none |
| rule color | `BrandText!30!BrandBackground` (foreground 30 % over the background) | `currentColor` (muted) at opacity 0.6 | — |
| rule → text | 0.8 ex | 0.55 em | `FOOT_BEFORE` 10 pt × K above the paragraph |
| width | `0.6\textwidth` | `max-width: 60%` | in place |
| hang | `1.1em` (`\enginefootnote`); `1.2em` in beamer's own `\footnote` template (`:995` area, `\hbox to 1.2em`) | `0.9em` (`padding-left`, `text-indent`, the dagger's width) | none |
| between entries | 0.4 ex | 0.3 em | — |
| mark | `BrandAccent`, bold | `--engine-accent`, bold | accent, not bold (`MARK_COLOR`; `style()` sets size and color only) |
| text | `BrandMuted`, footnote size | muted, footnote size, leading 1.35 (now the role's) | muted, footnote size |
| place | the frame's foot (`\enginefootnotespring`) | `bottom: 70px` | in place (pptx cannot move content) |

The rule's size already agrees as fractions; everything else is three hands. **Proposal:**
`boxes.footnote: {rule: 0.0022, rule-length: 0.075, rule-color: <blend>, width: 0.6, gap: <em>,
hang: <em>, step: <em>}` (the rule's thickness of the height and length of the width as two
scalars, since `emit_sty_boxes` writes a list as `[vertical, horizontal]`; `width` of the text
width; the ems of the footnote type), read by both themes; beamer's own `\footnote` template
takes the same hang; `style_footnotes.py` sets the hang on the paragraph (`marL`/`indent`, as
`references_style()`), the gap and step as its paragraph spacing, and the mark bold. **The pptx
draws no rule** (picked at planning): a shape drawn when the footnote is styled is orphaned when
`grid.py` or `columns.py` moves the paragraph into a new box, and a late step would need the
paragraph's rendered position, which nothing knows before PowerPoint opens the file; the ledger
holds it. **Moves both PDF and HTML**, and the pptx footnotes' indent and spacing. **Open on the
sheet:** hang 0.9 / 1.1 / 1.2 em; gap 0.55 em (HTML) or 0.44 em (the PDF's 0.8 ex); step 0.3 or
0.22 em; the rule color, one blend for both: the `rule` blend (ncar #A9B8CB, nasa-dark #606367,
between the two today) or foreground 30 % over background (the PDF's: #B2C2D7, #4C4C4C).
Side-by-side: the sample's `## Next steps` (†, ‡) and `## Citing sources` (a lifted note and a †)
in all three formats under ncar, cu and nasa-dark (the dark livery is where the blends part most).

### 5–7. The smaller piles of the same kind (the ledger's Untriaged, optional here)

5. **Strip spacing per format**: the scss, `grid.py` and the inner theme each set the gap above and
   below a strip on their own numbers (`--engine-strip-gap` is the pad's vertical; the pptx and
   the theme their own). One `boxes.strip.gap`.
6. **Small-caps tracking**: HTML 0.1em (label, eyebrow) / 0.08 (date) / 0.04 (table header),
   beamer `LetterSpace=4` (label and table header; the eyebrow and date untracked), pptx a fixed
   1 pt `spc="100"` (`common.style_runs`, the label), 0.1 em (`section_subtitle.py`) and 0.04 em
   (`style_tables.py:72`; the ledger said none). One `type.tracking` (em) for every small-caps run.
7. **White by hand on dark fields**: 16 `#fff`/`white` in the scss, 7 `white` in the beamer themes,
   `RGBColor(0xFF, 0xFF, 0xFF)` in `slide_layout.py` (the feature bar's number and panel text),
   where the composition's column role already reaches every format. `tests/test_cli.py`'s
   ratchet (`test_theme_literal_counts_only_fall`) holds the counts; each one taken off lowers its
   ceiling.

## Commits, in order

0. This handoff, with Ben's picks written in.
1. **The content title band** (item 1): `frametitle.top/height/rule-y`, emitted always, the four
   drawers reading them, the fallbacks gone; schema and `REFERENCE.md`; every livery's `build/`
   and `template.pptx` regenerated (`make livery` per livery). Parity: PDF and HTML flat, the pptx
   master and layouts (and every slide's title if the pptx title moves into the band).
2. **The hairline** (item 2): `frametitle.rule-width/rule-color`, all three the same. Visible in
   the PDF and the pptx.
3. **ex → em** (item 3, less the footnotes; the divider's gaps in). Moves the PDF, and the pptx
   divider stack.
4. **`boxes.footnote`** (item 4). Moves both; the pptx footnotes' indent and spacing; no rule.
5–7. The piles, one commit each (all three picked, 2026-10-22).
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
- `tests/app-open.sh` stays the release's step: no pptx shape is added (the footnote rule is not
  drawn).
- The pick sheets come from a throwaway shooter in the session's scratchpad: one code state, each
  candidate a copy of the livery with the candidate's keys set in its `livery.yml` (built with
  `livery build` and `livery template`, `extends` resolved through a link to the parent beside the
  copy), the deck built with `LIVERY_DIR=` on the copy; the before row is a worktree of `main`.

## Picks

Made at planning (2026-10-22): flat keys `frametitle.top/height/rule-y` and
`rule-width/rule-color`, the boolean `rule` kept; the divider's gaps in item 3 under `section:`;
no pptx footnote rule; items 5–7 all ride along (the white pile needs a text role on the feature
panel, a key Ben names when its sheet is up).

From the side-by-sides, each before its commit (the row filled in as Ben picks):

1. The pptx title in the 0.0778 band (one look) or spanning to the rule: **the band, and the PDF
   tab the band's height** ("the branch looks great", 2026-10-22).
2. The hairline's blend and weight (A `rule` at 0.0011 / B a lighter `hairline` blend / C A at
   beamer's 0.0016): **C** (2026-10-22).
3. ex → em: HTML's values (the PDF grows) or the PDF's (HTML shrinks): **the PDF's** (note 0.3,
   attribution 0.5, eyebrow 0.33, subtitle 0.66 em; "P looks good", 2026-10-22).
4. The footnotes: hang (0.9 / 1.1 / 1.2 em), gap (0.55 / 0.44), step (0.3 / 0.22), the rule's
   blend (`rule` / foreground 30 % over background): **the proposal** (hang 0.9, gap 0.55, step 0.3, `rule`; committed as the default overnight by
   agreement, confirmed by Ben from the sheets 2026-10-23: "I really can't tell any visible
   difference on 4-6").
5. The strip's gap: **0.3 em of the body above and below** (HTML's margin as it was; the PDF and pptx gain it;
   the sheet also showed no gap; confirmed 2026-10-23).
6. The tracking (one value, or per element): **one `type.tracking`, 0.08 em** (confirmed 2026-10-23; the
   sheet showed 0.1, 0.08 and 0.05; at 0.1 pdftotext splits the PDF's tracked words into letters,
   "S E C T I O N", measured on Poppins Bold at 8 pt: 8 % keeps them whole; the table header
   changes most).
7. The feature panel's text role and key: **a derived role, `roles.on-dark`** (whichever of
   background and foreground reads better on `dark`; white on every bundled livery, so the sheet
   is flat), read by the panel, the feature footline and number, the feature blocks, `.brand-dark`
   and the code tints; the key name confirmed 2026-10-23.

## Memory for the fresh session

`no-compat-shims.md`, `minimal-prs-versions.md`, `approval-text-in-chat.md`, `american-spelling.md`,
`options-by-slide-role.md` (confirm visible-default changes by the slide they land on),
`compare-against-reference-slides.md`, `design-framework-goal.md`, `sweep-127-135.md`.
