# Charts and plots in the livery

A design for plots that wear the brand, from one source of truth: the livery. It adds the
scientific Python stack to the image (matplotlib, numpy, pandas, seaborn, scipy), a chart-color
generator in the engine, and a plot style every format picks up. Written 2026-10-18 with Ben,
from a session that also fact-checked every livery's colors against its brand's published
sources (section 2). Implementation is section 9; the rest is the reasoning it rests on.

The principle is the one the engine already follows: **the livery is the source, and the engine
generates every chart color at build time**, beside `build/livery.{css,sty,theme}`. A livery
change recolors the plots, and `livery_build.py --check` keeps the outputs current.

## 1. Why a generator

Plots are basic to scientific publishing, and plots in the brand's colors and fonts, with no
effort from the author, are a real gain. But a livery's colors, as given, don't make a chart
palette. Measured with the dataviz method's validator (section 3):

| Palette | Result |
|---|---|
| sam-queries' NCAR facility set, light | passes every check |
| sam-queries' NCAR facility set, dark on `#011837` | passes every check |
| NASA's accents as the livery has them | fails: blue and yellow outside the lightness band, the gray reads as no color, yellow and cyan below 3:1 on white |
| CU's colors | fails: gold, navy and gray fail lightness or chroma; gray against sky blue is below the distinction floor for full color vision |

NCAR and UCAR specify many colors. CU really specifies one hue, gold, plus neutrals and two
blues. NASA specifies two brand colors and, separately, a full chart palette (section 2.2). So a
livery needs either a published chart palette or a generated one, and the generator has to be
brand-led: the brand's own colors first, invented hues last.

## 2. What the brands actually publish (fact check, 2026-10-18)

Every CU and NASA role and theme slot resolves to a color in that livery's own palette; no NCAR
value leaked in except white. The brand sites (colorado.edu, nasa.gov, ucar.edu) were blocked
from the session's network, so they were checked through search results and the brands' public
GitHub code. Anything that needs the sites or the brand guide is listed in section 9, step 5.

### 2.1 CU Boulder

All ten colors in `liveries/cu/_brand.yml` are the published palette. Primary: CU Gold
`#CFB87C` (PMS 4525 C), Black, Dark Gray `#565A5C`, Light Gray `#A2A4A3`. Secondary, used less
often: Accessible Gold `#8D7334` (text on white only), Sky Blue `#096FAE`, Light Gold `#F3F0E9`,
Dark Blue `#0A3758`, Light Blue `#EEF5F8`. CU Gold is "not accessible on a white background".
CU publishes no chart palette.

- **The web theme is not a brand source.** `CuBoulder/tiamat-theme` (8df166a, 2026-10-15) adds
  `--ucb-brick #AE5A39`, `--ucb-medium-blue #4FC3F7`, `--ucb-link #0277bd`, `--ucb-light-green
  #DCEDC8` and alert colors, mostly Material Design values: inspiration at most.
- **Another digital blue.** CU's accessibility page tests "Web Express Blue" `#0377BD`.

### 2.2 NASA

The nasa palette is part brand, part ours, part artifact.

- **NASA Blue and NASA Red are print colors.** The insignia is specified as PMS 286 and PMS 185
  (NASA's insignia guidelines for grantees). Our `#0032A0` and `#E4002B` are the standard sRGB
  values of those two Pantones. `liveries/nasa/reference/notes.md` cites the 2024 insignia
  color guide for them; that guide was not reachable to confirm the hexes.
- **NASA's screen colors are different.** The Horizon Design System, `nasa/hds-core` (f036e73,
  2026-10-07; CC0 public domain), is NASA's web design system:
  - `nasa-blue` `#1c67e3` (tint `#288bff`, shade `#0b3d91`, the old meatball blue);
  - `nasa-red` `#f64137` (tint `#ff5c52`, shade `#b60109`);
  - `international-orange` `#ea6f24`, `active-green` `#47da84`;
  - a carbon neutral ramp, `carbon-05` `#f6f6f6` to `carbon-90` `#17171b` (the dark-mode
    background), with `carbon-black` and `spacesuit-white`.

  Its usage rules: red means "go somewhere", blue "do something", and both are **"never for
  dataviz"**.
