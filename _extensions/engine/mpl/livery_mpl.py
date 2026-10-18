"""Plots in the livery: matplotlib (and seaborn, which draws through it) in the brand's colors,
fonts and type sizes (design/charts-and-plots.md, section 8).

    import livery_mpl                      # in a deck's first cell, `#| include: false`

On import: the Agg backend outside a Jupyter kernel, the livery's fonts registered with
addfont(), build/livery.mplstyle applied (Make.common's MATPLOTLIBRC already did, without the
fonts), the colormaps registered and `livery` made the default. The livery is found as the
engine's reader finds it: an argument to use(), $LIVERY_DIR, a `_livery` link in the current
directory, else a livery.json beside this file (the charts bundle, mpl_zip.py).

    livery_mpl.colors          the categorical slots of the livery's mode, in order
    livery_mpl.cycle           the same as a cycler (axes.prop_cycle)
    livery_mpl.families        up to 8 hues x 3 tints: a large map, the hue naming the group
    livery_mpl.status, .muted  {good, warning, serious, critical}; the "Others" color
    livery_mpl.figsize("half") the content area (or a column of two) in canvas inches; height=0.6
                               takes that share of its height
    livery_mpl.shade_family(c, n)  n tints of c toward the surface, as the families are built
    with livery_mpl.dark():    the dark chrome, slots and maps, where the slide is dark: an HTML
                               .brand-dark slide, every slide of a dark livery; elsewhere (pptx
                               and PDF draw .brand-dark as an ordinary slide) it changes nothing

Colormaps: livery (the default sequential map), livery_r, livery_div (diverging), one
livery_seq_<ramp> per sequential ramp, each with a _dark twin (the dark selections), all
interpolated in OKLab between the livery's steps. A figure drawn at figsize() carries the
slide's own text sizes in every format.
"""

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

import matplotlib

if "ipykernel" not in sys.modules and "MPLBACKEND" not in os.environ:
    matplotlib.use("Agg")   # scripts and servers; a kernel keeps its inline backend, which Quarto reads

import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib import colormaps, font_manager
from matplotlib.colors import LinearSegmentedColormap

HERE = Path(__file__).resolve().parent


def _find(path=None) -> Path:
    for c in (path, os.environ.get("LIVERY_DIR"), "_livery"):
        if c and (Path(c) / "build" / "livery.json").exists():
            return Path(c).resolve() / "build" / "livery.json"
    if (HERE / "livery.json").exists():
        return HERE / "livery.json"
    raise FileNotFoundError("no livery: pass a directory, export LIVERY_DIR, or run where _livery links")


# -- OKLab (Björn Ottosson), for the colormaps' interpolation ------------------------------------

def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _srgb(c):
    c = min(max(c, 0.0), 1.0)
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _oklab(h):
    r, g, b = (_lin(int(h.lstrip("#")[i:i + 2], 16) / 255) for i in (0, 2, 4))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def _hex(L, a, b):
    l, m, s = ((L + 0.3963377774 * a + 0.2158037573 * b) ** 3, (L - 0.1055613458 * a - 0.0638541728 * b) ** 3,
               (L - 0.0894841775 * a - 1.2914855480 * b) ** 3)
    rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    return "#" + "".join(f"{round(_srgb(c) * 255):02X}" for c in rgb)


def mix(a: str, b: str, t: float) -> str:
    """a moved toward b by t (0..1) in OKLab."""
    A, B = _oklab(a), _oklab(b)
    return _hex(*(x + (y - x) * t for x, y in zip(A, B)))


def _cmap(name: str, steps: list[str], n: int = 256) -> LinearSegmentedColormap:
    """A map through the steps, evenly spaced, interpolated in OKLab."""
    out = []
    for i in range(n):
        x = i / (n - 1) * (len(steps) - 1)
        k = min(int(x), len(steps) - 2)
        out.append(mix(steps[k], steps[k + 1], x - k))
    return LinearSegmentedColormap.from_list(name, out, N=n)


# -- state ---------------------------------------------------------------------------------------

livery: dict = {}
charts: dict = {}
mode = "light"
colors: list = []
cycle = None
families: list = []
status: dict = {}
muted = ""
style = None


def _register(name, cmap):
    if name in colormaps:
        colormaps.unregister(name)
    colormaps.register(cmap, name=name)


