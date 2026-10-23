# Sprint handoff: LaTeX authors first-class

**State (2026-10-22):** landed as #129, squash `cedc348`, released as 26.10.8 (#130). Departures: the review's three fixes (a16a9de, b48f1ff, 5ce634d); `tests/parity.sh` folds the plots' SVG `<dc:date>` stamp; the cookbook's 4:3 variant sets no overfull line and CI's ratchet covers every `sample*.log`.

**For a fresh session.** One PR against `main` (branch `latex/first-class` from `origin/main` at
`f54d050`, the 26.10.7 release), a commit per item in the order below, squash-merged once, no
version bump (the release is its own small PR after; ask before any tag). Start by reading
`CLAUDE.md` whole, `latex/README.md`, `_extensions/engine/beamerinnerthemeEngine.sty` from line
296, `engine-beamer.lua` (`beamer_columns`, `card_rows`, `status_items`, `strips`,
`lead_boxes`, `unwrap_layout`, `SCALE_TEX`), `decks/sample/sample.qmd`, and this file. Then
`source etc/config_env.sh`, `git checkout -b latex/first-class origin/main`, and take the parity
baselines (Verification, step 1) before the first commit. This file is the first commit, at
`design/latex-first-class-handoff.md`. Report at the end of each commit: what moved, what the
tests assert, what parity named.

House rules that bind here: roles only in theme files (no palette name or hex); a number every
format draws lives in `livery.json` and one drawer per format reads it; **no compatibility shims**
(Ben is the only consumer: when an environment's interface changes, the filter moves onto it in
the same commit and the old form is gone); `liveries/*/build/` is generated (`livery build
liveries/*/`), never edited; American spelling; a user-visible change gets a `CHANGELOG.md`
`[Unreleased]` `### LaTeX` line in its commit; a test writes only under `tmp_path`; the house
commit message (one-line title, a body with the mechanism and the fix, the session's attribution
lines). Every new command name below is Ben's pick (2026-10-21); do not rename one without asking.

Line numbers are on `f54d050`; re-grep before editing.

## Context

Everything since #126 already works from plain LaTeX: the filter writes ordinary environments,
and a hand-written deck (`~/.claude/plans/latex-first-class/probe.tex`, `steps.tex`; sheets
`sheet.png`, `picks.png`) compiled under ncar with cards, a lead, strips, status items, weighted
columns, a caution box, a note, and overlays inside cards (`\item<+->`, `\pause`, `\uncover`; a
pick moved across steps by `\alt`). What is missing is the person-facing half:

- **The interface was written for the filter.** `\begin{enginecard}[pick]{BrandSecondary}
  {0.3333}{3}{Title}{Sub}` (inner `.sty:392`) takes a TeX color and two numbers the filter
  computes; the default role by place in the row is `engine-beamer.lua:285`, not the theme;
  `livery.sty` carries neither the role table nor `boxes.card.roles` (`livery_build.py:871`
  skips it: "read from livery.json by the filters"). A status item is
  `\item[{\textcolor{EngineGlyphDone}{\bfseries ✓}}]` (`lua:329`), beside an older, unused
  `\cmark`/`\xmark`/`\pmark` (`engine_livery.sty:333-336`, pifont, on the ledger's Untriaged
  list). The filter defines private macros in the preamble (`SCALE_TEX`, `lua:405-420`;
  `\gdef\enginemarkingtext`, `lua:695`), so a hand author cannot scale a body or set the marking.
- **Undocumented.** `latex/README.md` "Writing slides in LaTeX" (`:85-109`) stops before #126:
  no columns, wide, cards, lead, strip, status, caution, note, marking, scale.
- **A theme nit, diagnosed.** The 6.07 pt overfull "in paragraph" on a card row is the **strip
  inside a card**: `enginestrip` (inner `:358-366`) widens `\linewidth` by two card pads and
  sets `\engine@barboxin` to `\hspace*{-padx}`, so the strip's line measures `hsize + padx`;
  6.07 pt is 0.8 em at ncar's 7.58 pt body (the log's line shows `\hspace*`'s zero-width rule
  and the box). beamer re-reads the frame body, so the log blames `\end{frame}`.

