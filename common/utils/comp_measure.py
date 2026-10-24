#!/usr/bin/env python3
"""Measure each format's title, divider, closing and feature slides against the livery's compositions.

    comp_measure.py [--fail-on html,pdf,pptx] <deck>...   (`make measure` in a deck directory)

Shoots the four slides of each built deck at 1600x900 (HTML: Playwright; PDF: pdftoppm; pptx:
soffice to PDF through pptx_pdf.py, skipped without it), picks the composition the formats pick (band, photo, light
from the front matter and the livery) and measures its boxes: filled edges (band, bar, panel, a
straight field edge) by the strongest color step near them; marks and sign-offs by the bbox of
non-field pixels in the box grown by 0.03; the text column by the bbox of its role's pixels down
the slide (left vs x, top or center by anchor, right within x + w). Writes _qa/measure.tsv,
_qa/compositions-<livery>.png (rows compositions, columns HTML | PDF | pptx, boxes in magenta)
and a table; exits 1 when a --fail-on format is over tolerance.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "_extensions", "engine"))
import livery as livery_mod  # noqa: E402  (the engine's reader)
import pptx_pdf  # noqa: E402
from deck_qa import deck_sources, serve  # noqa: E402

W, H = 1600, 900
GROW = 0.03                  # an image or text box is searched in its box grown by this
TOL, TOL_MIDDLE, TOL_EDGE = 0.02, 0.03, 0.005   # 0.03: pptx's middle-anchored stacks
FORMATS = ("html", "pdf", "pptx")
KINDS = ("title", "section", "closing", "feature")


# ------------------------------------------------------------------ the deck

def front_matter(deck):
    import yaml
    text = open(deck + ".qmd", encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    return (yaml.safe_load(m.group(1)) if m else None) or {}


def headings(deck):
    """The first divider's, closing slide's and feature slide's titles, from the sources."""
    found, fence = {}, False
    for path in deck_sources(deck):
        for line in open(path, encoding="utf-8"):
            if line.lstrip().startswith(("```", "~~~")):
                fence = not fence
            if fence:
                continue
            m = re.match(r"^(#{1,2}) (.+?)\s*(\{[^}]*\})?\s*$", line)
            if not m:
                continue
            text, attrs = m.group(2).strip(), m.group(3) or ""
            if m.group(1) == "#":
                found.setdefault("section", text)
            elif ".closing" in attrs:
                found.setdefault("closing", text)
            elif ".feature" in attrs:
                found.setdefault("feature", text)
    return found


def composition_names(fm, L):
    """kind -> composition, as the drawers pick: a band wins over light; a photo is the deck's
    titlegraphic or the livery's art.titlegraphic (unless titlegraphic: none)."""
    opts = fm.get("themeoptions") or []
    opts = opts if isinstance(opts, list) else str(opts).split(",")
    light = any(str(o).strip() == "title=light" for o in opts)
    band = (L.get("title") or {}).get("style") == "band"
    tg = fm.get("titlegraphic")   # `titlegraphic: none` asks for the plain cover over the livery's default
    photo = (bool(tg) and tg != "none") or (not tg and isinstance((L.get("art") or {}).get("titlegraphic"), str))
    title = "title-band" if band else ("title-photo" if photo else "title") + ("-light" if light else "")
    closing = "closing-band" if band else "closing-light" if light else "closing"
    return {"title": title, "section": "section", "closing": closing, "feature": "feature"}


# ------------------------------------------------------------------ shooting

def shoot_html(deck, titles, out):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "Playwright for Python is not installed"
    httpd = serve(os.getcwd())
    shots = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get("CHROME") or None)
            page = browser.new_page(viewport={"width": W, "height": H})
            page.goto("http://127.0.0.1:%d/%s.html" % (httpd.server_address[1], deck))
            page.wait_for_function("window.Reveal && Reveal.isReady()")
            page.evaluate("document.fonts.ready.then(() => true)")
            page.evaluate("Reveal.configure({transition: 'none', backgroundTransition: 'none'})")
            sel = {"title": "section.engine-title", "section": "section.engine-section",
                   "closing": "section.closing", "feature": "section.feature"}
            for kind, css in sel.items():
                i = page.evaluate("css => Reveal.getSlides().findIndex(s => s.matches(css))", css)
                if i < 0:
                    continue
                page.evaluate("i => { const ix = Reveal.getIndices(Reveal.getSlides()[i]); Reveal.slide(ix.h, ix.v); }", i)
                page.wait_for_timeout(500)
                shots[kind] = os.path.join(out, f"{deck}-html-{kind}.png")
                page.screenshot(path=shots[kind])
            browser.close()
    finally:
        httpd.shutdown()
    return shots


