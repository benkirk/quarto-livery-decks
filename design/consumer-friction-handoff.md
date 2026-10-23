# Sprint handoff: the first consumer's friction list (#133)

**For a fresh session.** One PR against `main` (branch `decks/consumer-friction` from `origin/main`
at `642be18`, v26.10.10), a commit per item in the order below, squash-merged once, no version bump
(ask before any tag; the release that follows is 26.10.11). Commit 0 is this file at
`design/consumer-friction-handoff.md`. Read `CLAUDE.md` whole first ("pandoc pptx gotchas",
"Build", "Full-slide figures", "Plots", "Chart colors"), then `design/gallery-handoff.md` for the
shape and house rules. House rules: roles only in theme files; every number from `livery.json`;
one reader, one drawer per format; **no compatibility shims**; American spelling; a CHANGELOG line
per user-visible change; tests under `tmp_path`; a step imports no other step's private name
(`tests/test_cli.py:214`). Line numbers are on `642be18` unless marked *(patch)*, which means the
uncommitted working-tree diff of `grid.py` and `slide_layout.py` (66 lines; `git diff` shows it,
and it is the starting point of commits 2 to 4, not something to redo).

The test case for the whole sprint is the consumer deck
`/Users/benkirk/Documents/CISL_mgmt/allocations/fy27-priorities` (42 slides, ncar livery, a
`Makefile` that includes this checkout's `Make.common`): `make qa` there must come out clean at the
end, and its pptx must open in PowerPoint and Keynote (`tests/app-open.sh` at the release).

## Context: why, and the triage

`fy27-priorities` is the first deck that leans on every element at once (leads, cards, `.full`
figures, tables beside bullets, notes under tables, plots) and it found the pptx seams `make qa`
cannot see. Issue #133 lists 14 items. The triage, with the rationale:

**In this sprint (12 commits), from cheapest to dearest:**

| # | Item | Why now | Size |
|---|---|---|---|
| 14 | last-slide `{.full}` in HTML | one helper, a known cause, also fixes a last feature/agenda slide | S |
| 3 | `use_layout()` crash on a table | two lines, already patched | S |
| 1 | lead after a figure (markers in the caption) | already patched; three fy27 slides; the markers are the only honest signal of the fold | M |
| 2 | lead before a table (Content with Caption) | already patched; two fy27 slides | M |
| 4 | `make qa` ignores "markers left" | the check that would have caught 1; the grep already exists in CI for the sample deck | S |
| 6 | engine edits do not rebuild a deck | one `wildcard` in `DEPS`; every engine sprint has hit it | S |
| 9 | ′ missing in PDF and plots | one `\newunicodechar` line; one rc line (`font.family` as a list) | S |
| 13 | PNG with `sBIT` blank in PowerPoint | the chunk is the only difference between the broken and fixed files (checked); a 20-line chunk filter | S, verify |
| 11 | "runs into the next table column" false positive | standing noise on four fy27 slides and every table-beside-bullets slide; the HTML already knows the table's box | M |
| 10a | image not pullable mid-release | a pre-check and one message; the failure today is docker's own | S |
| 5 | no pptx overflow check | `comp_measure.shoot_pptx()` already does the LibreOffice conversion; lifting it is most of the work. Hints first, failures when the numbers prove quiet | M, may slip |
| docs | 7 documented as unsupported, authoring and formats guides, CHANGELOG | | S |

**Deferred, each with its reason and the follow-up it wants:**

- **7, conditional content** (`::: {.content-visible when-format=}`). Quarto rewrites the Div into
  a classless custom-node scaffold before the engine's filters run (three nested Divs:
  `__quarto_custom`, `__quarto_custom_scaffold`, the author's Div with `content-visible` removed;
  hidden content already emptied). A `flatten_conditionals()` in `engine-common.lua` at every
  format's slide walk would unwrap it, but it deletes nodes Quarto's render stage owns, so it
  needs a `quarto render` in all three formats to prove safe (the pandoc harness cannot). The
  consumer dropped the need. **Follow-up issue**; this sprint documents it as unsupported.
- **8, per-element size** (`.lead scale=`). Every format must grow a new authoring attribute (the
  heading's `scale=` parse in `take_layout` :142-170 is the precedent; pptx would carry it on the
  marker, `parse()` already keeps `k=v` attributes :58-65, and `draw_lead` ignores them :587).
  It is a key a deck author learns, so it is Ben's pick (attribute, or a `lead` type role like
  `quote`'s). **Follow-up, one element sprint**; the raw-inline workaround stands meanwhile.