- **NASA publishes a chart palette.** HDS `tokens.json` `dataviz.color`, hand-authored in
  `src/scss/_hds-dataviz-palettes.scss`:
  - 11 sequential ramps (red, orange, yellow, gold, lime, green, aqua, slate, blue, purple,
    magenta), 10 steps each, 10 to 100;
  - 12 categorical colors for light (`#1159cd`, `#ef483f`, `#e8892e`, `#386470`, `#b0a26a`,
    `#3f83ef`, `#8f0800`, `#79a3ad`, `#3e1c99`, `#e09d00`, `#387d00`, `#0cc9ac`) and 12 for
    dark;
  - curated sets for 2 to 5 series, four options each, light and dark.

  Its rules: charts only, never UI; a 1 px divider between touching fills; to highlight, a
  saturated dark hue for focus against a desaturated light one for the baseline.
- **The rest of our nasa palette is our own invention**, as its notes already say: carbon,
  gray, silver, light-gray, sky, yellow, and nasa-dark's graphite, light-blue, light-red, steel
  and frost.
- **One copy-paste artifact.** nasa-dark's `cyan` `#00B0F0` came from the NASA Science reference
  deck, but it is Office's standard "Light Blue" swatch, not a NASA color. That deck's other
  theme slots, `#0B3D91` and `#E31937`, are the old NASA blue and red.
- **HDS against the validator.** Its full 12-color categorical fails the strict checks in
  places (the slates and gold are deliberately desaturated; orange beside red is ΔE 13.4 for
  normal vision). Its curated 5-series light set passes everything except chroma (the gold) and
  contrast (three colors).

Ben, 2026-10-18: the nasa liveries' screen colors are **decided later** (an issue carries the
findings); only their chart colors take HDS now.

### 2.3 NSF NCAR and UCAR

`liveries/ncar/_brand.yml` cites the 2026 "Vermilion" NSF NCAR / UCAR / UCP Brand Guide,
pp. 17-21. The guide is not online. The cross-checks:

| Source | What it shows |
|---|---|
| `NCAR/music-box-interactive` issue #588, quoting "our brand guide" | exactly our ten colors: NCAR Blue `#0057C2`, Dark Blue `#00357A` (the primary text color), UCAR Aqua `#00A2B4`, Space `#011837`, White, Light Gray `#F1F0EE`, Light Blue `#42C0FF`, Light Aqua `#34E1F4`, Orange `#FAA119`, Yellow `#FFDD31` |
| the four official 2026 templates (`liveries/*/reference/report.md`) | the same colors off by one in a channel (`#003479`, `#41C0FF`, `#FFDD30`, `#00A2B3`, `#34E1F3`): rounding, since the layouts are "Google Shape"s and the decks went through Google Slides. Their lt2 `#E8E8E8` is in CU's NSI deck too: a tool default, not a brand gray |
| UCAR's web theme, `NCAR/koru-jekyll` `assets/koru-base/scss/_variables.scss` (55ce7c3, 2026-09-03) | **brand tint ladders**, base / -33 / -66: ncar `#0057c2` `#6b8cce` `#adc2e6`, ncar light `#42c0ff` `#86d3fc` `#bfe5f9`, ucar `#00818f` `#00a2b4` `#71c0cb`, ucar light `#34e1f4` `#86e8f5` `#c0f0f5`, blue `#00357a` `#5a77a6` `#a8b7ce`, space `#011837` `#556379` `#a5adb7`, orange `#faa119` `#fabe72` `#f8dbb5`, yellow `#fdd509` `#fbe174` `#f8ebb7`; also red `#FF1F1F` and light gray `#f6f7f6` |
| `benkirk/sam-queries` `src/webapp/static/css/variables.css` (6e0f00d), citing NCAR's "Unity" `_variables.scss` (NCAR/unity is private) | the same family, plus `--ncar-vermilion` `#ff1f1f` ("NSF NCAR defining accent"), `--ncar-gold` `#fdd509`, grays `#97999b` and `#bbbcbc` |

