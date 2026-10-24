"""Resolve a livery (_brand.yml + livery.yml, `extends` applied) into build/livery.{json,sty,css,theme,mplstyle}.

    livery build <livery dir>...          write build/ (committed)
    livery build --check <livery dir>...  exit 1 if a committed build/ is stale

Color names in livery.yml roles resolve against the brand palette; a value starting with '#'
passes through. `extends: <name>` names a sibling livery whose resolved values the child's
override key by key (dicts merge, everything else replaces); the parent's relative paths are
rebased onto the child. `blends` holds the theme's blends of two roles (BLENDS), computed
here unless livery.yml's `blends:` sets the key. livery.json is the one truth (Lua and Python read it);
livery.sty is what engine_livery.sty inputs (overrides/livery-extra.sty of the livery and its
ancestors appended); livery.css what engine-revealjs.lua attaches; livery.theme is pandoc's
highlight theme, engine.theme with the roles filled in; livery.mplstyle matplotlib's style (the
chart colors of livery.json `charts`, emit_mplstyle()). `marks` names the mark and sign-off
for each field by its role (MARK_ROLES); `installed-fonts` names installed faces to prefer;
`compositions` the title, closing, section and feature slides as boxes (compositions()).
"""

import json
import math
import os
import re
import sys
from fractions import Fraction
from pathlib import Path

import yaml

import livery as livery_mod   # the reader: the version and the color math, one copy
import livery_charts

# the engine's one version, _extension.yml's (a release's tag; build/livery.json records it)
ENGINE_VERSION = livery_mod.engine_version()

# (key, role a, role b, share of a): the theme's recipes, engine-revealjs.scss `table` and
# `.engine-caution`, beamerinnerthemeEngine.sty `enginecautionfill`
BLENDS = [
    ("table-rule", "foreground", "surface", 0.20),
    ("table-band", "surface", "background", 0.60),
    ("caution-fill", "warning", "background", 0.18),
    ("alert-text", "accent", "dark", 0.72),
    ("rule", "foreground", "surface", 0.30),
    # the inverted content slide ({.brand-dark}): its hairline and table rules, its banded rows, its
    # inline code's field and its muted text, on-dark mixed toward the dark role
    ("dark-rule", "on-dark", "dark", 0.25),
    ("dark-band", "on-dark", "dark", 0.06),
    ("dark-code", "on-dark", "dark", 0.12),
    ("dark-muted", "on-dark", "dark", 0.70),
]
# blend -> the color beamerinnerthemeEngine.sty mixes for it itself, unless livery.sty defines it first
BEAMER_BLENDS = {"table-band": "enginetableband", "table-rule": "enginetablerule", "caution-fill": "enginecautionfill"}
# livery role -> the LaTeX color the themes read (the 14 roles; livery.json latex.roles carries them
# and the blends' names to the beamer filter); on-dark is derived unless a livery names it
ROLE_TEX = {"primary": "BrandPrimary", "primary-text": "BrandPrimaryText",
            "primary-contrast": "BrandPrimaryContrast", "secondary": "BrandSecondary",
            "accent": "BrandAccent", "highlight": "BrandHighlight", "foreground": "BrandText", "background": "BrandBackground",
            "muted": "BrandMuted", "surface": "BrandSurface", "warning": "BrandWarning", "dark": "BrandDark",
            "code-text": "BrandCodeText", "on-dark": "BrandOnDark"}
W, H = 1600, 900   # revealjs slide pixels (engine-revealjs.scss)
# art.<kind> files: backgrounds per slide kind, and titlegraphic, the title photo a deck sets none of
ART_KINDS = ("title", "title-light", "section", "closing", "content", "titlegraphic")
COMP_ART = ("title", "title-light", "section", "closing", "content")   # the kinds a composition's art names
# the title slide's composition (title: in livery.yml) when it is the band: fractions of the slide,
# roles for the colors; its strip wears marks.<field>
BAND = {"top": 0.27, "bottom": 0.72, "split": 0.62, "band": "primary", "field": "dark", "field-text": "background"}
# theme1.xml slot -> role, the slot contract of design section 4 (livery_template.py writes it)
SLOT_ROLES = {"dk1": "foreground", "lt1": "background", "dk2": "primary", "lt2": "surface",
              "accent1": "secondary", "accent2": "highlight", "accent3": "dark", "accent4": "accent",
              "accent5": "warning", "accent6": "primary-contrast", "hlink": "primary", "folHlink": "highlight"}
# the content slides' title (livery.yml frametitle:): its alignment beside the mark, the accent tab at the
# paper's edge, the hairline under it, and the band as fractions of the height (44, 70 and 130 px of
# 900): the title centered in top..top+height (a taller one grows down), the hairline at rule-y,
# rule-width thick (0.4 pt of the PDF's 254 pt paper, 1.4 px of 900; Ben's pick from the side-by-side)
# in rule-color (a role, blend or hex; resolved to hex in the json)
FRAMETITLE = {"align": "left", "symmetric": False, "tab": True, "rule": True, "top": 0.0489, "height": 0.0778,
              "rule-y": 0.1444, "rule-width": 0.0016, "rule-color": "rule", "color": "foreground"}
TITLE_GAP = 0.025   # a content title's gap beside the mark, of the width (HTML's 40 px of 1600)
BODY_GAP = 0.0223   # the content body's top under the hairline, or under a taller mark: 20 px of 900 (0.1444 + it rounds to the 0.1667 the formats drew)
# the divider stack's gaps (livery.yml section:), em of the element above the gap: the eyebrow's under
# it (of the eyebrow type), the subtitle's above it (of the section subtitle type). These and the note
# and attribution gaps are the PDF's old ex gaps as em (Ben's pick from the side-by-side, 2026-10-22)
SECTION = {"eyebrow-gap": 0.33, "subtitle-gap": 0.66}
BODY_BOTTOM = 0.9222   # its foot (the pptx body placeholder's; 70 px of 900 above the edge, as HTML pads)
# the fields every livery has: content slides on the background role, the colored fields (dividers,
# the cover title and closing, feature covers) on primary, the inverted content slide on dark (primary's
# marks unless the livery names its own, as every reader fell back to); a band title adds its field role
MARK_ROLES = ("background", "primary", "dark")
CORNERS = ("top-left", "top-right", "bottom-left", "bottom-right")   # where a content slide's marks sit
# a corner's mark (geometry.marks.<corner>): its height, and its distance from its top or bottom edge
# (the content mark's 58 and 48 px of 900; a foot lockup's 27); a side inset absent is the margin
MARK = {"height": 0.0644, "top": 0.0533, "bottom": 0.03}
MARK_HEIGHTS = ("title-height", "section-height", "closing-height")   # the logo entry's, the compositions' marks
# Type: every text role's size in points on the pptx canvas, with its leading. The default canvas is
# 13.333 x 7.5 in (960 x 540 pt); the default sizes are the NSF NCAR template's guidance (body 12 pt
# on its 405 pt slide, levels 12/11/10/9/8, page title 20, cover title 22, ...) carried onto that
# canvas and rounded to whole points. A livery states its own in livery.yml type: (points on its
# pptx.size canvas); a role it leaves out is the default, scaled by the canvas and the body and
# rounded to the half point. HTML and beamer take the same sizes as fractions of the slide height
# (livery.css --engine-type-*, livery.sty \engine@type@*), so the formats fit and overflow alike.
CANVAS = (960, 540)   # pt
TYPE = {"body": (16, 1.4), "subhead": (20, 1.2), "frametitle": (27, 1.15), "table": (13, 1.3),
        "code": (11, 1.3), "caption": (11, 1.3), "footnote": (11, 1.35), "title": (29, 1.12),
        "subtitle": (20, 1.3), "date": (11, 1.2), "author": (16, 1.3), "institute": (16, 1.3),
        "fineprint": (7, 1.4), "section": (40, 1.08), "sectionsubtitle": (20, 1.3), "eyebrow": (11, 1.2),
        "closing": (40, 1.08), "pagenumber": (9, 1.2), "footer": (9, 1.2), "marking": (9, 1.2),
        "display": (40, 1.08), "quote": (24, 1.3)}   # display: a card's big number ([$20M]{.big}); quote: a quote block's text
LEVELS = (16, 15, 13, 12, 11)   # the body's five list levels, the first the body itself
# the roles that scale with the body when a livery leaves them out (the rest scale with the canvas)
BODY_ROLES = ("subhead", "table", "code", "caption", "footnote", "quote")
TRACKING = 0.08   # small caps' letter spacing (type.tracking), em of the run's size, every format: above 0.08
                  # pdftotext splits the PDF's tracked words into letters (Poppins Bold at 8 pt)
# the compositions every livery.json carries (compositions()), and the keys each one has (null when absent)
COMPOSITIONS = ("title", "title-photo", "title-light", "title-photo-light", "title-band",
                "closing", "closing-light", "closing-band", "section", "feature")
FEATURE_STYLES = ("bar", "cover")   # feature.style: the photo under a bar and panel, or the cover
COMP_KEYS = ("field", "art", "photo", "band", "waves", "bar", "panel", "mark", "signoff", "column", "byline", "fineprint",
             "eyebrow")
COVERS = ("title", "title-photo", "title-light", "title-photo-light", "title-band")   # the compositions with a byline
ELEMENTS = ("date", "title", "subtitle", "author", "institute")   # a cover's text, in the column's default order
BYLINE = ("author", "institute", "date")   # a byline's default elements
# Boxes (livery.yml boxes:): one set of numbers for every format's columns and boxes. Units: gap of the
# slide's width; bar, rule, outline, radius, line, badge and dot of its height; pad [vertical,
# horizontal] in em of the body type; tint a share of the role over the background; the colors a
# role, a blend, a palette name or a hex (hex in livery.json, as marking's). A livery's block merges
# over these one box at a time.
BOXES = {
    "columns": {"gap": 0.03, "rule": 0},   # rule: its width, 0 for none
    "caution": {"bar": 0.0089, "pad": [0.55, 0.9]},   # 8 px of 900, HTML's
    "panel": {"pad": [0.6, 0.9]},   # the feature panel
    "lead": {"fill": "surface", "bar": 0.0089, "bar-color": "accent", "pad": [0.55, 0.9]},
    # the agenda slide: its section numbers' color and the current section's title's (text on the content
    # background: primary-contrast reads there on every livery, the eyebrow and primary not); gap the
    # space above each row and number-width the number column, em of the body (HTML's 0.55em, 2em)
    "agenda": {"number-color": "primary-contrast", "current-color": "primary-contrast", "gap": 0.55, "number-width": 2},
    "quote": {"bar": 0.0089, "bar-color": "primary-contrast", "pad": [0.3, 1.0],   # a quote block: a bar, no fill,
              "family": None, "style": "normal",   # its lines' face: a typography.fonts family (null: the body's), its style
              "attribution-gap": 0.5},   # the attribution's distance under the lines, em of the caption type
    "note": {"gap": 0.3},   # a ::: note under a figure or table: its distance under it, em of the caption type
    # (primary-contrast: a thin bar must read on the background, and secondary does not on every livery)
    "card": {"fill": "background", "radius": 0, "outline": 0.0033, "outline-color": "highlight",
             "border": 0.0016, "border-color": "rule",   # every card's hairline (a pick's outline replaces it; none on a solid card)
             "pad": [0.5, 0.8], "head-pad": [0.35, 0.8],
             "roles": ["primary", "secondary", "accent"]},   # a card without role=: by its place in the row
    "strip": {"tint": 0.18, "pad": [0.3, 0.8], "gap": 0.3},   # 0.18: caution-fill's share (BLENDS), one tint recipe;
                                                            # gap: above and below it, em of the body
    "status": {"done": "highlight", "warn": "warning", "fail": "accent"},   # the ✓ ⚠ ✗ glyphs
    # steps and timelines: line, badge and dot of the height (the rail's thickness, a step's badge's
    # and a milestone's dot's diameter); fill a cell behind each item, null for none
    # and a milestone's dot's diameter; ring a pending dot's stroke, of the dot); role the marks' color
    # when the div names no role= (primary-contrast: a small mark must read on the background)
    "rail": {"line": 0.004, "line-color": "rule", "badge": 0.05, "dot": 0.02, "ring": 0.2, "role": "primary-contrast",
             "fill": None, "pad": [0.4, 0.4]},
    # image galleries: gap between the cells, both ways, of the width (a close wall of pictures: the
    # columns' 0.03 is loose); pad the cell's inset and the caption's distance under its picture; fill a cell
    # behind each picture and caption, null for none
    "gallery": {"gap": 0.006, "pad": [0.15, 0.15], "fill": None},
    # the references slide's list (a deck's bibliography): each entry's hanging indent and the gap
    # above it, em of the footnote type it is set in
    "references": {"hang": 1.5, "gap": 0.4},
    # the slide footnotes (†, ‡, § and ¶ paragraphs, ^[...] notes) at the slide's foot: the short rule above
    # them (rule its thickness of the height, rule-length of the width, rule-color a role, blend or hex),
    # width of the text width, and in em of the footnote type the gap under the rule, the marker's hang
    # and the step between entries; the pptx styles them in place (hang, gap, step; no rule)
    "footnote": {"rule": 0.0022, "rule-length": 0.075, "rule-color": "rule", "width": 0.6, "gap": 0.55, "hang": 0.9, "step": 0.3},
}
# a box's color keys (a role, a blend, a palette name or a hex; null, where the schema allows it, for none)
BOX_COLORS = {"lead": ("fill", "bar-color"), "quote": ("bar-color",), "agenda": ("number-color", "current-color"), "card": ("fill", "outline-color", "border-color"), "status": ("done", "warn", "fail"),
              "rail": ("line-color", "fill"), "gallery": ("fill",), "footnote": ("rule-color",)}
