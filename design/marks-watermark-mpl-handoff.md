# Sprint handoff: marks in any corner, a watermark, a pip-installable livery_mpl

**State (2026-10-24):** executed as PR #149 (`decks/marks-watermark-mpl`, nine commits on #148's squash `bb671e1`). Ben's picks at the start: a corner entry's `light`/`dark` as the role defaults; nasa-ccp's art by rerunning `reference/ccp_art.py` on the template (`CCP_IAFM.pptx`); `livery_mpl` git-only with no console script; the watermark text-only on every slide at 8%, 30 degrees, 120 pt. Mid-sprint: on a composed slide the watermark wears the composition's text color, on a dark slide on-dark (the navy word vanished on ncar's blue fields). Departures: HTML's marks are one `.engine-marks` box per content slide holding the corner elements (Quarto's `.columns:nth-child(3)` margin counts a slide's children; one element per corner moved nsi's body 21 px); a flavor's corner entry naming another mark replaces its parent's instead of merging (nasa-ccp's insignia over nasa's logo corner); the `*-height` keys refused on any entry but the logo's; the default watermark size scales with the canvas (120 pt is the default 540 pt canvas's, 0.22 of the height everywhere); the beamer macros are `\engine@corner@<corner>@<key>`; pdftotext splits the turned word, so `deck_qa` drops its pieces by height and the LaTeX test reads `-raw` in a document of its own; item 2 ran in a parallel worktree and was picked after commit 3. Planned by the reviewing session after #146 and release 26.10.11.

**For a fresh session.** One PR against `main` (branch `decks/marks-watermark-mpl` from
`origin/main` AFTER sprint A merges: it builds on A's `furniture`, per-role marks and
`engine-dark`), a commit per step in the order below, squash-merged once, no version bump. Item 2
(commits 4-5) touches no file items 1 and 3 touch except `CHANGELOG.md`, `CLAUDE.md`,
`docs/authoring.md` and `REFERENCE.md`, so it can run in a parallel worktree and rebase last. Read
`CLAUDE.md` whole ("Marks and numbers", "Content title", "Compositions", "Plots", "Chart colors",
"The engine", "revealjs (HTML) theme"), `design/gallery-handoff.md` (shape and house rules),
`design/cells-dark-handoff.md` (sprint A: the cross-sprint rules it set), `liveries/nasa-ccp/
reference/notes.md` "Marks", `design/engine-and-liveries.md` :843-852 (where `signoff` was
introduced as "a second lockup"), then `source etc/config_env.sh`, branch, parity baselines
(Verification 1), this file as commit 0 at `design/marks-watermark-mpl-handoff.md`. Report at the
end of each commit: what moved, what the tests assert, what parity named.

House rules: as sprint A's, plus: a livery key is renamed only with Ben's agreement (the names
below are his picks or proposals marked as open questions), `liveries/*/build/` and every
`template.pptx` generated and committed. Line numbers are on `2a1cf0a`; sprint A moves some: re-grep.

## Item 1: one mark per corner, any corner, named

### Context anchors (on `2a1cf0a`; sprint A moves the mark emitters)
- `livery_build.py`: `MARK_ROLES` :80; `resolve()` :277-292 (`frametitle.body` from the ONE
  logo :278-280; corner checks :281-284; the `signoff` block :285-292, `aspect` required);
  `band()` :429-440 (`title.signoff-height` :437, `logo-height` :438); `marks()` :442-474
  (defaults :452-453 from `logo.medium.*` and `signoff.light|dark`; refuses other keys :458-460;
  the `-print` twin for `logo` only :467-468); `compositions()` :497-687 (`logo = g.get("logo")`
  :503; `mark()` :513-516; `signoff()` :518-523; `strip()` :525-536; the `*-height` keys :547,
  :598, :619; `img`/`img-print` :670-686); `emit_sty` :833-844, the geometry loop :935-941;
  `emit_css` :1116-1125, :1154-1163, :1176-1178, :1183-1190, :1221-1230; compositions' images
  :1485-1487 (untouched).
