# Stress test: the SAMuel decks under ncar and nsi

2026-10-17. The question and the method are in `stress-test-handoff.md`. The SAMuel decks
were written and tuned slide by slide against the old NCAR framework (theme 2.8.0). Here they
are rebuilt unchanged with this framework (engine 3.7.0) under `LIVERY=ncar` and `LIVERY=nsi`,
from copies in a scratch directory. No SAMuel content appears below beyond slide titles.

## 1. Verdict

**Robust, and more consistent across formats than the framework the decks were tuned on.**

- Every deck builds in every format under both liveries: 13 decks, 39 outputs each, no
  render errors or warnings. `make qa` passes under both. Slide counts agree everywhere:
  242 slides in the 12 part decks, 232 in the whole deck, the same as the old outputs.
- **A slide's verdict (fits / sparse / overflows) agrees across HTML, PDF and pptx on 201 of
  208 content slides under ncar and 204 under nsi.** On the old outputs: 187.
- **Body heights agree across formats.** On text slides the PDF body is 0.95x the HTML
  body's height, with 80% of slides between 0.94 and 0.95; pptx is 1.01x. The old outputs
  were 1.21x and 1.20x, spread over 1.0-1.47. nsi matches ncar (0.93x, 1.02x).
- **What changes from ncar to nsi is what the sizes predict.** Fills shift by a few
  hundredths, and title wraps don't increase in HTML or PDF (nsi's 32 pt titles are
  condensed). The one exception is pptx titles, where nsi uses a regular-width face
  (section 5, livery).
- **The old tuning no longer fills the slides.** The 89 slides tuned
  `{.vcenter scale="1.15"}` fill a median 0.40 of the body now, in every format and both
  liveries. In the old outputs they filled 0.61 in PDF, 0.58 in pptx and 0.47 in HTML. The
  decks were tuned on the old PDF/pptx sizes, which were 31% and 20% larger than today's.
  The slides are consistent and uniformly roomy, not broken.
- **Five framework defects, all in pptx or the measuring tools, none in HTML or PDF.**
  Fixed in #45-#48; one more waits for a decision (section 7).

## 2. Method

Tools: the framework's `make qa` (`deck_qa.py`) and `make measure` (`comp_measure.py`), plus
scratch scripts (not in git) that measure every content slide in each format:

- **HTML**: a Playwright pass over every slide records the autofit factor (`--engine-fit`),
  the title's line count, and the extent of the body's text (every text node's line boxes)
  as a share of the body area (title bottom to the floor or the footnotes).
- **PDF**: `pdftotext -bbox-layout` per frame gives title lines and the body text's extent
  over the same area. Overflow is `deck_qa`'s footer, margin and overlap checks.
- **pptx**: LibreOffice renders each deck twice, as built and with `normAutofit` stripped.
  The as-built render shows which slides PowerPoint's shrink-on-overflow would shrink (the
  ratio of body line heights). The stripped render shows how far the text really runs.
- **Verdict per slide and format:** overflows when the text won't fit at its stated size (HTML
  autofit shrank it, PDF failed `deck_qa`, pptx would shrink or runs past the placeholder);
  sparse when the text fills at most 0.60 of the body; fits at 0.70 or more; between the two
  it counts as "edge", which agrees with either. Sparse is judged on text, column, table and
  code slides only.

**Measurement caveats** (several corrected during the run):

- LibreOffice does **not** read fonts embedded in a pptx. ncar's renders are right on the
  test Mac only because Poppins is installed there. A fresh LibreOffice profile (as
  `comp_measure` used) draws a serif; fixed in #48.
- Homebrew LibreOffice can't see macOS's Helvetica Neue (nsi's pptx face) or pandoc's code
  face `Courier`; both fall back to serifs. The scratch measurements map them to Liberation
  Sans and Liberation Mono (Arial/Helvetica and Courier New metrics). nsi pptx line breaks
  are therefore close but not exact.
- An ink (pixel) extent was tried first and dropped: rules under titles and footnotes read
  as content, and nsi's faded satellite photo behind content slides (present in all three
  formats) filled the whole body. Text extents are immune to both.
- `make measure` matched the cover as the first divider whenever a part deck's subtitle
  repeats its first divider's title; fixed in #45.

## 3. Counts

Verdicts on the 208 content slides of the 12 part decks (whole deck excluded, as it repeats
them):

| outputs | format | fits | edge | sparse | overflows (shrunk) |
|---|---|---|---|---|---|
| old (2.8.0) | HTML | 112 | 10 | 82 | 4 |
| | PDF | 129 | 27 | 52 | 0 |
| | pptx | 126 | 21 | 55 | 6 |
| ncar | HTML | 108 | 9 | 87 | 4 |
| | PDF | 111 | 4 | 93 | 0 |
| | pptx | 112 | 7 | 87 | 2 |
| nsi | HTML | 110 | 4 | 92 | 2 |
| | PDF | 111 | 1 | 96 | 0 |
| | pptx | 112 | 3 | 92 | 1 |

