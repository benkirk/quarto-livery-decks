"""Check a columns slide's frames in the pptx (grid-pptx.lua, then pptx_steps/columns.py).

    python3 -m pytest tests/test_grid.py

pandoc writes a deck on the livery's template with grid-pptx.lua (slide-layout.lua's `wide` line
written by hand: that filter needs Quarto), then the driver's steps run in a subprocess under the
livery's LIVERY_DIR. A 55/45 slide's placeholders are the shares of the content box less the gap,
within 1 EMU; a picture pandoc put at the old half frame moves into its column and scales to its
width, its aspect kept; a {.wide} slide's box starts at geometry.wide-margin, its Title and Content
body and a table too (its grid columns scaled); every offset, extent and size is an integer EMU. Under ncar and nasa-jsc-eg (another
canvas, a dark livery). Needs pandoc ($QUARTO_PANDOC).
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

ENGINE = ROOT / "_extensions" / "engine"
IMAGE = ROOT / "decks" / "quickstart" / "images" / "example.jpg"
CARDS = ('## Cards\n\n:::: {.columns}\n'
         '::: {.column .card .pick role="primary"}\n### OPTION 1\n[Procure a system]{.sub}\n\n'
         '**Total**\n[LOCAL INVESTMENT]{.label}\n[$20M]{.big}\n\n::: {.strip role="accent"}\nTo the consortium\n:::\n\n'
         '- one\n- two\n- three\n:::\n'
         '::: {.column .card role="secondary"}\n### OPTION 2\nShort.\n:::\n'
         '::: {.column .card .solid role="accent"}\n### OPTION 3\nSolid.\n:::\n::::\n')
DEFAULTS = ('## Default roles\n\n:::: {.columns}\n' + ''.join(f'::: {{.column .card}}\n### {t}\nText.\n:::\n' for t in 'ABCD')
            + '::::\n')
WIDE = "\n::: notes\nengine-layout: wide\n:::\n"
MD = ('## Split\n\n:::: {.columns}\n::: {.column width="55%"}\n- One\n- Two\n:::\n::: {.column}\n![](p.jpg)\n:::\n::::\n\n'
      '## Wide\n\n:::: {.columns}\n::: {.column}\nLeft\n:::\n::: {.column}\nRight\n:::\n::::\n' + WIDE + '\n'
      '## Wide text\n\nA paragraph.\n' + WIDE + '\n'
      '## Three\n\n:::: {.columns}\n::: {.column}\n- AAA\n- aaa\n:::\n::: {.column}\nBBB\n:::\n::: {.column}\nCCC\n:::\n::::\n\n'
      '## Lead\n\n::: {.lead}\n**The headline**\nA plain line under it.\n:::\n\n'
      ':::: {.columns}\n::: {.column}\nLLL\n:::\n::: {.column}\nMMM\n:::\n::::\n\n'
      '## Lead alone\n\n::: {.lead}\nOnly a lead.\n:::\n\n' + CARDS + '\n' + DEFAULTS + '\n'
      '## Wide table\n\n| a | b | c |\n|---|---|---|\n| 1 | 2 | 3 |\n' + WIDE)
STEP = """
import sys
from pathlib import Path
from pptx import Presentation
from pptx_steps import columns, grid, slide_layout
p = Path(sys.argv[1]); prs = Presentation(p)
slide_layout.run(prs, p); columns.run(prs, p.name); grid.run(prs, p.name); prs.save(p)
"""   # the driver's order


@pytest.fixture(scope="module", params=["ncar", "nasa-jsc-eg"])
def deck(request, tmp_path_factory):
    name = request.param
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    if not pandoc:
        pytest.fail("pandoc not found: set QUARTO_PANDOC or source etc/config_env.sh")
    tmp = tmp_path_factory.mktemp(f"grid-{name}")
    shutil.copy(IMAGE, tmp / "p.jpg")
    d = ROOT / "liveries" / name
    out = tmp / "t.pptx"
    subprocess.run([pandoc, "--lua-filter", str(ENGINE / "grid-pptx.lua"), "--reference-doc", str(d / "template.pptx"),
                    "-o", str(out)], input=MD, text=True, cwd=tmp, check=True, capture_output=True)
    env = {**os.environ, "LIVERY_DIR": str(d), "PYTHONPATH": str(ENGINE)}
    subprocess.run([sys.executable, "-c", STEP, str(out)], env=env, check=True, capture_output=True)
    from pptx import Presentation
    return json.loads((d / "build" / "livery.json").read_text()), Presentation(str(out)), out


def boxes(livery, width, shares, wide=False):
    g = livery["geometry"]
    m, gap = g["wide-margin" if wide else "margin"], livery["boxes"]["columns"]["gap"]
    room, x, out = 1 - 2 * m - gap * (len(shares) - 1), m, []
    for s in shares:
        out.append((x * width, room * s * width))
        x += room * s + gap
    return out


def flat(shapes):
    """Every shape, the ones in groups too (a card, a lead, a strip is a group of its shapes)."""
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:   # a group
            yield from flat(sh.shapes)


def body_placeholders(slide):
    return {sh.placeholder_format.idx: sh for sh in slide.placeholders if sh.placeholder_format.idx in (1, 2)}


def test_shares(deck):
    livery, prs, _ = deck
    slide = prs.slides[0]
    (x1, w1), (x2, w2) = boxes(livery, prs.slide_width, [0.55, 0.45])
    ph = body_placeholders(slide)
    assert abs(ph[1].left - x1) <= 1 and abs(ph[1].width - w1) <= 1, f"left column {ph[1].left, ph[1].width}, want {x1, w1}"
    pic = next(sh for sh in slide.shapes if sh.shape_type == 13)
    assert abs(pic.width - w2) <= 1 and abs(pic.left - x2) <= 1, f"the picture {pic.left, pic.width}, want {x2, w2}"
    from PIL import Image
    iw, ih = Image.open(IMAGE).size
    assert abs(pic.height / pic.width - ih / iw) < 0.01, "the picture's aspect"
    assert not slide.notes_slide.notes_text_frame.text.strip().startswith("engine-columns"), "the line left in the notes"


def test_wide(deck):
    livery, prs, _ = deck
    (x1, w1), (x2, w2) = boxes(livery, prs.slide_width, [0.5, 0.5], wide=True)
    ph = body_placeholders(prs.slides[1])
    assert abs(ph[1].left - x1) <= 1 and abs(ph[2].left - x2) <= 1 and abs(ph[2].width - w2) <= 1, \
        f"wide columns {[(p.left, p.width) for p in ph.values()]}, want {x1, x2, w2}"
    m = livery["geometry"]["wide-margin"]
    body = body_placeholders(prs.slides[2])[1]
    assert abs(body.left - m * prs.slide_width) <= 1 and abs(body.width - (1 - 2 * m) * prs.slide_width) <= 1, \
        "a wide Title and Content body"
    assert body.top > 0 and body.height > 0, "the body's top and height kept (all four fields set)"
    table = next(sh for sh in prs.slides[8].shapes if getattr(sh, "has_table", False))   # a graphicFrame, not a body
    assert abs(table.left - m * prs.slide_width) <= 1 and abs(table.width - (1 - 2 * m) * prs.slide_width) <= 1, \
        f"a wide table {table.left, table.width}: pandoc's frame kept"
    cols = table.table._tbl.findall("{*}tblGrid/{*}gridCol")
    assert abs(sum(int(c.get("w")) for c in cols) - table.width) <= len(cols), "the grid columns not scaled to the frame"


def test_integers(deck):
    *_, out = deck
    with zipfile.ZipFile(out) as z:
        xml = "".join(z.read(n).decode() for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n))
    floats = re.findall(r'\b(x|y|cx|cy|w|h|sz|marL|indent|adj)="-?[0-9]+\.[0-9]+"', xml)
    assert not floats, f"non-integer EMUs: {floats[:5]}"


def test_three_columns(deck):
    """A three-column slide: three text boxes at the formula's frames, the placeholder gone, its
    list keeping the template's bullet (the box's list style is the master's body style)."""
    livery, prs, _ = deck
    slide = prs.slides[3]
    cols = sorted((sh for sh in slide.shapes if re.fullmatch(r"Column \d+", sh.name)), key=lambda sh: sh.name)
    assert [c.name for c in cols] == ["Column 1", "Column 2", "Column 3"], [sh.name for sh in slide.shapes]
    for c, (x, w) in zip(cols, boxes(livery, prs.slide_width, [0.3333, 0.3333, 0.3333])):
        assert abs(c.left - x) <= 2 * len(cols) and abs(c.width - w) <= 2 * len(cols), f"{c.name} {c.left, c.width}, want {x, w}"
    assert [c.text_frame.text.split("\n")[0] for c in cols] == ["AAA", "BBB", "CCC"], "the columns' text"
    assert not body_placeholders(slide), "the emptied placeholder left on the slide"
    xml = slide._element.xml
    assert "⟦" not in xml, "a marker left"
    assert cols[0]._element.find(".//{*}lstStyle/{*}lvl1pPr") is not None, "no list style in the box"


