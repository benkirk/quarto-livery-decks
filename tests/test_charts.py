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
from conftest import ENGINE, ROOT

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
            "type": {"canvas": {"w": 960, "h": 540}},   # geometry.body and half as livery build derives them
            "geometry": {"margin": 0.06, "body-bottom": 0.9222, "body": [0.06, 0.1667, 0.88, 0.7555], "half": 0.425},
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
    # the family list itself names the fallback: matplotlib builds its per-glyph chain from
    # font.family alone, so a generic `sans-serif` there resolves to the base face and a glyph it
    # lacks (′, →) draws as a box (#133)
    assert rc["font.family"] == ([family, "DejaVu Sans"] if family else ["DejaVu Sans"]), f"{d.name}: mplstyle family {rc['font.family']}"
    assert rc["font.sans-serif"][:2] == [family, "DejaVu Sans"], f"{d.name}: mplstyle sans-serif {rc['font.sans-serif']}"
    names = [n for n, _ in C.custom_colors(ch)]
    assert len(names) <= C.SLOTS and all(n.startswith(f"Data {i} · ") for i, n in enumerate(names, 1)), \
        f"{d.name}: custom colors {names}"


GLYPHS = r"""
import logging, sys
import matplotlib
matplotlib.use("Agg")
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
import livery_mpl
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(2, 1))
ax.text(0.1, 0.5, "5′ → 2″ ≤ 3")   # the prime, the arrow: not in Poppins; DejaVu Sans has them
fig.savefig(sys.argv[1])
"""


def test_missing_glyphs_fall_back(tmp_path):
    """A character the base face lacks is drawn from DejaVu Sans, not as a box: matplotlib logs
    "Glyph … missing from font(s)" when it cannot, and the plot under the ncar style logs nothing.
    A subprocess with its own MPLCONFIGDIR (the font cache), the style and the livery as Make.common
    passes them."""
    import os
    import subprocess
    import sys
    d = ROOT / "liveries" / "ncar"
    env = {**os.environ, "MPLCONFIGDIR": str(tmp_path / "mpl"), "LIVERY_DIR": str(d),
           "MATPLOTLIBRC": str(d / "build" / "livery.mplstyle"), "PYTHONPATH": str(ENGINE / "mpl")}
    r = subprocess.run([sys.executable, "-c", GLYPHS, str(tmp_path / "g.png")], env=env, capture_output=True, text=True, check=True)
    assert "missing from font" not in r.stderr, r.stderr
    assert (tmp_path / "g.png").stat().st_size > 0


def _gp_mode(text: str, mode: str) -> str:
    """A livery.gp's datablock of one mode's commands."""
    return text.split(f"$livery_{mode} << EOD\n", 1)[1].split("\nEOD\n", 1)[0]


def test_gp(livery: Path):
    """build/livery.gp: each mode's datablock holds its categorical slots as linetypes, its chrome
    and status colors; the sizes are the type roles (as the mplstyle's); the livery's mode is
    applied last. With gnuplot here the file loads whole, each mode's block to its last line
    (gnuplot's @ expansion cut a long macro off silently, which this would catch)."""
    import shutil
    import subprocess
    d = livery
    L = json.loads((d / "build" / "livery.json").read_text())
    ch, ty = L["charts"], L["type"]
    text = (d / "build" / "livery.gp").read_text()
    for m in ("light", "dark"):
        block = _gp_mode(text, m)
        lts = [ln.split("'")[1] for ln in block.splitlines() if ln.startswith("set linetype ") and "lc rgb" in ln]
        assert lts == ch[m]["categorical"], f"{d.name}: livery.gp {m} linetypes {lts}"
        c = ch["chrome"][m]
        assert f"set border 3 back lc rgb '{c['spine']}'" in block and f"livery_text = '{c['text']}'" in block, f"{d.name}: {m} chrome"
        assert f"lc rgb '{c['grid']}'" in block and f"livery_good = '{ch[m]['status']['good']}'" in block, f"{d.name}: {m} grid, status"
    family = L["typography"].get("base")
    assert f'livery_font = "{family},{ty["roles"]["caption"]["pt"]:g}"' in text, f"{d.name}: livery.gp font"
    assert f'set xlabel font ",{ty["roles"]["body"]["pt"]:g}"' in text and f'set tics font ",{ty["levels"][2]:g}"' in text, f"{d.name}: livery.gp sizes"
    assert text.rstrip().endswith(f"@livery_{ch['mode']}"), f"{d.name}: livery.gp does not apply its mode"
    if shutil.which("gnuplot"):
        out = {}
        for m in ("light", "dark"):
            # one -e a line: a line's macros expand before any of it runs; a cairo terminal first, as
            # the README says, and once with none (a display-less gnuplot's `unknown`)
            for term in (["-e", "set terminal pdfcairo fontscale 0.75 linewidth 1", "-e", "set output '/dev/null'"], []):
                r = subprocess.run(["gnuplot", "-d", *term, "-e", f"load '{d / 'build' / 'livery.gp'}'", "-e", f"@livery_{m}",
                                    "-e", "@livery_div", "-e", "print livery_mode, ' ', livery_text"], capture_output=True, text=True)
                assert r.returncode == 0, f"{d.name}: livery.gp under gnuplot {term}: {r.stderr}"
            out[m] = r.stderr.split()
        for m in ("light", "dark"):
            assert out[m] == [m, ch["chrome"][m]["text"]], f"{d.name}: gnuplot read {out[m]} for {m}"


