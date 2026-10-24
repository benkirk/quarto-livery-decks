"""Compile a deck written on the theme's LaTeX layer (latex/authoring.md): cards on keys, strips,
status lists, columns, a caution box, a note, a scale group, steps, a timeline, the marking and
an unnumbered divider.

    python3 -m pytest tests/test_latex.py

A small deck on every environment (a status list nested in a status list among them, which once
looped TeX) compiles with XeLaTeX through latexmk, TEXINPUTS and TTFONTS set as latex/Makefile
sets them (the theme, the liveries and the root), and its log has no Overfull line; the frame
whose pick moves (`pick=<2>`) is two pages, and the frame whose step holds an `\\uncover<2->`; a
`role=` that is neither a role nor a color leaves the theme's warning in the log and takes the
default; the marking is on every page; a quote reads with its attribution, in a card too; an unnumbered divider has no eyebrow and leaves the count alone; the agenda lists the numbered
sections, a hand subtitle under its title, the Backup not; a third card or step on a row opened for two is the share
error; a gallery under its caption line, a bare [enginefull] frame filled with one, and four images on
three cells or thirteen in all the gallery's errors. A second deck cites with biblatex (author-year, bibtex, as the cookbook): the citation reads
on its frame, `\footcite` sets beamer's footnote there, the entries are on the References frame,
and its log has no Overfull line; skipped without biblatex. Skipped without xelatex (CI's latex
job runs in the image, which has TeX).
"""

import os
import re
import shutil
import subprocess

import pytest

from conftest import ENGINE, ROOT

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
\begin{frame}{Steps and a timeline}
\begin{enginesteps}[role=secondary]{3}
\begin{enginestep}{Propose} A one-page case. \end{enginestep}
\begin{enginestep}{Pilot} Six weeks. \par A second line. \uncover<2->{Overlays work.} \end{enginestep}
\begin{enginestep}{Scale} The allocation follows the pilot's numbers. \end{enginestep}
\end{enginesteps}
\begin{enginetimeline}{3}
\enginemilestone[done]{Q1 2025}{Proposal accepted}
\enginemilestone{Q3 2025}{Pilot complete}
\enginemilestone{2026}{Full allocation}
\end{enginetimeline}
\end{frame}
\begin{frame}{Steps from four}
\begin{enginesteps}[start=4]{2}
\begin{enginestep}{Review} The board reads it. \end{enginestep}
\begin{enginestep}{Decide} Yes or no. \end{enginestep}
\end{enginesteps}
\end{frame}
\begin{frame}{A quote}
\begin{enginequote}[role=accent]{R. Hamming, 1962}
The purpose of computing is insight, not numbers.
\end{enginequote}
\begin{enginequote}{}
No attribution, its own color.
\end{enginequote}
\begin{enginecards}{2}
\begin{enginecard}{IN A CARD}{}
\begin{enginequote}[role=nosuchrole]{Them}A quote in a card.\end{enginequote}
\end{enginecard}
\begin{enginecard}{OTHER}{}Text.\end{enginecard}
\end{enginecards}
\end{frame}
\begin{frame}{Pictured cards}
\begin{enginecards}{2}
\begin{enginecard}{PICTURED}{}
\includegraphics[width=\linewidth]{g1.png}
\enginenote{A caption.}
A line under it.
\end{enginecard}
\begin{enginecard}{OTHER}{}Text.\end{enginecard}
\end{enginecards}
\end{frame}
\begin{frame}[enginedark]{Dark}
\begin{itemize}\item A list item with \texttt{inline code}\end{itemize}
\begin{enginestatus}\done Done\fail Failed\end{enginestatus}
\begin{enginecards}{2}\begin{enginecard}{CARD}{}\enginelabel{A label} On its own fill.\end{enginecard}
\begin{enginecard}{OTHER}{}Text.\end{enginecard}\end{enginecards}
\enginefootnotespring
\begin{enginefootnotes}\enginefootnote{†}{A footnote on the dark frame.}\end{enginefootnotes}
\end{frame}
\begin{frame}{Light again}Back on the background.\end{frame}
\sectionsubtitle{Its subtitle}
\section{Numbered}
\begin{frame}{In the section}A slide.\end{frame}
\enginesectionunnumbered{Backup}{A subtitle}
\section{Second}
\begin{frame}{Where we are}\engineagenda\end{frame}
\begin{frame}{A gallery}
\begin{enginegallery}[cols=3]
\engineimage[A wide one]{g1.png}
\engineimage{g2.png}
\engineimage{g3.png}
\end{enginegallery}
\end{frame}
\begin{frame}[enginefull]
\enginefullcaption{The caption of the full gallery.}
\begin{enginegallery}[fit=cover]
\engineimage{g1.png}\engineimage{g2.png}\engineimage{g3.png}\engineimage{g1.png}
\end{enginegallery}
\end{frame}
\end{document}
"""

TOO_MANY_IMAGES = r"""
\documentclass[aspectratio=169]{beamer}
\usetheme[livery=liveries/ncar,fonts=bundled]{Engine}
\begin{document}
\begin{frame}{Four on three}
\begin{enginegallery}[cols=3,rows=1]
\engineimage{g1.png}\engineimage{g2.png}\engineimage{g3.png}\engineimage{g1.png}
\end{enginegallery}
\end{frame}
\end{document}
"""
THIRTEEN_IMAGES = TOO_MANY_IMAGES.replace("[cols=3,rows=1]", "").replace(
    r"\engineimage{g1.png}\engineimage{g2.png}\engineimage{g3.png}\engineimage{g1.png}", r"\engineimage{g1.png}" * 13)

TOO_MANY_STEPS = r"""
\documentclass[aspectratio=169]{beamer}
\usetheme[livery=liveries/ncar,fonts=bundled]{Engine}
\begin{document}
\begin{frame}{Three on two}
\begin{enginesteps}{2}
\begin{enginestep}{One} a \end{enginestep}
\begin{enginestep}{Two} b \end{enginestep}
\begin{enginestep}{Three} c \end{enginestep}
\end{enginesteps}
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


