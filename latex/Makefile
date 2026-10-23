# The engine's pure-LaTeX side: the starter deck, the examples and their variants
#
#   make            talk.pdf             (the starter: talk.tex, XeLaTeX via latexmk)
#   make html       examples/quarto-demo.html  (revealjs, needs quarto)
#   make examples   examples/{template,sample,paper,mathfonts,quarto-demo}.pdf (sample.tex: the
#                   cookbook, the twin of decks/sample/sample.qmd; latex/authoring.md)
#   make variants   brand/title/aspect-ratio/engine/math-font variants of examples/template.tex,
#                   and sample.tex under cu, nasa-dark and at 4:3
#   make previews   math-fonts.png from the specimen, sample.png from the cookbook and two of its
#                   variants, preview.png from the starter under ncar and cu (needs poppler's
#                   pdftoppm; the sheets need Pillow too)
#   make diagrams   examples/diagrams/*.pdf from their .dot/.mmd (needs Graphviz, npx)
#   make overleaf   engine-beamer-overleaf.zip: talk.tex + the theme + ncar (livery zip)
#   make clean
#
# The theme lives in ../_extensions/engine/, the liveries in ../liveries/. LaTeX finds the
# .sty files, a livery=liveries/<name>/ and its logos through TEXINPUTS, and the bundled
# fonts through TTFONTS (set here, and by latexmkrc), as an Overleaf zip's latexmkrc does.
# The root itself is on both: livery= names its files as liveries/<name>/..., which the
# theme looks up as files first (TTFONTS without it falls back to an installed face by
# name: in the image, Poppins with SemiBold for bold). Never $(ROOT)//: that would
# search conda-env/ too.
#
ROOT    := $(abspath $(CURDIR)/..)
THEME   := $(ROOT)/_extensions/engine
ENGINE  ?= xelatex
TEXENV  := TEXINPUTS=$(THEME)//:$(ROOT)/liveries//:$(ROOT)/:$(CURDIR)/: TTFONTS=$(ROOT)/:$(ROOT)/liveries//:$(THEME)//:
LATEXMK := latexmk -interaction=nonstopmode -halt-on-error

VARIANTS := template-ucar template-ucp template-ncarucar template-light template-43 template-pdflatex \
            template-mathpoppins sample-nasa-dark sample-cu sample-43

# latexmk tracks \input files, images and the theme itself -- always ask it (FORCE)
default: talk.pdf

talk.pdf: talk.tex FORCE
	$(TEXENV) $(LATEXMK) -$(ENGINE) talk.tex

html: examples/quarto-demo.html

examples/quarto-demo.html: examples/quarto-demo.qmd FORCE
	cd examples && quarto render quarto-demo.qmd --to engine-revealjs

examples: examples/template.pdf examples/sample.pdf examples/paper.pdf examples/mathfonts.pdf examples/quarto-demo.pdf

examples/%.pdf: examples/%.tex FORCE
	cd examples && $(TEXENV) $(LATEXMK) -$(ENGINE) $*.tex

examples/quarto-demo.pdf: examples/quarto-demo.qmd FORCE
	cd examples && quarto render quarto-demo.qmd --to engine-beamer

# \enginethemeoptions / \engineaspectratio are hooks in examples/template.tex
opts_template-ucar       := livery=liveries/ucar
opts_template-ucp        := livery=liveries/ucp
opts_template-ncarucar   := livery=liveries/ncarucar,footer=full
opts_template-light      := title=light,fonts=bundled
opts_template-43         :=
opts_template-pdflatex   :=
opts_template-mathpoppins := mathfont=poppins
aspect_template-43       := 43
engine_template-pdflatex := pdflatex

variants: $(addprefix examples/,$(addsuffix .pdf,$(VARIANTS)))

examples/template-%.pdf: examples/template.tex FORCE
	cd examples && $(TEXENV) $(LATEXMK) -$(or $(engine_template-$*),$(ENGINE)) -jobname=template-$* \
	  -usepretex='\def\enginethemeoptions{$(opts_template-$*)}\def\engineaspectratio{$(or $(aspect_template-$*),169)}' \
	  template.tex

