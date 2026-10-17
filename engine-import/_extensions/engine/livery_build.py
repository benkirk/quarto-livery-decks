#!/usr/bin/env python3
"""Resolve a livery (_brand.yml + livery.yml, `extends` applied) into build/livery.{json,sty,css}.

    livery_build.py <livery dir>...          write build/ (committed)
    livery_build.py --check <livery dir>...  exit 1 if a committed build/ is stale

Color names in livery.yml roles resolve against the brand palette; a value starting with '#'
passes through. `extends: <name>` names a sibling livery whose resolved values the child's
override key by key (dicts merge, everything else replaces); the parent's relative paths are
rebased onto the child. `derived` holds the theme's blends of two roles (BLENDS), computed
here unless livery.yml sets the key. livery.json is the one truth (Lua and Python read it);
livery.sty is what engine_livery.sty inputs (overrides/livery-extra.sty of the livery and its
ancestors appended); livery.css what engine-revealjs.lua attaches; livery.theme is pandoc's
highlight theme, engine.theme with the roles filled in. `marks` names the mark and sign-off
for each field by its role (MARK_ROLES); `installed-fonts` names installed faces to prefer;
`compositions` the title, closing, section and feature slides as boxes (compositions()).
"""

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

# (key, role a, role b, share of a): the theme's recipes, engine-revealjs.scss `table` and
# `.engine-caution`, beamerinnerthemeEngine.sty `enginecautionfill`
BLENDS = [
    ("table-rule", "foreground", "surface", 0.20),
    ("table-band", "surface", "background", 0.60),
    ("caution-fill", "warning", "background", 0.18),
    ("alert-text", "accent", "dark", 0.72),
    ("rule", "foreground", "surface", 0.30),
]
# livery role -> the LaTeX color the themes read (engine_livery.sty's six, plus the four new)
ROLE_TEX = {"primary": "BrandPrimary", "primary-text": "BrandPrimaryText",
            "primary-contrast": "BrandPrimaryContrast", "secondary": "BrandSecondary",
            "accent": "BrandAccent", "highlight": "BrandHighlight", "foreground": "BrandText", "background": "BrandBackground",
            "muted": "BrandMuted", "surface": "BrandSurface", "warning": "BrandWarning", "dark": "BrandDark"}
W, H = 1600, 900   # revealjs slide pixels (engine-revealjs.scss)
# art.<kind> files: backgrounds per slide kind, and titlegraphic, the title photo a deck sets none of
ART_KINDS = ("title", "section", "closing", "content", "titlegraphic")
# the title slide's composition (title: in livery.yml) when it is the band: fractions of the slide,
# roles for the colors; its strip wears marks.<field>
BAND = {"top": 0.27, "bottom": 0.72, "split": 0.62, "band": "primary", "field": "dark", "field-text": "background"}
# theme1.xml slot -> role, the slot contract of design section 4 (livery_template.py writes it)
SLOT_ROLES = {"dk1": "foreground", "lt1": "background", "dk2": "primary", "lt2": "surface",
              "accent1": "secondary", "accent2": "highlight", "accent3": "dark", "accent4": "accent",
              "accent5": "warning", "accent6": "primary-contrast", "hlink": "primary", "folHlink": "highlight"}
# the livery.yml keys this script reads; any other is reported, not silently dropped
KNOWN = {"name", "extends", "roles", "derived", "aspect", "geometry", "divider", "art", "pptx", "overrides",
         "latex", "signoff", "title", "marks", "installed-fonts", "compositions", "feature"}
# the fields every livery has: content slides on the background role, the colored fields (dividers,
# the cover title and closing, feature covers) on primary; a band title adds its own field role
MARK_ROLES = ("background", "primary")
# the compositions every livery.json carries (compositions()), and the keys each one has (null when absent)
COMPOSITIONS = ("title", "title-photo", "title-light", "title-photo-light", "title-band",
                "closing", "closing-light", "closing-band", "section", "feature")
FEATURE_STYLES = ("bar", "cover")   # feature.style: the photo under a bar and panel, or the cover
COMP_KEYS = ("field", "art", "photo", "band", "waves", "bar", "panel", "mark", "signoff", "column", "fineprint", "eyebrow")
# installed-fonts faces, and how a bare family string names them (full name, PostScript name)
FACES = {"regular": ("", ""), "bold": (" Bold", "-Bold"), "italic": (" Italic", "-Italic"),
         "bolditalic": (" Bold Italic", "-BoldItalic")}
