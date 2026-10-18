# Onboarding notes: nsi

The CU Center for National Security Initiatives, a flavor of `cu` (`extends: cu`). The reference
is the same deck as cu's: NSI's `NSI MASTER SLIDE DECK JULY2026 EXTERNAL.pptx` (a Google Slides
export, July 2026, from NSI via Ben; not committed). `../../cu/reference/report.md` is the inspect
tool's reading of it; `../../cu/reference/notes.md` holds the CU decisions this flavor inherits
(palette, roles, fonts, the brand site as the stricter authority). There is no
NSI brand guide: the deck and the CU rules are the guide.

## Files, from the deck's `ppt/media/`

| file | from | treatment |
|---|---|---|
| `logos/nsi-lockup.png` | `image10.png` (gold NSI, dark text; 1316x719, aspect 1.830) | as is |
| `logos/nsi-lockup-white.png` | `image4.png` (gold NSI, white text) | as is |
| `logos/nsi-lockup-black.png` | `image10.png` | every pixel black, alpha kept: a one-color stand-in for the gold fields, where the gold mark vanishes; swap for NSI's own one-color file when one arrives |
| `art/constellation.jpg` | `image1.jpeg` (4400x2475, the title layout's background) | scaled to 1920x1080 |
| `art/campus.jpg` | `image3.png` (1216x806, the band's campus photo) | as JPEG |
| `art/content-satellite.jpg` | `image71.jpg` (2002x1014, pre-faded ISS photo behind slides 12-23) | centre-cropped to 16:9, 1600x900, no further fading (the deck shows it as is) |
| `logos/rio-lockup.{svg,png,pdf}` | not the deck: RIO's own two-page overview, `colorado.edu/researchinnovation/sites/default/files/attached-files/rio_overview_071620.pdf` (InDesign), whose footer carries the Research & Innovation Office lockup as vector art | cut out with `pdftocairo -svg -x 375 -y 738` (page 1; the lettering is glyph outlines, the monogram four paths), boxed tightly (213.69 x 33.83 pt, aspect 6.317), the PDF's print gold `#CCB567` set to CU Gold `#CFB87C` and its dark to `#231F20`; PNG `rsvg-convert -h 240` for HTML and pptx, PDF `rsvg-convert -f pdf` for LaTeX. It replaced the deck's 1911x298 PNG (`image6.png`). nsi's own sign-off (NSI is an RIO center); cu's placeholder until cu took the CU Boulder lockup |
| `logos/rio-lockup-white.{svg,png,pdf}` | the same | the lettering's groups filled white, the monogram's paths untouched (gold with its dark outline), as the deck's white RIO (`image2.emf`) shows it on the black title |

## Mapping

- **Title** (deck slide 1): `title: {style: band}`, engine >= 3.1.0. Measured on the slide: the
  gold band from 0.276 to 0.724 of the height, the campus photo right of 0.62; the white RIO
  lockup bottom left at 0.115 of the height and the white NSI lockup bottom right at 0.198, both
  centred in the strip below the band (ours 0.11 and 0.19). The constellation picture is the
  field's `art.title`; the campus photo is `art.titlegraphic`, which a deck's `titlegraphic:`
  replaces. The deck's title is centred in the band with the date under it; ours keeps the
  engine's date / title / subtitle / rule / author column, left-aligned with the tab.
- **Content slides**: the NSI mark top left (`geometry.logo.corner: top-left`), 0.085 of the
  height (the deck's 0.135 would cross the title rule; it centres its title, ours stays left of
  the tab beside the mark), the RIO sign-off bottom left (nsi's own `signoff`, in cu's slot)
  and the page number bottom right (cu's), the satellite photo as `art.content`.
- **Closing** (deck slide 27): under the band style the closing slide wears the band's field and
  the title art (no `art.closing`), with the two white lockups in the strip (`marks.dark`, the
  band's field role); in pptx the template's `Closing` layout does the same.
- **Dividers and feature covers**: cu's gold field, with the one-color black NSI mark
  (`marks.primary`, engine 3.3.0; the band's black field wears `marks.dark`, white NSI and RIO
  lockups). The deck has neither.
- **pptx scheme**: inherited from cu (engine 3.3.0: a flavor keeps its parent's explicit
  `pptx.scheme` overrides, `hlink` accessible gold and `folHlink` sky blue; earlier engines
  dropped them and nsi restated them). Helvetica Neue where installed is cu's too
  (`installed-fonts`).

## Decided with Ben (2026-10-16)

Content background: the deck's satellite photo (over cu's Flatirons or none). The band's photo:
a livery default (the deck's campus shot) that a deck's `titlegraphic:` overrides. The closing
slide: the constellation field, as the deck's last slide.

## Follow-ups

- NSI's own one-color (black) lockup, to replace the recoloring; ideally vector files of the
  full-color stacked lockup too (NSI or RIO). No public vector exists: the website's is a
  375 px raster, and RIO's CNSI fact sheet (colorado.edu/researchinnovation/media/6004, March
  2025) carries only a raster one-color white horizontal lockup (1673x161), evidence that
  NSI uses one-color treatments. Re-typesetting the lockup is not an option: its Helvetica
  Neue Condensed light weight is not on macOS, and the brand forbids recreated lockups.
  Tracing the deck's 1316x719 PNG (shape for shape) would be the faithful fallback.
- The deck's "Helvetica Neue Extra Black Cond" headlines are not reproduced (cu's Heros Cn
  headings stand in).
- The rights of the deck's photos are NSI's; check before any use outside NSI decks.
- `title=light` is ignored under the band, with a warning, in every format (since the
  compositions, 2026-10-17; before, the pptx drew the white light cover while HTML and PDF kept
  the band). A light title is not an nsi look.

## Content titles (2026-10-17)

Ben compared a content slide with the master deck's slide 20 ("MSSC Secure Research
Infrastructure", Lindsay's): her NSI mark is larger (0.135 of the height, from 0.04), her titles
are centred beside it, with no gold tab and no hairline. nsi now says `frametitle: {align: center,
tab: false, rule: false}` and the mark's `top: 0.04, height: 0.135, inset: 0.015` (near the paper's edge,
as hers, not at the text margin; `geometry.logo.inset`, engine 3.8.0); the body starts below the
mark (0.197; `frametitle.body`, engine 3.8.0). Still different from hers, left as they are: the
titles' condensed face in HTML and PDF (Heros Condensed, the brand's headline rule; her deck sets
regular-width Helvetica Neue Bold, as the pptx does), her ~18 pt body with black bullets, and her
white footer band under the photo with a larger RIO lockup.

## Chart colors (2026-10-18)

Inherited from cu through `extends` (generated from CU Gold and Sky Blue); see
../cu/reference/notes.md.