def page_texts(pdf):
    text = subprocess.run(["pdftotext", "-layout", pdf, "-"], check=True, capture_output=True, text=True).stdout
    return [" ".join(p.split()) for p in text.split("\f")]


def shoot_pdf(pdf, titles, out, tag):
    """The title page and the first page holding each other kind's title."""
    pages, shots = page_texts(pdf), {}
    want = {"title": 1}
    for kind in ("section", "closing", "feature"):
        t = " ".join(titles.get(kind, "\0").split())
        # after the title page: a part deck's subtitle is often its first divider's title
        want[kind] = next((n for n, p in enumerate(pages[1:], 2) if t in p), None)
    for kind, n in want.items():
        if n:
            stem = os.path.join(out, f"{tag}-{kind}")
            subprocess.run(["pdftoppm", "-f", str(n), "-l", str(n), "-singlefile", "-scale-to-x", str(W),
                            "-scale-to-y", str(H), "-png", pdf, stem], check=True)
            shots[kind] = stem + ".png"
    return shots


def shoot_pptx(deck, titles, out, L):
    """The pptx as LibreOffice draws it (pptx_pdf.to_pdf: the livery's faces, a private
    profile), shot like the PDF; the reason, when soffice is not installed."""
    with tempfile.TemporaryDirectory() as tmp:
        pdf, why = pptx_pdf.to_pdf(deck + ".pptx", L, tmp)
        if pdf is None:
            return why
        return shoot_pdf(pdf, titles, out, f"{deck}-pptx")


# ------------------------------------------------------------------ measuring

def px(box):
    x, y, w, h = box
    return round(x * W), round(y * H), round((x + w) * W), round((y + h) * H)


def grown(box, g=GROW):
    x, y, w, h = box
    x0, y0 = max(0, x - g), max(0, y - g)
    return [x0, y0, min(1, x + w + g) - x0, min(1, y + h + g) - y0]


def flat(im):
    return list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())   # Pillow 12 renames it


def profile(im, box, axis):
    """Mean color per pixel along `axis` ('x' or 'y') of the box's region."""
    from PIL import Image
    r = im.crop(px(box))
    r = r.resize((r.width, 1) if axis == "x" else (1, r.height), Image.BOX)
    return flat(r)


def edge(im, pos, axis, lo, hi):
    """The strongest color step within 0.05 of `pos` (a fraction along `axis`), the step
    averaged over [lo, hi] of the other axis; None when there is no clear step."""
    a, b = max(0.0, pos - 0.05), min(1.0, pos + 0.05)
    box = [a, lo, b - a, hi - lo] if axis == "x" else [lo, a, hi - lo, b - a]
    prof = profile(im, box, axis)
    steps = [sum(abs(p - q) for p, q in zip(prof[i - 1], prof[i + 1])) for i in range(1, len(prof) - 1)]
    if not steps or max(steps) < 24:
        return None
    i = max(range(len(steps)), key=steps.__getitem__) + 1
    return a + i / (W if axis == "x" else H)


def mask_of(im, box, rgb, near, cut=(), dist=60):
    """A 0/255 mask of the box's pixels within (near=True) or beyond `dist` of rgb, cut boxes zeroed."""
    from PIL import Image, ImageChops, ImageDraw
    r = im.crop(px(box))
    d = ImageChops.difference(r, Image.new("RGB", r.size, rgb))
    ch = d.split()
    m = ImageChops.lighter(ImageChops.lighter(ch[0], ch[1]), ch[2])
    m = m.point(lambda v: 255 if (v < dist) == near else 0)
    draw = ImageDraw.Draw(m)
    ox, oy = px(box)[:2]
    for c in cut:
        x0, y0, x1, y1 = px(grown(c, 0.005))
        draw.rectangle((x0 - ox, y0 - oy, x1 - ox, y1 - oy), fill=0)
    return m


