"""A pptx as LibreOffice draws it: the PDF `make qa` checks and `make measure` shoots.

soffice reads no embedded fonts, and a private profile sees none installed: it gets the livery's
bundled faces (copied into the profile's user/fonts), and a typeface the livery names but does not
bundle (cu's Helvetica Neue) is drawn in its bundled stand-in, the base family, or the text would be
measured in a serif; pandoc's Courier (code) in DejaVu Sans Mono, matplotlib's, which advances as
Courier does. A private profile also keeps a running LibreOffice from blocking the default
one. LibreOffice is not PowerPoint: it applies no autofit and substitutes the faces it lacks, so a
box that overflows here may be shrunk there; the checks on its PDF are hints until the numbers
prove quiet (deck_qa.check_pptx). A hidden slide (`show="0"`: a details slide, pptx_steps/details.py)
is drawn like the rest: LibreOffice's export leaves hidden slides out, which would shift every page
after one against its slide, so the copy it reads has them shown.
"""

import os
import re
import shutil
import subprocess
import tempfile
import zipfile

SOFFICE = [shutil.which("soffice"), "/opt/homebrew/bin/soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"]


def soffice():
    """The LibreOffice binary, or None."""
    return next((s for s in SOFFICE if s and os.path.exists(s)), None)


MONO_FAMILY = "DejaVu Sans Mono"   # Courier's stand-in: 0.6 em a character, as Courier advances


def _mono_stand_in():
    """matplotlib's DejaVu Sans Mono (the env's and the image's), or None."""
    try:
        import matplotlib
    except ImportError:
        return None
    path = os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSansMono.ttf")
    return path if os.path.exists(path) else None


SLIDE = re.compile(r"ppt/slides/slide\d+\.xml")
HIDDEN = re.compile(rb'(<p:sld\b[^>]*?)\s+show="0"')   # the slide's own attribute, on its root


def _family(spec):
    return spec if isinstance(spec, str) else (spec or {}).get("family")


def hidden_slides(pptx):
    """How many of the pptx's slides are hidden (`show="0"`)."""
    with zipfile.ZipFile(pptx) as z:
        return sum(bool(HIDDEN.search(z.read(f))) for f in z.namelist() if SLIDE.fullmatch(f))


def to_pdf(pptx, livery, out_dir):
    """<out_dir>/<stem>.pdf from the pptx, or (None, why) when LibreOffice is not installed.
    `livery` is livery.json as the engine's reader loads it (its `dir` names the livery)."""
    exe = soffice()
    if not exe:
        return None, "soffice (LibreOffice) is not installed"
    stem = os.path.splitext(os.path.basename(pptx))[0]
    with tempfile.TemporaryDirectory() as tmp:
        fonts = os.path.join(tmp, "profile", "user", "fonts")
        os.makedirs(fonts)
        bundled = set()
        for font in livery["typography"].get("fonts", []):
            for f in font.get("files", []):
                path = os.path.join(livery["dir"], f["path"])
                if os.path.exists(path):
                    shutil.copy(path, fonts)
                    bundled.add(font.get("family"))
        src, typeface = pptx, (livery.get("pptx") or {}).get("typeface")
        base = _family(livery["typography"].get("base"))
        swaps = []   # (typeface the pptx names, the face drawn for it)
        if typeface and typeface not in bundled and base in bundled:
            swaps.append((typeface, base))
        mono = _mono_stand_in()
        if mono:   # pandoc's Courier, a code block's face: a private profile has none, and a serif is drawn
            shutil.copy(mono, fonts)
            swaps.append(("Courier", MONO_FAMILY))
        if swaps or hidden_slides(pptx):   # a copy: the stand-in faces, every slide shown
            src = os.path.join(tmp, stem + ".pptx")
            with zipfile.ZipFile(pptx) as zin, zipfile.ZipFile(src, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename.endswith(".xml"):
                        for old, new in swaps:
                            data = data.replace(('typeface="%s"' % old).encode(), ('typeface="%s"' % new).encode())
                    if SLIDE.fullmatch(item.filename):
                        data = HIDDEN.sub(rb"\1", data)
                    zout.writestr(item, data)
        subprocess.run([exe, f"-env:UserInstallation=file://{tmp}/profile", "--headless", "--convert-to", "pdf",
                        "--outdir", out_dir, src], check=True, capture_output=True)
    return os.path.join(out_dir, stem + ".pdf"), None