Ben's decisions (2026-10-21, final): a hand-written LaTeX twin of the sample deck with
documentation; a LaTeX-friendly layer, the filter its first client; diagrams and the other
Quarto-only features out of scope, each with one sentence and the LaTeX way. Picks: card
`{Title}{Sub}` both mandatory; `enginestatus` with `\done`/`\warn`/`\fail` and `\engineglyph`,
the `\cmark` family retired; `role=` takes a role, a blend or any defined color; a new
`latex/authoring.md`; the cookbook is `latex/examples/sample.tex` beside `template.tex`; the
Overleaf zip ships it; a committed contact sheet; a LaTeX compile test in pytest;
`enginecolumns`/`\enginecolumn` for hand authors, the filter keeping pandoc's columns on the
primitives. Key-value machinery: **pgfkeys** (tikz and tcolorbox already load it; the kernel's
`\DeclareKeys` is built for package options and reads worse in a document body).

## The interface, as agreed

```latex
\begin{enginecards}{3}                      % {3}: three equal cards; {2,1,1}: weights; numbers that
                                            % add to 1 or less are shares of the row (the filter's rule)
  \begin{enginecard}[pick]{OPTION 1}{A modern GPU system}         % role by place: primary
    \enginelabel{Local investment}\enginebig{\$20M}
    \begin{enginestrip}[role=accent]→ \textbf{\$10M} to the consortium\end{enginestrip}
    \begin{enginestatus}
      \done Data archive expansion
      \warn<2-> High-resolution runs                                % overlay spec as on \item
      \fail Interactive analysis                                    % text muted, as HTML and pptx
      \item An ordinary bullet
    \end{enginestatus}
  \end{enginecard}
  \begin{enginecard}[role=secondary, pick=<2>]{OPTION 2}{Join the consortium} ... \end{enginecard}
  \begin{enginecard}[solid]{OPTION 3}{} ... \end{enginecard}      % no sub-line: {}
\end{enginecards}

\begin{enginecolumns}{2,1}                  % over beamer's columns[T,onlytextwidth] and \column
  \enginecolumn The wide column.
  \enginecolumn The narrow one.             % the livery's gap, and its rule when it has one
\end{enginecolumns}

\begin{enginescale}{1.4} ... \end{enginescale}   % the filter's scale=, now a theme environment
\enginemarking{CUI}                               % the marking strip's text (preamble; {} for none)
\engineglyph{done}                                % ✓ in its status color, anywhere (a table cell)
```

