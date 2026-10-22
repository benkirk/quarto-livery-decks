# Sprint handoff: citations and references in every format

**For a fresh session.** The first of three sprints planned on 2026-10-22 after #129 (this, then
`steps-timelines-handoff.md`, then `agenda-quote-handoff.md`). One PR against `main` (branch
`cite/every-format` from `origin/main` once #129 is merged), a commit per item in the order below,
squash-merged once, no version bump (the release is its own small PR after; ask before any tag).
Start by reading `CLAUDE.md` whole, `design/latex-first-class-handoff.md` (the shape and the house
rules, which bind here too), `_extensions/engine/engine-common.lua` lines 111-156 (the footnote
lift), the two `hoist_footnotes` (`engine-beamer.lua`, `engine-revealjs.lua`),
`pptx_steps/style_footnotes.py`, `slide-layout.lua`, `pptx_steps/slide_layout.py` from `run()`,
`decks/sample/sample.qmd`, `latex/examples/sample.tex`, and this file. Then
`source etc/config_env.sh`, branch, and take the parity baselines (Verification, step 1) before the
first commit. This file is commit 0 at `design/citations-handoff.md`, with the goal paragraph
below. Report at the end of each commit: what moved, what the tests assert, what parity named.

House rules: roles only in theme files; a number every format draws lives in `livery.json` and
one drawer per format reads it; **no compatibility shims**; `liveries/*/build/` is generated,
never edited; American spelling; a user-visible change gets a `CHANGELOG.md` `[Unreleased]` line in
its commit (Decks, Liveries, Plots or LaTeX); a test writes only under `tmp_path`; the house commit
message (a one-line title, a body with the mechanism and the fix, the session's attribution lines).
Every name below is Ben's pick (2026-10-22); do not rename one without asking. Line numbers are on
#129's tip; re-grep before editing.

## The goal, stated (commit 0 carries it)

Ben, 2026-10-22: the project is now a general graphics design framework for technical
presentations, not a deck builder with extras. Commit 0 writes that down, once, where future
elements and sweeps are measured against it:

- `design/engine-and-liveries.md`, a paragraph at its head: *"The engine is a design framework for
  technical presentations. An element (a card, a strip, a status list, a lead, a caution box, a
  steps row, a quote, an agenda) is a brand-neutral structure that meets three rules: one reader
  (`engine-common.lua`) that turns the author's Markdown into the element's data; one drawer per
  format (the revealjs scss and Lua, the beamer theme, a pptx step) that draws it from that data;
  and every number and color it draws from the livery (`roles`, `type`, `boxes`), never from the
  drawer. The Quarto filter and a hand LaTeX author are two clients of the same layer: the theme's
  environments are written as a person writes them, and the filter writes through them."*
- `CLAUDE.md` "What this is", one sentence after the first paragraph: *"The engine is a design
  framework for technical presentations: an element is one reader, one drawer per format, every
  number from the livery (`design/engine-and-liveries.md`, the head)."*

## Context

Facts gathered on 2026-10-22, three of them correcting first assumptions:

- **The engine's filters never see citeproc's output.** Quarto's `resolveFilters` appends
  `citeproc` after the extension's filters (they run inside `main.lua`'s slots), so in all three
  formats the Lua sees `Cite` inlines and the author's *empty* `::: {#refs}` div; the `csl-entry`
  paragraphs exist only for what runs after pandoc: the pptx steps, the beamer theme (Quarto's
  `CSLReferences` partial), the revealjs css. A note-style CSL (citations as `Note` inlines) is out
  of reach without taking citeproc over (`pandoc.utils.citeproc`): a documented limit, author-year
  styles only.
- **HTML footnotes are not a broken extra slide under Quarto.** Quarto's `coalesceAsides` moves a
  slide's `^[...]` into `<aside><ol class="aside-footnotes">` at the slide's foot, numbered
  `<sup>1</sup>`, in Quarto's own look over the engine's footer furniture: a second footnote style.
  pptx makes an extra "Notes" slide at the end and a "1" in the text; beamer writes
  `\footnote<.->[frame]{..}`.
- **The theme already touches beamer's own apparatus**: the `footnote` template
  (`beamerinnerthemeEngine.sty` ~:649-651, no rule, no colors), `frametitle continuation` (:648),
  `bibliography entry author|title|location|note` colors (`beamercolorthemeEngine.sty:54-57`),
  `bibliography item` as `\insertbiblabel` (inner :198). Beamer sets `bibliography entry
  author`'s font at every `\bibitem`, inside Quarto's `CSLReferences` too, so one `\setbeamerfont`
  sizes CSL entries.
- **TeX on the machines**: `biblatex.sty` is on the Mac (Homebrew TeX Live); biber is not, bibtex
  is. The image installs neither biblatex (`texlive-bibtex-extra`) nor biber (`Dockerfile:22`);
  CI rebuilds the image on a Dockerfile change.
- **Markers**: `footnote_marker` assumes 3-byte markers (`engine-common.lua:120`);
  `style_footnotes._split_marker` takes `text[0]`, so any one-character marker works in pptx.
  `take_footnotes` is called only by the two hoists. `engine-common.lua` runs under `pandoc lua`
  given a `quarto` shim (`quarto.log.warning`, `quarto.json.decode`), so its functions can be
  unit-tested without Quarto; no test renders through Quarto today.
- The quickstart hand-rolls one reference as a dagger line (`quickstart.qmd:98`); the sample has
  none. `Make.common:108` FRAGMENTS does not name `*.bib` or `*.csl`.

Ben's decisions (2026-10-22, final): a deck that cites but has no `::: {#refs}` gets a
`## References` slide appended, with a warning; lifted `^[...]` notes continue the printer's
sequence `† ‡ § ¶` after the slide's own dagger lines (a fifth warns and stays pandoc's); the
LaTeX cookbook's biblatex backend is **bibtex** (biber named as the one-line switch); the
reference list is set in the `footnote` type role, text color, 1.5 em hanging indent (no new role,
no `livery build`); the quickstart is untouched.

