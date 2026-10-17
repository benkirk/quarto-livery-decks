# One engine, many liveries

A design for taking this framework from one brand (NSF NCAR) to many: CU Boulder,
NASA, and a family of NASA program flavors, each onboarded from a reference
PowerPoint the customer supplies. It is written to be the founding design of two
new repositories (section 2), forked from this one and from the NCAR beamer theme,
so that the NCAR pair keeps serving its users untouched.

Vocabulary, used throughout:

| Term | Meaning |
|---|---|
| **engine** (the chassis) | everything that is the same whoever's logo is on the slide: the layout machinery, styles that read roles and geometry rather than colors and lengths, the Lua filters, the autofit script, the pptx post-processors, QA and site tooling |
| **livery** | one brand flavor as a directory of data and assets: palette mapped onto roles, type, logos, art, geometry, the pandoc-compliant `template.pptx`, and the customer's reference deck |
| **flavor** | a livery that `extends` another and overrides a few keys (a NASA program under NASA). Not a separate concept, just a short livery |

An airline paints identical aircraft in its own livery. That is the whole idea.

## 1. Where the brand lives today

The survey behind this design found the NCAR brand in roughly thirty places across
three copies of the same data. The seam already exists, which is why the design is an
opening of it rather than a rewrite.

**The beamer theme is two-layered.** `ncar_branding.sty` (vendored under
`docs/common/_extensions/benkirk/ncar/`) owns the palette (eleven `\definecolor`s,
lines 34-46), six semantic roles switched by `brand=ncar|ucar|ncarucar`
(`BrandPrimary`, `BrandPrimaryText`, `BrandPrimaryContrast`, `BrandSecondary`,
`BrandAccent`, `BrandText`, lines 49-62), the fonts (Poppins, bundled under
`ncar-assets/fonts/Poppins/`), and the logo lockups. The color, inner and outer
themes read roles about 80% of the time. The leaks that read raw palette names:

- callouts in `ncar-beamer.lua:321-332` (`NCARBlue`, `UCARAquaContrast`, `BrandOrange`)
- `example text`, `block title example`, `block title alerted` in `beamercolorthemeNCAR.sty`
- `\cmark`, `\xmark`, `\pmark` and the `ncar` listings style in `ncar_branding.sty`
- feature frames (`LightBlue`, `Space`) and the slide footnotes (`CoolGray4`, `CoolGray7`)
- `ncar.theme`, the highlight theme, with NCAR hexes

**The revealjs side carries the data again**: `$ncar-*` variables in
`ncar-revealjs.scss` (and five `--ncar-*` custom properties on `:root`, overridden under
`html.ncar-brand-ucar`), a `BRANDS` table in `ncar-revealjs.lua:63`, logo `url()`s in
`ncar-revealjs.css`, and the Poppins `@font-face` rules. The waves are inline SVG drawn
by the Lua filter from the same control points the TikZ uses.

**The pptx side carries it a third time**, split between the template and the
scripts. `template.pptx`'s `theme1.xml` has the scheme (dk1 `00357A`, dk2 `0057C2`,
lt2 `F1F0EE`, accent1 `42C0FF`, accent4 `FAA119`, accent5 `FDD509`; both fonts Poppins).
The content-slide waves on the master are a raster, `ppt/media/image1.png`; only the
Section Header layout is procedural (`branding/ncar/build_divider_layout.py`). The
post-render scripts hardcode hex constants and Poppins paths and take no brand
argument: `style_footnotes.py:35-36`, `style_tables.py:30-32`,
`slide_layout.py:43-45`, `link_captions.py`, `section_subtitle.py:58-70` (the divider
geometry and the Poppins files it measures with), `embed_poppins.py:28` (the
`.fntdata` blobs and the `Poppins` typeface name), `site_index.py` (palette and Google
Fonts link), and `linked-images.lua:11`. Only `section_subtitle.py` and
`build_divider_layout.py` write theme scheme slots and are brand-neutral already.

**The glue is brand-named**: `Make.common` renders `--to ncar-revealjs` and
`--to ncar-beamer` and links `common/` into each deck directory as `_ncar`; the shared
`_quarto.yml` says `reference-doc: _ncar/branding/ncar/template.pptx`.

**Geometry is a fourth copy.** The same lengths appear as `0.06\paperwidth`,
`0.018\paperwidth`, `0.06\paperheight` in `beamerouterthemeNCAR.sty:38-41`, as
`$ncar-margin: 96px`, `$ncar-tab: 29px`, `$ncar-logo-h: 58px` in the scss (lines
82-84, in 1600x900 slide pixels), as `TAB_W = 29` in `section_subtitle.py:66`, and as
`EDGE = 0.94` in `deck_qa.py:33`.

## 2. Repositories

Two new repositories, forked, with general nouns. The NCAR repositories stay exactly as
they are for the people who use `\usetheme{NCAR}` from LaTeX and for the NCAR decks
built here.

```
benkirk/NCAR_beamer_template ──fork──▶ beamer-livery-theme   engine + reference liveries (ncar, ucar, ncarucar)
                                           │ vendored into the framework (quarto add / quarto update)
benkirk/quarto-docs-framework ─fork──▶ quarto-livery-decks   framework: Make.common, post-processors, QA,
                                           │             liveries/ for cu, nasa, nasa/<program>
                                           │ git submodule
                                        <customer>-decks  the customer's .qmd decks; each deck Makefile
                                                          includes ../framework/docs/Make.common and sets LIVERY
                              optional: <customer>-liveries  a customer's liveries in their own repo, vendored
                                                          into quarto-livery-decks, only when logo license, privacy
                                                          or ownership require a separate home
```

Names, settled 2026-10-16 before the forks were created:

| What | Name |
|---|---|
| engine repo | `beamer-livery-theme` |
| Quarto extension directory, hence format names | `engine` → `engine-beamer`, `engine-revealjs` |
| LaTeX theme and brand package | `\usetheme[livery=<dir>]{Engine}`, `engine_livery.sty` |
| framework repo | `quarto-livery-decks` |
| links Make creates in a deck directory | `_engine` (today `_ncar`) and `_livery` |

With the rename, every `ncar@` macro, `ncar-*` CSS class and HTML id, `--ncar-*` custom
property, `ncar-layout:` notes line, and `ncar-beamer:` warning prefix takes the new
noun. `when-format="beamer"` keeps working, because the base format is unchanged.

**Why forks rather than refactoring in place.** The Quarto format names derive from the
extension's directory name and an extension cannot alias another's formats, so a clean
rename is a breaking change for anyone using `ncar-beamer` from Quarto. The LaTeX entry
point `\usetheme{NCAR}` and the `ncar@` macro namespace are the same story. A fork gives
the general names a clean start and the NCAR names an undisturbed home.

**Coexistence and the exit.** The ncar livery in the engine is the forward path for NCAR
decks, and byte-level parity of its output with today's is the acceptance test of the
whole refactor (section 8). Once that holds, two optional moves end the double
maintenance: `beamerthemeNCAR.sty` upstream becomes a shim
(`\usetheme[livery=ncar]{Engine}` behind the old option names), and this repo becomes a
thin consumer of `quarto-livery-decks` with `LIVERY=ncar`. Neither is required by this design.

**Where liveries live** is a licensing and ownership question, not a code one. The
reference liveries ship with the engine (they are its test fixtures). New liveries
start in `quarto-livery-decks/docs/common/liveries/`. A customer's set moves to its own repo
only when the assets demand it: NASA insignia and program lockups may well. The contract
is per directory, so a repo can hold one livery or ten; this is deliberately neither one
repo per customer per style nor one per customer.

## 3. The template is the spec

Each brand reproduces its reference deck's layout, not only its palette. So geometry has
one source of truth: the livery's pandoc-compliant `template.pptx`, built from the
reference deck's own master and layouts (section 6). beamer and revealjs imitate it from
measurements the compile step extracts (placeholder boxes, logo box, footer, divider
field), stored as fractions of the slide and converted to beamer paper fractions and to
1600x900 slide pixels.

This inverts today's flow, where scss constants were copied into Python, and makes
"pptx primary" literal. Fidelity is graded: pptx exact (it is the customer's master);
HTML and PDF faithful to the measured geometry; whatever parameters cannot express goes
into the livery's override files (section 4).

Consequences for the engine: every length in `beamerouterthemeNCAR.sty:38-41`, every
`$ncar-*` length in the scss, and the geometry constants in `section_subtitle.py`,
`slide_layout.py` and `deck_qa.py` become livery values, with today's numbers recorded
as the ncar livery's measurements.

## 4. The livery contract

```
liveries/<name>/
  _brand.yml      the authoring manifest, in the Quarto/Posit brand.yml standard, kept
                  strictly standard: color.palette plus color.primary/secondary/foreground/
                  background, typography fonts with file sources, logo light and dark
  livery.yml      engine knobs the standard has no slot for: extends; roles (primary-text,
                  primary-contrast, accent, muted, surface, warning, dark); art {title,
                  content, section, closing, feature}; divider {label, eyebrow, tab};
                  signoff {light, dark, aspect, height, bottom, corner}: a second lockup at
                  the foot; geometry.logo.corner (top-right | top-left | none) and
                  geometry.pagenumber.corner (bottom-left | bottom-right); title {style:
                  cover | band, ...}; marks {<role>: {logo, signoff}}: the mark and sign-off
                  each field wears by its role (background, primary, the band's field);
                  installed-fonts {base, headings}: installed faces preferred over the
                  bundled ones; pptx {template, fonts, typeface, heading-typeface, scheme};
                  aspect (16:9 default); overrides. Any other key is warned about
  template.pptx   THE SPEC: pandoc-compliant, derived from the reference deck (section 6)
  logos/          pdf (LaTeX) and png/svg (web, RGB), same basenames, light and dark variants
  art/            background art per slide kind: svg (web) + pdf (LaTeX) + png (pptx master
                  and layouts). The NCAR waves become three such files, exported once from
                  the existing TikZ and SVG generators; the engine has no procedural motif
  fonts/          ttf; fonts/pptx/*.fntdata embedded once by hand in PowerPoint (Options >
                  Save > Embed fonts; no reliable Python writer exists). Absent: embedding
                  is skipped with a warning
  overrides/      the escape hatch: livery-extra.sty, livery-extra.css, livery-extra.lua
  reference/      the customer's deck(s), extracted media, report.md, onboarding notes.
                  Never read at build time
  build/          GENERATED by livery_build.py, committed, freshness checked in CI:
                  livery.json   the one resolved truth, extends applied, geometry included;
                                Lua (quarto.json) and Python both read it
                  livery.sty    \definecolor palette, \colorlet roles, logo, font and
                                geometry macros: what \usetheme[livery=...] inputs
                  livery.css    @font-face, logo and art url()s, :root{--engine-*} values
                  livery.theme  the pandoc highlight theme in the palette
```

**Why brand.yml for authoring and nothing more.** It is Quarto's own brand standard
(1.6+), so a livery author gets a documented schema and tooling instead of a house
format. But Quarto's own `brand:` processing is not used at render time: it reaches only
revealjs (not beamer, not pptx), its generated Sass layer sits below the theme's scss
(which would silently win), and its Lua API needs Quarto 1.7. So `_brand.yml` is read by
the compile step only, and the shared `_quarto.yml` never sets `brand:`.

**Why derived, committed outputs.** LaTeX cannot read YAML, and standalone users need a
`.sty`; the pptx post-processors run outside Quarto; `extends` should resolve exactly
once, in one place. Committed generated files are already the repo's pattern
(`build_divider_layout.py`, the README screenshots), with a `--check` mode in CI.

**pptx color contract.** The template's `theme1.xml` scheme carries the roles, so most
post-processors need no brand argument at all; they write scheme slots the way
`section_subtitle.py` already does:

| slot | role | | slot | role |
|---|---|---|---|---|
| `dk1` | text | | `accent1` | secondary |
| `lt1` | white | | `accent4` | accent |
| `dk2` | primary | | `accent5` | warning |
| `lt2` | surface | | | |

Muted and the caution fill have no slot and come from `livery.json`.

**`extends`.** A deep merge inside the generator; the child's files override the
parent's by name. A flavor without its own template gets the parent's template recolored
(scheme swap in `theme1.xml`, logo media swap), which is the same operation the
onboarding pipeline performs, so it costs nothing extra.

**Geometry in `livery.json`**, measured from the template (section 6), in fractions of
the slide: content area, title box, logo box (corner, height, aspect), footer and slide
number boxes, the divider's field and label box, the body size ladder (today
20/18/16/14/12 pt, chosen so autofit never fires). The engine converts to its units.

