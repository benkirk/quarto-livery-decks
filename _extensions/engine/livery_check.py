"""Check a livery directory before decks are built from it (design section 6, step 3).

    livery check <livery dir>... [--swatch DIR] [--qa]

Per livery: build/ is fresh (livery build --check); every file the data names exists (fonts,
logos, the marks, art, the template, the font blobs when pptx.fonts is set); template.pptx is
pandoc-compliant (the seven layout names and our two extra ones, slideLayout1's five placeholders,
the chrome placeholders at idx 20-22 and no content box there, the color and font schemes
matching the json, media numbered without gaps) and rebuilds byte-identically from the data (a
hand-edited template fails); WCAG 4.5:1 warnings for the small-text roles, which never fail; the chart
colors' checks (livery_charts.py: a generated palette must pass, a published one only warns), and
with --swatch DIR their contact sheet, DIR/charts-<livery>.png (needs Pillow).
Exit 1 on any failure. With --qa (the `livery` command's), the quickstart deck's `make qa` follows."""

import re
import tempfile
import zipfile
from pathlib import Path

import livery as livery_mod
import livery_charts
import livery_build
from livery_build import SLOT_ROLES
from livery_template import EXTRA_LAYOUTS, LAYOUTS, Builder

CHROME = {"dt": 20, "ftr": 21, "sldNum": 22}      # livery_template.py's chrome placeholders
TITLE_PH = {"ctrTitle", "subTitle", "dt", "ftr", "sldNum"}   # pandoc's five for Title Slide
# small text on a field: the pairs that must read (WCAG AA, 4.5:1)
CONTRAST = [("primary-contrast", "background"), ("highlight", "background"), ("muted", "background"),
            ("foreground", "background"), ("foreground", "surface"), ("primary-text", "primary"),
            ("code-text", "surface"), ("alert-text", "surface"), ("foreground", "caution-fill"),
            ("foreground", "table-band")]   # derived blends count as roles here


class Report:
    """A livery's checks as lines: warnings and failures always, a passing check only when verbose,
    then one summary line."""
    def __init__(self, name, verbose=False):
        self.name, self.verbose = name, verbose
        self.n, self.warned, self.failures = 0, 0, 0

    @property
    def failed(self): return self.failures > 0
    def ok(self, what):
        self.n += 1
        if self.verbose:
            print(f"{self.name}: ok    {what}")
    def warn(self, what): self.n += 1; self.warned += 1; print(f"{self.name}: warn  {what}")
    def fail(self, what): self.n += 1; self.failures += 1; print(f"{self.name}: FAIL  {what}")
    def note(self, what): print(f"{self.name}: {what}")
    def check(self, cond, what, detail=""):
        (self.ok if cond else self.fail)(what + (f": {detail}" if detail and not cond else ""))
    def summary(self):
        warned = f", {self.warned} warning{'s' * (self.warned != 1)}" if self.warned else ""
        if self.failures:
            print(f"{self.name}: FAILED ({self.failures} of {self.n} checks{warned})")
        else:
            print(f"{self.name}: ok ({self.n} checks{warned})")