## The interface, as agreed

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

```latex
\usepackage[style=authoryear,backend=bibtex]{biblatex}   % the cookbook's preamble; biber: backend=biber
\addbibresource{references.bib}

\begin{frame}{Citing sources}
  MPAS solves the compressible equations on a C-grid \parencite{skamarock2012}; see \textcite{knuth84}.
  A footnote citation\footcite{skamarock2012} is beamer's footnote, in the theme's look.
\end{frame}

\begin{frame}[allowframebreaks]{References}
  \printbibliography[heading=none]
\end{frame}
```

The engine adds no class to write: the slide holding `#refs` is the references slide in every
format. A lifted note's in-text mark is a superscript span (`engine-noteref`, in the accent); its
text joins the slide's footnotes under the rule (HTML, PDF) or in place, muted (pptx).

## The commits, in order

### 0. This handoff and the goal

`design/citations-handoff.md`; the paragraph in `design/engine-and-liveries.md` and the sentence
in `CLAUDE.md` ("The goal, stated"). `make test`'s docs gate.

### 1. `^[...]` footnotes become slide footnotes, in every format

- `engine-common.lua`: `MARKERS` (:113) becomes the ordered list `{"†", "‡", "§", "¶"}`;
  `footnote_marker` (:115) and `strip_marker` (:124) match each by its own byte length. New
  `lift_footnotes(blocks)`: the slide's used markers first (`footnote_marker` over the walk
  `take_footnotes` already does), then every `Note` inline outside a `.notes` div, in order,
  becomes `Span({Superscript{Str m}}, {class = "engine-noteref"})` in the text and a `Para`
  `{Str m, Space, …}` of the note's paragraphs' inlines (joined by `LineBreak`) at the slide's end,
  before its `.notes` divs; a note holding a non-paragraph block, or a fifth note, warns and stays.
  `take_footnotes` (:143) calls it first, so both hoists (`engine-beamer.lua:119`,
  `engine-revealjs.lua:332`) lift without a change. Exported.
- pptx: new `_extensions/engine/inline-footnotes.lua` (the per-slide walk `slide-layout.lua`
  uses: `C.content_heading`, `C.is_slide_break`) calling `C.lift_footnotes`; on a plain
  two-column slide the paragraph goes inside the last `.column` (content after `.columns` splits:
  CLAUDE.md "Columns: two tiers"), on a grid slide at the end (where grid.py leaves trailing
  text: verify in the proof; else warn and leave the Note). `_extension.yml` pptx filters: after
  `slide-layout.lua`, before `grid-pptx.lua`, with its comment line. `style_footnotes.py:23`
  `MARKERS += ("§", "¶")`. pandoc's "Notes" slide disappears with the notes.
