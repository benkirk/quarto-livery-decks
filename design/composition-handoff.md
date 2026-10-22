# Handoff: compositions as boxes

**State:** done (engine 3.5.0, 2026-10-17; `tests/test_compositions.py` holds the boxes).

Written 2026-10-17, after the docs handoff (framework #28-#32, engine 3.4.0), for a fresh
session. Read this, `CLAUDE.md`, and the newest entries of `docs/design/engine-and-liveries.md`
section 10. The repos, environment and conventions (one step per PR, CI green, merge
authorized, contact sheets before a PR, parity, a layman's summary before any questions, text
for approval in the chat itself) are as in `docs/design/nsi-handoff.md`, "The two repos and
how work flows". Two traps from the last sessions: in the engine checkout every `gh pr`
command needs `--repo benkirk/beamer-livery-theme`; and the shell is zsh, so `set -- $var`
does not split and a bare `=====` is a command. Tags: during the sprint a tag is moved
(`git tag -f vX && git push -f origin vX`) for a backwards-compatible step, bumped only for a
breaking one; both `release.yml`s upload over an existing release; ask before any tag push.

## Why

Every composition that is not a content slide is drawn by four implementations in two repos,
in two languages each: the title (cover, cover with a photo, `title=light`, the band), the
closing, the section divider and the feature (photo) slide. beamer draws them in TikZ
(`beamerouterthemeEngine.sty` 256-340, text in `beamerinnerthemeEngine.sty` 43-162); revealjs
in Lua SVG (`engine-revealjs.lua` 357-483, 561-630) and scss (`engine-revealjs.scss` 377-602,
630-635, 730-738); the pptx template builder in `livery_template.py` (253-374, with
`pptx_waves.py`); and the framework's post-render `slide_layout.py` (277-381) redraws the
cover and feature on the slide itself. The 2026-10-16 retrospective deferred the fix "until the
next new composition" (design section 7). NASA is the next livery and will want its own cover,
so it goes first.

A code survey (2026-10-17) put numbers on the drift. About twenty quantities are hand-copied
into three to five places:

| quantity | where |
|---|---|
| wave band opacities 0.18 / 0.10 | outer .sty 190-191; lua 442; `pptx_waves` 83 |
| cover band 0.65 between lines 2 and 3, wave shift 0 on covers | outer .sty 310-312; lua 461; `pptx_waves` 70-71 |
| wave line width | 0.8pt (.sty 182) / 2.4px (lua 427) / 2.4px (`pptx_waves` 66, 78) |
| cover photo box | beamer 0.52W anchored right (.sty 309); HTML left 48% width 52% (scss 380); pptx the full slide (`slide_layout.cover` 320) |
| straight field edge without waves | 0.5 (.sty 174) / 0.5 (lua 459) / 0.52 (`pptx_waves` 91) |
| mark y and height, title / section / closing | beamer 0.06H / 0.075H / 0.075H (inner 70, 108, 153); HTML 72px / 72px / 81px (scss 392, 507, 554); pptx 0.06 / 0.08 / 0.09 (template 336, 363, 279; `slide_layout` 331) |
| sign-off box (height, bottom, corner, aspect) | .sty 74-83; `emit_css` 447-455 + scss 117-130; template 147-154; `slide_layout` 334-340 |
| band box (top, bottom, split) | .sty 225-228; `emit_css` 460-461 + scss 452-468; lua 467-468; template 301-306; `slide_layout` 311-312 |
| band text column = split − margin − 0.04 | inner 44; `emit_css` 462 (64px); template 308 |
| band strip middle (1 − bottom)/2 | .sty 235, 241; `emit_css` 463; template 256 |
| title text width | beamer 0.47W / 0.62W (inner 62); HTML 44% / 58% **of the padded box** = 0.387 / 0.510 W (scss 393-394); pptx 0.50 (template 345); feature cover 0.44 (`slide_layout` 365) |
| title rule | 0.13W × 1.2pt (inner 56) / 208px × 3px (scss 425) / 0.065W × 1.5pt (template 350) |
| title vertical stack | beamer gaps 0.06/0.055/0.02/0.035/0.035 H; HTML em margins from top ≈ 0.20; pptx fixed date 0.375, title 0.43, rule 0.615, subtitle 0.64 |
| section text | beamer 0.62W, `\vfill`…`\vfill\vfill` (inner 107-122, parks the block at a third); HTML 62% of the padded box = 0.546W, centred in `geometry.divider` (scss 505-521); pptx 0.62 (template 367), `section_subtitle.py` centres in `divider` |
| closing text | beamer 0.62W, `\vfill` (inner 152-162); HTML 60% / 58% of the padded box (scss 560, 566); pptx title (m, 0.30, 0.62, 0.16), body (m, 0.49, 0.58, 0.36) (template 281-293) |
| feature | beamer and HTML: full-bleed photo, a 0.2H title bar at 72% dark, body in translucent blocks / a 52%-of-padded-box dark panel (.sty 334-340, 398; scss 577-602); pptx: the **title cover** (field + 65% band + lines + mark on the photo), title 0.34/0.16, rule 0.525, body 0.55/0.36 (`slide_layout` 361-381) |
| accent tab, margin, 1600×900 frame | `geometry.tab`/`margin` read in every file; the frame in `livery_build` 40, lua 60, template 31-33, `pptx_waves` 7, `section_subtitle` 42-45, `slide_layout` 371 |

And the copies disagree in ways a reader sees: beamer keeps the dark sign-off under
`title=light` on both cover variants (.sty 313, 328) and gives the section page the light
lockup on a primary field (inner 13-17, 109); pptx has no light closing; `art.title` under a
cover with a photo is omitted by beamer, painted under the photo by HTML, hidden in pptx; the
pptx feature is a different composition from the other two; nsi's `title=light` differs by
format (its notes). HTML's percentages being of the padded box, not the slide, means the
"everyone agrees on 0.62" cases are beamer and pptx only.

## What to build

One description of each composition, in the livery's resolved data, drawn by one drawer per
format. The band title already works this way in all three formats (beamer draws its text in
the background at the fractions; the scss places the photo box and column from `--engine-band-*`;
the builder and `slide_layout.band_photo` use the same numbers), which is why it was the
easiest composition to get consistent. Generalize it.

### The schema

`livery_build.py` gains `compositions(name, data, out)` (after `marks()`), writing
`out["compositions"]` into `build/livery.json`: ten fully resolved entries, so consumers pick
a name and never apply variant logic:

`title`, `title-photo`, `title-light`, `title-photo-light`, `title-band`, `closing`,
`closing-light`, `closing-band`, `section`, `feature`.

Variants are separate entries, not flags (a flag means conditionals in four languages; here
the only logic is "pick the name"). The resolver derives the variants from the base; a
`livery.yml` override on `title` reaches its variants, one on `title-photo` only that one.
`KNOWN` gains `compositions`; `merge()` already replaces lists whole, which is right for a box.

Every entry has every key (null when absent), so the emitters are table-driven. A box is
`[x, y, w, h]` in slide fractions, y down from the top-left (as `art.waves` and pptx are):

```
"title-photo": {
  "field":     {"role": "primary", "box": [0, 0, 0.5, 1]},   # the straight edge without waves; with waves the edge is line 2
  "art":       null,                                          # art kind painted under: title | section | closing (closing-band resolves its fallback to "title")
  "photo":     {"box": [0.48, 0, 0.52, 1]},                   # cover-fit, clipped to the box
  "band":      null,                                          # {"box", "role"} for the band style
  "waves":     {"style": "cover", "shift": 0, "role": "secondary", "opacity": [0.65], "line": 0.0015},
               # style: bands (opacity [0.18, 0.10] between lines 1-2, 2-3) | lines | cover (field to line 2, band 2-3 at opacity[0]); null without art.waves
  "bar":       null,                                          # feature: {"box", "role", "opacity"}
  "panel":     null,                                          # feature: {"box", "role", "opacity"}
  "mark":      {"role": "primary", "box": [0.06, 0.06, 0.199, 0.09]},   # null under geometry.logo.corner none; w = h * aspect * 9/16
  "signoff":   null,                                          # {"role", "box"} when the livery has a signoff
  "column":    {"box": [0.06, 0.20, 0.44, 0.66], "anchor": "top", "role": "primary-text", "tab": true, "rule": [0.13, 0.0033]},
               # anchor top | middle; rule [w of W, h of H] or null
  "fineprint": {"box": [0.06, 0.86, 0.44, 0.10], "anchor": "bottom", "role": "primary-text"},
  "eyebrow":   null                                           # section: {"label": "Section", "color": "secondary" | "#hex"}
}
```

Boxes kept are the ones at least two formats place. The pptx-only sub-boxes (date, title and
subtitle placeholders; the closing's headline/body split) are derived by the builder from
`column` and are not data.

**Derivation from today's knobs**, so a livery with no `compositions:` key changes nothing in
its yml (`m = geometry.margin`, mark width `h * geometry.logo.aspect * 9/16`):

- `title`: field primary, full; art `title` if set; waves `bands` at `art.waves.shift.title`
  (null without waves); mark `[m, 0.06, w, geometry.logo.title]` role primary (null if corner
  none); sign-off from `signoff` (`[m | 1-m-w, 1-bottom-h, w, h]`, role primary); column
  `[m, mark.y+mark.h+0.05, 0.50, 1 - that - 0.14]` anchor top, rule `[0.13, 0.0033]`, tab;
  fineprint `[m, 0.86, 0.50, 0.10]` anchor bottom.
- `title-photo`: field box `[0, 0, 0.5, 1]`; art null; photo `[0.48, 0, 0.52, 1]`; waves
  `cover`, shift 0, opacity `[0.65]`; column width 0.44; fineprint width 0.44.
- `title-light`, `title-photo-light`: field role background; art null; waves `lines` (cover
  variant: `cover` in the background role); mark and sign-off role `background`;
  column and fineprint role `foreground`.
- `title-band`: field `title.field`; art `title`; band `[0, top, 1, bottom-top]` role
  `title.band`; photo `[split, top, 1-split, bottom-top]`; waves null; mark and sign-off
  centred on `(1+bottom)/2` (the sign-off in its corner, the mark opposite; heights
  `title.signoff-height`, `title.logo-height`; role `title.field`); column
  `[m, top, split - m - 0.04, bottom-top]` anchor middle role primary-text; fineprint
  `[m, bottom + 0.018, column.w, 0.06]` anchor top role `title.field-text`.
- `closing`: art `closing`; waves `bands` at shift title; mark `[m, 0.09, w, geometry.logo.closing]`;
  column `[m, mark.y+mark.h+0.03, 0.62, 0.88 - that]` anchor middle, no rule, tab.
  `closing-light`: as the light title. `closing-band`: field `title.field`, art `closing`
  else `title`, the strip marks, column `[m, 0.10, 0.62, title.bottom - 0.13]` middle role
  `title.field-text`.
- `section`: art `section`; waves `bands` at shift section; mark `[m, 0.08, w, geometry.logo.section]`;
  column `[m, divider.top, 0.62, 1 - divider.top - divider.bottom]` middle, tab `divider.tab`;
  eyebrow `{label: divider.label, color: divider.label-color | "secondary"}`.
- `feature`, by `feature.style` in `livery.yml` (engine default `bar`): **bar**: photo full;
  field, art, waves, mark, sign-off null; bar `[0, 0, 1, 0.2]` dark 0.72; column
  `[m, 0, 1-2m, 0.2]` middle role `background` (white in every livery; `primary-text` is
  black for cu), tab false; panel `[m, 0.2556, 0.46, 0.667]` dark 0.72. **cover**: the
  `title-photo` composition with the deck's photo, column `[m, 0.34, 0.44, 0.52]` anchor top.
  Both are drawable by every format from the same keys; a livery picks (Ben: "we need
  flexibility to support the NCAR look and others"). Send Ben a contact sheet of both under
  ncar before setting ncar's.

**Resolved examples** (ncar: m 0.06, aspect 3.934, no sign-off, waves; nsi: band, sign-off
aspect 6.317, mark aspect 1.83, corner top-left):

| ncar | |
|---|---|
| `title.mark` / `title.column` | `[0.06, 0.06, 0.199, 0.09]` / `[0.06, 0.20, 0.50, 0.66]` top, rule `[0.13, 0.0033]` |
| `title.waves` | bands, shift 0.20, `[0.18, 0.10]`, line 0.0015 |
| `title-photo.field` / `.photo` | `[0, 0, 0.5, 1]` / `[0.48, 0, 0.52, 1]`, waves cover 0.65 |
| `title-light.field` / `.mark` | background / role background, waves lines |
| `section.mark` / `.column` | `[0.06, 0.08, 0.177, 0.08]` / `[0.06, 0.1333, 0.62, 0.7778]` middle, eyebrow secondary |
| `closing.mark` / `.column` | `[0.06, 0.09, 0.221, 0.10]` / `[0.06, 0.22, 0.62, 0.66]` middle |
| `feature.bar` / `.panel` (bar) | `[0, 0, 1, 0.2]` dark 0.72 / `[0.06, 0.2556, 0.46, 0.667]` dark 0.72 |

| nsi | |
|---|---|
| `title-band.field` / `.art` / `.band` | dark / `art/constellation.jpg` (kind title) / `[0, 0.276, 1, 0.448]` primary |
| `title-band.photo` / `.column` | `[0.62, 0.276, 0.38, 0.448]` / `[0.06, 0.276, 0.52, 0.448]` middle, primary-text |
| `title-band.signoff` / `.mark` | role dark `[0.06, 0.807, 0.391, 0.11]` / role dark `[0.744, 0.767, 0.196, 0.19]` |
| `title-band.fineprint` | `[0.06, 0.742, 0.52, 0.06]` top, role background |
| `closing-band` | field dark, art title (fallback resolved), the strip boxes, column `[0.06, 0.10, 0.62, 0.594]` middle role background |
| `section.mark` / `.signoff` | role primary `[0.06, 0.08, 0.082, 0.08]` / `[0.06, 0.92, 0.178, 0.05]` |

cu: `waves` null everywhere (the straight edge from `field.box`), `mark` null everywhere
(corner none), sign-off `[0.06, 0.925, 0.245, 0.04]`.

### Which value wins

Rule (Ben, 2026-10-17): where two formats agree, their value; where all three differ, HTML's
(the theme's look) unless the brand template gives a number; pptx placeholders are fixed boxes,
so pptx's sub-layout is derived, never a tie-breaker. One commit per row in PR 1.

| quantity | beamer | HTML | pptx | decided | reason |
|---|---|---|---|---|---|
| cover photo box | 0.52W anchored right | left 48%, w 52% | full slide | `[0.48, 0, 0.52, 1]` | the brand cover art's edge is at x = 0.487 (ncar report); pptx's surplus was hidden under the field |
| straight field edge (no waves) | 0.5 | 0.5 | 0.52 | 0.5 | two agree |
| wave line width | 0.8pt = 0.0018W | 2.4px = 0.0015W | 0.0015 | 0.0015 | two agree |
| band / cover / bar opacities | 0.18/0.10, 0.65, 0.72 | same | same | data | already agree |
| mark y: title / section / closing | 0.06 / 0.075 / 0.075 | 0.08 / 0.08 / 0.09 | 0.06 / 0.08 / 0.09 | 0.06 / 0.08 / 0.09 | two agree each |
| title column top | ≈0.205 | 0.20 | 0.375 | 0.20 (mark bottom + 0.05) | two agree; the pptx stack moves up under the mark |
| title column anchor | top | top | fixed y | top | Ben, 2026-10-17 |
| title column w, no photo | 0.62 | 0.510 | 0.50 | 0.50 | HTML and pptx agree |
| title column w, photo | 0.47 | 0.387 | 0.50 | 0.44 | none agree; the widest that stays on the opaque field (line 2 is at x ≥ 0.514) |
| title rule | 0.13W × 1.2pt | 0.13W × 3px | 0.065W × 1.5pt | `[0.13, 0.0033]` | width two agree; thickness HTML |
| fineprint | 0.02H above the floor | bottom 36px, w 50% | none | `[m, 0.86, w, 0.10]` anchor bottom | HTML; pandoc has no slot, pptx stays without |
| sign-off under title=light | dark | light | light | role background | two agree |
| section mark under title=light | light | dark | dark | role primary | two agree; the section field is still primary |
| art.title under a photo | none | painted, hidden | none | null | two agree |
| art.title under light | painted | painted | none | null | the brand's light cover (UCAR Communications' template, slide 4) is plain; moot today |
| section column | `\vfill` thirds, 0.62W | centred in divider, 0.546W | centred, 0.62 | centred in `[m, divider.top, 0.62, ...]` | box two agree; width two agree |
| closing column | `\vfill` thirds, 0.62W | centred in padding, 0.528W | fixed 0.30/0.49, 0.62W | `[m, 0.22, 0.62, 0.66]` middle | derived from the mark; width two agree |
| closing-band column | strut + `\vfill` | as closing | 0.30/0.49 | `[m, 0.10, 0.62, bottom - 0.13]` | must end above the strip (nsi bottom 0.724) |
| title=light under a band | ignored | ignored | light cover | ignored, with a warning | two agree; nsi's notes say light is not an nsi look |
| closing under title=light, pptx | light | light | dark Closing | new `Closing (light)` layout | parity with the title |
| feature | photo + bar + blocks | photo + bar + panel | the cover with a mark | per livery: `feature.style` | Ben: both looks must stay available; the brand guide forbids a mark on photos, so `bar` is the engine default |
| band fineprint gap | bottom + 0.02 | bottom + 0.018 | none | 0.018 | HTML (2px) |
| HTML waves drawn past the slide | — | yes (E = 1200px) | — | keep | a letterbox trick, invisible inside the slide; measure inside the slide |

### How each format consumes it, and what goes away

**`livery_build.py`.** `compositions()` + helpers (`mark_box`, `signoff_box`, `strip_boxes`,
`variant(base, **overrides)`); `band()` and `marks()` stay as the authoring knobs it reads.
`emit_sty` (283-389) writes a `% compositions` section: per entry and box
`\def\engine@c@<comp>@<box>@x{..}` `@y` `@w` `@h` (comp names without hyphens:
`titlephotolight`), scalars (`column@anchor`, `waves@style`, `waves@shift`, `waves@line`,
`waves@opacity@i/ii`, `bar@opacity`, `eyebrow@label`), roles as `\colorlet{EngineC<comp>Field}`
(`Text`, `Band`, `Bar`, `Eyebrow` likewise), image stems `\engine@c@<comp>@mark@img`,
`@signoff@img`, `@art`. Absent keys stay undefined; the sty tests `\ifcsname`. Lines 374-386
(the `engine@title@*` band macros) go. `emit_css` (392-510): the per-kind `SEL` loop
(481-486), the mark/sign-off rules (487-497) and the band block (501-508) become one `CSEL`
map, composition → selector, emitting **generic** vars so the scss reads one name set
regardless of variant: `--engine-cmp-<box>-x/-y/-w/-h` (px; `px()` with W for x/w, H for
y/h), `--engine-cmp-<box>-display: block|none`, `--engine-cmp-field`, `--engine-cmp-text`,
`--engine-cmp-column-justify: flex-start|center`, `--engine-cmp-rule-w/-h`,
`--engine-cmp-bar-fill: color-mix(in srgb, var(--engine-dark) 72%, transparent)`,
`--engine-cmp-panel-fill`, `--engine-cmp-eyebrow`, the art `background`, the mark `::after`
image, the `.engine-signoff` image. Selectors: `title` → `div.reveal div.slides
section.engine-title.quarto-title-block`; `title-photo` → `… .engine-title-photo` (the Lua adds
it for a deck photo or the default); `title-light` → `html.engine-title-light div.reveal …`;
`title-photo-light` → both; `title-band` → `… .engine-band`; `closing` → `.reveal .slides
section.slide.level2.closing`; `closing-light`, `closing-band` likewise; `section` →
`… .engine-section`; `feature` → `… .feature`. Emit base → photo → light → photo-light so
specificity selects. The band vars (456-473), the per-kind logo vars (417-419) and the divider
vars (423-424) go; the content-slide vars stay. New `tools/test_compositions.py` (engine; in
CI's "Check the liveries are built" step): asserts the resolved boxes of ncar, cu and nsi (the
framework's, by path, when present) against today's HTML/PDF numbers in fractions, with an
`EXPECTED_DELTAS` dict naming each decided change; asserts the band invariants (column
w = split − m − 0.04, strip centre (1+bottom)/2, photo = band right of split) and the light
variants' roles.

**`beamerouterthemeEngine.sty`.** One drawer replaces seven: `\engine@drawcomp{<comp>}` =
`\engine@cfield` (a rect of `field.box` in its role, or, when `waves.style` is `cover`, the
region left of line 2) → `\engine@cart` → `\engine@cphoto` (`\engine@coverbox` of
`\inserttitlegraphic` or the feature image into `photo.box`, clipped to the box; the line-1
clip of `\engine@photo` goes) → `\engine@cband` → `\engine@cwaves` (by style; `\engine@band`
and `\engine@lines` take the opacities and `line\paperwidth` from the comp) → `\engine@cbar`
→ `\engine@cmark` / `\engine@csignoff` (nodes anchored north west at `(x, 1-y)`, `height =
h\paperheight`) → `\engine@ctext{<comp>}`. Helpers `\engine@box{<comp>}{<box>}` (loads
`\engine@bx` `\engine@by` `\engine@bw` `\engine@bh`, `by = (1-y-h)\paperheight`) and
`\engine@ifcbox{comp}{box}{yes}{no}`. The `background` template (256-278) picks the name:
`\engine@titlecomp` from `\inserttitlegraphic`, `\engine@titlestyle` and `\engine@title@style`
(band + light: `\PackageWarning`, band wins); closing → `closing` / `closinglight` /
`closingband`; section; feature. Deleted: `\engine@signoff` for field styles (74-83 stays for
normal frames), `\engine@photo` (197-205), `\engine@bandbox` and `\engine@bandmarks` (223-242),
`EngineTitleField` (244-247), `\engine@drawtitlebg` through `\engine@drawfeaturebg` (283-340),
`\engine@featuretitle` (398), and the literals 0.8pt / 0.18 / 0.10 / 0.65 / 0.52 / 0.5.

**`beamerinnerthemeEngine.sty`.** Text is placed by the background in the column box, as the
band does (`\engine@bandtext`, 43-59, is the model): `\engine@ctext{comp}` sets a TikZ node
`[anchor=north west | west, text width=\engine@bw, inner sep=0pt]` at the box's top-left or
left-middle holding the composition's stack: `\engine@titlestack` (date, tab + title +
subtitle, rule from `column.rule`, author, institute: today's `\engine@bandtext` body, now for
every title comp), `\engine@sectionstack` (eyebrow in `EngineC…Eyebrow`, title, subtitle),
`\engine@closingstack` (`\engineclosingcontent` stores the headline and a `\global\setbox` of
the body at `column.w`; the background uses them, as `\enginefullcaption` does), the fineprint
as a node anchored south west / north west in `fineprint.box`. `title page`, `section page`
and the closing frame bodies become `\vbox to \textheight{\vfil}`. **Fallback decided**: the
closing body is user content that may hold overlays (`\pause`), which a node cannot; keep the
closing body in the frame body positioned with `\vbox to`, only the headline in the node. The
feature `frametitle` under style feature places the title in `column.box` (centred in the
bar) instead of the `0.045\paperheight` stack; the body on feature frames goes into
`\begin{enginefeaturepanel}` (the Lua wraps it; a minipage of `panel.w` on a `BrandDark` fill
at `panel.opacity`, white text), the one new drawing primitive. Deleted: `\engine@fieldlogo`
(13-17), `\engine@coverpage` (60-91), the vskip/vfill scaffolding of the section page
(107-122) and closing (152-162), `\engine@bandtext`'s width arithmetic (44),
`\engine@featureblocks`'s translucency (190-202).

**`engine-revealjs.lua`.** Keeps the SVG primitives (357-436) and `photo_img`. `waves`,
`photo_waves`, `band_art`, `light_waves` (438-477) become one `comp_art(comp, src)`: `<img>`
when `comp.photo` (the box is CSS), then an `<svg>` with, by `comp.waves.style`: bands →
`band(1,2)`, `band(2,3)` at `opacity[1..2]` + lines (`stroke-width = line*W`); lines → lines;
cover → `field(2)` in the field role + `band(2,3)` at `opacity[1]` + lines; null and
`field.box.w < 1` → a rect of the field box; `comp.band` → the band rect. `Pandoc()` 561-575
and 581-607 shrink to: pick the comp name (band wins over light with `quarto.log.warning`),
`data-background-color = r[comp.field.role]`, classes `engine-field` when the field role is
not background, `engine-band`, `engine-title-photo`, insert `comp_art`. The feature branch
(608-630) adds nothing new (bar and panel are CSS). `along()` (372-376, unused) goes.

**`engine-revealjs.scss`.** Title (377-446) on the generic vars: `.engine-title-photo-img
{ left/top/width/height: var(--engine-cmp-photo-*) }`; `.engine-title-text { position:
absolute; left/top/width/height: var(--engine-cmp-column-*); display: flex; flex-direction:
column; justify-content: var(--engine-cmp-column-justify) }` (the band's rule, 458-468, made
general); `::after` and `.engine-signoff` from `--engine-cmp-mark-*` / `-signoff-*` with
`display`; `.engine-title-rule { width/height: var(--engine-cmp-rule-*) }`; `.engine-fineprint`
from its vars; one colour rule `color: var(--engine-cmp-text)` replaces `&.engine-field`
(443-445) and the `html.engine-title-light` rules (630-635). The band block (448-496) shrinks
to the `.closing.engine-band` colour rule. Section (501-544): padding
`var(--engine-cmp-column-y) calc(100% - x - w) calc(100% - y - h) var(--engine-cmp-column-x)`,
`h1 { max-width: none }`, the eyebrow `color: var(--engine-cmp-eyebrow)`, the mark from the
vars. Closing (549-572): the same padding form; the `max-width` rules go. Feature (577-602):
`> h2 { top/height: var(--engine-cmp-bar-*); background: var(--engine-cmp-bar-fill) }`,
`.engine-feature-body { position: absolute; left/top/width: var(--engine-cmp-panel-*);
background: var(--engine-cmp-panel-fill) }` (`padding-top: 230px` goes). Print (730-738):
restate the same vars with `!important`. After this no literal px remains in the title, band,
section, closing or feature rules; the content-slide rules are out of scope.

**`livery_template.py`.** `title_slide`, `band_title_slide`, `closing`, `section_header`
(266-374) become `field_layout(name, comp, kind)` = `comp_shapes(comp, rids)` (art pic; the
field rect from `field.box` or the wave field; `pptx_waves.comp_shapes`; the band rect; the
default photo via `cover_pic` into `photo.box` when `art.titlegraphic` and the comp has a
photo box, i.e. the band; `box_pic` for mark and sign-off) + `column_placeholders(comp,
kind)`: title kinds → dt `(x, y, w, 0.045)`, ctrTitle `(x, y+0.055, w, 0.16)`, the rule at
`y+0.23` (`rule.w`, `ln w = rule.h * H_EMU`), subTitle to the column bottom for `anchor: top`;
for `anchor: middle` the rule sits at `y + h/2`, ctrTitle anchored `b` above it, dt at the
column top, subTitle anchored `t` below; closing kinds → headline `(x, y, w, 0.4h)` anchor
`b`, body `(x, y + 0.4h + 0.03, w, 0.6h - 0.03)` anchor `t`; section → title `(x, y, w,
0.12)`, body below (`section_subtitle.py` re-places them). Layouts: `Title Slide` ←
`title-band` or `title`; `Title Slide (light)` ← `title-light`; `Closing` ← `closing-band` or
`closing`; new **`Closing (light)`** ← `closing-light` (`EXTRA_LAYOUTS`, `LAYOUT_TYPES`;
`livery_check.py` follows through `EXTRA_LAYOUTS`); `Section Header` ← `section`. Media:
`build()` 432-442 names files `mark-<role>`, `signoff-<role>`, `art-<kind>`, `photo`, and
469-492 become a `media_for(comp)` loop (rId2 mark, rId3 sign-off, rId4 art, rId5 photo).
Deleted: `logo()` and `signoff_pic()` (143-154) → `box_pic(rid, name, box)`; `band_strip()`
(253-264); every literal in 266-374. **`pptx_waves.py`**: `cover_shapes`, `wave_shapes`,
`straight_cover_shapes` (66-96) → `comp_shapes(lines, comp, first_id, w_emu, h_emu,
field_slot, line_slot)` by `waves.style`, alpha `opacity * 100000`, `ln w = waves.line * w_emu`,
the straight field as a rect of `field.box`; the 0.52 / 65000 / 18000 / 10000 / 2.4 literals go.

**`slide_layout.py`** (framework). `COMP = LIVERY["compositions"]`; `cover()` / `title_cover()`
(315-352) → `draw_cover(slide, comp, photo)`: `_back_picture` into `comp.photo.box`,
`pptx_waves.comp_shapes(comp)`, mark and sign-off pictures from their boxes, the layout's tab
and rule copied as today; `band_photo` (309-312) → the same `_back_picture` into
`title-band.photo.box`; `feature_cover` (361-381) → `draw_feature` by `feature.style`: bar →
the photo full, a rectangle for the bar with `fill.fore_color` dark and alpha 72% (python-pptx
has no alpha API: write `<a:alpha val="72000"/>` with lxml, as `pptx_waves` does), the title
placeholder framed to `column.box` anchor middle in white, the panel rect framed to
`panel.box` and cut to the body's `_text_height` estimate (the `caution_box` pattern,
143-163), the body on it in white, no mark, `showMasterSp="0"`; cover → `draw_cover` with the
feature column. `main()` 411-423: the light switch only when not band; `closing` + light →
`Closing (light)`. Deleted: `BAND`, `COVER_TITLE/RULE/BODY` (61-63) and every literal in
`cover` / `feature_cover`. **`section_subtitle.py`**: `BLOCK_TOP/BLOCK_BOTTOM` (43-44) from
`compositions.section.column.box` (y and y+h in px); `LABEL_PT/LABEL_GAP/BODY_GAP` are type,
not boxes, and stay. **`slide-layout.lua`**: unchanged.

## The PRs

Ten, each shippable; engine PRs regenerate `liveries/{ncar,ucar,ucp,ncarucar}/build/` (and
the templates when the builder changes); framework PRs vendor the merged engine (`make
vendor-engine` to build against a branch, `quarto update` after the tag, which must then show
no diff) and regenerate cu's and nsi's `build/` and templates. Versions: PR 1 re-cuts v3.4.0
(data only); PR 3 bumps `_extension.yml` and `engine-revealjs.lua` to 3.5.0 (the first visible
change); later PRs re-cut v3.5.0; the framework re-cuts v1.0.0 after each vendor PR. Ask
before each tag push.

| # | repo | what | visible change | check |
|---|---|---|---|---|
| 1 | engine | `compositions()` + emitters + `KNOWN` + `tools/test_compositions.py`; `build/` regenerated. Commit 1: boxes at today's HTML/PDF numbers (the test asserts equality); then **one commit per decided row** of "Which value wins", each editing one default, its `EXPECTED_DELTAS` entry and `build/` | none | `livery_build.py --check`, `livery_check.py` ×4, the test, `tools/parity.sh check` (HTML differs only in `livery.css`) |
| 2 | framework | vendor PR 1; `livery_build.py` on cu, nsi; **the measurement tool** `docs/common/utils/comp_measure.py` + `make measure` (below); a third fixture deck `photo-light` (`DECKS += photo-light`: `titlegraphic` + `title=light`); the before-picture committed as `docs/design/compositions-baseline.md` (every format's deviation from the boxes before any switch) | none | parity clean but `livery.css`; the tool runs on fixtures × {ncar, cu, nsi} |
| 3 | engine 3.5.0 | HTML reads the boxes: `emit_css` CSEL blocks, the scss rewrite, Lua `comp_art` | HTML: title mark 0.08 → 0.06, title column 0.51 → 0.50 / 0.387 → 0.44, section and closing widths → 0.62, closing padding → the box | screenshot diff of `talk-quarto.html` and `quarto-demo.html` restricted to the listed boxes; all else pixel-identical |
| 4 | engine | beamer reads the boxes: `\engine@drawcomp`, `\engine@ctext`, the stacks; the deletions in both `.sty` | PDF: section and closing columns centred in their boxes, mark y 0.075 → 0.08 / 0.09, title widths, rule 0.77pt, lines 0.68pt, light sign-off and section mark fixed, band+light warns | `tools/parity.sh check`: only title, divider, closing and feature pages differ; `make variants` |
| 5 | framework | vendor PRs 3 and 4; contact sheets (HTML, PDF) | HTML and PDF as above under ncar, cu, nsi | `comp_measure.py` HTML + PDF within tolerance; parity: pptx byte-identical, PDF/HTML differ on the listed slides only |
| 6 | engine | pptx: `pptx_waves.comp_shapes`, `field_layout`, `Closing (light)`, the media loop; four templates regenerated; `livery_check.py` for the new layout | templates only | `livery_check.py` ×4 byte-identical rebuild; CI |
| 7 | framework | vendor PR 6; `slide_layout.py` and `section_subtitle.py` from the boxes; cu, nsi templates; contact sheet with pptx | pptx: title stack up under the mark, column widths, photo box, straight edge 0.5, light closing, band ignores light, marks from boxes | `comp_measure.py` all three formats; parity: pptx XML differs on the title, divider and closing layouts/slides only; LibreOffice review of fixtures × 3 liveries |
| 8 | engine | feature `style`: bar (beamer `enginefeaturepanel` + frametitle in the bar; HTML done in PR 3) and cover (the cover drawer with the deck photo); a contact sheet of both under ncar for Ben, who sets ncar's | PDF feature per style | parity: feature pages only |
| 9 | framework | vendor PR 8; `draw_feature` in `slide_layout.py` | pptx feature per style | `comp_measure.py` feature row; parity: feature slides only |
| 10 | both | docs: design §4 (the `compositions:` override key; `build/livery.json` gains `compositions`), §5 ("Compositions" is already there: make it the contract), §7 (done), §10 log; both CLAUDE.md (a Compositions bullet, `make measure`); cu/nsi notes (light under band resolved); the engine README's Liveries section; `make gallery` rerun | none | CI |

Deletions happen in the PR that replaces each piece; no separate deletion PR. PRs 3 and 4 may
merge as one engine release if the review load allows; keep the commits separate.

## Verification

**`comp_measure.py`** (`docs/common/utils/`, `make measure` in a deck directory, `LIVERY=` as
elsewhere): for each built deck and format, render the title, the first divider, the closing
and the first feature slide to 1600×900 PNGs (HTML: Playwright via `deck_qa.serve` and
`Reveal.slide`, transitions off, as `screenshots.py` does; PDF: `pdftoppm -scale-to-x 1600
-scale-to-y 900`; pptx: `soffice --headless --convert-to pdf`, then the same; skipped with a
note when `soffice` is missing, as `deck_qa` skips without Playwright). Pick the composition
name the way the formats do (band / photo / light from the deck's metadata and the livery).
Per box: **overlay** the box rectangles in magenta on each shot
(`_qa/compositions-<livery>.png`, rows = compositions, columns = HTML | PDF | pptx: the
contact sheet for Ben); **measure**: filled boxes (the field edge on a photo cover, the band,
the bar, the panel) by colour transition along the box's mid scanline or column; image boxes
(mark, sign-off, photo) by the bbox of non-field pixels inside the box dilated by 0.03; the
column by the bbox of text-coloured pixels inside the dilated column (left edge vs x, top vs
y for `top`, centre vs y + h/2 for `middle`, right edge ≤ x + w). Tolerance 0.02 (0.03 for
pptx's middle-anchored stacks, whose date placeholder is fixed), 0.005 for drawn edges.
Output `_qa/measure.tsv` (livery, deck, format, composition, box, edge, expected, measured,
delta) and a table on stdout; exit 1 over tolerance. CI: `ci-liveries.yaml` installs
`libreoffice-impress` (apt; Ben allows anything on runners) and runs `make measure` on the
fixtures after the PDF step.

**Parity** (`tools/parity.sh` in the engine; `docs/common/utils/parity.sh` here): a baseline
on `main` before each PR; after, the diff must be *exactly* the slides or pages listed in the
PR's row (title, dividers, closing, feature; the HTML always differs in `livery.css` and the
title markup). Any other page or XML part differing is a regression. PR 2's `photo-light`
fixture joins `DECKS` so the baseline covers the four title variants under ncar (waves), cu (no
waves, no mark, sign-off) and nsi (band, extends, sign-off, top-left mark). Note the framework
baseline in `_baseline/` dates from engine 3.2.0; rebuild it from `main` first.

**Contact sheets** from `comp_measure.py` per livery, with PRs 5, 7, 8 and 9, beside the
before-picture from PR 2; `make gallery` at PR 10 for the README.

## Decided with Ben (2026-10-17)

- Scope: title, closing, section, feature. Now, before NASA.
- Disagreements per quantity by the rule above; the table is the decision.
- The title text block anchors at the top, under the mark.
- The feature look is per-livery data (`feature.style`), both looks drawable everywhere;
  engine default `bar`; ncar's chosen from a contact sheet.
- The closing body keeps a `\vbox` fallback (overlays); LibreOffice goes into CI.

## Open for the session

1. pptx middle-anchored stacks (band, closing) leave a gap between the fixed date placeholder
   and a short title: accept, or drop the date placeholder from those layouts.
2. Whether PRs 3 and 4 ship as one engine release.
3. `extends`: the resolver, not TeX, handles a flavor whose parent has no band (nsi → cu); add
   a `test_compositions.py` case for it.
4. `?print-pdf` restates paddings; keep the restatements on the same vars.
5. Media renumbering changes every template's bytes (expected in PRs 6 and 7; the
   byte-identical rebuild check is what matters).
