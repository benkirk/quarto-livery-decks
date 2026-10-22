# Writing a deck

A new deck directory, the front matter and the slide kinds, the per-slide controls (linked
images, notes under a figure, centering and scaling, columns, cards and lead boxes, shell chunks), the text sizes and autofit, and `make qa`. The quickstart deck
(`decks/quickstart/quickstart.qmd`) is the one to copy; `decks/sample/sample.qmd` shows every pattern.

## Adding a new deck

```bash
cd decks
mkdir roadmap && cd roadmap

cat > Makefile <<'EOF'
include ../../Make.common
EOF

# then author roadmap.qmd. _quarto.yml is auto-symlinked from
# ../../common/_quarto.yml on first `make` invocation.
make pptx
```

`Make.common` infers the deck name from `$(notdir $(CURDIR))`, so the
output file is `<dirname>.pptx`. Override with `OUT=foo` if needed.

A directory can hold several decks that share images and fragments, e.g. a
full deck plus one deck per part:

```make
DECKS := roadmap 1-intro 2-details
include ../../Make.common
```

Each `<name>.qmd` builds `<name>.pptx` / `.html` / `.pdf`, and `make pptx`
builds all of them. Put shared slide bodies in `_*.qmd` fragments and pull
them in with `{{< include _1-intro.qmd >}}`; quarto skips underscore files
when rendering, and make treats every `_*.qmd` and `data/*` in the directory
as a prerequisite of every deck, so editing one rebuilds them all.

A deck that needs custom Quarto config (a different reference template,
extra extensions, etc.) can replace the symlinked `_quarto.yml` with a
real file: `make` sees the file already exists and skips the symlink
recipe.

## Front matter and slide kinds

