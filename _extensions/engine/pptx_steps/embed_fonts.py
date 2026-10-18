#!/usr/bin/env python3
"""Re-embed the livery's typeface into a pandoc-rendered pptx.

Reads the four EOT-subsetted blobs <family>-{regular,bold,italic,bolditalic}.fntdata
from the livery's fonts/pptx/ (embedded once by hand in PowerPoint: Options > Save >
Embed fonts, then extracted; no reliable Python writer exists) and injects them:

  * adds ppt/fonts/<family>-{regular,bold,italic,bolditalic}.fntdata
  * adds a <Default Extension="fntdata" .../> entry to [Content_Types].xml
  * adds four font Relationships to ppt/_rels/presentation.xml.rels
  * adds embedTrueTypeFonts="1" + <p:embeddedFontLst> to ppt/presentation.xml

Idempotent: replaces any existing <p:embeddedFontLst> and skips duplicate
Relationships / Content-Types entries.

Run after `quarto render ... --to pptx`, where LIVERY_DIR or a _livery link names the
livery (utils/livery.py). Exits non-zero (with guidance) if the font blobs are missing."""

import re
import sys
from pathlib import Path

import livery as livery_mod

LIVERY = livery_mod.load()
TYPEFACE = LIVERY["pptx"]["typeface"]
FAMILY = TYPEFACE.lower().replace(" ", "")
FONTS_DIR = Path(LIVERY["dir"]) / LIVERY["pptx"].get("fonts", "fonts/pptx")

VARIANTS = [
    # (xml tag, blob filename, arcname inside pptx)
    (tag, f"{FAMILY}-{tag.lower()}.fntdata", f"ppt/fonts/{FAMILY}-{tag.lower()}.fntdata")
    for tag in ("regular", "bold", "italic", "boldItalic")
]

FONT_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"
FONT_CONTENT_TYPE = "application/x-fontdata"  # matches the original NCAR template

NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"


def check_fonts() -> dict[str, bytes]:
    missing = [b for _, b, _ in VARIANTS if not (FONTS_DIR / b).exists()]
    if missing:
        sys.exit(
            "embed_fonts: missing font blob(s): "
            + ", ".join(missing)
            + f"\n  expected under {FONTS_DIR}/ (livery {LIVERY['name']})"
        )
    return {b: (FONTS_DIR / b).read_bytes() for _, b, _ in VARIANTS}


def patch_content_types(xml: str) -> str:
    if 'Extension="fntdata"' in xml:
        return xml
    entry = f'<Default Extension="fntdata" ContentType="{FONT_CONTENT_TYPE}"/>'
    if '<Default Extension="rels"' in xml:
        return xml.replace(
            '<Default Extension="rels"', entry + '<Default Extension="rels"', 1
        )
    return xml.replace("</Types>", entry + "</Types>")


def next_rids(rels_xml: str, count: int) -> list[str]:
    existing = [int(m) for m in re.findall(r'Id="rId(\d+)"', rels_xml)]
    start = (max(existing) if existing else 0) + 1
    return [f"rId{start + i}" for i in range(count)]


def patch_rels(xml: str, rids: list[str]) -> str:
    # Skip any font rel already pointing at our targets (idempotency).
    existing_targets = set(re.findall(r'Target="(fonts/' + re.escape(FAMILY) + r'-[^"]+\.fntdata)"', xml))
    to_add = []
    for (_, blob, arc), rid in zip(VARIANTS, rids):
        target = f"fonts/{blob}"
        if target in existing_targets:
            continue
        to_add.append(
            f'<Relationship Id="{rid}" '
            f'Type="{FONT_REL_TYPE}" '
            f'Target="{target}"/>'
        )
    if not to_add:
        return xml
    return xml.replace("</Relationships>", "".join(to_add) + "</Relationships>")


def effective_font_rids(rels_xml: str) -> dict[str, str]:
    """Map blob filename → rId, scanning the post-patch rels."""
    out = {}
    for rid, target in re.findall(
        r'<Relationship[^>]+Id="(rId\d+)"[^>]+Type="' + re.escape(FONT_REL_TYPE) + r'"[^>]+Target="fonts/(' + re.escape(FAMILY) + r'-[^"]+\.fntdata)"',
        rels_xml,
    ):
        out[target] = rid
    return out