FACE_KEYS = ("regular", "bold", "italic", "bolditalic", "semibold")


def mix(a: str, b: str, share: float) -> str:
    """Sass mix(): a's share of each channel plus b's remainder, rounded; '#RRGGBB' in and out."""
    pairs = zip(bytes.fromhex(a.lstrip("#")), bytes.fromhex(b.lstrip("#")))
    return "#" + "".join(f"{round(x * share + y * (1 - share)):02X}" for x, y in pairs)


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


def read(d: Path) -> dict:
    brand = yaml.safe_load((d / "_brand.yml").read_text()) or {}
    knobs = yaml.safe_load((d / "livery.yml").read_text()) or {}
    for k in sorted(set(knobs) - KNOWN):
        print(f"warning: {d.name}: unknown livery.yml key {k!r} (ignored)", file=sys.stderr)
    merged = {"brand": brand, **{k: v for k, v in knobs.items() if k != "extends"}}
    parent = knobs.get("extends")
    if parent:   # pptx.scheme holds only explicit overrides; resolve() fills the rest from the roles
        merged = merge(rebase(read(d.parent / parent), d.parent / parent, d), merged)
    return merged


def resolve(d: Path) -> tuple[dict, dict]:
    """(livery.json content, the roles' source names for livery.sty's \\colorlet lines)."""
    data = read(d)
    palette = {k: str(v).upper() for k, v in data["brand"].get("color", {}).get("palette", {}).items()}

    def hex_of(name):
        if isinstance(name, str) and name.startswith("#"):
            return name.upper()
        if name in palette:
            return palette[name]
        sys.exit(f"{d.name}: color {name!r} is neither a palette name nor a hex value")

    color = data["brand"].get("color", {})
    sources = {k: color[k] for k in ("primary", "secondary", "foreground", "background") if k in color}
    sources.update(data.get("roles", {}))
    roles = {k: hex_of(v) for k, v in sources.items()}
    derived = {k: mix(roles[a], roles[b], share) for k, a, b, share in BLENDS if a in roles and b in roles}
    derived.update({k: hex_of(v) for k, v in data.get("derived", {}).items()})
    out = {
        "name": data.get("name", d.name),
        "palette": palette,
        "roles": roles,
        "derived": derived,
        "typography": data["brand"].get("typography", {}),
        "logo": data["brand"].get("logo", {}),
    }
    for key in ("aspect", "geometry", "divider", "art", "pptx", "overrides", "latex"):
        if key in data:
            out[key] = data[key]
    for corner, legal in (("logo", ("top-right", "top-left", "none")), ("pagenumber", ("bottom-left", "bottom-right"))):
        v = out.get("geometry", {}).get(corner, {}).get("corner")
        if v is not None and v not in legal:
            sys.exit(f"{d.name}: geometry.{corner}.corner {v!r} is not one of {legal}")
    if "signoff" in data:   # the sign-off lockup's box; its images (light, dark) are marks defaults
        so = {k: v for k, v in data["signoff"].items() if k not in ("light", "dark")}
        if so.get("corner", "bottom-left") not in ("bottom-left", "bottom-right"):
            sys.exit(f"{d.name}: signoff.corner {so['corner']!r} is not bottom-left or bottom-right")
        so.setdefault("height", 0.05); so.setdefault("bottom", 0.03); so.setdefault("corner", "bottom-left")
        if "aspect" not in so:
            sys.exit(f"{d.name}: signoff.aspect (width / height of the image) is required")
        out["signoff"] = so
    if "title" in data:   # only when set, so a livery without it keeps its build/ unchanged
        out["title"] = band(d.name, data["title"], out)
    out["marks"] = marks(d.name, data, out)
    out["compositions"] = compositions(d.name, data, out)
    if "installed-fonts" in data:
        out["installed-fonts"] = installed_fonts(d.name, data["installed-fonts"])
    out.setdefault("pptx", {})
    # the slot contract, from the roles; a livery's own pptx.scheme overrides slot by slot
    scheme = {slot: roles[role] for slot, role in SLOT_ROLES.items() if role in roles}
    scheme.update({k: hex_of(v) for k, v in out["pptx"].get("scheme", {}).items()})
    out["pptx"]["scheme"] = scheme
    tmpl = d / out["pptx"].get("template", "template.pptx")
    if not tmpl.exists():   # livery_template.py builds it from build/livery.json, so only a warning
        print(f"{d.name}: pptx template {tmpl} missing; run livery_template.py", file=sys.stderr)
    return out, sources


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
    for k in ("logo", "signoff"):   # the old spelling of marks.<field>, which marks() reads
        t.pop(k, None)
    if "signoff" in out:
        t.setdefault("signoff-height", out["signoff"]["height"])
    t.setdefault("logo-height", out.get("geometry", {}).get("logo", {}).get("title", 0.09))
    return t


