#!/usr/bin/env python3
"""The `livery` command, everything a livery owner does, and the reader of a livery's resolved
truth, build/livery.json, for the template builder, the checks, the pptx post-render steps and
the framework's scripts.

    livery new <dir> [--from <deck.pptx>] [--extends <name>]   scaffold a livery (livery_new.py)
    livery inspect <deck.pptx> [-o report.md] [--media DIR]     report on a reference deck
    livery build <dir>... [--check]     _brand.yml + livery.yml -> build/, validated (livery_build.py)
    livery template <dir> [-o FILE]     build/livery.json -> template.pptx (livery_template.py)
    livery check <dir>... [--swatch DIR] [--qa]   the livery's checks; --qa then the quickstart's make qa
    livery all <dir>... [--qa]          build, template, check: the onboarding loop
    livery zip <dir> -o <zip> [--starter FILE] [--photo FILE]   the Overleaf project: the starter and the cookbook (overleaf_zip.py)
    livery zip --charts <dir> -o <zip>  the charts bundle for matplotlib (mpl_zip.py)
    livery schema --doc [-o FILE] [--check]   livery.yml's reference from its schema
    livery deps|mono|figsize <dir>      for Make.common: the files a deck build reads, the code
                                        face's family, the plots' default size ("<w> <h>" inches)

`livery` is this file: `python3 <framework>/_extensions/engine/livery.py`, or the framework's
`make livery LIVERY=<name>` (or LIVERY_DIR=), which runs `livery all`. The subcommands import
their modules only when run, so `zip` needs nothing beyond Python and the engine.

    import livery as livery_mod     load, color, hex, scheme, blend, mix, font_file, mark, files

The reader's directory comes from the argument, else $LIVERY_DIR (exported by the framework's
Make.common), else a `_livery` link in the current directory. `deps` prints
build/livery.{json,sty,css,theme,mplstyle}, the template and every file the data names (the
parent's too), joined to the directory as given, and warns when another engine version wrote
build/; deps, mono and figsize print nothing when build/livery.json is missing."""

import json
import math
import os
import sys
from pathlib import Path


# the pptx template's space before a body paragraph, as a share of the body type: the first list
# level, then the deeper ones (livery_template.py writes it as a:spcBef; the steps that cut a box
# to its measured text add the same, pptx_steps/measure.py)
SPC_BEFORE = (0.5, 0.3)


def livery_dir(path: str | os.PathLike | None = None) -> Path:
    for candidate in (path, os.environ.get("LIVERY_DIR"), "_livery"):
        if candidate and Path(candidate).is_dir():
            return Path(candidate).resolve()
    raise FileNotFoundError("no livery: pass a directory, export LIVERY_DIR, or run where _livery links")


def load(path: str | os.PathLike | None = None) -> dict:
    d = livery_dir(path)
    f = d / "build" / "livery.json"
    if not f.exists():
        raise FileNotFoundError(f"{f} missing: run livery build {d}")
    data = json.loads(f.read_text())
    data["dir"] = str(d)
    return data


def mix(a: str, b: str, share: float) -> str:
    """Sass mix(): a's share of each channel plus b's remainder, rounded; '#RRGGBB' in and out."""
    pairs = zip(bytes.fromhex(a.lstrip("#")), bytes.fromhex(b.lstrip("#")))
    return "#" + "".join(f"{round(x * share + y * (1 - share)):02X}" for x, y in pairs)


def luminance(hexv: str) -> float:
    """WCAG relative luminance of '#RRGGBB'."""
    ch = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x / 255) for x in bytes.fromhex(hexv.lstrip("#")))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG 2 contrast ratio of two '#RRGGBB' colors."""
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def color(livery: dict, role: str) -> str:
    """A role's hex without '#', as the pptx scripts write it."""
    return livery["roles"][role].lstrip("#").upper()


