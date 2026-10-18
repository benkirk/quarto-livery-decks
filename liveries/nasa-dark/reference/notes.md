# Onboarding notes: nasa-dark

The dark variant of `nasa` (`extends: nasa`; read `../nasa/reference/notes.md` first): content
slides on black, as the NASA Science public-engagement deck sets them. Fonts, marks, type,
geometry and the title photo are nasa's.

## Roles

`_brand.yml` sets `foreground: white`, `background: black` (the reference deck's black;
`livery.json` then says `"mode": "dark"`, which the engine and the framework read). The brand's
blues and red are too dark for small text on black (NASA Blue 2.0:1, NASA Red 4.3:1), so the
small-text roles are lifted: `primary-contrast` `light-blue` `#6E9BFF` (7.8:1), `highlight` the
reference deck's own cyan `#00B0F0` (8.5:1), `muted` `steel` `#A3A7AD` (8.7:1). NASA Red stays
the accent (tabs, bullets, marks of emphasis); code alerts get `light-red` `#FF4458` through
`blends: alert-text` (the default blend darkens the accent to 2.0:1). `surface` is `graphite`
`#1C2026` (code, table bands), and code text has its own role, `code-text: frost` `#E6E8EB`,
because the `dark` role stays black for the bars and fields (engine >= 3.8.0). The pptx link
slots are restated (`hlink: light-blue`, `folHlink: cyan`).

## Fields and marks

- The cover and closing are on black (`compositions: {title, closing: {field, mark, signoff:
  {role: dark}}}`), with the full-color insignia (the brand allows it on black) and the white
  agency name, as the reference deck's cover and closing. Dividers keep nasa's NASA Blue with the
  white-rule insignia.
- Content slides wear the full-color insignia and the white name (`marks.background`).
- The photo slide's bar is the black `dark` role, so its title text is the foreground
  (`compositions.feature.column.role`).

## Art

`art.content` is `art/starfield.jpg`: the Hubble eXtreme Deep Field ("Hubble Goes to the eXtreme
to Assemble Farthest-Ever View of the Universe", images.nasa.gov `GSFC_20171208_Archive_e001651`;
NASA, ESA, G. Illingworth et al.), cropped to 16:9 at 1920 x 1080, saturation 70%, blended 72%
toward black (mean brightness 3%), so text reads over it at full contrast.

## Diagrams

Mermaid and Graphviz draw dark on white. Under a dark livery the framework's
`diagram-dark.lua` turns each diagram Quarto bakes for pptx and PDF (mermaid and dot cells) into
the dark: HLS lightness flipped with hue and saturation kept, white to the background, black to
the foreground (`utils/diagram_dark.py`). HTML draws mermaid live in the roles and inlines
Graphviz as SVG, which the engine's `livery.css` flips the same way (a CSS filter).

## Known limits

- The pptx theme slots follow the roles, so "Dark 1" (`dk1`) holds white and "Light 1" black.
  The deck is consistent, but PowerPoint's built-in table, chart and SmartArt styles assume a
  light `lt1`. Swapping the `clrMap` instead (PowerPoint's own way of a dark theme) needs engine
  design: a follow-up.

## Chart colors (2026-10-18)

Inherited from nasa (HDS's dataviz palette, its dark set on this livery's black); see
../nasa/reference/notes.md. The fact check found that `cyan` `#00B0F0`, taken from the NASA
Science reference deck for `highlight`, is Office's standard "Light Blue" swatch, not a NASA
color; it stays until the screen-color decision (see nasa's notes).
