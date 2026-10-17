#!/usr/bin/env python3
"""Build a livery's pandoc-compliant template.pptx from its data (design section 6, step 2).

    livery_template.py <livery dir> [-o template.pptx]

Everything comes from build/livery.json: the theme's color slots (pptx.scheme), the typeface,
the geometry fractions, the marks (marks), art.content and the wave curves on the master, and
the compositions (compositions) of the field layouts: their field, art, band, waves, marks, the
band's default photo and the text column the placeholders are derived from. The master carries
the title with its accent tab and hairline rule, the lockup, the faint wave lines and the
body-size ladder; the seven layouts pandoc looks up by name are generated (Title Slide, Title
and Content, Section Header, Two Content, Comparison, Content with Caption, Blank), the Title
Slide with its five placeholders, then three pandoc never picks (it uses only those names) and
slide_layout.py points slides at: Closing, Title Slide (light) and Closing (light). Fonts are
embedded later by embed_fonts.py; a deck's title photo by slide_layout.py.
Rewrites in place with fixed zip timestamps, so an unchanged rebuild is byte-identical.
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

import livery as livery_mod
import pptx_waves
from livery_build import SLOT_ROLES

# the canvas in EMU: the livery's (livery.json type.canvas, pptx.size), set by Builder; 13.333 x 7.5 in
# by default. The themes think in 1600x900 slide pixels.
W_EMU, H_EMU = 12192000, 6858000
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NSDECL = f'xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"'
XMLDECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
LAYOUTS = ["Title Slide", "Title and Content", "Section Header", "Two Content", "Comparison",
           "Content with Caption", "Blank"]
ROLE_SLOT = pptx_waves.ROLE_SLOT
# carried into every deck by pandoc untouched; slide_layout.py re-points slides at them
EXTRA_LAYOUTS = ["Closing", "Title Slide (light)", "Closing (light)"]
ALL_LAYOUTS = LAYOUTS + EXTRA_LAYOUTS
LAYOUT_TYPES = {"Closing": "obj", "Closing (light)": "obj", "Title Slide (light)": "title", "Title Slide": "title", "Title and Content": "obj", "Section Header": "secHead",
                "Two Content": "twoObj", "Comparison": "twoTxTwoObj", "Content with Caption": "objTx", "Blank": "blank"}


# the layouts drawn from a composition: layout -> (composition, its band variant, kind of text)
FIELD_LAYOUTS = {"Title Slide": ("title", "title-band", "title"), "Title Slide (light)": ("title-light", None, "title"),
                 "Section Header": ("section", None, "section"), "Closing": ("closing", "closing-band", "closing"),
                 "Closing (light)": ("closing-light", None, "closing")}


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
        global W_EMU, H_EMU   # emu() and xfrm() read them
        W_EMU, H_EMU = (livery["type"]["canvas"][k] * 12700 for k in ("w", "h"))
        self.L = livery
        self.geom = livery["geometry"]
        self.roles = livery["roles"]
        self.scheme = livery.get("pptx", {}).get("scheme") or {
            slot: livery["roles"][role] for slot, role in SLOT_ROLES.items() if role in livery["roles"]}
        self.typeface = livery["pptx"]["typeface"]
        self.heading_typeface = livery["pptx"].get("heading-typeface", self.typeface)
        art = livery.get("art") or {}
        self.waves = art.get("waves")
        self.art = {k: art[k] for k in ("title", "section", "content", "closing", "titlegraphic") if isinstance(art.get(k), str)}
        self.signoff = livery.get("signoff")
        self.band = (livery.get("title") or {}).get("style") == "band"
        self.comps = livery["compositions"]
        t = livery["type"]   # type sizes in points on the livery's canvas (hundredths in the xml)
        self.sz = lambda role, scale=1: round(t["roles"][role]["pt"] * scale * 2) * 50
        self.levels = [round(p * 100) for p in t["levels"]]
        # absolute lengths drawn for the 540 pt canvas (indents, insets), scaled onto this one
        self.k = H_EMU / 6858000
        self.logo_corner = self.geom["logo"].get("corner", "top-right")
        self.number_corner = self.geom.get("pagenumber", {}).get("corner", "bottom-left")
        self.sid = 10

    def next_id(self):
        self.sid += 1
        return self.sid

    # ------------------------------------------------------------------ waves
    def own(self, shapes):
        """Shapes from pptx_waves, numbered on from here (the layout root declares the namespaces)."""
        self.sid += len(shapes)
        return [s.replace(f" {pptx_waves.XMLNS}", "") for s in shapes]

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

    def chrome(self, light_text=True, with_date=True, text_role="primary-text"):
        """Slide number, date and footer placeholders (idx 20-22: pandoc matches content by idx too,
        so these must never share a number with a content box)."""
        color = fill("tx1") if light_text else srgb(self.roles[text_role])
        right = self.number_corner == "bottom-right"
        num = (f'<p:sp><p:nvSpPr><p:cNvPr id="{self.next_id()}" name="Slide Number Placeholder"/><p:cNvSpPr>'
               f'<a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="sldNum" sz="quarter" idx="22"/></p:nvPr></p:nvSpPr>'
               f'<p:spPr>{xfrm(0.96 if right else 0.001, 0.945, 0.039, 0.053)}</p:spPr><p:txBody><a:bodyPr anchor="ctr"/><a:lstStyle>'
               f'<a:lvl1pPr algn="ctr"><a:defRPr sz="{self.sz("pagenumber")}" b="1">{color}</a:defRPr></a:lvl1pPr></a:lstStyle>'
               f'<a:p><a:fld id="{{C5EF2332-01BF-834F-8236-50238282D533}}" type="slidenum"><a:rPr lang="en-US"/>'
               f'<a:t>‹#›</a:t></a:fld></a:p></p:txBody></p:sp>')
        dt = self.ph("Date Placeholder", "dt", 20, xfrm(0.74 if right else 0.856, 0.956, 0.113, 0.027),
                     'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"',
                     f'<a:lvl1pPr algn="r"><a:defRPr sz="{self.sz("footer")}">{color}</a:defRPr></a:lvl1pPr>', "", sz="half")
        ftr = self.ph("Footer Placeholder", "ftr", 21, xfrm(0.046, 0.956, 0.34, 0.027),
                      'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"',
                      f'<a:lvl1pPr algn="l"><a:defRPr sz="{self.sz("footer")}">{color}</a:defRPr></a:lvl1pPr>', "", sz="quarter")
        return num + (dt if with_date else "") + ftr

    def pic(self, rid, name, x, y, w, h):
        return (f'<p:pic><p:nvPicPr><p:cNvPr id="{self.next_id()}" name="{name}"/>'
                f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr>'
                f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
                f'<p:spPr>{xfrm(x, y, w, h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')

    def box_pic(self, rid, name, box):
        return self.pic(rid, name, *box)

    def rect(self, name, x, y, w, h, slot):
        return (f'<p:sp><p:nvSpPr><p:cNvPr id="{self.next_id()}" name="{name}"/><p:cNvSpPr/><p:nvPr userDrawn="1"/>'
                f'</p:nvSpPr><p:spPr>{xfrm(x, y, w, h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
                f'{fill(slot)}<a:ln><a:noFill/></a:ln></p:spPr></p:sp>')

    def cover_pic(self, rid, name, path, x, y, w, h):
        """A picture cropped (srcRect) to cover the box, as the themes' object-fit: cover."""
        from PIL import Image
        iw, ih = Image.open(path).size
        box = w * W_EMU / (h * H_EMU)
        lr, tb = (round((1 - box / (iw / ih)) / 2 * 100000), 0) if iw / ih > box else (0, round((1 - (iw / ih) / box) / 2 * 100000))
        crop = f'<a:srcRect l="{lr}" t="{tb}" r="{lr}" b="{tb}"/>' if lr or tb else ""
        return self.pic(rid, name, x, y, w, h).replace('<a:stretch>', crop + '<a:stretch>')

    def art_pic(self, rid, kind):
        """A full-slide picture under everything, or '' when the livery has no art.<kind>."""
        return self.pic(rid, f"Art ({kind})", 0, 0, 1, 1) if kind in self.art else ""

    # ------------------------------------------------------------------ master
    def master(self):
        g = self.geom; m, tab = g["margin"], g["tab"]
        title_top, rule_y, body_top, body_bottom = 0.049, 0.1444, 0.1667, 1 - 0.0778
        logo_h = g["logo"]["height"]; logo_w = logo_h * g["logo"]["aspect"] * H_EMU / W_EMU
        corner = self.logo_corner
        title_x = m + logo_w + 0.025 if corner == "top-left" else m
        title_w = 1 - 2 * m - (logo_w + 0.025 if corner != "none" else 0)
        # the ladder: the livery's five list levels (type.levels), the first the body
        sizes = self.levels
        ind, tabsz, ins = (round(v * self.k) for v in (228600, 457200, 45720))   # 0.25, 0.5, 0.05 in on 7.5 in
        bullets = [("Arial", "•"), ("Wingdings", "§"), ("Courier New", "o"), ("Arial", "–"), ("Arial", "»")]
        body_lvls = ""
        for i, (sz, (bfont, bchar)) in enumerate(zip(sizes, bullets), 1):
            mar = ind * i
            # the space before an item, as HTML's list-item margins: a share of the body
            spc = f'<a:spcBef><a:spcPts val="{round(sizes[0] * (0.5 if i == 1 else 0.3))}"/></a:spcBef>'
            body_lvls += (f'<a:lvl{i}pPr marL="{mar}" indent="-{ind}" algn="l" defTabSz="{tabsz}" rtl="0" eaLnBrk="1" '
                          f'latinLnBrk="0" hangingPunct="1"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc>{spc}'
                          f'<a:buFont typeface="{bfont}"/><a:buChar char="{bchar}"/><a:defRPr sz="{sz}" kern="1200">'
                          f'{fill("tx1")}<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/>'
                          f'</a:defRPr></a:lvl{i}pPr>')
        for i in range(len(sizes) + 1, 10):
            body_lvls += (f'<a:lvl{i}pPr marL="{ind * i}" indent="-{ind}" algn="l"><a:defRPr sz="{sizes[-1]}" kern="1200">'
                          f'{fill("tx1")}<a:latin typeface="+mn-lt"/></a:defRPr></a:lvl{i}pPr>')
        other = "".join(f'<a:lvl{i}pPr marL="{tabsz * (i - 1)}" algn="l" defTabSz="{tabsz}"><a:defRPr sz="{self.sz("table")}" kern="1200">'
                        f'{fill("tx1")}<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/>'
                        f'</a:defRPr></a:lvl{i}pPr>' for i in range(1, 10))
        tab_sp = (f'<p:sp><p:nvSpPr><p:cNvPr id="{self.next_id()}" name="Title tab"/><p:cNvSpPr/><p:nvPr userDrawn="1"/>'
                  f'</p:nvSpPr><p:spPr>{xfrm(0, title_top, tab, rule_y - title_top)}<a:prstGeom prst="rect"><a:avLst/>'
                  f'</a:prstGeom>{fill("accent4")}<a:ln><a:noFill/></a:ln></p:spPr></p:sp>')
        rule = (f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{self.next_id()}" name="Title rule"/><p:cNvCxnSpPr/>'
                f'<p:nvPr userDrawn="1"/></p:nvCxnSpPr><p:spPr>{xfrm(m, rule_y, 1 - 2 * m, 0)}'
                f'<a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:ln w="9525">{fill("tx1", 30000)}</a:ln></p:spPr></p:cxnSp>')
        title = self.ph("Title Placeholder", "title", None, xfrm(title_x, title_top, title_w, rule_y - title_top),
                        'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"><a:normAutofit/><a:x',
                        "", "Click to edit Master title style")
        # (the bodyPr trick above closes the element; restate it plainly)
        title = title.replace('<a:bodyPr vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"><a:normAutofit/><a:x/>',
                              '<a:bodyPr vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"><a:normAutofit/></a:bodyPr>')
        body = self.ph("Text Placeholder", "body", 1, xfrm(m, body_top, 1 - 2 * m, body_bottom - body_top),
                       f'vert="horz" lIns="0" tIns="{ins}" rIns="0" bIns="{ins}"><a:normAutofit/></a:bodyPr><a:lstStyle/>'
                       '<a:p><a:pPr lvl="0"/><a:r><a:rPr lang="en-US"/><a:t>Click to edit Master text styles</a:t></a:r></a:p>'
                       '</p:txBody></p:sp><!--', "", "")
        body = body.split("<!--")[0]
        waves = "".join(self.own(pptx_waves.wave_shapes(self.waves["lines"], self.sid + 1, W_EMU, H_EMU,
                                                        self.waves["shift"]["content"], "lt2"))) if self.waves else ""
        art = self.art_pic("rId4", "content")   # under everything (the layouts with a field hide the master)
        logo = "" if corner == "none" else self.pic("rId2", "Logo (light)", m if corner == "top-left" else 1 - m - logo_w,
                                                    g["logo"]["top"], logo_w, logo_h)
        so = ""
        if self.signoff:   # the content slides' sign-off, the light one in its corner
            h = self.signoff["height"]; w = h * self.signoff["aspect"] * H_EMU / W_EMU
            x = m if self.signoff["corner"] == "bottom-left" else 1 - m - w
            so = self.pic("rId3", "Sign-off (light)", x, 1 - self.signoff["bottom"] - h, w, h)
        shapes = art + waves + tab_sp + rule + title + body + self.chrome() + logo + so
        return (XMLDECL + f'<p:sldMaster {NSDECL}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
                f'<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                f'<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
                f'</a:xfrm></p:grpSpPr>{shapes}</p:spTree></p:cSld>'
                f'<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
                f'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
                f'<p:sldLayoutIdLst>' + "".join(f'<p:sldLayoutId id="{2147483649 + i}" r:id="rId{10 + i}"/>' for i in range(len(ALL_LAYOUTS))) +
                f'</p:sldLayoutIdLst><p:txStyles><p:titleStyle><a:lvl1pPr algn="l" defTabSz="{tabsz}" rtl="0" eaLnBrk="1" '
                f'latinLnBrk="0" hangingPunct="1"><a:spcBef><a:spcPct val="0"/></a:spcBef><a:buNone/>'
                f'<a:defRPr sz="{self.sz("frametitle")}" b="1" kern="1200" baseline="0">{fill("tx1")}<a:latin typeface="+mj-lt"/>'
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

    def field_text(self, size, bold=False, caps=False, role="primary-text"):
        """A lstStyle for text on the brand field, in the primary-text role (or another)."""
        return (f'<a:lvl1pPr algn="l" marL="0" indent="0"><a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/>'
                f'<a:defRPr sz="{self.sz(size)}" b="{1 if bold else 0}"{" cap=\"all\"" if caps else ""}>'
                f'{srgb(self.roles[role])}<a:latin typeface="+mn-lt"/></a:defRPr></a:lvl1pPr>')

    def column(self, c, kind):
        """The text placeholders, derived from the composition's column: a title's date, title (with
        its tab), rule and subtitle stacked from the column's top, or centred on its middle; a
        closing's headline (bottom-anchored) over its body; a section's title and subtitle about
        the column's middle (section_subtitle.py places them on each slide)."""
        col = c["column"]; x, y, w, h = col["box"]; role = col["role"]
        no_inset = 'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="{}"><a:normAutofit/></a:bodyPr><a:lstStyle>'
        tab = lambda ty, th: [self.rect("Title tab", 0, ty, self.geom["tab"], th, "accent4")] if col["tab"] else []
        out = []
        if kind == "title":
            if col["anchor"] == "middle":   # the band: the title down to the rule at the middle, the subtitle under it
                t_h = 0.14; mid = y + h / 2; t_y = mid - 0.015 - t_h; rule_y, sub_y, t_anchor = mid, mid + 0.02, "b"
                dt = (x, y, w, 0.04); sub_h = y + h - 0.02 - sub_y
            else:   # from the top: the brand template's stack (date, title, rule, subtitle to the column's foot)
                t_y, t_h, rule_y, sub_y, t_anchor = y + 0.055, 0.16, y + 0.24, y + 0.265, "t"
                dt = (x, y, w, 0.045); sub_h = y + h - sub_y
            out += tab(t_y, t_h)
            out.append(self.ph("Date", "dt", 20, xfrm(*dt), no_inset.format("t") + self.field_text("date", bold=True, caps=True, role=role)
                               + "</a:lstStyle><a:p><a:fld id=\"{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}\" type=\"datetime1\"><a:rPr lang=\"en-US\"/><a:t>Date</a:t></a:fld></a:p></p:txBody></p:sp><!--",
                               "", "").split("<!--")[0])
            out.append(self.ph("Title", "ctrTitle", None, xfrm(x, t_y, w, t_h),
                               f'{no_inset.format(t_anchor)}{self.field_text("title", bold=True, role=role)}</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Title</a:t></a:r></a:p></p:txBody></p:sp><!--',
                               "", "").split("<!--")[0])
            if col["rule"]:
                out.append(f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{self.next_id()}" name="Title rule"/><p:cNvCxnSpPr/><p:nvPr userDrawn="1"/>'
                           f'</p:nvCxnSpPr><p:spPr>{xfrm(x, rule_y, col["rule"][0], 0)}<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
                           f'<a:ln w="{round(col["rule"][1] * H_EMU)}">{fill("accent1")}</a:ln></p:spPr></p:cxnSp>')
            out.append(self.ph("Subtitle", "subTitle", 1, xfrm(x, sub_y, w, sub_h),
                               no_inset.format("t") + self.field_text("subtitle", role=role) + '</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Subtitle</a:t></a:r></a:p></p:txBody></p:sp><!--',
                               "", "").split("<!--")[0])
        elif kind == "closing":   # split at the middle: a short headline and body sit on the column's centre
            hh = 0.5 * h
            out += tab(y + hh - 0.09, 0.075)
            out.append(self.ph("Title 1", "title", None, xfrm(x, y, w, hh),
                               no_inset.format("b") + f'<a:lvl1pPr algn="l"><a:lnSpc><a:spcPct val="90000"/></a:lnSpc><a:defRPr sz="{self.sz("closing")}" b="1">{srgb(self.roles[role])}'
                               '<a:latin typeface="+mj-lt"/></a:defRPr></a:lvl1pPr></a:lstStyle><a:p><a:r><a:rPr lang="en-US"/>'
                               '<a:t>Thank you</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "").split("<!--")[0])
            lvls = "".join(f'<a:lvl{i}pPr><a:defRPr sz="{self.levels[i - 1]}">{srgb(self.roles[role])}</a:defRPr></a:lvl{i}pPr>'
                           for i in (1, 2, 3))
            out.append(self.ph("Content Placeholder 2", None, 1, xfrm(x, y + hh + 0.03, w, h - hh - 0.03),
                               no_inset.format("t") + lvls + '</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Contact details</a:t></a:r></a:p></p:txBody></p:sp><!--',
                               "", "").split("<!--")[0])
        else:   # section
            mid = y + h / 2
            title_lst = (f'<a:lvl1pPr algn="l"><a:lnSpc><a:spcPct val="90000"/></a:lnSpc><a:defRPr sz="{self.sz("section")}" b="1" cap="none" baseline="0">'
                         f'{srgb(self.roles[role])}<a:latin typeface="+mj-lt"/></a:defRPr></a:lvl1pPr>')
            out.append(self.ph("Title 1", "title", None, xfrm(x, mid - 0.12, w, 0.12),
                               'lIns="0" tIns="0" rIns="0" bIns="0" anchor="b"><a:normAutofit/></a:bodyPr><a:lstStyle>' + title_lst +
                               '</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Section title</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "").split("<!--")[0])
            out.append(self.ph("Text Placeholder 2", "body", 1, xfrm(x, mid + 0.01, w, 0.133),
                               'lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:normAutofit/></a:bodyPr><a:lstStyle>' + self.field_text("sectionsubtitle", role=role) +
                               '</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Subtitle</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "").split("<!--")[0])
        return out

    def comp_name(self, name):
        base, band, _ = FIELD_LAYOUTS[name]
        return band if self.band and band else base

    def field_layout(self, name, livery_dir):
        """A layout drawn from its composition: the art, the waves (or a straight field), the band
        with the default photo in its box, the mark and sign-off in theirs (rId4, rId5, rId2, rId3),
        the column's placeholders, the slide number."""
        c, kind = self.comps[self.comp_name(name)], FIELD_LAYOUTS[name][2]
        field = ROLE_SLOT[c["field"]["role"]]
        shapes = [self.pic("rId4", f"Art ({c['art']})", 0, 0, 1, 1)] if c["art"] else []
        if c["band"]:
            shapes.append(self.rect("Title band", *c["band"]["box"], ROLE_SLOT[c["band"]["role"]]))
            if "titlegraphic" in self.art and c["photo"]:
                shapes.append(self.cover_pic("rId5", "Title photo", Path(livery_dir) / self.art["titlegraphic"], *c["photo"]["box"]))
        shapes += self.own(pptx_waves.comp_shapes(self.waves and self.waves["lines"], c, self.sid + 1, W_EMU, H_EMU, field,
                                                  ROLE_SLOT[c["waves"]["role"]] if c["waves"] else "accent1"))
        for key, rid, label in (("mark", "rId2", "Logo"), ("signoff", "rId3", "Sign-off")):
            if c[key]:
                shapes.append(self.box_pic(rid, f"{label} ({c[key]['role']})", c[key]["box"]))
        shapes += self.column(c, kind)
        shapes.append(self.chrome(light_text=False, with_date=kind != "title", text_role=c["column"]["role"]))
        return self.layout(name, shapes, bg=fill(field), show_master=False)

    def media_for(self, name):
        """{rId: media name} a field layout's composition wears: its mark, sign-off, art and photo."""
        c, out = self.comps[self.comp_name(name)], {}
        if c["mark"]:
            out["rId2"] = f"mark-{c['mark']['role']}"
        if c["signoff"]:
            out["rId3"] = f"signoff-{c['signoff']['role']}"
        if c["art"]:
            out["rId4"] = f"art-{c['art']}"
        if c["band"] and c["photo"] and "titlegraphic" in self.art:
            out["rId5"] = "photo"
        return out

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
            head_lst = f'<a:lvl1pPr marL="0" indent="0"><a:buNone/><a:defRPr sz="{self.sz("subhead")}" b="1">{fill("tx2")}</a:defRPr></a:lvl1pPr>'
            for i, (idx_head, idx_body, x) in enumerate(((1, 11, m), (3, 2, m + half + 0.03))):
                shapes.append(self.ph(f"Text Placeholder {i + 2}", "body", idx_head, xfrm(x, body_top, half, head_h),
                                      'vert="horz" anchor="b"><a:normAutofit/></a:bodyPr><a:lstStyle>' + head_lst +
                                      '</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>Heading</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "", sz="quarter" if i else None).split("<!--")[0])
                shapes.append(self.ph(f"Content Placeholder {i + 4}", None, idx_body, xfrm(x, body_top + head_h + 0.01, half, h - head_h - 0.01), 'vert="horz"', "", "Content", sz="half"))
        elif name == "Content with Caption":
            cap_w = 0.33
            shapes[0] = self.ph("Title 1", "title", None, xfrm(m, body_top, cap_w, 0.13),
                                'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0" anchor="b"><a:normAutofit/></a:bodyPr><a:lstStyle>'
                                f'<a:lvl1pPr algn="l"><a:defRPr sz="{self.sz("subhead")}" b="1"/></a:lvl1pPr></a:lstStyle><a:p><a:r><a:rPr lang="en-US"/>'
                                '<a:t>Caption title</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "").split("<!--")[0]
            shapes.append(self.ph("Content Placeholder 2", None, 1, xfrm(m + cap_w + 0.03, body_top, 1 - 2 * m - cap_w - 0.03, h), 'vert="horz"', "", "Content"))
            shapes.append(self.ph("Text Placeholder 3", "body", 2, xfrm(m, body_top + 0.14, cap_w, h - 0.14),
                                  'vert="horz" lIns="0" tIns="0" rIns="0" bIns="0"><a:normAutofit/></a:bodyPr><a:lstStyle>'
                                  f'<a:lvl1pPr marL="0" indent="0"><a:buNone/><a:defRPr sz="{self.sz("table")}"/></a:lvl1pPr></a:lstStyle><a:p><a:r><a:rPr lang="en-US"/>'
                                  '<a:t>Caption</a:t></a:r></a:p></p:txBody></p:sp><!--', "", "", sz="half").split("<!--")[0])
        elif name == "Blank":
            shapes = []
        shapes.append(self.chrome())
        return self.layout(name, shapes)

    # -------------------------------------------------------------------- parts
    def theme(self):
        cs = "".join(f'<a:{slot}><a:srgbClr val="{self.scheme[slot].lstrip("#")}"/></a:{slot}>' for slot in SLOT_ROLES if slot in self.scheme)
        tf, hf = self.typeface, self.heading_typeface
        fs = (f'<a:fontScheme name="{tf}"><a:majorFont><a:latin typeface="{hf}"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
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
        # media, numbered in this order: the master's mark, sign-off and art, then each field layout's
        mark = lambda role, kind="logo": livery_mod.mark(self.L, role, kind)
        names = ["mark-background"] + (["signoff-background"] if self.signoff else []) + (["art-content"] if "content" in self.art else [])
        names += [n for lay in FIELD_LAYOUTS for n in self.media_for(lay).values()]
        def path_of(n):
            kind, _, key = n.partition("-")
            return (mark(key) if kind == "mark" else mark(key, "signoff") if kind == "signoff"
                    else self.art[key] if kind == "art" else self.art["titlegraphic"])
        part_of, by_path = {}, {}   # one media part per file: a lockup serving two roles is stored once
        for name in dict.fromkeys(names):
            rel_path = path_of(name)
            f = Path(livery_dir) / rel_path
            if rel_path not in by_path:
                by_path[rel_path] = f"image{len(by_path) + 1}{f.suffix}"
                parts["ppt/media/" + by_path[rel_path]] = f.read_bytes()
            part_of[name] = by_path[rel_path]
        image_rel = lambda rid, name: f'<Relationship Id="{rid}" Type="{REL}/image" Target="../media/{part_of[name]}"/>'
        parts["ppt/theme/theme1.xml"] = self.theme()
        parts["ppt/slideMasters/slideMaster1.xml"] = self.master()
        rels = [f'<Relationship Id="rId1" Type="{REL}/theme" Target="../theme/theme1.xml"/>', image_rel("rId2", "mark-background")]
        if self.signoff:
            rels.append(image_rel("rId3", "signoff-background"))
        if "content" in self.art:
            rels.append(image_rel("rId4", "art-content"))
        rels += [f'<Relationship Id="rId{10 + i}" Type="{REL}/slideLayout" Target="../slideLayouts/slideLayout{i + 1}.xml"/>' for i in range(len(ALL_LAYOUTS))]
        parts["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = XMLDECL + f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(rels)}</Relationships>'
        for i, name in enumerate(ALL_LAYOUTS, 1):
            self.sid = 10
            xml = self.field_layout(name, livery_dir) if name in FIELD_LAYOUTS else self.content_layout(name)
            parts[f"ppt/slideLayouts/slideLayout{i}.xml"] = xml
            r = [f'<Relationship Id="rId1" Type="{REL}/slideMaster" Target="../slideMasters/slideMaster1.xml"/>']
            if name in FIELD_LAYOUTS:
                r += [image_rel(rid, m) for rid, m in self.media_for(name).items()]
            parts[f"ppt/slideLayouts/_rels/slideLayout{i}.xml.rels"] = XMLDECL + f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(r)}</Relationships>'
        parts["ppt/presentation.xml"] = (XMLDECL + f'<p:presentation {NSDECL} saveSubsetFonts="1" autoCompressPictures="0">'
                                         f'<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst/>'
                                         f'<p:sldSz cx="{W_EMU}" cy="{H_EMU}"{' type="screen16x9"' if (W_EMU, H_EMU) == (9144000, 5143500) else ""}/><p:notesSz cx="6858000" cy="9144000"/>'
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
                     + "".join(f'<Override PartName="/ppt/slideLayouts/slideLayout{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>' for i in range(1, len(ALL_LAYOUTS) + 1))
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
    print(f"livery_template: wrote {out} ({len(ALL_LAYOUTS)} layouts)")


if __name__ == "__main__":
    main()
