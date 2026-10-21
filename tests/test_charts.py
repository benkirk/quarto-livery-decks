"""Check livery_charts.py, the chart colors (design/charts-and-plots.md).

    python3 -m pytest tests/test_charts.py

The color math against fixed points; every bundled livery: `charts` has both modes, no check
fails, a generated palette passes every check, the build is deterministic, the published
palettes come out as given (ncar's and ucar's sam-queries pins, nasa's HDS colors); then the
rules on made-up liveries: one brand hue grows to eight that pass, an avoided hue range stays
empty, a light pin is lifted for the dark surface, a ninth series never makes a family, an
unknown color is refused (unknown keys are the schema's: test_schema.py), an extra map joins the
generated ones without touching the slots; each livery's build/livery.mplstyle parses in
matplotlib (the cycle is the categorical slots, the sizes the type scale), and the Custom Colors
names are plain.
"""

import json
import warnings
from pathlib import Path

import pytest

import livery_build as lb

C = lb.livery_charts

# the published palettes, as their sources give them
SAM_LIGHT = ["#0057C2", "#E0681A", "#00A2B4", "#D4246B", "#9A7B00", "#6B46C1"]   # sam-queries FAIR_SHARE_LIGHT
SAM_DARK = ["#4687EA", "#D9772C", "#11A0B0", "#DE4B80", "#AD8D1C", "#8F70E8"]    # FAIR_SHARE_DARK
BURN_LIGHT = ["#1F63B0", "#86B6E6", "#DDE1E5", "#F0A07C", "#C0272D"]           # --data-burn-0..4
HDS_LIGHT_HEAD = ["#1159CD", "#EF483F", "#E8892E"]                              # dataviz.color.cat.light.1-3


def test_math_points():
    assert abs(C.contrast("#000000", "#FFFFFF") - 21) < 1e-9, "contrast black/white is not 21:1"
    assert C.contrast("#777777", "#777777") == 1, "contrast of a color with itself is not 1"
    for h in ("#0057C2", "#CFB87C", "#000000", "#FFFFFF", "#E4002B"):
        assert C.from_oklch(*C.oklch(h)) == h, f"OKLCH round trip of {h}"
    L, Cc, _ = C.oklch("#FFFFFF")
    assert abs(L - 1) < 1e-6 and Cc < 1e-6, "white is not L 1, C 0 in OKLab"
    assert abs(C.delta_e("#0057C2", "#E0681A") - C.delta_e("#E0681A", "#0057C2")) < 1e-12, "dE is not symmetric"
    out = C.from_oklch(0.7, 0.4, 145)   # far outside sRGB: chroma is reduced, hue and lightness held
    L2, C2, h2 = C.oklch(out)
    assert abs(L2 - 0.7) < 0.01 and C.hue_gap(h2, 145) < 2 and C2 < 0.4, f"gamut clip of an impossible green: {out}"
    assert C._lift("#0057C2", "#FFFFFF") == "#0057C2", "lift changes a color that already clears 3:1"
    lifted = C._lift("#00357A", "#011837")
    assert C.contrast(lifted, "#011837") >= 3, f"lift of navy on space is {C.contrast(lifted, '#011837'):.2f}:1"


