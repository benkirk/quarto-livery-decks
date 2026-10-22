# Writing slides in LaTeX

The theme is beamer with a livery; everything beamer does works. What this page adds is the
layer the engine draws the framework's slide patterns with, written as a hand author writes it:
columns at shares, a lead box, cards, strips, status lists, a caution box, notes, a scale group,
the marking strip. `examples/sample.tex` is the cookbook, the twin of the Quarto cookbook
`decks/sample/sample.qmd` slide for slide (`make examples` here); `make variants` builds it under
`cu`, under the dark livery `nasa-dark` and at 4:3. Four of its pattern slides under three
liveries:

![The cookbook's pattern slides under ncar, cu and nasa-dark](sample.png)

## The patterns

A Quarto deck writes the same things in Markdown ([docs/formats.md "PDF (beamer)"](../docs/formats.md#pdf-beamer);
[docs/authoring.md](../docs/authoring.md) has every one).

| | LaTeX |
|---|---|
| Title slide | `\titlepage` in a `[plain]` frame |
| Photo on the title slide (else the livery's default, if it has one: the NCAR family's is the Mesa Lab) | `\titlegraphic{\includegraphics{photo.jpg}}`; `\enginenotitlegraphic` for the plain cover |
| Fine print under the title | `\titlefineprint{...}` |
| Section divider | `\section{...}` |
| Divider subtitle | `\sectionsubtitle{...}` before `\section` |
| Slide | `\begin{frame}{Title}` |
| Blocks | `block`, `exampleblock`, `alertblock` |
| Emphasis | `\alert{...}` |
| Columns at shares, the livery's gap between them (and its rule, when it draws one) | `\begin{enginecolumns}{2,1}`, each column opened by `\enginecolumn`; `{3}` is three equal columns, `{55,45}` weights, `{0.6,0.3}` shares of the row (the rest stays empty) |
| A plain beamer `columns` block at the same widths | `\begin{column}{\enginecolshare{0.6667}{2}\linewidth}` (a share, the column count), `\enginecolrule` before each column but the first |
| Wide body (the slide less `geometry.wide-margin` a side): room for four columns or a wide table | `\begin{enginewide} ... \end{enginewide}` round the body |
| Lead box over a row of cards, or alone | `\begin{enginelead} ... \end{enginelead}`; each line its own paragraph (`\par`) |
| Cards, side by side at one height | `\begin{enginecards}{3}` holding `\begin{enginecard}[<keys>]{Title}{Sub}` (next section) |
| A strip, in a card or on its own | `\begin{enginestrip}[role=accent] ... \end{enginestrip}` |
| Status list: ✓ ⚠ ✗ as the bullets | `\begin{enginestatus}` with `\done`, `\warn`, `\fail` items (and plain `\item`); `\engineglyph{done}` is the glyph anywhere |
| Warning slide: the body on the soft yellow field with the brand-yellow bar | `\begin{enginecaution} ... \end{enginecaution}` |
| Note under a figure or table (the caption's look: small, muted, centered) | `\enginenote{...}` |
| Scale the body (its lists, tables and code with it) | `\begin{enginescale}{1.4} ... \end{enginescale}`; beamer's `[shrink]` goes the other way, down to fit |
| Center a short slide's body | `\begin{frame}[c]`; a list as a block: `\begin{center}\begin{varwidth}{\linewidth}` (the `varwidth` package) |
| Marking strip on every slide (`marking:` in a Quarto deck) | `\enginemarking{CUI}` in the preamble, where the livery places it; `\enginemarking{}` turns a livery's default off |
| Slide footnote (an aside at the foot, under a short rule) | `\enginefootnotespring` first in the frame and again after the content, then `\begin{enginefootnotes}\enginefootnote{†}{...}\end{enginefootnotes}` |
| Photo "feature" slide | `\begin{frame}[enginebg=photo.jpg]`, the body in `\begin{enginefeaturepanel}` |
| Full-slide figure (no title, logo or rule; optional caption) | `\begin{frame}[enginefull=diagram.pdf]`, `\enginefullcaption{...}` in the body |
| Closing slide | `\engineclosingframe{Thank you!}{...}` |
| Speaker notes | `\note{...}` in the frame; `\setbeameroption{show notes}` in the preamble shows them |
| Code | `lstlisting` (styled automatically; the frame `[fragile]`), `\lstinputlisting{file}` |
| Table | your own `tabular`, unstyled; `\engineth{...}` for a header cell and `\rowcolor{enginetableband}` for a band are there to use, and the cookbook's Tables slide draws the rules as the theme draws a Quarto table |
| Extra logo or slide decoration | `\logo{...}`: bottom right, above the footer (space reserved) |
| Theme options | `\usetheme[<options>]{Engine}` ([latex/README.md "Theme options"](README.md#theme-options)) |
| Math font | `\usetheme[mathfont=stix]{Engine}` |
| Smaller (or larger) text, every slide | `\usetheme[typescale=0.85]{Engine}` |

The colors are the livery's roles (`BrandPrimary`, `BrandAccent`, ...; [latex/README.md "Colors"](README.md#colors)),
and a `role=` below takes a role's name.

## Cards, strips and status lists

The cookbook's Options slide, as the Quarto one in [docs/authoring.md "Cards and lead boxes"](../docs/authoring.md#cards-and-lead-boxes):

```latex
\begin{enginelead}
  \textbf{Three ways to spend the next allocation}\par
  Each trades local capacity against a share of the consortium system.
\end{enginelead}
\begin{enginecards}{3}                       % three equal cards; {2,1,1} weights; {0.5,0.25,0.25} shares
  \begin{enginecard}[pick]{OPTION 1}{A modern GPU system}    % role by place: primary
    \textbf{Total cost \$30M}
    \enginelabel{Local investment}
    \enginebig{\$20M}
    \begin{enginestrip}[role=accent]
      → \textbf{\$10M} to the consortium
    \end{enginestrip}
    \begin{enginestatus}
      \done Data archive expansion
      \warn High-resolution runs
    \end{enginestatus}
  \end{enginecard}
  \begin{enginecard}{OPTION 2}{Join the consortium}          % secondary
    ...
  \end{enginecard}
  \begin{enginecard}[solid]{OPTION 3}{}                      % accent, all the role's; no sub-line
    ...
  \end{enginecard}
\end{enginecards}
```

- **`enginecards{<shares>}`** opens the row: a number is that many equal cards; a comma list is a
  weight per card, kept as shares of the row when they add to 1 or less, else divided by their
  sum. A card beyond the shares is an error. The row draws every card at one height, the
  tallest body and head, as HTML and pptx do; a card's body is set first into a box, so
  verbatim works inside it.
- **`enginecard[<keys>]{Title}{Sub}`**: both braces are mandatory, `{}` for no sub-line. The
  keys: `role=<name>` colors the head band, a role or blend of the livery (`primary`,
  `secondary`, `accent`, `highlight`, `table-band`, ...), else any defined color (the livery's
  exported palette, your own `\definecolor`); a name that is neither warns in the log and takes
  the default, the card's place in the row (`boxes.card.roles`: primary, secondary, accent,
  around again). `pick` draws the outline; `solid` fills the card with the role, its text in the
  primary text color; `plain` is a column beside cards, no fill, no band.
- **`pick=<overlay>`** moves the pick across steps: `pick=<1>` on the first card, `pick=<2>` on
  the second. The outline's width is reserved on every step, so nothing moves between them. The
  cookbook's "Options, the pick moving across steps" is the three-step version. A spec with a
  comma goes in braces, `pick={<1,3>}`: the keys are split at commas.
- **`\enginelabel{...}`** is the small-caps label and **`\enginebig{...}`** the big number, each
  a line of its own.
- **`enginestrip[role=]`** is a band in its role's tint (default `accent`), as wide as the card
  it sits in; on a solid card, the role itself.
- **`enginestatus`** is an itemize whose `\done`, `\warn` and `\fail` items carry ✓ ⚠ ✗ as
  their bullets in the livery's status colors, a failed item's text muted; `\item` is an ordinary
  bullet among them. Each takes an overlay spec as `\item` does: `\warn<2->`. The three names are
  defined only inside the environment.
- **Overlays inside cards** work as anywhere in beamer: `\item<+->`, `\pause`, `\uncover<2->{...}`.
  `\uncover` keeps the row one height across the steps; `\only` would make it jump. The
  cookbook's "Steps inside cards" has all three.

## Out of scope for LaTeX

What the Quarto decks do that a LaTeX deck does not, and the LaTeX way:

| Quarto | Why not here | In LaTeX |
|---|---|---|
| Mermaid and Graphviz cells | Quarto renders them in a headless browser or WASM at build time | `make diagrams` renders `examples/diagrams/*.mmd` and `*.dot` to PDFs once; `\includegraphics` them, or draw in TikZ with the roles' colors |
| Diagrams recolored on a dark livery | a filter over those baked pictures | draw the diagram in the roles (`BrandText`, `BrandBackground`), and it follows the livery |
| Executable code cells | Jupyter runs them at render | capture the session to a file, `\lstinputlisting` it (the cookbook's "Showing captured shell output") |
| matplotlib plots in the deck | Jupyter again | plot outside the deck with the charts bundle (`livery zip --charts`: the livery's style and `livery_mpl` helper), `\includegraphics` the PDF |
| The linked-image footer | `linked-images.lua` writes it per format | `\href{url}{\includegraphics{...}}` and the URL as a slide footnote (`\enginefootnote`) |
| Quarto callouts | Quarto's own tcolorboxes | beamer's `block`, `exampleblock`, `alertblock`, or a `tcolorbox` in the roles |
| HTML autofit and `{.fill}` | a browser measures the slide | `[shrink]` on the frame, `enginescale`, `typescale=` for the deck |
| `{.brand-dark}` | an HTML-only slide class | a dark livery (`nasa-dark`), the whole deck |
| `date: last-modified` | Quarto reads the file's time | `\date{\today}` |
| `{{< include file >}}` | a Quarto shortcode | `\lstinputlisting{file}` to show it, `\input{file}` to use it |
| Speaker notes in PowerPoint's pane | a pptx has one | `\note{...}`, shown by `\setbeameroption{show notes}` (or `show notes on second screen=right`) |