# installed-fonts faces, and how a bare family string names them (full name, PostScript name)
FACES = {"regular": ("", ""), "bold": (" Bold", "-Bold"), "italic": (" Italic", "-Italic"),
         "bolditalic": (" Bold Italic", "-BoldItalic")}
FACE_KEYS = ("regular", "bold", "italic", "bolditalic", "semibold")


def merge(base, over):
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            out[k] = merge(base.get(k), v) if k in base else v
        return out
    return over


def rebase(data: dict, parent: Path, child: Path) -> dict:
    """The parent's relative file paths, written relative to the child's directory."""
    rel = lambda p: os.path.relpath(parent / p, child) if not os.path.isabs(p) else p
    brand = data.get("brand", {})
    for font in brand.get("typography", {}).get("fonts", []):
        for f in font.get("files", []):
            f["path"] = rel(f["path"])
    for img in brand.get("logo", {}).get("images", {}).values():
        img["path"] = rel(img["path"])
    art = data.get("art", {})
    for kind in ART_KINDS:   # static art files; waves are data
        if isinstance(art.get(kind), str):
            art[kind] = rel(art[kind])
    pptx = data.get("pptx", {})
    for k in ("template", "fonts"):
        if k in pptx:   # the child's own file when it has one (livery_template.py builds every livery's)
            pptx[k] = pptx[k] if (child / pptx[k]).exists() else rel(pptx[k])
    return data


def schema():
    """livery_schema.py, loaded once, when a livery is first read."""
    global _schema
    if _schema is None:
        import livery_schema as _schema   # when a livery is read: `livery mono` and the zips need no jsonschema
    return _schema


_schema = None


def read(d: Path) -> dict:
    brand = yaml.safe_load((d / "_brand.yml").read_text()) or {}
    knobs = yaml.safe_load((d / "livery.yml").read_text()) or {}
    errors = schema().check(knobs, brand, d)   # each file as written, before extends merges
    if errors:
        sys.exit("\n".join(errors))
    merged = {"brand": brand, **{k: v for k, v in knobs.items() if k != "extends"}}
    parent = knobs.get("extends")
    if parent:   # pptx.scheme holds only explicit overrides; resolve() fills the rest from the roles
        merged = merge(rebase(read(d.parent / parent), d.parent / parent, d), merged)
    return merged


def resolve(d: Path) -> tuple[dict, dict]:
    """(livery.json content, the roles' source names for livery.sty's \\colorlet lines)."""
    data = read(d)
    palette = {k: str(v).upper() for k, v in data["brand"].get("color", {}).get("palette", {}).items()}

    def hex_of(name, where):   # where: the key, as the schema's errors name it
        if isinstance(name, str) and name.startswith("#"):
            return name.upper()
        if name in palette:
            return palette[name]
        sys.exit(f"{d / where[0]}: {where[1]}: {name!r} is neither a palette name nor a hex value "
                 "(_brand.yml color.palette)")

    color = data["brand"].get("color", {})
    sources = {k: color[k] for k in ("primary", "secondary", "foreground", "background") if k in color}
    sources.update(data.get("roles", {}))
    if "dark" in sources:   # code text: the dark role unless a livery says otherwise (a dark livery's dark is a field)
        sources.setdefault("code-text", sources["dark"])
    given = data.get("roles", {})
    def role_key(k):   # a role's key: livery.yml's roles, else the brand's color, else code-text's dark
        if k in given:
            return ("livery.yml", f"roles.{k}")
        return ("_brand.yml", f"color.{k}") if k in color else ("livery.yml", "roles.dark")
    roles = {k: hex_of(v, role_key(k)) for k, v in sources.items()}
    if "on-dark" not in roles and {"dark", "background", "foreground"} <= set(roles):
        # text on the dark role (the feature panel and bar, a .brand-dark slide): whichever of the
        # background and the foreground reads better on it, unless a livery names one (roles.on-dark)
        lighter = max(("background", "foreground"), key=lambda r: livery_mod.contrast(roles[r], roles["dark"]))
        roles["on-dark"], sources["on-dark"] = roles[lighter], sources[lighter]
    blends = {k: livery_mod.mix(roles[a], roles[b], share) for k, a, b, share in BLENDS if a in roles and b in roles}
    blends.update({k: hex_of(v, ("livery.yml", f"blends.{k}")) for k, v in data.get("blends", {}).items()})
    out = {
        "engine": ENGINE_VERSION,   # the engine that wrote it (Make.common warns when it is another)
        "schema": data["schema"],   # the livery.yml schema it was written for
        "name": data.get("name", d.name),
        "palette": palette,
        "roles": roles,
        "blends": blends,
        # dark: light text on a dark background (content slides); the formats add what that needs
        "mode": "dark" if livery_mod.luminance(roles["background"]) < livery_mod.luminance(roles["foreground"]) else "light",
        "typography": data["brand"].get("typography", {}),
        "logo": data["brand"].get("logo", {}),
    }
    for key in ("geometry", "section", "art", "pptx", "latex"):
        if key in data:
            out[key] = data[key]
    out["section"] = {**SECTION, **(data.get("section") or {})}   # the divider stack's gaps always in the json
    # the TeX name of each role and blend (livery.sty defines them, and carries this table as
    # \engine@role@<name> for a card's or strip's role=; the filters check a role= against it)
    out.setdefault("latex", {})["roles"] = {**{r: t for r, t in ROLE_TEX.items() if r in roles},
                                            **{b: tex_name("brand-" + b, {}) for b in blends}}
    g = out.setdefault("geometry", {})   # the margin, a {.wide} slide's side margin, and the body's foot
    g.setdefault("margin", 0.06)
    g.setdefault("wide-margin", round(g["margin"] / 2, 4))
    g.setdefault("body-bottom", BODY_BOTTOM)
    out["frametitle"] = {**FRAMETITLE, **(data.get("frametitle") or {})}
    if out["frametitle"]["align"] not in ("left", "center"):
        sys.exit(f"{d.name}: frametitle.align {out['frametitle']['align']!r} is not left or center")
    rc = out["frametitle"]["rule-color"]   # the hairline's color as hex: a role, a blend (the default) or a palette name
    out["frametitle"]["rule-color"] = roles.get(rc) or blends.get(rc) or hex_of(rc, ("livery.yml", "frametitle.rule-color"))
    tc = out["frametitle"]["color"]   # the title's color as hex: a role (the body text's by default), a blend or a palette name
    out["frametitle"]["color"] = roles.get(tc) or blends.get(tc) or hex_of(tc, ("livery.yml", "frametitle.color"))
    g["marks"] = corner_marks(d.name, g.get("marks") or {})
    # the body's top (derived, not a key): BODY_GAP under the hairline, or under a taller mark in a top corner
    below = max([e["top"] + e["height"] for c, e in g["marks"].items() if e and c.startswith("top")], default=0)
    out["frametitle"]["body"] = round(max(out["frametitle"]["rule-y"], below) + BODY_GAP, 4)
    v = g.get("pagenumber", {}).get("corner")
    if v is not None and v not in ("bottom-left", "bottom-right"):
        sys.exit(f"{d.name}: geometry.pagenumber.corner {v!r} is not one of ('bottom-left', 'bottom-right')")
    if "title" in data:   # only when set, so a livery without it keeps its build/ unchanged
        out["title"] = band(d.name, data["title"], out)
    out["marks"] = marks(d.name, data, out)
    out["boxes"] = boxes(data.get("boxes") or {},   # its colors as hex, as marking's (a blend too: the rail's rule)
                         lambda c, k: roles.get(c) or blends.get(c) or hex_of(c, ("livery.yml", f"boxes.{k}")), roles)
    qf = out["boxes"]["quote"]["family"]   # a face every format draws: one the livery bundles
    if qf is not None and not family_files(out, qf):
        sys.exit(f"livery.yml: boxes.quote.family: {qf!r} is not a typography.fonts family with files")
    # derived, not yml keys: the content body's box (the template's placeholder, the plots' size) and
    # the Two Content column's width (the template's halves, the shares' reference in columns.py)
    m, top = g["margin"], out["frametitle"]["body"]
    g["body"] = [m, top, round(1 - 2 * m, 4), round(g["body-bottom"] - top, 4)]
    g["half"] = round((1 - 2 * m - out["boxes"]["columns"]["gap"]) / 2, 4)
    b = data.get("bullets")   # list glyphs per level; null keeps each format's own shapes
    out["bullets"] = None if not b else {
        "glyphs": list(b["glyphs"]),
        "color": roles.get(b.get("color", "primary-contrast")) or hex_of(b["color"], ("livery.yml", "bullets.color"))}
    out["compositions"] = compositions(d.name, data, out)
    out["type"] = type_scale(d.name, data)
    out["furniture"] = furniture(out)
    out["marking"] = markings(d.name, data.get("marking") or {}, out,   # colors as hex: a role, a palette name or a hex
                              lambda c, k: roles.get(c) or hex_of(c, ("livery.yml", f"marking.{k}")))
    try:   # the chart colors, per mode (livery_charts.py; livery.yml charts:)
        out["charts"] = livery_charts.charts(out, data.get("charts"))
    except ValueError as e:
        sys.exit(f"{d.name}: {e}")
    if "installed-fonts" in data:
        out["installed-fonts"] = installed_fonts(d.name, data["installed-fonts"])
    out.setdefault("pptx", {})
    # the slot contract, from the roles; a livery's own pptx.scheme overrides slot by slot
    scheme = {slot: roles[role] for slot, role in SLOT_ROLES.items() if role in roles}
    scheme.update({k: hex_of(v, ("livery.yml", f"pptx.scheme.{k}")) for k, v in out["pptx"].get("scheme", {}).items()})
    out["pptx"]["scheme"] = scheme
    return out, sources


def corner_marks(name: str, spec: dict) -> dict:
    """geometry.marks resolved: every CORNERS key, null or {mark, height, top|bottom, aspect, inset?,
    light?, dark?, and on the logo's entry its *-height keys} (a flavor's entry merged over its
    parent's; null drops one). mark names the image a corner wears ([a-z]+, once per livery: marks:
    keys it per role), aspect its width over its height; a top corner's distance is top, a bottom
    one's bottom."""
    res, seen = {}, {}
    for corner in CORNERS:
        e = spec.get(corner)
        if e is None:
            res[corner] = None
            continue
        where = f"{name}: geometry.marks.{corner}"
        side, other = ("top", "bottom") if corner.startswith("top") else ("bottom", "top")
        for k in ("mark", "aspect"):   # required once the parent's entry is merged in (not in the schema: a
            if k not in e:              # flavor's entry may override one key)
                sys.exit(f"{where}.{k} is required")
        if not re.fullmatch(r"[a-z]+", e["mark"]):   # it becomes TeX control-sequence and CSS names
            sys.exit(f"{where}.mark: {e['mark']!r} is lower-case letters only")
        if other in e:
            sys.exit(f"{where}: a {side} corner's distance is {side}, not {other}")
        if e["mark"] in seen:
            sys.exit(f"{where}.mark: {e['mark']!r} is already geometry.marks.{seen[e['mark']]}'s")
        if e["mark"] != "logo" and (bad := [k for k in MARK_HEIGHTS if k in e]):
            sys.exit(f"{where}: {bad} belong to the entry whose mark is logo")
        seen[e["mark"]] = corner
        res[corner] = {"mark": e["mark"], "height": e.get("height", MARK["height"]), side: e.get(side, MARK[side]),
                       **{k: v for k, v in e.items() if k not in ("mark", "height", side)}}
    return res


def mark_entry(g: dict, mark: str) -> dict | None:
    """The corner entry (geometry.marks, resolved) that wears this mark, or None."""
    return next((e for e in g["marks"].values() if e and e["mark"] == mark), None)


def title_room(out: dict) -> tuple[float, float]:
    """The content title's room beside the marks, (left, right) of the width past the margin: per top
    corner its inset, its mark's width and TITLE_GAP less the margin, on its side; frametitle.symmetric
    gives both sides the larger (a centered title on the slide's center). Every drawer of the title
    reads it: furniture() (the pptx master, slide_layout), emit_css; the beamer theme restates it on
    the marks it measures."""
    return tuple(corner_room(out, c) if c else 0 for c in title_corners(out))


def corner_room(out: dict, corner: str) -> float:
    """A top corner's room past the margin: its inset, its mark's width and TITLE_GAP, less the margin."""
    g = out["geometry"]; e = g["marks"][corner]
    cw, ch = (out["type"]["canvas"][k] * 12700 for k in ("w", "h"))   # the canvas in EMU: a mark's width is its height's
    return max(0, e.get("inset", g["margin"]) + e["height"] * e["aspect"] * ch / cw + TITLE_GAP - g["margin"])


def title_corners(out: dict) -> tuple[str | None, str | None]:
    """The top corner whose mark each side of the content title gives way to, (left, right): its own,
    else none; under frametitle.symmetric both sides the wider room's (title_room())."""
    own = tuple(c if out["geometry"]["marks"][c] else None for c in ("top-left", "top-right"))
    if not out["frametitle"].get("symmetric") or own == (None, None):
        return own
    wider = max((c for c in own if c), key=lambda c: corner_room(out, c))
    return wider, wider