- `livery.py` `mark()` :136-141 (keyed by name, unchanged), `files()` :144-153 (`("logo",
  "logo-print", "signoff")` hard-coded :153; `livery_check.py:123`, `overleaf_zip.py:46`, `deps`
  go through it).
- Beamer `beamerouterthemeEngine.sty`: dimens :41-46, `\engine@ifcorner` :50-51,
  `\engine@framelogo` :55 (`\enginelogo` `engine_livery.sty` :342-343), `\engine@logowidth`
  :70-74 (0 under `logo=false`, `beamerthemeEngine.sty:44`), `\engine@signoff` :76-85,
  `\engine@ftbeside` :97-98, the title width :99-108, the hskip :136, background :353-369.
- HTML scss: the content mark `::after` :122-135 (both pseudo-elements spent: `::before` is the
  hairline :208), `.engine-signoff` :138-151, `.full .engine-signoff` :153, the title fallback
  :185, the composed slides' `::after`/`.engine-signoff` :763-786 (untouched), `.full` :1089.
  `engine-revealjs.lua` `add_signoff()` :401-410 (`SIGNOFF_SKIP`), the chain :881, the
  dependency's files :626-643. `title-slide.html:56` (untouched).
- pptx `livery_template.py`: `self.signoff` :87, `self.logo_corner` :95, `master()` :167-252
  (room :173-180, `rId2` "Logo (light)" :227-228, `rId3` "Sign-off (light)" :230-233, order
  :239), `pic()` :139-143, `build()` :422-452 (media names :427, `path_of` :428-433, master rels
  rId1-4 then rId10+; rId5-9 free). `slide_layout.py` `hide_furniture()` :263-268 and
  `draw_feature()` :637 hide every master pic: nothing to do.
- Readers of the old keys: `tests/test_boxes.py:190-192`, `tests/test_compositions.py` :29-44,
  :160-161, `tests/test_schema.py:74,77`, `livery_new.py` :96, `liveries/README.md` :57-64,
  `docs/formats.md` :95. `deck_qa.py` and `comp_measure.py` read none. `parity.sh` :46-53 unzips
  pptx XML: a master shape name or rId change is a parity diff.
- The liveries (`grep -n "^signoff\|^  logo:" liveries/*/livery.yml`): ncar :45-52, ucar :14-16,
  ucp :9-11, ncarucar :8-9, cu :19-25 and :30-37 (`corner: none`), nsi :10-15 and :18-23
  (top-left, inset 0.015), nasa :20-26 and :31-38, nasa-dark (`marks` :20-22), nasa-jsc-eg
  :23-29 (bottom 0.009) and :37-44, nasa-ccp :21 (`signoff: null`), :23-25, :30-35. `merge()`
  :162-168 is recursive: a flavor overrides one key of one corner; `null` drops a parent's corner.
- nasa-ccp's art: `reference/ccp_art.py` :48-66 (`insignia_box`, `paint_out`), :71-79, :86-97
  (`with_bar()` pastes the vector insignia into `content.jpg` and `section.jpg`). Measured on the
  committed `content.jpg`: the insignia's box `[0.9143, 0.0745, 0.0711, 0.106]`, right inset
  0.0146; `meatball` aspect 1.2146 (`liveries/nasa/livery.yml:35`).

