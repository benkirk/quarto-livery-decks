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
