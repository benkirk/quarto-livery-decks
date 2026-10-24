"""Plots in the livery: matplotlib (and seaborn, which draws through it) in the brand's colors,
fonts and type sizes (design/charts-and-plots.md, section 8).

    import livery_mpl                      # in a deck's first cell, `#| include: false`

    import livery_mpl                      # installed by pip: call use() first
    livery_mpl.use("ncar-charts.zip")      # a release's charts bundle, or a livery's directory

On import: the Agg backend outside a Jupyter kernel and, when a livery is found, use(): the
livery's fonts registered with addfont(), build/livery.mplstyle applied (Make.common's
MATPLOTLIBRC already did, without the fonts), the colormaps registered and `livery` made the
default. The livery is found as the engine's reader finds it: an argument to use(), $LIVERY_DIR,
a `_livery` link in the current directory, else a livery.json beside this file (the charts
bundle, mpl_zip.py). With none (pip's install) the module imports unconfigured, `livery` empty.
A bundle's zip given to use() is unpacked once into $XDG_CACHE_HOME (else ~/.cache)
/livery_mpl/<zip stem>-<engine>/, again only when the zip is newer.

    livery_mpl.colors          the categorical slots of the livery's mode, in order
    livery_mpl.cycle           the same as a cycler (axes.prop_cycle)
    livery_mpl.families        up to 8 hues x 3 tints: a large map, the hue naming the group
    livery_mpl.status, .muted  {good, warning, serious, critical}; the "Others" color
    livery_mpl.figsize("half") the content area (or a column of two) in canvas inches; height=0.6
                               takes that share of its height
    livery_mpl.surface         the background the plots sit on (the dark one inside dark())
    livery_mpl.shade_family(c, n)  n tints of c toward the surface, as the families are built
    livery_mpl.mix(a, b, t)    a moved toward b by t (0..1), in OKLab
    with livery_mpl.dense():   every text size scaled together (0.65 by default, to the half
                               point), for small multiples: a 3 x 4 grid at the slide's sizes
                               leaves no room for the data
    with livery_mpl.raster():  the figures shown inside as PNG (200 dpi unless given) where the
                               deck draws vector (HTML's SVG, the PDF's PDF): one plot with
                               thousands of marks, the rest of the deck still vector
    with livery_mpl.dark():    the dark chrome, slots and maps, for a dark slide: a {.brand-dark}
                               slide, which every format draws on the dark role, or any slide of
                               a dark livery
    livery_mpl.use(path)       load another livery (a directory, a bundle's, or a bundle's zip)
    livery_mpl.__version__     the engine's version (a bundle's: the engine that packed it; pip's:
                               the release it was installed from)

Colormaps: livery (the default sequential map), livery_r, livery_div (diverging), one
livery_seq_<ramp> per sequential ramp, each with a _dark twin (the dark selections), all
interpolated in OKLab between the livery's steps. A figure drawn at figsize() carries the
slide's own text sizes in every format.

These names (__all__, and the colormaps) are the stable API: a change to them is a Plots entry
in CHANGELOG.md.
"""

import json
import os
import sys
import zipfile
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

__all__ = ["__version__", "use", "colors", "cycle", "families", "status", "muted", "surface",
           "figsize", "shade_family", "mix", "dark", "dense", "raster"]


def _engine_version() -> str:
    """The engine's version: its _extension.yml beside this file's directory (in the engine), else
    the stamp in the livery.json beside this file (a charts bundle: the engine that packed it),
    else the installed distribution's (pip's, which pyproject.toml read from _extension.yml)."""
    ext = HERE.parent / "_extension.yml"
    if ext.exists():
        for line in ext.read_text().splitlines():
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip()
    if (HERE / "livery.json").exists():
        return json.loads((HERE / "livery.json").read_text()).get("engine", "unknown")
    from importlib.metadata import PackageNotFoundError, version
    try:
        return version("livery-mpl")
    except PackageNotFoundError:
        return "unknown"


__version__ = _engine_version()


def _unpack(z) -> Path:
    """A charts bundle's zip unpacked into $XDG_CACHE_HOME (else ~/.cache)/livery_mpl/<stem>-<engine>/,
    unless an unpacking newer than the zip is there; livery.json last, so a broken one is redone."""
    z = Path(z).resolve()
    with zipfile.ZipFile(z) as zf:
        engine = json.loads(zf.read("livery.json")).get("engine", "unknown")
        d = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "livery_mpl" / f"{z.stem}-{engine}"
        stamp = d / "livery.json"
        if not stamp.exists() or stamp.stat().st_mtime < z.stat().st_mtime:
            for n in sorted(zf.namelist(), key=lambda n: n == "livery.json"):
                zf.extract(n, d)
    return d


def _find(path=None) -> Path | None:
    """livery.json of the first livery found (the module's docstring), else None."""
    if path and str(path).endswith(".zip"):
        path = _unpack(path)
    for c in (path, os.environ.get("LIVERY_DIR"), "_livery"):
        for f in ("build/livery.json", "livery.json"):   # a livery's directory, an unpacked bundle
            if c and (Path(c) / f).exists():
                return Path(c).resolve() / f
    if (HERE / "livery.json").exists():
        return HERE / "livery.json"
    return None


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
surface = ""
style = None


def _register(name, cmap):
    if name in colormaps:
        colormaps.unregister(name)
    colormaps.register(cmap, name=name)