def test_column_rules(deck):
    """boxes.columns.rule: one rule in each gap where the livery sets one (nasa-jsc-eg), none where
    it is 0 (ncar); centered in the gap, its width the fraction of the slide's height."""
    livery, prs, _ = deck
    w = round(livery["boxes"]["columns"]["rule"] * prs.slide_height)
    counts = [sum(sh.name == "Column rule" for sh in s.shapes) for s in prs.slides]
    if w == 0:
        assert counts == [0] * 9, f"rules under a livery without one: {counts}"
        return
    assert counts == [1, 1, 0, 2, 1, 0, 2, 3, 0], f"rules per slide {counts}, want one per gap"
    slide = prs.slides[3]
    cols = sorted((sh for sh in slide.shapes if re.fullmatch(r"Column \d+", sh.name)), key=lambda sh: sh.name)
    for rule, (a, b) in zip(sorted((sh for sh in slide.shapes if sh.name == "Column rule"), key=lambda sh: sh.left), zip(cols, cols[1:])):
        mid = (a.left + a.width + b.left) / 2
        assert rule.width == w and abs(rule.left + rule.width / 2 - mid) <= 1, f"a rule at {rule.left}, {rule.width}; the gap's middle {mid}"
        assert rule.height > 0 and rule.top == a.top, "the rule runs down the row from its top"