def marks(name: str, data: dict, out: dict) -> dict:
    """{role: {logo, logo-print?, signoff?}} as paths, for MARK_ROLES, the band's field and every role
    marks: names. background defaults to logo.medium.light and signoff.light, primary to the dark
    ones, any other role to primary's; each key defaults on its own."""
    images, medium = out["logo"].get("images", {}), out["logo"].get("medium", {})
    so = data.get("signoff") or {}
    given = {k: dict(v or {}) for k, v in (data.get("marks") or {}).items()}
    t = data.get("title") or {}
    field = {**BAND, **t}["field"] if t.get("style") == "band" else None
    alias = {k: t[k] for k in ("logo", "signoff") if k in t}
    if alias and field:
        print(f"warning: {name}: title.logo and title.signoff are deprecated; write marks: {{{field}: ...}}", file=sys.stderr)
        given[field] = {**alias, **given.get(field, {})}
    elif alias:
        print(f"warning: {name}: title.logo and title.signoff apply to a band title only (ignored)", file=sys.stderr)
    defaults = {"background": {"logo": medium.get("light"), "signoff": so.get("light")},
                "primary": {"logo": medium.get("dark"), "signoff": so.get("dark")}}
    roles = list(MARK_ROLES) + [r for r in [field, *given] if r and r not in MARK_ROLES]
    names = {}
    for role in dict.fromkeys(roles):
        if role not in out["roles"]:
            sys.exit(f"{name}: marks.{role} is not a role")
        bad = set(given.get(role, {})) - {"logo", "signoff"}
        if bad:
            sys.exit(f"{name}: marks.{role} takes logo and signoff, not {sorted(bad)}")
        names[role] = {**(defaults[role] if role in defaults else names["primary"]), **given.get(role, {})}
    res = {}
    for role, m in names.items():
        if m["logo"] not in images:
            sys.exit(f"{name}: marks.{role}.logo {m['logo']!r} is not a logo.images name")
        r = {"logo": images[m["logo"]]["path"]}
        if m["logo"] + "-print" in images:   # LaTeX takes the print (CMYK) lockup when there is one
            r["logo-print"] = images[m["logo"] + "-print"]["path"]
        if "signoff" in out:
            if m.get("signoff") not in images:
                sys.exit(f"{name}: marks.{role}.signoff {m.get('signoff')!r} is not a logo.images name")
            r["signoff"] = images[m["signoff"]]["path"]
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


