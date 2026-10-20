#!/usr/bin/env python3
"""Give every SVG picture in a pandoc-rendered pptx a PNG fallback, as PowerPoint itself does.

The deck's plots are SVG (`fig-format: svg`, common/_quarto.yml), and pandoc's pptx writer puts
each in as a plain .svg picture, which PowerPoint does not expect. For each picture whose blip
points at an SVG this rasterizes it to a PNG in ppt/media (the next free imageN, rsvg-convert at
the deck's fig-dpi), points the blip's r:embed at the PNG, and keeps the SVG through Office 2016's
extension, a:blip/a:extLst/a:ext/asvg:svgBlip, on a relationship of its own. PowerPoint 2016+
draws the SVG (vector, sharp at any zoom); anything that does not know the extension draws the
PNG (Google Slides' import; LibreOffice reads the SVG too). [Content_Types].xml gets Defaults for
png and svg. Zip surgery via lxml, first in pptx_post.py, so every later step (python-pptx's
picture.image reads the PNG) sees an ordinary picture. Idempotent: a blip that has the extension
is left alone; a plot that is PNG already (livery_mpl.raster()) is untouched."""

import posixpath
import re
import shutil
import subprocess

from lxml import etree

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
ASVG = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
SVG_EXT = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"   # the a:ext uri Office writes for svgBlip
IMAGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
DPI = 200   # the fallback's resolution: common/_quarto.yml's fig-dpi for engine-pptx


def _xml(root):
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _rasterize(svg: bytes) -> bytes:
    exe = shutil.which("rsvg-convert")
    if exe is None:
        raise SystemExit("svg_fallback: rsvg-convert not found (conda-forge librsvg, in "
                         "conda-env.yaml): an SVG picture needs its PNG fallback")
    return subprocess.run([exe, "--dpi-x", str(DPI), "--dpi-y", str(DPI), "-f", "png"],
                          input=svg, capture_output=True, check=True).stdout


def run(parts: dict, name: str) -> None:
    """The deck's zip members (name -> bytes), changed in place; name for the message."""
    used = [int(m.group(1)) for p in parts if (m := re.match(r"ppt/media/image(\d+)\.", p))]
    nxt = max(used, default=0) + 1
    pngs = {}   # an SVG's member name -> its PNG's, shared by every picture of it
    done = 0
    for rels_name in sorted(p for p in parts if re.match(r"ppt/slides/_rels/slide\d+\.xml\.rels$", p)):
        part = posixpath.join("ppt/slides", posixpath.basename(rels_name)[:-len(".rels")])
        if part not in parts:
            continue
        rels = etree.fromstring(parts[rels_name])
        targets = {r.get("Id"): r.get("Target") for r in rels}
        ids = {int(i[3:]) for i in targets if i.startswith("rId") and i[3:].isdigit()}
        root = etree.fromstring(parts[part])
        changed = False
        for blip in root.iter("{%s}blip" % A):
            rid = blip.get("{%s}embed" % R)
            target = targets.get(rid) or ""
            if not target.lower().endswith(".svg") or blip.find("{%s}extLst" % A) is not None:
                continue
            svg = posixpath.normpath(posixpath.join("ppt/slides", target))
            if svg not in pngs:
                pngs[svg] = "ppt/media/image%d.png" % nxt
                nxt += 1
                parts[pngs[svg]] = _rasterize(parts[svg])
            new = "rId%d" % (max(ids, default=0) + 1)
            ids.add(int(new[3:]))
            etree.SubElement(rels, "{%s}Relationship" % PR, Id=new, Type=IMAGE,
                             Target="../media/" + posixpath.basename(pngs[svg]))
            blip.set("{%s}embed" % R, new)   # the PNG is the picture
            ext = etree.SubElement(etree.SubElement(blip, "{%s}extLst" % A), "{%s}ext" % A, uri=SVG_EXT)
            etree.SubElement(ext, "{%s}svgBlip" % ASVG, nsmap={"asvg": ASVG}).set("{%s}embed" % R, rid)
            changed = True
            done += 1
        if changed:
            parts[rels_name], parts[part] = _xml(rels), _xml(root)
    if done:
        ct = etree.fromstring(parts["[Content_Types].xml"])
        have = {d.get("Extension").lower() for d in ct.findall("{%s}Default" % CT)}
        for ext, mime in (("png", "image/png"), ("svg", "image/svg+xml")):
            if ext not in have:
                ct.insert(0, etree.Element("{%s}Default" % CT, Extension=ext, ContentType=mime))
        parts["[Content_Types].xml"] = _xml(ct)
    print(f"svg_fallback: {done} SVG picture(s), {len(pngs)} PNG fallback(s) at {DPI} dpi → {name}")
