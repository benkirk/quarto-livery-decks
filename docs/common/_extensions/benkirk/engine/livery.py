"""Read a livery's resolved truth, build/livery.json, for the template builder, the checks and
the framework's post-render scripts (which load this file through their own livery.py).

The directory comes from the argument, else $LIVERY_DIR (exported by the framework's
Make.common), else a `_livery` link in the current directory. Generate the file with
livery_build.py."""

import json
import os
from pathlib import Path


def livery_dir(path: str | os.PathLike | None = None) -> Path:
    for candidate in (path, os.environ.get("LIVERY_DIR"), "_livery"):
        if candidate and Path(candidate).is_dir():
            return Path(candidate).resolve()
    raise FileNotFoundError("no livery: pass a directory, export LIVERY_DIR, or run where _livery links")


def load(path: str | os.PathLike | None = None) -> dict:
    d = livery_dir(path)
    f = d / "build" / "livery.json"
    if not f.exists():
        raise FileNotFoundError(f"{f} missing: run livery_build.py {d}")
    data = json.loads(f.read_text())
    data["dir"] = str(d)
    return data


def mix(a: str, b: str, share: float) -> str:
    """Sass mix(): a's share of each channel plus b's remainder, rounded; '#RRGGBB' in and out."""
    pairs = zip(bytes.fromhex(a.lstrip("#")), bytes.fromhex(b.lstrip("#")))
    return "#" + "".join(f"{round(x * share + y * (1 - share)):02X}" for x, y in pairs)


def color(livery: dict, role: str) -> str:
    """A role's hex without '#', as the pptx scripts write it."""
    return livery["roles"][role].lstrip("#").upper()


def scheme(livery: dict, slot: str) -> str:
    """The hex of a theme1.xml scheme slot (dk2, accent4, ...; design section 4)."""
    return livery["pptx"]["scheme"][slot].lstrip("#").upper()


def derived(livery: dict, key: str) -> str:
    """The hex of a blend livery_build.py derived from the roles (table-rule, caution-fill, ...)."""
    return livery["derived"][key].lstrip("#").upper()


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
