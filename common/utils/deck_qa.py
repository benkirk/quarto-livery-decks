#!/usr/bin/env python3
"""Check built decks for layout defects: `make qa`, or `deck_qa.py <deck>...` in a deck dir.

Reads the already-built <deck>.{html,pdf,pptx} and writes to _qa/:
  report.txt        everything below, per deck (also printed)
  usage.tsv         per HTML slide: kind, body use, fit, layout classes
  names.txt         plain-text names from qa-names.txt (one per line), if the file exists
  <deck>-html.png   contact sheet of every HTML slide; <deck>-pdf.png and <deck>-pptx.png the same
                    for the PDF and the pptx (as LibreOffice draws it)
Failures (exit 1): slide counts that differ between formats, PDF text past the right margin,
into the footer band, overlapping other text or running into the next table column (the table's own
columns: the HTML says where the table is), HTML content past the right edge, a {.full}
caption or a ::: note paragraph that wraps in HTML (a gallery caption past its cell too), a grid
marker (`⟦engine:…⟧`) left in a pptx slide's text (an element the pptx steps did not draw), and a bare
`<word>` in the sources (revealjs reads it as a tag, and `<code>` swallows the slides after it).
Hints (never fail): short slides, `.smaller` without `.fill`, slides the HTML autofit shrank, and
the pptx as LibreOffice draws it (pptx_pdf.py) through the PDF's edge, footer and overlap checks
(QA_PPTX_FAIL=1 makes those failures; <deck>-pptx.png is its contact sheet).
Needs poppler (pdftoppm, pdftotext) and Pillow; the HTML checks need Playwright for Python
(`python -m playwright install chromium`, or set CHROME to a Chromium binary) and are skipped
without it, the pptx checks LibreOffice (soffice) and are skipped without it.
"""

import argparse
import functools
import glob
import html
import http.server
import os
import re
import shutil
import subprocess
import sys
import threading
import unicodedata
import zipfile

SHORT_USE = 0.65      # a text slide using less of its body than this is "short"
EDGE = WIDE_EDGE = None   # set in main() from the livery: 1 - margin, and 1 - geometry.wide-margin
                          # on a {.wide} slide (columns keep to the text width, onlytextwidth)
TOL = 1.5             # pt of slack before a PDF word counts as past an edge
STRIPS = []           # set in main(): the livery's marking strips' boxes, furniture the text checks skip
WATERMARK = ""        # set per deck in main(): the watermark's text (an HTML slide's), which the text checks skip
WM_HEIGHT = 0.0       # set in main(): the watermark's size, of the page's height (livery.json watermark)