def hex(livery: dict, value: str) -> str:
    """A role's or a blend's, or a '#RRGGBB' value's, six digits upper: the one color form the pptx
    steps write (a box's color in livery.json is a hex, a role= attribute a role)."""
    if not value.startswith("#"):
        value = livery["roles"].get(value) or livery["blends"][value]
    return value.lstrip("#").upper()


def scheme(livery: dict, slot: str) -> str:
    """The hex of a theme1.xml scheme slot (dk2, accent4, ...; design section 4)."""
    return livery["pptx"]["scheme"][slot].lstrip("#").upper()


def blend(livery: dict, key: str) -> str:
    """The hex of a blend `livery build` derived from the roles (table-rule, caution-fill, ...)."""
    return livery["blends"][key].lstrip("#").upper()


def type_pt(livery: dict, role: str, height_pt: float | None = None) -> float:
    """A text role's size in points on the livery's pptx canvas (livery.json type: whole or half
    points, livery_build.py TYPE and livery.yml type:); on a slide height_pt tall, scaled to it."""
    t = livery["type"]
    pt = t["roles"][role]["pt"]
    return pt if height_pt is None else pt * height_pt / t["canvas"]["h"]


def canvas_scale(livery: dict) -> float:
    """The livery's canvas height over the 540 pt (7.5 in) one the absolute lengths in the
    post-processors were drawn for (indents, pads, gaps): multiply them by it."""
    return livery["type"]["canvas"]["h"] / 540


def half_pt(pt: float) -> float:
    """A size to the nearest half point, as every computed pptx size is (scale=, the deck's step)."""
    return math.floor(pt * 2 + 0.5) / 2   # halves up, not to even


def font_file(livery: dict, family: str, weight: int = 400, italic: bool = False) -> Path:
    """The TTF of one face of a brand.yml font family, resolved against the livery directory."""
    for font in livery["typography"]["fonts"]:
        if font.get("family") != family:
            continue
        for f in font.get("files", []):
            if f.get("weight", 400) == weight and (f.get("style") == "italic") == italic:
                return Path(livery["dir"]) / f["path"]
    raise FileNotFoundError(f"livery {livery['name']}: no {family} file at weight {weight}"
                            f"{' italic' if italic else ''}")


def mark(livery: dict, role: str, kind: str = "logo") -> str | None:
    """The mark (kind logo) or sign-off (kind signoff) a field of this role wears, relative to the
    livery dir; None for a sign-off when the livery has none. A role marks: does not name wears
    primary's."""
    m = livery["marks"].get(role, livery["marks"]["primary"])
    return m.get(kind)


def files(livery: dict) -> list[tuple[str, str]]:
    """Every livery-relative file the data names, with what names it; a logo's or art file's
    same-named .pdf (which LaTeX picks) too, when it exists."""
    d = Path(livery["dir"])
    out = []
    for font in livery["typography"].get("fonts", []):
        out += [(f["path"], f"font {font['family']}") for f in font.get("files", [])]
    images = [(img["path"], f"logo {k}") for k, img in livery["logo"].get("images", {}).items()]
    for role, m in livery.get("marks", {}).items():
        images += [(m[k], f"marks {role} {k}") for k in ("logo", "logo-print", "signoff") if k in m]
    images += [(v, f"art {kind}") for kind, v in (livery.get("art") or {}).items() if isinstance(v, str)]
    for path, what in images:
        out.append((path, what))
        pdf = Path(path).with_suffix(".pdf")
        if pdf.as_posix() != path and (d / pdf).exists():
            out.append((pdf.as_posix(), what + " (pdf)"))
    pptx = livery["pptx"]
    out.append((pptx.get("template", "template.pptx"), "pptx template"))
    if "fonts" in pptx:
        family = pptx["typeface"].lower().replace(" ", "")
        out += [(f"{pptx['fonts']}/{family}-{face}.fntdata", "pptx font blob") for face in ("regular", "bold", "italic", "bolditalic")]
    return out