Conclusions:
- **Our ten colors are right for the 2026 guide**: two independent copies agree to the digit,
  and the templates differ only by rounding.
- **The web themes are a generation behind in two places.** Their yellow is `#FDD509`, which
  our design log already calls "not the brand yellow" against the guide's `#FFDD31`. And koru
  makes `#00818F` UCAR's base with `#00A2B4` its tint, where the guide makes `#00A2B4` UCAR
  Aqua and `#00818F` its small-text contrast color.
- **Possibly missing from our palette:** vermilion `#FF1F1F` (the guide's edition is named
  for it) and the grays `#97999b` and `#bbbcbc`. Ben confirms against the guide (step 5).
- **The koru ladders are the brand's own ramps.** sam-queries' `UNITY_STACK_20` is built from
  exactly these steps.

Decisions (Ben, 2026-10-18): ncar's and ucar's `charts.ramps` take koru's ladders, the yellow
one rebuilt on `#FFDD31` with the tint blend fitted from koru's other ladders; the templates'
one-off values and their `#E8E8E8` are left alone and noted as a Google Slides artifact in each
livery's `reference/notes.md`.

## 3. The method

The dataviz method (the dataviz skill's color formula) supplies the jobs and the checks. A
palette does one of five jobs: categorical (identity), ordinal, sequential (magnitude),
diverging (polarity) or status (state). A categorical palette must pass:

| Check | Light | Dark |
|---|---|---|
| OKLCH lightness band | 0.43-0.77 | 0.48-0.67 |
| chroma floor | 0.10 | 0.10 |
| adjacent pairs under protan and deutan (Machado, Oliveira and Fernandes 2009, severity 1), target / floor | ΔE 8 / 6 | ΔE 8 / 6 |
| normal-vision floor, a hard gate | ΔE 15 | ΔE 15 |
| contrast on the surface | 3:1 | 3:1 |

ΔE is Euclidean distance in OKLab ×100. Its other rules: a categorical palette has at most 8
fixed slots, assigned in order (a 9th series folds into "Other"); for an all-pairs chart such
as a scatter, only the first three slots can pass; sequential is one hue light to dark,
diverging two hues and a neutral gray midpoint; status colors are reserved; dark is
**selected**, its own steps from the same ramps, never a flipped light palette. A sequential or
ordinal ramp is checked for monotone lightness (adjacent ΔL at least 0.06, the light end at
2:1), not for categorical separation.

**sam-queries** (`src/webapp/dashboards/charts/theme.py`, `static/css/variables.css`) adds what
years of NCAR dashboards taught:
- **Data colors versus chrome.** Hues are the same in both themes, so a series keeps its color
  on either page. Chrome (text, spines, grid, edges, the surface) is what a dark theme swaps.
- **Light keeps the brand palette as it is; dark lifts it.** On white, brand yellows below 3:1
  read fine beside their neighbors. On a dark surface the failing colors are the brand's own
  darks used as fills, and `lift_for_contrast()` tints them toward white just far enough. Tinting
  rather than raising lightness keeps three similar blues apart.
- **Large maps as hue families.** `UNITY_STACK_20` is 8 hues with 2-4 tints each, grouped and
  ordered warm to cool. The hue names the group, the tint the member: the composite encoding the
  8-slot rule allows, and the answer to "large maps that stay distinguishable".
- **Roles beside the palette:** a `muted` "Others" color per theme, an area alpha per theme
  (0.85 light, 1.0 dark), `shade_family()` blending toward the surface rather than white.
- **Fonts:** register the TTFs with `addfont()`, use the Agg backend, and test that `findfont()`
  resolves inside the font directory.
- **Not carried over:** `svg.fonttype: none`. sam-queries inlines its SVG into a page that
  loads Poppins; Quarto puts an SVG in an `<img>`, which can't see the page's fonts.

## 4. The generator: `_extensions/engine/livery_charts.py`

A pure-Python engine module (named like `livery_build.py` and `livery_check.py`, and loaded by
path, since the tests and the framework load `livery_build.py` by path too) called from
`resolve()` in `livery_build.py`: a build needs no matplotlib or numpy. It holds OKLab and OKLCH
both ways, sRGB gamut clipping by reducing chroma, WCAG contrast, the Machado matrices and ΔE,
written from the published formulas and the method's thresholds; on 3,000 random pairs its
numbers match the dataviz validator's to 1e-13. Deterministic.

1. **Gather hues in brand order.** Anchors, the brand colors that must appear, in slot order
   (default `primary`, then `accent`, `secondary`, `highlight`, duplicate hues dropped);
   extended, the livery's other palette colors with real chroma, used before anything is
   invented; generated, only if still short of 8, by farthest-point search in OKLab, the
   distance being the minimum over normal, protan and deutan vision. Generated candidates sit at
   the anchors' median chroma, skip `avoid`ed hues, and stay 22° of hue from every chosen hue, so
   no two share a family.
2. **Build a ramp per hue,** 7 steps, 100 to 700, at the hue's own angle, gamut-clipped, with
   the brand color at its nearest step.
3. **Select per mode,** against that mode's surface (light: `background`; dark: `dark`, for a
   `.brand-dark` HTML slide, or `background` on a dark livery):
   - `categorical`: 8 slots, each the brand color itself when it is a legal mark, else moved to
     the nearest lightness inside the band that clears 3:1 (chroma raised to the floor, hue held),
     then snap-to-passing (move a slot's lightness while a neighbor pair falls short). Slot 1 is
     the first anchor, the other brand hues follow and the generated ones come last, each group in
     the order with the best worst adjacent separation under color blindness, gated on the
     normal-vision floor;
   - `families`: up to 8 hues × 3 steps, base and two tints toward the surface (a third and two
     thirds of the way on light, as koru's -33 and -66; 0.3 and 0.55 on dark, or the pale end sinks
     into the surface), a brand ramp's step standing in for a tint it is within ΔE 3 of;
   - `sequential`: one ramp per hue, light to dark (reversed on dark, so the low end meets the
     surface), checked for monotone lightness and visible steps (a color map's low end may meet the
     surface, so the ordinal pale-end check is left out); the default map is the primary's;
   - `diverging`: two poles (default the primary and the categorical hue farthest from it) and
     a neutral midpoint from `muted`, equal steps per arm, the dark midpoint at least 1.6:1 on
     its surface;
   - `status`: good, warning, serious, critical, fixed hues (150°, 85°, 55°, 27°) on the step
     nearest mid lightness that is at least ΔE 12 from every categorical slot; most brands have
     no red or green, so these are declared deviations;
   - `muted` and `area-alpha`.
4. **Report.** `livery.json` holds the selections and, per block, which parts are published;
   the checks are computed when reported (`livery_charts.evaluate()`), not stored. `livery_check.py`
   prints every check per mode, and with `--swatch DIR` writes a contact sheet,
   `DIR/charts-<livery>.png`, light and dark, generated slots marked (the framework's
   `livery_check.py --qa` puts it in `decks/quickstart/_qa/`). A failure of a generated palette
   fails the livery (the generator is broken); a published palette's failures are warnings (the
   brand is the authority, and its failures are surfaced, not fixed).

