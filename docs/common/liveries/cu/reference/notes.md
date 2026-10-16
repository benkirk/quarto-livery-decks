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
blobs come from PowerPoint).

## Lockups

The deck carries unit lockups only (NSI; the Research & Innovation Office). The plain CU Boulder
lockup lives in the lockup library (ucomm-exten2.colorado.edu, CU login). Until Ben supplies it,
the RIO lockup from the deck is the placeholder (`logos/cu-rio-lockup.png`, dark text for light
backgrounds; `cu-rio-lockup-white.png` is the same PNG recolored white by alpha; the deck's own
white version is an EMF). The brand wants the lockup as a "sign off" at the bottom, so it is the
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

The `nsi` flavor (`extends: cu`: the NSI marks, `image4/7/8.png` in the deck), the band title
style, Heros Condensed headings, pptx font embedding, the plain CU lockup, `livery_check.py`.