GP = r"""
import json, sys
import livery_gp
p = livery_gp.plot('''
set xlabel 'Nodes'; set ylabel 'Time (s)'
plot '-' using 1:2 with linespoints title 'Run A', '-' using 1:2 with linespoints title 'Run B'
1 10
2 6
4 3
e
1 12
2 7
4 5
e
''', kind="half", dark=sys.argv[2] == "dark")
p.save(sys.argv[1] + ".pdf")
if p.svg is not None:
    p.save(sys.argv[1] + ".svg")
print(json.dumps(list(p._repr_mimebundle_())))
"""


@pytest.mark.skipif(not __import__("shutil").which("gnuplot"), reason="no gnuplot (the image's gnuplot-nox; brew install gnuplot)")
def test_gp_render(tmp_path):
    """livery_gp.plot() under ncar, as Make.common runs a deck: the SVG (pptx and HTML) has the text
    as paths, the figure's size in pt, the first data line in the first categorical color at
    2 pt (the dark mode's with dark=True); the PDF (beamer) is what Jupyter is handed there and
    embeds the livery's family."""
    import os
    import re
    import subprocess
    import sys
    d = ROOT / "liveries" / "ncar"
    L = json.loads((d / "build" / "livery.json").read_text())
    w, h = L["charts"]["figsize"]["half"]
    for fmt, mode in (("html", "light"), ("html", "dark"), ("pdf", "light")):
        env = {**os.environ, "LIVERY_DIR": str(d), "ENGINE_FORMAT": fmt, "XDG_CACHE_HOME": str(tmp_path / "cache"),
               "MPLCONFIGDIR": str(tmp_path / "mpl"), "PYTHONPATH": str(ENGINE / "mpl")}
        env.pop("GNUPLOT_LIB", None)
        stem = tmp_path / f"{fmt}-{mode}"
        r = subprocess.run([sys.executable, "-c", GP, str(stem), mode], env=env, capture_output=True, text=True, cwd=tmp_path)
        assert r.returncode == 0, r.stderr
        mimes = json.loads(r.stdout.splitlines()[-1])
        assert mimes == (["application/pdf"] if fmt == "pdf" else ["image/svg+xml"]), f"{fmt}: {mimes}"
        fonts = subprocess.run(["pdffonts", f"{stem}.pdf"], capture_output=True, text=True).stdout
        assert L["typography"]["base"].replace(" ", "") in fonts, f"{fmt}: pdffonts {fonts}"
        if fmt == "pdf":
            continue
        svg = Path(f"{stem}.svg").read_text()
        assert "<text" not in svg and "<path" in svg, f"{mode}: SVG text not outlined"
        assert f'width="{w * 72:g}pt"' in svg and f'height="{h * 72:g}pt"' in svg, f"{mode}: SVG size {svg[:300]}"
        first = re.search(r'stroke-width="2"[^>]*stroke="rgb\(([\d.]+)%, ([\d.]+)%, ([\d.]+)%\)"', svg) or \
            re.search(r'stroke="rgb\(([\d.]+)%, ([\d.]+)%, ([\d.]+)%\)"[^>]*stroke-width="2"', svg)
        assert first, f"{mode}: no 2 pt line"
        got = "#" + "".join(f"{round(float(v) * 2.55):02X}" for v in first.groups())
        assert got == L["charts"][mode]["categorical"][0], f"{mode}: first line {got}"


@pytest.mark.skipif(not __import__("shutil").which("gnuplot"), reason="no gnuplot (the image's gnuplot-nox; brew install gnuplot)")
def test_gp_bundled_face(tmp_path):
    """livery_gp.plot() embeds a face the livery bundles but the machine has not installed: nasa's
    Public Sans. ncar's Poppins is installed on the Macs this runs on, so test_gp_render passes
    there without livery_gp's fontconfig file; without it (or without PANGOCAIRO_BACKEND=fc,
    Homebrew's pango then draws through CoreText) a Mac draws this in Helvetica. The image installs
    every livery's fonts, so there it passes either way."""
    import os
    import subprocess
    import sys
    d = ROOT / "liveries" / "nasa"
    family = json.loads((d / "build" / "livery.json").read_text())["typography"]["base"]
    env = {**os.environ, "LIVERY_DIR": str(d), "ENGINE_FORMAT": "pdf", "XDG_CACHE_HOME": str(tmp_path / "cache"),
           "MPLCONFIGDIR": str(tmp_path / "mpl"), "PYTHONPATH": str(ENGINE / "mpl")}
    env.pop("GNUPLOT_LIB", None)
    r = subprocess.run([sys.executable, "-c", GP, str(tmp_path / "p"), "light"], env=env, capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    fonts = subprocess.run(["pdffonts", str(tmp_path / "p.pdf")], capture_output=True, text=True).stdout
    assert family.replace(" ", "") in fonts, f"nasa: pdffonts {fonts}"
