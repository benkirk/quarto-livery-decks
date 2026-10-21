# Onboarding notes: nasa-jsc-eg

The NASA Johnson Space Center Aeroscience and Flight Mechanics Division (EG) template, a flavor
of `nasa-dark` (`extends: nasa-dark`; read `../nasa/reference/notes.md` and
`../nasa-dark/reference/notes.md` first). The source is the division's PowerPoint template
(13.33 x 7.5 in, 11 layouts, a sample talk), read in `report.md`. The deck itself stays out of
git, and so does everything of the sample talk's: its titles, text and content images.

## Art and marks

The template draws its furniture at fixed places, so the furniture is art, rendered from the
template's own layouts by `eg_art.py` (python-pptx strips the talk's slides, the placeholders and
the marks the engine draws itself; LibreOffice renders; 1920 x 1080 JPEG):

- `art/content.jpg` (EG - Title & Content): the starfield, the white 15%-to-0% band behind the
  title, the soft dark glow behind the insignia, the short rule left of the page number. The title
  hairline is the engine's (`frametitle.rule`, `blends.rule`), not the art's.
- `art/title.jpg` (EG - Title Slide): the starfield, the orange-to-yellow band with its contour
  lines, the lab photo behind the arc, the division patch top left: the cover's art (the `title`
  composition). `art.titlegraphic` is `null`, unsetting nasa's Earth limb; a deck's own
  `titlegraphic:` is drawn full-bleed with no field over it (`compositions.title-photo`: the
  photo's box the slide, `field: null`), replacing the whole cover art.
- `art/closing.jpg` (EG - Closing): the starfield, the division patch centered, the rule between
  the agency name and the insignia. Section slides wear it too: the template's divider ("Backup")
  is its closing layout.

The marks: content slides by their field role (`marks`), the composed slides by name
(`compositions.<name>.signoff.image`):

| slides | field | mark | sign-off |
|---|---|---|---|
| content | `background` | the full-color insignia (nasa's) | `eg-footer`, the division bar |
| cover (and its light variant) | `dark` | the insignia | `group-patch`, beside the division's (`image:`) |
| closing, sections | `dark` | the insignia | `nasa-name-2line` (`image:`) |

The art covers the fields. `nasa-name-2line` is the agency name in two right-aligned lines of
Liberation Sans Bold (Arial's metrics) as outlines, built by `eg_art.py`. The division bar and the
patches are the template's PNGs.

## The group patch: swapping in another group's

The cover's second patch is the Flight Sciences Lab's, as in the template's sample; it is a mark
(`group-patch`), not art, so another group in the division swaps it without rebuilding anything:

```sh
livery new liveries/nasa-jsc-eg-<group> --extends nasa-jsc-eg
```

then, in that livery's `_brand.yml`:

```yaml
logo:
  images:
    group-patch:
      path: logos/group-patch.png   # the group's patch, RGB PNG, with logos/group-patch.pdf beside it
```

and `make livery LIVERY=nasa-jsc-eg-<group>`. The patch fills its box's height (0.344 of the
slide) at its own aspect. A group with no patch of its own sets `compositions: {title:
{signoff: null}}` instead.

## Palette and roles

The template's theme names the colors (`_brand.yml`, `eg-*`): accent1 yellow `#FCDB00` (the
division bar, the cover band), accent2 navy `#061F5F` (`primary`: table headers, under white),
accent3 red `#F93A1D` (`accent`), accent4 orange `#FEA20B` (`warning`), accent5 blue `#297DE0`
(`primary-contrast`, links: 5.0:1 on black), dk2 gray `#959595` (`muted`, 7.4:1), the yellow as
`highlight` (code strings, tips). Black and white, `surface` graphite and `code-text` frost are
nasa-dark's. The pptx link slots are the template's: `hlink` the blue, `folHlink` `#BD92DE`.

**Body text is pure white**, the template's (Ben, 2026-10-20, after a side-by-side with `#E1E1E1`,
the template's lt2, and `#EBEBEB`). It is one line, `roles.foreground`; the content titles follow
it too (the engine has no separate title color), so a fainter body dims the titles with it.

**The cover**: the title and subtitle black on the yellow band (Ben, 2026-10-20, to assess; the
template sets the title white, 1.4:1 on the yellow), the author, institute and date white below
it, where the template lists its byline (`compositions.title.byline`, its own box from y 0.68).
The title alone is the template's white with one edit: the column's `role: foreground`.

## Chart colors

nasa-dark's, NASA's Horizon Design System palette (`../nasa/reference/notes.md`), with one change
on dark slides (Ben, 2026-10-21): the template's yellow `#FCDB00` takes the HDS orange's place,
as the third series and the second of every small set. The orange moves to the tenth slot, in
place of HDS's own yellow, so the palette holds one yellow. The checks give the same warnings as
nasa-dark (the yellow, like the orange, is lighter than the band). Light slides keep HDS's
palette: the yellow reads 1.4:1 on white. seaborn's bars desaturate it toward mustard, and in a
stacked area the yellow family's darker shades go olive.

## Marking strip

The template has a marking placeholder on every layout, a strip at the top edge ("Click to edit
CUI Marking": x 0.111, width 0.777, y 0.004, height 0.028, centered, no fill). `marking:` draws it
in every format, white bold on the cover photo's regolith violet `#6840F0` so it stands out (Ben,
2026-10-21: `fill: eg-violet`, `color: white`, `bold: true`, each its own knob; 5.9:1), with demo
text as the livery's default: "This
presentation contains no sensitive information; but if it did, here's where the disclaimer would
go". A deck sets its own (`marking: "CUI"`), or `marking: none`. The template's 16 pt does not fit
the strip's height on one line; 13 does (`type.marking`).

## Type and fonts

Arial throughout in the template; Liberation Sans stands in for it (Arial's metrics, so lines
break where PowerPoint breaks them; SIL OFL 1.1, liberation-fonts 2.1.5), and Liberation Mono for
its Courier New code. The pptx names Arial (`pptx.typeface`) and Courier New for code
(`pptx.code-typeface`, installed with PowerPoint), HTML prefers an installed Arial
(`installed-fonts`). Sizes are the template's on its canvas: titles 32, the cover title and the
closing 36. The body is 16 with levels 16/15/13/12/11, the share every livery takes, so a deck
moves between liveries without overflowing; the template's master says 20 for every level, and
its own sample slides shrink to fit.

## What the engine cannot do yet

Onboarding this livery filed engine improvements (#124) and bugs (#125). Two sprints added what it
uses now: the cover's byline, centered closing and divider text (`column.align`), dividers without
a label, `field: null` on a photo cover, the marking strip; then marks by image per composition,
`art.titlegraphic: null`, the template's square, dash and dot bullets (`bullets:`), Courier New for
the pptx's code (`pptx.code-typeface`), the hairline between columns (`boxes.columns.rule`),
column widths in the pptx and three or more columns there, and the template's card look
(`boxes.card`: the surface fill, an eg-green outline on a picked card). Still open:

- **The light cover's art**: the engine takes `art.title-light` now; rendering the template's
  "EG - Title Slide- Light" with `eg_art.py` needs the reference deck (on Ben's laptop).
- **Pictures and tables in cards and in slides of three or more columns** are not drawn in their
  column in the pptx yet (the render warns).

`make measure` reports its boxes "over" on the cover, closing and dividers: the measurer reads the
art's own ink (the starfield, the patches, the rule beside the insignia) as content. The deltas are
the same in all three formats, which is what it checks.

## The template's other layouts

The template has eleven layouts; pandoc picks seven by name, and the engine's template adds Closing
and Title Slide (light). How the rest map:

- **Title & Content, Title & 2 Column, Title Only, Closing, Title Slide**: the engine's own.
- **Title & Image**: a figure slide (one picture, pandoc fits it to the content area) or `{.full}`.
- **Title, Content & Image**: two columns, text and picture, `width="67%"` on the text's: the
  engine sets the pptx's columns at their widths, as HTML and PDF.
- **Title & 3 Column, 3 Image Column, 4 Quadrants**: nothing reaches the layouts; three or four
  `.column`s are drawn as text boxes at their widths (`{.wide}` for four), but not yet with a
  picture in a column.