MEASURE_JS = r"""
(i) => {
  const s = Reveal.getSlides()[i];
  const h = s.querySelector(':scope > h2');
  const wm = s.querySelector(':scope > .engine-watermark');   // its text: the PDF's word checks skip it
  const watermark = wm ? wm.textContent.trim() : null;
  if (!s.classList.contains('level2') || !h) return {level2: false, watermark};
  const cls = [...s.classList];
  // a gallery caption past its cell (one line, nowrap: its text overflows the box)
  const galleryCapOver = [...s.querySelectorAll('.engine-gallery-item figcaption')].some(
    c => c.scrollWidth > c.clientWidth + 1);
  if (s.classList.contains('full')) {
    // use: the drawn figure's share of its box (it keeps its shape, so one axis is full)
    const box = s.querySelector(':scope > .engine-full-figure');
    const cap = s.querySelector(':scope > .engine-full-caption');
    const fig = box && box.querySelector('svg:not(svg *), img');
    let use = 0;
    if (fig) {
      const r = fig.getBoundingClientRect(), b = box.getBoundingClientRect();
      const vb = fig.tagName.toLowerCase() === 'img'
        ? {width: fig.naturalWidth, height: fig.naturalHeight} : fig.viewBox && fig.viewBox.baseVal;
      const aw = vb && vb.width ? vb.width : r.width, ah = vb && vb.height ? vb.height : r.height;
      const k = Math.min(r.width / aw, r.height / ah);
      use = (aw * k) * (ah * k) / (b.width * b.height);
    }
    return {level2: true, title: h.textContent.trim(), cls: cls.join(' '), kind: 'full',
            use, fit: 1, scale: 1, overRight: false,
            capOver: !!cap && cap.scrollHeight > cap.clientHeight + 1, noFigure: !fig, galleryCapOver, watermark};
  }
  const sr = s.getBoundingClientRect(), cs = getComputedStyle(s);
  const shift = parseFloat(s.style.getPropertyValue('--engine-shift')) || 0;
  const fit = parseFloat(s.style.getPropertyValue('--engine-fit')) || 1;
  const scale = parseFloat(s.getAttribute('data-engine-scale')) || 1;
  // engine-revealjs.js's FURNITURE (tests/test_cli.py holds it a subset), and what the QA leaves out besides
  const skip = 'h2, .engine-waves, .engine-footnotes, .engine-signoff, .engine-marks, .engine-marking, .engine-watermark, .engine-feature-bar, .engine-title-photo-img, aside, style, script, .footer';
  const kids = [...s.children].filter(e => !e.matches(skip));
  let bot = 0, right = 0;
  for (const k of kids) for (const e of [k, ...k.querySelectorAll('*')]) {
    const r = e.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) {
      bot = Math.max(bot, r.bottom - sr.top); right = Math.max(right, r.right - sr.left);
    }
  }
  const foot = s.querySelector(':scope > .engine-footnotes');
  const floor = s.clientHeight - parseFloat(cs.paddingBottom);
  const limit = foot ? foot.getBoundingClientRect().top - sr.top : floor;
  const top = h.getBoundingClientRect().bottom - sr.top + 20;
  const has = sel => kids.some(k => k.matches(sel) || k.querySelector(sel));
  const kind = has('table') ? 'table' : has('pre') ? 'code'
    : has('img, svg, .cell-output-display') ? 'figure' : has('.columns') ? 'columns' : 'text';
  // the table's span across the slide (shares of the width): the PDF's column check reads only
  // the lines inside it, so bullets beside the table in a .columns slide are not its columns
  const tbl = kind === 'table' && s.querySelector('table');
  const tableBox = tbl ? [(tbl.getBoundingClientRect().left - sr.left) / sr.width,
                          (tbl.getBoundingClientRect().right - sr.left) / sr.width] : null;
  // a ::: note paragraph past one line (layout pixels: reveal's scaling leaves offsetHeight alone)
  const noteWrap = [...s.querySelectorAll('.engine-note p')].some(
    p => p.offsetHeight > 1.5 * parseFloat(getComputedStyle(p).lineHeight));
  return {level2: true, title: h.textContent.trim(), cls: cls.join(' '), kind,
          use: Math.max(0, (bot - shift - top) / (limit - top)), fit, scale,
          // the right edge: the padding, or on a {.wide} slide the wide margin the body widens to
          overRight: right > sr.width - (s.classList.contains('engine-wide')
            ? parseFloat(cs.getPropertyValue('--engine-wide-margin')) : parseFloat(cs.paddingRight)) + 16,  // inline-code padding overhangs
          noteWrap, galleryCapOver, tableBox, watermark};
}
"""


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def contact_sheet(pngs, out, cols=4, width=480, gap=6):
    from PIL import Image, ImageDraw
    if not pngs:
        return
    thumbs = []
    for p in pngs:
        im = Image.open(p).convert("RGB")
        thumbs.append(im.resize((width, round(im.height * width / im.width))))
    h = max(t.height for t in thumbs)
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (width + gap) + gap, rows * (h + gap) + gap), "#888888")
    draw = ImageDraw.Draw(sheet)
    for n, t in enumerate(thumbs):
        x, y = gap + (n % cols) * (width + gap), gap + (n // cols) * (h + gap)
        sheet.paste(t, (x, y))
        draw.rectangle((x, y, x + 26, y + 14), fill="#000000")
        draw.text((x + 3, y + 2), str(n + 1), fill="#FFFFFF")
    sheet.save(out)


# --------------------------------------------------------------------------- PDF

BOX = r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)"'
WORD = re.compile(r'<word %s>(.*?)</word>' % BOX)
LINE = re.compile(r'<line %s>(.*?)</line>' % BOX, re.S)
PAGE = re.compile(r'<page width="([\d.]+)" height="([\d.]+)">')


def boxes(pattern, text):
    return [(float(a), float(b), float(c), float(d), t) for a, b, c, d, t in pattern.findall(text)]