**Theme options** go in a deck's front matter: `themeoptions: [title=light, fonts=bundled]`. A
deck-level list replaces the shared one, so keep `fonts=bundled` (from the shared
`_quarto.yml`): it pins the livery's bundled fonts and never probes for a system copy
(`fonts=brand` uses an installed brand face instead; see
[formats.md "Installed brand fonts"](formats.md#installed-brand-fonts)).

- `titlegraphic: images/photo.jpg` puts a photo on the title slide, in every
  format, where the livery's title composition places it. Without one the livery's
  default appears (`art.titlegraphic`: ncar's Mesa Lab, nsi's campus, nasa's Earth
  limb); `titlegraphic: none` keeps the plain cover.
- `fineprint: "..."` adds small print under the title block.
- `marking: "CUI"` (any text) puts a marking strip on every slide, in every format: a
  restriction or distribution marking. Where it sits, how wide, its fill and its colors are
  the livery's `marking:`, and a livery may set default text every deck under it shows
  (nasa-jsc-eg does); `marking: none` turns a livery's default off.
- `mathfont=stix` (or `lm`, `pagella`, `sans`, `fira`, `poppins`, any
  OpenType math font) changes the math font; the default is New Computer
  Modern Math, scaled to sit with the text font. Quarto's own `mathfont:` key
  also works. [latex/README.md "Math fonts"](../latex/README.md#math-fonts) shows every preset on one slide.
- `waves=false` removes the faint wave lines behind content slides of a
  livery that has them (they are on the pptx master too).

**Slide kinds**, by a class on the heading (the quickstart deck shows each):

- `## Title {.feature background-image="images/photo.jpg"}` makes a
  full-bleed photo slide (`background=` also works; `background-image=`
  doubles as the revealjs background). Its look is the livery's `feature.style`:
  `bar` (the title on a dark bar, the text on a translucent panel; the default) or
  `cover` (the title cover's field and waves, the photo beside them), in every format.
- `## Title {.full}` gives one diagram or image the whole slide: no title,
  logo or rule, and the paragraph after it (or a `::: note`) becomes a one-line caption. The
  title stays in the source for navigation and `make qa`. pptx gets it
  from `slide_layout.py`.
- `# Backup {.unnumbered}` is a section divider outside the count, in every format: no
  "SECTION n" over it, and the dividers after it keep their numbers. A paragraph right after it
  is its subtitle, as under any divider. In the PDF it has no bookmark.
- `## Thank you! {.closing}` makes a closing slide.
- `### Heading {.example}` / `{.alert}` give block variants.
- `[text]{.alert}` emphasizes text.

## Linked images

Wrap an image in a link and the picture opens that page, in every format:

```markdown
[![](images/dashboard.png){height="72%" fig-align="center"}](https://example.org/dashboard)
```

Each format also shows the URL, small and muted, so a reader knows the
picture is live: the slide footer in HTML, a line at the foot of the PDF page
(the engine's `linked-images.lua`), and a caption box in pptx (`link_captions.py`;
pandoc can't add one without splitting the slide). One line per slide, from
its first linked image. `{height="72%"}` is the full-width screenshot recipe
and fits all three.

## Columns

`:::: {.columns}` with a `::: {.column}` per column lays them out side by side, alike in every
format: each column takes its `width=` share of the row less the livery's gap, and a column
without a width takes an equal share of what is left.

```markdown
:::: {.columns}
::: {.column width="67%"}
- The wider column
:::
::: {.column}
![](images/example.jpg)
:::
::::
```

- **Two columns** are pandoc's own two-column layout in pptx, set to their widths after
  rendering; a picture or table in a column moves and scales with it.
- **Three or more columns** are drawn in pptx as text boxes at the same widths (pandoc's pptx
  keeps only two). First-cut limit: a picture or table in one of them is not drawn in its
  column yet; the render warns, naming the slide, and pandoc splits the slide (`make qa`'s
  slide count catches it). Put pictures and tables on a two-column slide.
- **`{.wide}`** on the heading widens the body to the slide less a narrower margin
  (`geometry.wide-margin`), in every format: the deliberate way to room for four columns or a
  wide table.
- A livery may draw a **rule** between columns (`boxes.columns.rule`; nasa-jsc-eg does).
- In pptx, text after a picture in a column is dropped by pandoc; keep it above the picture.

## Cards and lead boxes

A lead box over a row of cards is a slide of options side by side:

```markdown
::: {.lead}
**Three ways to spend the next allocation**
Each trades local capacity against a share of the consortium system.
:::

:::: {.columns}
::: {.column .card .pick}
### OPTION 1
[A modern GPU system]{.sub}

**Total cost $30M**
[Local investment]{.label}
[$20M]{.big}

::: {.strip role="accent"}
→ **$10M** to the consortium
:::

- [x] Data archive expansion
- [!] High-resolution runs
- [-] Interactive analysis
:::
::: {.column .card}
...
:::
::::
```

- **`::: {.lead}`** sets its lines on the livery's lead fill with an accent bar at its left.
  In a lead and in a card each source line is a line: no blank line between the bold headline
  and the line under it.
- **`.card`** on a column draws a head band in its `role=` (any livery role) over a body. A card
  without one takes the livery's `boxes.card.roles` in turn by its place in the row (by default
  primary, secondary, accent), so a row's cards differ. The `###` is the band's title, a `[...]{.sub}` paragraph right after it the band's
  second line. `.pick` outlines the chosen card; `.solid` makes the whole card the role's color,
  its text white. A row's cards are one height.
- **`[...]{.label}`** is a small capitals label, **`[...]{.big}`** a big number, each on a line
  of its own.
- **`::: {.strip role="accent"}`** is a band tinted in its role, across the card (or on its own,
  across the body).
- **Status items.** In a card or a `::: {.status}` list, `- [x]`, `- [!]` and `- [-]` show ✓, ⚠
  and ✗ in the livery's status colors where the bullet was, a failed item's text muted. A
  literal ✓ ⚠ ✗ first in an item works anywhere. `- [ ]` stays an unchecked task box.
- pptx draws cards, leads and strips as native shapes and text boxes, editable in PowerPoint:
  each is one group ("Card 1", "Lead"), so a click selects it whole and a second click its text.
  The first-cut limit of three columns holds for cards: no picture or table in a card (the PDF
  draws a row with a table as plain columns). A lead beside a table goes in the title or the
  notes: a lead makes the slide a card slide, and the table would split it. A card slide's
  `.caution` and `.vcenter` do not apply in pptx.
- The same slide in LaTeX is [latex/authoring.md "Cards, strips and status lists"](../latex/authoring.md#cards-strips-and-status-lists).

## Quotes

A quotation is a `quote` div, or a bare `>` blockquote, anywhere in a slide's body:

```markdown
::: {.quote role="accent"}
The purpose of computing is insight, not numbers.
— Richard Hamming, 1962
:::

> A bare blockquote is the same box, in the livery's bar color.
```

- Its lines are set in the livery's `quote` size (24 pt on the default canvas) beside a bar at
  its left, with no fill. `role=` colors the bar (any livery role or blend); without it the bar
  takes the livery's `boxes.quote.bar-color`, by default `primary-contrast` (the primary that reads
  on the background). A `role=` you pick should read on the background too: a thin bar in a light
  role fades on white. Each source line is a line, as in a lead.
- Its face is the body's unless the livery names one: `boxes.quote.family` (a family the livery
  bundles in `_brand.yml`'s `typography.fonts`) and `boxes.quote.style` (`normal` or `italic`),
  in every format; PowerPoint sets it in `pptx.quote-typeface` (by default the family's name, so
  install the face or name an installed one). The attribution stays in the body's face.
- A last line that starts with `—`, `–` or `--` is the **attribution**: set under the quote at the
  caption size, muted, after "— ". A last line that begins with a dash for another reason is
  read the same way, so reword it.
- A quote works on its own, in a column and in a card (inside the card's pads). Inside a lead or a
  strip it is not drawn (those are boxes of lines already): a warning, and its lines stay. In the
  speaker notes a `>` stays as it is.
- pptx draws it as a text box and a bar, one group ("Quote"); a quote in a column makes the slide
  a card slide (drawn by the engine, like three columns), so keep pictures and tables off it.
- In LaTeX it is `\begin{enginequote}[role=accent]{Richard Hamming, 1962}`
  ([latex/authoring.md](../latex/authoring.md#the-patterns)).

## Agenda

An agenda slide lists the deck's numbered sections; the engine writes its body:

```markdown
## Agenda {.agenda}

# Basics

A paragraph right after a divider is its subtitle, and the agenda shows it too.

...

# Wrap-up

## Where we are {.agenda}
```

- **`{.agenda}`** on a slide heading with an empty body draws a row per numbered section: its
  number beside its title, the divider's subtitle under it. Speaker notes stay; anything else in
  the body warns and is dropped.
- **By position.** Up front (before the first divider) every section is upcoming. Placed in a
  section, that one is current (bold, in the livery's `boxes.agenda.current-color`), the earlier
  ones are done (muted) and the later ones upcoming. The numbers take `boxes.agenda.number-color`;
  both are `primary-contrast` by default, the primary that reads on the background.
- An unnumbered divider (`# Backup {.unnumbered}`) is not on the agenda.
- pptx draws the rows as text boxes, one group ("Agenda"); a long agenda that runs past the slide
  loses its subtitles there, with a warning. The PDF draws it from beamer's table of contents,
  which a second LaTeX run fills (Quarto's build reruns for it).
- In LaTeX it is `\engineagenda` in a frame ([latex/authoring.md](../latex/authoring.md#the-patterns)).

## Steps and timelines

A process, step by step, is an ordered list in a `steps` div; milestones are a bullet list in a
`timeline` div:

```markdown
## A process, step by step

::: {.steps}
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

- Both draw a thin rail across the row, the items at equal widths with the columns' gap between
  them. A step gets a numbered badge on the rail, its title bold under the badge and its text
  below; a milestone gets a dot, its date bold above the dot and its label below.
- **The first bold run of an item is its title** (a step's) **or its date** (a milestone's); the
  rest of the item is the text, and in it each source line is a line, as in a card.
- **`- [x]`** marks a milestone done: its dot is filled. A plain item (or `- [ ]`) is still to
  come: its dot is hollow. `[!]` and `[-]` mean nothing on a timeline; they warn and draw hollow.
- **`role=`** colors the badges and dots. Without it they take the livery's `primary-contrast`,
  the primary that reads on the slide's background (on a dark livery the primary itself does
  not), and a badge's number is knocked out in the background color. A role you pick should read
  on the background too: a light one on a light livery makes faint marks.
- **Limits:** at most six items; text only (a list in a step is fine, a picture or table is not);
  never inside a card or a column. Anything else in the div, the wrong kind of list or a seventh
  item, warns and leaves the div as plain content. A longer process goes on over a second slide
  whose list starts at `7.`: the badges follow the list's numbers. Keep a step to two or three lines: the row is
  as tall as its tallest step, and a long one crowds the slide in pptx and overflows in the PDF.
- pptx draws each as native shapes, one group ("Steps", "Timeline"; inside it "Step 1 badge",
  "Step 1 text", "Milestone 1 dot", "Milestone 1 title", "Rail"), so a click selects the whole
  row and a second click a part. A slide with one is a grid slide, as a lead makes it: a picture
  or table beside it splits the slide.
- The same slides in LaTeX are [latex/authoring.md "Steps and timelines"](../latex/authoring.md#steps-and-timelines).

## Notes under a figure

A remark that belongs to a figure or table, a summary line or where its numbers come from, goes
in a `note` div right after it:

```markdown
## Campaign quotas and use

![](images/capacity.png)

::: note
121 PiB used of 141 PiB; quotas total 166 PiB, 1.24x the 95% line.
:::
```

Every format draws it as the figure's caption, as a `{.full}` slide draws its caption: the
caption size, the livery's muted color, centered, just under the figure. In pptx the engine's
`single-body.lua` folds it into pandoc's caption box, and `slide_layout.py` sets its look and
moves the box up under the picture or table, shrinking a picture that would leave it no room. A
note may hold several paragraphs. A `†` line in it or after it stays a footnote: HTML and PDF
move it to the slide's foot, pptx sets it on the left under the note. A cell prints one with
`#| output: asis`: `print("\n::: note\n" + summary + "\n:::\n")`.

Put it after the slide's one figure or table: anywhere else pptx shows it as body text. Without
the div, a paragraph after a figure is body text in HTML and PDF, and in pptx it joins the
caption box at body size.

A figure's own caption (`![A caption](x.png)`) has the same look in every format, note or not:
the caption size, muted, centered, just under the picture, with no "Figure 1:" label in the PDF.
A note follows it in the same look, so the two read as one block. A table and its caption
(`: A caption` after the table) are centered in every format too, the caption in the same look:
under the table in HTML and pptx, above it in the PDF, where beamer puts a table's caption.

## Citations and footnotes

A deck cites from a bibliography beside it, as any Quarto document does:

```markdown
---
bibliography: references.bib      # beside the .qmd; csl: optional (author-year styles only)
---

## Citing sources

MPAS solves the compressible equations on a C-grid [@skamarock2012]; see also @knuth84.
A footnote citation^[Skamarock et al. (2012), eqs. (3)–(7).] lifts to the slide's foot.

† A dagger line is still a slide footnote; a lifted note takes the next marker (‡).

## References

::: {#refs}
:::
```

`[@key]` cites in parentheses, `@key` in the text. The slide that holds `::: {#refs}` is the
references slide in every format: the entries in the footnote size, each hanging by 1.5 em, 0.4 em
apart. In the PDF its frame breaks over as many pages as the list needs, titled "References (1)",
"References (2)". A deck that cites but has no `::: {#refs}` gets a References slide last, with a
warning (`reference-section-title:` names it; `suppress-bibliography: true` leaves it out). A
`[@fig-x]` cross-reference is not a citation. Editing the `.bib` (or a `.csl`) rebuilds the deck.

**Slide footnotes.** A paragraph that starts with `†`, `‡`, `§` or `¶` is a slide footnote: HTML
and PDF move every one on a slide (in a column or a div too) to its foot, under a short rule, the
marker in the accent; pptx cannot move content, so it mutes them in place. A `^[...]` note is one
too: it takes the next of those markers after the slide's own dagger lines, leaves the marker as a
superscript in the text, and joins them, so a deck has one footnote look in every format (pptx no
longer makes a "Notes" slide at the end). On a two-column slide pptx puts it at the foot of the
last column. A note in the speaker notes stays as pandoc writes it; a fifth note on a slide, or one
holding more than paragraphs (a list), warns and stays as pandoc writes it.

Limits: author-year styles only (a note style, whose citations are footnotes, would need the
engine to run citeproc itself); pptx shows a citation as text, not a link. A very long list in
HTML shrinks to the autofit floor and then scrolls; split it over two slides.

## Centering and scaling a short slide

Six per-slide controls on the heading, each independent, act on the body
(everything but the title, speaker notes and footnotes). The engine's themes draw them
in HTML and PDF; pptx gets them through `slide_layout.py`, a step of the
[build pipeline](formats.md#build-pipeline).

```markdown
## Who's still on legacy {.center scale="1.4"}
## A short script {.hcenter .fill}
```

| Control | HTML | PDF | pptx |
|---|---|---|---|
| `.hcenter`: center the body across as a block | yes | prose, lists, plain code (a table centers anyway) | no |
| `.vcenter`: center it between the title and the floor | yes | yes | text yes; a table to its measured center |
| `.center`: both (the theme's, not Quarto's) | yes | yes | as `.vcenter` |
| `scale="S"`: text, tables and code × S | yes (autofit shrinks an overshoot) | yes (no autofit: check the page) | yes |
| `.fill`: grow until it just fits, up to 3× | yes | no; add `scale=` | no; add `scale=` |
| `.caution`: the body on a soft field with a bar in the warning color, for warning slides | yes | yes | yes; the box cut to its measured text, footnotes inside it |

## Executable shell chunks

Quarto can capture the live output of a shell command at render time:

````markdown
```{bash}
#| echo: true
which mpicxx && mpicxx --version
```
````

Both the command and its captured stdout land on the slide. This needs
the Jupyter `bash` kernel, which `make conda-env` installs and registers
into the env (`bash_kernel` pip package + `python -m bash_kernel.install
--sys-prefix`). The deck's frontmatter must opt in:

```yaml
engine: jupyter
jupyter: bash
```

Code runs on the build host, not the viewer's machine: output is baked
into the .pptx.

## Text sizes and the slide size

Each livery states its text sizes in whole or half points on its PowerPoint canvas, from the
brand's own template or deck. ncar uses the NSF NCAR template's 10 x 5.625 in slide, with a 12 pt
body, 12/11/10/9/8 pt list levels, 20 pt slide titles and a 22 pt cover title. cu and nsi use
the NSI deck's 13.33 x 7.5 in slide, with a 16 pt body, 32 pt titles and 60 pt dividers. nasa
and nasa-dark use the NASA Science public-engagement deck's 10 x 5.625 in slide, with a 12 pt
body and 22 pt titles; nasa-jsc-eg its division template's 13.33 x 7.5 in slide, with a 16 pt
body and 32 pt titles, in Arial. So a slide copied from a built pptx into a hand-made deck on that
template keeps its geometry and its round sizes. HTML and PDF set the same sizes as the same
share of the slide, so a slide fits, or overflows, alike in all three. `scale="S"` on a slide
sizes it in every format, and PowerPoint's sizes round to the half point.

A whole deck can step its sizes down (or up) from the livery's, in all three formats:

```yaml
type-body: 10      # the body in points; every size scales by 10/12 under ncar
# type-scale: 0.85 # or a plain factor (type-body wins if both are set)
```

The NSF NCAR guide's "10 pts for three and four column layouts" is `type-body: 10`. PowerPoint
gets every size rounded to the half point (`type_step.py`), and a slide's `scale=` multiplies
on top. In plain LaTeX or Overleaf, the theme option `typescale=0.85` does the same. A livery's
sizes live in its `livery.yml` (`type:`, `pptx.size`; `livery_build.py`'s `TYPE` lists the roles).

## About text autofit

Pandoc leaves every pptx text box on "Do not Autofit", so the post-render step
`enable_autofit` sets "Shrink text on overflow". PowerPoint applies the shrink only on edit,
not on load: the file opens with the text overflowing, and a click into the box shrinks it
for good. Splitting a wall of text, or using columns, beats either.

The HTML deck fits itself: a content slide that runs past the bottom margin
shrinks its body text (down to 65%) until it fits, keeping the title size.
`{.smaller}` sets a slide smaller from the start:

```markdown
## Wall of text {.smaller}
```

PPTX silently ignores `{.smaller}`; revealjs honors it. Opt a slide out of
the HTML autofit with `{.no-autofit}` (or `{.scrollable}`), or a whole deck
with `themeoptions: [autofit=false]`. Beamer never shrinks overflowing text: add
`{.shrink}` to a dense slide's heading to scale that one slide down (pptx ignores the
class), or check it with `make qa`.

## Checking a deck

`make qa` builds every format, then checks the outputs (`common/utils/deck_qa.py`):

- **Failures:**
  - slide counts that differ between pptx, PDF and HTML;
  - PDF text past the right margin, into the footer, overlapping other text, or running into
    the next table column;
  - HTML content past the right edge, a `{.full}` caption that wraps, and a `::: note`
    paragraph that wraps (each is one caption line);
  - a bare `<word>` in the sources, outside code and backticks: revealjs reads it as a tag
    (reported as `file:line`).
- **Hints:**
  - short slides, with the share of the body they use;
  - `.smaller` without `.fill`;
  - slides the HTML autofit had to shrink.
- **Plain names:** list names that belong in backticks in `qa-names.txt` (one per line) in
  the deck directory, and every plain-text use is reported.

Everything lands in `_qa/` (gitignored): `report.txt`, `usage.tsv`, a contact sheet per
format, and per-slide PNGs. In a directory with several decks, `make qa DECKS=name`
checks one.

`make measure` checks the slides a livery composes, the title, divider, feature and closing
slides, against their **compositions**: the boxes in the livery's `build/livery.json` that
say where each one's field, photo, marks and text go, which every format draws from. It
shoots those slides in all three formats, measures every edge against its box and writes
`_qa/measure.tsv` and a contact sheet, `_qa/compositions-<livery>.png`; `MEASURE_FAIL` names
the formats whose misses fail the run.

The checks need poppler, Pillow and Playwright, which are all in `conda-env.yaml`
(`make measure` also LibreOffice, to shoot the pptx). `make conda-env` installs Playwright's
headless Chromium; set `CHROME` to use another build. Without Playwright the HTML checks are
skipped and the rest run. For Claude Code, the `deck-polish` skill (`.claude/skills/`)
covers what to do with the findings.