- HTML: `engine-revealjs.scss` beside the footnotes block (~:504-530): `.engine-noteref { color:
  var(--engine-accent) }`; nothing else (Quarto's `coalesceAsides` finds no `doc-noteref`
  anchors once the Notes are gone).
- Tests, `tests/test_footnotes.py` (new): a `pandoc lua` harness (a script that defines the
  `quarto` shim, `dofile`s `engine-common.lua`, runs `lift_footnotes` over `pandoc.read(md)` and
  writes markdown; `QUARTO_PANDOC` from the env as `conftest` resolves it): a slide with one dagger
  line and two notes yields `‡` and `§` marks and three foot paragraphs; a note inside `.notes`
  stays; a fifth note warns and stays. pptx: `pandoc_deck` of a `§` paragraph, then
  `style_footnotes.style` on it (`sys.path` has the engine).
- Proof: `tests/parity.sh check` identical (no deck has a Note). CHANGELOG Decks.

### 2. The references slide

- `engine-common.lua`: `has_cites(doc)`, `refs_div(blocks)`, `ensure_refs(blocks, meta, level)`
  (the appended `## References` + `::: {#refs}` and the warning `engine: [@..] cited but no
  ::: {#refs}; a References slide was added last`). Called by `slide-layout.lua` (pptx; before
  `take_layout`), `engine-beamer.lua` and `engine-revealjs.lua`, each before its slide walk.