def test_lead(deck):
    """A lead over two columns: its text box on the lead fill with a bar of bar-color at its left,
    cut to its text, its source lines two paragraphs; the columns below it, the slide a grid slide
    (two text boxes, no placeholder). A lead alone is drawn the same way."""
    livery, prs, _ = deck
    lead = livery["boxes"]["lead"]
    for n, text in ((4, ["The headline", "A plain line under it."]), (5, ["Only a lead."])):
        slide = prs.slides[n]
        by = {sh.name: sh for sh in flat(slide.shapes)}
        assert {"Lead", "Lead fill", "Lead bar", "Lead text"} <= set(by), f"slide {n + 1}: {sorted(by)}"
        assert by["Lead"].shape_type == 6 and len(by["Lead"].shapes) == 3, "the lead one group of its three shapes"
        assert str(by["Lead fill"].fill.fore_color.rgb) == lead["fill"][1:], "the lead's fill"
        assert str(by["Lead bar"].fill.fore_color.rgb) == lead["bar-color"][1:], "the bar's color"
        assert by["Lead bar"].width == round(lead["bar"] * prs.slide_height), "the bar's width"
        assert by["Lead fill"].height == by["Lead text"].height < prs.slide_height / 3, "the lead cut to its text"
        assert [p.text for p in by["Lead text"].text_frame.paragraphs] == text, "a source line a paragraph"
        assert "⟦" not in slide._element.xml, "a marker left"
    by = {sh.name: sh for sh in flat(prs.slides[4].shapes)}
    assert by["Column 1"].top >= by["Lead fill"].top + by["Lead fill"].height, "the columns under the lead"
    assert not body_placeholders(prs.slides[4]), "the emptied placeholder left"


def test_cards(deck):
    """Three cards: at the formula's frames, one height; each head band in its role, the title
    run bold in the subhead size and primary-text; the pick outlined in outline-color; the solid
    card's fill its role; the label in caps, the big number in the display size; no marker left."""
    import livery as livery_mod
    livery, prs, _ = deck
    slide = prs.slides[6]
    by = {sh.name: sh for sh in flat(slide.shapes)}
    cards = [by[f"Card {n} fill"] for n in (1, 2, 3)]
    for n in (1, 2, 3):   # each card one group: its fill, head or outline, text and strips inside
        g = by[f"Card {n}"]
        assert g.shape_type == 6 and f"Card {n} fill" in {sh.name for sh in flat(g.shapes)}, f"Card {n} is not a group of its shapes"
    for c, (x, w) in zip(cards, boxes(livery, prs.slide_width, [0.3333, 0.3333, 0.3333])):
        assert abs(c.left - x) <= 6 and abs(c.width - w) <= 6, f"{c.name} {c.left, c.width}, want {x, w}"
    assert len({c.height for c in cards}) == 1 and len({c.top for c in cards}) == 1, "the cards one height"
    role = lambda r: livery["roles"][r][1:]
    assert str(by["Card 1 head"].fill.fore_color.rgb) == role("primary"), "the head band in its role"
    assert str(by["Card 2 head"].fill.fore_color.rgb) == role("secondary")
    assert "Card 3 head" not in by and str(by["Card 3 fill"].fill.fore_color.rgb) == role("accent"), "a solid card is its role"
    ol = by["Card 1 outline"]
    assert str(ol.line.color.rgb) == livery["boxes"]["card"]["outline-color"][1:], "the pick's outline color"
    assert ol.line.width == round(livery["boxes"]["card"]["outline"] * prs.slide_height), "the outline's width"
    assert "Card 2 outline" not in by, "an outline on a card not picked"
    title = by["Card 1 title"].text_frame.paragraphs[0].runs[0].font
    assert title.bold and title.size.pt == livery_mod.half_pt(livery["type"]["roles"]["subhead"]["pt"]), "the title's look"
    assert str(title.color.rgb) == role("primary-text"), "the title on the role in primary-text"
    body = by["Card 1 body"].text_frame.paragraphs
    label = next(p for p in body if p.text == "LOCAL INVESTMENT")
    big = next(p for p in body if p.text == "$20M")
    assert label.runs[0]._r.find("{*}rPr").get("cap") == "all", "the label in caps"
    assert big.runs[0].font.size.pt == livery_mod.half_pt(livery["type"]["roles"]["display"]["pt"]), "the big number's size"
    assert "⟦" not in slide._element.xml, "a marker left"


