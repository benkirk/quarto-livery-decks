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

**Since 2026-10-18 (#57) the engine lives in `quarto-livery-decks`**: `beamer-livery-theme` merged
in with its history (the engine at `_extensions/engine/`, its LaTeX examples at `latex/`, its
tests at `tests/`, every livery in `liveries/`, since the flatten of the same day; until then
all under `docs/`), to be archived on GitHub;
one version number, `_extension.yml`'s, tags the one repo. The rest of this section is the
two-repo arrangement as designed and run from 2026-10-16 to 2026-10-18.

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
                  feature {style: bar | cover}: the photo slide's look; compositions
                  {<name>: {<key>: ...}}: overrides of the composition boxes (section 5);
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
                  livery.json   the one resolved truth, extends applied, geometry, marks,
                                compositions and type included; Lua (quarto.json) and
                                Python both read it
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
  link to the vendored copy. (Since #57 nothing is vendored: every livery is in
  `liveries/`, and the bundled fallback is `liveries/<brand>` beside the
  `_extensions/` that holds the engine.)

**Compositions** (2026-10-17, `composition-handoff.md`): the title (cover, photo, light,
photo-light, band), closing (cover, light, band), section and feature slides are each one
composition, described once in `build/livery.json` as `compositions.<name>`: named boxes in
slide fractions (`field`, `photo`, `band`, `bar`, `panel`, `mark`, `signoff`, `column`,
`fineprint`; `[x, y, w, h]`, y down) plus the non-box parameters (`art` kind, `waves {style,
shift, opacity, line}`, roles, the column's `anchor`, `rule`, `tab`, the section `eyebrow`).
`livery_build.py` derives them from the knobs a livery already sets (geometry, title, signoff,
marks, art, divider) and merges an optional `compositions:` override; `feature.style: bar |
cover` picks the photo slide's look per livery. Every format has one drawer that places its
parts in those boxes (beamer `\engine@drawcomp`, the scss on `--engine-cmp-*` variables, the
template builder's `field_layout`, the framework's `slide_layout.py`), so no composition
number lives in theme code, and `comp_measure.py` (`make measure`) checks every format against
the boxes; `design/compositions-baseline.md` is the before-picture. A new composition, or
a livery's own look for one, is data: a box override in `livery.yml`, not a fifth drawer.

**Type** (2026-10-17; points since engine 3.6.0): a livery states its text sizes in **points on
its pptx canvas**, whole or half points, so a slide pasted into a hand-made deck carries round
numbers: `livery.yml` `pptx.size` (inches) and `type:` (role -> pt, the five list `levels`). The
engine's default (`livery_build.py` `TYPE`, `LEVELS`) is the NSF NCAR template's guidance carried
onto 13.333 x 7.5 in and rounded (body 16, levels 16/15/13/12/11, slide titles 27, cover 29,
dividers 40); a role a livery leaves out is that default scaled by its canvas (the body roles
by its body), to the half point. ncar takes the guidance itself on the brand's 10 x 5.625 in
(body 12, levels 12/11/10/9/8, titles 20, subhead 15, tables 10, cover 22, bold statement 30);
cu the NSI master deck's on 13.333 x 7.5 in (body 16, titles 32, cover 48 with the date 28,
dividers 60). `livery.json` `type` has the canvas, each role's points, its ratio to the body
and its leading, and the body's share of the height: HTML (`--engine-type-*`) and beamer
(`\engine@type@*`) set the same share of the slide, the template builder the points, the
post-processors `livery.type_pt()` and `canvas_scale()`, so a slide fits and overflows alike in
every format. `scale=` keeps working everywhere, a pptx size rounded to the half point.

For `quarto-livery-decks`:

- The post-processors keep their jobs and lose their constants, parameterized by
  `livery.json` and scheme slots: `embed_fonts.py` (was `embed_poppins.py`; typeface
  and blobs from the livery), `section_subtitle.py` (fonts to measure with, divider
  label and geometry), `style_tables.py`, `style_footnotes.py`, `slide_layout.py`
  (slots; muted and caution fill from the livery), `link_captions.py`,
  `linked-images.lua` (`quarto.json.decode` of `livery.json`), `site_index.py`
  (palette and font family; a Google Fonts link only for a google source),
  `deck_qa.py` (`EDGE` from the livery's margin).
- `Make.common`: `LIVERY ?= ncar`; `LIVERY_DIR ?= $(SHARED_LIVERIES)/$(LIVERY)`;
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

**Tools**, in `common/utils/`:

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
   `make -C decks/quickstart qa LIVERY=<name>`.

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
4. NASA general (done 2026-10-17: `nasa` and its dark flavor `nasa-dark`, engine 3.8.0), then
   the NASA programs (Artemis, Commercial Crew, ISS): Ben expects them to bear no relation to
   the general livery, so each stands alone rather than extending it.

Before step 4 (done 2026-10-16, engine 3.3.0): the post-NSI refactor (`docs/design/refactor-handoff.md`): the pptx template
tooling moves into the engine, marks are keyed by the field's role (`marks:`), and five cheap
fixes (unknown keys warn, livery files as make prerequisites, a fixture deck in parity and CI,
absolute art paths in beamer, flavors inherit `pptx.scheme` overrides), and a livery may
prefer an installed font over its bundled stand-in (`installed-fonts:`; cu: Helvetica Neue,
used where installed, never shipped).

**Before NASA (2026-10-17): one description of each composition.** The title, closing,
section and feature compositions are drawn four times (beamer, revealjs, the template builder,
`slide_layout.py`) in two repos, and the copies drift (about twenty quantities in three to
five places, several already disagreeing). Deferred after NSI "until the next new
composition"; NASA is that, so it goes first: compositions described once as boxes in slide
fractions in `livery.json` and drawn by every format (section 5, "Compositions"), in ten PRs
written up for a fresh session in `docs/design/composition-handoff.md`. Done 2026-10-17
(engine 3.5.0), with a type-size pass across the formats (section 5, "Type").

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

- **2026-10-18, `docs/` flattened; version 1.0.0** (this repo, `flatten`). Ben: "a lot of core
  infrastructure in docs". Everything moved up a level: `Make.common`, `_extensions/engine/`,
  `liveries/`, `common/` (`_quarto.yml`, the Lua filters, `utils/`), `decks/` (quickstart,
  sample, fixtures), `latex/`, `design/`, beside `tests/`. Decks include `../../Make.common`,
  a consumer `../framework/Make.common`, the container `make -f /opt/quarto-livery-decks/Make.common`.
  The engine's livery lookup is unchanged (liveries beside `_extensions/`); LaTeX's
  `TEXINPUTS` names `_extensions/engine//` and `liveries//` as an Overleaf zip does, never the
  root's `//` (it would reach `conda-env/`). The two NCAR decks, `sam_and_pbs` and
  `new_user_samples`, left the repo (they read hpc-scheduling-tools' data; the history keeps
  them). The engine's version became 1.0.0 (`_extension.yml` and `engine-revealjs.lua`'s
  `VERSION`, which had lagged at 3.7.0), and v1.0.0 is cut again over the first one: the repo
  was two days old and Ben its only user. Parity against the morning's baselines: unchanged but
  for the named text (the quickstart's closing slide names `decks/`, the sample's
  project-config slide shows `_quarto.yml`'s corrected comment, the LaTeX demo's install line
  names the framework's Makefile) and the HTML dependency's version, folded by `NORMALIZE`.
  Next: #57 Phase B.
- **2026-10-18, one repository** (#57 Phase A; this repo #60 the move, #61 CI, #62 docs).
  Ben chose the bold option of the retrospective: `beamer-livery-theme` merged in with its
  history (a fresh clone through `git filter-repo --to-subdirectory-filter engine-import`, an
  unrelated-histories merge after the vendored copy was removed, so `git log --follow` pairs
  each file with the engine's own and reaches back to the 2026 brand rebuild). The engine is
  `docs/common/_extensions/engine/`, every livery `docs/common/liveries/` (ncar a real
  directory; ucar, ucp, ncarucar beside it, so the CI matrix and the release zips are eight),
  the LaTeX examples `docs/latex/`, the tests `tests/`. A deck's `brand=` without `livery:`
  finds `liveries/<brand>` beside the `_extensions/` that holds the engine, from the
  extension's real directory; `_extension.yml`'s default highlight style is resolved lexically
  by Quarto, so `docs/latex/examples/` links `liveries` beside its `_extensions`. CI's new
  `latex` job runs the engine's tests and builds its examples; `release.yml` requires the tag to
  equal `_extension.yml`'s `version:`. Parity, baselines on `main` the same morning: every deck of
  quickstart, sample and fixtures under ncar, cu, nsi, nasa and nasa-dark unchanged (pptx XML,
  PDF text and pages, HTML), the engine's 195 LaTeX pages pixel-identical, all eight templates
  rebuilt byte-identically. Changed from the plan: `fit-waves.py` went to `docs/common/utils/`;
  `test_type.py` now checks every livery's template, not only the engine's four; the
  `quarto-demo.qmd` install line and `_quarto.yml`'s "vendored" comment wait (both are deck
  content, the sample quotes `_quarto.yml`). Open with Ben: the release number (v4.0.0
  proposed), archiving `beamer-livery-theme` with a banner, and whether to flatten `docs/`
  before that release. Next: Phase B, the pptx format into the engine.
- **2026-10-17, nsi content titles** (stacked on the NASA work: beamer-livery-theme `nsi-title`,
  this repo `nsi-title`; still 3.8.0). Ben compared an nsi text slide with Lindsay's slide 20 of the
  NSI master deck: her mark is larger, her titles centred, no gold tab; and our PDF's title sat
  high against the mark. New livery knob `frametitle: {align, tab, rule}` in all three formats; the
  body starts below a mark taller than ncar's (`frametitle.body`); beamer now centres the content
  title in the band HTML and the pptx template use (44-114 px of 900, the rule at 130, the body at
  150), which moves every livery's PDF titles a little. nsi: centred, no tab, no rule, its mark
  0.135 tall from 0.04 and 0.015 from the paper's edge (the deck's; new `geometry.logo.inset`). See `nsi/reference/notes.md` for what still differs.
- **2026-10-17, NASA general, light and dark** (beamer-livery-theme 3.8.0; this repo
  `nasa-livery`). Ben asked for a general NASA style for external communication in light and
  dark, with the preferred fonts and the meatball; there is no official template, so we take
  liberties. Sources: the Brand Center's guidelines (the 2024 color guide: NASA Blue `#0032A0`,
  Red `#E4002B`, superseding the `#0B3D91`/`#FC3D21` still quoted elsewhere; the insignia rules;
  the Horizon digital faces) and NASA Science's public-engagement deck (10 x 5.625 in, black
  slides, insignia top right; `nasa/reference/report.md`). Decided with Ben: the Horizon faces
  (Inter, Public Sans, DM Mono) for all text, Helvetica only inside the agency-name artwork;
  the insignia top right and the agency name as the sign-off, which together are the brand's
  preferred identifier; dark *content* slides, diagrams included; NASA photography. Two
  liveries, `nasa` and `nasa-dark` (`extends: nasa`); a deck-level mode switch would need
  engine design. The insignia comes from the Brand Center's own SVG, recolored to the 2024
  values, plus the guide's one-color white-rule version for the NASA Blue fields
  (`nasa/reference/nasa_marks.py`). Engine 3.8.0 (one PR): a `code-text` role (code was drawn
  in `dark`, a field color), beamer tints mixed toward the background rather than white, an
  overridden blend reaching beamer, `livery.json` `mode` (dark when the background is darker
  than the foreground) with dark-only css (callout title tints; a CSS lightness flip for inline
  Graphviz), contrast checks for the code and blend pairs, and `typography.monospace` (a
  bundled code face; DM Mono). The engine's four liveries rebuild their templates
  byte-identically and its 202 PDF pages pixel-identically. Here: Quarto bakes mermaid and
  dot cells to PNG before any Lua filter runs (tested even `at: pre-ast`), so
  `diagram-dark.lua` recolors the baked pictures (`utils/diagram_dark.py`: HLS lightness
  flipped, hues kept), in pptx and in beamer's raw LaTeX and `enginefull=` frame option; the
  pptx now takes the livery's highlight theme like HTML and PDF (a small visible change for
  ncar and cu: their pptx code wears their HTML colors), and pandoc's `monofont` from the
  livery. nasa's body is 12 pt, the share of the slide ncar's and cu's take (14 and 13 overflowed the sample deck's dense PDF slides into the sign-off).
  Follow-ups: whether the code-face treatment should be backported to ncar, cu and nsi (Ben);
  a native pptx `clrMap` swap for dark liveries (now `dk1` holds white); the fntdata blobs for
  embedding the Horizon faces (one PowerPoint save by Ben). Next: the NASA program liveries.