def furniture(out: dict) -> dict:
    """A content slide's furniture, the boxes [x, y, w, h] in slide fractions (y down) every drawer of
    it reads (livery_template.master() and slide_layout.draw_dark()): the title tab (null without
    one), the hairline (y its center line, h its width; null without one), the title's box (beside the
    marks, title_room()), and the marks by corner, {mark: name, box} or null (geometry.marks). Not
    rounded: the template's EMUs come from them, as they did from geometry and frametitle, so they
    must not move. Derived, not a livery.yml key."""
    g, ft = out["geometry"], out["frametitle"]
    cw, ch = (out["type"]["canvas"][k] * 12700 for k in ("w", "h"))
    m = g["margin"]
    left, right = title_room(out)
    marks = dict.fromkeys(CORNERS)
    for corner, e in g["marks"].items():
        if e:
            h = e["height"]; w = h * e["aspect"] * ch / cw
            inset = e.get("inset", m)   # the mark's distance from its side edge
            y = e["top"] if corner.startswith("top") else 1 - e["bottom"] - h
            marks[corner] = {"mark": e["mark"], "box": [inset if corner.endswith("left") else 1 - inset - w, y, w, h]}
    return {"tab": [0, ft["top"], g["tab-width"], ft["height"]] if ft.get("tab", True) else None,
            "rule": [m, ft["rule-y"], 1 - 2 * m, ft["rule-width"]] if ft.get("rule", True) else None,
            "title": [m + left, ft["top"], 1 - 2 * m - left - right, ft["height"]],
            "marks": marks}


def markings(name: str, spec: dict, out: dict, hexof) -> list:
    """The marking strips (livery.yml marking:, a map of named strips; null drops a parent's), in the
    livery's order, each resolved with its name, box, fill and text color as hex (hexof: a role, a
    palette name or a hex to its hex, given the key's path; every drawer then reads a hex), size in
    points (the marking role's by default) and leading. A livery without one gets a text-less
    `banner`, so a deck's marking: shows under any livery. A strip's text is the deck's marking:,
    else this default (None: no strip)."""
    role = out["type"]["roles"]["marking"]
    res = []
    for n, m in (spec or {"banner": {}}).items():
        if m is None:
            continue
        if not re.fullmatch(r"[a-z]+", n):   # it becomes TeX control-sequence and CSS class names
            sys.exit(f"{name}: marking.{n}: a strip's name is lower-case letters only")
        m = {"text": None, "edge": "top", "offset": 0.004, "width": 0.8, "height": 0.03, "align": "center",
             "fill": None, "bold": False, **m}
        m.setdefault("color", "primary-text" if m["fill"] else "muted")   # fill and color: two knobs
        m["color"] = hexof(m["color"], f"{n}.color")
        if m["fill"]:
            m["fill"] = hexof(m["fill"], f"{n}.fill")
        margin = out["geometry"]["margin"]
        x = {"center": (1 - m["width"]) / 2, "left": margin, "right": 1 - margin - m["width"]}[m["align"]]
        y = m["offset"] if m["edge"] == "top" else 1 - m["offset"] - m["height"]
        m["box"] = [round(x, 4), round(y, 4), m["width"], m["height"]]
        m["size"] = half(m["size"]) if m.get("size") is not None else role["pt"]
        res.append({"name": n, **m, "leading": role["leading"]})
    return res


def boxes(b: dict, hexof, roles=()) -> dict:
    """The boxes: block resolved: BOXES with the livery's keys over them, box by box, the colors as hex
    (hexof: a role, a palette name or a hex to its hex, given the key's path under boxes)."""
    out = {}
    for box, defaults in BOXES.items():
        v = {**defaults, **(b.get(box) or {})}
        for k in BOX_COLORS.get(box, ()):
            v[k] = None if v[k] is None else hexof(v[k], f"{box}.{k}")
        for i, r in enumerate(v.get("roles", [])):   # role names: every format names the role's own color
            hexof(r, f"{box}.roles[{i}]")
            if roles and (r.startswith("#") or r not in roles):
                sys.exit(f"livery.yml: boxes.{box}.roles[{i}]: {r!r} is not a role")
        if "role" in v:   # a role or blend name, kept as a name (the rail's default: role= resolves through it)
            hexof(v["role"], f"{box}.role")
            if v["role"].startswith("#"):
                sys.exit(f"livery.yml: boxes.{box}.role: {v['role']!r} is a hex, not a role or blend")
        out[box] = v
    return out


def half(v: float) -> float:
    """v to the nearest half point (an int when it is a whole one, so the json reads 12, not 12.0)."""
    v = math.floor(v * 2 + 0.5) / 2   # halves up, not to even (16.25 is 16.5)
    return int(v) if v == int(v) else v


def type_scale(name: str, data: dict) -> dict:
    """The type: block resolved: the canvas (pt, from pptx.size in inches), every role's size in
    points with its ratio to the body and its leading, the five list levels, and the body as a
    fraction of the canvas height (beamer's \\engine@type@frac)."""
    size = (data.get("pptx") or {}).get("size")
    if size is None:
        cw, ch = CANVAS
    else:
        if not (isinstance(size, list) and len(size) == 2 and all(isinstance(v, (int, float)) and v > 0 for v in size)):
            sys.exit(f"{name}: pptx.size {size!r} is not [width, height] in inches")
        cw, ch = round(size[0] * 72), round(size[1] * 72)   # whole points: 13.333 in is 960 pt
    t = data.get("type") or {}
    for k in sorted(set(t) - set(TYPE) - {"levels", "tracking"}):
        print(f"warning: {name}: unknown type: role {k!r} (ignored)", file=sys.stderr)
    tracking = t.get("tracking", TRACKING)   # every small-caps run's letter spacing, em
    if not (isinstance(tracking, (int, float)) and tracking >= 0):
        sys.exit(f"{name}: type.tracking {tracking!r} is not an em length")
    canvas = ch / CANVAS[1]
    body = float(t.get("body", TYPE["body"][0] * canvas))
    by_body = body / TYPE["body"][0]
    pts = {}
    for role, (pt, _) in TYPE.items():
        v = t.get(role)
        if v is not None and not (isinstance(v, (int, float)) and v > 0):
            sys.exit(f"{name}: type.{role} {v!r} is not a size in points")
        pts[role] = half(v if v is not None else pt * (by_body if role in BODY_ROLES else canvas))
    pts["body"] = half(body)
    levels = t.get("levels")
    if levels is None:
        levels = [pts["body"]] + [half(p * by_body) for p in LEVELS[1:]]
    elif not (isinstance(levels, list) and len(levels) == len(LEVELS) and all(isinstance(v, (int, float)) and v > 0 for v in levels)):
        sys.exit(f"{name}: type.levels {levels!r} is not {len(LEVELS)} sizes in points")
    given = [(r, t[r]) for r in TYPE if r in t] + [(f"levels[{i}]", v) for i, v in enumerate(t.get("levels") or [])]
    for role, v in given:   # sizes are whole or half points, so a pasted slide carries round numbers
        if half(v) != v:
            print(f"warning: {name}: type.{role} {v} rounded to {half(v)} pt", file=sys.stderr)
    levels = [half(v) for v in levels]
    b = pts["body"]
    return {"canvas": {"w": cw, "h": ch}, "body": round(b / ch, 6), "levels": levels, "tracking": tracking,
            "roles": {k: {"pt": pts[k], "size": round(pts[k] / b, 4), "leading": TYPE[k][1]} for k in TYPE}}


def band(name: str, title: dict, out: dict) -> dict:
    """The title: block resolved: style cover | band; a band gets its defaults and image paths."""
    t = dict(title)
    if t.setdefault("style", "cover") not in ("cover", "band"):
        sys.exit(f"{name}: title.style {t['style']!r} is not cover or band")
    if t["style"] == "cover":
        return t
    t = {**BAND, **t}
    for k in ("band", "field", "field-text"):
        if t[k] not in out["roles"]:
            sys.exit(f"{name}: title.{k} {t[k]!r} is not a role")
    g = out["geometry"]
    if so := mark_entry(g, "signoff"):
        t.setdefault("signoff-height", so["height"])
    t.setdefault("logo-height", (mark_entry(g, "logo") or {}).get("title-height", 0.09))
    return t


def marks(name: str, data: dict, out: dict) -> dict:
    """{role: {logo, logo-print?, <name>, <name>-print?...}} as paths, for MARK_ROLES, the band's field
    and every role marks: names: logo (the compositions' slot, worn or not) and every mark a corner
    wears (geometry.marks). background defaults to logo.medium.light and each corner's light image,
    primary to the dark ones, any other role to primary's; each name defaults on its own. A name's
    print (CMYK) twin, `<image>-print` in logo.images, rides along for LaTeX."""
    images, medium = out["logo"].get("images", {}), out["logo"].get("medium", {})
    worn = [e for e in out["geometry"]["marks"].values() if e]
    given = {k: dict(v or {}) for k, v in (data.get("marks") or {}).items()}
    t = data.get("title") or {}
    field = {**BAND, **t}["field"] if t.get("style") == "band" else None
    defaults = {"background": {"logo": medium.get("light"), **{e["mark"]: e["light"] for e in worn if "light" in e}},
                "primary": {"logo": medium.get("dark"), **{e["mark"]: e["dark"] for e in worn if "dark" in e}}}
    legal = ["logo"] + [e["mark"] for e in worn if e["mark"] != "logo"]
    roles = list(MARK_ROLES) + [r for r in [field, *given] if r and r not in MARK_ROLES]
    names = {}
    for role in dict.fromkeys(roles):
        if role not in out["roles"]:
            sys.exit(f"{name}: marks.{role} is not a role")
        bad = set(given.get(role, {})) - set(legal)
        if bad:
            sys.exit(f"{name}: marks.{role} takes {legal} (logo and the marks geometry.marks wears), not {sorted(bad)}")
        names[role] = {**(defaults[role] if role in defaults else names["primary"]), **given.get(role, {})}
    res = {}
    for role, m in names.items():
        r = {}
        for n in legal:
            if m.get(n) not in images:
                sys.exit(f"{name}: marks.{role}.{n} {m.get(n)!r} is not a logo.images name")
            r[n] = images[m[n]]["path"]
            if m[n] + "-print" in images:   # LaTeX takes the print (CMYK) lockup when there is one
                r[n + "-print"] = images[m[n] + "-print"]["path"]
        res[role] = r
    return res


def _box(x, y, w, h):
    return [round(v, 4) for v in (x, y, w, h)]


def variant(base: dict, **over) -> dict:
    """A copy of a composition with some keys replaced; a dict value merges into the key's dict."""
    out = json.loads(json.dumps(base))
    for k, v in over.items():
        out[k] = {**out[k], **v} if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def slide_hw(out: dict) -> float:
    """The slide's height over its width, from pptx.size as a ratio of small whole numbers (the
    default 13.333 x 7.5 in and ncar's 10 x 5.625 in are both 16:9)."""
    w, h = (out.get("pptx") or {}).get("size") or CANVAS
    r = Fraction(w / h).limit_denominator(32)
    return r.denominator / r.numerator


