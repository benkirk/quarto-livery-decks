# Handoff: stress-test the framework with the SAMuel decks (ncar and nsi)

For a fresh session. Written 2026-10-17, after the type-in-points sprint (engine 3.7.0,
beamer-livery-theme #32-#34; this repo #40-#43). Read this file, then CLAUDE.md, then
`engine-and-liveries.md` section 5 ("Type") and section 10 (the log's newest entries).

## 1. Purpose and question

Ben, in his words: re-render the SAMuel decks "in the new NCAR. Ostensibly they are similar but
our fork might have diverged significantly. This is not visual parity so much as scaling and
robustness: does the old markdown and its scaling fit sensibly still. And we also render with
NSI. In tandem this is intended to challenge our new framework; is its output fairly robust
and insensitive across different styles or is the spacing/scaling etc... fragile and bespoke."

The decks are a good test. They were tuned slide by slide (`scale=` on about half of them)
against sizes that no longer exist, and nsi changes the title sizes, fonts and fields.
Sharpened into criteria:

- **Robust** means three things:
  1. Every deck builds in every format under both liveries, and the slide counts agree.
  2. A slide's fit verdict (fits, overflows, too sparse) agrees across HTML, PDF and pptx.
  3. What changes from ncar to nsi is what the stated sizes predict (bigger titles wrap more),
     not spacing that collapses.
- **Sort every problem by cause:**
  - *content*: too much on the slide;
  - *old tuning*: a `scale=` value set for the old sizes;
  - *livery*: nsi's 32 pt condensed titles, 60 pt dividers, gold fields;
  - *framework*: the pptx estimates (a `.vcenter` table, the caution box, the band stack),
    `.fill` being HTML-only, beamer centring vertically;
  - *measurement*: LibreOffice substituting fonts in pptx renders.
- **A lever to test:** the deck-wide size step (`type-scale:` / `type-body:`, engine 3.7.0).
  Does one deck-wide value replace most of the per-slide `scale=` tuning?

## 2. Source

`/Users/benkirk/codes/project_samuel/devel/docs/presentations/samuel` (the samuel repo).
**Do not edit it, and keep its content out of this repo's git**: build a copy in the
scratchpad.

- **13 decks:** `samuel` (all parts) plus `1-overview` ... `5-deployment` and the appendices
  `A-peers` ... `G-cli`. Each is a front-matter wrapper that includes `_<part>.qmd`; the
  Makefile's `DECKS` lists them.
- **208 slides and 27 dividers in all.** Content:

  | item | count |
  |---|---|
  | `{dot}` diagrams | 23 (some with `pos=` and HTML-like labels) |
  | `{mermaid}` diagrams | 6 |
  | tables | 37 |
  | `.columns` | 37 |
  | images | 28 |
  | notes blocks | 190 |
  | `†` footnotes | 72 |
  | `{{< var >}}` (from `_variables.yml`) | 50 |
  | includes (`_tree_*.qmd`, `_out_*.qmd`, `_er_*.qmd`) | 10 |

  Also `data/*.tsv`, `companion/` (the Makefile's `SITE_EXTRA`) and `qa-names.txt`, which
  `deck_qa.py` reads when present.
- **Hand tuning:**

  | class | slides |
  |---|---|
  | `{.vcenter scale="1.15"}` | 91 |
  | `{.vcenter}` | 15 |
  | `{.smaller .center .fill}` | 17 |
  | other scale/fill mixes (0.85 to 1.25) | about 30 |
  | `{.caution .vcenter scale="1.15"}` | 6 |
  | `{.full}` | 5 |

  Figures: 19 `{height="72%" fig-align="center"}` and a few other heights and widths. No
  `themeoptions`, callouts or executable cells.
- **Old framework:** `../framework`, a submodule of quarto-docs-framework pinned at `c6adf5a`
  (theme 2.8.0, formats `ncar-beamer`/`ncar-revealjs`, beamer `fontsize: 10pt`). The deck
  directory's `_extensions`, `_ncar` and `_quarto.yml` are links into it. The sources name none
  of its paths.
- **The before-picture:** the old outputs (`*.pptx`, `*.pdf`, `*.html`) and `_qa/` (per-deck
  contact sheets, `report.txt`; every deck's slide counts agreed) are still in that directory.
- **What moved under it:** when the decks were tuned, the body was 0.043 of the slide height
  in PDF, 0.037 in pptx and 0.031 in HTML. It is now 0.0296 everywhere: PDF text is about 31%
  smaller, pptx about 20%, HTML about 5%.
  - ncar now sets its pptx on the brand's 10 x 5.625 in at body 12, titles 20, cover 22,
    dividers 30.
  - nsi (extends cu) is on 13.33 x 7.5 in at body 16, titles 32 (0.059 of the height against
    ncar's 0.049), cover 48, dates 28, dividers 60. Its headings are Heros Condensed in HTML
    and PDF, Helvetica Neue (not embedded) in pptx.
  - Expect fewer overflows and more sparse slides under ncar, and more title wraps under nsi.

## 3. Setup

```bash
S=<scratchpad>/samuel; SRC=/Users/benkirk/codes/project_samuel/devel/docs/presentations/samuel
# the old links and the old outputs stay behind (top level only: companion/pipeline.html is a source)
mkdir -p $S && rsync -a --exclude '/_extensions' --exclude '/_ncar' --exclude '/_quarto.yml' \
  --exclude '/_qa' --exclude '/_site' --exclude '/.quarto' --exclude '/*_files' \
  --exclude '/*.pptx' --exclude '/*.pdf' --exclude '/*.html' --exclude '/#*#' "$SRC/" "$S/"
# keep the samuel Makefile's DECKS, SITE_EXTRA etc.; point the include at this framework
sed -i '' 's#^include .*Make.common#include /Users/benkirk/Documents/quarto-livery-decks/docs/Make.common#' $S/Makefile
cd /Users/benkirk/Documents/quarto-livery-decks && source etc/config_env.sh
cd $S && make all qa LIVERY=ncar      # then measure; then the same with LIVERY=nsi
```

- Make creates `_engine`, `_extensions` and `_quarto.yml` (README "Using the framework from
  another repo").
- `LIVERY=` on the command line always wins (CLAUDE.md). Switching liveries rebuilds every
  deck, so keep one copy per livery (`$S-ncar`, `$S-nsi`) to compare them side by side.
- `Make.common` is `.NOTPARALLEL` and 13 decks x 3 formats is long. Run builds in the
  background, one livery at a time, and log each to a file.
- Mermaid needs Chrome Headless Shell installed; Graphviz is bundled.

## 4. Measurements

Per deck, per livery, per format. Tabulate everything; one TSV per livery is enough.

1. **Builds and counts:** any render error, and `deck_qa.py`'s `slides:` line (MISMATCH
   matters).
2. **Overflow:**
   - PDF: `deck_qa` flags runs into the footer and overlapping text;
   - HTML: content past the edges;
   - pptx: no direct check. Use `slide_layout.py`'s estimates, or render with LibreOffice and
     look.
   - Also record the HTML autofit shrink per slide: `engine-revealjs.js` sets the slide's font
     size and `--engine-fit` when it shrinks. A small Playwright read-out over every slide, as
     `deck_qa` does, gives "how close to overflowing" rather than a yes or no.
3. **Too sparse:** `deck_qa`'s "short ... uses N% of the body" hints, where the old `scale=` is
   now too small.
4. **The verdict table:** per slide, fit / overflow / sparse in each format. Disagreements are
   the fragility signal.
5. **Title wraps:** lines per slide title, ncar against nsi (from the HTML DOM, or the PDF's
   text boxes).
6. **Before and after (ncar):** counts against the old `_qa/report.txt` and its contact sheets.
7. **Compositions:** `make measure` on each deck's title, divider, closing and feature slides
   (0 misses is the current baseline on the fixtures and quickstart).
8. **The lever:** re-run one heavy deck (e.g. `2-concepts`) with a deck-wide `type-scale:`
   chosen from step 3's numbers, and count how many per-slide verdicts it fixes or breaks.

## 5. Outputs

- **`docs/design/stress-test-findings.md`:** the counts, the verdict table's disagreements,
  the worst slides by cause class (section 1), and what the lever did. No SAMuel content
  beyond slide titles and short phrases.
- **Contact sheets** of the worst slides (HTML | PDF | PPTX, ncar against nsi), sent to Ben
  with SendUserFile.
- **Fixes:** each is a separate small PR, engine first where the cause is there, with a
  contact sheet before it merges. Content and old-tuning findings are reported, not "fixed" in
  the samuel source.

## 6. Constraints and conventions

- **Working with Ben:** a plain-language summary before any questions; text he must approve
  goes in the chat; PRs merge once CI is green; ask before moving or cutting tags (engine 3.7.0
  has none). In the engine repo pass `gh --repo benkirk/beamer-livery-theme`.
- **Settled, do not reopen:** the compositions-as-boxes design, type in points on the livery's
  canvas (ncar 10 x 5.625 in), ncar's `feature.style: bar`, cu/nsi's NSI-deck sizes.
- **Deferred:** the sample deck's "Project config" PDF slide (code runs off the page, the
  right column doesn't paint) and beamer's vertical centring (HTML and pptx anchor at the
  top).
- **Measurement caveats:**
  - LibreOffice on this Mac has neither Poppins nor Helvetica Neue, so pptx renders substitute
    a serif. Judge pptx wrapping by the HTML and PDF renders (the same sizes), or from the
    estimates.
  - Beamer `itemize` stops at three levels (a fourth is "Too deeply nested").
- **Tools:**
  - `deck_qa.py` (`make qa`): counts, overflow, sparse hints, contact sheets.
  - `comp_measure.py` (`make measure`): compositions.
  - `docs/quickstart/screenshots.py` and `gallery.py`: Playwright patterns.
  - Two side-by-side composers were scratch scripts in the last session. The appendix has the
    recipe; promote one to `utils/` if it earns its keep.

## 7. Known background

- **Engine 3.7.0:**
  - `livery.yml` `type:` (role -> pt) and `pptx.size`; `livery.type_pt()`, `canvas_scale()`,
    `half_pt()`; `tools/test_type.py`.
  - HTML reads `--engine-type-*`, beamer `\engine@type@*`. Beamer's `scale=` scales
    `\engine@typebody`, so tables, code and levels follow it. LM Mono is set at 1.15, the same
    line width as HTML's monospace.
  - The deck step: beamer theme option `typescale=`, HTML `--engine-type-scale`, pptx
    `type_step.py`.
- **Framework:**
  - `slide_layout.py`: `band_stack()` centres the band title's stack; `_scale_paragraphs`
    rounds to the half point.
  - `comp_measure.py`: `widened()` keeps thin type over art.
  - The post-processors take slide pixels and points per pixel from the livery's canvas.
- **Memory files** (`~/.claude/projects/-Users-benkirk-Documents-quarto-livery-decks/memory/`):
  `type-points-canvas`, `compare-against-reference-slides`, `composition-handoff`,
  `options-by-slide-role`, `layman-summary-before-questions`, `approval-text-in-chat`.

## Appendix: a side-by-side composer

After `make qa` (per-slide PNGs in `_qa/<deck>/{html,pdf}/`), render the pptx with
`soffice --headless --convert-to pdf --outdir <tmp> <deck>.pptx`, then `pdftoppm -r 60 -png`.
Paste the n-th PNG of each format into one row per slide with PIL, 640 px a cell, a label row
on top. A fourth column for the other livery's copy (`$S-nsi/_qa/...`) makes the ncar-against-nsi
sheet.
