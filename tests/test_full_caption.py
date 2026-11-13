"""Check a {.full} slide's caption in the pptx (slide_layout.py's full_slide(), #178).

    python3 -m pytest tests/test_full_caption.py

The caption box is one caption line (geometry.full.caption) across the slide less geometry.full.pad
a side, as HTML's; a caption that wraps grows the box by a line for each line it wraps to, upward,
the picture's box shorter by as much, so it never runs off the slide's foot. slide-layout.lua under
plain pandoc (conftest's shim), single-body.lua's fold (its shim), the step in a subprocess under
ncar's LIVERY_DIR. Needs pandoc.
"""

import shutil

from conftest import ENGINE, ROOT, pandoc_exe, run_steps, slide_layout_shim

NCAR = ROOT / "liveries" / "ncar"
IMAGE = ROOT / "decks" / "quickstart" / "images" / "example.jpg"
MD = ("## Short {{.full}}\n\n![](p.jpg)\n\nA short caption.\n\n"
      "## Long {{.full}}\n\n![](p.jpg)\n\n{}\n").format("A caption that runs on, " * 12)
SINGLE = ('quarto = {{ doc = {{ is_format = function(f) return f == "pptx" end }},\n'
          '           utils = {{ resolve_path = function(p) return "{engine}/" .. p end }},\n'
          '           log = {{ warning = function(s) io.stderr:write("WARNING: " .. s .. "\\n") end }},\n'
          '           json = {{ decode = pandoc.json.decode }} }}\n'
          'dofile("{engine}/single-body.lua")\n')


def test_wrapped_caption_grows(tmp_path):
    import subprocess
    from pptx import Presentation
    shutil.copy(IMAGE, tmp_path / "p.jpg")
    out = tmp_path / "f.pptx"
    single = tmp_path / "single-body-shim.lua"
    single.write_text(SINGLE.format(engine=ENGINE))
    subprocess.run([pandoc_exe(), "--lua-filter", str(slide_layout_shim(tmp_path)), "--lua-filter", str(single), "--reference-doc",
                    str(NCAR / "template.pptx"), "-o", str(out)], input=MD, text=True, cwd=tmp_path, check=True, capture_output=True)
    run_steps(out, ["slide_layout"], NCAR)
    prs = Presentation(str(out))
    boxes = []
    for slide in prs.slides:
        cap = next(sh for sh in slide.shapes if sh.has_text_frame and "caption" in sh.text_frame.text)
        pic = next(sh for sh in slide.shapes if sh.shape_type == 13)
        boxes.append((cap, pic))
    (short, spic), (long, lpic) = boxes
    assert long.height > short.height, (short.height, long.height)
    assert long.top + long.height == short.top + short.height, "the box grew downward"
    assert lpic.top + lpic.height <= long.top, "the picture over the grown caption"
    assert long.top + long.height <= prs.slide_height
