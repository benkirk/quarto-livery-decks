#!/usr/bin/env python3
"""Check livery_build.py's compositions against the slides the formats drew before them.

    tools/test_compositions.py [<framework liveries dir>]

today() restates, in slide fractions, what engine 3.4.0's revealjs theme drew for each
composition (engine-revealjs.scss and .lua; beamer and pptx disagreed in places, recorded in
EXPECTED_DELTAS). The resolved compositions of ncar and, when present, the framework's cu and nsi
(benkirk/quarto-livery-decks docs/common/liveries, or the argument) must equal today() with every
EXPECTED_DELTAS row applied: one row per decision of docs/design/composition-handoff.md "Which
value wins", so a changed number is either named there or a failure. Then the invariants: every
entry has every key, the band's arithmetic, the light variants' roles, overrides and extends.
"""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "_extensions" / "engine"
spec = importlib.util.spec_from_file_location("livery_build", ENGINE / "livery_build.py")
lb = importlib.util.module_from_spec(spec); spec.loader.exec_module(lb)
W, H = 1600, 900
TOL = 1e-4   # compositions round to 4 places


def today(L: dict) -> dict:
    """The revealjs theme's compositions as of engine 3.4.0, from the livery's knobs."""
    g, m = L["geometry"], L["geometry"]["margin"]
    logo, art, so = g["logo"], L.get("art", {}), L.get("signoff")
    has = lambda k: isinstance(art.get(k), str)
    waves = art.get("waves")
    t = {**lb.BAND, "logo-height": logo.get("title", 0.09), **L.get("title", {})}
    if so:
        t.setdefault("signoff-height", so["height"])
    pad = 1 - 2 * m   # in-flow percentages are of the padded box (scss padding: ... var(--engine-margin))
    box = lambda x, y, w, h: [x, y, w, h]
    none = logo.get("corner") == "none"
    mark = lambda y, h, role: None if none else {"role": role, "box": box(m, y, h * logo["aspect"] * 9 / 16, h)}

    def signoff(role):
        if not so:
            return None
        h = so["height"]; w = h * so["aspect"] * 9 / 16
        return {"role": role, "box": box(m if so["corner"] == "bottom-left" else 1 - m - w, 1 - so["bottom"] - h, w, h)}

    def wave(style, shift, op):
        return waves and {"style": style, "shift": shift, "role": "secondary", "opacity": op, "line": 2.4 / W}

    rule = [208 / W, 3 / H]   # .engine-title-rule 208px x 3px
    empty = dict.fromkeys(lb.COMP_KEYS)
    # title: padding 180px m 60px, mark top 72px, text max-width 58% (44% with a photo), fineprint bottom 36px max-width 50%
    title = {**empty, "field": {"role": "primary", "box": box(0, 0, 1, 1)}, "art": "title" if has("title") else None,
             "waves": wave("bands", waves and waves["shift"]["title"], [0.18, 0.10]),
             "mark": mark(72 / H, logo["title"], "primary"), "signoff": signoff("primary"),
             "column": {"box": box(m, 180 / H, 0.58 * pad, 1 - 240 / H), "anchor": "top", "role": "primary-text",
                        "tab": True, "rule": rule},
             "fineprint": {"box": box(m, 1 - 36 / H - 0.10, 0.50, 0.10), "anchor": "bottom", "role": "primary-text"}}
    photo = lambda c: {**c, "field": {**c["field"], "box": box(0, 0, 0.5, 1)}, "photo": {"box": box(0.48, 0, 0.52, 1)},
                       "waves": wave("cover", 0, [0.65]), "column": {**c["column"], "box": c["column"]["box"][:2] + [0.44 * pad, c["column"]["box"][3]]}}

    def light(c):   # html.engine-title-light: no .engine-field, so the light marks; text in foreground
        w = c["waves"]
        return {**c, "field": {**c["field"], "role": "background"},
                "waves": {**w, "style": "lines", "opacity": []} if w and w["style"] == "bands" else w,
                "mark": c["mark"] and {**c["mark"], "role": "background"},
                "signoff": c["signoff"] and {**c["signoff"], "role": "background"},
                "column": {**c["column"], "role": "foreground"},
                "fineprint": c["fineprint"] and {**c["fineprint"], "role": "foreground"}}

    top, bottom, split, mid = t["top"], t["bottom"], t["split"], (1 + t["bottom"]) / 2
    left = so and so["corner"] == "bottom-left"   # --engine-band-logo-left: the mark opposite the sign-off, else at the margin
    sh = so and t["signoff-height"]; sw = so and sh * so["aspect"] * 9 / 16
    lh = t["logo-height"]; lw = lh * logo["aspect"] * 9 / 16
    smark = None if none else {"role": t["field"], "box": box(1 - m - lw if left else m, mid - lh / 2, lw, lh)}
    ssign = so and {"role": t["field"], "box": box(m if left else 1 - m - sw, mid - sh / 2, sw, sh)}
    band = {**empty, "field": {"role": t["field"], "box": box(0, 0, 1, 1)}, "art": "title" if has("title") else None,
            "photo": {"box": box(split, top, 1 - split, bottom - top)}, "band": {"role": t["band"], "box": box(0, top, 1, bottom - top)},
            "mark": smark, "signoff": ssign,
            "column": {"box": box(m, top, split - m - 64 / W, bottom - top), "anchor": "middle", "role": "primary-text",
                       "tab": True, "rule": rule},
            "fineprint": {"box": box(m, bottom + 16 / H, 0.50, 0.06), "anchor": "top", "role": t["field-text"]}}
    # closing: padding 150px m 80px, flex-centred, h2 max-width 60%, mark top 81px
    ccol = {"box": box(m, 150 / H, 0.60 * pad, 1 - 230 / H), "anchor": "middle", "role": "primary-text", "tab": True, "rule": None}
    closing = {**empty, "field": {"role": "primary", "box": box(0, 0, 1, 1)}, "art": "closing" if has("closing") else None,
               "waves": wave("bands", waves and waves["shift"]["title"], [0.18, 0.10]),
               "mark": mark(81 / H, logo["closing"], "primary"), "signoff": signoff("primary"), "column": ccol}
    cband = {**empty, "field": {"role": t["field"], "box": box(0, 0, 1, 1)},
             "art": "closing" if has("closing") else "title" if has("title") else None,
             "mark": smark, "signoff": ssign, "column": {**ccol, "role": t["field-text"]}}
    # section: padding divider-top m divider-bottom, flex-centred, h1 max-width 62%, mark top 72px
    dv, d = g["divider"], L.get("divider", {})
    section = {**empty, "field": {"role": "primary", "box": box(0, 0, 1, 1)}, "art": "section" if has("section") else None,
               "waves": wave("bands", waves and waves["shift"]["section"], [0.18, 0.10]),
               "mark": mark(72 / H, logo["section"], "primary"), "signoff": signoff("primary"),
               "column": {"box": box(m, dv["top"], 0.62 * pad, 1 - dv["top"] - dv["bottom"]), "anchor": "middle",
                          "role": "primary-text", "tab": d.get("tab", True), "rule": None},
               "eyebrow": {"label": d.get("label", "Section"), "color": d.get("label-color", "secondary")}}
    # feature: the h2 a 180px bar (flex-centred, padding 0 m), the body a 52% panel from 230px to the 70px padding
    feature = {**empty, "photo": {"box": box(0, 0, 1, 1)},
               "bar": {"role": "dark", "opacity": 0.72, "box": box(0, 0, 1, 180 / H)},
               "column": {"box": box(m, 0, pad, 180 / H), "anchor": "middle", "role": "background", "tab": False, "rule": None},
               "panel": {"role": "dark", "opacity": 0.72, "box": box(m, 230 / H, 0.52 * pad, 1 - 300 / H)}}
    res = {"title": title, "title-photo": photo(title), "title-light": light(title), "title-photo-light": light(photo(title)),
           "title-band": band, "closing": closing, "closing-light": light(closing), "closing-band": cband,
           "section": section, "feature": feature}
    return json.loads(json.dumps(res))   # no shared boxes, so a delta edits one entry


