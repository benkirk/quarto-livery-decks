"""Check the quote block: engine-common.lua's reader (quote_parts(), quote_blocks()) and its face.

    python3 -m pytest tests/test_quote.py

A `::: {.quote role=..}` div and a bare `>` blockquote read alike: role= kept when it is a role or
a blend of the livery (a bare `>` has none: the box's bar-color), else warned of and dropped; each
source line a line; a last line starting with —, – or -- (pandoc's smart quotes make `--` an en
dash) the attribution, its dash and the space after it dropped. quote_blocks() finds a quote at any
depth (a column, a card) but not in the speaker notes; inside a .lead or a .strip it is warned of
and left as its lines. engine-common.lua runs under `pandoc lua` with a `quarto` shim
(test_footnotes.py's harness). The face: cu copied with boxes.quote {family: TeX Gyre Heros Cn,
style: italic} carries it into livery.css and livery.sty; the pptx sets a quote's lines in it,
italic, and its attribution in the body's face, upright; the PDF embeds the family's italic. A
family the livery does not bundle fails the build with its path. Needs pandoc ($QUARTO_PANDOC); the
PDF check needs XeLaTeX.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

import pytest

from conftest import ROOT
from test_boxes import tmp_livery

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


FACE = "TeX Gyre Heros Cn"   # cu's headings family, bundled


@pytest.fixture(scope="module")
def faced(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("face")
    rc, err, j = tmp_livery(tmp, f"  quote: {{family: {FACE}, style: italic}}\n", "cu")
    assert rc == 0, err
    return tmp, tmp / "liveries" / "cu", j


def test_face_in_every_file(faced):
    _, d, j = faced
    assert j["boxes"]["quote"]["family"] == FACE and j["boxes"]["quote"]["style"] == "italic"
    css, sty = (d / "build" / "livery.css").read_text(), (d / "build" / "livery.sty").read_text()
    assert f'--engine-quote-family: "{FACE}";' in css and "--engine-quote-style: italic;" in css
    assert f"\\def\\engine@quotefont@family{{{FACE}}}" in sty and "\\def\\engine@boxes@quote@style{italic}" in sty
    assert "\\def\\engine@quotefont@italic{" in sty, "the faces the family has"
    assert f'@font-face {{ font-family: "{FACE}"; font-style: italic;' in css, "the family's faces declared"


def test_unbundled_family_refused(tmp_path):
    rc, err, _ = tmp_livery(tmp_path, "  quote: {family: Nonesuch Serif}\n")
    assert rc != 0 and "boxes.quote.family: 'Nonesuch Serif' is not a typography.fonts family with files" in err, err


def test_face_in_pptx(faced, tmp_path):
    """A quote's lines in the family (no pptx.quote-typeface: its own name), italic; the attribution
    in the body's face (no typeface of its own), upright."""
    _, d, _ = faced
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    out = tmp_path / "q.pptx"
    md = '## Quote\n\n::: {.quote}\nThe purpose of computing\n— R. Hamming\n:::\n'
    subprocess.run([pandoc, "--lua-filter", str(ENGINE / "grid-pptx.lua"), "--reference-doc", str(ROOT / "liveries" / "cu" / "template.pptx"),
                    "-o", str(out)], input=md, text=True, check=True, capture_output=True, cwd=tmp_path)
    step = ("import sys\nfrom pptx import Presentation\nfrom pptx_steps import grid\n"
            "prs = Presentation(sys.argv[1]); grid.run(prs, 'q'); prs.save(sys.argv[1])\n")
    subprocess.run([sys.executable, "-c", step, str(out)], env={**os.environ, "LIVERY_DIR": str(d), "PYTHONPATH": str(ENGINE)},
                   check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        xml = z.read("ppt/slides/slide1.xml").decode()
    runs = re.findall(r"<a:r>(.*?)</a:r>", xml, re.S)
    line = next(r for r in runs if "The purpose" in r)
    who = next(r for r in runs if "Hamming" in r)
    assert f'typeface="{FACE}"' in line and re.search(r'<a:rPr[^>]* i="1"', line), line
    assert "typeface" not in who and not re.search(r'<a:rPr[^>]* i="1"', who), who


def test_face_in_pdf(faced):
    tmp, _, _ = faced
    if not (shutil.which("xelatex") and shutil.which("latexmk")):
        pytest.skip("xelatex and latexmk")
    (tmp / "q.tex").write_text("\\documentclass[aspectratio=169]{beamer}\n\\usetheme[livery=liveries/cu,fonts=bundled]{Engine}\n"
                               "\\begin{document}\n\\begin{frame}{Q}\\begin{enginequote}{R. Hamming}The purpose of computing."
                               "\\end{enginequote}\\end{frame}\n\\end{document}\n")
    env = {**os.environ, "TEXINPUTS": f"{ENGINE}//:{tmp}/liveries//:{tmp}/:", "TTFONTS": f"{tmp}/:{tmp}/liveries//:{ENGINE}//:"}
    r = subprocess.run(["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "q.tex"], cwd=tmp, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:]
    fonts = subprocess.run(["pdffonts", str(tmp / "q.pdf")], capture_output=True, text=True).stdout
    assert re.search(r"HerosCn-Italic|HerosCondensed-Italic|heroscn-italic", fonts, re.I), fonts
