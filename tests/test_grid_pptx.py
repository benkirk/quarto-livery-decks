"""Check grid-pptx.lua: a two-column slide's shares on a notes line, a grid slide flattened.

    python3 -m pytest tests/test_grid_pptx.py

A two-column slide keeps the Two Content layout (pandoc's placeholders idx 1 and 2) and its notes
carry `engine-columns: <share> <share>` (engine-common.lua's column_shares(): width= or an equal
share of what is left), with `wide` when slide-layout.lua's line says so, and no marker paragraph.
A three-column slide is flattened into one placeholder with its markers, every column's text kept;
a picture in it is warned of. pandoc's pptx writer itself keeps only the first two `.column`s: the
premise is checked without the filter, and when pandoc writes the third, the flattening's reason
for three columns is gone. Needs pandoc ($QUARTO_PANDOC).
"""

import os
import re
import shutil
import subprocess
import zipfile

import pytest

from conftest import ROOT

FILTER = ROOT / "_extensions" / "engine" / "grid-pptx.lua"
COL = "::: {{.column{}}}\n{}\n:::\n"
NOTES = "::: notes\nengine-layout: wide\n:::\n"   # slide-layout.lua's line, as it writes it
LEAD = "## Lead\n\n::: {.lead}\n**Head**\nline\n:::\n\n"
PIC = "## Picture\n\n:::: {.columns}\n" + "".join(COL.format("", w) for w in ("![](p.png)", "HHH", "III")) + "::::\n\n"
MD = ("## Three\n\n:::: {.columns}\n" + "".join(COL.format("", w) for w in ("AAA", "BBB", "CCC")) + "::::\n\n"
      "## Two\n\n:::: {.columns}\n" + COL.format(' width="55%"', "DDD") + COL.format("", "EEE") + "::::\n\n"
      "## Wide\n\n:::: {.columns}\n" + COL.format("", "FFF") + COL.format("", "GGG") + "::::\n\n" + NOTES)


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not pandoc:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")
    tmp = tmp_path_factory.mktemp("cols")
    shutil.copy(ROOT / "decks" / "quickstart" / "screenshots" / "hero.png", tmp / "p.png")

    def render(md, *args):
        out = tmp / "t.pptx"
        r = subprocess.run([pandoc, *args, "-o", str(out)], input=md, text=True, cwd=tmp, capture_output=True, check=True)
        with zipfile.ZipFile(out) as z:
            parts = {n: z.read(n).decode() for n in z.namelist() if re.match(r"ppt/(slides|notesSlides)/(_rels/)?\w+\d+\.xml(\.rels)?$", n)}
        return r.stderr, parts
    err, slides = render(MD + "\n" + PIC + LEAD, "--lua-filter", str(FILTER))
    _, plain = render(MD)
    return err, slides, plain


def text(slides, part):
    return "".join(re.findall(r"<a:t>([^<]*)</a:t>", slides[part]))


def notes(slides, n):
    """Slide n's notes text, through its relationship to its notes slide."""
    m = re.search(r'Target="\.\./notesSlides/(notesSlide\d+\.xml)"', slides[f"ppt/slides/_rels/slide{n}.xml.rels"])
    return text(slides, f"ppt/notesSlides/{m.group(1)}") if m else ""


def test_three_flattened(rendered):
    err, slides, _ = rendered
    one = slides["ppt/slides/slide1.xml"]
    assert one.count("<p:ph idx=") == 1 and 'idx="2"' not in one, "a three-column slide not in one placeholder"
    t = text(slides, "ppt/slides/slide1.xml")
    assert "⟦engine:columns widths=0.3333,0.3333,0.3333⟧" in t, "no columns marker"
    assert t.count("⟦engine:column⟧") == 3 and t.count("⟦engine:end⟧") == 4, "column markers"
    assert all(w in t for w in ("AAA", "BBB", "CCC")), "a column's text lost"
    assert '"Three"' not in err, "a warning for a text grid"
    assert 'slide "Picture": a picture/table in a card or a 3+ column slide is not drawn' in err, f"no picture warning: {err!r}"


def test_pandoc_still_drops_the_third(rendered):
    *_, plain = rendered
    body = "".join(text(plain, n) for n in plain if re.match(r"ppt/slides/slide", n))
    assert "AAA" in body and "BBB" in body, "pandoc lost a column it keeps"
    assert "CCC" not in body, "pandoc now writes a third column: grid-pptx.lua need not flatten for it"


