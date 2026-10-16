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
highlight theme, engine.theme with the roles filled in.
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
# theme1.xml slot -> role, the slot contract of design section 4 (livery_template.py writes it)
SLOT_ROLES = {"dk1": "foreground", "lt1": "background", "dk2": "primary", "lt2": "surface",
              "accent1": "secondary", "accent2": "highlight", "accent3": "dark", "accent4": "accent",
              "accent5": "warning", "accent6": "primary-contrast", "hlink": "primary", "folHlink": "highlight"}


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
    pptx = data.get("pptx", {})
    for k in ("template", "fonts"):
        if k in pptx:   # the child's own file when it has one (livery_template.py builds every livery's)
            pptx[k] = pptx[k] if (child / pptx[k]).exists() else rel(pptx[k])
    return data


def read(d: Path) -> dict:
    brand = yaml.safe_load((d / "_brand.yml").read_text()) or {}
    knobs = yaml.safe_load((d / "livery.yml").read_text()) or {}
    merged = {"brand": brand, **{k: v for k, v in knobs.items() if k != "extends"}}
    parent = knobs.get("extends")
    if parent:
        inherited = rebase(read(d.parent / parent), d.parent / parent, d)
        inherited.get("pptx", {}).pop("scheme", None)   # a flavor's scheme follows its own roles
        merged = merge(inherited, merged)
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
    out.setdefault("pptx", {})
    if "scheme" not in out["pptx"]:   # the slot contract, from the roles
        out["pptx"]["scheme"] = {slot: roles[role] for slot, role in SLOT_ROLES.items() if role in roles}
    tmpl = d / out.get("pptx", {}).get("template", "template.pptx")
    if not tmpl.exists():
        sys.exit(f"{d.name}: pptx template {tmpl} missing")
    return out, sources


def tex_name(key: str, names: dict) -> str:
    return names.get(key) or "".join(w.capitalize() for w in key.split("-"))


def logo_path(livery: dict, variant: str, print_: bool) -> str:
    """The light/dark logo's path: the `<name>-print` image for LaTeX when there is one."""
    images, name = livery["logo"]["images"], livery["logo"]["medium"][variant]
    if print_ and name + "-print" in images:
        name += "-print"
    return images[name]["path"]


def base_font(livery: dict) -> tuple[str, list]:
    family = livery["typography"].get("base", "")
    for font in livery["typography"].get("fonts", []):
        if font.get("family") == family:
            return family, font.get("files", [])
    return family, []


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
    L.append("% logos (\\includegraphics finds the extension)")
    for variant in ("light", "dark"):
        p = Path(logo_path(livery, variant, True))
        L.append(f"\\def\\engine@logo@{variant}{{\\engineliverydir {p.with_suffix('').as_posix()}}}")
    family, files = base_font(livery)
    L.append("% fonts: the base family's files, by weight and style")
    L.append(f"\\def\\engine@font@family{{{family}}}")
    if files:
        L.append(f"\\def\\engine@font@dir{{\\engineliverydir {Path(files[0]['path']).parent.as_posix()}/}}")
    faces = {(400, False): "regular", (700, False): "bold", (400, True): "italic", (700, True): "bolditalic", (600, False): "semibold"}
    for f in files:
        face = faces.get((f.get("weight", 400), f.get("style") == "italic"))
        if face:
            L.append(f"\\def\\engine@font@{face}{{{Path(f['path']).stem}}}")
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
    for kind in ("title", "section", "closing", "content"):
        if isinstance(art.get(kind), str):
            L.append(f"\\def\\engine@art@{kind}{{\\engineliverydir {Path(art[kind]).with_suffix('').as_posix()}}}")
    L.append(extra.rstrip("\n"))
    L.append(r"\liveryrestoreat")
    return "\n".join(L) + "\n"


def emit_css(livery: dict) -> str:
    L = ["/* build/livery.css: GENERATED by livery_build.py from _brand.yml and livery.yml; do not edit.",
         f" * livery {livery['name']}. Attached by engine-revealjs.lua with the font and logo files",
         " * beside it, so the url()s are bare file names. */"]
    family, files = base_font(livery)
    for f in files:
        L.append(f'@font-face {{ font-family: "{family}"; font-style: {f.get("style", "normal")}; '
                 f'font-weight: {f.get("weight", 400)}; font-display: block; '
                 f'src: url("{Path(f["path"]).name}") format("truetype"); }}')
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
    props.append("--engine-overlay: color-mix(in srgb, var(--engine-dark) 72%, transparent);")
    L.append(":root {\n  " + "\n  ".join(props) + "\n}")
    # Quarto sets --mermaid-* on :root from its Sass; html:root outranks it, so mermaid wears the roles
    L.append("html:root {\n  --mermaid-bg-color: var(--engine-background);\n  --mermaid-node-bg-color: var(--engine-surface);"
             "\n  --mermaid-node-fg-color: var(--engine-foreground);\n  --mermaid-fg-color: var(--engine-foreground);"
             "\n  --mermaid-edge-color: var(--engine-foreground);\n  --mermaid-label-bg-color: var(--engine-background);"
             "\n  --mermaid-label-fg-color: var(--engine-primary-contrast);\n}")
    SEL = {"title": "section.engine-title", "section": "section.slide.engine-section",
           "closing": "section.slide.level2.closing", "content": "section.slide.level2:not(.engine-section):not(.closing):not(.feature):not(.full)"}
    for kind, sel in SEL.items():   # a static background per slide kind (the engine draws no waves there)
        f = livery.get("art", {}).get(kind)
        if isinstance(f, str):
            L.append(f'.reveal .slides {sel} {{ background: url("{Path(f).name}") center / cover no-repeat; }}')
    light, dark = (Path(logo_path(livery, v, False)).name for v in ("light", "dark"))
    L.append(".reveal .slides section.slide::after,\n.reveal .slides section.engine-title::after "
             f'{{ background-image: url("{light}"); }}')
    L.append(".reveal .slides section.slide.engine-field::after,\n.reveal .slides section.engine-title.engine-field::after "
             f'{{ background-image: url("{dark}"); }}')
    return "\n".join(L) + "\n"


def ancestors(d: Path) -> list[Path]:
    """The livery and its `extends` chain, parents first."""
    knobs = yaml.safe_load((d / "livery.yml").read_text()) or {}
    parent = knobs.get("extends")
    return (ancestors(d.parent / parent) if parent else []) + [d]


def overrides(d: Path, name: str) -> str:
    """The livery's and its ancestors' overrides/<name>, concatenated, parents first."""
    out = ""
    for a in ancestors(d):
        f = a / "overrides" / name
        if f.exists():
            out += f"% overrides from {os.path.relpath(f, d)}\n" + f.read_text()
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
            build / "livery.css": emit_css(livery)}


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