def test_card_type_step(pandoc_deck, tmp_path):
    """A deck's type-body: 10 scales a card's big number as the rest (type_step runs after grid):
    ncar's display role (30 pt on its 12 pt body) to half_pt(30 x 10 / 12)."""
    import livery as livery_mod
    md = "---\ntype-body: 10\n---\n\n" + CARDS
    d = ROOT / "liveries" / "ncar"
    pandoc = os.environ.get("QUARTO_PANDOC") or shutil.which("pandoc")
    out = tmp_path / "t.pptx"
    subprocess.run([pandoc, "--lua-filter", str(ENGINE / "grid-pptx.lua"), "--reference-doc", str(d / "template.pptx"),
                    "-o", str(out)], input=md, text=True, cwd=tmp_path, check=True, capture_output=True)
    step = STEP.replace("prs.save(p)", "from pptx_steps import type_step; type_step.run(prs, p); prs.save(p)")
    env = {**os.environ, "LIVERY_DIR": str(d), "PYTHONPATH": str(ENGINE)}
    subprocess.run([sys.executable, "-c", step, str(out)], env=env, check=True, capture_output=True)
    from pptx import Presentation
    j = json.loads((d / "build" / "livery.json").read_text())
    body = {sh.name: sh for sh in flat(Presentation(str(out)).slides[0].shapes)}["Card 1 body"].text_frame.paragraphs
    big = next(p for p in body if p.text == "$20M")
    want = livery_mod.half_pt(j["type"]["roles"]["display"]["pt"] * 10 / j["type"]["roles"]["body"]["pt"])
    assert big.runs[0].font.size.pt == want, f"the big number at {big.runs[0].font.size.pt}, want {want}"


def test_strip(deck):
    """A strip in a card: its rectangle the strip.tint of its role over the background, at the card's
    full width, between the body's text above and below it, its text in its own box."""
    import livery as livery_mod
    livery, prs, _ = deck
    by = {sh.name: sh for sh in flat(prs.slides[6].shapes)}
    strip, card = by["Card 1 strip 1"], by["Card 1 fill"]
    want = livery_mod.mix(livery["roles"]["accent"], livery["roles"]["background"], livery["boxes"]["strip"]["tint"])
    assert "#" + str(strip.fill.fore_color.rgb) == want, f"the strip's fill {strip.fill.fore_color.rgb}, want {want}"
    assert (strip.left, strip.width) == (card.left, card.width), "the strip at the card's full width"
    assert by["Card 1 strip 1 text"].text_frame.text == "To the consortium"
    above, below = by["Card 1 body"], by["Card 1 body 3"]
    assert above.top + above.height <= strip.top and strip.top + strip.height <= below.top, "the strip between the body's text"
    assert "one" in below.text_frame.text and "$20M" in above.text_frame.text, "the text on each side"


def test_default_roles(deck):
    """Cards without role= take boxes.card.roles in turn by their place in the row, the fourth the
    first again: no two neighbors alike."""
    livery, prs, _ = deck
    by = {sh.name: sh for sh in flat(prs.slides[7].shapes)}
    roles = livery["boxes"]["card"]["roles"]
    want = [livery["roles"][roles[k % len(roles)]][1:] for k in range(4)]
    assert [str(by[f"Card {n} head"].fill.fore_color.rgb) for n in (1, 2, 3, 4)] == want, "the heads' roles by place"