def engine_version() -> str:
    """The engine's one version, _extension.yml's."""
    import re
    return re.search(r"^version:\s*(\S+)", (Path(__file__).resolve().parent / "_extension.yml").read_text(), re.M)[1]


def deps(d: str) -> list[str]:
    if not (Path(d) / "build" / "livery.json").exists():
        return []
    lv = load(d)
    if lv.get("engine") != engine_version():   # Make.common runs this once a build: the warning's place
        by = f"engine {lv['engine']}" if lv.get("engine") else "an older engine"
        print(f"warning: {d}'s build/ was written by {by}, this is {engine_version()}: rebuild it with "
              f"`livery build {d}`", file=sys.stderr)
    rel = [f"build/livery.{x}" for x in ("json", "sty", "css", "theme", "mplstyle")] + [p for p, _ in files(lv)]
    return sorted({os.path.normpath(Path(d) / p) for p in rel if (Path(d) / p).exists()})


def mono(d: str) -> str:
    """The pptx's code face (pandoc's monofont, the pptx its only reader): pptx.code-typeface when the
    livery names one (an installed face, as the template's), else typography.monospace's family when
    the livery bundles its files (livery_build's mono_font()). HTML and PDF read typography.monospace."""
    if not (Path(d) / "build" / "livery.json").exists():
        return ""
    L = load(d)
    if (L.get("pptx") or {}).get("code-typeface"):
        return L["pptx"]["code-typeface"]
    import livery_build   # beside this file; only this command needs it (and PyYAML)
    return livery_build.mono_font(L)[0]


def figsize(d: str) -> str:
    """charts.figsize.full, the content area in canvas inches, as "<w> <h>"."""
    if not (Path(d) / "build" / "livery.json").exists():
        return ""
    return " ".join(str(v) for v in load(d)["charts"]["figsize"]["full"])


ENGINE = Path(__file__).resolve().parent
QUICKSTART = ENGINE.parents[1] / "decks" / "quickstart"   # the framework's, for check --qa


def check_qa(d: Path) -> bool:
    """The quickstart deck's `make qa` under the livery: LIVERY=<name> for one of the framework's
    liveries, else LIVERY_DIR=<dir>."""
    import subprocess
    if not (QUICKSTART / "Makefile").exists():
        print(f"{d.name}: --qa needs the framework's decks/quickstart, not found at {QUICKSTART}")
        return False
    bundled = (ENGINE.parents[1] / "liveries" / d.name).resolve() == d.resolve()
    which = f"LIVERY={d.name}" if bundled else f"LIVERY_DIR={d.resolve()}"
    ok = subprocess.run(["make", "-C", str(QUICKSTART), "qa", which]).returncode == 0
    print(f"{d.name}: {'ok   ' if ok else 'FAIL '} make -C decks/quickstart qa {which}")
    return ok