- **10b, a native env found beside the framework.** `DECKS_RUNTIME=auto` could pick
  `conda run -p <framework>/conda-env --no-capture-output make ... DECKS_RUNTIME=native` when that
  directory exists and `conda` is on PATH (a real activation, which `PATH` alone is not:
  CLAUDE.md "Env"). Changes which toolchain wins over the image. **Ben's pick**; 10a makes the
  failure legible either way.
- **12, named series to livery colors.** The livery knows hues, not a deck's series names; a
  `charts.series: {name: role|hex}` map is a palette-design decision for
  `design/charts-and-plots.md`, and the deck's five-line `fy27/palette.py` is the right answer
  today. **Follow-up with a design note.**

## What the exploration established (anchors for the commits)

- **Filter order** (`_extension.yml` pptx `filters:`): strip-raw-figure, slide-layout,
  inline-footnotes, **grid-pptx**, notes-last, **single-body**, linked-images, diagram-dark.
  grid-pptx writes a top-level `.lead` as paragraphs `⟦engine:lead⟧`, its lines, `⟦engine:end⟧`
  (`grid-pptx.lua:94-96, 231-234`; `split_lines` `engine-common.lua:547-566`). single-body's
  `fold_trailing` :139-174 folds every trailing Para (the markers pass `is_text` :44) into the
  one figure's caption through `caption_lines` :60-68, joined by `LineBreak`, so pandoc writes
  **one centered paragraph with `a:br`** and `grid.py`'s `MARK` :51 (whole-paragraph match on
  `para_text`, which ignores `a:br`) never fires. The fold is what keeps the slide whole
  (anything after a figure splits it), so the pptx step is the right place to split the markers.
- **Step order** (`pptx_post.py:58-66`): style_footnotes, link_captions, slide_layout, columns,
  grid, status_glyphs, style_tables, marking, type_step. `slide_layout.run` :716-722 applies
  `note_style` :203-220 (which calls the private `_split_lines` :185-200, the `a:br` splitter,
  then centers and mutes every line) and `note_place` :241-263 **before** grid runs. So a lead
  after a *captioned* figure (`own_caption` :83-92 marks the slide `note`) reaches grid with its
  lines already centered in the caption role; a lead after a bare plot (fy27's case) does not.
- **Cross-step imports** are allowed when the name is public (`grid.py` already takes `rules`
  from columns and `draw_gallery` from gallery); only `from X import _name` is forbidden.
- **Warnings** are `print(..., file=sys.stderr)` everywhere; `pptx_post.py` reads none. CI greps
  `decks/sample/sample.pptx` for `⟦engine:` (`ci.yaml:177-186`); `deck_qa.py` only counts pptx
  slides (`pptx_count` :361-366).
- **No test runs `single-body.lua`** (it needs `quarto.doc.is_format` and
  `quarto.utils.resolve_path`, :16-20); `tests/test_grid.py` runs `grid-pptx.lua` under pandoc
  with the real template and then the steps in the driver's order (`STEP` :58-64, `deck` :66-78).
- `comp_measure.py` `shoot_pptx` :144-172 already builds the scratch LibreOffice profile with
  the livery's fonts in `user/fonts`, rewrites an unbundled `typeface=` to the base family, and
  runs `soffice --headless --convert-to pdf`; `shoot_pdf` :123-137 rasterizes with `pdftoppm`.
- `deck_qa.py`'s table rule :166-192 runs on PDF text boxes of slides whose HTML `kind` is
  `table` (:83: `table` wins over `columns`), over **every** line below the title, with a
  "column" being any x where three lines start: bullets beside a table are such columns.
- `Make.common` `DEPS` :123 holds no engine source; `livery.py deps` :174-183 lists livery files
  only.
- `DECKS_IMAGE_TAG` defaults to `_extension.yml`'s version (`common/image.mk:9`); `image.yaml`
  pushes that tag only on `v*` tags (:163-176), so between the bump and the tag it does not
  exist; `Make.container` :84-91 prints the image and runs, no pre-check.
- Poppins (all five ncar TTFs) lacks U+2032 ′ U+2033 ″ and the arrows, ⚠ ✓ ✗ ▪ μ. The PDF
  borrows 26A0 2713 2717 25AA 2192 2190 2194 21D2 from DejaVu (`engine_livery.sty:190-210`,
  one `\newunicodechar` each). The mplstyle writes `font.family: sans-serif` and
  `font.sans-serif: Poppins, DejaVu Sans` (`livery_build.py:1301-1309`; asserted at
  `tests/test_charts.py:173`): matplotlib 3.11 builds its per-glyph fallback chain from
  `font.family` only, so DejaVu never joins it.
- The fy27 originals (`git show 3784a06:allocations/fy27-priorities/images/cmip7-*.png`) are
  8-bit RGB with one `sBIT [8,8,8]` chunk; the fixed files differ by that chunk alone.
- Quarto appends `::: {.quarto-auto-generated-content}` (a footer div, a logo when set) to the
  **revealjs** body only (`quarto.js:184482-184511`) and later moves it to `div.reveal`
  wherever it sits (`handleAutoGeneratedContent`). `split_full` `engine-common.lua:400-420`
  admits only `notes`/`hidden` Divs (:406); `agenda_notes` :480-491 warns and drops anything but
  notes; the revealjs feature branch :791-801 puts it in `body`, so a last feature slide with no
  body draws an empty panel (`.engine-feature-body`, scss :1042-1052).

## The commits

**0. The handoff.** This file at `design/consumer-friction-handoff.md`.

**1. Item 14: Quarto's asides ride with the notes.** `engine-common.lua`: `is_aside(b)` (a
`notes`, `hidden` or `quarto-auto-generated-content` Div), exported; `split_notes` :86-92 puts
asides on the notes side; `split_full` :406 and `agenda_notes` :480-491 accept them through it;
`single-body.lua` :23-26 drops its own `is_aside` for `C.is_aside`. Revealjs then renders a last
`.full`, feature or agenda slide right, and the empty feature panel goes. Test: `test_gallery.py`'s
`lua_common` harness gains a case where a trailing `quarto-auto-generated-content` Div follows the
figure (split_full returns the figure) and an agenda body (no warning). The decks stay as they
are: the Lua test and the fy27 deck (its backup ends on two `.full` slides, which `deck_qa.py`'s
HTML `noFigure` check now passes) are the proof.

