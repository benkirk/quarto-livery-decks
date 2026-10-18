# Onboarding notes: cu

The reference deck is the CU Center for National Security Initiatives' master deck,
`NSI MASTER SLIDE DECK JULY2026 EXTERNAL.pptx` (a Google Slides export, July 2026), supplied by
Ben from NSI. It is not committed: download it beside this file as `reference/cu.pptx` to rerun
`livery_inspect.py`. The stricter authority is the CU Boulder brand site
(https://www.colorado.edu/imc/cu-boulder-brand/visual-identity, .../campus-lockups-and-marks);
the deck is "a strong guide" where the two differ (Ben, 2026-10-16).

`report.md` is the tool's reading of the deck. Decisions, in the order of the design's human steps:

## Layout mapping

The deck uses two of its eleven layouts: `1_Title Slide` (black field, a gold band with the title
and date, a campus photo filling the right of the band, the two lockups along the bottom) and
PowerPoint's default `Title and Content`. The rest are PowerPoint's stock layouts, unused. So the
template is generated from the livery's data like the NCAR family's, not mapped: title field in
the primary (gold) with black text, the generic builder's composition. The deck's band
composition is a follow-up (`title: band` style for the builder and both engine themes).

## Roles

Palette from the brand site (CU Gold `#CFB87C`, Black, Dark Gray `#565A5C`, Light Gray `#A2A4A3`;
secondary Accessible Gold `#8D7334`, Sky Blue `#096FAE`, Light Gold `#F3F0E9`, Dark Blue
`#0A3758`, Light Blue `#EEF5F8`). Primary gold carries the fields with black text (the deck's
band); `primary-contrast` is the accessible gold, since CU Gold is not accessible as text on
white; `highlight` is sky blue, which the brand allows for text only; `muted` is the dark gray;
`surface` the light gold; `secondary` (rules) the dark gray; the pptx `hlink`/`folHlink` slots
are overridden to the accessible gold and sky blue for the same reason.

## Type sizes

`livery.yml` `type:` takes the NSI master deck's sizes, in points on its 13.33 x 7.5 in canvas
(engine >= 3.6.0): body 16 (its dense slides 12-14, which a deck reaches with `scale=`), slide
titles 32 (it runs 32-36, bold), in-body heads 20, footnotes 9, the cover title 48 with the date
28 (a subtitle, which its cover lacks, at the heads' 20), dividers 60, the closing 48. Its master's own ladder (40/28/24/20/18) is Office's untouched
default, which none of its slides use; the list levels 16/14/13/12/11 follow its text boxes.

## Fonts

The brand's Helvetica Neue (Condensed for headlines, Regular for body) is Monotype's and cannot be
bundled. The pptx names `Helvetica Neue` without embedding (Macs have it; Windows substitutes
Arial, which the deck itself uses as its second font). HTML and PDF bundle TeX Gyre Heros (a free
Helvetica clone, GUST Font License, from TeX Live) in four faces, and Heros Condensed as the
headings family for the brand's condensed headlines (`typography.headings`; the pptx keeps
Helvetica Neue for titles too: "Helvetica Neue Condensed Bold" is a face of that family on macOS,
not a family name PowerPoint resolves everywhere, so `pptx.heading-typeface` stays unset).
Follow-up: embedding Heros into the pptx (CFF outlines need converting, and PowerPoint's fntdata
blobs come from PowerPoint). Since engine 3.3.0 the livery names the real face as
`installed-fonts` (Helvetica Neue, the headings as Helvetica Neue Condensed Bold): the HTML deck's
`@font-face` rules try it by `local()` name before Heros, and a PDF built with
`themeoptions: [fonts=brand]` on a machine that has it embeds it (checked on a Mac: `pdffonts`
lists the HelveticaNeue faces; under `fonts=bundled` Heros). Nothing copies the font files.

## Lockups

The deck carries unit lockups only (NSI; the Research & Innovation Office). The plain CU Boulder
lockup is CU's own web brand asset, the one-line version (CU monogram and "University of Colorado
Boulder"): `cdn.colorado.edu/static/brand-assets/live/images/cu-boulder-logo-text-black.svg` and
`-white.svg` (black or white text, the monogram gold either way), kept as `logos/cu-boulder-
lockup{,-white}.svg` with a PNG (`rsvg-convert -h 240`, for HTML and pptx) and a PDF (`rsvg-convert
-f pdf`, which LaTeX picks over the PNG of the same name, so the PDF deck's lockup is vector) of
each. The lockup library (ucomm-exten2.colorado.edu, CU login) has the stacked versions too.
Until 2026-10-16 the deck's RIO lockup stood in; it now belongs to the nsi flavor, which uses it.
The black-text lockup serves the gold field too (`logo.medium.dark`), the gold being light. The
brand wants the lockup as a "sign off" at the bottom, so it is the
livery's `signoff` (bottom-left, the deck's placement), `geometry.logo.corner` is `none` (no mark
top right; the NSI flavor puts its own mark top-left) and the page number sits bottom-right as in
the deck.

## Art

No wave curves: the title field ends in a straight edge in every format. `art.content`
(`art/content-flatirons.jpg`) is a Flatirons photo desaturated, blended 78% to white and
softened (contrast 0.8): Ben's choice over the deck's space photo, the deck's own campus photo
and a faint CU monogram (a translucent lockup alters its colors, which the brand forbids; the
buffalo marks are Athletics'). Its source is a Reddit wallpaper post (r/wallpaper `hr1v4a`,
"The Flatirons, Boulder, CO", user HellsJuggernaut, `i.redd.it/o6c18zg6vta51.jpg`): the rights
are unverified, so before any public use swap it for a photo from the brand's CU-only textured
backgrounds library or one CU owns. Swap the file to change it.

## Follow-ups

Done: the `nsi` flavor (`../../nsi/`, on the engine's band title style), Heros Condensed
headings, `livery_check.py`, the plain CU Boulder lockup (2026-10-16).

Open (deferred 2026-10-16, none blocking):

- **The content photo's rights.** `art/content-flatirons.jpg` is a Reddit wallpaper with
  unverified rights (see Art): swap it for a CU-owned photo (the CU-only textured backgrounds
  library, or CU's photo library) before any public use. nsi is not affected (its own photos).
- **pptx fonts are not embedded.** The pptx names Helvetica Neue unembedded (Macs have it,
  Windows substitutes Arial). Embedding TeX Gyre Heros needs its CFF outlines converted and
  PowerPoint's fntdata blobs made (`pptx.fonts`; `embed_fonts.py` does nothing without them).
  A possibility Ben raised, if portability turns out to matter: name a substitute font in the
  pptx instead (`pptx.typeface`, and `heading-typeface` for titles), most simply Arial, which
  every PowerPoint has and the NSI deck itself uses as its second font, at the cost of the
  brand's Helvetica look on Macs. Either route is a livery change only; rerun
  `livery_template.py` after it. HTML and PDF already prefer an installed Helvetica Neue
  (`installed-fonts`, see Fonts); a PDF built that way carries the face to every reader, which
  is the builder's licence question, not the repo's.
- **The accent tab vanishes on the gold fields.** `accent` and `primary` are both CU Gold, so
  the tab beside the title, divider and closing headlines is gold on gold in every format (it
  shows on white content slides). A darker accent (black, dark gray) would bring it back;
  undecided, since the brand gives gold that role.
- **The pptx title text sits at fixed positions.** The pptx Title Slide's date, title, rule and
  subtitle placeholders are placed for a one-line title; HTML and PDF set the block in the
  flow (the band style centres it in the band), so a two-line title lands differently in pptx.
  Framework-wide (every livery, cover and band), not cu's alone.
- **Two older quirks, framework-wide.** In reveal's print view (`?print-pdf`) the closing
  slide's block sits high instead of centred (the engine's print padding); in pptx a slide
  with a layout marker (`.closing`, `.vcenter`, ...) keeps the empty notes page the marker
  leaves when `slide_layout.py` removes it.
- **Other CU lockups.** The one-line CU Boulder lockup is in; the lockup library (CU login)
  also has the stacked versions, should a layout want one.

## Chart colors (2026-10-18)

Generated from the brand (design/charts-and-plots.md), with the campus in it (Ben, 2026-10-18:
"their campus is famously sandstone with red tile roofs and it would be awesome to work this into
the design"). CU publishes no chart palette, and the brand has one hue, gold, plus neutrals and
two blues. So `livery.yml` `charts:` adds colors sampled from the campus photo, nsi's
`art/campus.jpg` (median of patches; the photo is at golden hour, so the shaded facades read
gray and were left out):

- **The roof tile in sun, `#9C3F29`**, is the third brand hue (`extended`). CU's web style guide
  names the tile "Brick", `#AE5A39`, but that lighter value is dE 13.5 from the slots' CU Gold,
  under the 15 the first three slots need pairwise (a scatter); the photo's tile is dE 20.2 (16.8
  for color-blind readers), 6.7:1 on white and 3.2:1 on black.
- **The campus map** (`maps.campus`, the default color map): CUB Light Gold `#F3F0E9`, a blend
  `#D2B39F`, the Flatirons' sandstone `#AE7858`, the tile in sun `#9C3F29`, in shade `#76312B` and
  in deep shade `#412429`. The sandstone alone is too gray for a series (chroma 0.08).
- **The diverging scale**: Sky Blue to the tile, the sky over the roofs, a neutral midpoint.
- **Sage** (Ben: "if CU needs any more color diversity I think a sage green could be aesthetic"):
  classic sage `#9CAF88` is too gray for a series (chroma 0.06), so the generator holds its hue
  and raises it to the chroma floor, `#7A9C51` on white, `#7D9F54` on black; the series had no
  green before. It is the fourth hue (`extended`).

The series: CU Gold moved into the mark band (`#CFB87C` becomes `#AD8E38`, close to the brand's own
Accessible Gold), the tile, Sky Blue `#096FAE`, sage, then four generated hues at the brand's
chroma: `#812F62 #00A1B8 #334C98 #008777` on white, `#913E71 #AE660D #009EB1 #B8566A` on black (in
the order the generator picks for separation). Every check passes.

The fact check found the ten palette colors exactly as the brand site and cu.edu publish them.
CU's web theme (`CuBoulder/tiamat-theme` 8df166a) adds brick `#AE5A39`, medium blue `#4FC3F7`,
link blue `#0277BD` and light green `#DCEDC8`, mostly Material Design values, and the accessibility
page tests a "Web Express Blue" `#0377BD`: none is a brand standard, so none is used. If a CU chart
palette or a fuller web palette turns up (styleguide.colorado.edu/colors), it goes in
`charts.extended` and replaces generated hues.

**styleguide.colorado.edu/colors, read 2026-10-18** (hexes from its `css/ucb-styles.css`): the web
style guide's palette, "chosen from the Google Material Color Palette", one secondary or tertiary
color per page. Beyond Black and Gold it shares nothing with the brand page: neutrals Light Gray
`#EEEEEE`, Dark Gray `#424242`; link Blue `#0277BD`; secondary Light Blue `#E1F5FE`, Light Green
`#DCEDC8`, Light Gold `#F1EBD9`, Medium Blue `#4FC3F7`, Dark Blue `#01579B`, Brick `#AE5A39`;
application (error, warning, success) Red `#B71C1C`, Green `#2E7D32`, Amber `#FFD740`;
notification Light Red `#FFEBEE`, Yellow `#FFF9C4`. The brand page
(colorado.edu/imc/cu-boulder-brand/visual-identity) confirms our nine exactly (its Sky Blue RGB,
9 112 174, is `#0970AE`, one off its stated hex). So CU publishes no further brand hue; Brick and
Medium Blue are the only candidates for `charts.extended`, and they are website UI colors, not
brand colors: a decision for step 5.

The style guide's source, `CuBoulder/styleguide` (`scss/modules/_colors.scss`, last changed
2019-12-06; its header links Material Design's color tool), defines two more, `$purple #5E35B1`
and `$orange #FF9800`, that the site never lists, and its `docs/_data/colors.yml` has errors (Blue as
`#E1F5FE`, Red as Brick's `#ae5a39`): not a source to pin brand colors to.

**CU Boulder Accessible Color Contrast Recommendations** (Rev. 6-28-17, one page, CU Digital
Accessibility; `colorado.edu/digital-accessibility/sites/default/files/attached-files/
cu_boulder_accessible_color_contrast_recommendations_rev_6-28-17.pdf`): a WCAG 2.0 AA text/background
matrix of White, Black, Gold `#CFB87C` (PMS 4525 C, CMYK 0 10 48 22), Dark Gray `#565A5C` (PMS 425 C,
CMYK 38 28 21 63), Light Gray `#A2A4A3` (PMS 422 C, CMYK 16 11 11 29) and Web Express `#007BC8`
(Process Blue C). It confirms our gold and grays with their Pantones, and that Gold and Light Gray
fail on white even as large text (why the chart slots move CU Gold to `#AD8E38` and never use Light
Gray as a series). Web Express was the old Web Express CMS's blue: `#007BC8` here, where the
accessibility web page tests `#0377BD`; superseded by CUB Sky Blue `#096FAE`, and unused.

**Plots in PDF take Type 3 fonts.** TeX Gyre Heros is a CFF OpenType font (`OTTO`). Asked for
`pdf.fonttype: 42`, matplotlib (3.11) embeds it but declares it a TrueType font, and poppler reports
"Mismatch between font type and embedded font file"; Ghostscript renders it silently. So
`livery_build.py` gives a livery whose base family is CFF `pdf.fonttype: 3` (`is_cff()`): the
glyphs are embedded as Type 3 procedures, still subset and searchable (pdffonts: `Type 3`, `uni
yes`). nsi inherits it. SVG takes paths and PNG pixels, so only the beamer PDF is affected.