def test_livery_charts(livery: Path):
    d = livery
    L, _ = lb.resolve(d)
    ch = L.get("charts")
    assert ch is not None, f"{d.name}: no charts"
    for m in ("light", "dark"):
        b = ch[m]
        for key in ("surface", "categorical", "families", "sequential", "default-map", "diverging",
                    "status", "muted", "area-alpha", "published"):
            assert key in b, f"{d.name}: charts.{m}.{key} missing"
        assert len(b["families"]) <= C.SLOTS, f"{d.name}: {m} has {len(b['families'])} families"
        assert len(b["diverging"]) % 2 == 1, f"{d.name}: {m} diverging has no midpoint"
        if not b["published"]["categorical"]:
            ev = C.evaluate(ch)[m]["categorical"]
            bad = {k: v for k, v in ev.items() if v[0] != "pass"}
            assert not bad, f"{d.name}: generated {m} palette does not pass: {bad}"
    st = C.states(ch)
    assert "fail" not in st, f"{d.name}: a chart check fails"
    L2, _ = lb.resolve(d)
    assert json.dumps(L2["charts"], sort_keys=True) == json.dumps(ch, sort_keys=True), f"{d.name}: charts not deterministic"
    built = json.loads((d / "build" / "livery.json").read_text()).get("charts")
    assert built == json.loads(json.dumps(ch)), f"{d.name}: build/livery.json charts is stale"
    if d.name in ("ncar", "ncarucar"):
        assert ch["light"]["categorical"] == SAM_LIGHT and ch["dark"]["categorical"] == SAM_DARK, f"{d.name}: sam-queries pins changed"
        assert ch["light"]["diverging"] == BURN_LIGHT, f"{d.name}: burn scale changed"
    if d.name in ("ucar", "ucp"):
        swap = lambda p: [p[2], p[1], p[0]] + p[3:]
        assert ch["light"]["categorical"] == swap(SAM_LIGHT) and ch["dark"]["categorical"] == swap(SAM_DARK), \
            f"{d.name}: UCAR Aqua does not lead the sam-queries set"
    if d.name in ("nasa", "nasa-dark", "nasa-jsc-eg"):   # nasa-jsc-eg inherits HDS
        assert ch["light"]["categorical"][:3] == HDS_LIGHT_HEAD and len(ch["light"]["categorical"]) == 12, \
            f"{d.name}: not HDS's 12 categorical colors"
        assert len(ch["light"]["sequential"]) == 11 and all(len(r) == 10 for r in ch["light"]["sequential"].values()), \
            f"{d.name}: not HDS's 11 ramps of 10"
        assert set(ch["light"]["sets"]) == {"2", "3", "4", "5"}, f"{d.name}: HDS sets missing"


def fake(palette: dict, roles: dict, mode="light") -> dict:
    roles = {"background": "#FFFFFF", "foreground": "#111111", "dark": "#0B1B33", "muted": "#666A70", **roles}
    return {"name": "x", "palette": palette, "roles": roles, "mode": mode,
            "type": {"canvas": {"w": 960, "h": 540}}, "geometry": {"margin": 0.06, "body-bottom": 0.9222},
            "frametitle": {"body": 0.1667}, "boxes": {"columns": {"gap": 0.03}}}


ONE = fake({"teal": "#00818F"}, {"primary": "#00818F"})
PINNED = fake({"blue": "#0057C2"}, {"primary": "#0057C2", "dark": "#000814"})


def test_one_hue_grows_to_slots():
    ch = C.charts(ONE, {})
    for m in ("light", "dark"):
        cat = ch[m]["categorical"]
        assert len(cat) == C.SLOTS, f"one hue grows to {len(cat)} slots in {m}"
        assert C.hue_gap(C.oklch(cat[0])[2], C.oklch("#00818F")[2]) < 3, f"slot 1 is not the brand hue in {m}: {cat[0]}"
        ev = C.evaluate(ch)[m]["categorical"]
        assert all(v[0] == "pass" for v in ev.values()), f"one-hue generated {m} palette fails: {ev}"
        hues = [C.oklch(c)[2] for c in cat]
        assert all(C.hue_gap(a, b) >= C.FAMILY for i, a in enumerate(hues) for b in hues[i + 1:]), \
            f"two generated hues of one family in {m}"


def test_avoided_hue_stays_empty():
    ch = C.charts(ONE, {"avoid": [{"hue": 330, "width": 60}]})
    gen = [c for c in ch["light"]["categorical"] if c in ch["light"].get("generated", [])]
    assert all(C.hue_gap(C.oklch(c)[2], 330) > 30 for c in gen), f"an avoided hue was generated: {gen}"