def compositions(name: str, data: dict, out: dict) -> dict:
    """The title, closing, section and feature slides as boxes ([x, y, w, h], slide fractions, y
    down) and roles, one fully resolved entry per COMPOSITIONS name with every COMP_KEYS key, so
    each format's drawer picks a name and applies no variant logic. Derived from the geometry,
    title, signoff and art knobs; livery.yml `compositions: {<name>: {<key>: ...}}` overrides,
    an override on title reaching its photo and light variants, one on closing its light one."""
    g = out["geometry"]; m = g["margin"]
    logo = mark_entry(g, "logo") or {}   # the content mark's entry: its aspect and *-height keys (none: no field mark)
    hw = slide_hw(out)   # a height as a fraction of the width
    art = out.get("art") or {}
    has_art = lambda k: isinstance(art.get(k), str)
    waves = art.get("waves")
    t = {**BAND, "logo-height": logo.get("title-height", 0.09), **(out.get("title") or {})}
    so = mark_entry(g, "signoff")   # the sign-off's entry: the fields wear it in its corner
    if so:
        t.setdefault("signoff-height", so["height"])

    def mark(y, h, role):   # the mark top left on a field; null where the livery draws none
        if not logo:
            return None
        return {"role": role, "box": _box(m, y, h * logo.get("aspect", 1) * hw, h)}

    def signoff(role):   # in its corner, as on a content slide
        if not so:
            return None
        h = so["height"]; w = h * so["aspect"] * hw
        inset = so.get("inset", m)
        x = inset if so_corner.endswith("left") else 1 - inset - w
        return {"role": role, "box": _box(x, so["top"] if so_corner.startswith("top") else 1 - so["bottom"] - h, w, h)}

    so_corner = next((c for c, e in g["marks"].items() if e is so), None) if so else None

    def strip(role):   # the band's strip: the sign-off on its corner's side, the mark opposite, centered
        mid, left = (1 + t["bottom"]) / 2, None
        sig = None
        if so:
            h = t["signoff-height"]; w = h * so["aspect"] * hw
            left = so_corner.endswith("left")
            sig = {"role": role, "box": _box(m if left else 1 - m - w, mid - h / 2, w, h)}
        mk = None
        if logo:
            h = t["logo-height"]; w = h * logo.get("aspect", 1) * hw
            mk = {"role": role, "box": _box(m if left is False else 1 - m - w, mid - h / 2, w, h)}
        return mk, sig

    def wave(style, shift, opacity, role="secondary"):
        if not waves:
            return None
        return {"style": style, "shift": shift, "role": role, "opacity": opacity, "line": 0.0015}

    shift = (waves or {}).get("shift", {})
    empty = dict.fromkeys(COMP_KEYS)
    pad_w = 1 - 2 * m   # the HTML's padded box, which its percentages are of
    rule = [0.13, 0.0033]   # [width of W, thickness of H]
    tm = (0.06, logo.get("title-height", 0.09))   # the title mark's y and height; the column starts 0.05 under it
    ty = tm[0] + tm[1] + 0.05
    title = {**empty,
             "field": {"role": "primary", "box": _box(0, 0, 1, 1)},
             "art": "title" if has_art("title") else None,
             "waves": wave("bands", shift.get("title", 0), [0.18, 0.10]),
             "mark": mark(*tm, "primary"),
             "signoff": signoff("primary"),
             "column": {"box": _box(m, ty, 0.50, 0.86 - ty), "anchor": "top",
                        "role": "primary-text", "tab": True, "rule": rule},
             "fineprint": {"box": _box(m, 0.86, 0.50, 0.10), "anchor": "bottom", "role": "primary-text"}}
    over = data.get("compositions") or {}
    for k, v in over.items():
        if k not in COMPOSITIONS:
            sys.exit(f"{name}: compositions.{k} is not one of {COMPOSITIONS}")
        bad = set(v or {}) - set(COMP_KEYS)
        if bad:
            sys.exit(f"{name}: compositions.{k} takes {COMP_KEYS}, not {sorted(bad)}")
    title = merge(title, over.get("title") or {})

    def photo(c):
        col, fp = c["column"]["box"], c["fineprint"]
        return variant(c, art=None, fineprint=fp and {**fp, "box": [fp["box"][0], fp["box"][1], 0.44, fp["box"][3]]}, field={"box": _box(0, 0, 0.5, 1)}, photo={"box": _box(0.48, 0, 0.52, 1)},
                       waves=wave("cover", 0, [0.65], "secondary"),
                       column={"box": [col[0], col[1], 0.44, col[3]]},
                       byline=narrow(c["byline"]))

    def narrow(b):   # a byline's box beside the photo, as the column's
        return b and {**b, "box": b.get("box") and [b["box"][0], b["box"][1], min(0.44, b["box"][2]), b["box"][3]]}

    def light(c, art=None):   # art: the light cover's own picture (art.title-light), else none
        w = c["waves"]
        return variant(c, art=art, field={"role": "background"},
                       waves=w and {**w, "style": "lines", "opacity": []} if w and w["style"] == "bands" else w,
                       mark=c["mark"] and {**c["mark"], "role": "background"},
                       signoff=c["signoff"] and {**c["signoff"], "role": "background"},
                       column={"role": "foreground"},
                       byline=c["byline"] and {**c["byline"], "role": "foreground"},
                       fineprint=c["fineprint"] and {**c["fineprint"], "role": "foreground"})

    top, bottom, split = t["top"], t["bottom"], t["split"]
    smark, ssign = strip(t["field"])
    title_band = {**empty,
                  "field": {"role": t["field"], "box": _box(0, 0, 1, 1)},
                  "art": "title" if has_art("title") else None,
                  "photo": {"box": _box(split, top, 1 - split, bottom - top)},
                  "band": {"role": t["band"], "box": _box(0, top, 1, bottom - top)},
                  "mark": smark, "signoff": ssign,
                  "column": {"box": _box(m, top, split - m - 64 / W, bottom - top), "anchor": "middle",
                             "role": "primary-text", "tab": True, "rule": rule},
                  "fineprint": {"box": _box(m, bottom + 0.018, split - m - 64 / W, 0.06), "anchor": "top", "role": t["field-text"]}}
    cm = (0.09, logo.get("closing-height", 0.10))   # the closing mark's y and height; the column starts 0.03 under it
    cy = cm[0] + cm[1] + 0.03
    closing_col = {"box": _box(m, cy, 0.62, 0.88 - cy), "anchor": "middle",
                   "role": "primary-text", "tab": True, "rule": None}
    closing = merge({**empty,
                     "field": {"role": "primary", "box": _box(0, 0, 1, 1)},
                     "art": "closing" if has_art("closing") else None,
                     "waves": wave("bands", shift.get("title", 0), [0.18, 0.10]),
                     "mark": mark(*cm, "primary"),
                     "signoff": signoff("primary"),
                     "column": closing_col}, over.get("closing") or {})
    closing_band = {**empty,
                    "field": {"role": t["field"], "box": _box(0, 0, 1, 1)},
                    "art": "closing" if has_art("closing") else "title" if has_art("title") else None,
                    "mark": smark, "signoff": ssign,
                    "column": {**closing_col, "box": _box(m, 0.10, 0.62, bottom - 0.13), "role": t["field-text"]}}
    div = g.get("section", {}); dv = out.get("section", {})
    section = {**empty,
               "field": {"role": "primary", "box": _box(0, 0, 1, 1)},
               "art": "section" if has_art("section") else None,
               "waves": wave("bands", shift.get("section", 0), [0.18, 0.10]),
               "mark": mark(0.08, logo.get("section-height", 0.08), "primary"),
               "signoff": signoff("primary"),
               "column": {"box": _box(m, div.get("top", 0.1333), 0.62, 1 - div.get("top", 0.1333) - div.get("bottom", 0.0889)),
                          "anchor": "middle", "role": "primary-text", "tab": bool(dv.get("tab", True)), "rule": None},
               "eyebrow": {"label": dv.get("label", "Section"),   # section.label-color, a role or a hex, as hex
                           "color": (lambda c: c if c.startswith("#") else out["roles"][c])(dv.get("label-color", "secondary")),
                           "progress": bool(dv.get("progress", False))}   # "SECTION 3 of 5"
                          if dv.get("label", "Section") else None}   # section.label: null, no eyebrow
    feature = {**empty,
               "photo": {"box": _box(0, 0, 1, 1)},
               "bar": {"role": "dark", "opacity": 0.72, "box": _box(0, 0, 1, 180 / H)},
               "column": {"box": _box(m, 0, pad_w, 180 / H), "anchor": "middle", "role": "background", "tab": False, "rule": None},
               "panel": {"role": "dark", "opacity": 0.72, "box": _box(m, 230 / H, 0.52 * pad_w, 1 - 230 / H - 70 / H)}}
    style = (data.get("feature") or {}).get("style", "bar")
    if style not in FEATURE_STYLES:
        sys.exit(f"{name}: feature.style {style!r} is not one of {FEATURE_STYLES}")
    if style == "cover":   # the cover with the deck's photo, the body where the subtitle would be
        tp = photo(title)
        feature = variant(tp, fineprint=None, column={"box": _box(m, 0.34, 0.44, 0.52), "anchor": "top"})
    res = {"title": title,
           "title-photo": photo(title),
           "title-light": light(title, "title-light" if has_art("title-light") else None),
           "title-photo-light": light(photo(title)),
           "title-band": title_band,
           "closing": closing,
           "closing-light": light(closing),
           "closing-band": closing_band,
           "section": section,
           "feature": feature}
    for k in COMPOSITIONS:   # every override last; a base's already reached its variants
        if k not in ("title", "closing"):
            res[k] = merge(res[k], over.get(k) or {})
    for k, v in over.items():   # the small print's default text belongs to a cover
        if k not in COVERS and ((v or {}).get("fineprint") or {}).get("text"):
            sys.exit(f"{name}: compositions.{k}.fineprint.text: only a cover has default small print")
    title_text = (res["title"]["fineprint"] or {}).get("text")
    for k in COVERS:   # its paragraphs (blank-line apart, white space collapsed): a cover's own, else title's
        fp = res[k]["fineprint"]
        if fp:
            text = fp.pop("text", None) or title_text
            if text:
                fp["paragraphs"] = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text.strip())]
    for c in res.values():   # the column's text alignment, left unless a livery centers it
        if c["column"]:
            c["column"].setdefault("align", "left")
    for k in COVERS:   # the cover's text: which elements the column and the byline hold, in order
        res[k] = cover_elements(name, k, res[k])
    for k, c in res.items():
        for role in [c[b]["role"] for b in COMP_KEYS if isinstance(c[b], dict) and "role" in c[b]]:
            if role not in out["roles"]:
                sys.exit(f"{name}: compositions.{k}: role {role!r} is not a role")
    images = out["logo"].get("images", {})
    for k, c in res.items():   # each mark's and sign-off's files: by image when set, else its role's
        for part, kind in (("mark", "logo"), ("signoff", "signoff")):
            p = c[part]
            if not p:
                continue
            if p.get("image"):
                if p["image"] not in images:
                    sys.exit(f"{name}: compositions.{k}.{part}.image: {p['image']!r} is not a logo.images name")
                p["img"] = images[p["image"]]["path"]
                if p["image"] + "-print" in images:   # LaTeX takes the print (CMYK) lockup when there is one
                    p["img-print"] = images[p["image"] + "-print"]["path"]
            else:
                m = out["marks"].get(p.get("role"), out["marks"]["primary"])
                p["img"] = m.get(kind)
                if kind == "logo" and "logo-print" in m:
                    p["img-print"] = m["logo-print"]
    return res


def cover_elements(name: str, k: str, c: dict) -> dict:
    """A cover's column and byline resolved: the byline's role, anchor, align, box and elements
    (author, institute, date unless named), and the column's elements (every element, less a boxed
    byline's, unless named). The title is the column's; no element is in both when the byline has
    a box (without one, its elements stay in the column's flow, in its color)."""
    col, by = c["column"], c["byline"]
    if by is not None:
        by = c["byline"] = {"role": col["role"], "box": None, "anchor": "top", "align": col["align"],
                            "elements": list(BYLINE), **by}
    boxed = by["elements"] if by and by["box"] else []
    col.setdefault("elements", [e for e in ELEMENTS if e not in boxed])
    for part, els in (("column", col["elements"]), ("byline", by["elements"] if by else [])):
        if bad := [e for e in els if e not in ELEMENTS] or (len(set(els)) < len(els) and ["a repeat"]):
            sys.exit(f"{name}: compositions.{k}.{part}.elements: {bad} (elements: {', '.join(ELEMENTS)}, once each)")
    if "title" not in col["elements"] or "title" in (by["elements"] if by else []):
        sys.exit(f"{name}: compositions.{k}: the title is the column's (column.elements, not byline.elements)")
    if both := sorted(set(col["elements"]) & set(boxed)):
        sys.exit(f"{name}: compositions.{k}: {both} in both the column and the byline's box")
    return c


def installed_fonts(name: str, spec: dict) -> dict:
    """installed-fonts resolved: {base, headings} each {family, faces: {face: [full, PostScript]}};
    a bare family string names its four faces the usual way (Helvetica Neue Bold, HelveticaNeue-Bold)."""
    out = {}
    for k, v in (spec or {}).items():
        if k not in ("base", "headings"):
            sys.exit(f"{name}: installed-fonts.{k} is not base or headings")
        if isinstance(v, str):
            ps = v.replace(" ", "")
            v = {"family": v, "faces": {f: [v + a, ps + b] for f, (a, b) in FACES.items()}}
        if not isinstance(v, dict) or not isinstance(v.get("family"), str) or not isinstance(v.get("faces"), dict):
            sys.exit(f"{name}: installed-fonts.{k} is a family name or {{family, faces}}")
        for face, names in v["faces"].items():
            if face not in FACE_KEYS or not isinstance(names, list) or not 1 <= len(names) <= 2:
                sys.exit(f"{name}: installed-fonts.{k}.faces.{face}: a face of {FACE_KEYS}, "
                         "as [full name, PostScript name]")
        out[k] = {"family": v["family"], "faces": {f: list(n) for f, n in v["faces"].items()}}
    return out


def tex_escape(text: str) -> str:
    """Plain text for LaTeX: its special characters escaped."""
    special = {"\\": "\\textbackslash{}", "&": "\\&", "%": "\\%", "$": "\\$", "#": "\\#", "_": "\\_",
               "{": "\\{", "}": "\\}", "~": "\\textasciitilde{}", "^": "\\textasciicircum{}"}
    return "".join(special.get(ch, ch) for ch in text)


def tex_name(key: str, names: dict) -> str:
    return names.get(key) or "".join(w.capitalize() for w in key.split("-"))


def texpath(p: str) -> str:
    """A livery path for livery.sty: relative ones under \\engineliverydir, absolute ones as they are."""
    p = Path(p).as_posix()
    return p if os.path.isabs(p) else f"\\engineliverydir {p}"


def base_font(livery: dict) -> tuple[str, list]:
    family = livery["typography"].get("base", "")
    for font in livery["typography"].get("fonts", []):
        if font.get("family") == family:
            return family, font.get("files", [])
    return family, []


def family_files(livery: dict, family: str) -> list:
    """A typography.fonts family's files ([] when it has none, or no such family)."""
    return next((f["files"] for f in livery["typography"].get("fonts", []) if f.get("family") == family and f.get("files")), [])


def heading_font(livery: dict) -> tuple[str, list]:
    """The headings family and its files when it is a second family with files of its own."""
    t = livery["typography"]
    family = t.get("headings", "")
    if family and family != t.get("base", "") and family_files(livery, family):
        return family, family_files(livery, family)
    return "", []


def quote_font(livery: dict) -> tuple[str, list]:
    """The quote's family (boxes.quote.family) and its files when it is not the body's."""
    family = livery["boxes"]["quote"]["family"]
    if family and family != livery["typography"].get("base", ""):
        return family, family_files(livery, family)
    return "", []