## 5. The engine contract

For `beamer-livery-theme`:

- `\usetheme[livery=<absolute dir>]{Engine}` inputs `<dir>/build/livery.sty` and the
  optional `overrides/livery-extra.sty`. The color, inner and outer themes read only
  roles and geometry macros; the leaks listed in section 1 move to roles, with new
  roles `BrandMuted`, `BrandSurface`, `BrandWarning`, `BrandDark` for what the six
  cannot express. Page backgrounds per style (title, content, section, closing, feature)
  come from `art/` as PDF includes instead of TikZ.
- `engine-beamer.lua` reads the metadata key `livery:`, resolves it to an absolute path
  (the `\input@path` trick stays), and passes `livery=`. Absent, the engine's bundled
  ncar reference livery applies, so an old framework and a new engine still build.
- `engine-revealjs.lua` reads `livery:` → `build/livery.json`. `add_dependency()`
  attaches `build/livery.css` plus the livery's fonts, logos and art as dependency
  resources, and injects a `:root{--engine-*}` style block. The scss expresses every
  color and length as `var(--engine-*)` with the ncar values as defaults, so one
  compiled theme serves every livery. Backgrounds are the livery's SVGs.
- `highlight-style` is overridable by the project (`_livery/build/livery.theme`).
- The reference liveries live under `liveries/` in the engine repo; vendoring brings
  them along under the extension directory, and the framework's `liveries/ncar` becomes a
  link to the vendored copy.

For `quarto-livery-decks`:

- The post-processors keep their jobs and lose their constants, parameterized by
  `livery.json` and scheme slots: `embed_fonts.py` (was `embed_poppins.py`; typeface
  and blobs from the livery), `section_subtitle.py` (fonts to measure with, divider
  label and geometry), `style_tables.py`, `style_footnotes.py`, `slide_layout.py`
  (slots; muted and caution fill from the livery), `link_captions.py`,
  `linked-images.lua` (`quarto.json.decode` of `livery.json`), `site_index.py`
  (palette and font family; a Google Fonts link only for a google source),
  `deck_qa.py` (`EDGE` from the livery's margin).
- `Make.common`: `LIVERY ?= ncar`; `LIVERY_DIR ?= $(SHARED_COMMON)/liveries/$(LIVERY)`;
  a `.livery` stamp whose content is `$(LIVERY)` and an `ln -sfn` rule for the `_livery`
  link (a missing-only rule, like today's three, would silently keep the old livery
  after `make LIVERY=cu`); `DEPS += _livery`; `FORMAT_HTML ?= engine-revealjs` and
  `FORMAT_PDF ?= engine-beamer`; `LIVERY_DIR` exported for the scripts.
- The shared `_quarto.yml`: `reference-doc: _livery/template.pptx` and a top-level
  `livery: _livery`, the key by which both Lua filters find the livery. No `brand:`.
- CI: `livery_build.py --check` over every livery; a matrix over liveries rendering the
  quickstart deck with `LIVERY=$x`, grepping `ppt/theme/theme1.xml` for the livery's
  primary hex, `embeddedFontLst` for its typeface, and the HTML for `livery.css`; the
  consumer workflow checks the `_livery` link beside the three it checks today.

## 6. Onboarding a brand from a reference PowerPoint

Every new brand starts from a deck the customer supplies: a visual guide, not a
pandoc-compliant template. Reverse-engineering it is a repeatable step, with three tools
and a short list of judgement calls.

**What the tools can rely on.** python-pptx enumerates masters, layouts, placeholders
(type, index, box), pictures and media, and can rename layouts. It cannot edit
`theme1.xml`, embed fonts, set `showMasterSp`, add typed placeholders to a layout, or
cleanly delete layouts. The repo convention holds: python-pptx for the report,
lxml-on-zip for the writes, fixed zip timestamps for reproducible files.

**Tools**, in `docs/common/utils/`:

1. `livery_inspect.py reference.pptx <livery dir>` writes `reference/report.md` (slide
   size and aspect; the twelve scheme slots; the font scheme; per master and layout its
   name, type, placeholders with boxes, pictures and background fill; every `srgbClr`
   ranked by frequency), extracts the media into `reference/media/`, and seeds
   `_brand.yml` (palette from the slots and the frequent hexes, fonts from the font
   scheme) and a `livery.yml` with a blank layout-mapping table.
2. `livery_template.py <livery dir>` (in the engine since 3.3.0) produces the compliant template from the reference's
   master and the mapped layouts: renames them to pandoc's names (`Title Slide`,
   `Title and Content`, `Section Header`, `Two Content`, `Comparison`,
   `Content with Caption`, `Blank`), guarantees the five `slideLayout1` placeholders
   (`ctrTitle`, `subTitle`, `dt`, `ftr`, `sldNum`), writes the slot contract into
   `clrScheme` and the font scheme, places art and logo media as `ppt/media/image*`,
   injects `fonts/pptx/*.fntdata` if present, and then measures the result into the
   geometry block of `livery.json`.