Disagreements across formats: old 21, ncar 7, nsi 4. Under ncar they were:

- 4 diagram slides that HTML autofit shrinks to 0.92-0.97 while PDF and pptx fit: 2-concepts
  s20 "Now: jobs live with their machine" and s24 "The verbs", 3-databases s3, 5-deployment
  s3. The old report hinted at the same four.
- 2 caution slides pptx shrank (fixed, #46).
- 1 `.fill` slide (D-security s8).

nsi has the same diagrams (2 of them), one caution slide and the same `.fill` slide.

Body height against HTML's, median [10th-90th percentile]:

| | text (75) | columns (15) | code (11) |
|---|---|---|---|
| old PDF / pptx | 1.21 [1.01-1.47] / 1.20 [1.09-1.41] | 1.16 / 1.20 | 1.42 / 1.33 |
| ncar PDF / pptx | 0.95 [0.94-0.95] / 1.01 [0.98-1.10] | 0.94 / 1.02 | 1.00 / 1.19 |
| nsi PDF / pptx | 0.93 [0.92-0.94] / 1.02 [0.97-1.11] | 0.92 / 0.99 | 1.01 / 1.17 |

The pptx code column is section 5's code-size defect; with it fixed it is 0.93 in both
liveries.

**Title lines** (content slides): HTML 206 single, 2 double under both liveries (the
`.full` slides' captions aside). PDF: ncar wraps one title (2-concepts s22 "replay(history)
== amount: SCSG0001 on Derecho"), nsi none. pptx: ncar none; nsi 3 when the pptx shrink is
off (2-concepts s22, s36, A-peers s7), which spill past the title box (section 5).

**Compositions** (`make measure`, title, divider and closing slides of all 13 decks):

| | html | pdf | pptx |
|---|---|---|---|
| ncar, as first measured | 0/189 | 33/189 | 22/189 |
| ncar, with #45 and #48 | 0/189 | 0/189 | 0/189 |
| nsi, as first measured | 0/336 | 110/336 | 121/336 |
| nsi, with #45 and #48 | 0/336 | 0/336 | 11/336 |

nsi's last 11 are the pptx band title stack, fixed by #47 (measured within tolerance on
2-concepts, the quickstart and the fixtures).

## 4. Before and after (ncar against the old outputs)

- Counts are identical deck by deck, and both sets agree across formats.
- The old outputs disagreed across formats three times as often (21 against 7). Their PDF
  and pptx ran about 20% taller than HTML, and the decks were tuned to the PDF and pptx: the
  old HTML had about as many sparse slides (82) as today's (87). Today the other two formats
  have joined HTML.
- The old report's four autofit hints are the same four diagram slides as today's, at the
  same factors.

## 5. Problems by cause

**Content (too much on the slide): none overflow.** The densest slides (5-deployment s7
"Fourteen workflows", 4-systems s8 "Who's still on legacy", G-cli s5) fit in every format and
both liveries.

**Old tuning (a `scale=` set for the old sizes): the main visible change.**

- 93 sparse slides in PDF under ncar (52 before). They are the `{.vcenter scale="1.15"}`
  slides, now at a median 0.40 of the body.
- Sparsest: 5-deployment s16 "The HPC hosts, too" (0.20), 2-concepts s33 "Usage rolls uphill"
  and s39 "Detach ≠ independence" (0.22).
- Reported, not changed in the source. The lever (section 6) shows a deck-wide step is not a
  substitute for retuning these slides.

**Livery (nsi):**

- **nsi pptx titles use a regular-width face.** HTML and PDF set nsi's headings in Heros
  Condensed. The pptx names Helvetica Neue for everything, at full width, in a title box
  sized for one 32 pt line (0.095 of the height). Three titles that are one line in HTML/PDF
  wrap in pptx and spill out of the box. PowerPoint shrinks them only once edited, so the
  file opens overflowing. Options: name the condensed face for pptx headings (`Helvetica Neue
  Condensed Bold`, which `installed-fonts` already lists), or give the title placeholder a
  two-line height. A livery decision, not made here.
- Fill shifts slightly (text use 0.39 against ncar's 0.40); nothing that collapses. The gold
  fields, 60 pt dividers and 48 pt cover measure clean.

**Framework:**

- **pptx code blocks at the body size** (12 pt ncar, 16 pt nsi), where the livery's `code` role
  (8 pt, 11 pt) sets them in HTML and PDF. pandoc gives code no size. Branch
  `pptx-code-size` adds `style_code.py`; held for a decision because it changes every pptx
  deck's code (section 7).
- **The caution box was cut before `scale=`** (fixed, #46). 2-concepts s23 and 3-databases s15
  shrank to 0.87 and 0.93 in pptx under ncar.
- **The nsi band cover's pptx stack** read date / title / rule / subtitle / author, 0.033 low.
  HTML, PDF and the nsi notes have date / title / subtitle / rule / author (fixed, #47).
- **`.fill` is HTML-only** (known). The 45 `.fill` slides grow 1.5-2x in HTML and stay put in
  PDF and pptx. Worst: 5-deployment s29 "What it hosts", 2-concepts s30 and s35 (HTML 0.89,
  PDF 0.31).
- **Live diagrams** (known, unchanged): HTML draws mermaid and Graphviz live and autofit
  shrinks four of them to 0.92-0.97; PDF and pptx use PNGs and fit.
- **pptx can't grow a title box or shrink a table.** Seen only under the lever (section 6): a
  two-line title spills into the body (HTML and PDF push the body down), and a table grows
  past the body's foot (PowerPoint never shrinks tables). Latent at the decks' own sizes.
- **Beamer's vertical centring** (deferred) is not exercised here: 96 of the 97 SAMuel text
  and column slides are `.vcenter`, so every format centres them.

**Measurement:** the LibreOffice font and profile issues of section 2 (#48 fixes
`comp_measure`), and `comp_measure`'s cover-as-divider match (#45).

## 6. The lever: one deck-wide `type-scale:`

2-concepts (40 content slides) rebuilt at `type-scale: 1.2` and `1.35`, keeping its per-slide
`scale=`. Each cell: sparse slides now fit / slides that now overflow.

| | HTML | PDF | pptx | median text use (H/P/X) | two-line titles (H/P/X) |
|---|---|---|---|---|---|
| ncar, 1 | 18 sparse | 19 sparse | 18 sparse | 0.38 / 0.36 / 0.40 | 0 / 1 / 0 |
| ncar, 1.2 | 7 / 0 | 7 / 0 | 6 / 5 | 0.52 / 0.52 / 0.52 | 3 / 3 / 3 |
| ncar, 1.35 | 12 / 3 | 9 / 5 | 10 / 11 | 0.71 / 0.69 / 0.64 | 8 / 6 / 8 |
| nsi, 1 | 20 sparse | 20 sparse | 20 sparse | 0.35 / 0.33 / 0.38 | 0 / 0 / 2 |
| nsi, 1.2 | 4 / 0 | 4 / 1 | 4 / 5 | 0.49 / 0.46 / 0.46 | 2 / 1 / 3 |
| nsi, 1.35 | 10 / 1 | 5 / 3 | 6 / 10 | 0.62 / 0.55 / 0.56 | 2 / 1 / 7 |

- The step moves every format alike: the medians stay within a few hundredths of each other.
  That is the robustness result again.
- It does not replace the per-slide tuning. The deck's density runs from three short bullets
  to full tables, so any value that fills the short slides overflows the dense ones. At 1.2
  it fixes a third of the sparse slides and breaks none in HTML or PDF. Its pptx breaks are
  two caution boxes (fixed since, #46), one table that grows past the body, and titles
  spilling out of the title box.
- `type-scale` also scales the titles, which is what makes them wrap. A step for the body
  alone would be a different lever; not proposed here.

## 7. Fixes and what is open

| PR | cause | change |
|---|---|---|
| #45 | measurement | `comp_measure` looks for divider, closing and feature pages after the cover |
| #46 | framework | caution box cut after `scale=`; the estimate counts line breaks |
| #47 | framework | nsi band cover: rule between subtitle and author, stack centred |
| #48 | measurement | `comp_measure`'s LibreOffice profile gets the livery's fonts (and stand-in) |
| (held) | framework | `style_code.py`: pptx code at the livery's `code` size |

Open, for Ben:

1. **pptx code size** (branch `pptx-code-size`): every pptx deck's code blocks drop from body
   size to the livery's `code` size (ncar 12 -> 8 pt), as HTML and PDF already set them.
2. **nsi pptx headings:** name the condensed Helvetica Neue for titles, or a two-line title
   box, or leave it.
3. **The scratch measuring scripts** (per-slide verdicts across formats, the ncar-against-nsi
   composer) could become a `utils/` tool (`make verdicts`?). They found everything above that
   `deck_qa` and `comp_measure` did not.
4. **For the SAMuel author** (not changed here): the `scale="1.15"` slides could go to about
   1.4-1.5 to look as they did in the old PDF, or the deck could take `type-scale: 1.2` and
   keep its per-slide values.