### The model
```yaml
geometry:
  marks:                       # one mark per corner, by corner; null drops a parent's
    top-left:    {mark: logo, light: ccp-emblem, dark: ccp-emblem, height: 0.107, top: 0.0728, aspect: 0.9717, inset: 0.008}
    top-right:   {mark: insignia, light: meatball, dark: meatball, height: 0.106, top: 0.0745, aspect: 1.2146, inset: 0.0146}
    bottom-left: null
marks:                         # per field role, any name a corner wears (plus logo and signoff, the compositions' slots)
  background: {logo: ccp-emblem}
```
- `CORNERS = ("top-left", "top-right", "bottom-left", "bottom-right")`; `corner_marks(name, data,
  out)` after the roles: per corner `{mark, height, top|bottom, aspect, inset?, light?, dark?}`;
  `mark` is `[a-z]+` and required; `aspect` required; `top` for a top corner, `bottom` for a
  bottom one (the other refused); defaults height 0.0644, top 0.0533, bottom 0.03, inset absent
  (= the margin). Two corners with one `mark` name refused. `title-height`/`section-height`/
  `closing-height` stay as keys of the entry whose mark is `logo` (compositions untouched this
  sprint: `mark()` :513, `strip()` :533, `band()` :438 read them as before). `livery.json`
  `geometry.marks` is the resolved map; sprint A's `furniture.marks.<corner>` is derived from it.
- `frametitle.body` = `max(rule-y, max(top + height over the top corners)) + BODY_GAP`.
- `marks()`: legal names per role = `{logo, signoff} ∪ {e.mark}`; defaults: `logo` ←
  `logo.medium.light|dark`, a corner entry's `light`/`dark` ← background/primary, other roles ←
  primary's; every name gets its `-print` twin when `logo.images` has one.
- `band()` reads `signoff-height` from the entry whose mark is `signoff`; `compositions()`:
  `logo = entry_of("logo") or {}`, `mark()` null when none wears `logo`; `signoff()` places the
  default box in the signoff entry's corner (any of four); `strip()` by `endswith("left")`.