**When a livery has `ramps`,** steps 1 and 2 are skipped and step 3 selects from the brand's
own steps: the method's "snap to the customer's ramps", so every color is the brand's.

**The prototype** (in memory, 2026-10-18): from NASA's two colors and CU's three, steps 1 and 3
alone produced 8-color sets that pass every light-mode check. Dark needs the snap-to-passing
loop. NASA's generated extras bunched into pinks, which is why the extended tier and the
one-family limit exist.

## 5. The livery keys: `charts:` in `livery.yml`

Every key is optional; with no `charts:`, everything is derived.

```yaml
charts:
  anchors: [primary, accent]          # brand hues that must appear, in slot order (roles, palette names or hex)
  extended: [cyan, yellow, sky]       # secondary brand colors to use before generating any
  avoid: [{hue: 330, width: 40}]      # hue ranges never generated (OKLCH degrees)
  chroma: 0.12                        # chroma of generated hues (default: the anchors' median)
  ramps: {blue: ["#...", ...], ...}   # a brand's published ramps, light to dark
  maps: {campus: ["#...", ...]}       # more color maps, light to dark, that leave the slots alone
  sets: {light: {3: [...], ...}}      # its curated small-series sets
  categorical: ["#0057c2", ...]       # pin the whole cycle; the checks still run
  default-map: primary                # the default colormap: a hue (its nearest ramp) or a map's name
  diverging: [primary, accent]        # the two poles
  status: {good: ..., warning: ..., serious: ..., critical: ...}
  dark: {categorical: [...], diverging: [...]}   # pinned dark selections win over derived ones
```

