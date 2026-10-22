"""Check the quote block's reader: engine-common.lua's quote_parts() and quote_blocks().

    python3 -m pytest tests/test_quote.py

A `::: {.quote role=..}` div and a bare `>` blockquote read alike: role= kept when it is a role or
a blend of the livery (a bare `>` has none: the box's bar-color), else warned of and dropped; each
source line a line; a last line starting with —, – or -- (pandoc's smart quotes make `--` an en
dash) the attribution, its dash and the space after it dropped. quote_blocks() finds a quote at any
depth (a column, a card) but not in the speaker notes; inside a .lead or a .strip it is warned of
and left as its lines. engine-common.lua runs under `pandoc lua` with a `quarto` shim
(test_footnotes.py's harness). Needs pandoc ($QUARTO_PANDOC).
"""

import json
import os
import shutil
import subprocess

import pytest

from conftest import ROOT

ENGINE = ROOT / "_extensions" / "engine"

# quote_blocks() over the markdown from stdin: each quote drawn as a JSON line {role, lines, who},
# the rest of the document after them as markdown, each warning a line "WARNING: ..."
HARNESS = r"""
local warnings = {}
quarto = { log = { warning = function(s) table.insert(warnings, s) end } }
local C = dofile(arg[1])
local livery = { roles = { accent = "#000000", secondary = "#111111" }, blends = { rule = "#222222" } }
local doc = pandoc.read(io.read("a"), "markdown")
local drawn = {}
local out = C.quote_blocks(doc.blocks, livery, "t", function(q)
  local lines = {}
  for _, b in ipairs(q.body) do table.insert(lines, pandoc.utils.stringify(b)) end
  table.insert(drawn, pandoc.json.encode({ role = q.role or pandoc.json.null, lines = lines,
    who = q.attribution and pandoc.utils.stringify(q.attribution) or pandoc.json.null }))
  return pandoc.Para({ pandoc.Str("QUOTE") })
end)
for _, d in ipairs(drawn) do io.write(d .. "\n") end
io.write(pandoc.write(pandoc.Pandoc(out), "markdown", { wrap_text = "none" }))
for _, w in ipairs(warnings) do io.write("\nWARNING: " .. w) end
"""


def read(tmp_path, md):
    exe = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not exe:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")
    script = tmp_path / "harness.lua"
    script.write_text(HARNESS)
    r = subprocess.run([exe, "lua", str(script), str(ENGINE / "engine-common.lua")], input=md, text=True,
                       capture_output=True, check=True)
    quotes = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    rest = "\n".join(l for l in r.stdout.splitlines() if not l.startswith("{") and not l.startswith("WARNING:"))
    return quotes, rest, [l for l in r.stdout.splitlines() if l.startswith("WARNING:")]


def test_div_and_blockquote(tmp_path):
    md = ('::: {.quote role="accent"}\nThe purpose of computing\nis insight.\n— R. Hamming, 1962\n:::\n\n'
          '> A bare blockquote.\n> -- Someone\n\n'
          '::: {.quote role="rule"}\nA blend colors it too.\n– Anon\n:::\n\n'
          '> A dash inside a line - is not one.\n')
    quotes, _, warnings = read(tmp_path, md)
    assert quotes == [
        {"role": "accent", "lines": ["The purpose of computing", "is insight."], "who": "R. Hamming, 1962"},
        {"role": None, "lines": ["A bare blockquote."], "who": "Someone"},
        {"role": "rule", "lines": ["A blend colors it too."], "who": "Anon"},
        {"role": None, "lines": ["A dash inside a line - is not one."], "who": None},
    ], quotes
    assert not warnings


def test_bad_role_warned(tmp_path):
    quotes, _, warnings = read(tmp_path, '::: {.quote role="nope"}\nText.\n:::\n')
    assert quotes == [{"role": None, "lines": ["Text."], "who": None}]
    assert any('role="nope" is not a role or a blend' in w for w in warnings), warnings


def test_where_drawn(tmp_path):
    """In a column and a card: drawn. In the notes: left alone. In a lead or a strip: its lines,
    warned of."""
    md = (':::: {.columns}\n::: {.column .card}\n### A\n> In a card.\n:::\n::: {.column}\n> In a column.\n:::\n::::\n\n'
          '::: notes\n> In the notes.\n:::\n\n'
          '::: {.lead}\n> In a lead.\n:::\n\n'
          '::: {.strip}\n::: {.quote}\nIn a strip.\n:::\n:::\n')
    quotes, rest, warnings = read(tmp_path, md)
    assert [q["lines"] for q in quotes] == [["In a card."], ["In a column."]], quotes
    assert "> In the notes." in rest, rest
    assert "In a lead." in rest and "> In a lead." not in rest and "In a strip." in rest
    assert sum("inside a .lead or a .strip is not drawn" in w for w in warnings) == 2, warnings
