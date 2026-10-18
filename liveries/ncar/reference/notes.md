# Onboarding notes: ncar

The reference deck is UCAR Communications' `NSF NCAR-Template.pptx` (April 2026), in the brand's
Drive folder: https://docs.google.com/presentation/d/1S2-GIzbDFtDn0h8aA_aFoOHeXGaypiUk (shared drive
`0AGsogMH8E27yUk9PVA`, folder `1aXl3R3WEJea8DHim1f8v3joQrC6jzEL5`). It is not committed:
download it beside this file as `reference/ncar.pptx` to rerun `livery_inspect.py`.

`report.md` is the tool's reading of it. The layout mapping and the template decisions go
here as they are made (design section 6, "the human steps").

## Chart colors (2026-10-18)

`livery.yml` `charts:` (design/charts-and-plots.md):

- **Series and diverging scale: pinned from sam-queries** (`benkirk/sam-queries` 6e0f00d,
  `src/webapp/dashboards/charts/theme.py` `FAIR_SHARE_LIGHT`/`_DARK`, and the calendar burn steps
  `--data-burn-0..4` of `src/webapp/static/css/variables.css`), validated there with the dataviz
  checks for the NCAR brand. The set adds a pink, a purple and a darker gold because the brand
  colors alone fail the checks: gold and orange too light and too close, navy too dark, teal gray.
  Every check passes as given, except the dark set's first three slots taken all-pairs, at
  dE 12.8 (blue against teal). That is reported as a warning: a pinned palette is the authority.
- **Ramps: the UCAR web theme's tint ladders**, base, -33 and -66 (`NCAR/koru-jekyll` 55ce7c3,
  `assets/koru-base/scss/_variables.scss`), light to dark. The yellow ladder is rebuilt on the
  2026 guide's `#FFDD31`: koru's is on the older `#FDD509`, and its steps fit an OKLab mix toward
  white at 0.575 and 0.26, which gives `#FFF2B9`, `#FFE77D`. koru also makes `#00818F` UCAR's base
  with `#00A2B4` its tint, the reverse of the 2026 guide; the steps are kept as published.
- **For comparison, the generator alone** (no pins, no ramps) picks
  `#0057C2 #CE8200 #009BD7 #AA9100 #008D9D #883500 #881E70 #C14054` on white: the brand blue,
  orange, light blue, yellow and teal moved into the mark band (orange, yellow and teal darkened
  for 3:1), then a brown, a plum and a rose.

## Color fact check (2026-10-18)

The palette is the 2026 guide's (pp. 17-21): NCAR/music-box-interactive issue #588 quotes the same
ten colors to the digit. The official template's theme differs by one in a channel (`#003479`,
`#41C0FF`, `#FFDD30`, `#00A2B3`, `#34E1F3`), a Google Slides rounding artifact (its layouts are
"Google Shape"s), and its lt2 `#E8E8E8` is a tool default (CU's NSI deck has it too); both are left
alone. Open, for the final polish with the guide in hand: the web themes (koru, and sam-queries
citing NCAR's private "Unity") carry vermilion `#FF1F1F` ("NSF NCAR defining accent"), grays
`#97999B` and `#BBBCBC`, and the older yellow `#FDD509`. Does the 2026 guide list the vermilion
and the grays?