`charts` is in the schema (`livery.schema.json`, #58). A flavor inherits its parent's charts
through `merge()`. A brand guide's published data palette goes in `ramps`/`sets` or `extended`,
its source in `reference/notes.md`.

Per livery:

| Livery | Charts from |
|---|---|
| ncar | pins from sam-queries (`FAIR_SHARE_LIGHT`/`_DARK` as `categorical`, the burn steps `--data-burn-0..4` as `diverging`, light and dark), ramps from koru re-based on 2026 |
| ucar | ncar's, with UCAR Aqua leading: sam-queries' set with slots 1 and 3 swapped, which passes the same checks |
| ucp, ncarucar | their parents' (`extends`: ucar, ncar) |
| nasa, nasa-dark | HDS's 12 categorical colors, its sets (option 1 for 2 to 5 series) and its 11 ramps, verbatim (CC0); HDS blue 70 and red 70 as diverging poles; never the brand red and blue |
| cu, nsi | generated from the gold and the blues, with the campus: the roof tile `#9C3F29` (sampled from the campus photo) as the third brand hue and sage the fourth, a campus map (Light Gold, sandstone, tile) as the default, Sky Blue to the tile as diverging (2026-10-18) |

ncar's notes record why sam-queries' set adds a pink, a purple and a darker gold (the brand
colors alone failed the checks), and the generator's own ncar result for comparison. The checks
must pass the ncar pins unchanged; if they fail, the checks are wrong.

## 6. Every format

`livery_build.py` writes the selections into:
- **`build/livery.json` `charts`**, the source the helper reads;
- **`build/livery.mplstyle`**: chrome in the livery's mode (text and ticks `foreground`, spines
  and grid `muted` and `derived.rule`, `savefig.transparent: True` so a plot sits on any
  field), the categorical cycle as `axes.prop_cycle`, `font.family` the livery's base family
  (DejaVu Sans fallback), `mathtext.fontset: custom`, `pdf.fonttype: 42`, `svg.fonttype: path`,
  sizes in points from `livery.type_pt()` (labels and titles `body`, ticks and legends
  `levels[2]`, annotations `caption`), a light grid, no top or right spine. A figure drawn at
  the content width in canvas inches has slide-sized text in every format;
- **`build/livery.css`**: `--engine-data-1..8`, `--engine-data-muted`, `--engine-status-*`,
  light and dark, `.brand-dark` taking the dark set;
- **`build/livery.sty`**: `\definecolor{EngineData1..8}` and, when pgfplots is loaded, a
  `livery` cycle list, so LaTeX and Overleaf plots match;
- **`template.pptx`** (`livery_template.py`): the light categorical palette as
  `<a:custClrLst>` in `theme1.xml`, each color named ("Data 1 · Blue"), shown by PowerPoint as
  a Custom Colors row in every color picker (section 7).

Later and cheap, not this work: a Plotly template or a Vega theme from the same data.

## 7. PowerPoint: the colors are already baked in