3. `livery_check.py <livery dir>` verifies layout names, the five placeholders, the slot
   contract, media naming and `build/` freshness, then runs
   `make -C docs/quickstart qa LIVERY=<name>`.

**The human steps**, in order: inspect → map the reference layouts onto pandoc's (which
of a customer's six title variants is "Title Slide"; which rich layouts pandoc can never
pick and should be dropped) → choose the roles (customer slots are arbitrarily ordered,
`dk2` is not reliably the primary; the builder warns on WCAG contrast for the
small-text role) → logo variants and clear space → art per slide kind (vector preferred;
rasters acceptable on masters, never as a procedural recipe) → build, template, check →
open the template in PowerPoint (the "Repair?" prompt cannot be automated) → `make
screenshots` contact sheet reviewed against the reference and committed under
`reference/` → commit.

**Not doable, by design**: extracting the reference's embedded fonts (licensing, EOT
decoding; the customer supplies the TTFs), and vectorizing bitmap art.

## 7. Phasing

0. This document, copied into both forks as their founding design; nouns settled.
1. `quarto-livery-decks`: de-brand the framework with the ncar livery as the migration proof.
   Move `branding/ncar/` to `liveries/ncar/`, write its `_brand.yml` and `livery.yml`
   from `ncar_branding.sty`, add `livery_build.py` and the `livery.py` loader,
   parameterize the post-processors one per commit, add `LIVERY` to Make, and wire CI.
   Every step is parity-checked (section 8).
2. `beamer-livery-theme`: the engine refactor of section 5 (rename, roles only, geometry from
   the livery, art files, `livery=`); re-vendor into the framework; `liveries/ncar`
   becomes a link to the vendored reference livery.
3. CU Boulder: the first foreign livery and the first run of the onboarding tools (no
   waves, other fonts, a template from a reference deck). Joins the CI matrix.
4. NASA general, then the first program flavor via `extends` (recolored template, its
   own lockups).

Before step 4 (done 2026-10-16, engine 3.3.0): the post-NSI refactor (`docs/design/refactor-handoff.md`): the pptx template
tooling moves into the engine, marks are keyed by the field's role (`marks:`), and five cheap
fixes (unknown keys warn, livery files as make prerequisites, a fixture deck in parity and CI,
absolute art paths in beamer, flavors inherit `pptx.scheme` overrides), and a livery may
prefer an installed font over its bundled stand-in (`installed-fonts:`; cu: Helvetica Neue,
used where installed, never shipped).

**Deferred on purpose: one description of each title composition.** The title, closing and
feature compositions are drawn four times (beamer, revealjs, the template builder,
`slide_layout.py`) in two repos, and the copies drift. The fix, compositions described once as
boxes in slide fractions in `livery.json` and drawn by every format, is a design change for
section 5, to be done before the next new composition (`refactor-handoff.md`, last section).

## 8. Verification

- Phase 1 holds a baseline built on `main` (`make all`, `make qa`, `make screenshots`
  for `docs/sample` and `docs/quickstart`) and checks after every step: per-part XML
  diff of the unzipped pptx (timestamps differ, XML must not), `pdftotext` equal, an
  empty `git diff docs/quickstart/screenshots`, and the greps CI already runs
  (`image-divider-logo.png`, `ncar-section-label`, `embeddedFontLst`).
- Phase 2: the ncar livery's generated `livery.sty` diff-equals the color block of
  `ncar_branding.sty:34-62`; the engine's own sample decks render byte-equal under
  `livery=ncar` and under the old `brand=ucar`.
- Phases 3 and 4: `livery_check.py`, `make qa LIVERY=<name>`, a reviewed contact sheet
  against the reference deck, and PowerPoint opening the template without a repair
  prompt.

## 9. Risks and open questions

- Reproducing pptx geometry in HTML and PDF from measurements will be approximate for
  exotic layouts. The override files are the valve; decide per livery how far to chase.
- A 4:3 reference deck: `aspect` is in the contract, but phase 3 should confirm the
  engine handles it or declare 16:9 only.
- pandoc's layout chooser is fixed. The demotions documented in `CLAUDE.md` (Two
  Content, Comparison, Content with Caption) apply to every livery, and a reference
  deck's richer layouts are unreachable from Markdown; drop them from the template.
- Body size ladders: a brand face far from Poppins' x-height may need its own ladder to
  keep autofit quiet. It is a livery value, so this is a per-brand tuning, not an
  engine change.
- Naming is settled (section 2). The nouns were picked before the forks were created, since
  they end up in format names, macro namespaces and CSS classes.

## 10. Log

Newest first. The first unchecked item of section 7 is the next step.

