"""gnuplot in the livery: a gnuplot script drawn in the brand's colors, fonts and type sizes, text as
outlines, at the slide's content size (design/plots-gnuplot-and-r.md, section 3).

    import livery_gp                       # in a deck's first cell, `#| include: false`

    livery_gp.plot('''
    set xlabel 'Nodes'; set ylabel 'Time (s)'
    plot 'data/scaling.tsv' using 1:2 with linespoints title 'Run A'
    ''')                                   # the cell's last line: Jupyter shows what it returns

The livery is livery_mpl's (imported here: the one reader of livery.json): the one it found or
the last given to livery_mpl.use(). plot() writes a script that sets a cairo PDF terminal at
livery_mpl.figsize(kind, height), loads the livery's livery.gp (build/livery.gp, a bundle's
livery.gp; Make.common also exports GNUPLOT_LIB, so a plain gnuplot script can `load
'livery.gp'`), applies @livery_dark when dark, then runs the author's lines with `gnuplot -d` (no
~/.gnuplot) in the current directory, so a data file's path is the deck's. gnuplot sees the
livery's font directories through a fontconfig file of its own, which pango reads on a Mac too
(PANGOCAIRO_BACKEND=fc), so a machine without the face still draws it. What it returns shows as
the PDF where the deck draws PDF (beamer) and as SVG with the glyphs as paths elsewhere
(pdftocairo -svg; pptx's PNG fallback is svg_fallback's, as for any SVG plot). Commands that
start with @ go on a line of their own: a line's macros expand before any of it runs. Needs gnuplot with its cairo terminals (the image's gnuplot-nox; `brew install gnuplot`)
and poppler's pdftocairo.

    livery_gp.plot(script, kind="full", height=1.0, dark=False)
                               a Plot: shown by Jupyter, .pdf (bytes), .svg (text), .save(path)

In the script: linetypes 1..n are the categorical slots, the palette the livery's default map,
@livery_div the diverging one, @livery_dark/@livery_light the other mode, and the strings
livery_good, livery_warning, livery_serious, livery_critical, livery_muted, livery_surface and
livery_text the mode's colors (`lc rgb livery_muted`).

These names (__all__, and the livery.gp names above) are the stable API: a change to them is a
Plots entry in CHANGELOG.md.
"""

import base64
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

import livery_mpl

__all__ = ["plot", "Plot"]

# cairo's text is pango's, at 96 dpi: fontscale 0.75 makes a font's size points
TERMINAL = "set terminal pdfcairo size {w}in,{h}in fontscale 0.75 linewidth 1"


class Plot:
    """A rendered plot: Jupyter shows it as the format's figure (_repr_mimebundle_)."""

    def __init__(self, pdf: bytes, svg: str | None):
        self.pdf, self.svg = pdf, svg

    def _repr_mimebundle_(self, include=None, exclude=None):
        if self.svg is None:
            return {"application/pdf": base64.b64encode(self.pdf).decode()}
        return {"image/svg+xml": self.svg}

    def save(self, path) -> None:
        """Write the PDF (path ending .pdf) or the outlined SVG."""
        p = Path(path)
        if p.suffix == ".pdf":
            p.write_bytes(self.pdf)
        else:
            p.write_text(self.svg if self.svg is not None else _svg(self.pdf))


def _need(tool: str, what: str) -> str:
    exe = shutil.which(tool)
    if not exe:
        raise RuntimeError(f"livery_gp: no {tool} on PATH ({what})")
    return exe


