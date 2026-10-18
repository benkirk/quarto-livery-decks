# Plots in the livery

`plots.qmd` is the cookbook for Python plots in a framework deck: matplotlib and seaborn in the
livery's chart colors, its font and the slide's own type sizes, in all three formats, with no
styling code. The design and the color science are in
[`design/charts-and-plots.md`](../../design/charts-and-plots.md); the framework README's "Plots
and chart colors" has the summary.

![The plots deck under every livery: lines, hue families, a heatmap, a dark slide](screenshots/liveries.png)

## A deck with plots

````markdown
---
engine: jupyter
jupyter: python3
---

```{python}
#| include: false
import livery_mpl                  # the livery's fonts, colormaps and helpers
import matplotlib.pyplot as plt
```

## Throughput by month

```{python}
fig, ax = plt.subplots()           # the slide's content area: labels at the body size
ax.plot(months, jobs)              # the livery's first series color
plt.show()
```
````

`make pptx|html|pdf` does the rest. `Make.common` exports the livery's `build/livery.mplstyle`
as `MATPLOTLIBRC`, puts `livery_mpl` on `PYTHONPATH`, and gives the deck the content area as its
figure size, so a plot drawn at the default size has slide-sized text. The engine shows each
figure at the slide's scale in HTML and PDF, and pandoc does in pptx: plot text measures the
same as body text in every format.

## What the helper offers

| | |
|---|---|
| `livery_mpl.colors` | the categorical slots of the livery's mode, in order (the color cycle) |
| `livery_mpl.families` | up to 8 hues by 3 tints, for a large map where the hue names the group and the tint the member (the stacked-area slide) |
| `livery_mpl.status`, `.muted` | `good`, `warning`, `serious`, `critical`; the color for "Other" |
| `livery_mpl.figsize("half")` | one of two columns; `figsize("full", height=0.6)` a wide, short plot |
| `livery_mpl.shade_family(c, n)` | `n` tints of `c` toward the surface, as the families are built |
| `with livery_mpl.dark():` | a `{.brand-dark}` slide: the dark chrome and colors where that slide is dark (HTML, a dark livery) |
| colormaps | `livery` (the default, the livery's own map), `livery_r`, `livery_div` (diverging), `livery_seq_<ramp>`, each with a `_dark` twin |

What breaks it: `sns.set_theme()` or `plt.style.use(...)` (they replace the livery's style), a
hand-picked `figsize` (it changes the text size), a colormap by name such as `viridis`, more
than eight series (fold the rest into "Other").

## The liveries' chart colors

![Each livery's series colors, default map and diverging scale, light and dark](screenshots/palettes.png)

Each row is one livery on its light or dark surface: the categorical slots (at most eight), the
default color map, the diverging scale. Where they come from (each livery's
`reference/notes.md`, "Chart colors"):

- **ncar, ucar** (and their flavors ucp, ncarucar): the series are sam-queries' validated sets
  for the NCAR brand. ucar's leads with UCAR Aqua. The maps run through the brand's own blues,
  Light Blue's tints to Space (ucar: along UCAR Aqua). The ramps are the UCAR web theme's tint
  ladders, re-based on the 2026 guide.
- **cu, nsi**: CU publishes no chart palette, so the engine generates one from CU Gold and Sky
  Blue, with the campus in it: the red tile roofs (`#9C3F29`, sampled from the campus photo) as
  the third color and a sage green the fourth, a campus map of Light Gold, the Flatirons' sandstone and the tile in sun and
  shade, and a diverging scale from the sky to the roofs.
- **nasa, nasa-dark**: NASA's own dataviz palette from the Horizon Design System, verbatim.

The colors pass the dataviz checks (lightness band, chroma, separation under color blindness,
contrast on the surface). A palette the engine generates must pass. A brand's published palette
is kept as given, and its shortfalls are reported as warnings. `python3
_extensions/engine/livery.py check liveries/<name> --swatch DIR` prints the checks and draws a
livery's full contact sheet.

## Outside the decks

`make charts-zip LIVERY=<name>` (any deck directory) writes `<name>-charts.zip`: the style, the
helper, `livery.json`, the fonts and their licenses, and the contact sheet. Unzip it beside a
script, `import livery_mpl`, and its plots wear the livery. Every release attaches one per
livery: `releases/latest/download/<name>-charts.zip`.

## Rebuilding the images

`make gallery` here writes `screenshots/liveries.png` and `palettes.png` (committed). Rerun it
after a livery's charts change, look at the images, and commit them.
