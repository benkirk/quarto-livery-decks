"""Pack one livery's plot style into a charts bundle, for matplotlib outside the decks.

    livery zip --charts <livery dir> -o <zip>

The zip holds, at its top: livery_mpl.py (the engine's helper), build/livery.mplstyle and
build/livery.json as livery.mplstyle and livery.json (its font paths rewritten to fonts/), every
font file the livery names (a flavor's parent's too) with the licenses beside them in their
directories, the chart colors' contact sheet (charts-<name>.png, livery_charts.swatch(); needs
Pillow) and a README. Unzipped anywhere, `import livery_mpl` in a script beside it (or with the
directory on PYTHONPATH) plots in the livery: the helper finds the livery.json beside itself."""

import json
import sys
import tempfile
import zipfile
from pathlib import Path

import livery as livery_mod
import livery_charts

ENGINE = Path(__file__).resolve().parent
LICENSES = ("*.txt", "LICENSE*", "OFL*", "COPYING*")

README = """\
# {name}: plots in the livery

matplotlib (and seaborn, which draws through it) in the {name} livery's chart colors, font and
type sizes, from quarto-livery-decks (design/charts-and-plots.md). Generated from the livery's
build/livery.json; do not edit, rebuild it (`make charts-zip LIVERY={name}`).

Packed by engine {engine} (`livery_mpl.__version__`) from a livery written for schema {schema}.
Each release attaches one bundle per livery (this version's: .../releases/tag/v{engine} at
https://github.com/benkirk/quarto-livery-decks), and its CHANGELOG.md says what changed for plots.

    import livery_mpl                  # fonts, style, colormaps: every plot after this is styled
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()           # the slide's content area, {full_w} x {full_h} in
    ax.plot(x, y)                      # the categorical colors, in order

Keep this directory beside your script, or put it on PYTHONPATH. Without the helper,
`plt.style.use("livery.mplstyle")` gives the colors and sizes; the font then has to be installed.

- livery_mpl.colors, .families, .status, .muted: the chart colors ({mode} slides); charts-{name}.png
  shows them all, light and dark
- livery_mpl.figsize("full" | "half"): a slide's content area or one of two columns, in inches;
  a figure at this size has the slide's text sizes ({body} pt labels on a {canvas} in slide)
- colormaps: livery (sequential), livery_div (diverging), livery_seq_<ramp>, each with _dark
- with livery_mpl.dark(force=True): the dark chrome and colors, for a dark slide or page
- livery_mpl.use(path): another livery (a directory, or another bundle)
- fonts/: the livery's fonts and their licenses

These names, livery_mpl.__all__ and the colormaps, are the helper's stable API.
"""


def bundle(livery_dir: Path) -> dict[str, bytes | Path]:
    """archive path -> bytes or source file."""
    lv = livery_mod.load(livery_dir)
    d = Path(lv["dir"])
    name = livery_dir.name
    data = json.loads((d / "build" / "livery.json").read_text())
    out: dict[str, bytes | Path] = {}
    seen = {}
    for font in data.get("typography", {}).get("fonts", []):
        for f in font.get("files", []):
            src = (d / f["path"]).resolve()
            arc = f"fonts/{src.name}"
            if seen.get(arc, src) != src:
                sys.exit(f"two fonts named {src.name}: {seen[arc]} and {src}")
            seen[arc] = src
            out[arc] = src
            f["path"] = arc
            for pat in LICENSES:   # the license files beside the font
                for lic in sorted(src.parent.glob(pat)):
                    out.setdefault(f"fonts/{lic.name}", lic)
    data.pop("dir", None)
    out["livery.json"] = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
    out["livery.mplstyle"] = d / "build" / "livery.mplstyle"
    out["livery_mpl.py"] = ENGINE / "mpl" / "livery_mpl.py"
    ch, ty = data["charts"], data["type"]
    out["README.md"] = README.format(
        name=name, engine=data["engine"], schema=data["schema"], mode=ch["mode"], full_w=ch["figsize"]["full"][0], full_h=ch["figsize"]["full"][1],
        body=ty["roles"]["body"]["pt"], canvas=f"{ty['canvas']['w'] / 72:g} x {ty['canvas']['h'] / 72:g}").encode()
    with tempfile.TemporaryDirectory() as tmp:
        sheet = Path(tmp) / f"charts-{name}.png"
        livery_charts.swatch(data["name"], ch, sheet)
        out[sheet.name] = sheet.read_bytes()
    return out


def write(livery: Path, out: Path):
    """The livery's charts bundle."""
    files = bundle(livery)
    missing = [str(v) for v in files.values() if isinstance(v, Path) and not v.is_file()]
    if missing:
        sys.exit("missing: " + ", ".join(missing))
    out.unlink(missing_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc in sorted(files):
            v = files[arc]
            zf.writestr(arc, v) if isinstance(v, bytes) else zf.write(v, arc)
    print(f"wrote {out}: {livery.name}, {len(files)} files")
