# Onboarding notes: nasa

NASA general, for external communication, in two liveries: `nasa` (light: content on white,
NASA Blue fields) and `nasa-dark` (content on black; see its own notes). Program flavors
(Artemis, Commercial Crew, ISS) are to come and stand alone; they need not extend this.

NASA publishes no slide template. The authorities are the Brand Center's guidelines
(https://www.nasa.gov/nasa-brand-center/brand-guidelines/, read 2026-10-17) and, for the look of
a NASA deck, the NASA Science public-engagement deck ("Collection of Interactive PowerPoint
Slides to be Used in Public Engagement", NASA/JPL-Caltech, 2021;
https://science.nasa.gov/resource/collection-of-interactive-powerpoint-slides-to-be-used-in-public-engagement/).
The deck is not committed: download its PPTX beside this file as `reference/nasa.pptx` to rerun
`livery_inspect.py`. `report.md` is the tool's reading of it. Ben's brief (2026-10-17): we may take
liberties where the guidelines are silent.

## The reference deck

10 x 5.625 in (16:9), 28 slides, one master, background `tx1` (black): white bold titles top left
(20-24 pt) with a smaller "– subtitle" run, a small full-color insignia top right, the site's
address bottom right, a closing slide that is the insignia large and centered on black. Arial
throughout (55 Helvetica Roman on the cover). Its theme slots are Office-like (accent3 `#0B3D91`
and accent4 `#E31937` are the old NASA blue and red); its most used color is a cyan, `#00B0F0`.
Its layouts are photo-heavy (cover with a square image, title-only) and pandoc can reach none of
them, so the template is generated from the data, like ncar's and cu's, not mapped.

## Roles and palette

The 2024 insignia color guide gives NASA Blue `#0032A0` (PMS 286) and NASA Red `#E4002B` (PMS
185); the older `#0B3D91` / `#FC3D21` still quoted elsewhere are superseded. The guidelines name
PMS 877 (silver) as a preferred insignia background; `silver` is a flat stand-in (`#8A8D8F`).
The rest is ours: `carbon` `#1C1C1C` text, `gray` `#5C5E62` muted (6.5:1 on white), `light-gray`
`#F0F1F3` surface, `sky` `#0B6BCB` a second blue for small text (5.3:1), `yellow` `#FFC72C` for
caution slides only. Primary NASA Blue carries the fields with white text (10.7:1); the accent
(tabs, bullets) is NASA Red (4.8:1 on white).

## Type

Fonts: the guidelines recommend Helvetica and Garamond for print and, for digital work, the
Horizon Design System's three families: Inter for headings, Public Sans for body, DM Mono for
numbers and labels. Ben chose the hybrid: the Horizon faces for every slide's text (all SIL
OFL, bundled in `fonts/` from rsms/inter v4.1, uswds/public-sans v2.001 and google/fonts'
dmmono), Helvetica only inside the agency-name artwork, where the brand requires it. DM Mono is
the code face (`typography.monospace`, engine >= 3.8.0); it advances 0.6 em, as HTML's monospace
does, so the PDF sets it at 1.0. The pptx names Public Sans (body) and Inter (headings) and DM
Mono for code (pandoc's `monofont`); it embeds none of them until PowerPoint has made the
`fntdata` blobs once (`embed_fonts.py`), so a machine without them substitutes.

Sizes, in points on the reference deck's 10 x 5.625 in canvas: body 12, levels 12/11/10/9/8 (the
share of the slide ncar's and cu's bodies take, so a deck moves between liveries without
trimming; 14 and 13 pushed the sample deck's dense slides into the sign-off in the PDF), slide
titles 22 (the deck's 20-24), in-body heads 16, code 10 (a step under the body, as ncar's), the
cover title 32 (its 36), dividers and the closing 32.

## Marks

- **Insignia (meatball)**: from the Brand Center's own vector, `insignia-spherecentered.svg`
  (its middle panel, a self-contained insignia group), recolored to the 2024 Blue and Red; the
  file's own fills (`#003e96`, `#ff1500`) are off-guide. `meatball.svg` is the full-color
  version (white, black, gray, silver backgrounds and photographs; never reversed, never with a
  white rule). `meatball-rule.svg` is the guide's "one-color with white rule" version, in NASA
  Blue with a white rule and a pale swoosh, for the NASA Blue fields, where the full-color
  sphere would vanish.
- **Agency name**: "National Aeronautics and Space Administration" set in Helvetica Neue Medium
  (the Mac's; the guide's lockups use a Helvetica), converted to outlines so no font ships:
  `nasa-name.svg` (black) and `nasa-name-white.svg`. It is the livery's `signoff`, bottom left.
- **Together**: the insignia top right and the agency name bottom left on every slide are the
  guidelines' preferred identifier ("insignia aligned to the upper right, agency name aligned
  left, on one line"). The guide's two-line lockup (insignia, rule, name) is buildable by the
  same script but unused: the engine draws one mark per field.
- Clear space: the guide asks 1N (the height of the "N" in NASA) round the sphere; the mark's
  top 0.045 and its 0.075 height leave it on content slides. Minimum size: 37 px on screen (the
  content mark is 68 px of a 900 px slide).
- `nasa_marks.py` (here) rebuilds all of them: `python3 -I nasa_marks.py
  <insignia-spherecentered.svg> <outdir>`, with rsvg-convert and ImageMagick.
- The guidelines say the insignia and logotype "are not in the public domain" and restrict
  their use; questions go to agency-brand@mail.nasa.gov. These liveries are for NASA's own
  presentations. The worm (logotype) is not used.

## Art

No wave curves: fields end in a straight edge. `art.titlegraphic` (the title photo for decks that
set none) is `art/earth-limb.jpg`, the Earth's limb from the ISS (Expedition 42,
`iss042e340851`, NASA JSC, images.nasa.gov), resized to 1600 px. NASA-produced imagery is not
copyrighted; the credit is NASA. Ben may swap it from the candidates on the onboarding contact
sheet (Earthrise `as08-14-2383`, the Blue Marble `as17-148-22727`, an aurora limb
`iss058e005282`).

## Known limits

- pptx math is OMML, which LibreOffice cannot draw (any livery); check it in PowerPoint.
- Templates have to be opened once in PowerPoint to confirm there is no "Repair?" prompt.

## Chart colors (2026-10-18)

`livery.yml` `charts:` is NASA's own chart palette, verbatim: the Horizon Design System's dataviz
tokens (`nasa/hds-core` f036e73, `tokens.json` `dataviz.color`, CC0): the 12 categorical colors
for light and for dark, the curated sets for 2 to 5 series (option 1 of four each), and the 11
ramps (red, orange, yellow, gold, lime, green, aqua, slate, blue, purple, magenta) in 10 steps.
HDS says the brand red and blue are "never for dataviz", so they are not anchors. HDS publishes no
diverging scale; its poles here are HDS blue 70 `#1159CD` and red 70 `#C41D14`.

The dataviz checks warn on the published colors (reported, not fixed): the slates and the gold are
desaturated by design, red beside orange is dE 13.4 for normal vision, five light colors are below
3:1 on white, and several dark ones sit above the dark band. The curated sets are the safer picks
for a few series.

## Color fact check (2026-10-18)

NASA Blue and NASA Red are print colors: the insignia is PMS 286 and PMS 185 (NASA's insignia
guidelines for grantees), and `#0032A0`/`#E4002B` are those Pantones' standard sRGB values.
**Confirmed 2026-10-18** on the Brand Center's Brand Guidelines page (updated 2026-02-27), in its
image "NASA Full-Color Insignia Colors" (`wp-content/uploads/2023/07/nasa-insignia-colorguide.png`):
NASA Blue RGB 0 50 160, `#0032A0`, CMYK 100/80/0/12, PMS 286; NASA Red RGB 228 0 43, `#E4002B`,
CMYK 0/100/100/0, PMS 185. One set for every medium ("PANTONE, CMYK or the RGB using the color
formulas given above"), no separate screen hex; `#0B3D91`/`#FC3D21` appear nowhere on the page.
"2024" is only in another image's file name, so cite it as the Brand Center's insignia colors. NASA's
screen colors are different: HDS `nasa-blue` `#1C67E3` (tint `#288BFF`, shade `#0B3D91`),
`nasa-red` `#F64137` (tint `#FF5C52`, shade `#B60109`), `international-orange` `#EA6F24`, and a
carbon neutral ramp with `carbon-90` `#17171B` as the dark background. carbon, gray, silver,
light-gray, sky and yellow here are ours. Whether the nasa liveries move to the HDS screen colors
is decided later (an issue carries this).
