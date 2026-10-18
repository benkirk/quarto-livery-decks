#!/usr/bin/env python3
"""Check livery_charts.py, the chart colors (design/charts-and-plots.md).

    tests/test_charts.py [<liveries dir>]

The color math against fixed points; every livery (liveries/, or the argument): `charts` has both
modes, no check fails, a generated palette passes every check, the build is deterministic, the
published palettes come out as given (ncar's and ucar's sam-queries pins, nasa's HDS colors); then
the rules on made-up liveries: one brand hue grows to eight that pass, an avoided hue range stays
empty, a light pin is lifted for the dark surface, a ninth series never makes a family, unknown
keys are refused; each livery's build/livery.mplstyle parses in matplotlib (the cycle is the
categorical slots, the sizes the type scale), and the Custom Colors names are plain.
"""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "_extensions" / "engine"
spec = importlib.util.spec_from_file_location("livery_build", ENGINE / "livery_build.py")
lb = importlib.util.module_from_spec(spec); spec.loader.exec_module(lb)
C = lb.livery_charts
fails = []

# the published palettes, as their sources give them
SAM_LIGHT = ["#0057C2", "#E0681A", "#00A2B4", "#D4246B", "#9A7B00", "#6B46C1"]   # sam-queries FAIR_SHARE_LIGHT
SAM_DARK = ["#4687EA", "#D9772C", "#11A0B0", "#DE4B80", "#AD8D1C", "#8F70E8"]    # FAIR_SHARE_DARK
BURN_LIGHT = ["#1F63B0", "#86B6E6", "#DDE1E5", "#F0A07C", "#C0272D"]           # --data-burn-0..4
HDS_LIGHT_HEAD = ["#1159CD", "#EF483F", "#E8892E"]                              # dataviz.color.cat.light.1-3


def check(cond, msg):
    if not cond:
        fails.append(msg)


def math_points():
    check(abs(C.contrast("#000000", "#FFFFFF") - 21) < 1e-9, "contrast black/white is not 21:1")
    check(C.contrast("#777777", "#777777") == 1, "contrast of a color with itself is not 1")
    for h in ("#0057C2", "#CFB87C", "#000000", "#FFFFFF", "#E4002B"):
        check(C.from_oklch(*C.oklch(h)) == h, f"OKLCH round trip of {h}")
    L, Cc, _ = C.oklch("#FFFFFF")
    check(abs(L - 1) < 1e-6 and Cc < 1e-6, "white is not L 1, C 0 in OKLab")
    check(abs(C.delta_e("#0057C2", "#E0681A") - C.delta_e("#E0681A", "#0057C2")) < 1e-12, "dE is not symmetric")
    out = C.from_oklch(0.7, 0.4, 145)   # far outside sRGB: chroma is reduced, hue and lightness held
    L2, C2, h2 = C.oklch(out)
    check(abs(L2 - 0.7) < 0.01 and C.hue_gap(h2, 145) < 2 and C2 < 0.4, f"gamut clip of an impossible green: {out}")
    check(C._lift("#0057C2", "#FFFFFF") == "#0057C2", "lift changes a color that already clears 3:1")
    lifted = C._lift("#00357A", "#011837")
    check(C.contrast(lifted, "#011837") >= 3, f"lift of navy on space is {C.contrast(lifted, '#011837'):.2f}:1")


def check_livery(d: Path):
    L, _ = lb.resolve(d)
    ch = L.get("charts")
    check(ch is not None, f"{d.name}: no charts")
    if ch is None:
        return
    for m in ("light", "dark"):
        b = ch[m]
        for key in ("surface", "categorical", "families", "sequential", "sequential-default", "diverging",
                    "status", "muted", "area-alpha", "published"):
            check(key in b, f"{d.name}: charts.{m}.{key} missing")
        check(len(b["families"]) <= C.SLOTS, f"{d.name}: {m} has {len(b['families'])} families")
        check(len(b["diverging"]) % 2 == 1, f"{d.name}: {m} diverging has no midpoint")
        if not b["published"]["categorical"]:
            ev = C.evaluate(ch)[m]["categorical"]
            bad = {k: v for k, v in ev.items() if v[0] != "pass"}
            check(not bad, f"{d.name}: generated {m} palette does not pass: {bad}")
    st = C.states(ch)
    check("fail" not in st, f"{d.name}: a chart check fails")
    L2, _ = lb.resolve(d)
    check(json.dumps(L2["charts"], sort_keys=True) == json.dumps(ch, sort_keys=True), f"{d.name}: charts not deterministic")
    built = json.loads((d / "build" / "livery.json").read_text()).get("charts")
    check(built == json.loads(json.dumps(ch)), f"{d.name}: build/livery.json charts is stale")
    if d.name in ("ncar", "ncarucar"):
        check(ch["light"]["categorical"] == SAM_LIGHT and ch["dark"]["categorical"] == SAM_DARK, f"{d.name}: sam-queries pins changed")
        check(ch["light"]["diverging"] == BURN_LIGHT, f"{d.name}: burn scale changed")
    if d.name in ("ucar", "ucp"):
        swap = lambda p: [p[2], p[1], p[0]] + p[3:]
        check(ch["light"]["categorical"] == swap(SAM_LIGHT) and ch["dark"]["categorical"] == swap(SAM_DARK),
              f"{d.name}: UCAR Aqua does not lead the sam-queries set")
    if d.name in ("nasa", "nasa-dark"):
        check(ch["light"]["categorical"][:3] == HDS_LIGHT_HEAD and len(ch["light"]["categorical"]) == 12,
              f"{d.name}: not HDS's 12 categorical colors")
        check(len(ch["light"]["sequential"]) == 11 and all(len(r) == 10 for r in ch["light"]["sequential"].values()),
              f"{d.name}: not HDS's 11 ramps of 10")
        check(set(ch["light"]["sets"]) == {"2", "3", "4", "5"}, f"{d.name}: HDS sets missing")