`role=` on a card or strip: a role or blend name (`secondary`, `table-band`), else any defined
color (`NCARBlue`, the livery's exported palette), else a `\PackageWarning` and the default
(the card's place, a strip's `accent`), as the other formats fall back. `plain` stays for a
column beside cards (no fill, no band). `\done`/`\warn`/`\fail` exist only inside
`enginestatus` (defined locally: no clash with a document's macros). `\enginecolshare` and
`\enginecolrule` stay as the primitives `enginecolumns` is built on, documented for a plain
beamer `columns` block; the filter keeps writing them (pandoc's writer scopes a heading's block
to its column, `lua:222-223`).

## The commits, in order

### 0. This handoff

`design/latex-first-class-handoff.md`, as it stands.

### 1. `livery.sty` carries the role table and the card roles

- `livery_build.py:707` `emit_sty`: after the `ROLE_TEX` `\colorlet`s (`:719`) and the blends
  (`:730`), one `\def\engine@role@<role>{<TeX name>}` per entry of `latex.roles` (built at
  `:216`: the roles and the blends, the table #127 added). `emit_sty_boxes:861-879`: the
  `roles` key is no longer skipped (`:871`): `\def\engine@boxes@card@roles{primary,secondary,accent}`
  (role names; the theme resolves them through `\engine@role@`).
- `livery build liveries/*/`: every `build/livery.sty` changes, committed here (CI's `--check`).
- Test: `tests/test_boxes.py::test_every_key` (`:31-50`, per livery) asserts both lines.
- Nothing renders differently: `parity-latex check` identical.

### 2. The strip in a card measures its line

- Inner `.sty:310-322`: `\engine@barboxin` gets a twin `\engine@barboxout` (empty by default),
  placed after the box in `\endengine@barbox` before `\par`; `enginestrip` (`:361-364`) sets it
  with the same `\edef` to `\kern-<padx>` so the line is `hsize` wide. No pixel moves (an
  overfull line is still set from the left margin).
- Proof: the probe compiles without `Overfull`; `tests/parity.sh check` identical for the
  sample's and quickstart's PDFs (the only decks with a strip in a card; `parity-latex` has
  none), and `decks/sample/sample.log` loses its Overfull line. CHANGELOG LaTeX: one line.

### 3. Cards and strips on keys; the filter moves onto them

- Inner `.sty:368-461`. `\pgfkeys{/engine/card/.cd, role/.store in=..., pick/.code=...,
  pick/.default={}, solid/.is if=..., plain/.is if=...}` and `/engine/strip/.cd, role/.store in`.
- `\newenvironment{enginecards}[1]`: `\engine@shares{#1}` (shared with commit 5): a lone
  integer n is n equal shares; a comma list is weights, kept as shares when they add to 1 or
  less, else divided by their sum (`C.column_shares`'s rule, `engine-common.lua:245-253`, so the
  filter's `%.4f` shares round-trip; 1.0001 normalizes to the same widths). Stored as
  `\engine@cards@n` and `\engine@cards@share@<k>`.
- `\newenvironment{enginecard}[3][]{...}` (`[keys]{Title}{Sub}`): card k > n is a
  `\PackageError{Engine}{enginecards{n}: card k has no share}`; width = share_k × (`\linewidth`
  − gap × (n−1)) as `:398` computes it; role: the key, else the k-th of
  `\engine@boxes@card@roles` cyclically (`lua:285`'s rule), through `\engine@rolecolor{<name>}
  {<default>}`: `\ifcsname engine@role@#1\endcsname`, else `\ifcsname\string\color@#1\endcsname`
  (a defined color), else `\PackageWarning{Engine}{role=#1 is not a role of the livery or a
  color; <default>}`. `pick` alone: the outline, as today. `pick=<spec>`: `\alt<spec>
  {\engine@pickedtrue}{\engine@pickedfalse}` at read time (beamer's `\alt` takes the `<2>`
  tokens; the body is set at `\begin`, inside the frame's overlay pass), and the rule width
  reserved on every step so the body width does not change between steps (the frame is drawn in
  the fill, or the role on a solid card, when not picked). The `\in@{pick}` option words
  (`:400,413,417,434,451-460`) go. `\engine@cardval` (`:402`) is already gone (#127).
- `enginestrip[role=]` (`:358`): default `accent`, resolved the same way.
- `engine-beamer.lua` `card_rows:267-315`: writes `\begin{enginecards}{s1,s2,s3}` (the shares,
  `%.4f`) and `\begin{enginecard}[role=<name>,pick,solid]{head}{sub}`; a card without `role=`
  writes no key (the theme's by-place default); `C.box_role`'s warning stays in Lua so all three
  formats warn alike on an unknown name, and the resolved role name is what reaches the theme;
  a plain column is `[plain]{}{}`. `strips:354-363`: `\begin{enginestrip}[role=<name>]`. The
  `livery.latex.roles` lookups (`:268,293,358`) go.
- Proof: `tests/parity.sh check` identical under ncar, cu, nsi (the same numbers reach
  tcolorbox); `make -C decks/quickstart pdf LIVERY=nasa-jsc-eg` renders. CHANGELOG LaTeX.

### 4. Status lists: `enginestatus` and `\engineglyph`; the `\cmark` family retired

- Inner `.sty`, beside the cards: `\newcommand\engineglyph[1]` →
  `{\textcolor{EngineGlyph<Kind>}{\bfseries <✓|⚠|✗>}}` (kinds `done|warn|fail`; the glyphs and
  colors `engine-common.lua:344` and `livery.sty` use). `\newenvironment{enginestatus}`: beamer's
  `itemize` with `\done`, `\warn`, `\fail` defined inside it, each `\@ifnextchar<` for an
  overlay spec, then `\item<spec>[\engineglyph{kind}]`; `\fail` follows its item with
  `\color{BrandMuted}`, and the environment's `\item` (let to beamer's, then redefined locally)
  restores `\usebeamercolor[fg]{normal text}` first, so a plain or done item after a failed one
  is the text color again (on a solid card that is `BrandPrimaryText`, as the card sets it).
- `engine_livery.sty:333-336`: `\cmark`, `\xmark`, `\pmark` and `\RequirePackage{pifont}` go
  (grep the tree and `latex/` first: no caller today). `design/unplanned-city-ledger.md:106`:
  the item comes off Untriaged (done here, with the PR number).
- `engine-beamer.lua` `status_items:320-351`: `\begin{enginestatus}`, `\done ` / `\warn ` /
  `\fail ` / `\item ` before each item's inlines, `\end{enginestatus}`; `STATUS_TEX` and the
  `\textcolor{BrandMuted}{...}` wrap go. One known, intended difference: a failed item's
  sub-list is muted too (the Lua muted only the first paragraph's inlines); HTML mutes the whole
  item. The quickstart and sample have no sub-list under a status item: parity identical.
- Proof: `tests/parity.sh check` identical; `parity-latex` identical (no LaTeX deck used the
  marks). CHANGELOG LaTeX (the retirement named).

### 5. The column helper, and the filter's private macros become theme commands

- Inner `.sty:333-350`: `\newenvironment{enginecolumns}[1]` → `\engine@shares{#1}` then
  `\begin{columns}[T,onlytextwidth]`; `\newcommand\enginecolumn` → `\column{<share_k of
  \linewidth less the gaps>}` (beamer's command form closes the previous column) and
  `\enginecolrule` from the second on; one column too many is the `\PackageError`. The
  primitives stay.
- `enginescale`: `\newenvironment{enginescale}[1]` in the inner theme takes `SCALE_TEX`'s body
  (`lua:405-420`: `\engine@size`, the `\engine@typebody` scaling, the sub-item fallbacks) as its
  begin and `\endgroup` as its end; the Lua's `used.scale` header injection goes;
  `unwrap_layout:193-195` writes `\begin{enginescale}{S}` / `\end{enginescale}` and
  `opens_paragraph:386` matches it.
- `\enginemarking{<text>}`: outer `.sty:369-372` `\newcommand\enginemarking[1]{\gdef
  \engine@markingtext{#1}}`, `\engine@drawmarking` reads it (`\enginemarkingtext` goes);
  `lua:688-697` writes `\enginemarking{...}` (`none` → `{}`).
- Proof: `tests/parity.sh check` identical (sample: a `scale=` slide; nasa-jsc-eg's quickstart:
  the marking); `parity-latex` identical. CHANGELOG LaTeX.

### 6. A LaTeX compile test

- `tests/test_latex.py`: a module-scoped fixture (`tmp_path_factory`) writes a small deck on
  the layer (a lead; a `{3}` row with a strip, a status list and `pick=<2>`; `enginecolumns{2,1}`;
  a caution, a note, `enginescale`, `\enginemarking`) and compiles it with `xelatex` through
  `latexmk -interaction=nonstopmode -halt-on-error`, `TEXINPUTS`/`TTFONTS` from `ROOT` as
  `latex/Makefile:24` sets them; `pytest.skip` when `shutil.which("xelatex")` is None (CI's
  latex job runs in the image, which has TeX). Asserts: no `Overfull` in the log; the frame with
  `pick=<2>` is two pages (`pdfinfo`); `role=nonesuch` leaves the warning in the log; a second,
  three-card deck on `enginecards{2}` fails with the share error. `-n auto --dist loadfile`
  keeps the module on one worker; ~15 s.
- CLAUDE.md's test list names it.

### 7. The cookbook deck

- `latex/examples/sample.tex`: the twin of `decks/sample/sample.qmd`, slide for slide in its
  order, with the `\enginethemeoptions`/`\engineaspectratio` hooks `template.tex:6-8` has. One
  photo for every picture slide, `images/wallpaper/mesa_lab.jpg` (reached through `TEXINPUTS`'s
  `$(CURDIR)/`; the zip, commit 8, carries it). The mapping:

  | sample.qmd | sample.tex |
  |---|---|
  | Basics divider + subtitle | `\sectionsubtitle{...}` `\section{Basics}` |
  | Text & inline formatting, lists | itemize, enumerate, `\alert`, `\href` |
  | Wall of text `.smaller` | `\small` (`enginescale{0.85}` named in a comment) |
  | Math | `equation`; the `mathfont=` note |
  | Tables | `tabular` with `\engineth` and `\rowcolor{enginetableband}` |
  | Two-column, two-thirds, three columns | `enginecolumns{55,45}`, `{2,1}`, `{3}` |
  | Four columns on a wide slide | `enginewide` round `enginecolumns{4}` |
  | Options side by side | `enginelead`, the `{3}` row above, a second frame with `pick=<1>`, `<2>`, `<3>` moving (the steps proof) |
  | Solid cards | `[solid]` ×3 |
  | *(LaTeX only)* Steps inside cards | after the solid cards, `steps.tex`'s frame: `\item<+->` in one card, `\pause` in the second, a strip under `\uncover<2->` in the third; the row keeps one height across the steps (a comment: `\only` would make it jump). Beyond the sample's headings, because the body is boxed before the row is drawn and an author would not guess overlays survive that |
  | Image embed + note | `\includegraphics[width=0.6\linewidth]` + `\enginenote` |
  | A linked screenshot | `\href{url}{\includegraphics[height=0.72\textheight]}` + `\enginefootnote{†}{url}` (the out-of-scope footer's LaTeX way) |
  | Full-bleed photo `.feature` | `[enginebg=...]` + `enginefeaturepanel` |
  | Full-slide image `.full` | `[enginefull=...]` + `\enginefullcaption` |
  | Dark slide, step by step | `\item<+->` (`.brand-dark` is HTML's; a dark livery is the variant) |
  | A warning slide, `.vcenter scale=` | `[c]` frame, `enginescale{1.15}` round `enginecaution`, a footnote below |
  | Centered, scaled table; filled list | `[c]` + `enginescale{1.4}`; `enginescale{1.3}` (`.fill`'s way: `[shrink]` noted) |
  | Static code | `lstlisting` ×2 |
  | Live shell output | `\lstinputlisting` of a captured file under `snippets/` (out of scope: the capture is the author's) |
  | Mermaid, Graphviz | `\includegraphics{diagrams/render.pdf}`, `{diagrams/systems.pdf}` (`make diagrams`) with `\enginenote` |
  | Speaker notes | beamer `\note{...}` (shown with `\setbeameroption{show notes}` in a comment) |
  | Next steps + footnotes | `\enginefootnotespring` … `enginefootnotes` with `†` and `‡` |
  | Thank you `.closing` | `\engineclosingframe` |
  | Backup: `_quarto.yml` include | `\lstinputlisting{latexmkrc}` (the file shown verbatim; found through `TEXINPUTS`, and the zip has its own) |
  | What `_quarto.yml` sets | `enginecolumns{2}` of prose: what `\usetheme`'s options set |

- `latex/Makefile`: `examples` += `examples/sample.pdf`; a second variant block
  (`examples/sample-%.pdf: examples/sample.tex`, `opts_sample-nasa-dark := livery=liveries/nasa-dark,fonts=bundled`,
  `opts_sample-cu := livery=liveries/cu,fonts=bundled`, `aspect_sample-43 := 43`); `VARIANTS` +=
  `sample-nasa-dark sample-cu sample-43`; the header comment. `make clean` covers them through
  `VARIANTS`.
- `.github/workflows/ci.yaml:341`: `examples/sample.pdf` joins the Poppins loop (not its
  variants: nasa-dark is Public Sans, cu TeX Gyre Heros); a step after it: `if grep -q
  '^Overfull' examples/sample.log; then exit 1; fi` (the cookbook is ours; zero is the ratchet;
  the `!` gotcha at `:351` applies). `parity-latex` snapshots `examples/*.pdf`, so the four PDFs
  join it by existing.
- Proof: look at the pages (`pdftoppm -r 60`): the three steps of the moving pick, every step of
  the steps-inside-cards frame (one row height throughout), the status steps, `sample-nasa-dark` (the dark fill behind cards, strips and the caution), `sample-43`
  (the `{4}` row and the wide slide at 4:3). Put a contact sheet of those in front of Ben.
  CHANGELOG LaTeX.

### 8. The Overleaf zip ships the cookbook

- `_extensions/engine/overleaf_zip.py:69` `write()`: `sample.tex` from `ROOT/latex/examples/`
  (the module knows `ENGINE`; add `LATEX = ENGINE.parent.parent / "latex"`), its `\usetheme`
  line rewritten by `rewrite_starter`'s first substitution only (its photo ships, so the
  `enginebg=` frames keep it: split `rewrite_starter` into the theme line and the starter's
  photo handling), plus `images/mesa_lab.jpg`, `diagrams/render.pdf`, `diagrams/systems.pdf`,
  the two `snippets/` files it reads. The docstring and `livery zip`'s help (`:3-12`).
- `tests/test_cli.py::test_zip_packs` (`:98`) parametrize gains `sample.tex` and
  `diagrams/render.pdf`.
- `.github/workflows/ci.yaml:440-445`: after `talk.tex`, `latexmk -xelatex ... sample.tex` in
  the same clean `/tmp/overleaf` (TeX's paths unset): every livery, dark ones included, proves
  the cookbook on every push; the artifact (`:494`) keeps `sample.pdf`. Check the photo's size
  first (`du -h latex/images/wallpaper/mesa_lab.jpg`); over 1 MB, the cookbook uses a 1600 px
  copy, `latex/images/sample.jpg`.
- `latex/README.md` "Overleaf" (`:10-12`): "a starter `talk.tex`" → "the starter `talk.tex` and
  the cookbook `sample.tex`"; `liveries/README.md:27`'s row. CHANGELOG LaTeX.

### 9. The contact sheet

- `latex/Makefile` `previews` += `sample.png`: `latex/sheet.py` (new, ~30 lines, Pillow and
  poppler from the env as `previews` already needs `pdftoppm`) finds four pattern pages by title
  (`pdftotext` per page, as `screenshots.py`'s `SLIDES` does: the moving-pick step 2, the
  steps-inside-cards frame at its last step, the status slide, the warning) in `examples/sample.pdf`, `sample-cu.pdf` and
  `sample-nasa-dark.pdf`, renders them at 60 dpi and tiles them, liveries down and patterns
  across; writes `latex/sample.png`, committed, shown at the top of `latex/authoring.md`.
- Rebuild it whenever the cookbook's pattern slides change (say so in the Makefile comment and
  CLAUDE.md, as the README images rule says for the quickstart).

### 10. Documentation

- **`latex/authoring.md`** (new): the contact sheet; "Writing slides in LaTeX" moved from
  `latex/README.md:85-109` and grown (rows: `enginecolumns`/`\enginecolumn` and the primitives,
  `enginewide`, `enginelead`, cards and `enginestrip`, `enginestatus` and `\engineglyph`,
  `enginecaution`, `\enginenote`, `enginescale`, `\enginemarking`, speaker notes `\note`,
  `\sectionsubtitle`); a section "Cards, strips and status lists" with the Options slide as its
  one example and the overlay notes (`pick=<2>`, `\done<2->`, `\uncover` keeps a row's height,
  `\only` makes it jump); a section "Out of scope for LaTeX", one row per feature, one sentence
  why and the LaTeX way: mermaid and Graphviz cells (Quarto bakes them in a browser or WASM →
  `make diagrams`' pre-rendered PDFs, or TikZ in the roles' colors); the dark-livery diagram
  recolor (a filter over those baked pictures → draw the diagram in the roles); executable code
  cells (Jupyter at render → capture to a file, `\lstinputlisting`); matplotlib plots in the
  deck (Jupyter → `livery zip --charts`' `livery_mpl` outside the deck, `\includegraphics` of
  its PDF); the linked-image footer (`linked-images.lua` → `\href` + `\enginefootnote`); Quarto
  callouts (Quarto's own tcolorboxes → beamer blocks, or a tcolorbox in the roles); HTML autofit
  and `.fill` (a browser measures → `[shrink]`, `enginescale`, `typescale=`); `.brand-dark`
  (HTML only → a dark livery, `nasa-dark`); `date: last-modified` (→ `\today`); the include
  shortcode (→ `\lstinputlisting`, `\input`); speaker notes in PowerPoint's pane (→ `\note`).
- `latex/README.md`: "Writing slides in LaTeX" becomes two lines pointing at the guide; "The
  starter and the examples" table gains `sample.tex` and its three variants and `sample.png`
  under `previews`. `README.md:133`: the row names the guide. `docs/formats.md:229`: the
  parenthesis points at `latex/authoring.md`. `docs/authoring.md` "Cards and lead boxes" gets
  one sentence: the same slide in LaTeX is `latex/authoring.md "Cards, strips and status lists"`.
- `CLAUDE.md`: "The engine" gains a bullet **LaTeX authoring** (the layer's environments and
  what the filter writes through them; the cookbook, its variants and the sheet; the compile
  test; the zip's second deck; `parity-latex` covers the cookbook); the test list names
  `test_latex.py`; the "LaTeX" bullet in the overview names the cookbook beside the starter.
- `make test`: every `README "X"` / `<guide>.md "X"` pointer resolves (`tests/test_docs.py:114`).

## Verification

1. Before the first commit, on `origin/main`: `tests/parity-latex.sh baseline` and
   `tests/parity.sh baseline` (ncar, cu, nsi; quickstart, sample, fixtures, plots). Same
   checkout, same day.
2. Every commit: `make test` (`livery build --check` on every livery, pytest, the docs gate);
   `livery build liveries/*/` in commit 1, committed with it.
3. `tests/parity.sh check` after commits 2, 3, 4, 5 and at the end: identical (commit 2 only
   removes a log line; 3–5 move the same numbers through new names). `tests/parity-latex.sh
   check` after 1, 2, 4, 5 (identical) and after 7 (the four `sample*` PDFs appear as extra
   pages; nothing else moves).
4. Commit 7: the pages, looked at: the moving pick's three steps, the status steps, the
   nasa-dark and 4:3 variants; the contact sheet for Ben (commit 9 makes it reproducible).
5. Commit 8: `make -C decks/quickstart overleaf LIVERY=nasa-dark`, unzip in a clean directory,
   `env -u TEXINPUTS -u TTFONTS latexmk -xelatex sample.tex` builds; the same for `cu`.
6. `make -C decks/sample all` and `make -C decks/quickstart all` at the end (the filter's three
   formats); `tests/app-open.sh` is the release's step, not this PR's (no pptx change here).
7. The PR body: a section per commit, the parity results, the sheet; `/pr-review N` before Ben
   merges; then the release PR (26.10.8 if still October).

## Memory for the fresh session

`~/.claude/projects/-Users-benkirk-Documents-quarto-livery-decks/memory/`: `no-compat-shims.md`,
`minimal-prs-versions.md`, `approval-text-in-chat.md`, `american-spelling.md`,
`sprint-tags-recut.md`. After the PR opens, write `latex-first-class.md` (the picks above, what
landed, the squash SHA when Ben merges) and an index line.
