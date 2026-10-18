#!/usr/bin/env python3
"""The plots README's images: `make gallery` in decks/plots/ writes, in screenshots/:

  liveries.png  four HTML slides of this deck per livery in LIVERIES (built with `make html
                LIVERY=<name>`): the lines, the hue families, the heatmap and the dark slide
  palettes.png  each livery's chart colors from its build/livery.json: the categorical slots, the
                default color map and the diverging scale, on its light and its dark surface

Needs Playwright (CHROME for another Chromium) and Pillow, as `make qa` does. Leaves the
directory built under the first livery (the default)."""

import json
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common", "utils"))
from deck_qa import serve  # noqa: E402

DECK, OUT = "plots", "screenshots"
LIVERIES = ["ncar", "ucar", "cu", "nsi", "nasa", "nasa-dark"]
COLUMNS = ["Lines take the categorical slots", "A stacked area in hue families",
           "A heatmap on the sequential map", "On a dark slide"]
LIVERIES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "liveries")


def shots(tmp):
    """The COLUMNS slides of the built HTML deck, as PNG paths in that order."""
    from playwright.sync_api import sync_playwright
    httpd = serve(os.getcwd())
    found = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get("CHROME") or None)
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            page.goto("http://127.0.0.1:%d/%s.html" % (httpd.server_address[1], DECK))
            page.wait_for_function("window.Reveal && Reveal.isReady()")
            page.evaluate("document.fonts.ready.then(() => true)")
            page.evaluate("Reveal.configure({transition: 'none', backgroundTransition: 'none'})")
            titles = page.evaluate("Reveal.getSlides().map(s => (s.querySelector('h1, h2') || {textContent: ''}).textContent)")
            for i, title in enumerate(titles):
                want = next((c for c in COLUMNS if c in title), None)
                if not want or want in found:
                    continue
                page.evaluate("i => { const ix = Reveal.getIndices(Reveal.getSlides()[i]); Reveal.slide(ix.h, ix.v); }", i)
                page.wait_for_timeout(700)
                found[want] = os.path.join(tmp, "s%03d.png" % i)
                page.screenshot(path=found[want])
            browser.close()
    finally:
        httpd.shutdown()
    missing = [c for c in COLUMNS if c not in found]
    if missing:
        sys.exit("no HTML slide for %s" % missing)
    return [found[c] for c in COLUMNS]


def grid(paths, out, cols, width, labels, gap=12, label_w=150):
    from PIL import Image, ImageDraw, ImageFont
    thumbs = [Image.open(p).convert("RGB") for p in paths]
    thumbs = [t.resize((width, round(t.height * width / t.width)), Image.LANCZOS) for t in thumbs]
    h = max(t.height for t in thumbs)
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (label_w + cols * (width + gap), rows * (h + gap)), "#FFFFFF")
    draw, font = ImageDraw.Draw(sheet), ImageFont.load_default(size=22)
    for n, t in enumerate(thumbs):
        r, c = divmod(n, cols)
        sheet.paste(t, (label_w + c * (width + gap), r * (h + gap)))
        if c == 0:
            draw.text((12, r * (h + gap) + h // 2 - 12), labels[r], fill="#333333", font=font)
    sheet.save(out, optimize=True)


def palettes(out):
    """A row per livery and mode: the categorical slots, the default map, the diverging scale."""
    from PIL import Image, ImageDraw, ImageFont
    S, G, LW = 34, 4, 170
    rows = []
    for name in LIVERIES:
        ch = json.load(open(os.path.join(LIVERIES_DIR, name, "build", "livery.json")))["charts"]
        for m in ("light", "dark"):
            b = ch[m]
            rows.append((f"{name} {m}", b["surface"], b["categorical"][:8], b["sequential"][b["sequential-default"]],
                         b["diverging"]))
    width = LW + 8 * (S + G) + 30 + 260 + 30 + 220 + 12
    img = Image.new("RGB", (width, len(rows) * (S + 10) + 10), "#FFFFFF")
    d, font = ImageDraw.Draw(img), ImageFont.load_default(size=16)

    def ramp(x, y, steps, w):   # the steps, evenly, as a strip (a picture of the map, not its OKLab blend)
        for i, c in enumerate(steps):
            d.rectangle([x + i * w // len(steps), y, x + (i + 1) * w // len(steps), y + S], fill=c)

    for r, (label, surface, cat, seq, div) in enumerate(rows):
        y = 10 + r * (S + 10)
        d.rectangle([0, y - 5, width, y + S + 5], fill=surface)
        ink = "#FFFFFF" if sum(bytes.fromhex(surface[1:])) < 384 else "#222222"
        d.text((12, y + S // 2 - 9), label, fill=ink, font=font)
        for i, c in enumerate(cat):
            d.rectangle([LW + i * (S + G), y, LW + i * (S + G) + S, y + S], fill=c)
        x = LW + 8 * (S + G) + 30
        ramp(x, y, seq, 260)
        ramp(x + 260 + 30, y, div, 220)
    img.save(out, optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    cells = []
    with tempfile.TemporaryDirectory() as tmp:
        for livery in LIVERIES:
            subprocess.run(["make", "html", f"LIVERY={livery}"], check=True, stdout=subprocess.DEVNULL)
            os.mkdir(os.path.join(tmp, livery))
            cells += shots(os.path.join(tmp, livery))
        grid(cells, os.path.join(OUT, "liveries.png"), len(COLUMNS), 400, LIVERIES)
    palettes(os.path.join(OUT, "palettes.png"))
    if LIVERIES[-1] != LIVERIES[0]:
        subprocess.run(["make", "html", f"LIVERY={LIVERIES[0]}"], check=True, stdout=subprocess.DEVNULL)
    for f in ("liveries.png", "palettes.png"):
        print(f"{OUT}/{f} {os.path.getsize(os.path.join(OUT, f)) // 1024} KB")


if __name__ == "__main__":
    main()