CITE = r"""
\documentclass[aspectratio=169]{beamer}
\usetheme[livery=liveries/ncar,fonts=bundled]{Engine}
\usepackage[style=authoryear,backend=bibtex]{biblatex}
\addbibresource{refs.bib}
\begin{document}
\begin{frame}{Citing sources}
MPAS runs on a C-grid \parencite{skamarock2012}; see \textcite{knuth84}.
A footnote citation\footcite{knuth84} at the foot.
\end{frame}
\begin{frame}[allowframebreaks]{References}
\printbibliography[heading=none]
\end{frame}
\end{document}
"""
BIB = """
@book{knuth84, author = {Knuth, Donald E.}, title = {The TeXbook}, publisher = {Addison-Wesley}, year = {1984}}
@article{skamarock2012, author = {Skamarock, William C. and Klemp, Joseph B.}, title = {A Multiscale
  Nonhydrostatic Atmospheric Model}, journal = {Monthly Weather Review}, volume = {140}, year = {2012}}
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
    from PIL import Image   # the galleries' images: a wide, a tall and a square one
    for name, size, color in (("g1.png", (320, 120), "#0057C2"), ("g2.png", (90, 240), "#FFA300"), ("g3.png", (150, 150), "#00A650")):
        Image.new("RGB", size, color).save(d / name)
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
    assert len(texts) == 18, "the pick=<2> and the \\uncover<2-> frames are two pages, the other fourteen one each"
    assert all("Lead and cards" in t for t in texts[:2]) and "Columns" in texts[2] and "Caution" in texts[3]
    assert "Overlays work" not in texts[4] and "Overlays work" in texts[5], "an overlay inside a step"
    for t in texts[4:6]:   # the rail's text in reading order: titles, bodies, dates, labels
        assert all(w in t for w in ("Propose", "Six weeks.", "Scale", "Q1 2025", "Proposal accepted", "2026")), t
    assert "Review" in texts[6] and {"4", "5"} <= set(texts[6].split()), "start=4: the badges read 4 and 5"


def test_quote(deck):
    """enginequote: its lines and the attribution after "— " on the frame, none without one; in a
    card too; a role= that is neither a role nor a color warns and takes the bar's color."""
    d, log = deck
    t = " ".join(pages(d / "deck.pdf")[7].split())
    assert "The purpose of computing is insight, not numbers. — R. Hamming, 1962" in t, t
    assert "No attribution, its own color." in t and "— No" not in t
    assert "A quote in a card. — Them" in t, t
    assert "role=nosuchrole is not a role of the livery or a color" in " ".join(log.split()), "the warning"


def test_pictured_card(deck):
    """A picture in a card at \\linewidth (the card's body width) with an \\enginenote caption under it:
    the frame draws the picture and the caption, the card's line after it (test_compiles_clean: no
    Overfull, so the picture fits the card)."""
    d, _ = deck
    t = " ".join(pages(d / "deck.pdf")[8].split())
    assert "Pictured cards" in t and "A caption." in t and t.index("A caption.") < t.index("A line under it."), t
    out = subprocess.run(["pdfimages", "-list", "-f", "9", "-l", "9", str(d / "deck.pdf")], capture_output=True, text=True).stdout
    assert len([l for l in out.splitlines()[2:] if l.split()[2:3] == ["image"]]) >= 1, out