def test_two_columns_marked(rendered):
    _, slides, _ = rendered
    two = slides["ppt/slides/slide2.xml"]
    assert 'idx="1"' in two and 'idx="2"' in two, "the 55/45 slide is not on Two Content's placeholders"
    assert "DDD" in text(slides, "ppt/slides/slide2.xml"), "the body is not its columns"
    assert "engine-columns: 0.55 0.45" in notes(slides, 2), "no shares line"
    assert "engine-columns: 0.5 0.5 wide" in notes(slides, 3), "no wide on the shares line"
    assert "engine-columns" not in notes(slides, 1), "a shares line on a three-column slide"
    assert not any("engine-columns" in text(slides, n) for n in slides if re.match(r"ppt/slides/slide", n)), "the line in a body"
    assert "⟦" not in text(slides, "ppt/slides/slide2.xml"), "a marker on a plain columns slide"


def test_lead_marked(rendered):
    _, slides, _ = rendered
    part = next(n for n in slides if re.match(r"ppt/slides/slide\d+\.xml$", n) and "Head" in text(slides, n))
    t = text(slides, part).removeprefix("Lead")
    assert t.startswith("⟦engine:lead⟧Head") and "line⟦engine:end⟧" in t, f"lead markers: {t!r}"
    paras = ["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", slides[part])]
    assert "Head" in paras and "line" in paras, f"the lead's two lines not two paragraphs: {paras}"


def test_card_marked(pandoc_deck, tmp_path):
    """A card column: its marker carries the role and flags, its heading is a ⟦engine:title⟧
    paragraph (no heading: pandoc would add spcBef), its sub, label and big lines theirs."""
    md = ('## Cards\n\n:::: {.columns}\n::: {.column .card .pick role="secondary"}\n### OPTION 1\n'
          '[The sub]{.sub}\n\n[LABEL]{.label}\n[$20M]{.big}\n:::\n::: {.column}\nPlain\n:::\n::::\n')
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    out = tmp_path / "c.pptx"
    subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        xml = z.read("ppt/slides/slide1.xml").decode()
    paras = ["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", xml)]
    for want in ("⟦engine:column card role=secondary pick⟧", "⟦engine:title⟧OPTION 1", "⟦engine:sub⟧The sub",
                 "⟦engine:label⟧LABEL", "⟦engine:big⟧$20M", "⟦engine:column⟧"):
        assert want in paras, f"{want!r} not a paragraph: {paras}"


def test_rail_marked(tmp_path):
    """Steps and a timeline: a rail marker with the kind and the role, an item marker per item
    (`done` on a done milestone), the title or date a ⟦engine:title⟧ paragraph, the text after it,
    every marker closed."""
    md = ('## Steps\n\n::: {.steps role="secondary"}\n1. **Propose** A case.\n2. **Pilot** Six weeks.\n:::\n\n'
          '## Timeline\n\n::: {.timeline}\n- [x] **Q1** Accepted\n- **2026** Full\n:::\n\n'
          '## Later\n\n::: {.steps}\n4. **Review** r\n:::\n')
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    out = tmp_path / "r.pptx"
    subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        slides = [z.read(f"ppt/slides/slide{n}.xml").decode() for n in (1, 2, 3)]
    paras = [["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", x)] for x in slides]
    paras = [[p for p in ps if p not in ("Steps", "Timeline", "Later")] for ps in paras]   # the titles
    assert paras[2][0] == "⟦engine:rail kind=steps role=primary-contrast start=4⟧", "a list from 4 carries its start"
    assert paras[0] == ["⟦engine:rail kind=steps role=secondary⟧", "⟦engine:item⟧", "⟦engine:title⟧Propose", "A case.",
                        "⟦engine:end⟧", "⟦engine:item⟧", "⟦engine:title⟧Pilot", "Six weeks.", "⟦engine:end⟧", "⟦engine:end⟧"], paras[0]
    assert paras[1] == ["⟦engine:rail kind=timeline role=primary-contrast⟧", "⟦engine:item done⟧", "⟦engine:title⟧Q1", "Accepted",
                        "⟦engine:end⟧", "⟦engine:item⟧", "⟦engine:title⟧2026", "Full", "⟦engine:end⟧", "⟦engine:end⟧"], paras[1]


