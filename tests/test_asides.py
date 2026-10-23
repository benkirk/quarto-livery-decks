"""Quarto's asides ride with the speaker notes (engine-common.lua's is_aside / split_notes).

    python3 -m pytest tests/test_asides.py

Quarto appends `::: {.quarto-auto-generated-content}` (its footer, a logo) to a revealjs document,
so the last slide's blocks hold it; Quarto moves it out of the slide afterwards. The engine's slide
walkers that validate a body (split_full, agenda_notes, split_notes for the feature slide) treat it
as they treat the notes and the hidden div: on the notes side, never a reason to refuse the slide.
engine-common.lua under `pandoc lua` with the conftest shim (lua_common).
"""

import json

from conftest import lua_common

HARNESS = r"""
local doc = pandoc.read(io.read("a"), "markdown")
local body, notes = C.split_notes(doc.blocks)
local out = { body = #body, notes = #notes, asides = 0 }
for _, b in ipairs(doc.blocks) do if C.is_aside(b) then out.asides = out.asides + 1 end end
if arg[2] == "full" then
  local fig, caption, rest = C.split_full(doc.blocks)
  out.full = fig ~= nil; out.caption = fig and #caption or -1; out.rest = fig and #rest or -1
elseif arg[2] == "agenda" then
  out.agenda = #C.agenda_notes(doc.blocks, "t", "Agenda")
end
io.write(pandoc.json.encode(out) .. "\n")
"""

AUTO = '::: {.quarto-auto-generated-content style="display: none;"}\n::: {.footer .footer-default}\n:::\n:::\n'
NOTES = "::: {.notes}\nSpoken.\n:::\n"


def read(tmp_path, md, mode):
    out, warnings = lua_common(tmp_path, HARNESS, md, mode)
    return json.loads(out), warnings


def test_full_slide_ending_the_deck(tmp_path):
    """A {.full} slide's figure, caption and notes with Quarto's div after them: still a full
    slide; the div is in the rest with the notes, not a reason to draw an ordinary slide."""
    md = "![](p.png)\n\nA one-line caption.\n\n" + NOTES + "\n" + AUTO
    out, warnings = read(tmp_path, md, "full")
    assert not warnings, warnings
    assert out["full"] is True and out["caption"] == 1 and out["rest"] == 2, out
    assert out["asides"] == 2 and out["notes"] == 2 and out["body"] == 2, "the notes and the div on the notes side"


def test_full_slide_still_refuses_a_body(tmp_path):
    """The div is the only new exception: a list after the figure still makes an ordinary slide."""
    out, _ = read(tmp_path, "![](p.png)\n\n- a list\n\n" + AUTO, "full")
    assert out["full"] is False


def test_agenda_ending_the_deck(tmp_path):
    """An agenda slide's notes followed by Quarto's div: no "has a body of its own" warning, both
    blocks kept (the engine writes the body; Quarto moves its div out)."""
    out, warnings = read(tmp_path, NOTES + "\n" + AUTO, "agenda")
    assert not warnings, warnings
    assert out["agenda"] == 2


def test_agenda_still_refuses_a_body(tmp_path):
    out, warnings = read(tmp_path, "A paragraph.\n\n" + NOTES, "agenda")
    assert out["agenda"] == 0 and len(warnings) == 1 and "has a body of its own" in warnings[0], warnings


def test_hidden_div_is_an_aside(tmp_path):
    """Quarto's vault (`.hidden`) counts too, as single-body.lua always had it."""
    out, _ = read(tmp_path, "Text.\n\n::: {.hidden}\nkept apart\n:::\n", "full")
    assert out["asides"] == 1 and out["body"] == 1 and out["notes"] == 1
