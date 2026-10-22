"""Pack one livery with the theme into a pure-XeLaTeX project (an Overleaf zip).

    livery zip <livery dir> -o <zip> [--starter talk.tex] [--photo <file>]

The zip holds the engine's *.sty under _extensions/engine/, liveries/<name>/ with build/livery.sty
and every file LaTeX reads (fonts of any extension, each logo as its .pdf when there is one else
its image, the art; a flavor's inherited ../<parent>/ paths land beside it), a latexmkrc pointing
TeX at both, the starter with its \\usetheme line rewritten to `livery=liveries/<name>,
fonts=bundled` (never the installed-fonts probe: fontconfig by name is too slow for a free Overleaf
compile), and the cookbook, latex/examples/sample.tex (latex/authoring.md), its theme line
rewritten the same way and the files it reads beside it (its photo, the pre-rendered diagrams,
the captured session). The starter's photos: --photo for both the title and the photo slide; else
the livery's art.titlegraphic (the theme's default title photo) on the photo slide and no
\\titlegraphic line; else no photo at all. Compiles with `latexmk -xelatex talk.tex` (or
sample.tex) alone."""

import posixpath
import re
import sys
import zipfile
from pathlib import Path

import livery as livery_mod

ENGINE = Path(__file__).resolve().parent
LATEX = ENGINE.parent.parent / "latex"   # the engine's pure-LaTeX side: the cookbook and what it reads
COOKBOOK = "examples/sample.tex"
# the cookbook's files, as it names them (TEXINPUTS reaches latex/ and latex/examples/ in the tree;
# the zip's root is both)
COOKBOOK_FILES = ["images/wallpaper/mesa_lab.jpg", "examples/diagrams/render.pdf", "examples/diagrams/systems.pdf",
                  "examples/snippets/terminal/whoami.session", "examples/references.bib",
                  *(f"images/gallery-{k}.jpg" for k in range(1, 7))]   # the gallery's: links to the sample deck's
LATEXMKRC = """\
# latexmk reads this file when run from this directory -- Overleaf does.  It
# points TeX at the theme in _extensions/engine/ and at the livery's logos and
# bundled fonts under liveries/; Overleaf has no other way to set them.  The
# engine is not set here: Overleaf's Menu > Compiler (XeLaTeX) overrides it.
$ENV{'TEXINPUTS'} = './_extensions/engine//:./liveries//:' . ($ENV{'TEXINPUTS'} // '');
$ENV{'TTFONTS'}   = './_extensions/engine//:./liveries//:' . ($ENV{'TTFONTS'}   // '');
"""


def livery_files(lv: dict, name: str) -> dict[str, Path]:
    """archive path -> source file: build/livery.sty and what LaTeX reads, the .pdf over its bitmap."""
    d = Path(lv["dir"])
    named = [(p, what) for p, what in livery_mod.files(lv) if not what.startswith("pptx")]
    paths = {p for p, _ in named}
    out = {}
    for p, what in [("build/livery.sty", "livery.sty")] + named:
        if not what.startswith("font") and Path(p).suffix != ".pdf" and Path(p).with_suffix(".pdf").as_posix() in paths:
            continue
        arc = posixpath.normpath(f"liveries/{name}/{p}")
        if not arc.startswith("liveries/"):
            sys.exit(f"{p} ({what}) escapes liveries/: a parent livery must be a sibling directory")
        out[arc] = d / p
    return out


def rewrite_theme(text: str, name: str, what: str) -> str:
    """The deck's \\usetheme line on this livery's bundled fonts."""
    text, n = re.subn(r"^\\usetheme\[[^\]]*\]\{Engine\}", rf"\\usetheme[livery=liveries/{name}, fonts=bundled]{{Engine}}", text, flags=re.M)
    if n != 1:
        sys.exit(f"the {what} has no \\usetheme[...]{{Engine}} line")
    return text


def rewrite_starter(text: str, name: str, photo: str | None, explicit: bool) -> str:
    """The \\usetheme line for this livery; the title and photo-slide pictures as decided."""
    text = rewrite_theme(text, name, "starter")
    # --photo names the title photo too; otherwise the theme supplies art.titlegraphic
    title = f"\\titlegraphic{{\\includegraphics{{{photo}}}}}\n" if explicit else ""
    text, n = re.subn(r"^\\titlegraphic\{.*\}.*\n", lambda m: title, text, flags=re.M)
    if explicit and not n:
        text = text.replace("\\begin{document}", title + "\n\\begin{document}", 1)
    # only the frame options, not the example text in a block body
    def frame(m):
        opts = m.group(1)
        if photo:
            return "\\begin{frame}[" + re.sub(r"enginebg=[^,\]]+", f"enginebg={photo}", opts) + "]"
        opts = ",".join(o for o in opts.split(",") if not o.strip().startswith("enginebg="))
        return "\\begin{frame}[" + opts + "]" if opts else "\\begin{frame}"
    return re.sub(r"^\\begin\{frame\}\[([^\]]*)\]", frame, text, flags=re.M)


def write(livery: Path, out: Path, starter: Path = ENGINE / "talk.tex", photo: Path | None = None):
    """The livery's Overleaf zip: the theme, its files and the starter (default the engine's talk.tex);
    photo is the title and photo-slide picture (default: the livery's art.titlegraphic)."""
    name = livery.name          # as named, not resolved: the framework's liveries/ncar is a link
    lv = livery_mod.load(livery)
    files = {f"_extensions/engine/{s.name}": s for s in sorted(ENGINE.glob("*.sty"))}
    files.update(livery_files(lv, name))
    if photo:
        files[f"images/{photo.name}"] = photo
        shown = f"images/{photo.name}"
    else:
        tg = (lv.get("art") or {}).get("titlegraphic")
        shown = posixpath.normpath(f"liveries/{name}/{tg}") if isinstance(tg, str) else None
    text = rewrite_starter(starter.read_text(), name, shown, bool(photo))
    cookbook = rewrite_theme((LATEX / COOKBOOK).read_text(), name, "cookbook")
    for f in COOKBOOK_FILES:   # at the paths the cookbook names (examples/ is its directory)
        files[f.removeprefix("examples/")] = LATEX / f
    missing = [str(src) for src in files.values() if not src.is_file()]
    if missing:
        sys.exit("missing: " + ", ".join(missing))
    out.unlink(missing_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("talk.tex", text)
        zf.writestr("sample.tex", cookbook)
        zf.writestr("latexmkrc", LATEXMKRC)
        for arc, src in files.items():
            zf.write(src, arc)
    print(f"wrote {out}: {name}, {len(files) + 3} files")