- pptx: `slide-layout.lua:22` `WORDS += "references"`, set when the slide's blocks hold the
  `#refs` div (the walk, not the heading's classes). `pptx_steps/slide_layout.py`:
  `references_style(slide)` beside `note_style`: every body paragraph's runs at
  `Pt(type_pt(LIVERY, "footnote"))`, `a:pPr marL`/`indent` = ±1.5 em of that size (`ppr_place`,
  `common.py:67`), `spcBef` 0.4 em; dispatched in `run()` before `lay_out`; `type_step` scales it
  last as everything else.
- beamer: `engine-beamer.lua`: the heading of a slide holding `#refs` gets
  `add_frameoption(el, "allowframebreaks")`. `beamerfontthemeEngine.sty`:
  `\setbeamerfont{bibliography entry author}{size=\engine@fs{footnote}}` and the same for `title`,
  `location`, `note`; inner theme after :198: `\AtBeginDocument{\ifdefined\cslhangindent
  \setlength\cslhangindent{1.5em}\fi}` (Quarto's partial defines it). The colors at :54-57 stay.
- HTML: `engine-revealjs.lua`'s slide loop adds class `engine-references` to the heading of a
  slide holding `#refs`; scss: `section.engine-references { font-size: 1em }` (undoes Quarto's
  `.smaller` on the title) and `#refs { font-size: calc(var(--engine-type-footnote) * 1em);
  .csl-entry { padding-left: 1.5em; text-indent: -1.5em; margin: 0.4em 0 } }`.
- `Make.common:108` `FRAGMENTS += $(wildcard *.bib) $(wildcard *.csl)`.
- Tests in `test_footnotes.py`: `pandoc_deck` on literal `::: {#refs .references .csl-bib-body
  .hanging-indent}` / `::: {#ref-a .csl-entry}` divs plus a notes line `engine-layout:
  references`, the step run as `test_boxes.py:113-125` does; assert the size and `marL`/`indent`.
  The `pandoc lua` harness: `ensure_refs` adds the slide once, and never when `#refs` exists.
- Proof: parity identical. CHANGELOG Decks.

### 3. The theme for LaTeX authors; the cookbook cites

- `beamercolorthemeEngine.sty`: `\setbeamercolor{footnote}{fg=BrandMuted}`, `{footnote
  mark}{fg=BrandAccent}`; inner :649-651: the `enginefootnotes` rule before a frame's first
  footnote (`\ifnum\value{footnote}=1`), the mark in `\bfseries`. `\AtBeginDocument{
  \@ifpackageloaded{biblatex}{\setlength\bibhang{1.5em}\setlength\bibitemsep{0.4ex}}{}}`.
- `latex/examples/sample.tex`: the preamble lines above, `latex/examples/references.bib` (new:
  knuth84, skamarock2012, an `@online` for Quarto, the sample's three), a "Citing sources" frame
  after Tables and the References frame before `\engineclosingframe`. `overleaf_zip.py`
  `COOKBOOK_FILES += "examples/references.bib"`; `tests/test_cli.py::test_zip_packs` names it.
  `Dockerfile:22` `+= texlive-bibtex-extra` (bibtex is already there). `latex/Makefile`: latexmk
  runs bibtex itself; `clean` covers `.bbl .blg .run.xml -blx.bib`.
- `tests/test_latex.py` `DECK`: a frame with `\footcite` and the References frame, a `.bib`
  written beside the deck by `compile_tex`; the module skips when `kpsewhich biblatex.sty` is
  empty; asserts the citation text on the frame and the entry on the last page.
- Proof: `make -C latex examples variants`; CI's Overleaf step compiles the cookbook on every
  livery (the bib in the zip); `parity-latex check`: the cookbook gains two pages, nothing else
  moves. CHANGELOG LaTeX.

### 4. The sample deck and CI

- `decks/sample/sample.qmd`: `bibliography: references.bib` in the front matter, "Citing
  sources" after Tables, "References" (with `::: {#refs}`) before "Thank you!";
  `decks/sample/references.bib` (the same three entries). CI's sample job: `grep -q
  'engine-references' sample.html`, `pdftotext sample.pdf - | grep -c Skamarock`, the python
  block asserts a pptx paragraph starting "Knuth" at the footnote size.
- Proof: `make -C decks/sample all qa` (counts agree: +2 in every format); the three References
  slides looked at; `tests/parity.sh check`: the sample's two slides appear, nothing else moves.
  CHANGELOG: none (the sample is the proof).

### 5. Documentation

`docs/authoring.md`: a section "Citations and footnotes" after "Notes under a figure": the front
matter, `[@key]`, `^[...]` and its markers, the References slide, the generated one, the limits
(author-year CSL only; pptx shows the rendered cite as text). `latex/authoring.md` "The patterns"
rows for `\footcite` and `\printbibliography`, and "Out of scope" loses nothing. `docs/formats.md`
names `§ ¶` where it names `† ‡`. `CLAUDE.md`: "Slide footnotes" grows the lift and the four
markers; a **Citations** bullet after it; the test list names `test_footnotes.py`; the pptx filter
list comment in `_extension.yml`. `make test`'s docs gate.

## Verification

1. Before commit 1, on `origin/main`: `tests/parity.sh baseline` (ncar cu nsi) and
   `tests/parity-latex.sh baseline`, same checkout, same day.
2. Every commit: `make test`.
3. `tests/parity.sh check` after 1 and 2: identical; `parity-latex check` after 3: two cookbook
   pages; `parity.sh check` after 4: the sample's two slides, nothing else.
4. Commit 4: `make -C decks/sample all qa`; `make -C decks/sample overleaf`, unzip in a clean
   directory, `env -u TEXINPUTS -u TTFONTS latexmk -xelatex sample.tex` builds with its bib.
5. pptx changes land in the sample: `tests/app-open.sh` at the release. The PR body: a section
   per commit, the parity results, the three References slides; `/pr-review N` before Ben merges.

## Risks

- A lifted note on a grid slide: where grid.py leaves trailing text is unverified (commit 1's
  proof; the fallback is to warn and leave the Note on such a slide).
- `allowframebreaks` on the engine's `[t]` frames with waves and the marking strip: look at the
  continuation page's furniture and "(2)".
- Quarto's `handleRefs` also adds `scrollable` to the HTML refs slide; check it under the autofit
  script.
- The `pandoc lua` harness is new to `tests/`; it needs `QUARTO_PANDOC`, which conftest resolves.
- biblatex is absent from the image until the Dockerfile lands and the image rebuilds: commit 3's
  CI run is the proof of that too.

## Deferred, for all three sprints (recorded here once; the ledger's Open list when this PR opens)

Chevron steps (`style="chevron"`), alternating timeline labels, subsections in the agenda,
`agenda: each`, the quote's quotation-mark glyph, `current=` on the agenda, a note-style CSL
(needs citeproc in the filter), callouts reaching pptx as a native shape, stat tiles as a card
preset, an image grid with captions (after the grid step's picture limit), editable pptx charts
from data, icons in pptx.

## Memory for the fresh session

`~/.claude/projects/-Users-benkirk-Documents-quarto-livery-decks/memory/`: `no-compat-shims.md`,
`minimal-prs-versions.md`, `approval-text-in-chat.md`, `american-spelling.md`,
`sprint-tags-recut.md`, `latex-first-class.md`, `design-framework-goal.md`,
`next-sprints-after-129.md`. After the PR opens, update `next-sprints-after-129.md` (what landed,
the squash SHA when Ben merges) and its index line.
