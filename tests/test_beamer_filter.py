"""Check engine-beamer.lua end to end under plain pandoc: the filter, then citeproc, as Quarto runs them.

    python3 -m pytest tests/test_beamer_filter.py

Quarto appends citeproc after the extension's filters, so a citation the filter has already turned
into LaTeX text prints as its key ("@key") and its entry never reaches the references (#172: a
quote's attribution). What commonly cites stays pandoc's inlines (the filter's wrapped()): a quote's
attribution, a `::: note`, a {.full} slide's caption; anywhere else the filter warns. The filter
runs with a `quarto` shim (its resolve_path, log and json). Needs pandoc ($QUARTO_PANDOC).
"""

import subprocess

from conftest import ENGINE, pandoc_exe

BIB = """@book{hamming1962, author={Hamming, R. W.}, title={Numerical Methods}, year={1962}, publisher={McGraw-Hill}}
@misc{wiki, author={{Wikipedia contributors}}, title={Livery}, year={2026}}
"""

DECK = """---
title: T
bibliography: refs.bib
---

## A quote

::: {.quote}
The purpose of computing is insight, not numbers.

— @hamming1962
:::

## A table with a note

| a | b |
|---|---|
| 1 | 2 |

::: note
Source: @wiki
:::

## Full {.full}

![](pic.png)

After [@hamming1962].

## A card

:::: {.columns}
::: {.column .card}
### Head @wiki

Body.
:::
::::

## References

::: {#refs}
:::
"""


def beamer(tmp_path, md):
    """(the LaTeX pandoc writes for md through engine-beamer.lua and citeproc, the filter's warnings)."""
    shim = tmp_path / "beamer-shim.lua"
    shim.write_text(
        f'local ENGINE = "{ENGINE}/"\n'
        'quarto = { utils = { resolve_path = function(p) return ENGINE .. p end },\n'
        '           log = { warning = function(s) io.stderr:write("WARNING: " .. s .. "\\n") end },\n'
        '           json = { decode = pandoc.json.decode }, doc = {} }\n'
        'return dofile(ENGINE .. "engine-beamer.lua")\n')
    (tmp_path / "refs.bib").write_text(BIB)
    r = subprocess.run([pandoc_exe(), "-t", "beamer", "--slide-level", "2", "--lua-filter", str(shim), "--citeproc"],
                       input=md, text=True, capture_output=True, cwd=tmp_path, check=True)
    return r.stdout, [w[len("WARNING: "):] for w in r.stderr.splitlines() if w.startswith("WARNING: ")]


def test_citations_reach_citeproc(tmp_path):
    tex, warns = beamer(tmp_path, DECK)
    assert "\\begin{enginequote}{Hamming (1962)}" in tex, "a quote's attribution that cites"
    assert "\\vskip-\\LTpost\\enginenote{Source: Wikipedia contributors (2026)}" in tex, "a note under a table"
    assert "\\enginefullcaption{After (Hamming 1962).}" in tex, "a full slide's caption"
    assert "@hamming1962" not in tex and "Hamming, R. W. 1962." in tex and "Wikipedia contributors. 2026." in tex, \
        "both entries in the references"
    assert "{Head @wiki}" in tex and len(warns) == 1 and 'a citation in "Head @wiki" prints as its key' in warns[0], warns


def test_plain_quote_and_note_unchanged(tmp_path):
    """Without a citation the LaTeX is what it was: the environment's line, the note's macro."""
    md = "## Q\n\n::: {.quote role=accent}\nLine one.\n\n— R. Hamming, *1962*\n:::\n\n::: {.quote}\nNo attribution.\n:::\n\n## N\n\n![](pic.png)\n\n::: note\nA *remark*.\n\nA second line.\n:::\n"
    tex, warns = beamer(tmp_path, md)
    assert "\\begin{enginequote}[role=accent]{R. Hamming, \\emph{1962}}" in tex and "\\begin{enginequote}{}" in tex
    assert "\\enginenote{A \\emph{remark}.\\par A second line.}" in tex and not warns, warns