def pdf_pages(pdf):
    """[(width, height, words, lines)] per page, each a list of (x0, y0, x1, y1, text)."""
    xml = run(["pdftotext", "-bbox-layout", pdf, "-"])
    pages = []
    for chunk in xml.split("<page ")[1:]:
        w, h = map(float, PAGE.match("<page " + chunk).groups())
        words = [b[:4] + (html.unescape(b[4]),) for b in boxes(WORD, chunk)]
        lines = [b[:4] + (" ".join(wd[4] for wd in boxes(WORD, b[4])),) for b in boxes(LINE, chunk)]
        pages.append((w, h, words, lines))
    return pages


def frame_number(w, h, words):
    """The frame-number word in a bottom corner (geometry.pagenumber.corner), or None (title,
    section, closing pages): the lowest such number, since a plot's axis ticks can sit there too."""
    num = [wd for wd in words if wd[4].isdigit() and (wd[0] < w * 0.1 or wd[2] > w * 0.9) and wd[1] > h * 0.85]
    return max(num, key=lambda wd: wd[3]) if num else None


def frames(pages):
    """Each page's frame index: beamer overlays (incremental lists) repeat a frame's number."""
    idx, prev, out = -1, None, []
    for w, h, words, _ in pages:
        n = frame_number(w, h, words)
        num = n[4] if n else None
        if num is None or num != prev:
            idx += 1
        prev = num
        out.append(idx)
    return out


SPAN_PAD = 0.02   # of the width: the HTML table's span, widened before the PDF's lines are read against it
INDENT = 0.02     # of the width: an edge this close to the right of a cell's own start is an indented
                  # sub-row of its column (a hierarchy table's), not the next column


def table_overruns(lines, w, h, span=None):
    """Lines crossing a column edge, where an edge is an x that three or more lines start at.

    pdftotext keeps each table cell a line of its own, and merges two touching cells into one,
    so a cell that overruns its column is a line spanning the next column's edge. Only a cell
    counts: a line that starts at a column edge itself (a merged cell starts at its own column's),
    or sits within the rows of the column it crosses. A table's caption above it, or a note
    under it, is wider than its columns but neither, and an edge within INDENT of a cell's own
    start is its column's indented sub-rows (a hierarchy table's), not a column it crosses.
    `span` is the table's (left, right) as shares
    of the width, the HTML's measure of the same slide: only the lines reaching into it are read,
    so a bullet list beside the table (its hanging lines start at an x of their own) is no column."""
    body = [ln for ln in lines if ln[1] > h * 0.16]          # below the frame title
    if span:
        x0, x1 = (span[0] - SPAN_PAD) * w, (span[1] + SPAN_PAD) * w
        body = [ln for ln in body if ln[2] > x0 and ln[0] < x1]
    starts = {}
    for ln in body:
        starts.setdefault(round(ln[0]), []).append(ln)
    out = []
    for a in body:
        in_column = len(starts[round(a[0])]) >= 3
        for x, col in starts.items():
            # an edge within INDENT of the line's own start is an indented sub-row of its column
            if len(col) < 3 or not a[0] + max(5, INDENT * w) < x < a[2] - 1:
                continue
            mid = (a[1] + a[3]) / 2
            if not in_column and not min(b[1] for b in col) <= mid <= max(b[3] for b in col):
                continue
            near = [b for b in col if abs(b[1] - a[1]) < 3 * (a[3] - a[1])]
            # a right-aligned column: shorter numbers start further right, same right edge
            if near and not all(abs(b[2] - a[2]) < 1 for b in near):
                out.append(("runs into the next table column", repr(a[4])))
                break
    return out


