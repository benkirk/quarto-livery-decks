#!/usr/bin/env python3
"""Resolve a livery (_brand.yml + livery.yml, `extends` applied) into build/livery.json.

    livery_build.py <livery dir>...          write build/livery.json (committed)
    livery_build.py --check <livery dir>...  exit 1 if a committed build/livery.json is stale

Color names in livery.yml roles resolve against the brand palette; a value starting
with '#' passes through. `extends: <name>` names a sibling livery directory whose
resolved values the child's override key by key (dicts merge, everything else replaces).
`derived` holds the theme's blends of two roles (BLENDS), computed here unless livery.yml
sets the key itself.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

from livery import mix

HEX = "#0123456789abcdefABCDEF"
# (key, role a, role b, share of a): the theme's recipes, engine-revealjs.scss `table` and
# `.ncar-caution`, beamerinnerthemeNCAR.sty `ncarcautionfill`
BLENDS = [
    ("table-rule", "foreground", "surface", 0.20),
    ("table-band", "surface", "background", 0.60),
    ("caution-fill", "warning", "background", 0.18),
]


def merge(base, over):
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            out[k] = merge(base.get(k), v) if k in base else v
        return out
    return over


def read(d: Path) -> dict:
    brand = yaml.safe_load((d / "_brand.yml").read_text()) or {}
    knobs = yaml.safe_load((d / "livery.yml").read_text()) or {}
    merged = {"brand": brand, **{k: v for k, v in knobs.items() if k != "extends"}}
    parent = knobs.get("extends")
    if parent:
        merged = merge(read(d.parent / parent), merged)
    return merged


def resolve(d: Path) -> dict:
    data = read(d)
    palette = {k: v for k, v in data["brand"].get("color", {}).get("palette", {}).items()}

    def hex_of(name):
        if isinstance(name, str) and name.startswith("#"):
            return name.upper()
        if name in palette:
            return str(palette[name]).upper()
        sys.exit(f"{d.name}: color {name!r} is neither a palette name nor a hex value")

    color = data["brand"].get("color", {})
    roles = {k: hex_of(color[k]) for k in ("primary", "secondary", "foreground", "background") if k in color}
    roles.update({k: hex_of(v) for k, v in data.get("roles", {}).items()})
    derived = {k: mix(roles[a], roles[b], share) for k, a, b, share in BLENDS if a in roles and b in roles}
    derived.update({k: hex_of(v) for k, v in data.get("derived", {}).items()})
    out = {
        "name": data.get("name", d.name),
        "palette": {k: str(v).upper() for k, v in palette.items()},
        "roles": roles,
        "derived": derived,
        "typography": data["brand"].get("typography", {}),
        "logo": data["brand"].get("logo", {}),
    }
    for key in ("aspect", "geometry", "divider", "art", "pptx", "overrides"):
        if key in data:
            out[key] = data[key]
    tmpl = d / out.get("pptx", {}).get("template", "template.pptx")
    if not tmpl.exists():
        sys.exit(f"{d.name}: pptx template {tmpl} missing")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("liveries", nargs="+", type=Path)
    ap.add_argument("--check", action="store_true", help="fail if a committed livery.json is stale")
    a = ap.parse_args()
    stale = 0
    for d in a.liveries:
        text = json.dumps(resolve(d), indent=2, sort_keys=True) + "\n"
        target = d / "build" / "livery.json"
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