Each `template.pptx` carries its colors and fonts in `ppt/theme/theme1.xml`: the 12-slot scheme
(`<a:clrScheme name="cu">`) and the font scheme, written by `livery_template.py`. Pandoc copies
the reference document's theme into every deck: a test deck built with pandoc 3.1.3 from
`liveries/cu/template.pptx` carried the `cu` scheme unchanged.

- **No external file is needed.** A framework deck opens with the brand's theme colors in
  PowerPoint's color picker on any machine. On a Mac, an extra file matters in one case only:
  making the brand colors appear in a deck started elsewhere. PowerPoint for Mac saves custom
  theme colors under `~/Library/Group Containers/UBF8T346G9.Office/User Content/Themes/Theme
  Colors/`; a `.potx` saved to My Templates does the same job.
- **CU's slots repeat colors.** `accent3` is `dk1`'s black, `accent4` and `accent5` both CU Gold,
  through the slot contract (`SLOT_ROLES` in `livery_build.py`). The picker shows duplicate
  columns, and PowerPoint's own charts, which take accent1-6 in order, come out gray, blue,
  black, gold, gold, dark gold. The contract ties accents to roles and the templates draw from
  `accent1` and `accent4`, so the accents can't simply become the chart palette.
- **The fix is the Custom Colors row** (section 6, Ben: yes, every livery). It puts the plot
  colors one click away for shapes and native charts without touching the slot contract.
  Checked 2026-10-18 in PowerPoint for Mac: the Shape Fill picker shows "Custom Colors" between
  Theme Colors and Standard Colors, its eight swatches named "Data 1 · Gold" ... "Data 8 · Teal"
  (cu; read through the accessibility tree, the popover opening off screen). Windows unchecked.
- **Native charts keep the accents** (Ben, 2026-10-18: the Custom Colors row for now). A chart
  inserted in PowerPoint takes accent1-6; a per-livery chart template (`.crtx`, installed once per
  machine) is the next step if people ask for it, re-mapping the accents (unbinding the templates
  and post-processors from `accent1`/`accent4`) the larger one.

## 8. Decks, the helper and the image