def mono_font(livery: dict) -> tuple[str, dict]:
    """typography.monospace (a family name, or {family: ...}) with files of its own: the code face, as
    {regular, italic, bold} files; bold is the heaviest upright above 400 (DM Mono has a Medium only)."""
    t = livery["typography"]
    m = t.get("monospace")
    family = m.get("family", "") if isinstance(m, dict) else (m or "")
    files = next((f.get("files", []) for f in t.get("fonts", []) if family and f.get("family") == family), [])
    faces = {}
    for f in files:
        w, it = int(f.get("weight", 400)), f.get("style") == "italic"
        if w == 400:
            faces["italic" if it else "regular"] = f
        elif w > 400 and not it and w >= int(faces.get("bold", {}).get("weight", 0)):
            faces["bold"] = f
    return (family, faces) if "regular" in faces else ("", {})


FACE_OF = {(400, False): "regular", (700, False): "bold", (400, True): "italic", (700, True): "bolditalic", (600, False): "semibold"}


def face_of(f: dict) -> str | None:
    """A font file's face name (regular, bold, italic, bolditalic, semibold) from its weight and style."""
    return FACE_OF.get((f.get("weight", 400), f.get("style") == "italic"))


def emit_sty(livery: dict, sources: dict, extra: str = "") -> str:
    """The .sty text; `extra` (the override files) goes before the catcode restore."""
    names = livery.get("latex", {}).get("colors", {})
    L = [r"% build/livery.sty: GENERATED by livery_build.py from _brand.yml and livery.yml; do not edit.",
         f"% livery {livery['name']}. \\engineliverydir (this directory, with a trailing /) is set by",
         r"% engine_livery.sty before it inputs this file. @ is made a letter for the engine@ macros",
         r"% and its catcode restored at the end (\makeatother would break a package that inputs this).",
         r"\edef\liveryrestoreat{\catcode`\noexpand\@=\the\catcode`\@\relax}\catcode`\@=11",
         "% palette"]
    for key, hexv in livery["palette"].items():
        L.append(f"\\definecolor{{{tex_name(key, names)}}}{{HTML}}{{{hexv[1:]}}}")
    L.append("% roles")
    for role, tex in ROLE_TEX.items():
        if role not in livery["roles"]:
            continue
        src = sources[role]
        if isinstance(src, str) and src.startswith("#"):
            L.append(f"\\definecolor{{{tex}}}{{HTML}}{{{src[1:].upper()}}}")
        else:
            L.append(f"\\colorlet{{{tex}}}{{{tex_name(src, names)}}}")
    L.append("% the blends")
    for key, hexv in livery["blends"].items():
        L.append(f"\\definecolor{{{tex_name('brand-' + key, {})}}}{{HTML}}{{{hexv[1:]}}}")
    blends = {k: livery_mod.mix(livery["roles"][a], livery["roles"][b], s) for k, a, b, s in BLENDS if a in livery["roles"] and b in livery["roles"]}
    for key, color in BEAMER_BLENDS.items():   # a livery's blends: override, which the theme would recompute
        if key in livery["blends"] and livery["blends"][key] != blends.get(key):
            L.append(f"\\colorlet{{{color}}}{{{tex_name('brand-' + key, {})}}}")
    L.append(f"\\def\\engine@mode{{{livery['mode']}}}   % dark: light text on a dark background (a dark frame is every frame)")
    L.append("% the roles and blends by name (a card's or strip's role=): \\engine@role@<name> is its color")
    for role, tex in livery["latex"]["roles"].items():   # hyphenated names: through \csname
        L.append(f"\\expandafter\\def\\csname engine@role@{role}\\endcsname{{{tex}}}")
    stem = lambda p: texpath(Path(p).with_suffix("").as_posix())   # \\includegraphics finds the extension
    L.append("% marks per field role: \\engine@mark@<role>@<name> (a name's print lockup when there is one);")
    L.append("% \\enginelogo{light|dark} draws background's and primary's logo")
    for role, m in livery["marks"].items():   # a role's name may hold a hyphen: through \\csname
        for name, path in m.items():
            if not name.endswith("-print"):
                L.append(f"\\expandafter\\def\\csname engine@mark@{role}@{name}\\endcsname{{{stem(m.get(name + '-print', path))}}}")
    worn = {c: livery["geometry"]["marks"][c] for c in CORNERS if livery["geometry"]["marks"][c]}
    L.append("% the content slides' marks by corner (geometry.marks): \\engine@corners the worn ones, each one's")
    L.append("% \\engine@corner@<corner>@<key>: mark (its name in \\engine@mark@<role>@<name>), height, top or bottom, aspect, inset")
    L.append(f"\\def\\engine@corners{{{','.join(worn)}}}")
    for c, e in worn.items():
        for k in ("mark", "height", "top", "bottom", "aspect", "inset"):
            if k in e:
                L.append(f"\\expandafter\\def\\csname engine@corner@{c}@{k}\\endcsname{{{e[k]}}}")
    family, files = base_font(livery)
    L.append("% fonts: the base family's files, by weight and style")
    L.append(f"\\def\\engine@font@family{{{family}}}")
    if files:
        L.append(f"\\def\\engine@font@dir{{{texpath(Path(files[0]['path']).parent.as_posix())}/}}")
        L.append(f"\\def\\engine@font@ext{{{Path(files[0]['path']).suffix}}}")
    for f in files:
        face = face_of(f)
        if face:
            L.append(f"\\def\\engine@font@{face}{{{Path(f['path']).stem}}}")
    hfamily, hfiles = heading_font(livery)
    if hfamily:   # a second family for headings (typography.headings), same shape
        L.append("% the headings family's files, when it is a family of its own")
        L.append(f"\\def\\engine@headfont@family{{{hfamily}}}")
        L.append(f"\\def\\engine@headfont@dir{{{texpath(Path(hfiles[0]['path']).parent.as_posix())}/}}")
        L.append(f"\\def\\engine@headfont@ext{{{Path(hfiles[0]['path']).suffix}}}")
        for f in hfiles:
            face = face_of(f)
            if face:
                L.append(f"\\def\\engine@headfont@{face}{{{Path(f['path']).stem}}}")
    qfamily, qfiles = quote_font(livery)
    if qfamily:   # the quote's face (boxes.quote.family), when not the body's: the faces it has
        L.append("% the quote's family's files (boxes.quote.family)")
        L.append(f"\\def\\engine@quotefont@family{{{qfamily}}}")
        L.append(f"\\def\\engine@quotefont@dir{{{texpath(Path(qfiles[0]['path']).parent.as_posix())}/}}")
        L.append(f"\\def\\engine@quotefont@ext{{{Path(qfiles[0]['path']).suffix}}}")
        for f in qfiles:
            face = face_of(f)
            if face:
                L.append(f"\\def\\engine@quotefont@{face}{{{Path(f['path']).stem}}}")
    mfamily, mfaces = mono_font(livery)
    if mfamily:   # the code face (typography.monospace), when the livery bundles one
        L.append("% the code face's files (typography.monospace)")
        L.append(f"\\def\\engine@monofont@family{{{mfamily}}}")
        L.append(f"\\def\\engine@monofont@dir{{{texpath(Path(mfaces['regular']['path']).parent.as_posix())}/}}")
        L.append(f"\\def\\engine@monofont@ext{{{Path(mfaces['regular']['path']).suffix}}}")
        for face, f in mfaces.items():
            L.append(f"\\def\\engine@monofont@{face}{{{Path(f['path']).stem}}}")
    installed = livery.get("installed-fonts", {})
    if installed:   # installed faces fonts=brand prefers (engine_livery.sty), by full name
        L.append("% installed fonts to prefer under fonts=brand (installed-fonts), by full name")
        if "base" in installed:
            L.append(f"\\def\\engine@font@installed{{{installed['base']['family']}}}")
        for k, tex in (("base", "base"), ("headings", "head")):
            for face, names in installed.get(k, {}).get("faces", {}).items():
                L.append(f"\\def\\engine@installed@{tex}@{face}{{{names[0]}}}")
    ft = livery["frametitle"]   # the content slides' title: the outer theme's \engine@frametitle reads every one
    L.append("% the content slides' title (frametitle): alignment, accent tab, hairline, the band and the body's top")
    L.append(f"\\def\\engine@ft@align{{{ft['align']}}}")
    for k in ("tab", "rule"):
        if not ft[k]:
            L.append(f"\\def\\engine@ft@no{k}{{}}")
    for k, tex in (("top", "top"), ("height", "height"), ("rule-y", "ruley"), ("rule-width", "rulewidth"), ("body", "bodytop")):
        L.append(f"\\def\\engine@ft@{tex}{{{ft[k]}}}")
    L.append(f"\\definecolor{{EngineFrametitleRuleColor}}{{HTML}}{{{ft['rule-color'][1:]}}}")
    L.append(f"\\definecolor{{EngineFrametitleColor}}{{HTML}}{{{ft['color'][1:]}}}")
    if ft["symmetric"]:   # the title's room mirrored about the slide's axis: a centered title on the slide's center
        L.append("\\def\\engine@ft@symmetric{}")
    L.append(f"\\def\\engine@ft@gap{{{TITLE_GAP}}}")
    L.append("% the divider stack's gaps (section:), em of the eyebrow and of the subtitle")
    for k in SECTION:
        L.append(f"\\def\\engine@section@{k.replace('-', '')}{{{livery['section'][k]}}}")
    mk = livery.get("marking") or []
    if mk:   # the marking strips, in order: each one's box (y down), alignment, colors, size and default text
        body = livery["type"]["roles"]["body"]["pt"]
        L.append("% the marking strips (marking:); each one's text is the deck's \\enginemarking[<name>], else its default")
        L.append(f"\\def\\engine@markings{{{','.join(s['name'] for s in mk)}}}")
        L.append(f"\\def\\engine@firstmarking{{{mk[0]['name']}}}")
        for s in mk:
            n = s["name"]
            for axis, v in zip("xywh", s["box"]):
                L.append(f"\\def\\engine@marking@{n}@{axis}{{{v}}}")
            L.append(f"\\def\\engine@marking@{n}@align{{{s['align']}}}")
            L.append(f"\\def\\engine@marking@{n}@type{{{{{round(s['size'] / body, 4)}}}{{{s['leading']}}}}}")
            for name, c in (("Text", s["color"]), ("Fill", s["fill"])):   # hex: markings() resolved them
                if c:
                    L.append(f"\\definecolor{{EngineMarking{n}{name}}}{{HTML}}{{{c[1:].upper()}}}")
            if s["fill"]:
                L.append(f"\\def\\engine@marking@{n}@fill{{}}")
            if s["bold"]:
                L.append(f"\\def\\engine@marking@{n}@bold{{}}")
            L.append(f"\\def\\engine@marking@{n}@default{{{tex_escape(s['text'] or '')}}}")
    L += emit_sty_boxes(livery)
    bu = livery.get("bullets")
    if bu:   # the list glyphs per level (bullets:), the last repeating; beamer has three levels
        L.append("% the list glyphs per level (bullets:), in their color")
        L.append(f"\\definecolor{{EngineBullet}}{{HTML}}{{{bu['color'][1:]}}}")
        for i, n in enumerate(("i", "ii", "iii")):
            L.append(f"\\def\\engine@bullet@{n}{{{bu['glyphs'][min(i, len(bu['glyphs']) - 1)]}}}")
    L.append("% geometry, in fractions of the slide")
    geom = livery.get("geometry", {})
    for k, v in geom.items():
        if k == "marks":   # by corner, above
            continue
        if isinstance(v, dict):
            for k2, v2 in v.items():
                L.append(f"\\def\\engine@geom@{k}{k2.replace('-', '')}{{{v2}}}")
        elif not isinstance(v, list):
            L.append(f"\\def\\engine@geom@{k.replace('-', '')}{{{v}}}")
    # the body box's height (geometry.body, derived: a list, which the loop skips): a gallery's default height
    L.append(f"\\def\\engine@geom@bodyheight{{{geom['body'][3]}}}")
    art = livery.get("art", {})
    waves = art.get("waves")
    if waves:
        L.append("% the wave lines (art.waves): line n top to bottom, shifted right by #1 of the width,")
        L.append("% and the same path bottom to top, for filling between two lines")
        fmt = lambda p: f"({{({p[0]:.4f}+#1)*\\paperwidth}},{1 - p[1]:.4f}\\paperheight)"
        for i, pts in enumerate(waves["lines"], 1):
            n = "i" * i
            L.append(f"\\def\\engine@wave@{n}@down#1{{{fmt(pts[0])}")
            L.append(f"  .. controls {fmt(pts[1])} and {fmt(pts[2])} .. {fmt(pts[3])}")
            L.append(f"  .. controls {fmt(pts[4])} and {fmt(pts[5])} .. {fmt(pts[6])}}}")
            L.append(f"\\def\\engine@wave@{n}@up#1{{{fmt(pts[6])}")
            L.append(f"  .. controls {fmt(pts[5])} and {fmt(pts[4])} .. {fmt(pts[3])}")
            L.append(f"  .. controls {fmt(pts[2])} and {fmt(pts[1])} .. {fmt(pts[0])}}}")
        for k, v in waves.get("shift", {}).items():
            L.append(f"\\def\\engine@waveshift@{k}{{{v}}}")
    for kind in ART_KINDS:   # (no hyphen in a TeX name: title-light is titlelight)
        if isinstance(art.get(kind), str):
            L.append(f"\\def\\engine@art@{kind.replace('-', '')}{{{stem(art[kind])}}}")
    if livery.get("title", {}).get("style") == "band":   # its boxes and colors are the compositions'
        L.append("\\def\\engine@title@style{band}")
    L.append("% type: the body as a fraction of the paper height, each role's size and leading as ratios to it,")
    L.append("% the list levels ii-v as ratios to the body (the pptx's points on its canvas, livery.json type)")
    ty = livery["type"]
    L.append(f"\\def\\engine@type@frac{{{ty['body']}}}")
    L.append(f"\\def\\engine@type@tracking{{{ty['tracking']}}}")   # small caps' letter spacing, em (\engine@tracking)
    for k, v in ty["roles"].items():
        L.append(f"\\def\\engine@type@{k}{{{{{v['size']}}}{{{v['leading']}}}}}")
    b, lead = ty["roles"]["body"]["pt"], ty["roles"]["body"]["leading"]
    for n, v in zip(("ii", "iii", "iv", "v"), ty["levels"][1:]):   # letters: TeX names take no digits
        L.append(f"\\def\\engine@type@level{n}{{{{{round(v / b, 4)}}}{{{lead}}}}}")
    L += emit_sty_charts(livery)
    L += emit_sty_compositions(livery, stem)
    L.append(extra.rstrip("\n"))
    L.append(r"\liveryrestoreat")
    return "\n".join(L) + "\n"