def check_cmd(dirs: list[Path], swatch: Path | None, qa: bool, verbose: bool = False) -> int:
    import livery_check
    bad = 0
    for d in dirs:
        ok = livery_check.check([d], swatch or (QUICKSTART / "_qa" if qa else None), verbose)
        if ok and qa:
            ok = check_qa(d)
        bad |= not ok
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="livery", description="Everything a livery owner does (livery.py).")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")
    p = sub.add_parser("new", help="scaffold a livery directory")
    p.add_argument("dir", type=Path)
    p.add_argument("--from", dest="deck", type=Path, metavar="DECK", help="a reference deck (.pptx) to seed it from")
    p.add_argument("--extends", metavar="NAME", help="make a flavor of the livery NAME beside it")
    p = sub.add_parser("inspect", help="report on a reference deck")
    p.add_argument("deck", type=Path)
    p.add_argument("-o", "--output", type=Path, help="write the report here (default: stdout)")
    p.add_argument("--media", type=Path, metavar="DIR", help="extract the deck's pictures into DIR")
    p = sub.add_parser("build", help="write build/ from _brand.yml and livery.yml")
    p.add_argument("dirs", nargs="+", type=Path)
    p.add_argument("--check", action="store_true", help="exit 1 if a committed build/ is stale")
    p = sub.add_parser("template", help="build template.pptx from build/livery.json")
    p.add_argument("dir", type=Path)
    p.add_argument("-o", "--output", type=Path, help="default: <dir>/template.pptx")
    p = sub.add_parser("check", help="the livery's checks")
    p.add_argument("dirs", nargs="+", type=Path)
    p.add_argument("--swatch", type=Path, metavar="DIR", help="write the chart colors' contact sheet into DIR")
    p.add_argument("--qa", action="store_true", help="then the quickstart deck's make qa under the livery")
    p.add_argument("-v", "--verbose", action="store_true", help="print every check, not only warnings and failures")
    p = sub.add_parser("all", help="build, template, check")
    p.add_argument("dirs", nargs="+", type=Path)
    p.add_argument("--qa", action="store_true", help="then the quickstart deck's make qa under the livery")
    p.add_argument("-v", "--verbose", action="store_true", help="print every check, not only warnings and failures")
    p = sub.add_parser("zip", help="the Overleaf project, or with --charts the charts bundle")
    p.add_argument("dir", type=Path)
    p.add_argument("-o", "--output", type=Path, required=True)
    p.add_argument("--charts", action="store_true", help="the charts bundle for matplotlib")
    p.add_argument("--starter", type=Path, help="the Overleaf starter (default: the engine's talk.tex)")
    p.add_argument("--photo", type=Path, help="the Overleaf title and photo-slide picture")
    p = sub.add_parser("schema", help="livery.yml's reference from its schema")
    p.add_argument("--doc", action="store_true", required=True)
    p.add_argument("-o", "--output", type=Path)
    p.add_argument("--check", action="store_true", help="exit 1 if the file is not the schema's")
    for name, help in (("deps", "the files a deck build reads (Make.common)"),
                       ("mono", "the code face's family, or nothing"), ("figsize", "the plots' default size")):
        sub.add_parser(name, help=help).add_argument("dir")
    a = ap.parse_args(argv)

    if a.cmd == "new":
        import livery_new
        livery_new.new(a.dir, a.deck, a.extends)
    elif a.cmd == "inspect":
        import livery_inspect
        livery_inspect.inspect(a.deck, a.output, a.media)
    elif a.cmd == "build":
        import livery_build
        return livery_build.build(a.dirs, a.check)
    elif a.cmd == "template":
        import livery_template
        livery_template.write(a.dir, a.output)
    elif a.cmd == "check":
        return check_cmd(a.dirs, a.swatch, a.qa, a.verbose)
    elif a.cmd == "all":
        import livery_build
        import livery_template
        for d in a.dirs:
            first = not (d / "template.pptx").exists()
            if livery_build.build([d], template_note=False):   # the template comes next
                return 1
            livery_template.write(d)
            if first:   # a new flavor's build named its parent's template; now it has its own
                livery_build.build([d], template_note=False)
        return check_cmd(a.dirs, None, a.qa, a.verbose)
    elif a.cmd == "zip":
        if a.charts:
            if a.starter or a.photo:
                ap.error("--starter and --photo are the Overleaf zip's, not --charts'")
            import mpl_zip
            mpl_zip.write(a.dir, a.output)
        else:
            import overleaf_zip
            overleaf_zip.write(a.dir, a.output, *([a.starter] if a.starter else []), photo=a.photo)
    elif a.cmd == "schema":
        import livery_schema
        return livery_schema.write_doc(a.output or livery_schema.REFERENCE, a.check)
    else:
        print({"deps": lambda d: " ".join(deps(d)), "mono": mono, "figsize": figsize}[a.cmd](a.dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