def luminance(hexv):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = bytes.fromhex(hexv.lstrip("#"))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_template(r, livery, d):
    tmpl = d / livery["pptx"].get("template", "template.pptx")
    if not tmpl.exists():
        return
    with zipfile.ZipFile(tmpl) as z:
        names = set(z.namelist())
        read = lambda n: z.read(n).decode("utf8")
        layouts = {}
        for n in sorted(names):
            m = re.fullmatch(r"ppt/slideLayouts/slideLayout(\d+)\.xml", n)
            if m:
                layouts[int(m.group(1))] = read(n)
        found = {re.search(r'<p:cSld name="([^"]*)"', x).group(1): x for x in layouts.values()}
        missing = [l for l in LAYOUTS if l not in found]
        r.check(not missing, "the seven layouts pandoc looks up by name", f"missing {missing}")
        extra = [l for l in EXTRA_LAYOUTS if l not in found]
        r.check(not extra, "Closing, Title Slide (light) and Closing (light), for slide_layout.py", f"missing {extra}: rerun livery template")
        if "Title Slide" in found:
            types = set(re.findall(r'<p:ph [^>]*type="([^"]+)"', found["Title Slide"]))
            r.check(TITLE_PH <= types, "Title Slide has ctrTitle, subTitle, dt, ftr, sldNum", f"missing {sorted(TITLE_PH - types)}")
        bad = []
        for name, x in list(found.items()) + [("master", read("ppt/slideMasters/slideMaster1.xml"))]:
            for ph in re.findall(r"<p:ph\b[^>]*>", x):
                t = re.search(r'type="([^"]+)"', ph); i = re.search(r'idx="(\d+)"', ph)
                t, i = (t.group(1) if t else "body"), (int(i.group(1)) if i else None)
                if t in CHROME and i != CHROME[t]:
                    bad.append(f"{name}: {t} at idx {i}")
                if t not in CHROME and i is not None and i >= 20:
                    bad.append(f"{name}: content box at idx {i}")
        r.check(not bad, "chrome placeholders at idx 20-22, no content box there", "; ".join(bad))
        theme = read("ppt/theme/theme1.xml")
        scheme = {s: v.upper() for s, v in re.findall(r"<a:(\w+)><a:srgbClr val=\"([0-9A-Fa-f]{6})\"/></a:\1>", theme)}
        want = {s: v.lstrip("#").upper() for s, v in livery["pptx"]["scheme"].items()}
        diff = {s: (scheme.get(s), want[s]) for s in SLOT_ROLES if scheme.get(s) != want.get(s)}
        r.check(not diff, "theme1.xml clrScheme is pptx.scheme", str(diff))
        cust = re.findall(r'<a:custClr name="([^"]*)"><a:srgbClr val="([0-9A-Fa-f]{6})"/></a:custClr>', theme)
        want_cust = [(n, c.lstrip("#")) for n, c in livery_charts.custom_colors(livery["charts"])] if livery.get("charts") else []
        r.check(cust == want_cust, "theme1.xml Custom Colors row is the chart colors", f"{cust} != {want_cust}")
        major = re.search(r'<a:majorFont><a:latin typeface="([^"]*)"', theme)
        minor = re.search(r'<a:minorFont><a:latin typeface="([^"]*)"', theme)
        tf, hf = livery["pptx"]["typeface"], livery["pptx"].get("heading-typeface", livery["pptx"]["typeface"])
        r.check(major and minor and major.group(1) == hf and minor.group(1) == tf, "the font scheme is pptx.typeface / heading-typeface",
                f"major {major and major.group(1)!r}, minor {minor and minor.group(1)!r}")
        media = sorted(int(m.group(1)) for n in names if (m := re.fullmatch(r"ppt/media/image(\d+)\.\w+", n)))
        r.check(media == list(range(1, len(media) + 1)), "media numbered image1.. without gaps", str(media))
    with tempfile.TemporaryDirectory() as tmp:
        rebuilt = Path(tmp) / "template.pptx"
        Builder(livery).build(rebuilt, d)
        r.check(rebuilt.read_bytes() == tmpl.read_bytes(), "template.pptx rebuilds byte-identically from the data (not hand-edited)")


def check_livery(d: Path, swatch: Path | None = None, verbose: bool = False) -> bool:
    r = Report(d.name, verbose)
    try:
        stale = [t.name for t, text in livery_build.outputs(d).items() if not t.exists() or t.read_text() != text]
        r.check(not stale, "build/ is fresh", f"stale: {', '.join(stale)} (run livery build {d})")
    except SystemExit as e:   # the build refuses the livery (schema): its message
        r.check(False, "build/ is fresh", str(e).splitlines()[0])
    livery = livery_mod.load(d)
    missing = [f"{what}: {path}" for path, what in livery_mod.files(livery) if not (d / path).exists()]
    r.check(not missing, "every file the data names exists", "; ".join(missing))
    check_template(r, livery, d)
    roles = {**livery["roles"], **livery.get("blends", {})}
    for fg, bg in CONTRAST:
        if fg in roles and bg in roles:
            ratio = contrast(roles[fg], roles[bg])
            (r.ok if ratio >= 4.5 else r.warn)(f"contrast {fg} on {bg}: {ratio:.1f}:1")
    check_charts(r, livery, swatch)
    r.summary()
    return not r.failed


def check_charts(r, livery, swatch=None):
    """The chart colors: every check of livery_charts.evaluate() as a line, a fail failing the livery
    (a published palette's failures arrive as warnings); the contact sheet when asked for."""
    ch = livery.get("charts")
    if not ch:
        r.fail("livery.json has no charts: rerun livery build")
        return
    for line in livery_charts.report(livery["name"], ch)[0:]:
        state, _, rest = line.strip().partition("  ")
        if state in ("pass", "warn", "fail"):
            {"pass": r.ok, "warn": r.warn, "fail": r.fail}[state](f"charts {rest.strip()}")
    if swatch:
        swatch.mkdir(parents=True, exist_ok=True)
        out = swatch / f"charts-{Path(livery['dir']).name}.png"
        livery_charts.swatch(livery["name"], ch, out)
        r.note(f"charts swatch sheet: {out}")


def check(liveries: list[Path], swatch: Path | None = None, verbose: bool = False) -> bool:
    """Every livery's checks (each runs, so all failures print); True when all pass. Quiet unless
    verbose: warnings, failures and a summary line per livery."""
    return all([check_livery(d.resolve(), swatch, verbose) for d in liveries])
