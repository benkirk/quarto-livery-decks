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
| `logos/rio-lockup.png` | `image6.png` (the Research & Innovation Office lockup, dark text; 1911x298, aspect 6.413) | as is; it was cu's placeholder sign-off until cu took the CU Boulder lockup, and is nsi's own sign-off (NSI is an RIO center) |
| `logos/rio-lockup-white.png` | `image6.png` | the text right of the CU monogram recolored white, the monogram kept (gold with its outline), as the deck's white RIO (`image2.emf`, a vector LibreOffice cannot convert with transparency) shows it on the black title |

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
  the title art (no `art.closing`), with the two white lockups in the strip; in pptx the
  template's `Closing` layout does the same.
- **Dividers and feature covers**: cu's gold field, with the one-color black NSI mark
  (`logo.medium.dark`). The deck has neither.
- **pptx scheme**: a flavor's scheme follows its own roles, so cu's link-slot overrides
  (`hlink` accessible gold, `folHlink` sky blue) are restated.

## Decided with Ben (2026-10-16)

Content background: the deck's satellite photo (over cu's Flatirons or none). The band's photo:
a livery default (the deck's campus shot) that a deck's `titlegraphic:` overrides. The closing
slide: the constellation field, as the deck's last slide.

## Follow-ups

- NSI's own one-color (black) lockup, to replace the recoloring.
- The deck's "Helvetica Neue Extra Black Cond" headlines are not reproduced (cu's Heros Cn
  headings stand in).
- The rights of the deck's photos are NSI's; check before any use outside NSI decks.