def bbox(mask, box, minimum):
    """The box (fractions) of the rows and columns holding at least `minimum` mask pixels."""
    from PIL import Image
    rows = flat(mask.resize((1, mask.height), Image.BOX))
    cols = flat(mask.resize((mask.width, 1), Image.BOX))
    ys = [i for i, v in enumerate(rows) if v * mask.width / 255 >= minimum]
    xs = [i for i, v in enumerate(cols) if v * mask.height / 255 >= minimum]
    if not xs or not ys:
        return None
    x0, y0 = px(box)[:2]
    return [(x0 + xs[0]) / W, (y0 + ys[0]) / H, (x0 + xs[-1] + 1) / W, (y0 + ys[-1] + 1) / H]


def widened(mask, box, core, minimum, gap=0.006):
    """core (a bbox() of an eroded mask) widened left and right through the un-eroded mask's
    columns, within the core's rows, holding at least `minimum` pixels, across gaps of up to
    `gap` of the width (the space between words): a stray art line crossing those rows puts one
    or two pixels in a column, a stroke of type its height."""
    from PIL import Image
    x0, y0 = px(box)[:2]
    rows = mask.crop((0, round(core[1] * H) - y0, mask.width, round(core[3] * H) - y0))
    cols = flat(rows.resize((rows.width, 1), Image.BOX))
    ink = [v * rows.height / 255 >= minimum for v in cols]
    lo, hi = round(core[0] * W) - x0, round(core[2] * W) - x0 - 1
    step = max(1, round(gap * W))
    for d in (-1, 1):
        i = lo if d < 0 else hi
        while True:
            nxt = next((j for j in range(i + d, i + d * (step + 1), d) if 0 <= j < len(ink) and ink[j]), None)
            if nxt is None:
                break
            i = nxt
        lo, hi = (i, hi) if d < 0 else (lo, i)
    return [(x0 + lo) / W, core[1], (x0 + hi + 1) / W, core[3]]


