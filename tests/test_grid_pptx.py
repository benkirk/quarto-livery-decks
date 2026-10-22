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
          '## Timeline\n\n::: {.timeline}\n- [x] **Q1** Accepted\n- **2026** Full\n:::\n')
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    out = tmp_path / "r.pptx"
    subprocess.run([pandoc, "--lua-filter", str(FILTER), "-o", str(out)], input=md, text=True, check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        slides = [z.read(f"ppt/slides/slide{n}.xml").decode() for n in (1, 2)]
    paras = [["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>.*?</a:p>", x)] for x in slides]
    paras = [[p for p in ps if p not in ("Steps", "Timeline")] for ps in paras]   # the titles
    assert paras[0] == ["⟦engine:rail kind=steps role=secondary⟧", "⟦engine:item⟧", "⟦engine:title⟧Propose", "A case.",
                        "⟦engine:end⟧", "⟦engine:item⟧", "⟦engine:title⟧Pilot", "Six weeks.", "⟦engine:end⟧", "⟦engine:end⟧"], paras[0]
    assert paras[1] == ["⟦engine:rail kind=timeline role=primary-contrast⟧", "⟦engine:item done⟧", "⟦engine:title⟧Q1", "Accepted",
                        "⟦engine:end⟧", "⟦engine:item⟧", "⟦engine:title⟧2026", "Full", "⟦engine:end⟧", "⟦engine:end⟧"], paras[1]