- **2026-10-16** The post-NSI refactor (`docs/design/refactor-handoff.md`), as
  beamer-livery-theme 3.3.0 and this repo's next PR. (1) The pptx template tooling lives in
  the engine: `livery_template.py`, `pptx_waves.py`, the json reader `livery.py` and the
  data and template checks of `livery_check.py` sit beside `livery_build.py`, and the
  engine's CI runs the checks on its four liveries, so a template change is one engine PR.
  Here `utils/livery.py` loads the vendored reader by path, `slide_layout.py` takes
  `pptx_waves` the same way, and `utils/livery_check.py` wraps the engine's and keeps
  `--qa`. (2) Marks by field: `marks: {<role>: {logo, signoff}}`, resolved for every livery
  into `livery.json` (background from `logo.medium.light` and `signoff.light`, primary
  from the dark ones, any other role from primary's); the themes, the css, the Lua
  dependency list, the builder and `slide_layout.py` read it; `title.logo`/`title.signoff`
  are deprecated aliases. nsi now says `primary: {logo: nsi-black}` and `dark: {logo:
  nsi-white, signoff: rio-white}` and drops its band keys, its `logo.medium.dark` and its
  restated scheme; both templates rebuilt byte-identically. (3) Cheap fixes: an unknown
  `livery.yml` key warns; absolute paths go into `livery.sty` without `\engineliverydir`;
  a flavor keeps its parent's `pptx.scheme` overrides; `livery.py deps` puts the livery's
  files into `DEPS`, and the `_livery` link became order-only, because make stats a
  link's target (the livery directory, older than a fresh `.livery` stamp) and so
  re-rendered every deck on every run after a livery switch; `docs/fixtures/` (a photo
  title and the light title) joins CI and `parity.sh`, which now snapshots every deck of
  `DECKS`, renders the PDF pages and covers nsi. (4) `installed-fonts`: cu names Helvetica
  Neue (headings: Condensed Bold); the css tries it by `local()` name before Heros and
  `fonts=brand` loads it in the PDF when installed. Checked on a Mac: `pdffonts` lists the
  HelveticaNeue faces under `fonts=brand` and Heros under `fonts=bundled`; Chrome's
  `CSS.getPlatformFontsForNode` reports Helvetica Neue (Condensed Bold for the headings),
  and TeX Gyre Heros with the `local()` names misspelled. Found by the contact sheet: the
  engine's HTML dependency is named for the engine version, not the livery, and quarto keeps
  a copied file newer than its source, so after a `LIVERY` switch without `make clean` a deck
  wore the old livery's css and marks; the HTML recipe now drops that directory first.
  Parity (quickstart, sample, fixtures under ncar, cu and nsi): pptx and PDF (text and
  pages) identical, HTML only the version path; engine parity 202 PDF pages identical, HTML
  only the version path; every template rebuilt byte-identically. Next: NASA.

- **2026-10-16** Retrospective after cu and nsi, with Ben. The livery contract held: nsi went
  in as data, the onboarding tools and CI took it as is. Frictions: each title composition
  written four times in two repos (and drifting); the template builder in the framework
  writing the engine's templates; one mark per field kind; and five cheap ones. Decided: one
  follow-up refactor for the builder's home, marks by field and the cheap fixes
  (`docs/design/refactor-handoff.md`, written for a fresh session); the composition rework
  deferred on purpose, recorded in section 7. Next: that refactor, then NASA.

- **2026-10-16** cu's placeholder lockup replaced: the plain CU Boulder lockup (one line, monogram
  and "University of Colorado Boulder") from CU's own web brand assets
  (`cdn.colorado.edu/static/brand-assets/live/images/cu-boulder-logo-text-{black,white}.svg`, which
  Ben found linked from the NSI website), kept as SVG with a PNG for HTML and pptx and a PDF of the
  same name, which LaTeX picks, so the PDF's sign-off is vector. Sign-off height 0.04 (one line;
  0.27 of the width). The deck's RIO lockup moved to the nsi flavor, whose deck uses it, as its own
  `signoff`. Next: NASA.