def test_light_pin_lifted_for_dark():
    ch = C.charts(PINNED, {"categorical": ["#00357A", "#0057C2", "#E0681A"]})
    assert ch["light"]["categorical"][0] == "#00357A", "a light pin is not kept as given"
    assert all(C.contrast(c, "#000814") >= 3 for c in ch["dark"]["categorical"]), "a light pin is not lifted for the dark surface"
    assert ch["light"]["published"]["categorical"] and ch["dark"]["published"]["categorical"], "pins not marked published"


def test_ninth_series_makes_no_family():
    many = ["#1159CD", "#EF483F", "#E8892E", "#386470", "#B0A26A", "#3F83EF", "#8F0800", "#79A3AD", "#3E1C99", "#E09D00"]
    ch = C.charts(PINNED, {"categorical": many})
    assert len(ch["light"]["families"]) == C.SLOTS, "a ninth series made a family"
    assert "fail" not in C.states(ch), "a published palette's failure is not downgraded"


@pytest.mark.parametrize("bad", [{"anchors": ["no-such-color"]}, {"default-map": "no-such-color"}],
                         ids=["anchors", "default-map"])
def test_unknown_color_refused(bad):   # unknown keys: test_schema.py
    with pytest.raises(ValueError):
        C.charts(PINNED, bad)


def test_extra_map_joins_generated():
    # an extra color map beside the generated ones, nameable as the default, leaving the
    # categorical selection as it was; reversed on dark like every map
    warm = ["#F3F0E9", "#D2B39F", "#AE7858", "#9C3F29", "#76312B", "#412429"]
    plain, mapped = C.charts(ONE, {}), C.charts(ONE, {"maps": {"warm": warm}, "default-map": "warm"})
    assert mapped["light"]["sequential"]["warm"] == warm and mapped["dark"]["sequential"]["warm"] == warm[::-1], \
        "a map is not kept light to dark (reversed on dark)"
    assert mapped["light"]["default-map"] == "warm" and mapped["dark"]["default-map"] == "warm", \
        "default-map: <map name> is not the default"
    assert mapped["light"]["categorical"] == plain["light"]["categorical"], "a map changed the categorical slots"
    assert set(mapped["light"]["sequential"]) == set(plain["light"]["sequential"]) | {"warm"}, "a map replaced the generated ramps"


def test_figsize():
    fs = C.figsize(fake({}, {}))
    assert fs["full"] == [11.73, 5.67] and fs["half"][0] < fs["full"][0] / 2, f"figsize {fs}"


def test_mplstyle(livery: Path):
    """build/livery.mplstyle as matplotlib reads it: no unknown key, the cycle, chrome and sizes."""
    import matplotlib
    d = livery
    L = json.loads((d / "build" / "livery.json").read_text())
    f = d / "build" / "livery.mplstyle"
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        rc = matplotlib.rc_params_from_file(f, use_default_template=False, fail_on_error=True)
    assert not w, f"{d.name}: livery.mplstyle warns: {[str(x.message) for x in w]}"
    ch = L["charts"]
    cycle = [c.upper() for c in rc["axes.prop_cycle"].by_key()["color"]]
    assert cycle == ch[ch["mode"]]["categorical"], f"{d.name}: mplstyle cycle {cycle}"
    assert rc["axes.labelsize"] == L["type"]["roles"]["body"]["pt"], f"{d.name}: mplstyle label size"
    assert rc["text.color"].upper() == ch["chrome"][ch["mode"]]["text"], f"{d.name}: mplstyle text color"
    assert rc["savefig.transparent"] is True and rc["svg.fonttype"] == "path", f"{d.name}: mplstyle not transparent or svg text"
    family = L["typography"].get("base")
    assert rc["font.sans-serif"][:2] == [family, "DejaVu Sans"], f"{d.name}: mplstyle family {rc['font.sans-serif']}"
    names = [n for n, _ in C.custom_colors(ch)]
    assert len(names) <= C.SLOTS and all(n.startswith(f"Data {i} · ") for i, n in enumerate(names, 1)), \
        f"{d.name}: custom colors {names}"