def _fonts_conf(gnuplot: str) -> Path:
    """A fontconfig file for gnuplot: its own configuration (FONTCONFIG_FILE, else its prefix's: a
    Homebrew or conda gnuplot's, else the system's) plus the livery's font directories, its cache under $XDG_CACHE_HOME."""
    base = livery_mpl.style.parent
    base = base.parent if base.name == "build" else base   # the livery's directory, or a bundle's
    dirs = sorted({str((base / ff["path"]).resolve().parent)
                   for font in livery_mpl.livery.get("typography", {}).get("fonts", [])
                   for ff in font.get("files", []) if (base / ff["path"]).exists()})
    own = [os.environ.get("FONTCONFIG_FILE")] + [Path(g).parent.parent / "etc/fonts/fonts.conf"   # Homebrew's
           for g in (gnuplot, Path(gnuplot).resolve())] + ["/etc/fonts/fonts.conf"]   # link, then its target
    system = next((str(c) for c in own if c and Path(c).exists()), None)
    cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "livery_gp"
    cache.mkdir(parents=True, exist_ok=True)
    conf = cache / f"fonts-{livery_mpl.livery['name']}.conf"
    text = "\n".join(['<?xml version="1.0"?>', '<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">',
                      "<fontconfig>", *(f"  <dir>{escape(d)}</dir>" for d in dirs),
                      f"  <cachedir>{escape(str(cache))}</cachedir>",
                      *([f'  <include ignore_missing="yes">{escape(system)}</include>'] if system else []),
                      "</fontconfig>"]) + "\n"
    if not conf.exists() or conf.read_text() != text:
        conf.write_text(text)
    return conf


def _svg(pdf: bytes) -> str:
    """The PDF as SVG, its glyphs as paths (pdftocairo writes the size in pt, which the engine's
    engine-plots.lua reads as the figure's natural size)."""
    exe = _need("pdftocairo", "poppler, for the SVG")
    with tempfile.TemporaryDirectory() as t:
        (Path(t) / "p.pdf").write_bytes(pdf)
        subprocess.run([exe, "-svg", "p.pdf", "p.svg"], cwd=t, check=True, capture_output=True)
        return (Path(t) / "p.svg").read_text()


def plot(script: str, kind: str = "full", height: float = 1.0, dark: bool = False) -> Plot:
    """Draw script (gnuplot commands, no terminal or output) at figsize(kind, height) in the
    livery; dark: the dark mode's colors, for a {.brand-dark} slide (a dark livery's are its own)."""
    if not livery_mpl.livery:
        raise RuntimeError("livery_gp: no livery: export LIVERY_DIR, run where _livery links, or call livery_mpl.use()")
    gnuplot = _need("gnuplot", "the image's gnuplot-nox; brew install gnuplot")
    w, h = livery_mpl.figsize(kind, height)
    style = livery_mpl.style.parent / "livery.gp"
    with tempfile.TemporaryDirectory() as t:
        out = Path(t) / "plot.pdf"
        (Path(t) / "plot.gp").write_text("\n".join([
            TERMINAL.format(w=w, h=h), f"set output {_q(out)}", f"load {_q(style)}",
            "@livery_dark" if dark else "", script, "unset output", ""]))
        # pango through fontconfig: Homebrew's draws through CoreText by default, which sees
        # installed faces only (a bundled one fell back to Helvetica)
        env = {**os.environ, "FONTCONFIG_FILE": str(_fonts_conf(gnuplot)), "PANGOCAIRO_BACKEND": "fc"}
        env.setdefault("GNUPLOT_LIB", str(style.parent))
        r = subprocess.run([gnuplot, "-d", str(Path(t) / "plot.gp")], env=env, capture_output=True, text=True)
        if r.returncode or not out.exists() or not out.stat().st_size:
            raise RuntimeError(f"livery_gp: gnuplot failed:\n{r.stderr.strip()}")
        if r.stderr.strip():   # warnings and print's output: the render's log shows them
            print(r.stderr.rstrip(), file=sys.stderr)
        pdf = out.read_bytes()
    return Plot(pdf, None if livery_mpl.output_format() == "pdf" else _svg(pdf))


def _q(p) -> str:
    """A path as a gnuplot single-quoted string ('' is a quote inside one)."""
    return "'" + str(p).replace("'", "''") + "'"
