# nasa-ccp: onboarding notes

The decisions taken while making this livery (liveries/README.md, "Adding a livery"): where each color, font
and mark came from, what the template says, and what was left for later.

The reference is the Commercial Crew Program's PowerPoint template (`CCP_IAFM.pptx`, from Ben,
2026-10-23; not committed): 13.333 x 7.5 in, one master, six layouts (Title Slide1, Title and
Content, Title Subtitle and Content, Section Title Page, Two Content, Title Only), Helvetica
throughout. Its one sample slide is a talk's cover; nothing of the talk (its title, names, photo)
is used. `report.md` is `livery inspect`'s, with the slide's title taken out.

## Markings

The template's markings are its point, and the livery's defaults are its text verbatim, so a deck
that says nothing is over-marked (the safe failure) and a deck replaces each (docs/authoring.md):

- **The CUI banner** (`marking.banner`): "CUI//SP-EXPT/SP-PROPIN//DL ONLY" in 16 pt bold white on
  `#7030A0`, across the top of every slide, 0.495 in tall. A deck's `marking:` (or
  `marking: {banner: ...}`) sets its own category line; `marking: {banner: none}` drops it.
- **The legend** (`marking.legend`): "MAY CONTAIN PROPRIETARY AND/OR LIMITED RIGHTS DATA; NOT
  REVIEWED FOR EXPORT CONTROL" in 10 pt gray at every slide's foot (the master's footer
  placeholder, which pandoc never fills, so the engine draws it).
- **The cover notice** (`compositions.title.fineprint.text`): the CCtCap LIMITED RIGHTS NOTICE
  (DEC 2007) (DEVIATION), (a) to (c), at 8 pt in the template's box (right of center under the
  byline), and as its last paragraph the template's separate line "Distribution limited to
  Commercial Crew Transportation Capability (CCtCap) contract support personnel." The template
  sets the contract line "SpaceX NNK14MA74C / Boeing NNK14MA75C" in red, its cue to keep the one
  that applies; the default keeps both, and a deck's `fineprint:` replaces the whole notice.
- **Dropped**: the cover's export-control placeholder, an instruction to the author ("Placeholder
  for Export Control marking to be applied before sharing outside of the Government and/or
  International Partners. Based on source data, select appropriate marking from here."), whose
  link is <https://ccp.nasa.gov/Template_Library/Export_Control_and_Data_Rights_101_Excerpt.ppt>
  (NASA-internal). The author picks the marking there and sets it with `marking:`.

## Palette and roles

The theme's slots are Office's defaults (Calibri, `#5B9BD5` accents), used nowhere on the slides,
so the colors are the shapes' and the emblem's: the banner's purple `#7030A0`; the divider band's
slate `#41556B` (also the title bar's middle, `#415264` sampled); the emblem's red `#D21241`, navy
`#002E62` and gold `#F3AB10` (the Commons SVG's fills); nasa's gray `#5C5E62` for muted text
(the legend: the template's is `tx1` at 65 % luminance, `#595959`). Text is black on white, as
the template's. Primary is the slate (no field wears it: the cover, closing and dividers are white
art), accent the red, links the navy.

## Fonts

Helvetica, the template's only face, named in the pptx (Windows substitutes Arial, the same
metrics) and stood in for by TeX Gyre Heros in HTML and PDF (its design; GUST Font License, cu's
files). `installed-fonts` names Helvetica itself, which HTML uses on a Mac and PDF under
`fonts=brand`. No code face: the template has none.

## Marks

- **The NASA insignia**: nasa's vector (`liveries/nasa/logos/meatball.svg`, the Brand Center's,
  2024 colors), inherited. The template has it twice as bitmaps baked into its art: in the title
  bar's JPEG (1280 x 90) and in the cover banner (2000 x 364). `reference/ccp_art.py` paints both
  out; the cover's comes back as the composition's mark (vector in every format), the bar's is
  drawn back into the content and divider art from the SVG at the art's 3840 px. The engine draws
  one mark per content slide (the emblem's corner); a second, vector one in the other corner is
  a follow-up (design/engine-and-liveries.md, "one mark per field").
- **The CCP emblem and lockup**: NASA's own vectors from the CCP Program Collector Card (2014), on
  Wikimedia Commons, public domain in the US (PD-USGov), their use restricted like every NASA
  insignia (14 CFR 1221):
  - `logos/ccp-emblem.svg`: `File:NASA_Commercial_Crew_Program_logo_(cropped).svg`, the emblem
    alone, on the title bar's left end of content slides and dividers (the template's 131 x 136
    PNG, stretched);
  - `logos/ccp-lockup.svg`: `File:NASA_Commercial_Crew_Program_logo.svg`, the emblem over
    COMMERCIAL CREW PROGRAM, on the cover and closing (the template's 158 x 195 PNG, squashed to
    0.81; the vector's own aspect is 0.61).
  `ccp_art.py` fetches them once and renders a PNG (HTML, pptx) and a PDF (beamer: still vector).
- No agency name at the foot (`signoff: null` drops nasa's).

## Geometry and slide styles

- **Content slides**: the CUI banner (0 to 0.066), the title bar under it (0.065 to 0.19, art),
  the emblem at its left, the title white, bold, 28 pt and centered *on the slide* in the bar
  (`frametitle.symmetric`); no tab, no hairline. The body runs from 0.20 to 0.955, above the
  legend; the page number is the template's, bottom right, 12 pt.
- **Cover**: white, the banner (0.065 to 0.389) with the insignia at its right end, the title
  (32 pt bold) and byline centered in black under it as the template's, the lockup bottom left,
  the notice right of center.
- **Dividers**: the template's Section Title Page: the bar, then a band slate at its top fading to
  white by its middle, the heading 28 pt black, centered at the band's foot. No "SECTION n".
- **Closing**: the template has none; the cover's art, marks and a centered headline.
- **Type**: body 16 on the 13.333 in canvas (the portable share, as nasa-jsc-eg's); the template's
  master says 20 bold at level 1 and 18 below, which overflows the decks that move between
  liveries. Level 1 is not bold here. The bullets are the template's disc, dash and square (its
  third level's § is a Wingdings square); its fourth "o" and fifth "•" take the square.

## Chart colors

nasa's (the Horizon Design System's), inherited: the template has no chart colors.