**2. Item 3 and the lift.** `slide_layout.use_layout()` :313-329 as patched (`p:spPr` looked
up, a graphicFrame skipped). Lift `_split_lines` :185-200 to `pptx_steps/common.py` as
`split_br(txBody)` (public; `note_style` calls it), since commit 3 needs the same splitter.
The patch's `_split_markers` (near-copy, drops `algn`) is not kept.

**3. Item 1: a lead after a figure.** In `grid.run()` *(patch :670-707)*: before parsing, for
each body box, `split_br` the paragraphs that hold `⟦engine:` with an `a:br`, and drop `algn`
from the split lines (the fold centered them); start the flow under the picture when the box
sits below one (*patch* `below`, `+ em(0.5)`), `lay_out` returns its end `y` (*patch* :632).
Guard the captioned case: `slide_layout.note_style` styles only paragraphs outside a
`⟦engine:…⟧ … ⟦engine:end⟧` span (a small `marker_spans(paragraphs)` in `common.py`, next to
`take_marker`), so a figure's own caption lines keep the caption look and the lead is drawn under
them. Sample deck: a slide "A lead under a figure" (the cookbook of every pattern; CI greps its
pptx for markers). Test in `test_grid.py`: markdown with an image whose caption carries the
folded shape (`![⟦engine:lead⟧\` hard breaks `⟦engine:end⟧](p.jpg)`, pandoc writes `a:br` for a
LineBreak in a caption; if pandoc refuses a LineBreak there, extend conftest's `LUA_SHIM` with
`quarto.doc.is_format` and `quarto.utils.resolve_path` and run `single-body.lua` after
`grid-pptx.lua`), asserting the "Lead" group exists, sits below the picture, and
`"⟦" not in slide._element.xml` as `test_lead` :169-189 does.

**4. Item 2: a lead before a table.** *(patch)* in `grid.run()`: a table beside the box
(`beside`) moves the slide onto Title and Content (`use_layout`), the lead lays out at the
layout's body frame (`_body_frame`, rename `body_frame` and put it in `common.py`: it reads the
template, not grid state), the table is `fit_table`'d under the flow, its note anchored at
`GEOM["body-bottom"]`. The note arithmetic (`text_height * SLACK`, `NOTE_GAP`) must not be a
second copy of `note_place` :241-263: give `slide_layout` a public `note_height(note, slide)`
and `foot_note(note, left, width, bottom)` and call them from both. Sample slide "A lead over a
table" (a lead, a four-column table, a `::: note`). Test as commit 3's, asserting the slide's
layout name, the table's width equal to the body's, and the note's top under the table.

**5. Item 4: markers fail `make qa`.** `deck_qa.py`: `pptx_count` becomes `pptx_scan(path)`,
returning the count and the slides whose `a:t` text holds `⟦engine:` (the zip's
`ppt/slides/slideN.xml`, no python-pptx); each is a failure line `pptx sN: markers left`. Drop
CI's sample grep (`ci.yaml:177-186`): `make -C decks/sample qa` now covers it, and every livery
job's `--qa` too. `tests/test_deck_qa.py` gets a pptx case (a slide XML with a marker in a
`tmp_path` zip).

**6. Item 6: the engine is a prerequisite.** `Make.common` :108-123: `ENGINE_FILES :=
$(wildcard $(FRAMEWORK_ROOT)_extensions/engine/*.lua ... /*.py ... /pptx_steps/*.py ... /*.sty
... /*.scss ... /*.html ... /_extension.yml ... /mpl/*.py)` joins `DEPS` (every format: the Lua
and theme files serve all three). `common/utils/deck_qa.py` needs nothing (`qa` is phony).
CLAUDE.md "Fragments are prerequisites" and `docs/formats.md` "Build pipeline" say so. A consumer
on a submodule pin sees no change.

**7. Item 9: the prime, and matplotlib's fallback.** `engine_livery.sty` :200-207: add
`\engine@symbol{"2032}{′}` and `{"2033}{″}` (and μ U+03BC? no: a Greek letter in running text is
the author's font choice; leave it). `livery_build.emit_mplstyle` :1301-1309: `font.family:
<base family>, DejaVu Sans` (the list, so the fallback chain holds both) and keep
`font.sans-serif`; `tests/test_charts.py:173` asserts the new line, and a new test renders
`"′ → μ"` to a PNG under `tmp_path` with the ncar style and checks no `.notdef` boxes
(matplotlib logs "Glyph … missing from font" at WARNING; assert the log is empty). Rebuild
`liveries/*/build/` (`livery build` on each; CI `--check`). HTML needs nothing (the CSS stack
falls back per glyph); pptx is PowerPoint's own fallback.

**8. Item 13: PNG hygiene.** A zip-parts step `png_clean.py` beside `svg_fallback.py`
(`pptx_post.py` :40-44, first among them): for each `ppt/media/*.png`, drop ancillary `sBIT`
chunks by a chunk walk (no re-encode: lossless, 20 lines, no PIL), warn once per file. **Verify
before keeping the commit**: embed the two original PNGs (from the fy27 history) in a quickstart
copy, open in PowerPoint without and with the step; if the originals draw fine, drop the commit
and close the item as not reproduced. Test: a PNG with an `sBIT` chunk through the step loses it
and still opens with PIL.

**9. Item 11: the table rule, column-aware.** `deck_qa.py` `MEASURE_JS` :38-95 reports, with
`kind == "table"`, the table's box as slide fractions (`tableLeft`, `tableRight`); the rule
:166-192 takes only PDF lines that overlap that span (plus an `EDGE`-sized margin) as `body`, so
a bullet column beside the table is outside it. `tests/test_deck_qa.py` gains a case: bullets at
x=40..300 and a table at 320..600 on one page, no finding; a line from the table's first column
running into its second, one finding. The fy27 deck's four findings vanish (check), the sample's
"Campaign quotas and use" slides still pass. `docs/authoring.md` "Checking a deck" :543-544
says the rule is scoped to the table.

**10. Item 10a: a missing image fails with its own words.** `common/Make.container`
`decks-container` :84-91: before `$(DECKS_RUN)`, a `check-image` recipe asks the runtime
(`docker|podman image inspect` locally, else `manifest inspect`; apptainer: the SIF exists or
the `docker://` URL resolves) and fails with: `image <name> is not available: a release's image
appears when its tag is cut; use DECKS_IMAGE_TAG=<YY.MM> (the month's newest) or
DECKS_IMAGE_TAG=latest, or source etc/config_env.sh to build natively`. `docs/container.md`
"Which image" :124-130 gets the sentence. Parses under make 3.81 (the header rule).

**11. Item 5: pptx through LibreOffice in `make qa`.** Lift `shoot_pptx`'s conversion
(`comp_measure.py` :144-172) to `common/utils/pptx_pdf.py` `to_pdf(pptx, livery, out_dir) ->
Path|None` (the profile, the fonts, the typeface rewrite; `None` with a reason when `soffice` is
missing), called by `comp_measure` and by a new `deck_qa.check_pptx()`: the PDF through
`pdf_problems` :195-231 (right edge, footer, overlap; not the table rule) and a contact sheet
`_qa/<deck>-pptx.png` like the PDF's. **Hints, not failures**, in this PR: LibreOffice is not
PowerPoint (no autofit, Liberation for Helvetica Neue and Courier on a Mac), so the numbers must
be watched on the sample, quickstart, fixtures and fy27 first; promote to failures in the sweep
after, with `QA_PPTX_FAIL=1` meanwhile. CI: the image has `libreoffice-impress`, so `make qa`
runs it there already; the Mac needs `/Applications/LibreOffice.app`. If this commit's hints are
noisy beyond a day's tuning, it slips to its own PR and the sprint merges without it.

**12. Docs and the changelog.** `docs/authoring.md`: "Cards and lead boxes" gets "a lead may
follow a figure or precede a table in every format"; a new paragraph under "Front matter and
slide kinds": Quarto's `.content-visible`/`.content-hidden` divs are not supported by the
engine's elements (a `.lead` or `::: note` inside one is plain text, and one after a table
splits the pptx slide); "Checking a deck" lists the pptx marker check and the LibreOffice pass.
`docs/formats.md` "Build pipeline": the engine as a prerequisite, the `png_clean` step.
`CHANGELOG.md` `[Unreleased]`: Decks (14, 1, 2, 4, 6, 9, 11, 5), Plots (9), and under Liveries
"nothing to do" (the builds are regenerated). CLAUDE.md: the steps list (png_clean), "Fragments
are prerequisites", "make qa first". Close #133 from the PR body with the deferred items 7, 8,
10b, 12 opened as their own issues (one each, the design sketch from this file).

## Verification

1. Before commit 1: `source etc/config_env.sh`; `tests/parity.sh baseline` and
   `tests/parity-latex.sh baseline`.
2. After each commit: `python3 -m pytest tests -k <its test>`; at the end `make test`.
3. `tests/parity.sh check`: the only moved pixels are the sample's two new slides (and, with
   commit 1, none in PDF or pptx: the aside is HTML-only).
4. The consumer deck: `make -C /Users/benkirk/Documents/CISL_mgmt/allocations/fy27-priorities
   qa` clean (no table-rule lines, no markers, the pptx hints read), then its pptx opened in
   PowerPoint and Keynote by hand (`tests/app-open.sh` runs on `decks/*/*.pptx`; point it at the
   deck or open it directly). Slides to look at: "Derecho's Track Record", "Running Behind",
   "What We Have to Work With" (lead under a plot), "Broken NSC Promises" and "Decisions Needed"
   (lead over a table), the two CMIP7 `.full` slides (item 13), "Three Options, Month by Month"
   as the last slide of a copy (item 14 in HTML).
5. Commit 6: edit a comment in `pptx_steps/grid.py`, `make pptx` in quickstart rebuilds.
6. Commit 10: `DECKS_RUNTIME=docker DECKS_IMAGE_TAG=0.0.0 make pptx` in quickstart prints the
   message and nothing else.
7. Commit 8's PowerPoint check as written there, before the PR is marked ready.
8. `/pr-review` on the PR, then squash; the release (26.10.11) is a separate PR after
   `tests/app-open.sh`.

## Open questions for Ben

- 10b (a native env found beside the framework through `conda run`): in this sprint or not?
- 8 (`.lead scale=`): attribute on the div, mirroring the heading's `scale=`, or a `lead` type
  role? Either way a follow-up unless you want it now.
- 5: fine as hints first, or hold it for its own PR so the sprint stays about the fixes?