def tex_camel(key: str) -> str:
    """bar-color -> BarColor, a key's part of a LaTeX color name."""
    return "".join(w.capitalize() for w in key.split("-"))


def emit_sty_boxes(livery: dict) -> list[str]:
    """The boxes (livery.json boxes): \\engine@boxes@<box>@<key> for each number (fractions of the paper,
    tint a share), @pady and @padx for each pad (em, so the factor goes before `em`), and a color per
    color key, EngineBoxes<Box><Key> (the status glyphs' EngineGlyph<Key>: EngineStatus* are the
    charts'), as hex, none for a null one (a rail's fill); the card roles as their names (the theme
    resolves them through \\engine@role@<name>)."""
    L = ["% boxes (boxes:): the column gap and rule, each box's bar, outline and radius (of the paper),",
         "% its pads (@pady, @padx: em of the body type), colors, and the card roles by place in a row"]
    for box, v in livery["boxes"].items():
        for k, val in v.items():
            name = k.replace("-", "")
            if k == "roles":
                L.append(f"\\def\\engine@boxes@{box}@{name}{{{','.join(val)}}}")
            elif (box, k) == ("quote", "family"):   # its files are the fonts' (\engine@quotefont@*, above)
                continue
            elif k in BOX_COLORS.get(box, ()):
                if val is None:   # none (a rail's fill): the theme tests \ifcsname
                    continue
                tex = f"EngineGlyph{tex_camel(k)}" if box == "status" else f"EngineBoxes{tex_camel(box)}{tex_camel(k)}"
                L.append(f"\\definecolor{{{tex}}}{{HTML}}{{{val[1:]}}}")
            elif isinstance(val, list):   # [vertical, horizontal]
                L.append(f"\\def\\engine@boxes@{box}@{name}y{{{val[0]}}}\\def\\engine@boxes@{box}@{name}x{{{val[1]}}}")
            else:
                L.append(f"\\def\\engine@boxes@{box}@{name}{{{val}}}")
    return L


def emit_sty_charts(livery: dict) -> list[str]:
    """The chart colors of the livery's mode (livery.json charts) as EngineData1.., EngineDataMuted and
    EngineStatus<State>, and a pgfplots cycle list `livery` of the categorical slots, made the
    default when a document loads pgfplots (so LaTeX and Overleaf plots match the slides)."""
    ch = livery["charts"]
    b = ch[ch["mode"]]
    L = [f"% chart colors (livery.json charts, {ch['mode']}): the categorical slots, muted, status"]
    for i, c in enumerate(b["categorical"], 1):
        L.append(f"\\definecolor{{EngineData{i}}}{{HTML}}{{{c[1:].upper()}}}")
    L.append(f"\\definecolor{{EngineDataMuted}}{{HTML}}{{{b['muted'][1:].upper()}}}")
    for k, c in b["status"].items():
        L.append(f"\\definecolor{{EngineStatus{k.capitalize()}}}{{HTML}}{{{c[1:].upper()}}}")
    marks = ("*", "square*", "triangle*", "diamond*", "pentagon*", "o", "square", "triangle")
    entries = "\n".join(f"  {{EngineData{i},mark={marks[(i - 1) % len(marks)]}}}," for i in range(1, len(b["categorical"]) + 1))
    L.append("\\AtBeginDocument{\\@ifpackageloaded{pgfplots}{%")
    L.append("\\pgfplotscreateplotcyclelist{livery}{%")
    L.append(entries.rstrip(",") + "}%")
    L.append("\\pgfplotsset{cycle list name=livery}}{}}")
    return L


# the role each composition key is drawn in -> the colorlet suffix livery.sty gives it
COMP_COLORS = {"field": "Field", "band": "Band", "waves": "Waves", "bar": "Bar", "panel": "Panel",
               "column": "Text", "byline": "Byline", "fineprint": "Fineprint"}
BOXED = ("field", "photo", "band", "bar", "panel", "mark", "signoff", "column", "byline", "fineprint")


def emit_sty_compositions(livery: dict, stem) -> list[str]:
    """compositions as \\engine@c@<comp>@<key>@x|y|w|h (comp without hyphens), scalars, the roles as
    EngineC<comp><Key> colors and the image stems; an absent key leaves its macros undefined."""
    tex = lambda role: ROLE_TEX.get(role, "BrandDark")
    L = ["% compositions (livery_build.py compositions()): boxes in fractions of the slide, y down"]
    for comp, c in livery["compositions"].items():
        n = comp.replace("-", "")
        d = lambda k, v: L.append(f"\\def\\engine@c@{n}@{k}{{{v}}}")
        for k in BOXED:
            if c[k] and c[k].get("box"):   # a byline may have none
                for axis, v in zip("xywh", c[k]["box"]):
                    d(f"{k}@{axis}", v)
        for k, suffix in COMP_COLORS.items():
            if c[k]:
                L.append(f"\\colorlet{{EngineC{n}{suffix}}}{{{tex(c[k]['role'])}}}")
        if c["waves"]:
            w = c["waves"]
            d("waves@style", w["style"]); d("waves@shift", w["shift"]); d("waves@line", w["line"])
            for i, o in enumerate(w["opacity"], 1):
                d(f"waves@opacity@{'i' * i}", o)
        for k in ("bar", "panel"):
            if c[k]:
                d(f"{k}@opacity", c[k]["opacity"])
        col = c["column"]
        d("column@anchor", col["anchor"]); d("column@tab", "true" if col["tab"] else "false")
        d("column@align", col["align"])
        if "elements" in col:   # a cover's text, in order; the byline's apart, or colored in the column's flow
            d("column@elements", ",".join(col["elements"]))
            by = c["byline"]
            if by:
                d("byline@elements", ",".join(by["elements"])); d("byline@anchor", by["anchor"]); d("byline@align", by["align"])
                if not by["box"]:
                    d("byline@inline", ",".join(by["elements"]))
        if col["rule"]:
            d("column@rule@w", col["rule"][0]); d("column@rule@h", col["rule"][1])
        if c["fineprint"]:
            d("fineprint@anchor", c["fineprint"]["anchor"])
            if c["fineprint"].get("paragraphs"):   # the livery's default small print, unless the deck sets its own
                d("fineprint@text", "\\par ".join(tex_escape(p) for p in c["fineprint"]["paragraphs"]))
        if c["eyebrow"]:
            e = c["eyebrow"]
            d("eyebrow@label", e["label"])
            if e["progress"]:   # \insertsectionnumberlabel adds "of <total>" (\enginesectiontotal)
                d("eyebrow@progress", "true")
            L.append(f"\\definecolor{{EngineC{n}Eyebrow}}{{HTML}}{{{e['color'][1:].upper()}}}")   # hex: compositions() resolved it
        for k in ("mark", "signoff"):   # its files, the composition's own (compositions())
            if c[k] and c[k].get("img"):
                d(f"{k}@img", stem(c[k].get("img-print", c[k]["img"])))
        if c["art"]:
            d("art", stem(livery["art"][c["art"]]))
    return L


def emit_css(livery: dict, extra: str = "") -> str:
    L = ["/* build/livery.css: GENERATED by livery_build.py from _brand.yml and livery.yml; do not edit.",
         f" * livery {livery['name']}. Attached by engine-revealjs.lua with the font and logo files",
         " * beside it, so the url()s are bare file names. */"]
    family, files = base_font(livery)
    hfamily, hfiles = heading_font(livery)
    installed = livery.get("installed-fonts", {})
    mfamily, mfaces = mono_font(livery)
    qfamily, qfiles = quote_font(livery)
    if qfamily in (hfamily, mfamily):   # already declared
        qfiles = []
    for fam, fs, inst in ((family, files, installed.get("base")), (hfamily, hfiles, installed.get("headings")),
                          (mfamily, list(mfaces.values()), None), (qfamily, qfiles, None)):
        for f in fs:   # an installed face first, by full and PostScript name (CSS local() matches no family)
            names = (inst or {}).get("faces", {}).get(face_of(f), [])
            local = "".join(f'local("{n}"), ' for n in names)
            L.append(f'@font-face {{ font-family: "{fam}"; font-style: {f.get("style", "normal")}; '
                     f'font-weight: {f.get("weight", 400)}; font-display: block; '
                     f'src: {local}url("{Path(f["path"]).name}") format("{"opentype" if Path(f["path"]).suffix == ".otf" else "truetype"}"); }}')
    props = [f"--engine-{k}: {v};" for k, v in livery["roles"].items()]
    props += [f"--engine-{k}: {v};" for k, v in livery["blends"].items()]
    geom = livery.get("geometry", {})
    px = lambda frac, axis=H: f"{round(frac * axis, 1):g}px"
    mark_w = lambda e: f"{round(e['height'] * H, 1) * e['aspect']:.1f}px"   # a corner mark's width: its height's px times its aspect
    for k in ("margin", "tab-width", "wide-margin"):
        if k in geom:
            props.append(f"--engine-{k}: {px(geom[k], W)};")
    # the body box's foot (the slide's padding below it; a gallery's rows fill to it)
    props.append(f"--engine-body-bottom: {px(geom['body-bottom'])};")
    for k, v in geom.get("full", {}).items():
        props.append(f"--engine-full-{k}: {px(v, W if k == 'pad' else H)};")
    # type: the body and the frame title in slide pixels, every other role as its ratio to the body
    # (an em factor, so {.smaller}, scale= and the autofit script carry it), the list levels as each
    # one's ratio to the level above it (nested lists are em-relative too)
    ty = livery["type"]
    # (the deck's size step, --engine-type-scale from engine-revealjs.lua, multiplies the px ones)
    tpx = lambda pt: f"calc({round(pt / ty['canvas']['h'] * H, 2):g}px * var(--engine-type-scale, 1))"
    props.append(f"--engine-type-body: {tpx(ty['roles']['body']['pt'])};")
    props.append(f"--engine-tracking: {ty['tracking']:g}em;")   # small caps' letter spacing (type.tracking)
    for k in ("frametitle", "pagenumber", "footer", "marking"):   # fixed px: not shrunk with the body
        props.append(f"--engine-type-{k}: {tpx(ty['roles'][k]['pt'])};")
    for k, v in ty["roles"].items():
        if k not in ("body", "frametitle", "pagenumber", "footer", "marking"):
            props.append(f"--engine-type-{k}: {v['size']};")
    for k, v in ty["roles"].items():   # each role's leading (a line-height factor), as the beamer theme reads it
        props.append(f"--engine-leading-{k}: {v['leading']};")
    lv = ty["levels"]
    for i in range(1, len(lv)):
        props.append(f"--engine-type-level{i + 1}: {round(lv[i] / lv[i - 1], 4)};")
    props.append(f'--engine-font-family: "{family}";')
    if hfamily:
        props.append(f'--engine-heading-font-family: "{hfamily}";')
    # the content slides' marks by corner (geometry.marks; the .engine-mark-<corner> rules below) and
    # the page number's corner; the title box gives way on each mark's side (title_room())
    marks = {c: geom["marks"][c] for c in CORNERS if geom["marks"][c]}
    margin = "var(--engine-margin)"
    inset = lambda e: px(e["inset"], W) if "inset" in e else margin   # a mark's distance from its side edge
    beside = lambda c: f"calc({inset(marks[c])} + {round(TITLE_GAP * W)}px + {mark_w(marks[c])})"
    ft = livery["frametitle"]   # the band (frametitle.top/height/rule-y) and the body's top, in slide pixels
    for k, name in (("top", "title-top"), ("height", "title-height"), ("rule-y", "title-rule-y"),
                    ("rule-width", "title-rule-width"), ("body", "body-top")):
        props.append(f"--engine-{name}: {px(ft[k])};")
    props.append(f"--engine-title-rule-color: {ft['rule-color']};")
    for k in SECTION:   # the divider stack's gaps, em of the eyebrow and of the subtitle (section:)
        props.append(f"--engine-section-{k}: {livery['section'][k]:g}em;")
    if ft["align"] == "center":
        props.append("--engine-title-justify: center;")
        props.append("--engine-title-text-align: center;")
    if not ft["tab"]:
        props.append("--engine-title-tab: none;")
    if not ft["rule"]:
        props.append("--engine-title-rule: none;")
    for s, c in zip(("left", "right"), title_corners(livery)):   # the corner whose room each side takes (title_room())
        props.append(f"--engine-title-{s}: {beside(c) if c else margin};")
    props.append(f"--engine-title-color: {ft['color']};")
    pn = geom.get("pagenumber", {}).get("corner", "bottom-left")
    props.append(f"--engine-pagenumber-left: {'auto' if pn == 'bottom-right' else '50px'};")
    props.append(f"--engine-pagenumber-right: {'50px' if pn == 'bottom-right' else 'auto'};")
    props += emit_css_boxes(livery, px)
    L.append(":root {\n  " + "\n  ".join(props) + "\n}")
    for s in livery.get("marking") or []:   # each marking strip, in slide pixels (its text: engine-revealjs.lua)
        x, y, w, h = s["box"]
        sp = [f"--engine-marking-x: {px(x, W)};", f"--engine-marking-y: {px(y)};",
              f"--engine-marking-w: {px(w, W)};", f"--engine-marking-h: {px(h)};",
              f"--engine-marking-justify: {dict(center='center', left='flex-start', right='flex-end')[s['align']]};",
              f"--engine-marking-align: {s['align']};",
              f"--engine-marking-fill: {s['fill'] or 'transparent'};",   # hex: markings() resolved them
              f"--engine-marking-text: {s['color']};",
              f"--engine-marking-weight: {700 if s['bold'] else 400};",
              f"--engine-marking-size: {tpx(s['size'])};"]
        L.append(f".reveal .slides section .engine-marking-{s['name']} {{\n  " + "\n  ".join(sp) + "\n}")
    L += emit_css_charts(livery)
    # Quarto sets --mermaid-* on :root from its Sass; html:root outranks it, so mermaid wears the roles
    if mfamily:   # the code face: reveal's code and pre read --r-code-font
        L.append(f'html:root {{ --r-code-font: "{mfamily}", "SFMono-Regular", Menlo, Monaco, Consolas, monospace; }}')
    L.append("html:root {\n  --r-main-font-size: var(--engine-type-body);\n  --mermaid-bg-color: var(--engine-background);\n  --mermaid-node-bg-color: var(--engine-surface);"
             "\n  --mermaid-node-fg-color: var(--engine-foreground);\n  --mermaid-fg-color: var(--engine-foreground);"
             "\n  --mermaid-edge-color: var(--engine-foreground);\n  --mermaid-label-bg-color: var(--engine-background);"
             "\n  --mermaid-label-fg-color: var(--engine-primary-contrast);"
             "\n  --mermaid-font-family: var(--engine-font-family), Helvetica, Arial, sans-serif;\n}")
    f = livery.get("art", {}).get("content")   # content slides' static background (the compositions carry the rest)
    if isinstance(f, str):
        # (not a dark slide, which promises the dark color: white text on the photo vanished)
        sel = "section.slide.level2:not(.engine-section):not(.closing):not(.feature):not(.full):not(.engine-dark)"
        L.append(f'.reveal .slides {sel} {{ background: url("{Path(f).name}") center / cover no-repeat; }}')
    # the marks per field role (--engine-mark-<role>-<name>), worn by the content slides (background),
    # the fields (primary) and the inverted content slide (dark)
    L.append("html:root {\n" + "".join(f'  --engine-mark-{role}-{name}: url("{Path(path).name}");\n'
                                       for role, m in livery["marks"].items() for name, path in m.items()
                                       if not name.endswith("-print")) + "}")
    for c, e in marks.items():   # each corner's mark (engine-revealjs.lua's .engine-mark-<corner> on a content slide)
        v, h = c.split("-")
        L.append(f".reveal .slides section.slide .engine-mark-{c} {{ {v}: {px(e[v])}; {h}: {inset(e)}; "
                 f"width: {mark_w(e)}; height: {px(e['height'])}; background-position: {h} {v}; "
                 f"background-image: var(--engine-mark-background-{e['mark']}); }}")
        L.append(f".reveal .slides section.engine-field .engine-mark-{c} {{ background-image: var(--engine-mark-primary-{e['mark']}); }}")
        L.append(f".reveal .slides section.engine-dark .engine-mark-{c} {{ background-image: var(--engine-mark-dark-{e['mark']}); }}")
    art = livery.get("art", {})
    if isinstance(art.get("titlegraphic"), str):   # the title photo when a deck sets none
        L.append(f'.reveal .slides section.engine-title .engine-title-photo-default {{ background: url("{Path(art["titlegraphic"]).name}") center / cover no-repeat; }}')
    bu = livery.get("bullets")
    if bu:   # the list glyphs per level (bullets:) in place of the theme's shapes, the last repeating
        for i in range(3):
            sel = ".reveal .slides section " + "ul " * (i + 1) + "> li::before"
            glyph = bu["glyphs"][min(i, len(bu["glyphs"]) - 1)]
            L.append(f'html {sel} {{ content: "{glyph}"; background: none; border: 0; border-radius: 0; width: auto; '
                     f'height: auto; top: 0; left: -1em; color: {bu["color"]}; line-height: inherit; }}')
    L += emit_css_compositions(livery)
    if livery.get("mode") == "dark":
        L += emit_css_dark()
    else:
        L += emit_css_dark_slide(livery)
    L.append(extra.rstrip("\n"))
    return "\n".join(L).rstrip("\n") + "\n"