- **2026-10-16** The `nsi` flavor (CU Center for National Security Initiatives), from
  `docs/design/nsi-handoff.md`, in four steps. (1) beamer-livery-theme #14 (3.1.0): the title
  slide's composition becomes a livery knob, `title.style: cover | band`; the band is a field
  in a role with `art.title` over it, a band holding the text left of `split` and the photo
  right of it, the mark and the sign-off centred in the strip below, and under it the closing
  slide wears the field, the art and the strip; `art.titlegraphic` is the photo for decks that
  set none. Beamer draws the band text in the background at the fractions, so PDF and HTML
  agree. (2) This repo #18: the same in pptx (the Title Slide layout is the band; a deck's
  photo goes into the band box). (3) beamer-livery-theme #15 (3.2.0) and this repo #19: Ben
  asked whether pandoc's choice among several title layouts could carry a closing style and
  NCAR's white title. Tested: pandoc picks by name only, takes the later of two same-named
  layouts (undocumented) and carries any other layout untouched; so every template gains
  `Closing` and `Title Slide (light)` and `slide_layout.py` re-points slides at them. The light
  title now follows the brand's own light cover (UCAR Communications' template, slide 4):
  foreground text and the wave lines alone, white between them, in all three formats. Found on
  the way: the revealjs filter normalized a flavor's `../cu/` paths through the deck's
  `_livery` link into the deck itself; it now resolves the livery physically. (4) This repo:
  `docs/common/liveries/nsi/` (marks, art and measurements from the deck, cu's palette, fonts
  and sign-off; a one-color black NSI mark for the gold fields, where the gold mark vanishes,
  until NSI supplies one; cu's white RIO lockup redone with the monogram kept). Decided with
  Ben: the deck's satellite photo behind content slides, the campus photo as the band's
  default, the constellation closing. Ben checked the NSI website's logo: it is a 375 px
  raster without "Center for", so the deck's 1316 px lockup stays. Next: the plain CU Boulder
  lockup for cu (the CU CDN serves `cu-boulder-logo-text-{black,white}.svg`), then NASA.

- **2026-10-16** Cleanup sprint before the NSI flavor (beamer-livery-theme PRs #11 and #12;
  this repo's sprint PR). With hindsight from CU, three contract gaps blocked NSI: one logo
  per background (NSI has a unit mark and a sign-off lockup), `extends` losing the parent's
  `art.*` paths, and pptx placing only `art.content`. Decided with Ben: the sign-off goes
  bottom-left and the page number moves right, both as livery parameters with today's layout
  as the defaults. The contract gains `signoff` (light and dark images, aspect, height,
  bottom, corner), `geometry.logo.corner` (top-right | top-left | none: none drops the mark
  everywhere, keeping its room on fields) and `geometry.pagenumber.corner`, drawn by all
  three themes and the template builder; `typography.headings` may now be a second family
  with files of its own (the beamer titles, reveal's heading font and the pptx major font
  follow; cu sets TeX Gyre Heros Cn for the brand's condensed headlines); `overrides/
  livery-extra.css` joins `livery-extra.sty`; the builder places `art.title` and
  `art.section` on their layouts and stores a file used twice once. Found on the way: pandoc
  never writes a slide-number box, so no pptx deck had numbers; `slide_layout.py` now copies
  the layout's placeholder onto every slide. Tooling: `make vendor-engine` syncs an engine
  checkout into the vendored copy (an unmerged engine branch testable in the framework),
  `parity.sh` snapshots every deck under every livery in `PARITY_LIVERIES` (ncar as the
  parity fixture, cu as the regression check). `livery_check.py` (section 6 step 3) checks
  build freshness, the files the data names, the template's pandoc compliance and that it
  rebuilds byte-identically from the data, and warns on small-text contrast (the ncar family's
  muted gray is 4.2:1 on white); CI runs it per livery, and the README gained an "Adding a
  livery" walkthrough. cu's content background is the deck's Flatirons photo, muted (Ben's
  pick over the space photo and a faint monogram). Next: NSI, from `docs/design/nsi-handoff.md`
  (written for a fresh session: the repos, the contract as it stands, the deck's facts, the plan).
- **2026-10-16** The first non-NCAR livery: `cu` (University of Colorado Boulder), a real
  directory in `docs/common/liveries/` (this repo PR #13; beamer-livery-theme PR #10). The
  reference is the CU Center for National Security Initiatives' master deck (Ben's download, a
  Google Slides export; not committed, `reference/notes.md` records it), the brand site the
  stricter authority. Decided with Ben: a generic `cu` now and an `nsi` flavor later; the
  pptx names Helvetica Neue unembedded (Monotype's font cannot be bundled) while HTML and PDF
  bundle TeX Gyre Heros, the free Helvetica clone, in `.otf`; the generic title composition
  first (the deck's black field with a gold band is a follow-up `title: band` style); a faint
  picture behind content slides as `art.content` (the deck's own pre-faded space photo, since
  the buffalo marks are Athletics'); the deck's Research & Innovation Office lockup as the
  placeholder until the plain CU Boulder lockup arrives from the CU-only lockup library. What
  the onboarding tools got right: inspect, build, template and the CI matrix took the new
  directory as is. What needed code: the engine assumed `.ttf` (fontspec `Extension`, the
  bundled-copy probe, the math ranges, the css `format()` hint); a livery's partial
  `pptx.scheme` replaced the whole slot contract instead of overlaying it (CU needs only the
  link slots changed, gold being inaccessible on white); `livery_build.py` exited on a
  missing template that `livery_template.py` was about to build; the revealjs theme still fed
  reveal's own custom properties (`--r-main-color`, `--r-link-color`, the fonts) from NCAR
  Sass literals, so the HTML wore navy and Poppins under any livery, now restated from the
  roles; `embed_fonts.py` exited without font blobs; the template builder had no
  `art.content`; the pptx cover had no shape without waves (now a straight edge, as the two
  themes draw); CI's font-embedding check assumed blobs. Also decided: the dark-field lockup
  is the dark-text one, the gold field being light. Next: the `nsi` flavor, the band title
  style, Heros Condensed headings (a second family in the engine), `livery_check.py`.
- **2026-10-16** The brand cover in pptx (this repo PR #11, with the template builder). Ben
  on the sample's `.feature` slide: "this was supposed to be a image eclipsed with solid like
  my sample covers ... my original slide master just required the image be 'pushed to back'
  in the pptx ordering and had the waves overlaid; then we adapted this to Beamer with the
  cutting". So no clipping in pptx: `slide_layout.py` pushes the photo (pandoc's slide
  background for `.feature`, the `titlegraphic` pandoc records in `docProps/custom.xml` for
  the title slide) to the back of the slide as a full-slide picture cropped to cover, then
  draws the livery's opaque field to wave line 2, a 65% band to line 3 and the three lines
  over it, the dark lockup, and (feature) moves title and body onto the field; the title
  slide copies its layout's tab and rule onto the slide, since slide shapes always draw above
  layout shapes. The custGeom builders moved into `utils/pptx_waves.py`, shared with
  `livery_template.py`. Reviewed with LibreOffice on the sample, the quickstart and a test
  deck with a `titlegraphic`. Next: `livery_check.py`, the Canto wave vectors, then CU.
- **2026-10-16** Phase 3 begun, a light pass on the NCAR family first (Ben: "refreshing our
  own NCAR/ucar/ucp from the sample pptx and canto elements, then CU"). `livery_inspect.py`
  (this repo PR #10) read UCAR Communications' four official templates into each livery's
  `reference/report.md` (beamer-livery-theme PR #8): a 10 x 5.625 in canvas, 5% margins with
  the body from 27% down, PowerPoint-named layouts with few placeholders (the covers are flat
  pictures), a theme two digits off the guide, Aptos as scheme font. Decided with Ben: keep
  the 13.33 x 7.5 in canvas, a full-width body with small margins, the title slide rebuilt
  from parts. `livery_template.py` (this repo PR #11) generates a livery's `template.pptx`
  from its data: theme slots by the slot contract (`livery_build.py` now derives
  `pptx.scheme` from the roles, `SLOT_ROLES`; a flavor no longer inherits its parent's), the
  typeface, the master with title, tab, rule, lockup and faint waves at the HTML/PDF geometry,
  the seven pandoc layouts with the chrome placeholders at idx 20-22 (a trap: pandoc matches
  content boxes by idx, and a date at idx 2 swallowed a second column). The four liveries
  (beamer-livery-theme PR #9) each have their own generated template; the UCAR, UCP and
  NSF NCAR-UCAR web logos are the brand kit's RGB PNGs from Canto, whose portal is public
  with a REST API (ids in the memory notes). Reviewed: both reference decks rendered with
  LibreOffice (Poppins installed in its profile fonts) slide by slide. The ncar pptx is thus
  no longer byte-parity with upstream, by design; PDF and HTML are unchanged. Next: the title
  photo (`titlegraphic:` into the pptx title slide, clipped to wave line 1), `livery_check.py`,
  then the Canto wave vectors (PDF-compatible .ai: Fills A-H, Lines-Only, narrow) as an art
  option to reassess the curves-as-data choice, then CU.
- **2026-10-16** Phase 2 complete, step 5 (beamer-livery-theme PR #7, this repo PR #9): the
  waves leave the engine as data, not files. Decided with Ben against section 4's letter:
  static art per slide kind would freeze the roles' colors into files per livery, drop the
  photo-in-the-wave title slide (a clip path has to exist at render time) and change nothing
  in pptx, whose master waves are already a raster. So `art.waves` in `livery.yml` carries the
  three curves (control points, `tools/fit-waves.py` prints the block) and the per-kind
  shifts; `livery_build.py` writes the TikZ macros into `livery.sty`, the Lua reads
  `livery.json`, the pptx divider layout is built from the same numbers. A livery without
  `art.waves` draws plain fields (straight-edged title photo); a livery may name a static
  background file per slide kind (`art.title|section|closing|content`), placed by both
  formats (tested with a throwaway flavor). To be reassessed once the brand kit's own wave
  art (Canto) has been looked at. Parity: every PDF page pixel-identical, every HTML slide
  pixel-identical. The engine now holds no NCAR data: palette, roles, fonts, logos, geometry
  and art are the livery's. Section 7's Phase 2 is done; the framework's `liveries/ncar`
  is a link to the vendored reference livery. Next: Phase 3, the first foreign livery, with
  the onboarding tools of section 6 (`livery_inspect.py`, `livery_template.py`,
  `livery_check.py`), measured against the brand's official pptx templates on Drive; and the
  template question, since the ncar template's own geometry is tighter than the brand's.
- **2026-10-16** Phase 2, step 4 (beamer-livery-theme PR #6, this repo PR #8): geometry from
  the livery. The `geometry` block (fractions of the slide) carries the margin, the tab, the
  logo's height per slide kind, top and aspect, the divider block's padding and the
  full-figure lengths; `livery_build.py` emits `engine@geom@*` and `--engine-*` pixels; the
  beamer themes, the Sass, `section_subtitle.py` and `slide_layout.py` read them. The ncar
  values are the themes' own, unified where HTML and PDF disagreed (content logo 0.0644, the
  HTML's; title, section and closing logos 0.09, 0.08, 0.10, beamer's), so the PDF content
  logo grew 7% and the HTML brand-field logos grew. Decided with Ben: the pptx template's
  tighter geometry (3% margin, an oversized logo) is NOT the source of truth; he tuned it by
  hand for figure room and wants it toned down. The brand's official pptx templates for all
  four lockups (UCAR Communications, April 2026) sit in a Drive folder (see the memory
  notes); they are the reference decks for section 6 and the yardstick for loosening the
  ncar template. The slide paddings and title rule of the two formats remain engine
  constants (each format's own). Next: step 5, the waves as art files, closing Phase 2.
- **2026-10-16** Phase 2, step 3 (beamer-livery-theme PR #5, this repo PR #7): roles only.
  No palette name is read outside `build/livery.sty`: the color, inner and outer themes, the
  check marks and listings style, Quarto's callouts and the Sass all read roles, with a new
  `highlight` role (ncar: UCAR Aqua Contrast, the guide's small-text accent) and the blends
  `alert-text` and `rule`. The Sass keeps its `$ncar-*` variables as the compile-time defaults
  Quarto's own rules need, sets every engine color as `var(--engine-*)`, and restates the
  visible Quarto rules (links, code, callouts, asides, selection) with the roles; mermaid's
  `--mermaid-*` come from the livery's css. `engine.theme` is now the highlight theme's
  template (`$role` colors) and `livery_build.py` fills `build/livery.theme`; the formats
  default to the ncar copy and the shared `_quarto.yml` points `highlight-style` at
  `_livery/build/livery.theme`. Parity: text and HTML unchanged; every HTML slide of both
  engine decks pixel-identical; the PDF pages that differ are the footnotes and full-figure
  captions (CoolGray7 joins the muted role, planned since Phase 1) and, in the ucar and ucp
  variants, the places where NCAR blue leaked (check marks, code keywords, the feature
  subtitle). Also in: the `ucp` livery (PR #4), a flavor of `ucar` with the UCP lockup, so the
  engine carries the guide's full set. Next: step 4, geometry from the livery (the lengths in
  `beamerouterthemeEngine.sty` and the Sass, `section_subtitle.py`'s block, the logo heights
  per livery), then step 5, the waves as art files.
- **2026-10-16** Phase 2, step 2 (beamer-livery-theme PR #3, this repo PR #6): the engine
  reads a livery. `_extensions/engine/liveries/{ncar,ucar,ncarucar}` hold the reference
  liveries (the framework's ncar livery with its fonts and logos moved beside it; `ucar` and
  `ncarucar` as flavors with `extends: ncar`, their inherited paths rebased), built by
  `_extensions/engine/livery_build.py` into `build/livery.{json,sty,css}` (the `.sty`: palette
  and roles under the LaTeX names of `livery.yml`'s `latex.colors`, logos, fonts, geometry,
  the override files appended inside a catcode guard; the `.css`: `@font-face`, `:root
  --engine-*` roles and blends, the logo box, the logo rules). `\usetheme[livery=<dir>]{Engine}`
  inputs the `.sty` (`brand=` is its old spelling, `fonts=brand` of `fonts=poppins`);
  `engine-beamer.lua` and `engine-revealjs.lua` take the directory from `livery:` else the
  bundled `liveries/<brand>`; the HTML dependency is the livery's css with its font and logo
  files, the Sass reads the logo box and roles as custom properties, and `ncar-assets/` is
  gone. Parity: every PDF page pixel-identical (183 pages, the brand variants included), the
  HTML identical except the dependency file and the dropped brand class, every HTML slide
  pixel-identical in a Playwright comparison. The framework's `liveries/ncar` is a link to the
  vendored copy, its `livery_build.py` the vendored one. Next: step 3, every remaining raw
  palette read in the themes moved to a role (section 1's list), then geometry, then art.
- **2026-10-16** Phase 2 begun: the rename (beamer-livery-theme PR #2, this repo PR #5).
  The theme is `_extensions/engine/` with the formats `engine-beamer` and `engine-revealjs`,
  `\usetheme{Engine}`, `engine_livery.sty`, the `engine@` namespace, `\engine*` commands and
  `engine*` frame keys, `engine-*` classes, properties and ids, and the `engine-layout:` notes
  line; version 3.0.0, untagged until Phase 2 is complete. Brand things keep their names
  (palette colors, `brand=`, `ncar-assets/`, the v1 shims). The framework re-vendors it,
  links `common/` as `_engine`, and its scripts, filters, CI greps and docs follow; both
  parity harnesses gained a `NORMALIZE` hook that folds the nouns. Parity with the nouns
  folded: identical except the version in the HTML dependency path, the compiled theme's
  hash, and the decks' own sentences and diagram labels that name the theme (the README
  screenshots were reshot for the mermaid slide). Next: `livery=` and the generated
  `build/livery.sty` in the engine, with the reference liveries under
  `_extensions/engine/liveries/` and `livery_build.py` moving there.
- **2026-10-16** Phase 1 complete (PR #4): `link_captions.py` and `linked-images.lua`
  take muted from the livery (the Lua filter reads `build/livery.json` by the `livery:`
  metadata key, else `$LIVERY_DIR`, else `_livery`); `deck_qa.py`'s edge is `1 - margin`
  (the redundant `geometry.edge` key is gone); `site_index.py` draws the index from the
  roles (dark mode blended toward `dark` with `livery.mix()`) and copies the base family's
  files to `_site/fonts/` as `@font-face`, a Google Fonts link only for a `google` source;
  `ci-liveries.yaml` is the livery matrix (listed from the directory, so a new livery joins
  by existing; it checks the stamp and link, the primary slot in `theme1.xml` and the
  typeface in `embeddedFontLst`; the `livery.css` check waits for the engine). Parity held
  byte-for-byte for both decks; the QA report and the index page were compared separately
  (identical report; the index indistinguishable in light and dark mode). Every post-render
  script and filter now reads the livery; what still names the brand is the engine's
  (`ncar-layout:`, `ncar-section-*`, the `_ncar` link, the `ncar-*` formats). Next: Phase 2
  in `beamer-livery-theme`, the engine refactor of section 5.
- **2026-10-16** Three more post-processors read the livery (PR #3): `section_subtitle.py`
  takes the divider label, the tab (`geometry.tab`, `divider.tab`) and the fonts it measures
  with (`typography.headings` 700, `typography.base` 400, via `livery.font_file()`);
  `style_tables.py`, `style_footnotes.py` and `slide_layout.py` take their colors as scheme
  slots (`dk2`, `accent4`, resolved to hex through `pptx.scheme` so the XML stays `srgbClr`),
  roles (`muted`, `warning`) and the new `derived` blends `livery_build.py` computes from the
  roles (`table-rule`, `table-band`, `caution-fill`; a `derived:` key in `livery.yml`
  overrides). Settled on the way: `divider.label` is `Section` (each format sets the
  capitals), `muted` is `#6B7C99` (the HTML and pptx value; the PDF's CoolGray7 `#6686AF`
  joins it in Phase 2), and the caution bar is the `warning` role because the ncar template's
  `accent5` (`FDD509`) is not the brand yellow. Parity held byte-for-byte at each step. Next:
  `link_captions.py` and `linked-images.lua` (muted from the livery; Lua through
  `quarto.json.decode` of `_livery/build/livery.json`), `site_index.py`, `deck_qa.py` (`EDGE`
  from `geometry.edge`), then the CI livery matrix.
- **2026-10-16** Phase 1 begun (PR #2): `utils/parity.sh baseline|check` snapshots both
  reference decks and gates every step; `branding/ncar/` is `liveries/ncar/` with
  `_brand.yml`, `livery.yml` and the generated `build/livery.json` (`livery_build.py`,
  `--check` in CI; `utils/livery.py` reads it); `Make.common` has `LIVERY`, the exported
  `LIVERY_DIR` and the `_livery` link that follows the stamp; `_quarto.yml` takes the
  template from `_livery/` and names `livery: _livery`; `embed_fonts.py` (was
  `embed_poppins.py`) takes the blobs and typeface from the livery. Parity held at each
  step; the only differences were pandoc's metadata dump (`docProps/custom.xml`, now
  excluded) and the sample deck's slide 27, which quotes `_quarto.yml`. Next: section 5's
  remaining post-processors, one per commit (`section_subtitle.py` first: divider label
  and geometry from the livery), then the CI livery matrix.
- **2026-10-16** Phase 0 done. Nouns settled (section 2), the design merged into
  `quarto-docs-framework` (#31) and the two repositories created from the full
  histories: `benkirk/beamer-livery-theme` (NCAR_beamer_template `724c3e6`, v2.8.0)
  and `benkirk/quarto-livery-decks` (quarto-docs-framework `cfeb1f7`). Each carries
  the design, a CLAUDE.md and a README banner; `upstream` remotes point at the NCAR
  repos. The fresh clone builds: `docs/quickstart` renders all three formats with
  `make qa` clean; `docs/sample` renders but its PDF QA fails on pre-existing overflow
  (slides 3, 6, 9, 27), so for the sample deck parity, not QA, is the Phase 1 criterion.
  Not done: `BENKIRK_GITHUB_TOKEN` for `cron-clean-action-log.yaml` (Ben).