def pdf_problems(w, h, words, lines, slide=None):
    """Text past the right margin, into the footer, overlapping, or across a table column.

    `slide` is the HTML measurement of the same slide, when the slide counts agree: it says
    whether the page is {.wide} (a wider right edge) or is a table (column checks); without it the
    wider edge, which any slide may have."""
    out = []
    # a marking strip's words are the livery's furniture (a full-width banner, a legend at the foot)
    words = [wd for wd in words if not any(x <= (wd[0] + wd[2]) / 2 / w <= x + bw and y <= (wd[1] + wd[3]) / 2 / h <= y + bh
                                           for x, y, bw, bh in STRIPS)]
    # the watermark's: furniture too, turned across the slide, which pdftotext gives as glyphs or pieces of
    # its text in boxes as tall as the turned letters (a body word that is one is a line's height)
    words = [wd for wd in words if not (WATERMARK and wd[4] in WATERMARK and wd[3] - wd[1] > 0.4 * WM_HEIGHT * h)]
    wide = slide is None or "engine-wide" in slide.get("cls", "").split()
    edge = w * (WIDE_EDGE if wide else EDGE) + TOL
    # the frame number (a bottom corner) marks the footline: furniture, which may sit past the
    # text's margin (the pptx's in the bottom right); small words beside it are the linked-image
    # URL line, which belongs there
    n = frame_number(w, h, words)
    for wd in words:
        if wd is not n and wd[2] > edge:
            out.append(("past the right margin", repr(wd[4])))
    if n:
        for wd in words:
            if wd is n or wd[3] <= n[1] + TOL or (wd[1] >= n[1] - 1 and wd[3] - wd[1] < 8.5):
                continue
            # meets the number (in either corner: within 6 pt of its box across), or below the footline
            if (wd[0] < n[2] + 6 and wd[2] > n[0] - 6) or wd[3] > n[3] + TOL:
                out.append(("into the footer", repr(wd[4])))
    # a math accent (the tilde of a typeset \tilde\rho) is a word of its own, set over its base
    solid = [wd for wd in words if not all(unicodedata.combining(c) for c in wd[4])]
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            vo = min(a[3], b[3]) - max(a[1], b[1])
            ho = min(a[2], b[2]) - max(a[0], b[0])
            ha, hb = a[3] - a[1], b[3] - b[1]
            # a sub- or superscript is its own word, tucked under its base's italic overhang:
            # much shorter than the base, and the overlap a sliver (TeX Gyre Heros showed it)
            if min(ha, hb) < 0.75 * max(ha, hb) and ho < 0.5 * min(a[2] - a[0], b[2] - b[0]):
                continue
            if ho > 1.0 and vo > 0.5 * min(ha, hb):
                out.append(("overlapping text", "%r/%r" % (a[4], b[4])))
    if slide and slide.get("kind") == "table":
        out += table_overruns(lines, w, h, slide.get("tableBox"))
    return out


def check_pdf(deck, qa, slides):
    pdf = deck + ".pdf"
    if not os.path.exists(pdf):
        return None, ["no %s; run make pdf" % pdf]
    pages = pdf_pages(pdf)
    index = frames(pages)
    nframes = index[-1] + 1 if index else 0
    lines = []
    for n, ((w, h, words, text_lines), f) in enumerate(zip(pages, index), 1):
        slide = slides[f] if len(slides) == nframes else None
        meta = slide if slide and slide.get("level2") else None
        found = {}
        for kind, detail in pdf_problems(w, h, words, text_lines, meta):
            found.setdefault(kind, []).append(detail)
        for kind, details in found.items():
            more = " (+%d more)" % (len(details) - 3) if len(details) > 3 else ""
            lines.append("p%d [s%d]: %s: %s%s" % (n, f + 1, kind, ", ".join(details[:3]), more))
    if shutil.which("pdftoppm"):
        d = os.path.join(qa, deck, "pdf")
        os.makedirs(d, exist_ok=True)
        for old in glob.glob(os.path.join(d, "*.png")):
            os.remove(old)
        run(["pdftoppm", "-r", "80", "-png", pdf, os.path.join(d, "p")])
        contact_sheet(sorted(glob.glob(os.path.join(d, "*.png"))),
                      os.path.join(qa, deck + "-pdf.png"))
    return nframes, lines


# -------------------------------------------------------------------------- HTML

