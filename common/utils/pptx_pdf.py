"""A pptx as LibreOffice draws it: the PDF `make qa` checks and `make measure` shoots.

soffice reads no embedded fonts, and a private profile sees none installed: it gets the livery's
bundled faces (copied into the profile's user/fonts), and a typeface the livery names but does not
bundle (cu's Helvetica Neue) is drawn in its bundled stand-in, the base family, or the text would be
measured in a serif. A private profile also keeps a running LibreOffice from blocking the default
one. LibreOffice is not PowerPoint: it applies no autofit and substitutes the faces it lacks, so a
box that overflows here may be shrunk there; the checks on its PDF are hints until the numbers
prove quiet (deck_qa.check_pptx).
"""

import os
import shutil
import subprocess
import tempfile
import zipfile

SOFFICE = [shutil.which("soffice"), "/opt/homebrew/bin/soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"]


def soffice():
    """The LibreOffice binary, or None."""
    return next((s for s in SOFFICE if s and os.path.exists(s)), None)


def _family(spec):
    return spec if isinstance(spec, str) else (spec or {}).get("family")


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
        if typeface and typeface not in bundled and base in bundled:
            src = os.path.join(tmp, stem + ".pptx")
            old, new = ('typeface="%s"' % typeface).encode(), ('typeface="%s"' % base).encode()
            with zipfile.ZipFile(pptx) as zin, zipfile.ZipFile(src, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    zout.writestr(item, data.replace(old, new) if item.filename.endswith(".xml") else data)
        subprocess.run([exe, f"-env:UserInstallation=file://{tmp}/profile", "--headless", "--convert-to", "pdf",
                        "--outdir", out_dir, src], check=True, capture_output=True)
    return os.path.join(out_dir, stem + ".pdf"), None