def use(path=None) -> dict:
    """Load a livery (see the module's docstring), register its fonts and colormaps, apply its
    style; called on import. Returns livery.json."""
    global livery, charts, mode, colors, cycle, families, status, muted, style
    f = _find(path)
    livery = json.loads(f.read_text())
    base = f.parent.parent if f.parent.name == "build" else f.parent   # the livery dir, or the bundle
    for font in livery.get("typography", {}).get("fonts", []):
        for ff in font.get("files", []):
            p = base / ff["path"]
            if p.exists():
                font_manager.fontManager.addfont(str(p))
    charts = livery["charts"]
    mode = charts["mode"]
    style = f.parent / "livery.mplstyle"
    keep = {}
    if "QUARTO_FIG_WIDTH" in os.environ:   # Quarto's setup cell set the deck's figure size and dpi
        keep = {k: plt.rcParams[k] for k in ("figure.figsize", "figure.dpi", "savefig.dpi")}
        if output_format() == "pdf":   # beamer's fig-width is paper inches (it sizes the diagrams), so
            keep["figure.figsize"] = tuple(livery["charts"]["figsize"]["full"])   # none is passed there
    if style.exists():
        plt.style.use(str(style))
    plt.rcParams.update(keep)
    for m in ("light", "dark"):   # the livery's mode unsuffixed, the dark selections as _dark twins
        b = charts[m]
        for tag in ([""] if m == mode else []) + (["_dark"] if m == "dark" else []):
            seq = b["sequential"]
            _register(f"livery{tag}", _cmap(f"livery{tag}", seq[b["sequential-default"]]))
            _register(f"livery{tag}_r", _cmap(f"livery{tag}_r", seq[b["sequential-default"]][::-1]))
            _register(f"livery_div{tag}", _cmap(f"livery_div{tag}", b["diverging"]))
            for n, r in seq.items():
                _register(f"livery_seq_{n}{tag}", _cmap(f"livery_seq_{n}{tag}", r))
    plt.rcParams["image.cmap"] = "livery"
    b = charts[mode]
    colors, families, status, muted = list(b["categorical"]), b["families"], b["status"], b["muted"]
    cycle = cycler(color=colors)
    return livery


def output_format() -> str:
    """The format being rendered: $ENGINE_FORMAT (Make.common sets pptx, html or pdf), else read
    from Quarto's figure format (svg is the HTML deck's), else ''."""
    f = os.environ.get("ENGINE_FORMAT")
    if f:
        return f
    return {"svg": "html", "pdf": "pdf", "png": "pptx"}.get(os.environ.get("QUARTO_FIG_FORMAT", ""), "")


def figsize(kind: str = "full", height: float = 1.0) -> tuple[float, float]:
    """The content area ("full") or one of two columns ("half") in canvas inches; height scales
    the content height (0.6: a wide, short plot)."""
    w, h = charts["figsize"][kind]
    return (w, round(h * height, 2))


def shade_family(color: str, n: int = 3, surface: str | None = None) -> list[str]:
    """n members of color's family: the color, then tints toward the surface, as far as two thirds
    of the way on light (0.55 on dark, where the pale end would sink into the surface)."""
    m = "dark" if surface is None and mode == "dark" else mode
    surface = surface or charts[m]["surface"]
    reach = 0.55 if m == "dark" else 2 / 3
    return [color] + [mix(color, surface, reach * i / (n - 1)) for i in range(1, n)] if n > 1 else [color]


def _rc(m: str) -> dict:
    c, b = charts["chrome"][m], charts[m]
    return {"text.color": c["text"], "axes.labelcolor": c["text"], "xtick.labelcolor": c["text"],
            "ytick.labelcolor": c["text"], "axes.edgecolor": c["spine"], "xtick.color": c["spine"],
            "ytick.color": c["spine"], "grid.color": c["grid"], "patch.edgecolor": b["surface"],
            "axes.prop_cycle": cycler(color=b["categorical"]),
            "image.cmap": "livery" if m == mode else "livery_dark"}


@contextmanager
def dark(force: bool = False):
    """Draw for a dark slide inside the block: the dark chrome, slots, families and maps. Applies on
    a dark livery and in the HTML deck (where .brand-dark is dark), or with force=True; pptx and PDF
    draw .brand-dark as an ordinary slide, so there it changes nothing."""
    global colors, families, status, muted, cycle
    on = force or mode == "dark" or output_format() == "html"
    if not on:
        yield
        return
    saved = (colors, families, status, muted, cycle)
    b = charts["dark"]
    colors, families, status, muted = list(b["categorical"]), b["families"], b["status"], b["muted"]
    cycle = cycler(color=colors)
    try:
        with plt.rc_context(_rc("dark")):
            yield
    finally:
        colors, families, status, muted, cycle = saved


use()
