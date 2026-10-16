#!/usr/bin/env python3
"""Build a livery's pandoc-compliant template.pptx from its data (design section 6, step 2).

    livery_template.py <livery dir> [-o template.pptx]

Everything comes from build/livery.json: the theme's color slots (pptx.scheme, or the roles
by the slot contract), the typeface, the light and dark logos, the geometry fractions and
the wave curves (art.waves) or a picture behind content slides (art.content; the other art
kinds are not placed yet). The master carries the title with its accent tab and hairline
rule, the lockup top right, the faint wave lines and the body-size ladder; the seven layouts
pandoc looks up by name are generated (Title Slide, Title and Content, Section Header, Two
Content, Comparison, Content with Caption, Blank), the Title Slide with its five
placeholders. Fonts are embedded later by embed_fonts.py; the title photo by title_photo.py.
Rewrites in place with fixed zip timestamps, so an unchanged rebuild is byte-identical.
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

import livery as livery_mod
import pptx_waves

# the pptx is 12192000 x 6858000 EMU; the themes think in 1600x900 slide pixels
W_EMU, H_EMU = 12192000, 6858000
PX = 7620
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NSDECL = f'xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"'
XMLDECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
# slot contract (design section 4) for a livery that sets no pptx.scheme of its own
SLOT_ROLES = {"dk1": "foreground", "lt1": "background", "dk2": "primary", "lt2": "surface",
              "accent1": "secondary", "accent2": "highlight", "accent3": "dark", "accent4": "accent",
              "accent5": "warning", "accent6": "primary-contrast", "hlink": "primary", "folHlink": "highlight"}
LAYOUTS = ["Title Slide", "Title and Content", "Section Header", "Two Content", "Comparison",
           "Content with Caption", "Blank"]
LAYOUT_TYPES = {"Title Slide": "title", "Title and Content": "obj", "Section Header": "secHead",
                "Two Content": "twoObj", "Comparison": "twoTxTwoObj", "Content with Caption": "objTx", "Blank": "blank"}


def emu(frac, axis):
    return round(frac * axis)


def xfrm(x, y, w, h):
    """An a:xfrm from slide fractions."""
    return (f'<a:xfrm><a:off x="{emu(x, W_EMU)}" y="{emu(y, H_EMU)}"/>'
            f'<a:ext cx="{emu(w, W_EMU)}" cy="{emu(h, H_EMU)}"/></a:xfrm>')


def fill(slot, alpha=None):
    a = f'<a:alpha val="{alpha}"/>' if alpha else ""
    return f'<a:solidFill><a:schemeClr val="{slot}">{a}</a:schemeClr></a:solidFill>'


def srgb(hexv):
    return f'<a:solidFill><a:srgbClr val="{hexv.lstrip("#")}"/></a:solidFill>'


class Builder:
    def __init__(self, livery: dict):
        self.L = livery
        self.geom = livery["geometry"]
        self.roles = livery["roles"]
        self.scheme = livery.get("pptx", {}).get("scheme") or {
            slot: livery["roles"][role] for slot, role in SLOT_ROLES.items() if role in livery["roles"]}
        self.typeface = livery["pptx"]["typeface"]
        art = livery.get("art") or {}
        self.waves, self.art_content = art.get("waves"), art.get("content")
        self.sid = 10

    def next_id(self):
        self.sid += 1
        return self.sid

    # ------------------------------------------------------------------ waves
    def wave_shapes(self, shift, slot, bands=True, width_px=2.4):
        """The livery's wave lines (and the two translucent bands) as freeform shapes."""
        if not self.waves:
            return []
        shapes = pptx_waves.wave_shapes(self.waves["lines"], self.sid + 1, W_EMU, H_EMU, shift, slot, bands, width_px)
        self.sid += len(shapes)
        return [s.replace(f" {pptx_waves.XMLNS}", "") for s in shapes]   # the layout root declares the namespaces

    # ------------------------------------------------------------- placeholders
    def ph(self, name, ptype, idx, box, body_pr, lst, text, sz=None):
        attrs = f' type="{ptype}"' if ptype else ""
        attrs += f' sz="{sz}"' if sz else ""
        attrs += f' idx="{idx}"' if idx is not None else ""
        return (f'<p:sp><p:nvSpPr><p:cNvPr id="{self.next_id()}" name="{name}"/><p:cNvSpPr><a:spLocks noGrp="1"/>'
                f'</p:cNvSpPr><p:nvPr><p:ph{attrs}/></p:nvPr></p:nvSpPr><p:spPr>{box}'
                f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
                f'<p:txBody><a:bodyPr {body_pr}/><a:lstStyle>{lst}</a:lstStyle>'
                f'<a:p><a:r><a:rPr lang="en-US"/><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>')

    def chrome(self, light_text=True, with_date=True):
        """Slide number, date and footer placeholders (idx 20-22: pandoc matches content by idx too,
        so these must never share a number with a content box)."""
        color = fill("tx1") if light_text else srgb(self.roles["primary-text"])
        num = (f'<p:sp><p:nvSpPr><p:cNvPr id="{self.next_id()}" name="Slide Number Placeholder"/><p:cNvSpPr>'
               f'<a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="sldNum" sz="quarter" idx="22"/></p:nvPr></p:nvSpPr>'
               f'<p:spPr>{xfrm(0.001, 0.945, 0.039, 0.053)}</p:spPr><p:txBody><a:bodyPr anchor="ctr"/><a:lstStyle>'
               f'<a:lvl1pPr algn="ctr"><a:defRPr sz="1200" b="1">{color}</a:defRPr></a:lvl1pPr></a:lstStyle>'
               f'<a:p><a:fld id="{{C5EF2332-01BF-834F-8236-50238282D533}}" type="slidenum"><a:rPr lang="en-US"/>'
               f'<a:t>‹#›</a:t></a:fld></a:p></p:txBody></p:sp>')
        dt = self.ph("Date Placeholder", "dt", 20, xfrm(0.856, 0.956, 0.113, 0.027),
                     'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"',
                     f'<a:lvl1pPr algn="r"><a:defRPr sz="900">{color}</a:defRPr></a:lvl1pPr>', "", sz="half")
        ftr = self.ph("Footer Placeholder", "ftr", 21, xfrm(0.046, 0.956, 0.34, 0.027),
                      'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"',
                      f'<a:lvl1pPr algn="l"><a:defRPr sz="900">{color}</a:defRPr></a:lvl1pPr>', "", sz="quarter")
        return num + (dt if with_date else "") + ftr

    def logo(self, rid, variant, x, y, h):
        w = h * self.geom["logo"]["aspect"] * H_EMU / W_EMU
        return (f'<p:pic><p:nvPicPr><p:cNvPr id="{self.next_id()}" name="Logo ({variant})"/>'
                f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr>'
                f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
                f'<p:spPr>{xfrm(x, y, w, h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')

    # ------------------------------------------------------------------ master
    def master(self):
        g = self.geom; m, tab = g["margin"], g["tab"]
        title_top, rule_y, body_top, body_bottom = 0.049, 0.1444, 0.1667, 1 - 0.0778
        logo_h = g["logo"]["height"]; logo_w = logo_h * g["logo"]["aspect"] * H_EMU / W_EMU
        title_w = 1 - 2 * m - logo_w - 0.025
        sizes = g.get("body-sizes-pt", [20, 18, 16, 14, 12])
        bullets = [("Arial", "•"), ("Wingdings", "§"), ("Courier New", "o"), ("Arial", "–"), ("Arial", "»")]
        body_lvls = ""
        for i, (sz, (bfont, bchar)) in enumerate(zip(sizes, bullets), 1):
            mar = 228600 * i
            spc = '<a:spcBef><a:spcPts val="1000"/></a:spcBef>' if i == 1 else '<a:spcBef><a:spcPts val="500"/></a:spcBef>'
            body_lvls += (f'<a:lvl{i}pPr marL="{mar}" indent="-228600" algn="l" defTabSz="457200" rtl="0" eaLnBrk="1" '
                          f'latinLnBrk="0" hangingPunct="1"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc>{spc}'
                          f'<a:buFont typeface="{bfont}"/><a:buChar char="{bchar}"/><a:defRPr sz="{sz * 100}" kern="1200">'
                          f'{fill("tx1")}<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/>'
                          f'</a:defRPr></a:lvl{i}pPr>')
        for i in range(len(sizes) + 1, 10):
            body_lvls += (f'<a:lvl{i}pPr marL="{228600 * i}" indent="-228600" algn="l"><a:defRPr sz="{sizes[-1] * 100}" kern="1200">'
                          f'{fill("tx1")}<a:latin typeface="+mn-lt"/></a:defRPr></a:lvl{i}pPr>')
        other = "".join(f'<a:lvl{i}pPr marL="{457200 * (i - 1)}" algn="l" defTabSz="457200"><a:defRPr sz="1800" kern="1200">'
                        f'{fill("tx1")}<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/>'
                        f'</a:defRPr></a:lvl{i}pPr>' for i in range(1, 10))
        tab_sp = (f'<p:sp><p:nvSpPr><p:cNvPr id="{self.next_id()}" name="Title tab"/><p:cNvSpPr/><p:nvPr userDrawn="1"/>'
                  f'</p:nvSpPr><p:spPr>{xfrm(0, title_top, tab, rule_y - title_top)}<a:prstGeom prst="rect"><a:avLst/>'
                  f'</a:prstGeom>{fill("accent4")}<a:ln><a:noFill/></a:ln></p:spPr></p:sp>')
        rule = (f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{self.next_id()}" name="Title rule"/><p:cNvCxnSpPr/>'
                f'<p:nvPr userDrawn="1"/></p:nvCxnSpPr><p:spPr>{xfrm(m, rule_y, 1 - 2 * m, 0)}'
                f'<a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:ln w="9525">{fill("tx1", 30000)}</a:ln></p:spPr></p:cxnSp>')
        title = self.ph("Title Placeholder", "title", None, xfrm(m, title_top, title_w, rule_y - title_top),
                        'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"><a:normAutofit/><a:x',
                        "", "Click to edit Master title style")
        # (the bodyPr trick above closes the element; restate it plainly)
        title = title.replace('<a:bodyPr vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"><a:normAutofit/><a:x/>',
                              '<a:bodyPr vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"><a:normAutofit/></a:bodyPr>')
        body = self.ph("Text Placeholder", "body", 1, xfrm(m, body_top, 1 - 2 * m, body_bottom - body_top),
                       'vert="horz" lIns="0" tIns="45720" rIns="0" bIns="45720"><a:normAutofit/></a:bodyPr><a:lstStyle/>'
                       '<a:p><a:pPr lvl="0"/><a:r><a:rPr lang="en-US"/><a:t>Click to edit Master text styles</a:t></a:r></a:p>'
                       '</p:txBody></p:sp><!--', "", "")
        body = body.split("<!--")[0]
        waves = "".join(self.wave_shapes(self.waves["shift"]["content"], "lt2", bands=False)) if self.waves else ""
        art = ""   # art.content: a full-slide picture under everything (the layouts with a field hide the master)
        if self.art_content:
            art = (f'<p:pic><p:nvPicPr><p:cNvPr id="{self.next_id()}" name="Content art"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/>'
                   f'</p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr><p:blipFill><a:blip r:embed="rId3"/><a:stretch><a:fillRect/></a:stretch>'
                   f'</p:blipFill><p:spPr>{xfrm(0, 0, 1, 1)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')
        logo = self.logo("rId2", "light", 1 - m - logo_w, g["logo"]["top"], logo_h)
        shapes = art + waves + tab_sp + rule + title + body + self.chrome() + logo
        return (XMLDECL + f'<p:sldMaster {NSDECL}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
                f'<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                f'<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
                f'</a:xfrm></p:grpSpPr>{shapes}</p:spTree></p:cSld>'
                f'<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
                f'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
                f'<p:sldLayoutIdLst>' + "".join(f'<p:sldLayoutId id="{2147483649 + i}" r:id="rId{10 + i}"/>' for i in range(len(LAYOUTS))) +
                f'</p:sldLayoutIdLst><p:txStyles><p:titleStyle><a:lvl1pPr algn="l" defTabSz="457200" rtl="0" eaLnBrk="1" '
                f'latinLnBrk="0" hangingPunct="1"><a:spcBef><a:spcPct val="0"/></a:spcBef><a:buNone/>'
                f'<a:defRPr sz="2800" b="1" kern="1200" baseline="0">{fill("tx1")}<a:latin typeface="+mj-lt"/>'
                f'<a:ea typeface="+mj-ea"/><a:cs typeface="+mj-cs"/></a:defRPr></a:lvl1pPr></p:titleStyle>'
                f'<p:bodyStyle>{body_lvls}</p:bodyStyle><p:otherStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr>{other}'
                f'</p:otherStyle></p:txStyles></p:sldMaster>')

    # ----------------------------------------------------------------- layouts
    def layout(self, name, shapes, bg=None, show_master=True):
        bgx = f'<p:bg><p:bgPr>{bg}<a:effectLst/></p:bgPr></p:bg>' if bg else ""
        sm = "" if show_master else ' showMasterSp="0"'
        return (XMLDECL + f'<p:sldLayout {NSDECL} type="{LAYOUT_TYPES[name]}" preserve="1"{sm}><p:cSld name="{name}">{bgx}'
                f'<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                f'<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
                f'</a:xfrm></p:grpSpPr>{"".join(shapes)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')

    def field_text(self, pt, bold=False, caps=False):
        """A lstStyle for text on the brand field, in the primary-text role."""
        return (f'<a:lvl1pPr algn="l" marL="0" indent="0"><a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/>'
                f'<a:defRPr sz="{pt * 100}" b="{1 if bold else 0}"{" cap=\"all\"" if caps else ""}>'
                f'{srgb(self.roles["primary-text"])}<a:latin typeface="+mn-lt"/></a:defRPr></a:lvl1pPr>')

    def title_slide(self):
        g, m = self.geom, self.geom["margin"]
        no_inset = 'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:normAutofit/></a:bodyPr><a:lstStyle>'
        shapes = self.wave_shapes(self.waves["shift"]["title"], "accent1") if self.waves else []
        shapes.append(self.logo("rId2", "dark", m, 0.06, g["logo"].get("title", 0.09)))
        tab_top, tab_h = 0.43, 0.16
        shapes.append(f'<p:sp><p:nvSpPr><p:cNvPr id="{self.next_id()}" name="Title tab"/><p:cNvSpPr/><p:nvPr userDrawn="1"/>'
                      f'</p:nvSpPr><p:spPr>{xfrm(0, tab_top, g["tab"], tab_h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
                      f'{fill("accent4")}<a:ln><a:noFill/></a:ln></p:spPr></p:sp>')
        shapes.append(self.ph("Date", "dt", 20, xfrm(m, 0.375, 0.45, 0.045),
                              no_inset + self.field_text(12, bold=True, caps=True) + "</a:lstStyle><a:p><a:fld id=\"{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}\" type=\"datetime1\"><a:rPr lang=\"en-US\"/><a:t>Date</a:t></a:fld></a:p></p:txBody></p:sp><!--",
                              "", "").split("<!--")[0])
        shapes.append(self.ph("Title", "ctrTitle", None, xfrm(m, tab_top, 0.50, tab_h),
                              f'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:normAutofit/></a:bodyPr><a:lstStyle>'
                              f'{self.field_text(36, bold=True)}</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Title</a:t></a:r></a:p></p:txBody></p:sp><!--',
                              "", "").split("<!--")[0])
        shapes.append(f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{self.next_id()}" name="Title rule"/><p:cNvCxnSpPr/><p:nvPr userDrawn="1"/>'
                      f'</p:nvCxnSpPr><p:spPr>{xfrm(m, 0.615, 0.065, 0)}<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
                      f'<a:ln w="19050">{fill("accent1")}</a:ln></p:spPr></p:cxnSp>')
        shapes.append(self.ph("Subtitle", "subTitle", 1, xfrm(m, 0.64, 0.50, 0.22),
                              no_inset + self.field_text(18) + '</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Subtitle</a:t></a:r></a:p></p:txBody></p:sp><!--',
                              "", "").split("<!--")[0])
        shapes.append(self.chrome(light_text=False, with_date=False))   # the date sits above the title
        return self.layout("Title Slide", shapes, bg=fill("tx2"), show_master=False)

    def section_header(self):
        g, m = self.geom, self.geom["margin"]
        shapes = self.wave_shapes(self.waves["shift"]["section"], "accent1") if self.waves else []
        shapes.append(self.logo("rId2", "dark", m, 0.08, g["logo"].get("section", 0.0644)))
        title_lst = (f'<a:lvl1pPr algn="l"><a:lnSpc><a:spcPct val="90000"/></a:lnSpc><a:defRPr sz="4400" b="1" cap="none" baseline="0">'
                     f'{srgb(self.roles["primary-text"])}<a:latin typeface="+mj-lt"/></a:defRPr></a:lvl1pPr>')
        shapes.append(self.ph("Title 1", "title", None, xfrm(m, 400 / 900, 0.62, 110 / 900),
                              'lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:normAutofit/></a:bodyPr><a:lstStyle>' + title_lst +
                              '</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Section title</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "").split("<!--")[0])
        shapes.append(self.ph("Text Placeholder 2", "body", 1, xfrm(m, 520 / 900, 0.60, 120 / 900),
                              'lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:normAutofit/></a:bodyPr><a:lstStyle>' + self.field_text(18) +
                              '</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Subtitle</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "").split("<!--")[0])
        shapes.append(self.chrome(light_text=False))
        return self.layout("Section Header", shapes, bg=fill("tx2"), show_master=False)

    def content_layout(self, name):
        g, m = self.geom, self.geom["margin"]
        body_top, body_bottom = 0.1667, 1 - 0.0778
        h = body_bottom - body_top
        inherit_title = self.ph("Title 1", "title", None, "", 'vert="horz"', "", "Click to edit Master title style")
        shapes = [inherit_title]
        half = (1 - 2 * m - 0.03) / 2
        if name == "Title and Content":
            shapes.append(self.ph("Content Placeholder 2", None, 1, xfrm(m, body_top, 1 - 2 * m, h), 'vert="horz"', "", "Click to edit Master text styles"))
        elif name == "Two Content":
            shapes.append(self.ph("Content Placeholder 2", None, 1, xfrm(m, body_top, half, h), 'vert="horz"', "", "Left", sz="half"))
            shapes.append(self.ph("Content Placeholder 3", None, 2, xfrm(m + half + 0.03, body_top, half, h), 'vert="horz"', "", "Right", sz="half"))
        elif name == "Comparison":
            head_h = 0.09
            head_lst = f'<a:lvl1pPr marL="0" indent="0"><a:buNone/><a:defRPr sz="1800" b="1">{fill("tx2")}</a:defRPr></a:lvl1pPr>'
            for i, (idx_head, idx_body, x) in enumerate(((1, 11, m), (3, 2, m + half + 0.03))):
                shapes.append(self.ph(f"Text Placeholder {i + 2}", "body", idx_head, xfrm(x, body_top, half, head_h),
                                      'vert="horz" anchor="b"><a:normAutofit/></a:bodyPr><a:lstStyle>' + head_lst +
                                      '</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Heading</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "", sz="quarter" if i else None).split("<!--")[0])
                shapes.append(self.ph(f"Content Placeholder {i + 4}", None, idx_body, xfrm(x, body_top + head_h + 0.01, half, h - head_h - 0.01), 'vert="horz"', "", "Content", sz="half"))
        elif name == "Content with Caption":
            cap_w = 0.33
            shapes[0] = self.ph("Title 1", "title", None, xfrm(m, body_top, cap_w, 0.13),
                                'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="b"><a:normAutofit/></a:bodyPr><a:lstStyle>'
                                '<a:lvl1pPr algn="l"><a:defRPr sz="2000" b="1"/></a:lvl1pPr></a:lstStyle><a:p><a:r><a:rPr lang="en-US"/>'
                                '<a:t>Caption title</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "").split("<!--")[0]
            shapes.append(self.ph("Content Placeholder 2", None, 1, xfrm(m + cap_w + 0.03, body_top, 1 - 2 * m - cap_w - 0.03, h), 'vert="horz"', "", "Content"))
            shapes.append(self.ph("Text Placeholder 3", "body", 2, xfrm(m, body_top + 0.14, cap_w, h - 0.14),
                                  'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0"><a:normAutofit/></a:bodyPr><a:lstStyle>'
                                  '<a:lvl1pPr marL="0" indent="0"><a:buNone/><a:defRPr sz="1400"/></a:lvl1pPr></a:lstStyle><a:p><a:r><a:rPr lang="en-US"/>'
                                  '<a:t>Caption</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "", sz="half").split("<!--")[0])
        elif name == "Blank":
            shapes = []
        shapes.append(self.chrome())
        return self.layout(name, shapes)

    # -------------------------------------------------------------------- parts
    def theme(self):
        cs = "".join(f'<a:{slot}><a:srgbClr val="{self.scheme[slot].lstrip("#")}"/></a:{slot}>' for slot in SLOT_ROLES if slot in self.scheme)
        tf = self.typeface
        fs = (f'<a:fontScheme name="{tf}"><a:majorFont><a:latin typeface="{tf}"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
              f'<a:minorFont><a:latin typeface="{tf}"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>')
        fmt = ('<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
               '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>'
               '<a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
               '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
               '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
               '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>'
               '<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
               '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
               '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>')
        return (XMLDECL + f'<a:theme xmlns:a="{A}" name="{self.L["name"]}"><a:themeElements><a:clrScheme name="{self.L["name"]}">{cs}'
                f'</a:clrScheme>{fs}{fmt}</a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>')

    def build(self, out: Path, livery_dir: Path):
        parts = {}
        light = Path(livery_dir) / livery_mod.logo_path(self.L, "light")
        dark = Path(livery_dir) / livery_mod.logo_path(self.L, "dark")
        parts["ppt/media/image1" + light.suffix] = light.read_bytes()
        parts["ppt/media/image2" + dark.suffix] = dark.read_bytes()
        light_part, dark_part = "image1" + light.suffix, "image2" + dark.suffix
        parts["ppt/theme/theme1.xml"] = self.theme()
        parts["ppt/slideMasters/slideMaster1.xml"] = self.master()
        rels = [f'<Relationship Id="rId1" Type="{REL}/theme" Target="../theme/theme1.xml"/>',
                f'<Relationship Id="rId2" Type="{REL}/image" Target="../media/{light_part}"/>']
        if self.art_content:
            art = Path(livery_dir) / self.art_content
            parts["ppt/media/image3" + art.suffix] = art.read_bytes()
            rels.append(f'<Relationship Id="rId3" Type="{REL}/image" Target="../media/image3{art.suffix}"/>')
        rels += [f'<Relationship Id="rId{10 + i}" Type="{REL}/slideLayout" Target="../slideLayouts/slideLayout{i + 1}.xml"/>' for i in range(len(LAYOUTS))]
        parts["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = XMLDECL + f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(rels)}</Relationships>'
        for i, name in enumerate(LAYOUTS, 1):
            self.sid = 10
            if name == "Title Slide":
                xml, img = self.title_slide(), dark_part
            elif name == "Section Header":
                xml, img = self.section_header(), dark_part
            else:
                xml, img = self.content_layout(name), None
            parts[f"ppt/slideLayouts/slideLayout{i}.xml"] = xml
            r = [f'<Relationship Id="rId1" Type="{REL}/slideMaster" Target="../slideMasters/slideMaster1.xml"/>']
            if img:
                r.append(f'<Relationship Id="rId2" Type="{REL}/image" Target="../media/{img}"/>')
            parts[f"ppt/slideLayouts/_rels/slideLayout{i}.xml.rels"] = XMLDECL + f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(r)}</Relationships>'
        parts["ppt/presentation.xml"] = (XMLDECL + f'<p:presentation {NSDECL} saveSubsetFonts="1" autoCompressPictures="0">'
                                         f'<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst/>'
                                         f'<p:sldSz cx="{W_EMU}" cy="{H_EMU}"/><p:notesSz cx="6858000" cy="9144000"/>'
                                         f'<p:defaultTextStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr></p:defaultTextStyle></p:presentation>')
        parts["ppt/_rels/presentation.xml.rels"] = (XMLDECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                                    f'<Relationship Id="rId1" Type="{REL}/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
                                                    f'<Relationship Id="rId2" Type="{REL}/theme" Target="theme/theme1.xml"/>'
                                                    f'<Relationship Id="rId3" Type="{REL}/presProps" Target="presProps.xml"/>'
                                                    f'<Relationship Id="rId4" Type="{REL}/viewProps" Target="viewProps.xml"/>'
                                                    f'<Relationship Id="rId5" Type="{REL}/tableStyles" Target="tableStyles.xml"/></Relationships>')
        parts["ppt/presProps.xml"] = XMLDECL + f'<p:presentationPr {NSDECL}/>'
        parts["ppt/viewProps.xml"] = XMLDECL + f'<p:viewPr {NSDECL}><p:normalViewPr><p:restoredLeft sz="15620"/><p:restoredTop sz="94660"/></p:normalViewPr><p:gridSpacing cx="76200" cy="76200"/></p:viewPr>'
        parts["ppt/tableStyles.xml"] = XMLDECL + f'<a:tblStyleLst xmlns:a="{A}" def="{{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}}"/>'
        parts["_rels/.rels"] = (XMLDECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                f'<Relationship Id="rId1" Type="{REL}/officeDocument" Target="ppt/presentation.xml"/>'
                                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                                f'<Relationship Id="rId3" Type="{REL}/extended-properties" Target="docProps/app.xml"/></Relationships>')
        parts["docProps/core.xml"] = (XMLDECL + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                                      'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
                                      'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                                      f'<dc:title>{self.L["name"]} template</dc:title><dc:creator>livery_template.py</dc:creator></cp:coreProperties>')
        parts["docProps/app.xml"] = (XMLDECL + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
                                     'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Microsoft Office PowerPoint</Application>'
                                     '<Slides>0</Slides></Properties>')
        exts = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml"}
        defaults = ''.join(f'<Default Extension="{e}" ContentType="{t}"/>' for e, t in exts.items() if any(n.endswith("." + e) for n in parts))
        overrides = (f'<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
                     f'<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
                     + "".join(f'<Override PartName="/ppt/slideLayouts/slideLayout{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>' for i in range(1, len(LAYOUTS) + 1))
                     + '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
                     '<Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>'
                     '<Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>'
                     '<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>'
                     '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                     '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>')
        parts["[Content_Types].xml"] = (XMLDECL + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                                        f'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                                        f'<Default Extension="xml" ContentType="application/xml"/>{defaults}{overrides}</Types>')
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for name in ["[Content_Types].xml", "_rels/.rels"] + sorted(n for n in parts if n not in ("[Content_Types].xml", "_rels/.rels")):
                data = parts[name]
                z.writestr(zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)), data.encode("utf-8") if isinstance(data, str) else data, zipfile.ZIP_DEFLATED)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("livery", type=Path)
    ap.add_argument("-o", "--out", type=Path, help="default: <livery>/template.pptx")
    a = ap.parse_args()
    livery = livery_mod.load(a.livery)
    out = a.out or a.livery / "template.pptx"   # a flavor gets its own, even if it inherited its parent's
    Builder(livery).build(out, a.livery)
    print(f"livery_template: wrote {out} ({len(LAYOUTS)} layouts)")


if __name__ == "__main__":
    main()