# One row per decision ("Which value wins"): what the three formats drew, and the change to today()
# (None when HTML already drew the decided value and only beamer or pptx move).
COVERS = ("title", "title-photo", "title-light", "title-photo-light")
PHOTOS = ("title-photo", "title-photo-light")
NCAR_FAMILY = {"ncar", "ucar", "ucp", "ncarucar", "over", "banded", "covered"}   # ncar and what extends it here


def each(comps, fn):
    """An EXPECTED_DELTAS change: fn(entry, livery) on each named composition."""
    return lambda c, L: [fn(c[k], L) for k in comps]


def setbox(key, i, value):
    """Set coordinate i (x y w h = 0 1 2 3) of key's box where the entry has the key; value may be fn(livery)."""
    def fn(x, L):
        if x[key]:
            x[key]["box"][i] = value(L) if callable(value) else value
    return fn


EXPECTED_DELTAS = {
    # row: (what each format drew and what was decided, the change to today() or None)
    "cover photo box": ({"pdf": "0.52W anchored right", "html": "left 48%, w 52%", "pptx": "full slide",
                         "decided": "[0.48, 0, 0.52, 1]"}, None),
    "straight field edge": ({"pdf": 0.5, "html": 0.5, "pptx": 0.52, "decided": 0.5}, None),
    "wave line width": ({"pdf": "0.8pt = 0.0018W", "html": "2.4px = 0.0015W", "pptx": 0.0015, "decided": 0.0015}, None),
    "mark y": ({"pdf": "0.06 / 0.075 / 0.075", "html": "0.08 / 0.08 / 0.09", "pptx": "0.06 / 0.08 / 0.09",
                "decided": "0.06 / 0.08 / 0.09"}, each(COVERS, setbox("mark", 1, 0.06))),
    "title column top": ({"pdf": 0.205, "html": 0.20, "pptx": 0.375, "decided": "mark bottom + 0.05 (0.20)"}, None),
    "title column anchor": ({"pdf": "top", "html": "top", "pptx": "fixed y", "decided": "top"}, None),
    "title column w, no photo": ({"pdf": 0.62, "html": 0.510, "pptx": 0.50, "decided": 0.50},
                                  each(("title", "title-light"), setbox("column", 2, 0.50))),
    "title column w, photo": ({"pdf": 0.47, "html": 0.387, "pptx": 0.50, "decided": 0.44},
                               each(PHOTOS, setbox("column", 2, 0.44))),
    "title rule": ({"pdf": "0.13W x 1.2pt", "html": "0.13W x 3px", "pptx": "0.065W x 1.5pt", "decided": "[0.13, 0.0033]"}, None),
    "fineprint": ({"pdf": "0.02H above the floor", "html": "bottom 36px, w 50%", "pptx": "none",
                   "decided": "[m, 0.86, w, 0.10] anchor bottom; the column ends at 0.86"},
                  lambda c, L: [each(COVERS, setbox("column", 3, 0.66))(c, L), each(PHOTOS, setbox("fineprint", 2, 0.44))(c, L)]),
    "sign-off under title=light": ({"pdf": "dark", "html": "light", "pptx": "light", "decided": "role background"}, None),
    "section mark under title=light": ({"pdf": "light", "html": "dark", "pptx": "dark", "decided": "role primary"}, None),
    "art.title under a photo": ({"pdf": "none", "html": "painted", "pptx": "hidden", "decided": None},
                                 each(PHOTOS, lambda x, L: x.update(art=None))),
    "art.title under light": ({"pdf": "painted", "html": "painted", "pptx": "none", "decided": None},
                               each(("title-light", "closing-light"), lambda x, L: x.update(art=None))),
    "section column": ({"pdf": "vfill thirds, 0.62W", "html": "centred in divider, 0.546W", "pptx": "centred, 0.62",
                        "decided": "centred in [m, divider.top, 0.62, ...]"}, each(("section",), setbox("column", 2, 0.62))),
    "closing column": ({"pdf": "vfill thirds, 0.62W", "html": "centred in padding, 0.528W", "pptx": "fixed 0.30/0.49, 0.62W",
                        "decided": "[m, mark bottom + 0.03, 0.62, 0.88 - y] middle"},
                       each(("closing", "closing-light", "closing-band"), lambda x, L: x["column"].update(
                           box=[L["geometry"]["margin"], 0.09 + L["geometry"]["logo"]["closing"] + 0.03, 0.62,
                                0.88 - 0.09 - L["geometry"]["logo"]["closing"] - 0.03]))),
    "closing-band column": ({"pdf": "strut + vfill", "html": "as closing", "pptx": "0.30/0.49",
                             "decided": "[m, 0.10, 0.62, bottom - 0.13]"},
                            lambda c, L: c["closing-band"]["column"].update(box=[L["geometry"]["margin"], 0.10, 0.62,
                                {**lb.BAND, **L.get("title", {})}["bottom"] - 0.13])),
    "title=light under a band": ({"pdf": "ignored", "html": "ignored", "pptx": "light cover",
                                  "decided": "ignored, with a warning"}, None),
    "closing under title=light, pptx": ({"pdf": "light", "html": "light", "pptx": "dark Closing",
                                         "decided": "new Closing (light) layout"}, None),
    "feature": ({"pdf": "photo + bar + blocks", "html": "photo + bar + panel", "pptx": "the cover with a mark",
                 "decided": "per livery: feature.style, engine default bar"}, None),
    "band fineprint gap": ({"pdf": "bottom + 0.02", "html": "bottom + 0.018", "pptx": "none", "decided": 0.018},
                           lambda c, L: (setbox("fineprint", 1, lambda L: {**lb.BAND, **L.get("title", {})}["bottom"] + 0.018)(c["title-band"], L),
                                         setbox("fineprint", 2, lambda L: {**lb.BAND, **L.get("title", {})}["split"] - L["geometry"]["margin"] - 0.04)(c["title-band"], L))),
    "band mark without a sign-off": ({"pdf": "right", "html": "left", "pptx": "right", "decided": "right"},
                                     each(("title-band", "closing-band"), lambda x, L: L.get("signoff") or setbox("mark", 0, lambda L:
                                         1 - L["geometry"]["margin"] - x["mark"]["box"][2])(x, L))),
    "title column top, ncar": ({"pdf": 0.205, "html": 0.20, "pptx": 0.375,
                                "decided": "ncar and its flavors: pptx's 0.375 (Ben, 2026-10-17); others under the mark"},
                               lambda c, L: L["name"] in NCAR_FAMILY and each(COVERS, lambda x, L: x["column"].update(
                                   box=[0.06, 0.375, 0.44 if x["photo"] else 0.50, 0.485]))(c, L)),
}