def serve(directory):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    handler = functools.partial(Quiet, directory=directory)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def check_html(decks, qa):
    """{deck: (count, [slide dicts])}, or a string saying why the HTML checks were skipped."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "Playwright for Python is not installed"
    httpd = serve(os.getcwd())
    base = "http://127.0.0.1:%d/" % httpd.server_address[1]
    results = {}
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(executable_path=os.environ.get("CHROME") or None)
            except Exception as e:  # noqa: BLE001 -- any launch failure means "skip"
                return "no browser (%s); run `python -m playwright install chromium` or set " \
                       "CHROME" % str(e).splitlines()[0]
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            for deck in decks:
                if not os.path.exists(deck + ".html"):
                    continue
                d = os.path.join(qa, deck, "html")
                os.makedirs(d, exist_ok=True)
                for old in glob.glob(os.path.join(d, "*.png")):
                    os.remove(old)
                page.goto(base + deck + ".html")
                page.wait_for_function("window.Reveal && Reveal.isReady()")
                # mermaid draws after reveal is ready; measuring a {.full} diagram before it
                # has finished reads an empty figure (seen on a busy machine)
                try:
                    page.wait_for_function("document.querySelectorAll('pre.mermaid-js').length === 0", timeout=20000)
                except Exception:
                    print("deck_qa: mermaid still rendering after 20 s; measuring anyway", file=sys.stderr)
                page.evaluate("document.fonts.ready.then(() => true)")
                page.evaluate("Reveal.configure({transition: 'none', backgroundTransition: 'none'})")
                n = page.evaluate("Reveal.getTotalSlides()")
                slides = []
                for i in range(n):
                    # `##` slides nest under their `#` divider: Reveal.slide(i) would stay on it
                    page.evaluate("i => { const ix = Reveal.getIndices(Reveal.getSlides()[i]);"
                                  " Reveal.slide(ix.h, ix.v); }", i)
                    page.wait_for_timeout(400)
                    page.screenshot(path=os.path.join(d, "s%03d.png" % (i + 1)))
                    slides.append(page.evaluate(MEASURE_JS, i))
                contact_sheet(sorted(glob.glob(os.path.join(d, "*.png"))),
                              os.path.join(qa, deck + "-html.png"))
                results[deck] = (n, slides)
            browser.close()
    finally:
        httpd.shutdown()
    return results


def html_findings(slides):
    fails, hints = [], []
    for n, s in enumerate(slides, 1):
        if not s.get("level2"):
            continue
        cls = s["cls"].split()
        tag = 's%d "%s"' % (n, s["title"])
        if s["overRight"]:
            fails.append("%s: content past the right edge" % tag)
        if s.get("capOver"):
            fails.append("%s: the {.full} caption runs past its line; shorten it" % tag)
        if s.get("noteWrap"):
            fails.append("%s: a ::: note paragraph wraps; shorten it, or split it into "
                         "paragraphs (each a caption line)" % tag)
        if s.get("galleryCapOver"):
            fails.append("%s: a gallery caption runs past its cell; shorten it" % tag)
        if s.get("noFigure"):
            fails.append("%s: {.full} slide without a drawn figure" % tag)
        # (Quarto marks the references slide .smaller itself; the theme sets that list's size)
        if "smaller" in cls and "engine-fill" not in cls and "engine-references" not in cls:
            hints.append("%s: .smaller without .fill shrinks the HTML text; drop it, or add "
                         ".fill with a PDF scale=" % tag)
        floor = 1.0 if "engine-fill" in cls else s["scale"]
        if s["fit"] < floor - 0.05:
            hints.append("%s: HTML autofit shrank it to %.2f; the PDF (no autofit) may "
                         "overflow" % (tag, s["fit"]))
        special = {"engine-layout", "feature", "closing", "engine-dark"}
        if s["kind"] in ("text", "columns") and s["use"] <= SHORT_USE and not special & set(cls):
            hints.append('%s: short (%s, uses %.0f%% of the body); try {.vcenter scale="1.15"}'
                         % (tag, s["kind"], 100 * s["use"]))
    return fails, hints


# ------------------------------------------------------------------- pptx, names

def check_pptx(deck, qa, slides, livery):
    """The pptx as LibreOffice draws it (pptx_pdf.to_pdf), through the PDF checks but the table
    rule (python-pptx's tables are not longtable's): text past the right margin, into the footer,
    overlapping; a contact sheet <deck>-pptx.png. Hints, since LibreOffice applies no autofit and
    substitutes the faces it lacks (a box it overflows PowerPoint may shrink); QA_PPTX_FAIL=1 makes
    them failures. (lines, skipped-reason)."""
    import pptx_pdf
    path = deck + ".pptx"
    if not os.path.exists(path):
        return [], None
    d = os.path.join(qa, deck, "pptx")
    os.makedirs(d, exist_ok=True)
    for old in glob.glob(os.path.join(d, "*")):
        os.remove(old)
    pdf, why = pptx_pdf.to_pdf(path, livery, d)
    if pdf is None:
        return [], why
    lines = []
    for n, (w, h, words, text_lines) in enumerate(pdf_pages(pdf), 1):   # a slide a page: no overlays
        slide = slides[n - 1] if n <= len(slides) else None
        meta = {**slide, "kind": "pptx"} if slide and slide.get("level2") else None
        found = {}
        for kind, detail in pdf_problems(w, h, words, text_lines, meta):
            found.setdefault(kind, []).append(detail)
        for kind, details in found.items():
            more = " (+%d more)" % (len(details) - 3) if len(details) > 3 else ""
            lines.append("s%d: %s: %s%s" % (n, kind, ", ".join(details[:3]), more))
    if shutil.which("pdftoppm"):
        run(["pdftoppm", "-r", "80", "-png", pdf, os.path.join(d, "p")])
        contact_sheet(sorted(glob.glob(os.path.join(d, "*.png"))), os.path.join(qa, deck + "-pptx.png"))
    return lines, None


MARKER = "⟦engine:"   # grid-pptx.lua's markers, which the pptx steps draw and delete


def pptx_scan(deck):
    """(the pptx's slide count, the slides still holding a grid marker), (None, []) without the
    file. A marker left in a slide's text is an element the steps did not draw (a lead folded
    into a figure's caption once reached PowerPoint as its literal text, #133): the steps warn,
    and this makes it a failure."""
    path = deck + ".pptx"
    if not os.path.exists(path):
        return None, []
    count, left = 0, []
    with zipfile.ZipFile(path) as z:
        for f in z.namelist():
            m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", f)
            if not m:
                continue
            count += 1
            if MARKER in z.read(f).decode("utf-8"):
                left.append(int(m.group(1)))
    return count, sorted(left)


def plain_names(names):
    """file:line hits of each listed name outside code, notes, link targets and attributes."""
    pat = re.compile(r"(?<![\w/.`-])(%s)(?![\w`-])" % "|".join(map(re.escape, names)))
    hits = []
    for f in sorted(glob.glob("*.qmd")):
        fence = notes = False
        for n, line in enumerate(open(f, encoding="utf-8"), 1):
            s = line.strip()
            if s.startswith("```"):
                fence = not fence
                continue
            if s.startswith("::: {.notes"):
                notes = True
            if fence or notes:
                notes = notes and s != ":::"
                continue
            prose = re.sub(r"`[^`]*`|\]\([^)]*\)|\{[^}]*\}|https?://\S+", "", line)
            hits += ["%s:%d: %s" % (f, n, m.group(1)) for m in pat.finditer(prose)]
    return hits


# ------------------------------------------------------------------- sources

INCLUDE = re.compile(r"\{\{<\s*include\s+(\S+)\s*>\}\}")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
CODE_SPAN = re.compile(r"(`+).+?\1")
BARE_TAG = re.compile(r"</?[a-z_]+>")


def deck_sources(deck):
    """<deck>.qmd and every file it includes, recursively, in reading order."""
    seen, order = set(), []

    def visit(path):
        if path in seen or not os.path.exists(path):
            return
        seen.add(path)
        order.append(path)
        for line in open(path, encoding="utf-8"):
            for inc in INCLUDE.findall(line):
                visit(os.path.normpath(os.path.join(os.path.dirname(path), inc)))
    visit(deck + ".qmd")
    return order


def bare_tags(path):
    """file:line hits of `<word>` outside code fences, code spans and raw-HTML lines."""
    hits, fence, front = [], None, False
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if n == 1 and line.strip() == "---":
            front = True
            continue
        if front:
            front = line.strip() not in ("---", "...")
            continue
        m = FENCE.match(line)
        if m and (fence is None or m.group(1).startswith(fence)):
            fence = m.group(1) if fence is None else None
            continue
        if fence or line.lstrip().startswith("<"):
            continue
        for tag in BARE_TAG.findall(CODE_SPAN.sub("", line)):
            hits.append("%s:%d: bare %s; put it in backticks" % (path, n, tag))
    return hits


# -------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("decks", nargs="+")
    ap.add_argument("--out", default="_qa")
    args = ap.parse_args()
    qa = args.out
    os.makedirs(qa, exist_ok=True)
    global EDGE, WIDE_EDGE, STRIPS, WATERMARK, WM_HEIGHT
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "_extensions", "engine"))
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))   # pptx_pdf
    import livery as livery_mod   # the engine's; here, not at import: screenshots.py imports serve() alone
    livery = livery_mod.load()
    geom = livery["geometry"]
    EDGE, WIDE_EDGE = 1 - geom["margin"], 1 - geom["wide-margin"]
    STRIPS = [s["box"] for s in livery.get("marking") or []]
    WM_HEIGHT = livery["watermark"]["size"] / livery["type"]["canvas"]["h"]
    pptx_fail = os.environ.get("QA_PPTX_FAIL") == "1"

    html_res = check_html(args.decks, qa)
    report, usage, failed = [], ["deck\tslide\tkind\tuse\tfit\ttitle\tclasses"], False
    if isinstance(html_res, str):
        report.append("HTML checks skipped: " + html_res)
        html_res = {}
    for deck in args.decks:
        report.append("== %s ==" % deck)
        # an included .yml or .py is shown inside a code fence, not read as markdown
        tags = [h for f in deck_sources(deck) if f.endswith((".qmd", ".md"))
                for h in bare_tags(f)]
        failed |= bool(tags)
        report += ["source " + h for h in tags]
        html_n, slides = html_res.get(deck, (None, []))
        WATERMARK = next((s["watermark"] for s in slides if s.get("watermark")), "")
        pdf_n, pdf_lines = check_pdf(deck, qa, slides)
        pptx_n, markers = pptx_scan(deck)
        counts = {"pptx": pptx_n, "pdf": pdf_n, "html": html_n}
        known = {k: v for k, v in counts.items() if v is not None}
        same = len(set(known.values())) <= 1
        failed |= not same
        report.append("slides: %s%s" % (", ".join("%s %d" % kv for kv in known.items()),
                                        "" if same else "  MISMATCH"))
        titles = {n: s.get("title", "") for n, s in enumerate(slides, 1)} if same else {}
        for line in pdf_lines:
            m = re.match(r"p\d+ \[s(\d+)\]", line)
            title = titles.get(int(m.group(1))) if m else None
            report.append("PDF %s%s" % (line, ' ("%s")' % title if title else ""))
        failed |= any(line.startswith("p") for line in pdf_lines)
        for n in markers:
            report.append("pptx s%d: a grid marker left in the text (an element the steps did not draw; "
                          "see their warnings)%s" % (n, ' ("%s")' % titles[n] if titles.get(n) else ""))
        failed |= bool(markers)
        pptx_lines, why = check_pptx(deck, qa, slides if same else [], livery)
        if why:
            report.append("pptx checks skipped: " + why)
        for line in pptx_lines:
            m = re.match(r"s(\d+)", line)
            title = titles.get(int(m.group(1))) if m else None
            report.append("%s pptx %s%s" % ("pptx" if pptx_fail else "hint", line, ' ("%s")' % title if title else ""))
        failed |= pptx_fail and bool(pptx_lines)
        fails, hints = html_findings(slides)
        failed |= bool(fails)
        report += ["HTML " + f for f in fails] + ["hint " + h for h in hints]
        for n, s in enumerate(slides, 1):
            if s.get("level2"):
                usage.append("%s\t%d\t%s\t%.2f\t%.2f\t%s\t%s"
                             % (deck, n, s["kind"], s["use"], s["fit"], s["title"], s["cls"]))
    if os.path.exists("qa-names.txt"):
        names = [n.strip() for n in open("qa-names.txt", encoding="utf-8")
                 if n.strip() and not n.lstrip().startswith("#")]
        hits = plain_names(names) if names else []
        with open(os.path.join(qa, "names.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(hits) + "\n")
        report.append("== names ==\n%d plain-text uses of qa-names.txt names (see %s/names.txt)"
                      % (len(hits), qa))
    with open(os.path.join(qa, "usage.tsv"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(usage) + "\n")
    with open(os.path.join(qa, "report.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report))
    print("\n%s; contact sheets and per-slide PNGs in %s/" % ("FAILED" if failed else "ok", qa))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