def test_dark_frame(deck):
    """[enginedark]: the page on the livery's dark role (ncar's #011837, read off the page's corner), its
    text there; the frame after it back on the background (the colors put back on reset)."""
    from PIL import Image
    d, _ = deck
    t = " ".join(pages(d / "deck.pdf")[9].split())
    assert t.replace("TEST MARKING", "").strip().startswith("Dark") and "inline code" in t and "A footnote on the dark frame." in t and "A LABEL" in t, t
    for page, want in ((10, (0x01, 0x18, 0x37)), (11, (0xFF, 0xFF, 0xFF))):
        subprocess.run(["pdftoppm", "-r", "20", "-f", str(page), "-l", str(page), "-png", str(d / "deck.pdf"), str(d / f"pg{page}")],
                       check=True)
        im = Image.open(next(d.glob(f"pg{page}*.png"))).convert("RGB")
        px = im.getpixel((im.width // 2, im.height // 2 + im.height // 4))
        assert all(abs(a - b) <= 3 for a, b in zip(px, want)), (page, px, want)
    assert "Light again" in pages(d / "deck.pdf")[10]


def test_dark_frame_on_a_dark_livery(tmp_path):
    """[enginedark] under nasa-dark (a dark livery, livery.sty's \\engine@mode dark) changes nothing:
    the page is the livery's background, as the frame without the key."""
    if not (shutil.which("xelatex") and shutil.which("latexmk")):
        pytest.skip("xelatex and latexmk")
    from PIL import Image
    tex = DECK.split("\\begin{document}")[0].replace("liveries/ncar", "liveries/nasa-dark")
    tex += "\\begin{document}\n\\begin{frame}[enginedark]{Dark}Text.\\end{frame}\n\\begin{frame}{Plain}Text.\\end{frame}\n\\end{document}\n"
    r, log = compile_tex(tmp_path, "dd", tex)
    assert r.returncode == 0, log[-2000:]
    px = []
    for page in (1, 2):
        subprocess.run(["pdftoppm", "-r", "20", "-f", str(page), "-l", str(page), "-png", str(tmp_path / "dd.pdf"), str(tmp_path / f"p{page}")], check=True)
        im = Image.open(next(tmp_path.glob(f"p{page}*.png"))).convert("RGB")
        px.append(im.getpixel((im.width // 2, im.height // 2 + im.height // 4)))
    assert px[0] == px[1], px


def test_unnumbered_divider(deck):
    """\\enginesectionunnumbered draws a divider outside the count: no eyebrow, its subtitle, and
    the next \\section is still section 2."""
    d, _ = deck
    texts = pages(d / "deck.pdf")[11:]
    words = [" ".join(t.replace("TEST MARKING", "").split()) for t in texts]
    assert words[0] == "SECTION 1 Numbered Its subtitle" and "In the section" in words[1], words
    assert words[2] == "Backup A subtitle", words[2]
    assert words[3] == "SECTION 2 Second", words[3]


def test_agenda(deck):
    """\\engineagenda: the numbered sections from beamer's table of contents (latexmk's second run),
    each once, a hand author's \\sectionsubtitle under its title (the aux file's copy), the
    unnumbered Backup absent."""
    d, _ = deck
    t = " ".join(pages(d / "deck.pdf")[-3].replace("TEST MARKING", "").split())   # before the two gallery frames
    assert t.startswith("Where we are"), t
    assert t.count("Numbered") == 1 and t.count("Second") == 1 and "Its subtitle" in t, t
    assert "Backup" not in t, t


def test_role_warns_and_falls_back(deck):
    _, log = deck
    assert re.search(r"Package Engine Warning: role=nonesuch is not a role of the livery or a color;\s*\n?\(Engine\)\s+accent", log) \
        or "role=nonesuch is not a role of the livery or a color" in log, "the theme warns on an unknown role"


def test_marking_on_every_page(deck):
    d, _ = deck
    assert all("TEST MARKING" in t for t in pages(d / "deck.pdf"))


WATERMARKED = r"""
\documentclass[aspectratio=169]{beamer}
\usetheme[livery=liveries/ncar,fonts=bundled]{Engine}
\enginewatermark{DRAFT}
\title{A title}
\begin{document}
\begin{frame}\titlepage\end{frame}
\section{Part one}
\begin{frame}{Content}One line of body text.\end{frame}
\begin{frame}[enginedark]{Dark}A dark frame.\end{frame}
\end{document}
"""


def test_watermark_on_every_page(deck):
    """\\enginewatermark{}: the word on every page, the cover, the divider, a content frame and a dark
    one (pdftotext -raw keeps the turned word whole; -layout splits it into its letters among the
    body's lines, so a document of its own, not DECK); none with no word and no default."""
    d, _ = deck
    r, log = compile_tex(d, "wm", WATERMARKED)
    assert r.returncode == 0, log[-1500:]
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(d / "wm.pdf")], capture_output=True, text=True).stdout).group(1))
    raw = [subprocess.run(["pdftotext", "-f", str(k), "-l", str(k), "-raw", str(d / "wm.pdf"), "-"], capture_output=True, text=True).stdout
           for k in range(1, n + 1)]
    assert n == 4 and all("DRAFT" in t for t in raw), raw
    r, log = compile_tex(d, "plain", WATERMARKED.replace("\\enginewatermark{DRAFT}\n", ""))
    assert r.returncode == 0 and not any("DRAFT" in t for t in pages(d / "plain.pdf"))


NAMED = r"""
\documentclass[aspectratio=169]{beamer}
\usetheme[livery=liveries/ncar,fonts=bundled]{Engine}
\enginemarking[banner]{NAMED MARKING}
\enginemarking[nonesuch]{LOST}
\begin{document}
\begin{frame}{One}x\end{frame}
\end{document}
"""


def test_marking_by_name(deck):
    """\\enginemarking[<strip>]{}: the strip by its name; an unknown name warns and draws nothing."""
    d, _ = deck
    r, log = compile_tex(d, "named", NAMED)
    assert r.returncode == 0, log[-1500:]
    text = pages(d / "named.pdf")[0]
    assert "NAMED MARKING" in text and "LOST" not in text, text
    assert "nonesuch is not a marking strip" in " ".join(log.split()), "the theme warns on an unknown strip"


def test_too_many_cards(deck):
    d, _ = deck
    r, log = compile_tex(d, "toomany", TOO_MANY)
    assert r.returncode != 0 and "enginecards{2}: card 3 has no share" in log, log[-1500:]


def test_too_many_steps(deck):
    d, _ = deck
    r, log = compile_tex(d, "toomanysteps", TOO_MANY_STEPS)
    assert r.returncode != 0 and "enginesteps{2}: item 3 has no share" in log, log[-1500:]


@pytest.fixture(scope="module")
def cited(tmp_path_factory):
    if not (shutil.which("xelatex") and shutil.which("latexmk")):
        pytest.skip("xelatex and latexmk: the LaTeX layer compiles only with TeX")
    if not subprocess.run(["kpsewhich", "biblatex.sty"], capture_output=True, text=True).stdout.strip():
        pytest.skip("biblatex: the image's texlive-bibtex-extra")
    d = tmp_path_factory.mktemp("cite")
    (d / "refs.bib").write_text(BIB)
    r, log = compile_tex(d, "cite", CITE)
    assert r.returncode == 0, (r.stdout[-2000:], log[-3000:])
    return pages(d / "cite.pdf"), log


def test_cites(cited):
    texts, log = cited
    assert len(texts) == 2 and "Overfull" not in log, [l for l in log.splitlines() if l.startswith("Overfull")]
    assert "Skamarock and Klemp 2012" in texts[0] and "Knuth (1984)" in texts[0], texts[0]
    assert "Knuth 1984." in texts[0] or "Knuth 1984" in texts[0].split("at the foot.")[1], "the footcite at the frame's foot"
    assert "References" in texts[1] and "(1)" not in texts[1], "one page: no continuation count"
    assert "Knuth, Donald E. (1984)" in texts[1] and "Monthly Weather Review" in texts[1], texts[1]


def test_gallery(deck):
    """enginegallery: its frame's caption line under the pictures (cols=3, one row); the bare
    [enginefull] frame draws the gallery and its caption with no title."""
    d, _ = deck
    texts = pages(d / "deck.pdf")
    assert "A gallery" in texts[-2] and "A wide one" in texts[-2], texts[-2]
    full = " ".join(texts[-1].replace("TEST MARKING", "").split())
    assert full.startswith("The caption of the full gallery.") and "A gallery" not in full, full
    out = subprocess.run(["pdfimages", "-list", "-f", str(len(texts)), "-l", str(len(texts)), str(d / "deck.pdf")],
                         capture_output=True, text=True).stdout
    assert len([l for l in out.splitlines()[2:] if l.split()[2:3] == ["image"]]) >= 4, out   # four cells drawn


@pytest.mark.parametrize("tex, why", [("TOO_MANY_IMAGES", "enginegallery: 4 images do not fit cols=3, rows=1"),
                                      ("THIRTEEN_IMAGES", "enginegallery: more than twelve images")])
def test_too_many_images(deck, tex, why):
    d, _ = deck
    r, log = compile_tex(d, tex.lower(), globals()[tex])
    assert r.returncode != 0 and why in log, log[-1500:]