def close(a, b, path=""):
    """[] when a and b agree (numbers within TOL), else the differing paths."""
    if isinstance(a, dict) and isinstance(b, dict):
        return [p for k in sorted(set(a) | set(b)) for p in close(a.get(k), b.get(k), f"{path}.{k}")]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [p for i, (x, y) in enumerate(zip(a, b)) for p in close(x, y, f"{path}[{i}]")]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return [] if abs(a - b) <= TOL else [f"{path}: {a} != {b}"]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def check(name: str, L: dict) -> list[str]:
    errs, c = [], L["compositions"]
    expected = today(L)
    for row, (was, apply) in EXPECTED_DELTAS.items():
        if apply:
            apply(expected, L)
    for comp in lb.COMPOSITIONS:
        errs += [f"{name} {comp}{p}" for p in close(c[comp], expected[comp])]
        if set(c[comp]) != set(lb.COMP_KEYS):
            errs.append(f"{name} {comp}: keys {sorted(c[comp])}")
    t, m = {**lb.BAND, **L.get("title", {})}, L["geometry"]["margin"]
    b = c["title-band"]
    if abs(b["column"]["box"][2] - (t["split"] - m - 0.04)) > TOL:
        errs.append(f"{name} title-band.column.w is not split - margin - 0.04")
    for k in ("mark", "signoff"):
        if b[k] and abs(b[k]["box"][1] + b[k]["box"][3] / 2 - (1 + t["bottom"]) / 2) > TOL:
            errs.append(f"{name} title-band.{k} is not centred on the strip")
    if close(b["photo"]["box"], [t["split"], t["top"], 1 - t["split"], t["bottom"] - t["top"]]):
        errs.append(f"{name} title-band.photo is not the band right of split")
    for comp in ("title-light", "title-photo-light", "closing-light"):
        x = c[comp]
        roles = (x["field"]["role"], x["column"]["role"], x["mark"] and x["mark"]["role"], x["signoff"] and x["signoff"]["role"])
        if roles[:2] != ("background", "foreground") or any(r not in (None, "background") for r in roles[2:]):
            errs.append(f"{name} {comp}: light roles {roles}")
    return errs


