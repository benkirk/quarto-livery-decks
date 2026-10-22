"""Compile a deck written on the theme's LaTeX layer (latex/authoring.md): cards on keys, strips,
status lists, columns, a caution box, a note, a scale group and the marking.

    python3 -m pytest tests/test_latex.py

A small deck on every environment (a status list nested in a status list among them, which once
looped TeX) compiles with XeLaTeX through latexmk, TEXINPUTS and TTFONTS set as latex/Makefile
sets them (the theme, the liveries and the root), and its log has no Overfull line; the frame whose pick moves (`pick=<2>`) is two pages; a `role=` that is neither a
role nor a color leaves the theme's warning in the log and takes the default; the marking is on
every page; a third card on a row opened for two is the share error. Skipped without xelatex
(CI's latex job runs in the image, which has TeX).
"""

import os
import re
import shutil
import subprocess

import pytest

from conftest import ROOT

ENGINE = ROOT / "_extensions" / "engine"
TEXENV = {"TEXINPUTS": f"{ENGINE}//:{ROOT}/liveries//:{ROOT}/:", "TTFONTS": f"{ROOT}/:{ROOT}/liveries//:{ENGINE}//:"}

DECK = r"""
\documentclass[aspectratio=169]{beamer}
\usetheme[livery=liveries/ncar,fonts=bundled]{Engine}
\enginemarking{TEST MARKING}
\begin{document}
\begin{frame}{Lead and cards}
\begin{enginelead}\textbf{Three ways.} Each trades one thing for another.\end{enginelead}
\begin{enginecards}{3}
\begin{enginecard}[pick]{OPTION 1}{A sub-line}
\enginelabel{Local investment}\enginebig{\$20M}
\begin{enginestrip}[role=accent]A strip in the card\end{enginestrip}
\begin{enginestatus}
\done Done thing
\warn<2-> Risky thing
\fail Failed thing
\item A plain item
\end{enginestatus}
\end{enginecard}
\begin{enginecard}[role=secondary,pick=<2>]{OPTION 2}{}
A body, the glyph in a line: \engineglyph{done}
\end{enginecard}
\begin{enginecard}[solid,role=nonesuch]{OPTION 3}{A sub-line}
On a solid card.
\begin{enginestatus}
\fail Failed, with a status list under it
  \begin{enginestatus}
  \warn Nested warn
  \done Nested done
  \end{enginestatus}
\done Done again
\end{enginestatus}
\end{enginecard}
\end{enginecards}
\end{frame}
\begin{frame}{Columns}
\begin{enginecolumns}{2,1}
\enginecolumn The wide column.
\enginecolumn The narrow one.
\end{enginecolumns}
\end{frame}
\begin{frame}[c]{Caution}
\begin{enginescale}{1.15}\begin{enginecaution}Careful.\end{enginecaution}\end{enginescale}
\enginenote{A note under it.}
\end{frame}
\end{document}
"""

TOO_MANY = r"""
\documentclass[aspectratio=169]{beamer}
\usetheme[livery=liveries/ncar,fonts=bundled]{Engine}
\begin{document}
\begin{frame}{Three on two}
\begin{enginecards}{2}
\begin{enginecard}{One}{} a \end{enginecard}
\begin{enginecard}{Two}{} b \end{enginecard}
\begin{enginecard}{Three}{} c \end{enginecard}
\end{enginecards}
\end{frame}
\end{document}
"""


def compile_tex(d, name: str, text: str):
    """latexmk on the deck written to d/name.tex: the completed process and the log's text."""
    (d / f"{name}.tex").write_text(text)
    r = subprocess.run(["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
                       cwd=d, env={**os.environ, **TEXENV}, capture_output=True, text=True)
    log = d / f"{name}.log"
    return r, log.read_text(errors="replace") if log.exists() else ""


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    if not (shutil.which("xelatex") and shutil.which("latexmk")):
        pytest.skip("xelatex and latexmk: the LaTeX layer compiles only with TeX")
    d = tmp_path_factory.mktemp("latex")
    r, log = compile_tex(d, "deck", DECK)
    assert r.returncode == 0, (r.stdout[-2000:], log[-3000:])
    return d, log


def pages(pdf) -> list[str]:
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    return [subprocess.run(["pdftotext", "-f", str(k), "-l", str(k), "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
            for k in range(1, n + 1)]


def test_compiles_clean(deck):
    _, log = deck
    assert "Overfull" not in log, [l for l in log.splitlines() if l.startswith("Overfull")]


def test_pick_moves(deck):
    d, _ = deck
    texts = pages(d / "deck.pdf")
    assert len(texts) == 4, "the pick=<2> frame is two pages, the other two one each"
    assert all("Lead and cards" in t for t in texts[:2]) and "Columns" in texts[2] and "Caution" in texts[3]


def test_role_warns_and_falls_back(deck):
    _, log = deck
    assert re.search(r"Package Engine Warning: role=nonesuch is not a role of the livery or a color;\s*\n?\(Engine\)\s+accent", log) \
        or "role=nonesuch is not a role of the livery or a color" in log, "the theme warns on an unknown role"


def test_marking_on_every_page(deck):
    d, _ = deck
    assert all("TEST MARKING" in t for t in pages(d / "deck.pdf"))


def test_too_many_cards(deck):
    d, _ = deck
    r, log = compile_tex(d, "toomany", TOO_MANY)
    assert r.returncode != 0 and "enginecards{2}: card 3 has no share" in log, log[-1500:]