- `emit_sty`: `\def\engine@corners{top-left,bottom-left}`, per corner `\engine@mark@<corner>@
  {name,height,top|bottom,aspect[,inset]}`; the per-role image macros are sprint A's
  `\engine@mark@<role>@<name>` (every role, every name; the print twin as :837); the geometry loop
  skips `marks`. `emit_css`: `--engine-logo-*`/`--engine-signoff-*` retire; per corner one rule
  `.reveal .slides section.slide .engine-mark-<corner> { top|bottom; left|right; width; height;
  background-image: url(--engine-mark-background-<name>); background-position }`,
  `section.engine-field .engine-mark-<corner>` the primary's, `section.engine-dark
  .engine-mark-<corner>` the dark role's (sprint A's `.engine-dark::after` rule moved here);
  `--engine-title-left|right` from one `title_room(livery) -> (left, right)` (per top corner
  `max(0, inset + height*aspect*hw + TITLE_GAP - margin)` on its side; `symmetric` → both the
  larger), which `livery_template.master()` also calls (today computed twice).
- Schema: `geometry.logo` and top-level `signoff` removed; `geometry.marks` with the four corner
  keys (`null | entry`, `additionalProperties: false`, `mark` and `aspect` required);
  `marks.<role>` → `additionalProperties: {"$ref": "#/$defs/image"}`; `livery schema --doc`.
- Drawers, one loop each. Beamer: `\@for\engine@c:=\engine@corners\do{…}`; a `\newdimen` per
  corner measured at `\begin{document}` (`\settowidth`, :70-74's pattern; 0 under `logo=false`
  for the corner named `logo`); `\engine@ftroomleft|right` computed there (the `title_room`
  formula on the measured widths); the title :97-108, :136 restated as `\hskip\engine@ftroomleft`
  and `\paperwidth - 2\engine@margin - left - right` (no `\engine@ftbeside`); the background
  template one node per corner anchored `north west|north east|south west|south east`,
  `\includegraphics[height]{\engine@mark@background@<name>}` (the dark role's on a dark frame,
  sprint A's branch); `\engine@signoff` :76-85 retires. HTML: `add_signoff()` → `add_marks()`:
  after a level-1 or `.closing` heading the composition's `.engine-signoff` (unchanged); after any
  other content heading one `<div class="engine-mark engine-mark-<corner>"></div>` per corner;
  scss :122-135 scoped to `section.engine-title::after` only (the composed slides' `::after`
  keeps its base properties: move them into :763-786), `.engine-mark { position: absolute;
  background: no-repeat contain; pointer-events: none }`, `.full .engine-mark` hidden with
  `.engine-signoff`, :185's fallback `var(--engine-margin)`; the dependency's files :632-633:
  every key of `livery.marks[role]` not ending in `-print`. pptx: `master()` one `self.pic(rid,
  LABEL, x, y, w, h)` per corner in `CORNERS` order; rIds: `rId2` always the background `logo`
  image (today written even under corner none), `rId3`, `rId5`, `rId6` the other names in corner
  order (`rId4` stays art); media names `f"{name}-background"`, `path_of` maps the compositions'
  `mark-` to `logo`; pic names `{"logo": "Logo", "signoff": "Sign-off"}.get(name, f"Mark {name}")
  + " (light)"`. The nine templates other than nasa-ccp rebuild **byte-identically** (logo before
  sign-off everywhere, same rIds and names): `livery check`'s rebuild check and `parity.sh` prove
  it; the two labels are kept on purpose (PowerPoint's shape names), not a shim.

### Commits
**0. This handoff.**

**1. Corner marks: the build, the schema, the ten liveries, the three drawers** (one commit: the
sty/css names change, so the drawers and the build move together). `livery_build.py`, `livery.py`
`files()` (every path key of `marks[role]`), `livery_new.py` :96 (`marks: {top-right: {mark: logo,
height: 0.0644, top: 0.0533, aspect: …}}`), the schema, `REFERENCE.md`, the ten `livery.yml` (cu's
`logo` block dropped whole: defaults and `corner: none`; nsi adds `top-left`; nasa-ccp
`bottom-left: null`), `beamerouterthemeEngine.sty`, `engine_livery.sty:343`, the scss, the
revealjs filter, `livery_template.py`; `livery build liveries/*/` and `livery template` on all
ten, committed. Tests: `tests/test_marks.py` (new): two top corners and the room on each side from
`title_room()` against the css and the template's title placeholder (`test_frametitle.py`'s
pattern), symmetric mirroring the wider side, `frametitle.body` under the taller, a bottom-right
entry's default box, `null` dropping a parent's corner (`tmp_livery` on a flavor), the refusals
(two corners one name, `top` on a bottom corner, a missing `aspect`, `marks.background.nope` when
no corner wears `nope`), the sty's `\engine@corners` and per-corner macros, the css per-corner
rules for background, primary and dark. `test_boxes.py`, `test_compositions.py`, `test_schema.py`
read `geometry.marks`; `EXPECTED_DELTAS` unchanged. Proof: `make test`; `parity.sh check` on ncar,
cu, nsi: pptx XML and PDF identical, HTML differs only by the mark's `<div>` per content slide and
`livery.css`; the nine templates byte-identical; screenshots under ncar (top-right), nsi
(top-left, symmetric), cu (sign-off only) unchanged to the eye.

**2. nasa-ccp: the insignia as the top-right mark, in vector.** `livery.yml`: the `top-right`
entry (re-measured on `content.jpg` with `ccp_art.insignia_box`), `section.signoff: {role:
background, image: meatball, box: [0.9143, 0.0745, 0.0724, 0.106]}` (new; title/closing keep the
lockup); `reference/ccp_art.py`: `with_bar()` no longer calls `place_insignia`, the bar's box
printed as the cover's is; the committed `art/content.jpg` and `art/section.jpg` painted out with
`paint_out(insignia_box(bar rows))` + the blur, quality 88 (the one-liner in the commit message);
`reference/notes.md` :58-64 closes the follow-up; `make livery LIVERY=nasa-ccp` (this template
changes: a third pic). Tests: `test_marks.py` adds nasa-ccp's two top corners resolving. Proof:
`livery check --qa liveries/nasa-ccp` (look at a content slide and a divider in all three: the
emblem left, the insignia right, no double edge); `make -C decks/fixtures measure LIVERY=nasa-ccp
MEASURE_FAIL= DECK_META=…` (the section's new sign-off row; title/closing flat); `make -C
decks/quickstart gallery` (commit `liveries.png` only if nasa-ccp's row visibly changed). CHANGELOG
Decks.

**3. Docs and records.** `liveries/README.md` :57-64 ("Marks" and "Geometry" for corners),
`docs/formats.md`, `CLAUDE.md` "Marks and numbers" and "Content title" (`title_room`),
`design/engine-and-liveries.md` a dated line, the ledger, CHANGELOG Liveries (a reshape line as
the marking map got: `geometry.logo` and `signoff` → `geometry.marks.<corner>`, how each livery's
keys moved, no alias).

### Fallback, argued against
Generalizing `signoff.corner` to the top corners is a third of the work, but leaves "signoff"
meaning "the other mark", caps the engine at two marks, and reopens the item for the next brand
with a top mark plus a foot lockup plus a program patch. The corner model does not reopen.

## Item 2: a pip-installable `livery_mpl` (#81)

### Context anchors
`_extensions/engine/mpl/livery_mpl.py` (303 lines): `HERE` :56, `__all__` :58-59,
`_engine_version()` :62-73 (two sources), `_find()` :79-85, `use()` :155-191 (fonts from `base /
ff["path"]` :160; the style :167), `use()` at import :303 (a bare import with no livery raises).
`mpl_zip.py`: layout :5-11, `README` :23-54 (:44), `bundle()` :57-87. `Make.common` :90,
:119-120, :131-133 (`mpl/*.py` only), :163-164. `release.yml` :53-66, :77. `ci.yaml` :496-523 (the
bundle tried from `/tmp/charts`), the `latex` job :348-368 (`make test` :364-365: the venv step's
place). Tests: `test_cli.py` :31 `VERSION`, :95-104, :133-149, `test_charts.py` :184-209;
`test_docs.py` :146-154 (`PIN` over `docs/other-repos.md`). No `pyproject.toml` anywhere;
`conda-env.yaml` has no `-e`; `Dockerfile` :44-48 creates the env before `COPY` :137 (no editable
install wanted: decks reach the helper by `PYTHONPATH`). The env's Python is 3.15 (`tomllib`).
Hatchling, verified in its source: `VersionFile` joins `root` and the path with
`os.path.normpath` and no containment check, so `path = "../_extension.yml"` is read at build
time; the default pattern wants `__version__ =`, so `pattern` must be given.

### Decisions
- The package is the subdirectory, one module: `name = "livery-mpl"`, `dynamic = ["version"]`,
  `requires-python = ">=3.10"`, `dependencies = ["matplotlib>=3.6"]`, `[tool.hatch.version]
  source = "regex", path = "../_extension.yml", pattern = '^version:\s*(?P<version>\S+)'`,
  `[tool.hatch.build.targets.wheel] only-include = ["livery_mpl.py"]`. **No sdist** (it cannot
  carry `../_extension.yml`); pip from git and `pip wheel` build in-tree. One home for the version.
- No `livery` console script, no root `pyproject.toml` (#58's reason: the command needs the
  checkout). Git-only install this PR: `pip install "livery-mpl @ git+https://github.com/benkirk/
  quarto-livery-decks@v<x.y.z>#subdirectory=_extensions/engine/mpl"`; a wheel on the release is
  one `pip wheel` line in `release.yml` (open question 4).
- A bare import no longer raises: the module imports unconfigured (`livery == {}`), `use(path)`
  configures it; docstring: "installed by pip: call `use()` first". Decks unaffected.
- `use("<name>-charts.zip")`: `_find()` gains a `.zip` branch: unpack into `$XDG_CACHE_HOME`-or-
  `~/.cache` `/livery_mpl/<stem>-<engine>/` unless its `livery.json` is newer than the zip, then
  proceed as an unpacked bundle. A URL is out of scope (download, then `use()`).

### Commits (independent of items 1 and 3)
**4. `livery_mpl`: a third version source, an import without a livery, `use()` on a bundle zip.**
`_engine_version()` gains `importlib.metadata.version("livery-mpl")` after the bundle; :303 becomes
`if _found(): use()`; `_unpack(zip)` and the `.zip` branch; the docstring. Tests, `test_cli.py`:
`test_livery_mpl_version` gains an "installed" case (`livery_mpl.py` copied into `tmp/site` beside
a `livery_mpl-<VERSION>.dist-info/METADATA`; no pip, no network), a bare-import case (exit 0,
`livery == {}`), `test_use_zip` (`livery zip --charts ncar`, `use(zip)` under `XDG_CACHE_HOME=tmp`:
the cache dir, the base family in `fontManager.ttflist`, `colors` ncar's). CHANGELOG Plots.

**5. `pyproject.toml`, the proof in CI, the docs.** The file as above;
`test_cli.py::test_pyproject_version_source` (`tomllib`: `dynamic == ["version"]`, the path
resolves to `ENGINE/_extension.yml`, the pattern matches `VERSION`, no sdist target);
`test_docs.py` `PIN` also over `decks/plots/README.md`. `ci.yaml` `latex` job after :365:
`/opt/conda-env/bin/python -m venv /tmp/venv && /tmp/venv/bin/pip install -q ./_extensions/
engine/mpl`, `make -C decks/quickstart charts-zip LIVERY=ncar DECKS_RUNTIME=native`, a probe in
`/tmp` with `LIVERY_DIR`, `PYTHONPATH`, `MATPLOTLIBRC` unset and `XDG_CACHE_HOME=/tmp/xdg`:
`use(zip)`, `__version__` equal to `_extension.yml`'s, the family registered from the cache, the
cycle equal to `livery.json`'s, a PDF plot whose `pdffonts` names the family. Docs:
`decks/plots/README.md` :124-131, `mpl_zip.py` `README` :44, `CLAUDE.md` "Plots", CHANGELOG
Plots. Close #81 from the PR body.

## Item 3: a watermark on every slide

### Context anchors
The marking strips are the model: `livery_build.py` `markings()` :328-355 (a text-less `banner`
always :338), `resolve()` :312-313, `emit_sty` :907-927, `emit_css` :1196-1206 (`tpx()` :1134);
`engine-common.lua` `deck_marking()` :455-468, `marking_texts()` :473-490; `engine-revealjs.lua`
`add_marking()` :414-424, the divs :726-736, the chain :881; `engine-beamer.lua` :742-746;
`slide-layout.lua` `marking_meta()` (after #146: every strip's text); `beamerouterthemeEngine.sty`
background :353-376 (`\engine@drawmarking` last :375), `\enginemarking` :383-386,
`\engine@drawstrip` :389-403; scss `.engine-marking` :157-175 (`z-index: 10`), the section's
`isolation: isolate` :115, `.engine-waves` `z-index: -1` :759, the art :799/:1009 `z-index: -1`;
`pptx_steps/marking.py`, `pptx_post.py` :55-65, `type_step.scale()` :43-51 (every `sz`: a
watermark run scales with the deck's step); `slide_layout._back_picture` :347-353 (`tree.insert(2,
…)`); `deck_qa.py` :42 `STRIPS`, :75 the HTML skip list, :226-228, `MEASURE_JS` :44, `main()`
:519-526; `livery.py` `placeholders()` :206-235; `tests/test_marking.py` (:38-57 the build,
:60-73 `strips()`, :87-125, :145), `tests/test_latex.py` :35, :278-280, `pages()` :217-219;
`docs/authoring.md` :66-72; `decks/fixtures/Makefile`, `parity.sh` :38-39.

### Shape
- Deck `watermark: DRAFT` (any text; `none` drops a livery default). Livery `watermark:`
  (optional): `text` (default null), `color` (role, palette name or hex; default `foreground`),
  `opacity` (0-1, default 0.08), `angle` (degrees counter-clockwise, default 30), `size` (points
  on the canvas, default 120, `half()`); **always in `livery.json`** (`WATERMARK` defaults), so a
  deck's `watermark:` shows under any livery. Centered, every slide (covers, closings, dividers,
  feature, full), **behind the content, over the art/field/waves**. Text only.
- One reader: `engine-common.lua` `watermark_text(meta, livery, who) -> Inlines | nil`.
- HTML: `add_watermark()` appends `<div class="engine-watermark">TEXT</div>` as the **last block
  of every slide** (after the art and waves in the DOM, so with `z-index: -1` it paints above them
  and under the in-flow body; `isolation: isolate` keeps it in print); `title-slide.html` gets
  `$engine-watermark$`. scss: `.engine-watermark { position: absolute; left: 50%; top: 50%;
  transform: translate(-50%, -50%) rotate(calc(-1 * var(--engine-watermark-angle))); color:
  var(--engine-watermark-color); opacity: var(--engine-watermark-opacity); font-size:
  var(--engine-watermark-size); font-weight: 700; white-space: nowrap; line-height: 1; z-index:
  -1; pointer-events: none }`; `emit_css` the four `--engine-watermark-*` (`size` via `tpx()`).
- PDF: `\enginewatermark{TEXT}` (`{}` none), `\engine@drawwatermark` in the background template
  after the style branches and before `\engine@drawmarking`: `\node[anchor=center,
  rotate=<angle>, opacity=<opacity>, text=EngineWatermarkColor, font=\engine@fsof{ratio}{1}
  \bfseries] at (0.5\paperwidth, 0.5\paperheight) {…}`; `emit_sty` the macros and color;
  `engine-beamer.lua` writes `\enginewatermark{…}` beside :742-746.
- pptx: `slide-layout.lua` `engine-watermark` MetaString ("none" when nil);
  `pptx_steps/watermark.py` (new, ~50 lines; imports `common` and `docprops`): per slide a text box
  `Watermark`, the slide's width wide and `size` pt × 1.2 tall, centered, `a:xfrm rot="<(360 -
  angle) * 60000>"` (OOXML rotates clockwise), one run in `color` with `<a:alpha val="<opacity *
  100000>"/>` under its `srgbClr` (lxml), bold, `Pt(size)`, no insets, centered; inserted **before
  the first shape holding text** (appended when none): on a content slide the title placeholder,
  so it sits at the back above the master's furniture; on a cover after `draw_cover`'s photo,
  field, waves and marks. `pptx_post.py` after `marking`, before `type_step`.
- QA: `deck_qa.py` :75 adds `.engine-watermark`; `MEASURE_JS` returns the slide's watermark text;
  `pdf_problems()` drops a word equal to it (`WATERMARK`, set in `main()` from the first HTML slide
  that has one, as `STRIPS` is), the pptx-as-PDF pass too. `livery placeholders`: a livery with a
  default text gets `watermark: SAMPLE`.
- Fixture: `decks/fixtures/draft.qmd` (`watermark: DRAFT`, `_body.qmd`), `DECKS += draft`: CI
  builds it, parity snapshots it as a new deck; every other deck is flat (no `watermark:`, no
  default: no element, node or shape).

### Commits (after item 2)
**6. The watermark: data, reader, HTML.** `livery_build.py` (`WATERMARK`, `watermark()`,
`emit_sty`/`emit_css`), the schema + `REFERENCE.md`, `engine-common.lua`, `engine-revealjs.lua`,
`title-slide.html`, the scss, `livery.py` `placeholders()`, `deck_qa.py`; `livery build
liveries/*/`. Tests: `tests/test_watermark.py` (new; `test_marking.py`'s shape): defaults, a role
and a hex, `size` 12.3 → 12.5, an angle out of range refused; the Lua reader (string, `none`, a
livery default, inlines); `test_deck_qa.py`: the word dropped, the element skipped;
`test_cli.py::test_placeholders` on a `tmp_livery` with a default text → `SAMPLE`. Proof: `make -C
decks/quickstart html` with `watermark: DRAFT` in a scratch copy, screenshots at 16:9 and
`?print-pdf`. CHANGELOG Decks + Liveries.

**7. pptx and PDF.** `slide-layout.lua`, `pptx_steps/watermark.py`, `pptx_post.py`,
`beamerouterthemeEngine.sty`, `engine-beamer.lua`, `latex/authoring.md` (`\enginewatermark`).
Tests: `test_watermark.py` pptx half (`strips()`'s harness with `watermark, type_step`): a
`Watermark` shape on every slide, `rot` = 330°·60000, `alpha` 8000, before the title placeholder,
absent under `none`, scaled by `type-body: 10`; `test_latex.py` `DECK` gains
`\enginewatermark{DRAFT}` and `test_watermark_on_every_page` (`pdftotext -layout`; if poppler
drops rotated text, `-raw`, and say so). Proof: `tests/app-open.sh` on a deck with the rotated,
alpha-colored box (new shape kind: run it at this commit).

**8. The fixture, docs, records.** `decks/fixtures/draft.qmd` + `Makefile`; `docs/authoring.md`
a `watermark:` bullet after `marking:`; `CLAUDE.md` a "Watermark" bullet beside the strips (the
reader, the three drawers, the DOM-order rule, the pptx insertion rule, `deck_qa`'s skip); the
ledger; CHANGELOG lines.

## Verification
1. Before commit 1, on `origin/main` (after sprint A merged): `tests/parity.sh baseline` and
   `tests/parity-latex.sh baseline`, same checkout, same day.
2. Every commit: `make test`.
3. After 1 and 3: `parity.sh check`: pptx and PDF identical for ncar, cu, nsi; HTML by the mark's
   element and `livery.css` only; `parity-latex check` identical. After 2: nasa-ccp's `livery check
   --qa`, `make measure` with placeholders, `make gallery`. After 7/8: parity names only `draft`.
4. The templates: after 1-2 `git status` shows only nasa-ccp's `template.pptx` and the ten
   `build/`.
5. Item 2: the venv step passes in CI; locally `python3 -m venv /tmp/v && /tmp/v/bin/pip install
   ./_extensions/engine/mpl` then the probe.
6. Item 3: `make -C decks/fixtures all qa`; PowerPoint and Keynote open `draft.pptx`.
7. The PR body: a section per commit, parity results, nasa-ccp's content slide and divider in
   three formats before/after, the draft fixture's cover and a content slide in three formats;
   `/pr-review N`.

## Risks
- The corner move is one commit across the build and three drawers: mechanical, no number
  changes, the two pptx labels kept, `logo=false` still dropping the `logo` corner; parity and the
  byte-identical templates are the net.
- HTML stacking of the watermark: `z-index: -1` is under the body only because the body is in
  normal flow; the `.full` figure box and the feature panel are absolute, so the watermark goes
  under them (say so in the docs; PDF and pptx draw it under the body alike).
- Rotated text in pdftotext: `deck_qa` drops it by its exact text.
- `a:alpha` on a text run in Keynote: untested; `app-open.sh` at commit 7. If refused, pre-blend
  the color with the slide's background (no alpha) and say so.
- The nasa-ccp art edit re-encodes two JPEGs once (quality 88 on a flat gradient).
- A clean venv in CI needs PyPI (~1 min), once per run.

## Open questions for Ben
1. Decided by Ben (2026-10-24): the key is `geometry.marks.<corner>` with `mark:` the name.
   Still open: `light`/`dark` on a corner entry as the role defaults (this design) vs requiring
   `marks:` to name every image.
2. Composed slides taking named corners later (their slots and the `*-height` keys stay).
3. nasa-ccp's art: the PIL paint-out of the committed JPEGs (this sprint) vs rerunning
   `ccp_art.py` from the template on your laptop with the new `with_bar()`.
4. `livery_mpl` on a release: git-only (this PR) or a wheel attached by `release.yml` too.
5. The `livery` console script: left out (#58's reason); confirm.
6. Watermark: text only vs an image stamp too; covers, closings and dividers included (recommend
   yes); the defaults 0.08 opacity, 30°, 120 pt (look at the draft fixture before the squash).
