# Writing a deck

A new deck directory, the per-slide controls (linked images, centering and scaling, shell
chunks), the text sizes and autofit, and `make qa`. The quickstart deck
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

## Centering and scaling a short slide

Six per-slide controls on the heading, each independent, act on the body
(everything but the title, speaker notes and footnotes). The engine's themes draw them
in HTML and PDF; pptx gets them through `slide_layout.py` (step 7 of
[formats.md "Build pipeline"](formats.md#build-pipeline)).

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
body and 22 pt titles. So a slide copied from a built pptx into a hand-made deck on that
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

Pandoc's PPTX writer emits empty `<a:bodyPr/>` on every placeholder,
which corresponds to PowerPoint's "Do not Autofit": long text overflows
the placeholder visually. `enable_autofit.py` rewrites these to
`<a:bodyPr><a:normAutofit/></a:bodyPr>`, which sets the dropdown to
"Shrink text on overflow."

PowerPoint computes the actual `fontScale` only on edit, not on load, so the file opens with
overflowing text; a click into any overflowing cell triggers the recompute and the text
shrinks permanently. Author-side discipline (split walls of text, use columns) beats driving
PowerPoint externally, so nothing is wired up for that.

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
  - HTML content past the right edge;
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
