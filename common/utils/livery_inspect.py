#!/usr/bin/env python3
"""Report on a reference PowerPoint and seed a livery from it (design section 6, step 1).

    livery_inspect.py <reference.pptx> <livery dir> [--media]

Writes <livery dir>/reference/report.md: slide size and aspect, the theme's twelve color
slots and font scheme, every master and layout with its placeholders, pictures and
background, which layout each sample slide uses, and every srgbClr ranked by frequency.
With --media the deck's pictures go to reference/media/ (large; keep them out of git).
Seeds _brand.yml and livery.yml (schema 1, the roles on the theme's slots) when the livery has
none.
"""

import argparse
import collections
import re
import shutil
import sys
import zipfile
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.util import Emu

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"a": A, "p": P}
SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"]


def scheme(theme_xml: bytes) -> tuple[dict, dict]:
    root = etree.fromstring(theme_xml)
    cs = root.find(".//a:clrScheme", NS)
    colors = {}
    for slot in SLOTS:
        el = cs.find(f"a:{slot}/*", NS) if cs is not None else None
        if el is not None:
            colors[slot] = el.get("val") if el.tag.endswith("}srgbClr") else f"system:{el.get('val')} ({el.get('lastClr')})"
    fs = root.find(".//a:fontScheme", NS)
    fonts = {k: fs.find(f"a:{k}Font/a:latin", NS).get("typeface") for k in ("major", "minor")} if fs is not None else {}
    return colors, fonts


def box(sh, W, H) -> str:
    if sh.left is None:
        return "inherits"
    return f"x={sh.left / W:.3f} y={sh.top / H:.3f} w={sh.width / W:.3f} h={sh.height / H:.3f}"


def shape_row(sh, W, H) -> str:
    if sh.is_placeholder:
        pf = sh.placeholder_format
        kind = f"placeholder `{str(pf.type).split(' ')[0]}` idx={pf.idx}"
    else:
        kind = str(sh.shape_type).split(" ")[0].lower() if sh.shape_type is not None else "shape"
        if kind == "picture":
            img = sh.image
            kind = f"picture `{img.filename}` {img.size[0]}x{img.size[1]}px"
    return f"| {kind} | {sh.name} | {box(sh, W, H)} |"


def background(el) -> str:
    bg = el.find("p:cSld/p:bg", NS)
    if bg is None:
        return "inherits"
    s = bg.find(".//a:srgbClr", NS); c = bg.find(".//a:schemeClr", NS)
    return f"#{s.get('val')}" if s is not None else (f"scheme {c.get('val')}" if c is not None else "fill")


