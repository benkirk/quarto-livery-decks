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
  lines, the lab photo behind the arc, the division patch top left. It is also
  `art.titlegraphic`, drawn full-bleed (`compositions.title-photo.photo`), so a deck's own
  `titlegraphic:` replaces the whole cover art, and nasa's Earth limb is never drawn.
- `art/closing.jpg` (EG - Closing): the starfield, the division patch centered, the rule between
  the agency name and the insignia. Section slides wear it too: the template's divider ("Backup")
  is its closing layout.

The marks, by field role (`marks`):

| field | slides | mark | sign-off |
|---|---|---|---|
| `background` | content | the full-color insignia (nasa's) | `eg-footer`, the division bar |
| `dark` | cover | the insignia | `group-patch`, beside the division's |
| `surface` | closing, sections | the insignia | `nasa-name-2line` |

The closing and section fields are `surface` only so that they get their own marks; the art
covers the field. `nasa-name-2line` is the agency name in two right-aligned lines of Liberation
Sans Bold (Arial's metrics) as outlines, built by `eg_art.py`. The division bar and the patches are
the template's PNGs.

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

and `make livery LIVERY=nasa-jsc-eg-<group>`, twice the first time (a new flavor's first build
reads its parent's template, so its first check finds `build/` stale; #125). The patch fills its box's height (0.344 of the
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

**The cover title is black on the yellow band** (Ben, 2026-10-20, to assess): the template sets
it white, 1.4:1 on the yellow. The column is one stack in one color, so the byline (date,
subtitle, author) goes on the band with it, at 18/16/12 pt, and a two-line title is tight. The
template's white title with its byline below the band on black is one edit: the title and
title-photo columns from y 0.426, `anchor: top`, `role: foreground`.

## Chart colors

nasa-dark's, NASA's Horizon Design System palette (`../nasa/reference/notes.md`), with one change
on dark slides (Ben, 2026-10-21): the template's yellow `#FCDB00` takes the HDS orange's place,
as the third series and the second of every small set. The orange moves to the tenth slot, in
place of HDS's own yellow, so the palette holds one yellow. The checks give the same warnings as
nasa-dark (the yellow, like the orange, is lighter than the band). Light slides keep HDS's
palette: the yellow reads 1.4:1 on white. seaborn's bars desaturate it toward mustard, and in a
stacked area the yellow family's darker shades go olive.

## Type and fonts

Arial throughout in the template; Liberation Sans stands in for it (Arial's metrics, so lines
break where PowerPoint breaks them; SIL OFL 1.1, liberation-fonts 2.1.5), and Liberation Mono for
its Courier New code. The pptx names Arial (`pptx.typeface`), HTML prefers an installed Arial
(`installed-fonts`). Sizes are the template's on its canvas: titles 32, the cover title and the
closing 36. The body is 16 with levels 16/15/13/12/11, the share every livery takes, so a deck
moves between liveries without overflowing; the template's master says 20 for every level, and
its own sample slides shrink to fit.

## What the engine cannot do yet

Onboarding this livery turned up engine improvements, filed as #124, and bugs, filed as #125.
The workarounds this livery uses until they land:

- **Cover byline** (#124): the whole stack sits on the band, in black, at smaller sizes.
- **Closing and divider marks** (#124): their fields take the `surface` role, which the art hides,
  so they wear the agency name while the cover wears the group patch.
- **Inherited title photo** (#124): the cover art doubles as `art.titlegraphic`, full-bleed, so a
  deck's own `titlegraphic:` replaces the whole cover. Its field box is `[0, 0, 0.001, 0.001]`:
  `null` crashes the pptx and an empty box `make measure` (#125).
- **Divider eyebrow** (#125): a muted "SECTION n" stays, since `eyebrow: null` breaks the PDF.
- **Bullets, centered closing text, the column rule, the light cover, the marking line, Courier
  New in the pptx** (#124): not reproduced.
- **A group's flavor**: run `make livery` twice the first time (#125).

`make measure` reports its boxes "over" on the cover, closing and dividers: the measurer reads the
art's own ink (the starfield, the patches, the rule beside the insignia) as content. The deltas are
the same in all three formats, which is what it checks; the pptx sets the closing and divider text
a little lower than HTML and PDF.

## The template's other layouts

The template has eleven layouts; pandoc picks seven by name, and the engine's template adds Closing
and Title Slide (light). How the rest map:

- **Title & Content, Title & 2 Column, Title Only, Closing, Title Slide**: the engine's own.
- **Title & Image**: a figure slide (one picture, pandoc fits it to the content area) or `{.full}`.
- **Title, Content & Image**: two columns, text and picture, but the pptx can't give the text
  two-thirds: pandoc ignores `.column` widths in pptx (equal halves; HTML and PDF honor them; #124).
- **Title & 3 Column, 3 Image Column, 4 Quadrants**: nothing reaches them, and **pandoc 3.8.3
  drops every column after the second in pptx, silently** (HTML and PDF lay out any number; #125).
  These are the layouts worth an engine step: `slide_layout.py` re-pointing a three-column slide to
  a three-content layout, as it already re-points Closing (#124).
