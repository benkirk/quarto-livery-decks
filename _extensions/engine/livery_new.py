"""Scaffold a livery directory (design section 6), ready for `livery all`.

    livery new <dir> [--from <deck.pptx>] [--extends <name>]

A scaffold builds in every format as it stands, and is meant to be edited: a palette named after
PowerPoint's twelve theme slots (dk1, lt1, dk2, ... accent6; with --from, the reference deck's,
else a neutral blue one), the roles on those slots, Public Sans (OFL, from liveries/nasa) as the
stand-in face with its license, a placeholder mark drawn from the livery's name in a light and a
dark version, the engine's default geometry, and reference/notes.md for the decisions. --from
also writes reference/report.md (`livery inspect`) and takes the deck's fonts as the pptx
typefaces and its slide size as pptx.size. --extends makes a flavor of a livery beside the new
directory: a livery.yml naming only its parent, an empty _brand.yml, the notes (with --from,
its reference/report.md too; the colors and fonts stay the parent's).
"""

import os
import shutil
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
STAND_IN = ENGINE.parents[1] / "liveries" / "nasa" / "fonts"   # Public Sans, OFL
STAND_IN_FILES = [("PublicSans-Regular.ttf", 400, None), ("PublicSans-Italic.ttf", 400, "italic"),
                  ("PublicSans-SemiBold.ttf", 600, None), ("PublicSans-Bold.ttf", 700, None),
                  ("PublicSans-BoldItalic.ttf", 700, "italic"), ("OFL-PublicSans.txt", None, None)]
# a neutral palette for a scaffold without a reference deck, on PowerPoint's slot names
DEFAULT_SLOTS = {"dk1": "1B2430", "lt1": "FFFFFF", "dk2": "1F4E8C", "lt2": "EEF1F5",
                 "accent1": "5AA9E6", "accent2": "A23B72", "accent3": "0E1A2B", "accent4": "E07A1F",
                 "accent5": "F2C230", "accent6": "1F4E8C"}


def header(d: Path) -> str:
    """The editor line: the schema by its path from the livery when the two share a project
    (../../_extensions/... in liveries/<name>/, ../framework/... beside a submodule), else by its
    absolute path (a livery in another tree)."""
    schema, d = ENGINE / "livery.schema.json", d.resolve()
    shared = Path(os.path.commonpath([schema, d]))
    near = len(shared.parts) > 3   # more than /, a top directory and one below it (/Users/<name>)
    path = Path(os.path.relpath(schema, d)).as_posix() if near else schema.as_posix()
    return f"# yaml-language-server: $schema={path}\n"


NOTES = """# {name}: onboarding notes

The decisions taken while making this livery (liveries/README.md, "Adding a livery"): where each color, font
and mark came from, what the brand guide says, and what was left for later.

## Palette and roles

## Fonts

## Marks

## Geometry and slide styles

## Chart colors
"""


