"""Build the NASA livery's marks from nasa.gov's insignia-spherecentered.svg (its middle panel).
usage: python3 -I nasa_marks.py <insignia-spherecentered.svg> <outdir>"""
import re, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
NS = "http://www.w3.org/2000/svg"; ET.register_namespace("", NS)
BLUE, RED = "#0032A0", "#E4002B"            # NASA Blue PMS 286, NASA Red PMS 185 (2024 guide)
root = ET.parse(SRC).getroot()
groups = [g for g in root.findall(f"{{{NS}}}g") if len(list(g.iter())) == 51]
g = groups[1]                                 # the middle panel's insignia (x 944..1600)
CX, CY, R = 1306.44, 442.74, 222.11           # its sphere: m1528.55,442.74 c0,121.83 ... radius 222.11
inner = ET.tostring(g, encoding="unicode").replace(f' xmlns="{NS}"', "")
# a tight box: the swoosh runs past the sphere left (to ~1057) and up-right; measured by rendering
def svg(body, vb, w=None):
    return f'<svg xmlns="{NS}" viewBox="{vb}">{body}</svg>'
def style(sphere, swoosh, white="#fff", rule=None):
    css = f".cls-7{{fill:{sphere}}}.cls-8{{fill:{white}}}.cls-10{{fill:{swoosh}}}"
    ring = (f'<circle cx="{CX}" cy="{CY}" r="{R + 4}" fill="none" stroke="{rule}" stroke-width="8"/>' if rule else "")
    return f"<defs><style>{css}</style></defs>{inner}{ring}"
def run(*a): subprocess.run(a, check=True)
probe = OUT / "_probe.svg"; probe.write_text(svg(style(BLUE, RED), "944 0 660 886"))
run("rsvg-convert", "-z", "1", str(probe), "-o", str(OUT / "_probe.png"))
w, h, x, y = map(int, re.findall(r"\d+", subprocess.run(["magick", str(OUT / "_probe.png"), "-trim", "-format", "%w %h %X %Y", "info:"], capture_output=True, text=True).stdout)[:4])
x0, y0 = 944 + x - 2, y - 2; W, H = w + 4, h + 4
probe.unlink(); (OUT / "_probe.png").unlink()
print("meatball box", x0, y0, W, H, "sphere diameter/box height", 2 * R / H)
VB = f"{x0} {y0} {W} {H}"
marks = {"meatball": style(BLUE, RED),                                   # full color: white, black, gray, silver, photos
         "meatball-rule": style(BLUE, "#A6B6D9", rule="#fff")}           # one color w/ white rule: NASA Blue fields
def fit(src_svg):
    """widen the viewBox to 4x, render at 1 px per unit, and trim its width to the drawing"""
    m = re.search(r'viewBox="([^"]+)"', src_svg); vb = [float(v) for v in m.group(1).split()]
    t = OUT / "_fit.svg"; t.write_text(src_svg.replace(m.group(0), f'viewBox="{vb[0]} {vb[1]} {vb[2] * 4} {vb[3]}"'))
    run("rsvg-convert", "-w", str(int(vb[2] * 4)), str(t), "-o", str(OUT / "_fit.png"))
    w, h, x, y = map(int, re.findall(r"\d+", subprocess.run(["magick", str(OUT / "_fit.png"), "-trim", "-format", "%w %h %X %Y", "info:"], capture_output=True, text=True).stdout)[:4])
    t.unlink(); (OUT / "_fit.png").unlink()
    return src_svg.replace(m.group(0), f'viewBox="{vb[0]:.1f} {vb[1]:.1f} {x + w + 0.01 * vb[3]:.1f} {vb[3]:.1f}"')
def emit(name, src_svg, png_h=240):
    src_svg = fit(src_svg)
    s = OUT / f"_{name}.svg"; s.write_text(src_svg)
    run("rsvg-convert", "-f", "svg", str(s), "-o", str(OUT / f"{name}.svg"))   # cairo: text to outlines
    run("rsvg-convert", "-f", "pdf", str(OUT / f"{name}.svg"), "-o", str(OUT / f"{name}.pdf"))
    run("rsvg-convert", "-h", str(png_h), str(OUT / f"{name}.svg"), "-o", str(OUT / f"{name}.png"))
    s.unlink()
for k, body in marks.items():
    emit(k, svg(body, VB), 480)
# the agency name, one line (the sign-off), and the two-line left identifier (title, closing)
FONT = "font-family:'Helvetica Neue';font-weight:500"
NAME = "National Aeronautics and Space Administration"
def name_svg(color):
    fs = 100; wd = 2380                       # Helvetica Neue Medium at 100: the line is ~2370 wide
    return svg(f'<text x="0" y="{fs * 0.72:.1f}" style="{FONT};font-size:{fs}px;fill:{color}">{NAME}</text>', f"0 -2 {wd} {fs * 0.72 + 4 + 0.22 * fs:.0f}")
D = 2 * R; ruleX = CX + R + 0.306 * D; textX = ruleX + 0.198 * D; fs = 0.153 * D
def ident(color, sphere_style):
    lines = (f'<text style="{FONT};font-size:{fs:.1f}px;fill:{color}"><tspan x="{textX:.1f}" y="{CY + 0.025 * D - 0.075 * D:.1f}">National Aeronautics and</tspan>'
             f'<tspan x="{textX:.1f}" y="{CY + 0.174 * D - 0.075 * D:.1f}">Space Administration</tspan></text>')
    rule = f'<rect x="{ruleX - 0.006 * D:.1f}" y="{CY - R:.1f}" width="{0.012 * D:.1f}" height="{D:.1f}" fill="{color}"/>'
    right = textX + fs * 14
    return svg(sphere_style + rule + lines, f"{x0} {y0} {right - x0:.0f} {H}")
emit("nasa-name", name_svg("#000"), 120); emit("nasa-name-white", name_svg("#fff"), 120)
emit("nasa-identifier", ident("#000", marks["meatball"]))
emit("nasa-identifier-white", ident("#fff", marks["meatball"]))
emit("nasa-identifier-rule", ident("#fff", marks["meatball-rule"]))