# the cookbook under a dark livery, under cu, and at 4:3 (the same hooks in examples/sample.tex)
opts_sample-nasa-dark := livery=liveries/nasa-dark,fonts=bundled
opts_sample-cu        := livery=liveries/cu,fonts=bundled
opts_sample-43        :=
aspect_sample-43      := 43

examples/sample-%.pdf: examples/sample.tex FORCE
	cd examples && $(TEXENV) $(LATEXMK) -$(ENGINE) -jobname=sample-$* \
	  -usepretex='\def\enginethemeoptions{$(opts_sample-$*)}\def\engineaspectratio{$(or $(aspect_sample-$*),169)}' \
	  sample.tex

# the README's math-font specimen: the summary slide of examples/mathfonts.pdf; authoring.md's
# contact sheet: four pattern slides of the cookbook under ncar, cu and nasa-dark (sheet.py finds
# them by title); the README's preview: the starter's title, divider, content and closing slides
# under ncar and cu (talk-cu.tex is talk.tex with its livery swapped, written here). All three are
# committed: rebuild them whenever the slides they show change (a theme change moves every one),
# look at them, and commit them (as the README images rule for the quickstart).
previews: math-fonts.png sample.png preview.png
math-fonts.png: examples/mathfonts.pdf
	pdftoppm -r 150 -f 9 -l 9 -singlefile -png $< math-fonts
sample.png: examples/sample.pdf examples/sample-cu.pdf examples/sample-nasa-dark.pdf sheet.py
	python3 sheet.py $(filter %.pdf,$^) -o $@
preview.png: talk.pdf talk-cu.pdf sheet.py
	python3 sheet.py --pages 1,2,3,-1 $(filter %.pdf,$^) -o $@
talk-cu.pdf: talk.tex FORCE
	sed 's|livery=liveries/ncar|livery=liveries/cu|' talk.tex > talk-cu.tex
	$(TEXENV) $(LATEXMK) -$(ENGINE) talk-cu.tex

# One source per example diagram: quarto-demo.qmd renders it itself, and
# template.tex includes the PDF built here (committed, so `make examples`
# needs neither tool).  mermaid-cli fetches a headless Chrome on first use.
DIAGRAMS := examples/diagrams
MMDC     ?= npx -y @mermaid-js/mermaid-cli
diagrams: $(DIAGRAMS)/systems.pdf $(DIAGRAMS)/render.pdf

$(DIAGRAMS)/%.pdf: $(DIAGRAMS)/%.dot
	dot -Tpdf $< -o $@

$(DIAGRAMS)/%.pdf: $(DIAGRAMS)/%.mmd
	$(MMDC) -i $< -o $@

# An Overleaf project: the starter deck on the ncar livery, one photo, latexmkrc
# (which finds the theme) and the LaTeX half of the theme -- no Quarto or revealjs
# files.  `livery zip` packs any livery the same way (the framework's too).
overleaf: engine-beamer-overleaf.zip
engine-beamer-overleaf.zip: talk.tex FORCE
	python3 $(THEME)/livery.py zip $(ROOT)/liveries/ncar -o $@ --photo images/wallpaper/mesa_lab_sunset.jpg

clean:
	latexmk -C -quiet talk.tex $(wildcard talk-cu.tex) 2>/dev/null
	rm -f engine-beamer-overleaf.zip talk-cu.tex
	rm -rf examples/quarto-demo_files examples/quarto-demo.html
	cd examples && latexmk -C -quiet template.tex sample.tex paper.tex $(addsuffix .tex,$(VARIANTS)) 2>/dev/null; \
	  rm -f *.pdf *.nav *.snm *.vrb *.xdv *.bbl *.blg *.run.xml *-blx.bib quarto-demo.tex

FORCE:
.PHONY: default html examples variants previews diagrams overleaf clean FORCE