def flavor(tmp: Path, name: str, parent: Path, knobs: str) -> dict:
    """A livery extending `parent` (linked beside it) with the given livery.yml body, resolved."""
    if not (tmp / parent.name).exists():
        (tmp / parent.name).symlink_to(parent)
    d = tmp / name; d.mkdir()
    (d / "_brand.yml").write_text("{}\n")
    (d / "livery.yml").write_text(f"name: {name}\nextends: {parent.name}\n{knobs}")
    (d / "template.pptx").write_text("")   # resolve() only warns without one
    return lb.resolve(d)[0]


def main():
    fw = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "quarto-livery-decks" / "docs" / "common" / "liveries"
    liveries = {"ncar": ENGINE / "liveries" / "ncar"}
    for name in ("cu", "nsi"):
        if (fw / name / "livery.yml").exists():
            liveries[name] = fw / name
        else:
            print(f"skip {name}: no {fw / name}")
    errs = []
    for name, d in liveries.items():
        errs += check(name, lb.resolve(d)[0])
    with tempfile.TemporaryDirectory() as tmp:
        tmp, ncar = Path(tmp), ENGINE / "liveries" / "ncar"
        # overrides: title's reaches its variants, title-photo's only that one
        L = flavor(tmp, "over", ncar, "compositions:\n  title: {column: {anchor: middle}}\n  title-photo: {fineprint: null}\n")
        c = L["compositions"]
        if [c[k]["column"]["anchor"] for k in ("title", "title-photo", "title-light", "title-photo-light")] != ["middle"] * 4:
            errs.append("over: an override on title does not reach its variants")
        if c["title-photo"]["fineprint"] is not None or c["title-photo-light"]["fineprint"] is None:
            errs.append("over: an override on title-photo reaches beyond it")
        # extends: a flavor's band from its own knobs over a parent without one
        L = flavor(tmp, "banded", ncar, "title: {style: band, top: 0.30, bottom: 0.70, split: 0.60}\n")
        errs += check("banded", L)
        if close(L["compositions"]["title-band"]["band"]["box"], [0, 0.30, 1, 0.40]):
            errs.append("banded: the flavor's band numbers did not reach title-band")
        # feature.style cover: the title-photo composition with the body's column
        L = flavor(tmp, "covered", ncar, "feature: {style: cover}\n")
        f, tp = L["compositions"]["feature"], L["compositions"]["title-photo"]
        if close({**f, "column": None}, {**tp, "column": None, "fineprint": None}) or close(f["column"]["box"], [0.06, 0.34, 0.44, 0.52]):
            errs.append("covered: feature.style cover is not the title-photo composition with the body column")
    for e in errs:
        print("FAIL", e)
    print(f"compositions: {len(liveries)} liveries and 3 flavors, {'%d failures' % len(errs) if errs else 'all as decided'}")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
