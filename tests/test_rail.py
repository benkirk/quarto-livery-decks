"""Check steps and timelines, the rail: engine-common.lua's reader (rail_kind(), rail_items()).

    python3 -m pytest tests/test_rail.py

A `::: {.steps}` div holds one ordered list, a `::: {.timeline}` one bullet list: each item's first
bold run is its title (a step's) or its date (a milestone's), the rest its text, a source line a
line; a milestone's `- [x]` is done, a plain item or `- [ ]` pending, `[!]` and `[-]` warned of and
pending. role= is taken off, `primary-contrast` by default, a name that is not the livery's warned
of. The wrong list, more than six items, or a picture inside warns and leaves the div alone; a rail
inside a column is not drawn (top_rails()), warned of.
engine-common.lua runs under `pandoc lua` with a `quarto` shim (conftest's lua_common).
Needs pandoc ($QUARTO_PANDOC).
"""

import json

import pytest

from conftest import lua_common


# rail_items() on every rail div of the markdown from stdin, as JSON lines: {kind, role, items:
# [{title, body (markdown), done}]} or {kind, nil: true} (conftest's lua_common: the quarto shim, C,
# the warnings)
HARNESS = r"""
local livery = arg[2] == "livery" and { roles = { ["primary-contrast"] = "#000000", secondary = "#111111" }, blends = { rule = "#222222" } } or nil
local doc = pandoc.read(io.read("a"), "markdown")
if arg[2] == "top" then   -- top_rails(): each drawn rail a paragraph naming it, the rest as it was
  local out = C.top_rails(doc.blocks, nil, "t", function(kind, r) return { pandoc.Para("RAIL " .. kind .. " " .. #r.items) } end)
  io.write(pandoc.write(pandoc.Pandoc(out), "markdown", { wrap_text = "none" }))
  return
end
local function md(blocks) return (pandoc.write(pandoc.Pandoc(blocks), "markdown", { wrap_text = "none" }):gsub("%s+$", "")) end
doc.blocks:walk({ Div = function(d)
  local kind = C.rail_kind(d)
  if not kind then return nil end
  local r = C.rail_items(d, kind, livery, "t")
  local out = { kind = kind, role_left = d.attributes["role"] or pandoc.json.null }
  if r then
    out.role, out.start, out.items = r.role, r.start or pandoc.json.null, {}
    for _, it in ipairs(r.items) do
      table.insert(out.items, { title = it.title and pandoc.utils.stringify(it.title) or pandoc.json.null,
                                body = md(it.body), done = it.done == nil and pandoc.json.null or it.done })
    end
  else
    out["nil"] = true
  end
  io.write(pandoc.json.encode(out) .. "\n")
end })
"""

STEPS = """::: {.steps role="secondary"}
1. **Propose** A one-page case; the review board reads it in a week.
2. **Pilot** Six weeks on the shared system.
   A second source line is a second line, as in a card.
3. **Scale** The allocation follows the pilot's numbers.
:::
"""
TIMELINE = """::: {.timeline}
- [x] **Q1 2025** Proposal accepted
- [ ] **Q3 2025** Pilot complete
- **2026** Full allocation
- [!] **2027** Review
:::
"""


def rails(tmp_path, md, livery=False):
    """The harness's output on md: (the rails, the warnings)."""
    out, warnings = lua_common(tmp_path, HARNESS, md, *(["livery"] if livery else []))
    return [json.loads(x) for x in out.splitlines()], warnings


def test_steps(tmp_path):
    (r,), warnings = rails(tmp_path, STEPS)
    assert not warnings, warnings
    assert r["kind"] == "steps" and r["role"] == "secondary" and r["role_left"] is None, "role= read and taken off"
    assert r["start"] == 1, "the list's first number"
    assert [i["title"] for i in r["items"]] == ["Propose", "Pilot", "Scale"]
    assert r["items"][0]["body"] == "A one-page case; the review board reads it in a week.", "the Space after the title dropped"
    assert r["items"][1]["body"] == "Six weeks on the shared system.\n\nA second source line is a second line, as in a card.", \
        "a source line a line"
    assert all(i["done"] is None for i in r["items"]), "a step has no status"


def test_start(tmp_path):
    """A process that goes on over a second slide: its list starts past 1, and the badges count
    from it (every format adds start - 1 to the item's place)."""
    (r,), warnings = rails(tmp_path, "::: {.steps}\n4. **Review** The board reads it.\n5. **Decide** Yes or no.\n:::\n")
    assert not warnings and r["start"] == 4 and [i["title"] for i in r["items"]] == ["Review", "Decide"], (r, warnings)


def test_timeline(tmp_path):
    (r,), warnings = rails(tmp_path, TIMELINE)
    assert r["kind"] == "timeline" and r["role"] == "primary-contrast", "the default role"
    assert r["start"] is None, "a timeline counts nothing"
    assert [i["title"] for i in r["items"]] == ["Q1 2025", "Q3 2025", "2026", "2027"]
    assert [i["done"] for i in r["items"]] == [True, False, False, False], "[x] done; [ ], plain and [!] pending"
    assert [i["body"] for i in r["items"]] == ["Proposal accepted", "Pilot complete", "Full allocation", "Review"], \
        "the glyph or box taken off"
    assert len(warnings) == 1 and "⚠ drawn as pending" in warnings[0], warnings


def test_role_checked(tmp_path):
    (r,), warnings = rails(tmp_path, STEPS.replace("secondary", "nope"), livery=True)
    assert r["role"] == "primary-contrast" and len(warnings) == 1 and 'role="nope"' in warnings[0], (r, warnings)
    (r,), warnings = rails(tmp_path, STEPS.replace("secondary", "rule"), livery=True)
    assert r["role"] == "rule" and not warnings, "a blend is a role="


@pytest.mark.parametrize("md, why", [
    ("::: {.steps}\n- **A** a bullet list\n:::\n", "holds one ordered list"),
    ("::: {.timeline}\n1. **A** an ordered list\n:::\n", "holds one bullet list"),
    ("::: {.steps}\n1. **A** one\n\nA paragraph after it.\n:::\n", "and nothing else"),
    ("::: {.steps}\n" + "".join(f"{k}. **S{k}** text\n" for k in range(1, 8)) + ":::\n", "has 7 items, more than 6"),
    ("::: {.steps}\n1. **A** ![](p.png)\n2. **B** text\n:::\n", "a picture or table"),
])
def test_refused(tmp_path, md, why):
    (r,), warnings = rails(tmp_path, md)
    assert r.get("nil") and len(warnings) == 1 and why in warnings[0], (r, warnings)


def test_no_title(tmp_path):
    """An item without a leading bold run: no title, all of it the text."""
    (r,), _ = rails(tmp_path, "::: {.steps}\n1. Plain *step*.\n2. **B**\n:::\n")
    assert r["items"][0] == {"title": None, "body": "Plain *step*.", "done": None}
    assert r["items"][1]["title"] == "B" and r["items"][1]["body"] == "", "a title alone: no text"


def test_top_level_only(tmp_path):
    """A rail at the slide's top level is drawn; one in a column is warned of and stays a list."""
    md = STEPS + "\n:::: {.columns}\n::: {.column}\n" + TIMELINE + ":::\n::::\n"
    text, warnings = lua_common(tmp_path, HARNESS, md, "top")
    assert "RAIL steps 3" in text and "RAIL timeline" not in text, text
    assert "Proposal accepted" in text, "the nested timeline kept as its list"
    assert len(warnings) == 1 and ".timeline inside a column or another div is not drawn" in warnings[0], warnings