- **`_extensions/engine/mpl/livery_mpl.py`**, in its own directory so it can sit on PYTHONPATH
  without hiding `common/utils/livery.py`. It reads `livery.json` itself (an argument,
  `$LIVERY_DIR`, `_livery`, then the bundle's directory). On import: the Agg backend, the
  livery's fonts registered with `addfont()`, the style applied, the colormaps `livery`,
  `livery_r`, `livery_div`, one `livery_seq_<hue>` per ramp and `_dark` twins (OKLab
  interpolation of the steps), `image.cmap` set. It exposes `colors`, `cycle`, `families`,
  `status`, `muted`, `figsize("full" | "half")`, `shade_family()`, and `with livery_mpl.dark():`
  (an `rc_context` with the dark chrome and selections, for a `.brand-dark` slide; a kernel
  renders one figure at a time, so sam-queries' rcParams thread-safety concern does not arise).
  A deck's first cell:

  ```python
  #| include: false
  import livery_mpl
  ```
- **`Make.common`** exports `MATPLOTLIBRC=$(LIVERY_DIR)/build/livery.mplstyle` (a plot is styled
  with no code at all), prepends the framework's `_extensions/engine/mpl` to `PYTHONPATH` (the
  same for a consumer's `../framework/Make.common` and the image's), and passes
  `charts.figsize.full` as the deck's `fig-width`/`fig-height` (to verify: that `-M` reaches
  Quarto's Python setup cell, which sets `figure.figsize` at the document level only).
- **`common/_quarto.yml`**: per-format `fig-format`/`fig-dpi` (pptx png at 200 dpi, revealjs
  svg, beamer pdf; since 2026-10-20 pptx svg, each with a PNG fallback at 200 dpi by
  `pptx_steps/svg_fallback.py`, after a spike Ben checked in PowerPoint and Google Slides). The engine's `diagram-dark.lua` recolors only mermaid and dot PNGs and is left
  alone.
- **`decks/plots/plots.qmd`**, `jupyter: python3` (a deck runs one kernel, so it can't share the
  bash sample deck), deterministic: lines in the cycle, a seaborn bar chart from pandas, a
  stacked area in `families`, a heatmap with the sequential map, a diverging field with scipy
  smoothing, two plots in columns, math in a label, a `.brand-dark` slide, a `.caution` slide.
- **The image**: numpy, scipy, pandas, matplotlib and seaborn in `conda-env.yaml` `pip:` (wheels
  for amd64 and aarch64; about 250-300 MB, to be measured by the merge job's size summary);
  matplotlib's font cache built into `/opt/matplotlib`, world-readable, and seeded into
  `$HOME/.cache/matplotlib` by the entrypoint unless `/opt/fonts` has files (a cache never
  rescans).
- **The release bundle**: `_extensions/engine/mpl_zip.py` writes `<livery>-charts.zip`
  (`livery.mplstyle`, `livery_mpl.py`, `livery.json`, the fonts and their licenses, the parent's
  for a flavor, the swatch sheet, a README); `make charts-zip LIVERY=<name>` beside `make
  overleaf`; `release.yml` builds one per livery.
- **To verify early**: that matplotlib embeds cu's CFF `.otf` TeX Gyre Heros in a PDF; if not,
  cu takes `pdf.fonttype: 3` or a PNG fallback for beamer, recorded in its notes.

## 9. Steps, one PR each, parity after every one

1. **The generator** (cloud): `livery_charts.py`, `charts:` in `resolve()` and `KNOWN` with `ramps` and
   `sets`; ncar's pins and koru ramps, nasa's HDS ramps and sets, each livery's notes; the
   `livery_check` report and swatch sheet; every `build/` regenerated; `tests/test_charts.py`
   (every livery's selections pass in both modes, the ordering is deterministic,
   `lift_for_contrast` leaves a passing color alone, ncar's pins come out unchanged; during
   development the module's numbers match the dataviz validator's). Also the NASA
   screen-color issue. Nothing renders differently.
2. **Every format's colors** (laptop): the mplstyle, the css and sty tokens, the Custom Colors
   row in every template (`test_type.py` and the template checks still pass; a built deck
   carries the row), the packages, a test that the style parses; then the two early checks
   (`-M fig-width:`, cu's OTF in a PDF).
3. **Decks and image** (laptop): the helper, the `Make.common` wiring, the figure formats,
   `decks/plots` in CI and `tests/parity.sh`, the font cache and entrypoint seeding, a Python
   plot in `.github/scripts/smoke-test.sh`.
4. **The bundle** (laptop): `mpl_zip.py`, `make charts-zip`, `release.yml`, the docs (README
   "Plots and chart colors", "Adding a livery" gets `charts:`, a container line; CLAUDE.md; this
   file's §10 entry in `engine-and-liveries.md`; a note on #58).
5. **Final color polish** (laptop, with the brand guide and PowerPoint for Mac):
   - NCAR: does the 2026 guide list vermilion `#FF1F1F` and the grays `#97999b`, `#bbbcbc`? If
     so, add them and a `vermilion` ramp, with the guide's pages. **Answered 2026-10-18: no**
     (pp. 17-22 list exactly the ten colors; `liveries/ncar/reference/notes.md`).
   - NASA: does the 2024 insignia color guide give `#0032A0` and `#E4002B`? Then the
     screen-color issue: HDS against the Pantone conversions, the invented neutrals, the
     Office cyan. **Answered 2026-10-18: yes**, one set for every medium (the Brand Center's
     insignia colors; `liveries/nasa/reference/notes.md`); the screen-color decision stays open.
   - CU: `styleguide.colorado.edu/colors`, the full named web colors; any for `extended`?
     **Read 2026-10-18**: a Material Design UI palette, no further brand hue; Brick `#AE5A39`
     and Medium Blue `#4FC3F7` are the candidates (`liveries/cu/reference/notes.md`). **Done**:
     the campus instead, the roof tile and sandstone sampled from the campus photo (cu's notes).
   - NCAR's color map: more vivid but compliant. **Done**: `ramps.ncar`, the brand's blues end to
     end, and `ramps.ucar` along UCAR Aqua.
   - PowerPoint for Mac: the Custom Colors row in a built deck's picker, a native chart per
     livery. **Done**: the row is there (section 7); native charts stay on the accents.

   Each answer is a small livery change: regenerate `build/` and the templates, parity on the
   liveries it touches, swatch sheets and notes updated.

## 10. Verification

- `make test`; `livery_build.py --check` and `livery_check.py` on every livery, no hard failure.
- Each livery's swatch sheet, looked at: the extras feel like the brand, and ncar's matches
  sam-queries' dashboards.
- `tests/parity.sh check`: quickstart, sample and fixtures unchanged under every livery.
- `make -C decks/plots all qa` under ncar, cu, nsi, nasa, nasa-dark, every format looked at: plot
  text matches the slide's body text in size and face, series distinct, no white boxes on dark,
  the stacked area reads by family, the column plots fit.
- Fonts: `pdffonts` shows the livery family; the pptx SVGs (and their PNG fallbacks) viewed; the HTML svg has no `<text>`.
- The image: `findfont()` resolves each livery's family; a `--user` run does no font-cache
  rebuild; the smoke test passes on both architectures; the size summary in the PR.
- The bundle: `nasa-charts.zip` unzipped in a clean directory, a script with only `import
  livery_mpl` and a plot, fonts and cycle checked.

## Sources

Brand pages, read through search results (the sites were blocked from the session):
[CU Boulder visual identity](https://www.colorado.edu/imc/cu-boulder-brand/visual-identity),
[CU color specifications](https://www.cu.edu/brand-and-identity-guidelines/color-specifications),
[Accessible CU Boulder color combinations](https://www.colorado.edu/digital-accessibility/color-combinations),
[CU Boulder Accessible Color Contrast Recommendations, rev. 6-28-17](https://www.colorado.edu/digital-accessibility/sites/default/files/attached-files/cu_boulder_accessible_color_contrast_recommendations_rev_6-28-17.pdf) (read 2026-10-18),
[CU Boulder web style guide](https://styleguide.colorado.edu) and its source [CuBoulder/styleguide](https://github.com/CuBoulder/styleguide) (a Material Design web palette, 2019),
[NASA Brand Center guidelines](https://www.nasa.gov/nasa-brand-center/brand-guidelines),
[NASA insignia guidelines for grantees](https://www.nasa.gov/wp-content/uploads/2018/03/nasa_insignia_guidelines_for_nasa_grantees.pdf),
[NASA style guide, 2006](https://w3.cs.jmu.edu/bernstdh/web/common/policies/NASA_StyleGuide_Nov06.pdf),
[NASA insignia (Wikipedia)](https://en.wikipedia.org/wiki/NASA_insignia),
[NCAR/UCP/UCAR logo and brand guidelines, 2014](https://news.ucar.edu/sites/default/files/news/2014/NCAR_UCP_UCAR_Logo_Brand_Guidelines_Fall_2014.pdf).

Code, read at these commits:
[nasa/hds-core](https://github.com/nasa/hds-core) f036e73 (2026-10-07; `tokens.json`,
`src/scss/_hds-dataviz-palettes.scss`, CC0),
[NCAR/koru-jekyll](https://github.com/NCAR/koru-jekyll) 55ce7c3 (2026-09-03;
`assets/koru-base/scss/_variables.scss`),
[CuBoulder/tiamat-theme](https://github.com/CuBoulder/tiamat-theme) 8df166a (2026-10-15),
[benkirk/sam-queries](https://github.com/benkirk/sam-queries) 6e0f00d (2026-10-16;
`src/webapp/dashboards/charts/theme.py`, `src/webapp/static/css/variables.css`),
[NCAR/music-box-interactive issue #588](https://github.com/NCAR/music-box-interactive/issues/588).