def emit_css_boxes(livery: dict, px) -> list[str]:
    """The boxes (livery.json boxes) as properties: the gap in slide pixels of the width, bars, rules,
    outlines and radii of the height, pads as `<v>em <h>em` (padding takes them as they are), the
    strip's tint a percentage (color-mix takes it), the colors hex."""
    b, p = livery["boxes"], []
    pad = lambda v: f"{v[0]:g}em {v[1]:g}em"
    p.append(f"--engine-column-gap: {px(b['columns']['gap'], W)};")
    p.append(f"--engine-column-rule: {px(b['columns']['rule'])};")
    p.append(f"--engine-caution-bar: {px(b['caution']['bar'])};")
    p.append(f"--engine-caution-pad: {pad(b['caution']['pad'])};")
    p.append(f"--engine-panel-pad: {pad(b['panel']['pad'])};")
    lead, card, strip = b["lead"], b["card"], b["strip"]
    p += [f"--engine-lead-fill: {lead['fill']};", f"--engine-lead-bar: {px(lead['bar'])};",
          f"--engine-lead-bar-color: {lead['bar-color']};", f"--engine-lead-pad: {pad(lead['pad'])};",
          f"--engine-lead-gap: {lead['pad'][0]:g}em;"]   # under it: its vertical pad, as the pptx and beamer leave
    p += [f"--engine-agenda-number: {b['agenda']['number-color']};", f"--engine-agenda-current: {b['agenda']['current-color']};",
          f"--engine-agenda-gap: {b['agenda']['gap']:g}em;", f"--engine-agenda-number-width: {b['agenda']['number-width']:g}em;"]
    quote = b["quote"]
    p += [f"--engine-quote-bar: {px(quote['bar'])};", f"--engine-quote-bar-color: {quote['bar-color']};",
          f"--engine-quote-pad: {pad(quote['pad'])};", f"--engine-quote-gap: {quote['pad'][0]:g}em;",   # above and below it: its vertical pad
          f"--engine-quote-style: {quote['style']};"]
    if quote["family"]:   # else the body's
        p.append(f'--engine-quote-family: "{quote["family"]}";')
    p += [f"--engine-card-fill: {card['fill']};", f"--engine-card-radius: {px(card['radius'])};",
          f"--engine-card-outline: {px(card['outline'])};", f"--engine-card-outline-color: {card['outline-color']};",
          f"--engine-card-border: {px(card['border'])};", f"--engine-card-border-color: {card['border-color']};",
          f"--engine-card-pad: {pad(card['pad'])};", f"--engine-card-head-pad: {pad(card['head-pad'])};",
          f"--engine-card-pad-x: {card['pad'][1]:g}em;"]   # a strip reaches the card's edges by it
    p += [f"--engine-strip-tint: {round(strip['tint'] * 100, 2):g}%;", f"--engine-strip-pad: {pad(strip['pad'])};",
          f"--engine-strip-gap: {strip['gap']:g}em;"]   # above and below it (boxes.strip.gap)
    p += [f"--engine-glyph-{k}: {c};" for k, c in b["status"].items()]   # the ✓ ⚠ ✗ glyphs (--engine-status-* are the charts')
    rail = b["rail"]
    p += [f"--engine-rail-line: {px(rail['line'])};", f"--engine-rail-line-color: {rail['line-color']};",
          f"--engine-rail-badge: {px(rail['badge'])};", f"--engine-rail-dot: {px(rail['dot'])};", f"--engine-rail-ring: {rail['ring']:g};",
          f"--engine-rail-fill: {rail['fill'] or 'transparent'};", f"--engine-rail-pad: {pad(rail['pad'])};",
          f"--engine-rail-pad-y: {rail['pad'][0]:g}em;", f"--engine-rail-pad-x: {rail['pad'][1]:g}em;"]   # a mark and a date line up with the text
    gal = b["gallery"]
    p += [f"--engine-gallery-gap: {px(gal['gap'], W)};", f"--engine-gallery-pad: {pad(gal['pad'])};",
          f"--engine-gallery-pad-y: {gal['pad'][0]:g}em;",   # a caption's distance under its picture
          f"--engine-gallery-fill: {gal['fill'] or 'transparent'};"]
    refs = b["references"]
    p += [f"--engine-references-hang: {refs['hang']:g}em;", f"--engine-references-gap: {refs['gap']:g}em;"]
    p += [f"--engine-quote-attribution-gap: {quote['attribution-gap']:g}em;",   # em of the caption type: set on the
          f"--engine-note-gap: {b['note']['gap']:g}em;"]                          # caption-sized element itself
    fn = b["footnote"]   # the slide footnotes' block: its ems are of the footnote type, set on the block itself
    p += [f"--engine-footnote-rule: {px(fn['rule'])};", f"--engine-footnote-rule-length: {px(fn['rule-length'], W)};",
          f"--engine-footnote-rule-color: {fn['rule-color']};", f"--engine-footnote-width: {round(fn['width'] * 100, 2):g}%;",
          f"--engine-footnote-gap: {fn['gap']:g}em;", f"--engine-footnote-hang: {fn['hang']:g}em;",
          f"--engine-footnote-step: {fn['step']:g}em;"]
    return p


def emit_css_charts(livery: dict) -> list[str]:
    """The chart colors as --engine-data-1.., --engine-data-muted and --engine-status-*: the livery's
    mode on :root, and on a light livery the dark set on a dark slide (.engine-dark)."""
    ch = livery["charts"]
    def props(b):
        p = [f"--engine-data-{i}: {c};" for i, c in enumerate(b["categorical"], 1)]
        p.append(f"--engine-data-muted: {b['muted']};")
        return p + [f"--engine-status-{k}: {c};" for k, c in b["status"].items()]
    L = ["/* chart colors (livery.json charts) */", ":root {\n  " + "\n  ".join(props(ch[ch["mode"]])) + "\n}"]
    if ch["mode"] == "light":
        L.append(".reveal .slides section.slide.engine-dark {\n  " + "\n  ".join(props(ch["dark"])) + "\n}")
    return L


def is_cff(path: Path) -> bool:
    """An OpenType font with CFF outlines ('OTTO'): matplotlib's pdf.fonttype 42 writes one into a
    PDF as a TrueType font, which poppler reports as a mismatch, so its PDFs take Type 3."""
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"OTTO"
    except OSError:
        return False


def emit_mplstyle(livery: dict, d: Path) -> str:
    """matplotlib's style (Make.common's MATPLOTLIBRC; livery_mpl.py applies it too): the chrome of the
    livery's mode (livery.json charts.chrome), transparent figures so a plot sits on any field, the
    categorical slots as the color cycle, the base family over DejaVu Sans, and sizes in points on the
    pptx canvas (labels and titles body, ticks and legends the third list level, other text the
    caption), so a figure drawn at charts.figsize carries the slide's own text sizes. Hex values
    without '#', which starts a comment in an rc file."""
    ch = livery["charts"]
    mode = ch["mode"]
    c, b = ch["chrome"][mode], ch[mode]
    h = lambda v: v.lstrip("#").upper()
    family, files = base_font(livery)
    pt = lambda role: livery["type"]["roles"][role]["pt"]
    small = livery["type"]["levels"][2]
    cff = bool(files) and is_cff(d / files[0]["path"])
    cycle = ", ".join(f"'{h(x)}'" for x in b["categorical"])
    # the family list names the fallback itself: matplotlib builds its per-glyph chain from
    # font.family alone, so under a generic `sans-serif` a glyph the base face lacks (′, →) drew
    # as a box (#133); DejaVu Sans is matplotlib's own, always there
    rc = [
        ("font.family", f"{family}, DejaVu Sans" if family else "DejaVu Sans"),
        ("font.sans-serif", f"{family}, DejaVu Sans" if family else "DejaVu Sans"),
        ("font.size", pt("caption")),
        ("mathtext.fontset", "custom"),
        ("mathtext.rm", family or "DejaVu Sans"),
        ("mathtext.sf", family or "DejaVu Sans"),
        ("mathtext.it", f"{family or 'DejaVu Sans'}:italic"),
        ("mathtext.bf", f"{family or 'DejaVu Sans'}:bold"),
        ("mathtext.fallback", "stixsans"),
        ("text.color", h(c["text"])),
        ("axes.labelcolor", h(c["text"])),
        ("axes.edgecolor", h(c["spine"])),
        ("axes.facecolor", "none"),
        ("axes.labelsize", pt("body")),
        ("axes.titlesize", pt("body")),
        ("axes.linewidth", 0.8),
        ("axes.spines.top", False),
        ("axes.spines.right", False),
        ("axes.grid", True),
        ("axes.axisbelow", True),
        ("axes.prop_cycle", f"cycler('color', [{cycle}])"),
        ("grid.color", h(c["grid"])),
        ("grid.linewidth", 0.5),
        ("xtick.color", h(c["spine"])),
        ("ytick.color", h(c["spine"])),
        ("xtick.labelcolor", h(c["text"])),
        ("ytick.labelcolor", h(c["text"])),
        ("xtick.labelsize", small),
        ("ytick.labelsize", small),
        ("legend.fontsize", small),
        ("legend.title_fontsize", small),
        ("legend.frameon", False),
        ("lines.linewidth", 2.0),
        ("patch.edgecolor", h(ch[mode]["surface"])),
        ("figure.facecolor", "none"),
        ("figure.edgecolor", "none"),
        ("figure.titlesize", pt("subhead")),
        ("figure.figsize", ", ".join(str(v) for v in ch["figsize"]["full"])),
        ("figure.constrained_layout.use", True),
        ("savefig.facecolor", "none"),
        ("savefig.edgecolor", "none"),
        ("savefig.transparent", True),
        ("savefig.dpi", 200),
        ("savefig.pad_inches", 0),   # a tight crop adds nothing: the picture is figsize, at canvas scale
        ("svg.hashsalt", livery["name"]),   # stable ids: a rebuilt SVG is byte-identical
        ("pdf.fonttype", 3 if cff else 42),
        ("ps.fonttype", 3 if cff else 42),
        ("svg.fonttype", "path"),
    ]
    head = [f"# build/livery.mplstyle: GENERATED by livery_build.py from livery.json charts; do not edit.",
            f"# livery {livery['name']}, {mode}; sizes in points on its {livery['type']['canvas']['w'] / 72:g} x "
            f"{livery['type']['canvas']['h'] / 72:g} in canvas: draw at charts.figsize.",
            "# the base family is a CFF OpenType font: PDF takes Type 3 (see is_cff())" if cff else None]
    return "\n".join([x for x in head if x] + [f"{k}: {v}" for k, v in rc]) + "\n"


