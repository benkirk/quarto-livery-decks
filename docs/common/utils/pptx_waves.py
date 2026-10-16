"""The livery's wave curves as DrawingML custom geometry, for livery_template.py and slide_layout.py.

`lines` is livery.json's art.waves.lines: three lines, each seven [x, y] slide fractions (y
down): start, ctrl, ctrl, peak, ctrl, ctrl, end, from the top edge to the bottom. Paths are in
a 16000 x 9000 unit box over the whole slide (0.1 slide px), shifted right by `shift`."""

PW, PH = 16000, 9000
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


def cover_shapes(lines, first_id, w_emu, h_emu, field_slot="tx2", line_slot="accent1", shift=0.0, line_px=2.4):
    """The brand cover over a full-slide photo: the opaque field to line 2, a 65% band to line 3,
    the three lines; the photo, pushed to the back, shows between lines 2 and 3 and to their right."""
    emu_px = w_emu / 1600
    out = [shape_xml(first_id, "Cover field", field_geom(lines, 1, shift), scheme_fill(field_slot), "<a:ln><a:noFill/></a:ln>", w_emu, h_emu),
           shape_xml(first_id + 1, "Cover band", band_geom(lines, 1, 2, shift), scheme_fill(field_slot, 65000), "<a:ln><a:noFill/></a:ln>", w_emu, h_emu)]
    for k in range(len(lines)):
        out.append(shape_xml(first_id + 2 + k, f"Wave line {k + 1}", line_geom(lines, k, shift), "<a:noFill/>",
                             f'<a:ln w="{round(line_px * emu_px)}">{scheme_fill(line_slot)}</a:ln>', w_emu, h_emu))
    return out


def wave_shapes(lines, first_id, w_emu, h_emu, shift, slot, bands=True, line_px=2.4):
    """The lines, with the two translucent bands between them when `bands` (dividers, title)."""
    emu_px = w_emu / 1600
    out, sid = [], first_id
    if bands:
        for k, m, alpha in ((0, 1, 18000), (1, 2, 10000)):
            out.append(shape_xml(sid, f"Wave band {k + 1}", band_geom(lines, k, m, shift), scheme_fill(slot, alpha), "<a:ln><a:noFill/></a:ln>", w_emu, h_emu)); sid += 1
    for k in range(len(lines)):
        out.append(shape_xml(sid, f"Wave line {k + 1}", line_geom(lines, k, shift), "<a:noFill/>",
                             f'<a:ln w="{round(line_px * emu_px)}">{scheme_fill(slot)}</a:ln>', w_emu, h_emu)); sid += 1
    return out


def straight_cover_shapes(first_id, w_emu, h_emu, field_slot="tx2", edge=0.52):
    """The cover of a livery without waves: an opaque field over the left `edge` of the slide, the
    straight edge the HTML and PDF themes draw (engine-revealjs.lua, beamer's \\engine@coverbox)."""
    return [(f'<p:sp {XMLNS}><p:nvSpPr><p:cNvPr id="{first_id}" name="Cover field"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
             f'<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{round(edge * w_emu)}" cy="{h_emu}"/></a:xfrm>'
             f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{scheme_fill(field_slot)}<a:ln><a:noFill/></a:ln></p:spPr></p:sp>')]
