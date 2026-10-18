"""The livery's wave curves as DrawingML custom geometry, for livery_template.py and slide_layout.py.

`lines` is livery.json's art.waves.lines: three lines, each seven [x, y] slide fractions (y
down): start, ctrl, ctrl, peak, ctrl, ctrl, end, from the top edge to the bottom. Paths are in
a 16000 x 9000 unit box over the whole slide (0.1 slide px), shifted right by `shift`."""

PW, PH = 16000, 9000
# role -> the color slot a shape fills with it (clrMap names, so a theme edit recolors it); the
# template builder's layouts and slide_layout.py's covers
ROLE_SLOT = {"primary": "tx2", "dark": "accent3", "background": "bg1", "foreground": "tx1", "surface": "bg2",
             "secondary": "accent1", "highlight": "accent2", "accent": "accent4", "warning": "accent5",
             "primary-contrast": "accent6"}
XMLNS = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'


def _pt(lines, k, i, shift):
    x, y = lines[k][i]
    return round((x + shift) * PW), round(y * PH)


def _cubics(lines, k, order, shift):
    return "".join("<a:cubicBezTo>" + "".join('<a:pt x="%d" y="%d"/>' % _pt(lines, k, i, shift) for i in order[j:j + 3])
                   + "</a:cubicBezTo>" for j in range(1, len(order), 3))


def _move(lines, k, i, shift):
    return '<a:moveTo><a:pt x="%d" y="%d"/></a:moveTo>' % _pt(lines, k, i, shift)


def _line_to(x, y):
    return f'<a:lnTo><a:pt x="{x}" y="{y}"/></a:lnTo>'


DOWN, UP = list(range(7)), list(range(6, -1, -1))


def geom(path_body, fill=True, stroke=True):
    return ('<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/>'
            f'<a:pathLst><a:path w="{PW}" h="{PH}"{"" if fill else " fill=\"none\""}{"" if stroke else " stroke=\"0\""}>'
            f'{path_body}</a:path></a:pathLst></a:custGeom>')


def line_geom(lines, k, shift):
    """Line k, top edge to bottom edge (stroke only)."""
    return geom(_move(lines, k, 0, shift) + _cubics(lines, k, DOWN, shift), fill=False)


def band_geom(lines, k, m, shift):
    """The region between lines k and m."""
    return geom(_move(lines, k, 0, shift) + _cubics(lines, k, DOWN, shift)
                + _line_to(*_pt(lines, m, 6, shift)) + _cubics(lines, m, UP, shift) + "<a:close/>", stroke=False)


def field_geom(lines, k, shift):
    """The slide left of line k."""
    return geom(f'<a:moveTo><a:pt x="0" y="0"/></a:moveTo>' + _line_to(*_pt(lines, k, 0, shift))
                + _cubics(lines, k, DOWN, shift) + _line_to(0, PH) + "<a:close/>", stroke=False)


def shape_xml(sid, name, geometry, fill_xml, ln_xml, w_emu, h_emu):
    """A full-slide p:sp with the geometry; fill_xml and ln_xml are a:solidFill / a:ln fragments."""
    return (f'<p:sp {XMLNS}><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{w_emu}" cy="{h_emu}"/></a:xfrm>{geometry}{fill_xml}{ln_xml}</p:spPr></p:sp>')


def scheme_fill(slot, alpha=None):
    a = f'<a:alpha val="{alpha}"/>' if alpha else ""
    return f'<a:solidFill><a:schemeClr val="{slot}">{a}</a:schemeClr></a:solidFill>'


def comp_shapes(lines, comp, first_id, w_emu, h_emu, field_slot="tx2", line_slot="accent1"):
    """A composition's waves (livery.json compositions) as shapes, by its waves.style: bands (the
    lines with translucent bands between lines 1-2 and 2-3), lines, or cover (the opaque field to
    line 2, the field's translucent band to line 3, the lines); without waves, a field narrower
    than the slide as a straight-edged rect. Alphas and the line width are the composition's."""
    w, f, out = comp["waves"], comp["field"], []
    if not (w and lines):
        if f and f["box"][2] < 1:
            x, y, bw, bh = f["box"]
            out.append(f'<p:sp {XMLNS}><p:nvSpPr><p:cNvPr id="{first_id}" name="Cover field"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
                       f'<p:spPr><a:xfrm><a:off x="{round(x * w_emu)}" y="{round(y * h_emu)}"/><a:ext cx="{round(bw * w_emu)}" cy="{round(bh * h_emu)}"/></a:xfrm>'
                       f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{scheme_fill(field_slot)}<a:ln><a:noFill/></a:ln></p:spPr></p:sp>')
        return out
    sid, shift, alpha = first_id, w["shift"], lambda o: round(o * 100000)
    none = "<a:ln><a:noFill/></a:ln>"
    if w["style"] == "cover":
        out.append(shape_xml(sid, "Cover field", field_geom(lines, 1, shift), scheme_fill(field_slot), none, w_emu, h_emu)); sid += 1
        out.append(shape_xml(sid, "Cover band", band_geom(lines, 1, 2, shift), scheme_fill(field_slot, alpha(w["opacity"][0])), none, w_emu, h_emu)); sid += 1
    elif w["style"] == "bands":
        for k, o in zip((0, 1), w["opacity"]):
            out.append(shape_xml(sid, f"Wave band {k + 1}", band_geom(lines, k, k + 1, shift), scheme_fill(line_slot, alpha(o)), none, w_emu, h_emu)); sid += 1
    for k in range(len(lines)):
        out.append(shape_xml(sid, f"Wave line {k + 1}", line_geom(lines, k, shift), "<a:noFill/>",
                             f'<a:ln w="{round(w["line"] * w_emu)}">{scheme_fill(line_slot)}</a:ln>', w_emu, h_emu)); sid += 1
    return out


def wave_shapes(lines, first_id, w_emu, h_emu, shift, slot, bands=True, line_px=2.4):
    """The lines alone, the content slides' (the master's): not a composition."""
    emu_px = w_emu / 1600
    return [shape_xml(first_id + k, f"Wave line {k + 1}", line_geom(lines, k, shift), "<a:noFill/>",
                      f'<a:ln w="{round(line_px * emu_px)}">{scheme_fill(slot)}</a:ln>', w_emu, h_emu) for k in range(len(lines))]