def build_embedded_font_lst(blob_to_rid: dict[str, str]) -> str:
    children = []
    for tag, blob, _ in VARIANTS:
        rid = blob_to_rid.get(blob)
        if rid is None:
            sys.exit(f"embed_fonts: internal error: no rId for {blob}")
        children.append(f'<p:{tag} r:id="{rid}"/>')
    return (
        "<p:embeddedFontLst>"
        "<p:embeddedFont>"
        f'<p:font typeface="{TYPEFACE}" pitchFamily="2" charset="77"/>'
        + "".join(children)
        + "</p:embeddedFont>"
        "</p:embeddedFontLst>"
    )


def patch_presentation_xml(xml: str, embedded_font_lst: str) -> str:
    # 1. Ensure embedTrueTypeFonts="1" is on the root <p:presentation> element.
    if "embedTrueTypeFonts=" not in xml:
        xml = re.sub(
            r"(<p:presentation\b)([^>]*)>",
            r'\1\2 embedTrueTypeFonts="1">',
            xml,
            count=1,
        )

    # 2. Replace any existing <p:embeddedFontLst>, or insert after <p:notesSz/>.
    if "<p:embeddedFontLst" in xml:
        return re.sub(
            r"<p:embeddedFontLst>.*?</p:embeddedFontLst>",
            embedded_font_lst,
            xml,
            count=1,
            flags=re.DOTALL,
        )

    # <p:notesSz cx=".." cy=".."/> (self-closing). Insert right after it.
    m = re.search(r"<p:notesSz[^/]*/>", xml)
    if not m:
        sys.exit("embed_fonts: couldn't locate <p:notesSz/> in presentation.xml")
    insert_at = m.end()
    return xml[:insert_at] + embedded_font_lst + xml[insert_at:]


def rewrite_parts(parts: dict, blobs: dict[str, bytes]) -> tuple[int, int]:
    # Pre-compute the patched rels so we know which rIds the embeddedFontLst uses.
    rels_xml = parts["ppt/_rels/presentation.xml.rels"].decode("utf-8")
    rids = next_rids(rels_xml, len(VARIANTS))
    rels_xml_patched = patch_rels(rels_xml, rids)
    blob_to_rid = effective_font_rids(rels_xml_patched)

    efl = build_embedded_font_lst(blob_to_rid)

    pres_xml = parts["ppt/presentation.xml"].decode("utf-8")
    pres_xml_patched = patch_presentation_xml(pres_xml, efl)

    ct_xml = parts["[Content_Types].xml"].decode("utf-8")
    ct_xml_patched = patch_content_types(ct_xml)

    existing_arcs = {arc for _, _, arc in VARIANTS if arc in parts}

    for _, _, arc in VARIANTS:   # written fresh below
        parts.pop(arc, None)
    parts["ppt/presentation.xml"] = pres_xml_patched.encode("utf-8")
    parts["ppt/_rels/presentation.xml.rels"] = rels_xml_patched.encode("utf-8")
    parts["[Content_Types].xml"] = ct_xml_patched.encode("utf-8")
    # Inject (or re-inject) the font blobs.
    for _, blob, arc in VARIANTS:
        parts[arc] = blobs[blob]
    return len(VARIANTS), len(existing_arcs)


def run(parts: dict, name: str) -> None:
    """The deck's zip members (name -> bytes), changed in place; name for the message."""
    if "fonts" not in LIVERY["pptx"]:   # a livery that names its typeface and embeds nothing
        print(f"embed_fonts: livery {LIVERY['name']} embeds no fonts (pptx.fonts unset) → {name} unchanged")
        return
    blobs = check_fonts()
    variants, replaced = rewrite_parts(parts, blobs)
    action = "replaced" if replaced else "embedded"
    print(
        f"embed_fonts: {action} {TYPEFACE} "
        f"({variants} variants) → {name}"
    )