def fake(palette: dict, roles: dict, mode="light") -> dict:
    roles = {"background": "#FFFFFF", "foreground": "#111111", "dark": "#0B1B33", "muted": "#666A70", **roles}
    return {"name": "x", "palette": palette, "roles": roles, "mode": mode,
            "type": {"canvas": {"w": 960, "h": 540}}, "geometry": {"margin": 0.06}, "frametitle": {"body": 0.1667}}


def rules():
    one = fake({"teal": "#00818F"}, {"primary": "#00818F"})
    ch = C.charts(one, {})
    for m in ("light", "dark"):
        cat = ch[m]["categorical"]
        check(len(cat) == C.SLOTS, f"one hue grows to {len(cat)} slots in {m}")
        check(C.hue_gap(C.oklch(cat[0])[2], C.oklch("#00818F")[2]) < 3, f"slot 1 is not the brand hue in {m}: {cat[0]}")
        ev = C.evaluate(ch)[m]["categorical"]
        check(all(v[0] == "pass" for v in ev.values()), f"one-hue generated {m} palette fails: {ev}")
        hues = [C.oklch(c)[2] for c in cat]
        check(all(C.hue_gap(a, b) >= C.FAMILY for i, a in enumerate(hues) for b in hues[i + 1:]),
              f"two generated hues of one family in {m}")
    ch = C.charts(one, {"avoid": [{"hue": 330, "width": 60}]})
    gen = [c for c in ch["light"]["categorical"] if c in ch["light"].get("generated", [])]
    check(all(C.hue_gap(C.oklch(c)[2], 330) > 30 for c in gen), f"an avoided hue was generated: {gen}")
    pinned = fake({"blue": "#0057C2"}, {"primary": "#0057C2", "dark": "#000814"})
    ch = C.charts(pinned, {"categorical": ["#00357A", "#0057C2", "#E0681A"]})
    check(ch["light"]["categorical"][0] == "#00357A", "a light pin is not kept as given")
    check(all(C.contrast(c, "#000814") >= 3 for c in ch["dark"]["categorical"]), "a light pin is not lifted for the dark surface")
    check(ch["light"]["published"]["categorical"] and ch["dark"]["published"]["categorical"], "pins not marked published")
    many = ["#1159CD", "#EF483F", "#E8892E", "#386470", "#B0A26A", "#3F83EF", "#8F0800", "#79A3AD", "#3E1C99", "#E09D00"]
    ch = C.charts(pinned, {"categorical": many})
    check(len(ch["light"]["families"]) == C.SLOTS, "a ninth series made a family")
    check("fail" not in C.states(ch), "a published palette's failure is not downgraded")
    for bad in ({"colours": []}, {"dark": {"cycle": []}}, {"anchors": ["no-such-color"]}):
        try:
            C.charts(pinned, bad)
            check(False, f"charts {bad} is accepted")
        except ValueError:
            pass
    fs = C.figsize(fake({}, {}))
    check(fs["full"] == [11.73, 5.67] and fs["half"][0] < fs["full"][0] / 2, f"figsize {fs}")


def style(d: Path, L: dict):
    """build/livery.mplstyle as matplotlib reads it: no unknown key, the cycle, chrome and sizes."""
    import matplotlib
    import warnings
    f = d / "build" / "livery.mplstyle"
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        rc = matplotlib.rc_params_from_file(f, use_default_template=False, fail_on_error=True)
    check(not w, f"{d.name}: livery.mplstyle warns: {[str(x.message) for x in w]}")
    ch = L["charts"]
    cycle = [c.upper() for c in rc["axes.prop_cycle"].by_key()["color"]]
    check(cycle == ch[ch["mode"]]["categorical"], f"{d.name}: mplstyle cycle {cycle}")
    check(rc["axes.labelsize"] == L["type"]["roles"]["body"]["pt"], f"{d.name}: mplstyle label size")
    check(rc["text.color"].upper() == ch["chrome"][ch["mode"]]["text"], f"{d.name}: mplstyle text color")
    check(rc["savefig.transparent"] is True and rc["svg.fonttype"] == "path", f"{d.name}: mplstyle not transparent or svg text")
    family = L["typography"].get("base")
    check(rc["font.sans-serif"][:2] == [family, "DejaVu Sans"], f"{d.name}: mplstyle family {rc['font.sans-serif']}")
    names = [n for n, _ in C.custom_colors(ch)]
    check(len(names) <= C.SLOTS and all(n.startswith(f"Data {i} \u00b7 ") for i, n in enumerate(names, 1)),
          f"{d.name}: custom colors {names}")


def main():
    lv = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "liveries"
    dirs = sorted(p for p in lv.iterdir() if (p / "livery.yml").exists())
    math_points()
    for d in dirs:
        check_livery(d)
        style(d, json.loads((d / "build" / "livery.json").read_text()))
    rules()
    for f in fails:
        print("FAIL", f)
    print(f"charts: {len(dirs)} liveries, {'all checks hold' if not fails else f'{len(fails)} failures'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