def compositions(name: str, data: dict, out: dict) -> dict:
    """The title, closing, section and feature slides as boxes ([x, y, w, h], slide fractions, y
    down) and roles, one fully resolved entry per COMPOSITIONS name with every COMP_KEYS key, so
    each format's drawer picks a name and applies no variant logic. Derived from the geometry,
    title, signoff and art knobs; livery.yml `compositions: {<name>: {<key>: ...}}` overrides,
    an override on title reaching its photo and light variants, one on closing its light one."""
    g = out.get("geometry", {}); m = g.get("margin", 0.06); logo = g.get("logo", {})
    aw, ah = (int(v) for v in str(out.get("aspect", "16:9")).split(":"))
    hw = ah / aw   # a height as a fraction of the width
    art = out.get("art") or {}
    has_art = lambda k: isinstance(art.get(k), str)
    waves = art.get("waves")
    t = {**BAND, "logo-height": logo.get("title", 0.09), **(out.get("title") or {})}
    so = out.get("signoff")
    if so:
        t.setdefault("signoff-height", so["height"])

    def mark(y, h, role):   # the mark top left on a field; null where the livery draws none
        if logo.get("corner", "top-right") == "none":
            return None
        return {"role": role, "box": _box(m, y, h * logo.get("aspect", 1) * hw, h)}

    def signoff(role):
        if not so:
            return None
        h = so["height"]; w = h * so["aspect"] * hw
        x = m if so["corner"] == "bottom-left" else 1 - m - w
        return {"role": role, "box": _box(x, 1 - so["bottom"] - h, w, h)}

    def strip(role):   # the band's strip: the sign-off in its corner, the mark opposite, centred
        mid, left = (1 + t["bottom"]) / 2, None
        sig = None
        if so:
            h = t["signoff-height"]; w = h * so["aspect"] * hw
            left = so["corner"] == "bottom-left"
            sig = {"role": role, "box": _box(m if left else 1 - m - w, mid - h / 2, w, h)}
        mk = None
        if logo.get("corner", "top-right") != "none":
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
    tm = (0.06, logo.get("title", 0.09))   # the title mark's y and height; the column starts 0.05 under it
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
                       column={"box": [col[0], col[1], 0.44, col[3]]})

    def light(c):
        w = c["waves"]
        return variant(c, art=None, field={"role": "background"},
                       waves=w and {**w, "style": "lines", "opacity": []} if w and w["style"] == "bands" else w,
                       mark=c["mark"] and {**c["mark"], "role": "background"},
                       signoff=c["signoff"] and {**c["signoff"], "role": "background"},
                       column={"role": "foreground"},
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
    cm = (0.09, logo.get("closing", 0.10))   # the closing mark's y and height; the column starts 0.03 under it
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
    div = g.get("divider", {}); dv = out.get("divider", {})
    section = {**empty,
               "field": {"role": "primary", "box": _box(0, 0, 1, 1)},
               "art": "section" if has_art("section") else None,
               "waves": wave("bands", shift.get("section", 0), [0.18, 0.10]),
               "mark": mark(0.08, logo.get("section", 0.08), "primary"),
               "signoff": signoff("primary"),
               "column": {"box": _box(m, div.get("top", 0.1333), 0.62, 1 - div.get("top", 0.1333) - div.get("bottom", 0.0889)),
                          "anchor": "middle", "role": "primary-text", "tab": bool(dv.get("tab", True)), "rule": None},
               "eyebrow": {"label": dv.get("label", "Section"), "color": dv.get("label-color", "secondary")}}
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
           "title-light": light(title),
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
    for k, c in res.items():
        for role in [c[b]["role"] for b in COMP_KEYS if isinstance(c[b], dict) and "role" in c[b]]:
            if role not in out["roles"]:
                sys.exit(f"{name}: compositions.{k}: role {role!r} is not a role")
    return res


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


def heading_font(livery: dict) -> tuple[str, list]:
    """The headings family and its files when it is a second family with files of its own."""
    t = livery["typography"]
    family = t.get("headings", "")
    if family and family != t.get("base", ""):
        for font in t.get("fonts", []):
            if font.get("family") == family and font.get("files"):
                return family, font["files"]
    return "", []


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
    L.append("% derived blends")
    for key, hexv in livery["derived"].items():
        L.append(f"\\definecolor{{{tex_name('brand-' + key, {})}}}{{HTML}}{{{hexv[1:]}}}")
    marks = livery["marks"]
    stem = lambda p: texpath(Path(p).with_suffix("").as_posix())   # \\includegraphics finds the extension
    L.append("% marks: light on the background field, dark on primary (the print lockup when there is one)")
    for variant, role in (("light", "background"), ("dark", "primary")):
        L.append(f"\\def\\engine@logo@{variant}{{{stem(marks[role].get('logo-print', marks[role]['logo']))}}}")
    if "signoff" in livery:   # the sign-off lockup at the foot (its corner, height and bottom are geometry)
        so = livery["signoff"]
        L.append("% the sign-off lockup (signoff), light and dark, and its box")
        for variant, role in (("light", "background"), ("dark", "primary")):
            L.append(f"\\def\\engine@signoff@{variant}{{{stem(marks[role]['signoff'])}}}")
        for k in ("height", "bottom", "corner"):
            L.append(f"\\def\\engine@signoff{k}{{{so[k]}}}")
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
    installed = livery.get("installed-fonts", {})
    if installed:   # installed faces fonts=brand prefers (engine_livery.sty), by full name
        L.append("% installed fonts to prefer under fonts=brand (installed-fonts), by full name")
        if "base" in installed:
            L.append(f"\\def\\engine@font@installed{{{installed['base']['family']}}}")
        for k, tex in (("base", "base"), ("headings", "head")):
            for face, names in installed.get(k, {}).get("faces", {}).items():
                L.append(f"\\def\\engine@installed@{tex}@{face}{{{names[0]}}}")
    L.append("% geometry, in fractions of the slide")
    geom = livery.get("geometry", {})
    for k, v in geom.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                L.append(f"\\def\\engine@geom@{k}{k2}{{{v2}}}")
        elif not isinstance(v, list):
            L.append(f"\\def\\engine@geom@{k.replace('-', '')}{{{v}}}")
    L.append(f"\\def\\engine@divider@label{{{livery.get('divider', {}).get('label', 'Section')}}}")
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
    for kind in ART_KINDS:
        if isinstance(art.get(kind), str):
            L.append(f"\\def\\engine@art@{kind}{{{stem(art[kind])}}}")
    t = livery.get("title", {})
    if t.get("style") == "band":   # the band title: fractions, colors, the strip's two images
        L.append("% the title's band composition (title: in livery.yml)")
        L.append("\\def\\engine@title@style{band}")
        for k in ("top", "bottom", "split", "logo-height", "signoff-height"):
            if k in t:
                L.append(f"\\def\\engine@title@{k.replace('-', '')}{{{t[k]}}}")
        for k, tex in (("band", "EngineBandFill"), ("field", "EngineBandField"), ("field-text", "EngineBandFieldText")):
            L.append(f"\\colorlet{{{tex}}}{{{ROLE_TEX.get(t[k], 'BrandDark')}}}")
        m = marks[t["field"]]   # the strip's two images
        L.append(f"\\def\\engine@title@logoimg{{{stem(m.get('logo-print', m['logo']))}}}")
        if "signoff" in m:
            L.append(f"\\def\\engine@title@signoffimg{{{stem(m['signoff'])}}}")
    L += emit_sty_compositions(livery, stem)
    L.append(extra.rstrip("\n"))
    L.append(r"\liveryrestoreat")
    return "\n".join(L) + "\n"


# the role each composition key is drawn in -> the colorlet suffix livery.sty gives it
COMP_COLORS = {"field": "Field", "band": "Band", "waves": "Waves", "bar": "Bar", "panel": "Panel",
               "column": "Text", "fineprint": "Fineprint"}
BOXED = ("field", "photo", "band", "bar", "panel", "mark", "signoff", "column", "fineprint")


def emit_sty_compositions(livery: dict, stem) -> list[str]:
    """compositions as \\engine@c@<comp>@<key>@x|y|w|h (comp without hyphens), scalars, the roles as
    EngineC<comp><Key> colors and the image stems; an absent key leaves its macros undefined."""
    tex = lambda role: ROLE_TEX.get(role, "BrandDark")
    L = ["% compositions (livery_build.py compositions()): boxes in fractions of the slide, y down"]
    for comp, c in livery["compositions"].items():
        n = comp.replace("-", "")
        d = lambda k, v: L.append(f"\\def\\engine@c@{n}@{k}{{{v}}}")
        for k in BOXED:
            if c[k]:
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
        if col["rule"]:
            d("column@rule@w", col["rule"][0]); d("column@rule@h", col["rule"][1])
        if c["fineprint"]:
            d("fineprint@anchor", c["fineprint"]["anchor"])
        if c["eyebrow"]:
            e = c["eyebrow"]
            d("eyebrow@label", e["label"])
            if str(e["color"]).startswith("#"):
                L.append(f"\\definecolor{{EngineC{n}Eyebrow}}{{HTML}}{{{e['color'][1:].upper()}}}")
            else:
                L.append(f"\\colorlet{{EngineC{n}Eyebrow}}{{{tex(e['color'])}}}")
        for k, kind in (("mark", "logo"), ("signoff", "signoff")):
            if c[k]:
                m = livery["marks"].get(c[k]["role"], livery["marks"]["primary"])   # as livery.mark()
                img = m.get("logo-print", m["logo"]) if kind == "logo" else m.get("signoff")
                if img:
                    d(f"{k}@img", stem(img))
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
    for fam, fs, inst in ((family, files, installed.get("base")), (hfamily, hfiles, installed.get("headings"))):
        for f in fs:   # an installed face first, by full and PostScript name (CSS local() matches no family)
            names = (inst or {}).get("faces", {}).get(face_of(f), [])
            local = "".join(f'local("{n}"), ' for n in names)
            L.append(f'@font-face {{ font-family: "{fam}"; font-style: {f.get("style", "normal")}; '
                     f'font-weight: {f.get("weight", 400)}; font-display: block; '
                     f'src: {local}url("{Path(f["path"]).name}") format("{"opentype" if Path(f["path"]).suffix == ".otf" else "truetype"}"); }}')
    props = [f"--engine-{k}: {v};" for k, v in livery["roles"].items()]
    props += [f"--engine-{k}: {v};" for k, v in livery["derived"].items()]
    geom = livery.get("geometry", {})
    logo = geom.get("logo", {})
    px = lambda frac, axis=H: f"{round(frac * axis, 1):g}px"
    if "height" in logo:
        props.append(f"--engine-logo-h: {px(logo['height'])};")   # 0.0644 * 900 is the scss's 58px
        if "aspect" in logo:
            props.append(f"--engine-logo-w: {round(logo['height'] * H, 1) * logo['aspect']:.1f}px;")
    if "aspect" in logo:
        props.append(f"--engine-logo-aspect: {logo['aspect']};")
    for k in ("top", "title", "section", "closing"):   # the logo's top, and its height per slide kind
        if k in logo:
            props.append(f"--engine-logo-{k}{'' if k == 'top' else '-h'}: {px(logo[k])};")
    for k in ("margin", "tab"):
        if k in geom:
            props.append(f"--engine-{k}: {px(geom[k], W)};")
    for k, v in geom.get("divider", {}).items():
        props.append(f"--engine-divider-{k}: {px(v)};")
    for k, v in geom.get("full", {}).items():
        props.append(f"--engine-full-{k}: {px(v, W if k == 'pad' else H)};")
    if "label-color" in livery.get("divider", {}):
        props.append(f"--engine-divider-label: {livery['divider']['label-color']};")
    props.append(f'--engine-font-family: "{family}";')
    if hfamily:
        props.append(f'--engine-heading-font-family: "{hfamily}";')
    props.append("--engine-overlay: color-mix(in srgb, var(--engine-dark) 72%, transparent);")
    # the content-slide mark's corner (top-right | top-left | none) and the page number's; the title
    # box gives way on the mark's side
    corner = logo.get("corner", "top-right")
    margin = "var(--engine-margin)"
    beside = f"calc({margin} + 40px + var(--engine-logo-w))"
    props.append(f"--engine-logo-left: {margin if corner == 'top-left' else 'auto'};")
    props.append(f"--engine-logo-right: {'auto' if corner == 'top-left' else margin};")
    props.append(f"--engine-logo-position: {'left' if corner == 'top-left' else 'right'} top;")
    props.append(f"--engine-logo-content: {'none' if corner == 'none' else '\"\"'};")
    props.append(f"--engine-title-left: {beside if corner == 'top-left' else margin};")
    props.append(f"--engine-title-right: {beside if corner == 'top-right' else margin};")
    pn = geom.get("pagenumber", {}).get("corner", "bottom-left")
    props.append(f"--engine-pagenumber-left: {'auto' if pn == 'bottom-right' else '50px'};")
    props.append(f"--engine-pagenumber-right: {'50px' if pn == 'bottom-right' else 'auto'};")
    if "signoff" in livery:
        so = livery["signoff"]
        props.append("--engine-signoff-display: block;")
        props.append(f"--engine-signoff-h: {px(so['height'])};")
        props.append(f"--engine-signoff-w: {round(so['height'] * H, 1) * so['aspect']:.1f}px;")
        props.append(f"--engine-signoff-bottom: {px(so['bottom'])};")
        props.append(f"--engine-signoff-left: {margin if so['corner'] == 'bottom-left' else 'auto'};")
        props.append(f"--engine-signoff-right: {'auto' if so['corner'] == 'bottom-left' else margin};")
        props.append(f"--engine-signoff-position: {'left' if so['corner'] == 'bottom-left' else 'right'} bottom;")
    t = livery.get("title", {})
    band = t.get("style") == "band"
    if band:   # the band title's box, text column, strip and images (engine-revealjs.scss .engine-band)
        top, bottom = t["top"], t["bottom"]
        props += [f"--engine-band-top: {px(top)};", f"--engine-band-height: {px(bottom - top)};",
                  f"--engine-band-split: {t['split'] * 100:g}%;",
                  f"--engine-band-text-w: calc({px(t['split'], W)} - var(--engine-margin) - 64px);",
                  f"--engine-band-strip: {px((1 - bottom) / 2)};",   # the strip's middle, from the bottom
                  f"--engine-band-fill: var(--engine-{t['band']});", f"--engine-band-field: var(--engine-{t['field']});",
                  f"--engine-band-field-text: var(--engine-{t['field-text']});",
                  f"--engine-band-logo-h: {px(t['logo-height'])};",
                  f"--engine-band-logo-w: {round(t['logo-height'] * H, 1) * logo.get('aspect', 1):.1f}px;"]
        so_left = livery.get("signoff", {}).get("corner", "bottom-left") == "bottom-left" and "signoff" in livery
        props += [f"--engine-band-logo-left: {'auto' if so_left else margin};",
                  f"--engine-band-logo-right: {margin if so_left else 'auto'};"]
        if "signoff" in livery:
            props += [f"--engine-band-signoff-h: {px(t['signoff-height'])};",
                      f"--engine-band-signoff-w: {round(t['signoff-height'] * H, 1) * livery['signoff']['aspect']:.1f}px;"]
    L.append(":root {\n  " + "\n  ".join(props) + "\n}")
    # Quarto sets --mermaid-* on :root from its Sass; html:root outranks it, so mermaid wears the roles
    L.append("html:root {\n  --mermaid-bg-color: var(--engine-background);\n  --mermaid-node-bg-color: var(--engine-surface);"
             "\n  --mermaid-node-fg-color: var(--engine-foreground);\n  --mermaid-fg-color: var(--engine-foreground);"
             "\n  --mermaid-edge-color: var(--engine-foreground);\n  --mermaid-label-bg-color: var(--engine-background);"
             "\n  --mermaid-label-fg-color: var(--engine-primary-contrast);"
             "\n  --mermaid-font-family: var(--engine-font-family), Helvetica, Arial, sans-serif;\n}")
    SEL = {"title": "section.engine-title", "section": "section.slide.engine-section",
           "closing": "section.slide.level2.closing", "content": "section.slide.level2:not(.engine-section):not(.closing):not(.feature):not(.full)"}
    for kind, sel in SEL.items():   # a static background per slide kind (the engine draws no waves there)
        f = livery.get("art", {}).get(kind)
        if isinstance(f, str):
            L.append(f'.reveal .slides {sel} {{ background: url("{Path(f).name}") center / cover no-repeat; }}')
    marks = livery["marks"]
    light, dark = (Path(marks[r]["logo"]).name for r in ("background", "primary"))
    L.append(".reveal .slides section.slide::after,\n.reveal .slides section.engine-title::after "
             f'{{ background-image: url("{light}"); }}')
    L.append(".reveal .slides section.slide.engine-field::after,\n.reveal .slides section.engine-title.engine-field::after "
             f'{{ background-image: url("{dark}"); }}')
    if "signoff" in livery:
        light, dark = (Path(marks[r]["signoff"]).name for r in ("background", "primary"))
        L.append(f'.reveal .slides section .engine-signoff {{ background-image: url("{light}"); }}')
        L.append(".reveal .slides section.engine-field .engine-signoff,\n.reveal .slides section.engine-title.engine-field .engine-signoff "
                 f'{{ background-image: url("{dark}"); }}')
    art = livery.get("art", {})
    if isinstance(art.get("titlegraphic"), str):   # the title photo when a deck sets none
        L.append(f'.reveal .slides section.engine-title .engine-title-photo-default {{ background: url("{Path(art["titlegraphic"]).name}") center / cover no-repeat; }}')
    if band:   # the band's strip images, on the title and the closing slide; the closing wears the title art
        sel = ".reveal .slides section.engine-title.engine-band", ".reveal .slides section.slide.level2.closing.engine-band"
        m = marks[t["field"]]
        L.append(",\n".join(f"{s}::after" for s in sel) + f' {{ background-image: url("{Path(m["logo"]).name}"); }}')
        if "signoff" in m:
            L.append(",\n".join(f"{s} .engine-signoff" for s in sel) + f' {{ background-image: url("{Path(m["signoff"]).name}"); }}')
        if not isinstance(art.get("closing"), str) and isinstance(art.get("title"), str):
            L.append(f'{sel[1]} {{ background: url("{Path(art["title"]).name}") center / cover no-repeat; }}')
    L += emit_css_compositions(livery)
    L.append(extra.rstrip("\n"))
    return "\n".join(L).rstrip("\n") + "\n"


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
    selector (CSEL), so the scss reads one name set whatever the variant; slide pixels."""
    px = lambda v, axis: f"{round(v * axis, 1):g}px"
    role = lambda r: r if str(r).startswith("#") else f"var(--engine-{r})"
    L = ["/* compositions (livery_build.py compositions()): boxes in slide px, roles as vars */"]
    for comp, sel in CSEL.items():
        c, props = livery["compositions"][comp], []
        for k in BOXED:
            box = c[k]["box"] if c[k] else [0, 0, 0, 0]
            props.append(f"--engine-cmp-{k}-display: {'block' if c[k] else 'none'};")
            props += [f"--engine-cmp-{k}-{a}: {px(v, W if a in 'xw' else H)};" for a, v in zip("xywh", box)]
        props.append(f"--engine-cmp-field: {role(c['field']['role']) if c['field'] else 'transparent'};")
        col = c["column"]
        props.append(f"--engine-cmp-text: {role(col['role'])};")
        props.append(f"--engine-cmp-column-justify: {'center' if col['anchor'] == 'middle' else 'flex-start'};")
        props.append(f"--engine-cmp-column-tab: {'block' if col['tab'] else 'none'};")
        rule = col["rule"] or [0, 0]
        props.append(f"--engine-cmp-rule-display: {'block' if col['rule'] else 'none'};")
        props += [f"--engine-cmp-rule-w: {px(rule[0], W)};", f"--engine-cmp-rule-h: {px(rule[1], H)};"]
        if c["fineprint"]:
            props.append(f"--engine-cmp-fineprint-color: {role(c['fineprint']['role'])};")
        for k in ("band", "bar", "panel"):
            if c[k]:
                fill = role(c[k]["role"])
                op = c[k].get("opacity", 1)
                props.append(f"--engine-cmp-{k}-fill: " + (fill if op == 1 else f"color-mix(in srgb, {fill} {op * 100:g}%, transparent)") + ";")
        if c["eyebrow"]:
            props.append(f"--engine-cmp-eyebrow: {role(c['eyebrow']['color'])};")
        L.append(f"{sel} {{\n  " + "\n  ".join(props) + "\n}")
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
    colors = {**livery["roles"], **livery["derived"]}
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
            build / "livery.css": emit_css(livery, overrides(d, "livery-extra.css", "/* {} */"))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("liveries", nargs="+", type=Path)
    ap.add_argument("--check", action="store_true", help="fail if a committed build/ is stale")
    a = ap.parse_args()
    stale = 0
    for d in a.liveries:
        for target, text in outputs(d).items():
            if a.check:
                if not target.exists() or target.read_text() != text:
                    print(f"stale: {target} (run livery_build.py {d})"); stale = 1
                else:
                    print(f"fresh: {target}")
            else:
                target.parent.mkdir(exist_ok=True)
                target.write_text(text)
                print(f"wrote {target}")
    sys.exit(stale)


if __name__ == "__main__":
    main()