- **2026-10-17, the container image** (this repo, `container-image`). Ben asked for the CI to
  be audited and for a product: the build environment as a multi-platform image a customer
  bind-mounts a deck directory into. `ghcr.io/benkirk/quarto-livery-decks` (root `Dockerfile`:
  ubuntu + micromamba on the same `conda-env.yaml`, apt TeX Live, LibreOffice, a broad font set,
  one Playwright headless Chromium for Quarto and `make qa` alike; activation baked as `ENV` and
  asserted against conda-forge's activate.d) is built natively on amd64 and arm64 runners and
  merged into one manifest list (`image.yaml`, after sam-queries' workflow), each leg smoke-tested
  on its host as a plain user with a mounted deck directory. A bare directory of `.qmd` files
  builds with `make pptx` (the entrypoint supplies `Make.common` and `DECKS`); `Make.common`
  re-points a dangling link so host and container builds alternate. The three CI workflows became
  one, `ci.yaml`, whose deck jobs run inside the image: no conda, TinyTeX, apt or chrome steps,
  no login-shell `set -e` gaps, `make qa` per livery at last; the cron job lost its PAT and a
  deprecated action. README "Building in the container".
- **2026-10-17, the SAMuel stress test** (this repo #45-#48; `stress-test-findings.md`). The 13
  SAMuel decks, tuned on theme 2.8.0, rebuilt unchanged under ncar and nsi: every deck in every
  format, counts identical to the old outputs, `make qa` clean. Per-slide verdicts (fits, sparse,
  overflows) agree across the three formats on 201 of 208 content slides under ncar and 204 under
  nsi, against 187 on the old outputs; the PDF body is 0.95x HTML's and pptx 1.01x (old: 1.21x,
  1.20x). The old `scale="1.15"` slides now fill 0.40 of the body in every format (sparse, not
  broken), and a deck-wide `type-scale:` moves every format alike but cannot replace per-slide
  tuning. Fixed: `comp_measure` matched the cover as the divider (#45) and drew pptx shots in a
  serif (LibreOffice reads no embedded fonts; #48); the caution box was cut before `scale=`
  (#46); the nsi band cover's pptx rule sat above the subtitle (#47). Then code sizes (#50, engine
  #35, 3.7.1): pptx sets code at the body's size, which Ben preferred, so the `code` role went
  up to meet it (ncar 10 pt on 12, cu and nsi 14 on 16). nsi's pptx titles, regular-width where
  HTML and PDF are condensed, are left to PowerPoint's autofit.
  Next: NASA.
- **2026-10-17, type in points** (beamer-livery-theme #32, #33, 3.6.0; this repo #40, #41). Ben
  asked whether the sizes were "nice" numbers: pptx slides get pasted into decks people keep by
  hand, and ours carried 16.79/15.11/13.6/12.24 pt, on a canvas a third larger than the brand
  template's. Now sizes are points on the livery's canvas (section 5, "Type"), defaulting to
  the brand's style guide: ncar on the NSF NCAR template's 10 x 5.625 in and its guidance (body
  12, titles 20), which its UCAR, UCP and NCAR-UCAR templates share; cu on the NSI master deck's
  (body 16, titles 32, cover 48, dividers 60). The post-processors lost their 13.33 in constants
  (slide pixels, points per pixel, pads). Found on the way and fixed: beamer's `scale=` left
  tables and code at their size (since 3.5.0); plain verbatim was set at body size; LM Mono ran
  13% narrower than HTML's monospace (now 1.15, the same line width); `deck_qa.py` read page
  numbers only bottom left. Checked against the references: five slides of each brand's own
  deck rebuilt with the same content, side by side, similar in size and wrapping. Still open:
  the sample deck's "Project config" slide (PDF: the code runs off the page and the right
  column doesn't paint, on main too). Then the deck-wide size step (beamer-livery-theme #34,
  3.7.0; this repo #42): front matter `type-body: <pt>` or `type-scale: <factor>` scales every
  size in all three formats (beamer `typescale=`, HTML `--engine-type-scale`, pptx
  `type_step.py` to the half point); `docs/fixtures/small.qmd` is `type-body: 10`. Then nsi's two measure misses (this repo
  #43), both older than the sprint: the sign-off's right edge read 0.028 short because the
  erosion that drops the band art's thin lines also took the lockup's thin "Office" (the
  lockup was drawn right in every format; `comp_measure.py` now widens the eroded core along
  its rows), and the pptx band stack sat 0.034 high, centred on its rule rather than as a
  whole (`slide_layout.py` `band_stack()` now centres date, title, rule and subtitle from
  their estimated heights). Every edge of the fixtures and the quickstart is now within
  tolerance under ncar, cu and nsi. Next: NASA.
- **2026-10-17, compositions as boxes** (beamer-livery-theme #21-#30, 3.5.0; this repo #34-#38).
  The title (cover, photo, light, photo-light, band), closing (and light, band), section and
  feature slides are one `compositions` block of boxes in `build/livery.json`
  (`livery_build.py compositions()`), drawn by one drawer per format: beamer
  `\engine@drawcomp`, revealjs the generic `--engine-cmp-*` properties and `comp_art()`, the
  template builder's `field_layout()` (with a new Closing (light) layout), and `slide_layout.py`'s
  `draw_cover`/`draw_feature`. The disagreements were settled per the handoff's table, one
  engine commit per row (`tools/test_compositions.py` names each change in `EXPECTED_DELTAS`),
  plus one the table missed (the band's mark goes right without a sign-off). `make measure`
  (`comp_measure.py`) shoots the four slides in every format and measures them against the
  boxes; `docs/design/compositions-baseline.md` is the before-picture. After the switch every
  HTML, PDF and pptx edge of the fixtures and the quickstart is within tolerance under ncar, cu
  and nsi, except nsi's sign-off right edge (the same before: the lockup's thin type on art)
  and the band's two-line pptx title stack (0.038, pptx centres it on the rule). Decided on the
  way with Ben: ncar's cover title text sits where the brand pptx template puts it (from 0.375),
  as the sprint's final commit; the feature looks are `feature.style: bar | cover`; ncar keeps
  the bar for photo slides inside a deck, the cover with waves being its title slide's (Ben,
  from a sheet of both in every format); on the feature panel beamer sets blocks as a heading over text
  (a beamer block box took the frame's margins and spilled past the panel). Open: the body type
  sizes disagreed across formats (PDF 0.043 of the slide height, pptx 0.037, HTML 0.031), deck
  wide and older than the sprint; at Ben's request a type pass made them fractions of the slide
  height (section 5, "Type"; HTML's scale, the brand template's): on a deck of plain content,
  block heights against HTML went from PDF 1.31x / pptx 1.10x to within 1-3% for lists, 6% for
  tables and 10% for paragraphs, the same line breaks in every format. Found on the way:
  `deck_qa.py` counted the feature's new bar as content; beamer still centres a frame's content
  vertically where HTML and pptx anchor it at the top. Next: NASA.
- **2026-10-17, the composition handoff.** Ben asked whether the deferred title-slide
  refactor should go before NASA. A code survey put numbers on the retrospective's friction:
  about twenty quantities (wave opacities, the cover band, the photo split, the mark offsets
  per kind, the sign-off box, the band's top/bottom/split, text column widths, the rule, the
  tab) hand-copied into three to five places across beamer, revealjs, the template builder
  and `slide_layout.py`, with real disagreements (pptx's feature is the cover with a mark on
  the photo; no light closing in pptx; beamer keeps the dark sign-off under `title=light`;
  HTML's percentages are of the padded box; beamer `\vfill`-parks section and closing text).
  Agreed: do it now, before NASA. Decided: scope title, closing, section, feature;
  disagreements settled per quantity (two formats agreeing win, else the HTML look unless the
  brand template gives a number); the title text anchors at the top under the mark; the
  feature look is per-livery data (`feature.style: bar | cover`), not one choice. Written up
  for a fresh session as `docs/design/composition-handoff.md`: the schema (ten resolved
  compositions, nine box kinds), each format's drawer and what it deletes, ten PRs with a
  measurement tool (`comp_measure.py`) and a committed before-picture. Next: that handoff,
  then NASA.
- **2026-10-17, the docs handoff done.** Engine 3.4.0: `overleaf_zip.py <livery> -o <zip>
  [--starter] [--photo]` packs any livery with the theme's `.sty`, `build/livery.sty`, every
  file LaTeX reads (fonts of any extension, the `.pdf` of a logo over its bitmap, the art, a
  flavor's parent files beside it) and a brand-neutral starter (`talk.tex` moved into the
  extension so a vendored engine has it) on `livery=liveries/<name>, fonts=bundled`; the
  engine's `make overleaf` uses it for ncar, its CI compiles ucp's too, and v3.4.0 is the
  engine's first 3.x release (its Overleaf link had served 2.3.1). Here: `make overleaf
  LIVERY=<name>`, `release.yml` attaching one zip per livery on a `v*` tag (v1.0.0 cut; tags
  are re-cut, not bumped, for backwards-compatible additions during the sprint),
  `ci-liveries.yaml` building the PDF and compiling each zip on an apt TeX Live, the README's
  per-livery Overleaf links. Both READMEs rewritten for liveries at about their length (the
  engine's with ncar | cu previews of the starter and a Liveries section, its design copy a
  pointer here; this one with the livery gallery, `make gallery`), the engine CLAUDE.md
  opening a list by area. Found on the way: a sub-make kept the exported `LIVERY_DIR` over its
  own `LIVERY=` (fixed: command-line `LIVERY` overrides). The About text is applied to both
  repos. The Overleaf smoke test (Playwright, Ben logged in; the four links opened as new
  projects and compiled on the free plan) found one more: under `fonts=bundled` `\sbseries`
  asked every livery for a semibold series, which TeX Gyre Heros lacks, a "Font shape
  undefined" warning per block title that Overleaf's panel counts as an error (engine #20:
  semibold only when the livery bundles one; v3.4.0 and v1.0.0 moved onto the fix). All four
  links now compile with clean logs. Next: NASA.
- **2026-10-17** Both READMEs still describe the single-brand world (the engine's is titled
  "NSF NCAR / UCAR Beamer Template", the framework's opens "NCAR-branded"), and a LaTeX user
  gets only the engine's reference liveries: the Overleaf zip packs `.ttf` fonts and PDF logos
  of `liveries/*` alone. Ben asked for both READMEs rewritten at about today's length with an
  NCAR and a CU example, Overleaf for any framework livery, and GitHub About text: written up
  for a fresh session as `docs/design/docs-handoff.md` (an engine `overleaf_zip.py`, per-livery
  zips released here, the two READMEs, the About text, three open questions). Next: that
  handoff, then NASA.

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
  the 13.33 x 7.5 in canvas (reversed 2026-10-17: ncar is on 10 x 5.625 in, `pptx.size`), a full-width body with small margins, the title slide rebuilt
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