# the roles a light livery's dark slide ({.brand-dark}, .engine-dark) swaps, as pptx's
# common.palette(): its text, muted text, accents and table blends; restored inside a box with a
# fill of its own (DARK_BOXES), which keeps its colors
DARK_SWAP = {"foreground": "on-dark", "muted": "dark-muted", "primary-contrast": "secondary", "primary": "secondary",
             "table-rule": "dark-rule", "table-band": "dark-band"}
DARK_BOXES = (".engine-card", ".engine-lead", ".engine-strip", ".callout")


def emit_css_dark_slide(livery: dict) -> list[str]:
    """A light livery's dark content slide: on the slide the roles of DARK_SWAP take their dark
    values (and reveal's text colors, which :root computed once, the title on-dark whatever
    frametitle.color says, and the hairline the dark-rule blend); in a box of DARK_BOXES (and a caution slide's body field) the livery's own; inline
    Graphviz turned to the dark as a dark livery's (lightness flipped, hues kept). Live mermaid
    reads :root (deferred)."""
    c = {**livery["roles"], **livery["blends"]}
    def swap(to):
        p = [f"--engine-{k}: {c[v if to else k]};" for k, v in DARK_SWAP.items()]
        fg = c["on-dark" if to else "foreground"]
        return "\n  ".join(p + [f"--r-main-color: {fg};", f"--r-heading-color: {fg};", f"color: {fg};"])
    sel = ".reveal .slides section.slide.engine-dark"
    boxes = ",\n".join([f"{sel} :is({', '.join(DARK_BOXES)})", f"{sel}.engine-caution > .engine-body"])
    return ["/* the dark slide (.engine-dark): the dark roles on it, the livery's in a box of its own */",
            f"{sel} {{\n  {swap(True)}\n  --engine-title-color: {c['on-dark']};\n  --engine-title-rule-color: {c['dark-rule']};\n}}",
            f"{boxes} {{\n  {swap(False)}\n}}",
            f"{sel} svg:has(> g.graph) > g.graph > polygon:first-of-type {{ fill: transparent; stroke: transparent; }}",
            f"{sel} svg:has(> g.graph) {{ filter: invert(1) hue-rotate(180deg); }}"]


def emit_css_dark() -> list[str]:
    """A dark livery's extras: Quarto tints callout titles toward its light $body-bg, and Graphviz
    draws black on white inline; the diagram is turned to the dark (lightness flipped, hues kept)."""
    L = ["/* mode: dark */"]
    for name, role in (("note", "primary-contrast"), ("tip", "highlight"), ("important", "foreground"),
                       ("warning", "accent"), ("caution", "accent")):
        L.append(f".reveal div.callout.callout-{name}.callout-style-default .callout-title "
                 f"{{ background-color: color-mix(in srgb, var(--engine-{role}) 18%, var(--engine-background)); }}")
    L.append(".reveal svg:has(> g.graph) > g.graph > polygon:first-of-type { fill: transparent; stroke: transparent; }")
    L.append(".reveal svg:has(> g.graph) { filter: invert(1) hue-rotate(180deg); }")
    return L


# composition -> the selector its custom properties go on, in cascade order: base, photo, light,
# photo-light, then the band (prefixed with html so it outranks light, as it wins over it)
TITLE_SEL = "div.reveal div.slides section.engine-title.quarto-title-block"
CLOSING_SEL = ".reveal .slides section.slide.level2.closing"
CSEL = {"title": TITLE_SEL,
        "title-photo": TITLE_SEL + ".engine-title-photo",
        "title-light": "html.engine-title-light " + TITLE_SEL,
        "title-photo-light": "html.engine-title-light " + TITLE_SEL + ".engine-title-photo",
        "title-band": "html " + TITLE_SEL + ".engine-band",
        "closing": CLOSING_SEL,
        "closing-light": "html.engine-title-light " + CLOSING_SEL,
        "closing-band": "html " + CLOSING_SEL + ".engine-band",
        "section": ".reveal .slides section.slide.engine-section",
        "feature": ".reveal .slides section.slide.level2.feature"}


def emit_css_compositions(livery: dict) -> list[str]:
    """Each composition's boxes and roles as one set of generic --engine-cmp-* properties on its
    selector (CSEL), so the scss reads one name set whatever the variant (slide pixels), with its
    art as the section's background and its mark's and sign-off's images."""
    px = lambda v, axis: f"{round(v * axis, 1):g}px"
    role = lambda r: r if str(r).startswith("#") else f"var(--engine-{r})"
    L = ["/* compositions (livery_build.py compositions()): boxes in slide px, roles as vars */"]
    for comp, sel in CSEL.items():
        c, props = livery["compositions"][comp], []
        for k in BOXED:   # x y w h, and r b: the distance of its right and bottom edges from the slide's
            x, y, w, h = c[k]["box"] if c[k] and c[k].get("box") else [0, 0, 0, 0]
            props.append(f"--engine-cmp-{k}-display: {'block' if c[k] and c[k].get('box') else 'none'};")
            props += [f"--engine-cmp-{k}-{a}: {px(v, W if a in 'xwr' else H)};"
                      for a, v in zip("xywhrb", (x, y, w, h, 1 - x - w, 1 - y - h))]
        props.append(f"--engine-cmp-field: {role(c['field']['role']) if c['field'] else 'transparent'};")
        col = c["column"]
        props.append(f"--engine-cmp-text: {role(col['role'])};")
        props.append(f"--engine-cmp-column-justify: {'center' if col['anchor'] == 'middle' else 'flex-start'};")
        props.append(f"--engine-cmp-column-tab: {'block' if col['tab'] else 'none'};")
        props.append(f"--engine-cmp-column-align: {col['align']};")
        props.append(f"--engine-cmp-rule-mx: {'auto' if col['align'] == 'center' else '0'};")   # a centered rule
        if "elements" in col:   # a cover's elements: in the column or the byline's box, in order, in a color
            by = c["byline"]; boxed = by["elements"] if by and by["box"] else []
            order = {}   # flex order; an institute right after an author shares its order, so each
            for part in (col["elements"], boxed):   # author's affiliations stay beside it (by-author)
                for i, e in enumerate(part):
                    order[e] = order["author"] if e == "institute" and i and part[i - 1] == "author" else i
            for e in ELEMENTS:
                props.append(f"--engine-cmp-{e}-col: {'block' if e in col['elements'] else 'none'};")
                props.append(f"--engine-cmp-{e}-byl: {'block' if e in boxed else 'none'};")
                props.append(f"--engine-cmp-{e}-order: {order.get(e, 0)};")
                props.append(f"--engine-cmp-{e}-color: {role(by['role'] if by and e in by['elements'] else col['role'])};")
            ce = col["elements"]   # the rule under the title, or under the subtitle that follows it
            after = "subtitle" if "subtitle" in ce and ce.index("subtitle") == ce.index("title") + 1 else "title"
            props.append(f"--engine-cmp-rule-order: {order[after]};")
            if by:
                props.append(f"--engine-cmp-byline-justify: {'center' if by['anchor'] == 'middle' else 'flex-start'};")
                props.append(f"--engine-cmp-byline-align: {by['align']};")
        rule = col["rule"] or [0, 0]
        props.append(f"--engine-cmp-rule-display: {'block' if col['rule'] else 'none'};")
        props += [f"--engine-cmp-rule-w: {px(rule[0], W)};", f"--engine-cmp-rule-h: {px(rule[1], H)};"]
        if c["fineprint"]:
            props.append(f"--engine-cmp-fineprint-color: {role(c['fineprint']['role'])};")
            props.append(f"--engine-cmp-fineprint-justify: {'flex-end' if c['fineprint']['anchor'] == 'bottom' else 'flex-start'};")
        for k in ("band", "bar", "panel"):
            if c[k]:
                fill = role(c[k]["role"])
                op = c[k].get("opacity", 1)
                props.append(f"--engine-cmp-{k}-fill: " + (fill if op == 1 else f"color-mix(in srgb, {fill} {op * 100:g}%, transparent)") + ";")
        if c["eyebrow"]:
            props.append(f"--engine-cmp-eyebrow: {c['eyebrow']['color']};")   # hex: compositions() resolved it
            props.append(f'--engine-cmp-eyebrow-label: "{c["eyebrow"]["label"]} ";')
        props.append(f"--engine-cmp-eyebrow-display: {'block' if c['eyebrow'] else 'none'};")
        art = livery.get("art", {}).get(c["art"]) if c["art"] else None   # the art under the field, or none
        props.append(f'background: {"url(%s) center / cover no-repeat" % json.dumps(Path(art).name) if art else "none"};')
        L.append(f"{sel} {{\n  " + "\n  ".join(props) + "\n}")
        for k, rule in (("mark", "::after"), ("signoff", " .engine-signoff")):
            if c[k] and c[k].get("img"):   # its file, the composition's own (compositions())
                L.append(f'{sel}{rule} {{ background-image: url("{Path(c[k]["img"]).name}"); }}')
    return L


def ancestors(d: Path) -> list[Path]:
    """The livery and its `extends` chain, parents first."""
    knobs = yaml.safe_load((d / "livery.yml").read_text()) or {}
    parent = knobs.get("extends")
    return (ancestors(d.parent / parent) if parent else []) + [d]


def overrides(d: Path, name: str, comment: str = "% {}") -> str:
    """The livery's and its ancestors' overrides/<name>, concatenated, parents first."""
    out = ""
    for a in ancestors(d):
        f = a / "overrides" / name
        if f.exists():
            out += comment.format(f"overrides from {os.path.relpath(f, d)}") + "\n" + f.read_text()
    return out


def emit_theme(livery: dict) -> str:
    """engine.theme (pandoc's highlight theme, colors as $role or $blend) with the livery's hex."""
    colors = {**livery["roles"], **livery["blends"]}
    def fill(v):
        if isinstance(v, str) and v.startswith("$"):
            return colors[v[1:]]
        return {k: fill(x) for k, x in v.items()} if isinstance(v, dict) else v
    theme = fill(json.loads((Path(__file__).parent / "engine.theme").read_text()))
    return json.dumps(theme, indent=2) + "\n"


def outputs(d: Path) -> dict[Path, str]:
    livery, sources = resolve(d)
    build = d / "build"
    return {build / "livery.json": json.dumps(livery, indent=2, sort_keys=True) + "\n",
            build / "livery.theme": emit_theme(livery),
            build / "livery.sty": emit_sty(livery, sources, overrides(d, "livery-extra.sty")),
            build / "livery.css": emit_css(livery, overrides(d, "livery-extra.css", "/* {} */")),
            build / "livery.mplstyle": emit_mplstyle(livery, d)}


def build(liveries: list[Path], check: bool = False, template_note: bool = True) -> int:
    """Write each livery's build/ (or with check, compare it); 1 when one is stale. template_note:
    say so when the livery has no template.pptx yet (`livery all` builds it next, so it doesn't)."""
    stale = 0
    for d in liveries:
        out = outputs(d)
        tmpl = d / (json.loads(out[d / "build" / "livery.json"])["pptx"].get("template") or "template.pptx")
        if template_note and not tmpl.exists():   # `livery template` builds it from build/livery.json
            print(f"{d.name}: no {tmpl} yet: run livery template {d}", file=sys.stderr)
        for target, text in out.items():
            if check:
                if not target.exists() or target.read_text() != text:
                    print(f"stale: {target} (run livery build {d})"); stale = 1
                else:
                    print(f"fresh: {target}")
            else:
                target.parent.mkdir(exist_ok=True)
                target.write_text(text)
                print(f"wrote {target}")
    return stale