def test_unnumbered_in_the_metadata(tmp_path):
    """pandoc's pptx writer drops `.unnumbered`: the filter writes the dividers outside the count,
    by their places among the dividers, as `engine-unnumbered` (docProps/custom.xml), for
    section_subtitle.py; a deck without one has no such property."""
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")

    def custom(md):
        out = tmp_path / "u.pptx"
        subprocess.run([pandoc, "--slide-level=2", "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True,
                       check=True, capture_output=True)
        with zipfile.ZipFile(out) as z:
            return z.read("docProps/custom.xml").decode() if "docProps/custom.xml" in z.namelist() else ""
    md = "# One\n\n## a\n\nx\n\n# Backup {.unnumbered}\n\n## b\n\ny\n\n# Two\n\n## c\n\nz\n\n# More {.unnumbered}\n\n## d\n\nw\n"
    prop = re.search(r'name="engine-unnumbered"[^>]*>.*?<vt:lpwstr>([^<]*)</vt:lpwstr>', custom(md), re.S)
    assert prop and prop.group(1) == "2 4", custom(md)
    assert "engine-unnumbered" not in custom(md.replace(" {.unnumbered}", ""))


def test_quote_marked(tmp_path):
    """A quote: `⟦engine:quote⟧` (role= only when it names one), a paragraph per source line, the
    attribution a paragraph led by `⟦engine:attribution⟧` without its dash, `⟦engine:end⟧`; a bare
    `>` the same. A quote in a column makes a two-column slide a grid slide (its columns flattened),
    and a quote on its own is marked too."""
    md = ('## Quote\n\n::: {.quote role="accent"}\nOne line\nanother\n— Who, 1962\n:::\n\n'
          '## Column\n\n:::: {.columns}\n::: {.column}\nLeft\n:::\n::: {.column}\n> Right\n> -- Them\n:::\n::::\n')
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    out = tmp_path / "q.pptx"
    subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        slides = [z.read(f"ppt/slides/slide{n}.xml").decode() for n in (1, 2)]
    paras = [["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", x)] for x in slides]
    assert paras[0][1:] == ["⟦engine:quote role=accent⟧", "One line", "another", "⟦engine:attribution⟧Who, 1962", "⟦engine:end⟧"], paras[0]
    assert paras[1][1:] == ["⟦engine:columns widths=0.5,0.5⟧", "⟦engine:column⟧", "Left", "⟦engine:end⟧", "⟦engine:column⟧",
                            "⟦engine:quote⟧", "Right", "⟦engine:attribution⟧Them", "⟦engine:end⟧", "⟦engine:end⟧", "⟦engine:end⟧"], paras[1]


def test_agenda_marked(tmp_path):
    """An agenda slide: its title, `⟦engine:agenda current=n⟧` (the numbered dividers before it), per
    numbered section an item marker with its number and state, the title and the divider's
    subtitle led by their prefixes; the unnumbered Backup absent; a body of its own dropped."""
    md = ("## Agenda {.agenda}\n\nAn author's line.\n\n# One\n\nIts subtitle.\n\n## a\n\nx\n\n"
          "# Two\n\n## Where we are {.agenda}\n\n# Backup {.unnumbered}\n\n## b\n\ny\n")
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    out = tmp_path / "a.pptx"
    r = subprocess.run([pandoc, "--slide-level=2", "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True,
                       check=True, capture_output=True)
    assert "has a body of its own" in r.stderr, r.stderr
    with zipfile.ZipFile(out) as z:
        texts = [[("".join(re.findall(r"<a:t>([^<]*)</a:t>", p))) for p in re.findall(r"<a:p>.*?</a:p>", z.read(n).decode())]
                 for n in sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                                 key=lambda n: int(re.search(r"(\d+)", n).group(1)))]
    front = next(t for t in texts if t and t[0] == "Agenda")
    assert front[1:] == ["⟦engine:agenda current=0⟧", "⟦engine:item n=1 state=next⟧", "⟦engine:title⟧One", "⟦engine:sub⟧Its subtitle.",
                         "⟦engine:end⟧", "⟦engine:item n=2 state=next⟧", "⟦engine:title⟧Two", "⟦engine:end⟧", "⟦engine:end⟧"], front
    later = next(t for t in texts if t and t[0] == "Where we are")
    assert "⟦engine:agenda current=2⟧" in later and "⟦engine:item n=1 state=done⟧" in later and "⟦engine:item n=2 state=current⟧" in later
    assert not any("Backup" in x for x in front + later), "an unnumbered divider is not on the agenda"


def test_quote_beside_a_picture(tmp_path):
    """A two-column slide with a quote in one column and a picture in the other stays pandoc's (a grid
    column cannot hold the picture): no marker, the quote pandoc's own blockquote, and a warning."""
    shutil.copy(ROOT / "decks" / "quickstart" / "screenshots" / "hero.png", tmp_path / "p.png")
    md = "## Beside\n\n:::: {.columns}\n" + COL.format("", "> Quoted\n> -- Them") + COL.format("", "![](p.png)") + "::::\n"
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    out = tmp_path / "b.pptx"
    r = subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, check=True,
                       capture_output=True, cwd=tmp_path)
    assert "a quote beside a picture or table in a two-column slide is not drawn in pptx" in r.stderr, r.stderr
    with zipfile.ZipFile(out) as z:
        xml = z.read("ppt/slides/slide1.xml").decode()
    assert "⟦engine:" not in xml and "Quoted" in xml and "<p:pic>" in xml, "pandoc's own slide, the picture in it"