def _mark(name: str, color: str, path: Path) -> float:
    """A placeholder lockup: the livery's name in the stand-in's bold, on transparency; its aspect."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(str(STAND_IN / "PublicSans-Bold.ttf"), 200)
    text = name.upper()
    l, t, r, b = font.getbbox(text)
    pad = 20
    img = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad - l, pad - t), text, font=font, fill="#" + color)
    img.save(path)
    return round(img.width / img.height, 3)


def _brand(name: str, slots: dict, family: str) -> str:
    L = [f"# {name}: the brand in Quarto's brand.yml form (colors, fonts, logos). The palette is named",
         "# after PowerPoint's theme slots; rename the colors after the brand's and check them",
         "# against its guide (livery.yml's roles and pptx.scheme name them too).",
         "meta:", f"  name: {name}", "", "color:", "  palette:"]
    L += [f'    {k}: "#{v}"' for k, v in slots.items()]
    L += ["  primary: dk2", "  secondary: accent1", "  foreground: dk1", "  background: lt1", "",
          "typography:", "  fonts:", f"    - family: {family}", "      source: file", "      files:"]
    for f, weight, style in STAND_IN_FILES:
        if weight is None:
            continue
        L += [f"        - path: fonts/{f}", f"          weight: {weight}"] + ([f"          style: {style}"] if style else [])
    L += [f"  base: {family}", f"  headings: {family}", "",
          "logo:", "  images:", "    mark: {path: logos/mark.png}", "    mark-white: {path: logos/mark-white.png}",
          "  medium: {light: mark, dark: mark-white}", ""]
    return "\n".join(L)


def _livery(d: Path, name: str, aspect: float, typeface: str, heading: str | None, size: list | None) -> str:
    L = [header(d).rstrip(), "schema: 1", f"name: {name}", "extends: null", "",
         "# every key: liveries/REFERENCE.md", "roles:",
         "  primary-text: lt1", "  primary-contrast: dk2", "  accent: accent4", "  highlight: accent2",
         '  muted: "#6B7280"', "  surface: lt2", "  warning: accent5", "  dark: accent3", "",
         "geometry:", "  margin: 0.06", "  tab-width: 0.018", "  logo:", "    height: 0.0644", "    top: 0.0533",
         f"    aspect: {aspect}", "  full:", "    pad: 0.025", "    footline: 0.075", "    caption: 0.06", "",
         "section:", "  label: Section", "", "pptx:", f"  typeface: {typeface}"]
    if heading and heading != typeface:
        L.append(f"  heading-typeface: {heading}")
    if size and [round(v, 3) for v in size] != [13.333, 7.5]:
        L.append(f"  size: [{size[0]}, {size[1]}]")
    return "\n".join(L) + "\n"


def new(d: Path, deck: Path | None = None, extends: str | None = None):
    if d.exists() and any(d.iterdir()):
        sys.exit(f"{d} exists and is not empty")
    name = d.name
    if extends:
        parent = d.parent / extends
        if not (parent / "livery.yml").exists():
            sys.exit(f"--extends {extends}: no livery at {parent} (a parent sits beside its flavor)")
        (d / "reference").mkdir(parents=True)
        (d / "livery.yml").write_text(f"{header(d)}schema: 1\nname: {name}\nextends: {extends}\n")
        (d / "_brand.yml").write_text(f"# {name}: a flavor of {extends}; name here only what differs from ../{extends}/_brand.yml\n")
        (d / "reference" / "notes.md").write_text(NOTES.format(name=name))
        if deck:   # a flavor takes its parent's colors and fonts; the deck's reading is still worth keeping
            import livery_inspect
            livery_inspect.inspect(deck, d / "reference" / "report.md")
        print(f"new flavor {d} of {parent}: edit livery.yml, then `livery all {d}`")
        return
    if not STAND_IN.is_dir():
        sys.exit(f"no stand-in fonts at {STAND_IN}: livery new needs the framework's liveries/nasa")
    for sub in ("fonts", "logos", "art", "reference"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    slots, typeface, heading, size = dict(DEFAULT_SLOTS), "Public Sans", None, None
    if deck:
        import livery_inspect
        f = livery_inspect.facts(deck)
        slots.update({k: v for k, v in f["colors"].items() if k in DEFAULT_SLOTS})
        typeface = f["fonts"].get("minor") or typeface
        heading = f["fonts"].get("major")
        size = f["size"]
        livery_inspect.inspect(deck, d / "reference" / "report.md")
    for f, *_ in STAND_IN_FILES:
        shutil.copy2(STAND_IN / f, d / "fonts" / f)
    aspect = _mark(name, slots["dk2"], d / "logos" / "mark.png")
    _mark(name, "FFFFFF", d / "logos" / "mark-white.png")
    (d / "_brand.yml").write_text(_brand(name, slots, "Public Sans"))
    (d / "livery.yml").write_text(_livery(d, name, aspect, typeface, heading, size))
    (d / "reference" / "notes.md").write_text(NOTES.format(name=name))
    print(f"new livery {d}{f' from {deck}' if deck else ''}: edit _brand.yml and livery.yml, then `livery all {d}`")
