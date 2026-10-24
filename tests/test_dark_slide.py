"""Check the inverted content slide, `{.brand-dark}`: its reader and each format's drawing.

    python3 -m pytest tests/test_dark_slide.py

engine-common.lua's take_layout() reads `.brand-dark` as a layout class (`dark`, the class taken off
the heading) under `pandoc lua` (conftest's lua_common). livery.css on a light livery swaps the
roles a dark slide's text reads and restores them in a box with a fill of its own; a dark livery's
has no swap (the class is a no-op there).
"""

import json

from conftest import ROOT, lua_common

# take_layout() on each heading of the markdown from stdin: {dark, classes} or {nil}
HARNESS = r"""
local doc = pandoc.read(io.read("a"), "markdown")
for _, b in ipairs(doc.blocks) do
  if b.t == "Header" then
    local lay = C.take_layout(b, "t")
    io.write(pandoc.json.encode(lay and { dark = lay.dark, classes = b.classes } or { ["nil"] = true }) .. "\n")
  end
end
"""


def test_take_layout_dark(tmp_path):
    """`.brand-dark` is a layout class: dark, the class off the heading, another class kept; with
    .vcenter both; a heading without one nil."""
    out, warnings = lua_common(tmp_path, HARNESS, "## A {.brand-dark .mine}\n\n## B {.brand-dark .vcenter}\n\n## C\n")
    got = [json.loads(x) for x in out.splitlines()]
    assert got == [{"dark": True, "classes": ["mine"]}, {"dark": True, "classes": []}, {"nil": True}], got
    assert not warnings


def test_css_swaps_on_a_light_livery():
    """ncar: on .engine-dark the text's roles take their dark values (on-dark, dark-muted, secondary,
    the dark table blends), reveal's text colors and the hairline with them; a card, lead, strip,
    callout or caution body gets the livery's own back. nasa-dark (a dark livery): no swap."""
    j = json.loads((ROOT / "liveries" / "ncar" / "build" / "livery.json").read_text())
    css = (ROOT / "liveries" / "ncar" / "build" / "livery.css").read_text()
    c = {**j["roles"], **j["blends"]}
    on = css[css.index("/* the dark slide (.engine-dark)"):]
    on, back = on[:on.index("}")], on[on.index("}") + 1:]
    back = back[:back.index("}")]
    for role, dark in (("foreground", "on-dark"), ("muted", "dark-muted"), ("primary-contrast", "secondary"),
                       ("table-rule", "dark-rule"), ("table-band", "dark-band")):
        assert f"--engine-{role}: {c[dark]};" in on, (role, on)
        assert f"--engine-{role}: {c[role]};" in back, (role, back)
    assert f"--engine-title-color: {c['on-dark']};" in on, "the title on-dark"
    assert f"--r-main-color: {c['on-dark']};" in on and f"--engine-title-rule-color: {c['dark-rule']};" in on
    assert ":is(.engine-card, .engine-lead, .engine-strip, .callout)" in back, "the boxes' restore"
    assert ".engine-dark.engine-caution > .engine-body" in css
    dark = (ROOT / "liveries" / "nasa-dark" / "build" / "livery.css").read_text()
    assert "/* the dark slide (.engine-dark)" not in dark, "a dark livery swaps nothing"