def ring_color(im, box):
    """The median color of the box's 4 px border: what an image in it sits on."""
    x0, y0, x1, y1 = px(box)
    pts = [im.getpixel((x, y)) for x in range(x0, x1, 3) for y in (y0, y0 + 3, y1 - 4, y1 - 1)]
    pts += [im.getpixel((x, y)) for y in range(y0, y1, 3) for x in (x0, x0 + 3, x1 - 4, x1 - 1)]
    return tuple(sorted(p[i] for p in pts)[len(pts) // 2] for i in range(3))


def rgb(hexv):
    return tuple(bytes.fromhex(hexv.lstrip("#")))


def measure(im, comp, L, fmt):
    """[(box, edge, expected, measured, tolerance)] for one shot."""
    from PIL import ImageChops, ImageFilter
    out, roles = [], L["roles"]

    def add(key, name, want, got, tol):
        out.append((key, name, round(want, 4), None if got is None else round(got, 4), tol))

    for key, sides in (("band", "tb"), ("bar", "b"), ("panel", "ltr")):
        c = comp[key]
        if not c:
            continue
        x, y, w, h = c["box"]
        for s in sides:   # a side is read in the box's top padding: the panel's text starts below it
            if s in "lr":
                add(key, "left" if s == "l" else "right", x if s == "l" else x + w,
                    edge(im, x if s == "l" else x + w, "x", y + 0.004, y + 0.014), TOL_EDGE)
            else:
                add(key, "top" if s == "t" else "bottom", y if s == "t" else y + h,
                    edge(im, y if s == "t" else y + h, "y", x + 0.45 * w, x + 0.55 * w), TOL_EDGE)
    if comp["band"] and comp["photo"]:   # the photo's edge on the band
        x, y, w, h = comp["photo"]["box"]
        add("photo", "left", x, edge(im, x, "x", y + 0.4 * h, y + 0.6 * h), TOL_EDGE)
    f = comp["field"]
    if f and f["box"][2] < 1 and not comp["waves"]:   # a straight field edge beside a photo
        add("field", "right", f["box"][2], edge(im, f["box"][2], "x", 0.70, 0.80), TOL_EDGE)
    for key in ("mark", "signoff"):
        c = comp[key]
        if not c:
            continue
        g = grown(c["box"])   # a mark contrasts with its field more than art's lines and stars do
        mask = mask_of(im, g, ring_color(im, g), near=False, dist=110)
        least = max(3, 0.03 * c["box"][3] * H)
        if comp["art"]:   # a picture under the field: drop its 1-2 px lines (a lockup's strokes are wider)
            raw, mask = mask, mask.filter(ImageFilter.MinFilter(3))
            b = bbox(mask, g, least)
            if b:   # the erosion took thin type too ("Office"): widen the core along its own rows
                b = widened(raw, g, b, least)
        else:
            b = bbox(mask, g, least)
        x, y, w, h = c["box"]
        for i, (name, want) in enumerate((("left", x), ("top", y), ("right", x + w), ("bottom", y + h))):
            add(key, name, want, b and b[i], TOL)
    col = comp["column"]
    x, y, w, h = col["box"]
    g = grown(col["box"])   # across, the grown box; down, the slide above the footer (a stack may be far off)
    g = [g[0], 0, g[2], 0.93]
    for k in ("band", "bar"):   # the text sits on it: the field beyond it may be the text's color
        if comp[k]:
            by, bh = comp[k]["box"][1], comp[k]["box"][3]
            g = [g[0], by, g[2], bh]
    # not the column's pixels: the marks grown (a format may draw them off their box), the rest as they are
    cut = [grown(comp[k]["box"]) for k in ("mark", "signoff") if comp[k]]
    cut += [comp[k]["box"] for k in ("fineprint", "panel") if comp[k]]
    by = comp.get("byline")
    if by and by["box"]:   # a cover's byline in a box of its own: its ink is not the column's
        cut.append(grown(by["box"]))
    f = comp["field"]
    if f and f["box"][2] < 1:   # beyond a field narrower than the slide: the photo, whose darks may be the text's color
        cut.append([f["box"][0] + f["box"][2], 0, 1 - f["box"][0] - f["box"][2], 1])
    mask = mask_of(im, g, rgb(roles[col["role"]]), near=True, cut=cut)
    if comp["eyebrow"]:   # the divider's stack starts with its eyebrow, in a color of its own
        mask = ImageChops.lighter(mask, mask_of(im, g, rgb(comp["eyebrow"]["color"]), near=True, cut=cut))   # a hex (livery_build)
    b = bbox(mask, g, 2)
    if col.get("align") == "center":   # column.align: the ink centered across the box, not at its left
        add("column", "center-x", x + w / 2, b and (b[0] + b[2]) / 2, TOL)
    else:
        add("column", "left", x, b and b[0], TOL)
    middle = col["anchor"] == "middle"
    tol = TOL_MIDDLE if middle and fmt == "pptx" else TOL
    if middle:
        add("column", "center", y + h / 2, b and (b[1] + b[3]) / 2, tol)
    else:
        add("column", "top", y, b and b[1], tol)
    add("column", "right<=", x + w, b and b[2], TOL)   # text may end short of the box, not past it
    if by and by["box"]:   # the byline's stack in its box, by its own anchor and alignment
        bx, byy, bw, bh = by["box"]
        gb = grown(by["box"])
        b = bbox(mask_of(im, gb, rgb(roles[by["role"]]), near=True,
                         cut=[grown(comp[k]["box"]) for k in ("mark", "signoff") if comp[k]]), gb, 2)
        if by["align"] == "center":
            add("byline", "center-x", bx + bw / 2, b and (b[0] + b[2]) / 2, TOL)
        else:
            add("byline", "left", bx, b and b[0], TOL)
        if by["anchor"] == "middle":
            add("byline", "center", byy + bh / 2, b and (b[1] + b[3]) / 2, TOL_MIDDLE if fmt == "pptx" else TOL)
        else:
            add("byline", "top", byy, b and b[1], TOL)
    return out


# ------------------------------------------------------------------ the sheet

def overlay(path, comp):
    from PIL import Image, ImageDraw
    im = Image.open(path).convert("RGB").resize((W, H))
    d = ImageDraw.Draw(im)
    for key in ("field", "photo", "band", "bar", "panel", "mark", "signoff", "column", "byline", "fineprint"):
        c = comp.get(key)
        if c and not c.get("box"):   # a box-less byline
            continue
        nominal = key == "field" and comp["waves"]   # with waves the field's edge is line 2, not its box
        if c and not nominal and c["box"] != [0, 0, 1, 1] and c["box"][2] > 0 and c["box"][3] > 0:   # not an empty box
            x0, y0, x1, y1 = px(c["box"])
            d.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(255, 0, 255), width=3)
            d.text((x0 + 5, y0 + 4), key, fill=(255, 0, 255))
    return im


def sheet(rows, out, width=480, label=150):
    from PIL import Image, ImageDraw
    h = round(width * H / W)
    im = Image.new("RGB", (label + 3 * (width + 6) + 6, 24 + len(rows) * (h + 6) + 6), "#777777")
    d = ImageDraw.Draw(im)
    for j, fmt in enumerate(FORMATS):
        d.text((label + 6 + j * (width + 6) + 4, 6), fmt.upper(), fill="white")
    for i, (name, shots) in enumerate(rows):
        y = 24 + i * (h + 6)
        d.text((6, y + 4), name.replace(": ", ":\n"), fill="white")
        for j, fmt in enumerate(FORMATS):
            if fmt in shots:
                im.paste(shots[fmt].resize((width, h), Image.LANCZOS), (label + 6 + j * (width + 6), y))
    im.save(out)


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("decks", nargs="+")
    ap.add_argument("--fail-on", default="html,pdf,pptx", help="formats whose deltas fail (comma list; empty: none)")
    a = ap.parse_args()
    fail_on = {f for f in a.fail_on.split(",") if f}
    L = livery_mod.load()
    comps = L["compositions"]
    os.makedirs("_qa/compositions", exist_ok=True)
    tsv, rows, shown, bad, notes = [], [], set(), 0, []
    for deck in a.decks:
        titles, names = headings(deck), composition_names(front_matter(deck), L)
        out = "_qa/compositions"
        shots = {}
        for fmt, path in (("html", deck + ".html"), ("pdf", deck + ".pdf"), ("pptx", deck + ".pptx")):
            if not os.path.exists(path):
                notes.append(f"{deck}: no {path}"); continue
            got = (shoot_html(deck, titles, out) if fmt == "html" else
                   shoot_pdf(path, titles, out, f"{deck}-pdf") if fmt == "pdf" else shoot_pptx(deck, titles, out, L))
            if isinstance(got, str):
                notes.append(f"{deck}: {fmt} skipped: {got}"); continue
            shots[fmt] = got
        from PIL import Image
        for kind in KINDS:
            name = names[kind]
            row = {}
            for fmt, got in shots.items():
                if kind not in got:
                    notes.append(f"{deck}: {fmt} has no {kind} slide"); continue
                im = Image.open(got[kind]).convert("RGB").resize((W, H))
                for key, edge_name, want, have, tol in measure(im, comps[name], L, fmt):
                    delta = None if have is None else round(have - want, 4)
                    ok = delta is not None and (delta <= tol if edge_name == "right<=" else abs(delta) <= tol)
                    tsv.append((L["name"], deck, fmt, name, key, edge_name, want, have, delta, "ok" if ok else "OVER"))
                    bad += (not ok) and fmt in fail_on
                row[fmt] = overlay(got[kind], comps[name])
            if name not in shown and row:
                shown.add(name)
                rows.append((f"{deck}: {name}", row))
    with open("_qa/measure.tsv", "w") as f:
        f.write("livery\tdeck\tformat\tcomposition\tbox\tedge\texpected\tmeasured\tdelta\tresult\n")
        for r in tsv:
            f.write("\t".join("" if v is None else str(v) for v in r) + "\n")
    sheet(rows, f"_qa/compositions-{L['name']}.png")
    print(f"{'deck':12} {'fmt':4} {'composition':18} {'box':9} {'edge':7} {'want':>7} {'got':>7} {'delta':>7}   (over tolerance)")
    for r in (r for r in tsv if r[9] != "ok"):
        print(f"{r[1]:12} {r[2]:4} {r[3]:18} {r[4]:9} {r[5]:7} {r[6]:7.4f} {'-' if r[7] is None else '%7.4f' % r[7]:>7} "
              f"{'-' if r[8] is None else '%+7.4f' % r[8]:>7} {'' if r[9] == 'ok' else r[9]}")
    for n in notes:
        print("note:", n)
    counts = ", ".join(f"{f} {sum(r[9] != 'ok' for r in tsv if r[2] == f)}/{sum(r[2] == f for r in tsv)}"
                       for f in FORMATS if any(r[2] == f for r in tsv))
    print(f"measure ({L['name']}): edges over tolerance: {counts}; _qa/measure.tsv, _qa/compositions-{L['name']}.png")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