def srgb_counts(z: zipfile.ZipFile) -> list[tuple[str, int]]:
    counts = collections.Counter()
    for name in z.namelist():
        if name.startswith("ppt/") and name.endswith(".xml"):
            counts.update(m.upper() for m in re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', z.read(name).decode("utf-8", "replace")))
    return counts.most_common()


def report(ref: Path, prs, z) -> str:
    W, H = prs.slide_width, prs.slide_height
    colors, fonts = scheme(z.read("ppt/theme/theme1.xml"))
    L = [f"# Reference deck: {ref.name}", "",
         f"Written by `livery_inspect.py`; the deck itself is not committed (see the onboarding notes).", "",
         "## Slide", "",
         f"- size {W} x {H} EMU ({Emu(W).inches:.2f} x {Emu(H).inches:.2f} in), aspect {W / H:.4f}"
         f" ({'16:9' if abs(W / H - 16 / 9) < 0.01 else '4:3' if abs(W / H - 4 / 3) < 0.01 else 'other'})",
         f"- {len(prs.slides)} sample slides, {len(prs.slide_masters)} master(s)", "",
         "## Theme", "", "| slot | color |", "|---|---|"]
    L += [f"| {k} | `#{v}` |" if not v.startswith("system") else f"| {k} | {v} |" for k, v in colors.items()]
    L += ["", f"Fonts: major (headings) `{fonts.get('major')}`, minor (body) `{fonts.get('minor')}`.", ""]
    for mi, m in enumerate(prs.slide_masters):
        L += [f"## Master {mi}", "", f"Background: {background(m._element)}.", "",
              "| kind | name | box (fractions of the slide) |", "|---|---|---|"]
        L += [shape_row(sh, W, H) for sh in m.shapes]
        L.append("")
        for lay in m.slide_layouts:
            typ = lay._element.get("type") or "-"
            used = sum(1 for s in prs.slides if s.slide_layout is lay)
            L += [f"### Layout: {lay.name}", "",
                  f"type `{typ}`, background {background(lay._element)}, used by {used} sample slide(s).", "",
                  "| kind | name | box |", "|---|---|---|"]
            L += [shape_row(sh, W, H) for sh in lay.shapes]
            L.append("")
    L += ["## Sample slides", "", "| # | layout | title |", "|---|---|---|"]
    for i, s in enumerate(prs.slides, 1):
        title = s.shapes.title.text_frame.text.strip().replace("\n", " ")[:60] if s.shapes.title is not None else ""
        L.append(f"| {i} | {s.slide_layout.name} | {title} |")
    L += ["", "## Colors used", "", "Every `srgbClr` in the deck, most frequent first.", "", "| color | uses |", "|---|---|"]
    L += [f"| `#{c}` | {n} |" for c, n in srgb_counts(z)[:40]]
    media = [n for n in z.namelist() if n.startswith("ppt/media/")]
    L += ["", "## Media", "", f"{len(media)} files: " + ", ".join(f"`{Path(n).name}` ({z.getinfo(n).file_size // 1024} KB)" for n in media), ""]
    return "\n".join(L)


def seed_brand(colors: dict, fonts: dict) -> str:
    L = ["# Seeded by livery_inspect.py from the reference deck's theme; name the colors and check them",
         "# against the brand guide. Fonts: the scheme's; replace with the brand's files.",
         "meta:", "  name: TODO", "", "color:", "  palette:"]
    for k, v in colors.items():
        if not v.startswith("system") and k not in ("hlink", "folHlink"):
            L.append(f'    {k}: "#{v}"')
    L += ["  primary: dk2", "  secondary: accent1", "  foreground: dk1", "  background: lt1", "",
          "typography:", f"  base: {fonts.get('minor', 'TODO')}", f"  headings: {fonts.get('major', 'TODO')}", "  fonts: []", "",
          "logo:", "  images: {}", "  medium: {light: TODO, dark: TODO}", ""]
    return "\n".join(L)


def seed_livery(name: str) -> str:
    L = ["# yaml-language-server: $schema=../../_extensions/engine/livery.schema.json",
         "# Seeded by livery_inspect.py from the reference deck (reference/report.md); the keys are",
         "# liveries/REFERENCE.md's. livery_template.py builds template.pptx from the data.",
         "schema: 1", f"name: {name}", "extends: null", "", "roles:", "  primary-text: lt1", "  primary-contrast: dk2",
         "  accent: accent2", "  highlight: accent5", "  muted: dk1", "  surface: lt2", "  warning: accent3", "  dark: accent4", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("reference", type=Path)
    ap.add_argument("livery", type=Path)
    ap.add_argument("--media", action="store_true", help="extract the pictures to reference/media/")
    a = ap.parse_args()
    prs = Presentation(str(a.reference))
    with zipfile.ZipFile(a.reference) as z:
        text = report(a.reference, prs, z)
        out = a.livery / "reference"; out.mkdir(parents=True, exist_ok=True)
        (out / "report.md").write_text(text)
        print(f"wrote {out / 'report.md'}")
        if a.media:
            (out / "media").mkdir(exist_ok=True)
            for n in z.namelist():
                if n.startswith("ppt/media/"):
                    (out / "media" / Path(n).name).write_bytes(z.read(n))
            print(f"extracted media to {out / 'media'}")
        colors, fonts = scheme(z.read("ppt/theme/theme1.xml"))
    for fname, content in (("_brand.yml", seed_brand(colors, fonts)), ("livery.yml", seed_livery(a.livery.name))):
        f = a.livery / fname
        if f.exists():
            print(f"kept {f} (exists; the seed is in reference/report.md's terms)")
        else:
            f.write_text(content); print(f"seeded {f}")


if __name__ == "__main__":
    main()