def use(path=None) -> dict:
    """Load a livery (see the module's docstring), register its fonts and colormaps, apply its
    style; called on import when a livery is found. Returns livery.json."""
    global livery, charts, mode, colors, cycle, families, status, muted, surface, style
    f = _find(path)
    if f is None:
        raise FileNotFoundError("no livery: pass a directory or a charts bundle's zip, export LIVERY_DIR, "
                                "or run where _livery links")
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
            _register(f"livery{tag}", _cmap(f"livery{tag}", seq[b["default-map"]]))
            _register(f"livery{tag}_r", _cmap(f"livery{tag}_r", seq[b["default-map"]][::-1]))
            _register(f"livery_div{tag}", _cmap(f"livery_div{tag}", b["diverging"]))
            for n, r in seq.items():
                _register(f"livery_seq_{n}{tag}", _cmap(f"livery_seq_{n}{tag}", r))
    plt.rcParams["image.cmap"] = "livery"
    b = charts[mode]
    colors, families, status, muted = list(b["categorical"]), b["families"], b["status"], b["muted"]
    surface = b["surface"]
    cycle = cycler(color=colors)
    return livery


def output_format() -> str:
    """The format being rendered: $ENGINE_FORMAT (Make.common sets pptx, html or pdf), else "pdf"
    when Quarto's figure format is pdf (only beamer's is), else '' (svg is both pptx's and HTML's)."""
    f = os.environ.get("ENGINE_FORMAT")
    if f:
        return f
    return "pdf" if os.environ.get("QUARTO_FIG_FORMAT") == "pdf" else ""


def figsize(kind: str = "full", height: float = 1.0) -> tuple[float, float]:
    """The content area ("full") or one of two columns ("half") in canvas inches; height scales
    the content height (0.6: a wide, short plot)."""
    w, h = charts["figsize"][kind]
    return (w, round(h * height, 2))


def shade_family(color: str, n: int = 3, surface: str | None = None) -> list[str]:
    """n members of color's family: the color, then tints toward the surface (the module's, so the
    dark one inside dark()), as far as two thirds of the way on light (0.55 on dark, where the pale
    end would sink into the surface)."""
    to = surface or globals()["surface"]
    reach = 0.55 if to == charts["dark"]["surface"] else 2 / 3
    return [color] + [mix(color, to, reach * i / (n - 1)) for i in range(1, n)] if n > 1 else [color]


def _rc(m: str) -> dict:
    c, b = charts["chrome"][m], charts[m]
    return {"text.color": c["text"], "axes.labelcolor": c["text"], "xtick.labelcolor": c["text"],
            "ytick.labelcolor": c["text"], "axes.edgecolor": c["spine"], "xtick.color": c["spine"],
            "ytick.color": c["spine"], "grid.color": c["grid"], "patch.edgecolor": b["surface"],
            "axes.prop_cycle": cycler(color=b["categorical"]),
            "image.cmap": "livery" if m == mode else "livery_dark"}


@contextmanager
def dark():
    """Draw for a dark slide inside the block: the dark chrome, slots, families and maps, in every
    format (each draws a {.brand-dark} slide on the dark role; a dark livery's slides all are)."""
    global colors, families, status, muted, surface, cycle
    saved = (colors, families, status, muted, surface, cycle)
    b = charts["dark"]
    colors, families, status, muted = list(b["categorical"]), b["families"], b["status"], b["muted"]
    surface = b["surface"]
    cycle = cycler(color=colors)
    try:
        with plt.rc_context(_rc("dark")):
            yield
    finally:
        colors, families, status, muted, surface, cycle = saved


SIZES = ("font.size", "axes.titlesize", "axes.labelsize", "xtick.labelsize", "ytick.labelsize",
         "legend.fontsize", "legend.title_fontsize", "figure.titlesize", "figure.labelsize")


@contextmanager
def dense(scale: float = 0.65):
    """Every text size scaled by scale inside the block, rounded to the half point, as a slide's
    sizes are: for small multiples, where the slide's type would crowd out the data. Named sizes
    ("large") resolve against font.size first."""
    base = plt.rcParams["font.size"]
    rc = {}
    for k in SIZES:
        v = plt.rcParams.get(k)
        if v is None:
            continue
        pt = font_manager.font_scalings.get(v, 1.0) * base if isinstance(v, str) else float(v)
        rc[k] = max(0.5, round(pt * scale * 2) / 2)
    with plt.rc_context(rc):
        yield


@contextmanager
def raster(dpi: float = 200):
    """Show the figures displayed inside the block as PNG at dpi, where the deck draws them as
    vector (the SVG of HTML and pptx, the PDF's PDF): a plot with thousands of marks makes a heavy
    SVG, and the Jupyter engine does not honor a cell's `fig-format` (Quarto's setup cell picks the
    document's format once). The rest of the deck stays vector; a run outside a kernel is
    unchanged. Call plt.show() inside the block: the format is picked when the figure is shown.
    The whole deck: `fig-format: png` in its front matter (docs/formats.md "HTML (revealjs)")."""
    try:
        from IPython.core.interactiveshell import InteractiveShell
        from matplotlib.figure import Figure
        from matplotlib_inline.backend_inline import set_matplotlib_formats
    except ImportError:
        yield
        return
    if not InteractiveShell.initialized():
        yield
        return
    formatters = InteractiveShell.instance().display_formatter.formatters
    mimes = {"image/png": "png", "image/svg+xml": "svg", "image/jpeg": "jpeg", "application/pdf": "pdf"}
    was = [fmt for mime, fmt in mimes.items() if Figure in formatters[mime].type_printers]
    if not was or was == ["png"]:   # no inline backend, or the deck draws PNG already
        yield
        return
    set_matplotlib_formats("png", dpi=dpi)
    try:
        yield
    finally:
        set_matplotlib_formats(*was)


if _find():
    use()
