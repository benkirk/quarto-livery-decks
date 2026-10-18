"""A livery's chart colors: categorical, families, sequential, diverging, status, muted, per mode.

livery_build.py calls charts() from resolve(); the result is livery.json `charts`
(design/charts-and-plots.md). Pure Python, deterministic: a build needs no matplotlib or numpy.

The method is the dataviz color formula: a categorical palette is at most 8 fixed slots that pass
a lightness band, a chroma floor, adjacent separation under protan and deutan color blindness
(Machado, Oliveira and Fernandes 2009, severity 1), a normal-vision floor and 3:1 contrast on the
surface; dark is selected from the same hues for its own surface, never a flipped light palette.
Distances are OKLab x100 (Björn Ottosson's OKLab). A brand's published palette (livery.yml
charts.categorical, .ramps, .sets) is the authority and is kept as given, its check results
reported; a generated one is built to pass.

    livery_charts.py <livery dir>...   print each livery's selections and their checks
"""

import itertools
import math
import sys

# -- color science -------------------------------------------------------------------------------

def _s2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lin2s(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def rgb(h: str) -> tuple[float, float, float]:
    """'#RRGGBB' -> sRGB channels in 0..1."""
    return tuple(b / 255 for b in bytes.fromhex(h.lstrip("#")[:6]))


def lin(h: str):
    return tuple(_s2lin(c) for c in rgb(h))


def hexof(lin_rgb) -> str:
    """Linear RGB (clamped) -> '#RRGGBB'."""
    return "#" + "".join(f"{round(_lin2s(min(max(c, 0.0), 1.0)) * 255):02X}" for c in lin_rgb)


def _lin2lab(r, g, b):
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def _lab2lin(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def oklab(h: str):
    return _lin2lab(*lin(h))


def oklch(h: str) -> tuple[float, float, float]:
    """(L, C, hue in degrees)."""
    L, a, b = oklab(h)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def _in_gamut(c, eps=1e-6):
    return all(-eps <= x <= 1 + eps for x in c)


def from_oklch(L: float, C: float, h: float) -> str:
    """The OKLCH color, its chroma reduced (hue and lightness held) until it is inside sRGB."""
    L = min(max(L, 0.0), 1.0)
    a, b = math.cos(math.radians(h)), math.sin(math.radians(h))
    if _in_gamut(_lab2lin(L, C * a, C * b)):
        return hexof(_lab2lin(L, C * a, C * b))
    lo, hi = 0.0, C
    for _ in range(30):   # bisect the largest in-gamut chroma
        mid = (lo + hi) / 2
        (lo, hi) = (mid, hi) if _in_gamut(_lab2lin(L, mid * a, mid * b)) else (lo, mid)
    return hexof(_lab2lin(L, lo * a, lo * b))


def mix(a: str, b: str, t: float) -> str:
    """a moved toward b by t (0..1) in OKLab."""
    A, B = oklab(a), oklab(b)
    return hexof(_lab2lin(*(x + (y - x) * t for x, y in zip(A, B))))


def luminance(h: str) -> float:
    r, g, b = lin(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG 2 contrast ratio."""
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# Machado, Oliveira and Fernandes (2009), severity 1.0, applied to linear RGB
MACHADO = {
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}


def _sim(h: str, kind: str | None):
    c = lin(h)
    if kind is None:
        return c
    return tuple(min(max(sum(m * x for m, x in zip(row, c)), 0.0), 1.0) for row in MACHADO[kind])


def delta_e(a: str, b: str, kind: str | None = None) -> float:
    """OKLab distance x100, under normal vision (kind None) or simulated protan, deutan, tritan."""
    return 100 * math.dist(_lin2lab(*_sim(a, kind)), _lin2lab(*_sim(b, kind)))


def cvd_e(a: str, b: str) -> float:
    """The worse of protan and deutan."""
    return min(delta_e(a, b, "protan"), delta_e(a, b, "deutan"))


def hue_gap(h1: float, h2: float) -> float:
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


# -- the checks ----------------------------------------------------------------------------------

BAND = {"light": (0.43, 0.77), "dark": (0.48, 0.67)}   # OKLCH L of a categorical mark
CHROMA_FLOOR = 0.10            # below it a hue reads as gray
CVD_TARGET, CVD_FLOOR = 8.0, 6.0
NORMAL_FLOOR = 15.0            # a hard gate: full-color readers must tell neighbors apart
CONTRAST_MIN = 3.0             # marks on the surface (WCAG 1.4.11)
ORDINAL_DL, ORDINAL_END = 0.06, 2.0
MIDPOINT_MIN = 1.6             # a diverging neutral must still show on its surface
MUTED_CONTRAST = 1.8           # "Others": recedes, but is not the surface


def check_categorical(pal: list[str], mode: str, surface: str, pairs: str = "adjacent") -> dict:
    """The six checks' computable five: {check: (state, detail)}, state pass | warn | fail."""
    lo, hi = BAND[mode]
    res = {}
    off = [c for c in pal if not lo <= oklch(c)[0] <= hi]
    res["band"] = ("fail" if off else "pass", f"outside L {lo}-{hi}: {off}" if off else f"all in L {lo}-{hi}")
    gray = [c for c in pal if oklch(c)[1] < CHROMA_FLOOR]
    res["chroma"] = ("fail" if gray else "pass", f"below C {CHROMA_FLOOR}: {gray}" if gray else f"all C >= {CHROMA_FLOOR}")
    idx = ([(i, j) for i in range(len(pal)) for j in range(i + 1, len(pal))] if pairs == "all"
           else [(i, i + 1) for i in range(len(pal) - 1)])
    if idx:
        cvd = min((cvd_e(pal[i], pal[j]), pal[i], pal[j]) for i, j in idx)
        nv = min((delta_e(pal[i], pal[j]), pal[i], pal[j]) for i, j in idx)
        state = "pass" if cvd[0] >= CVD_TARGET else "warn" if cvd[0] >= CVD_FLOOR else "fail"
        res["cvd"] = (state, f"worst {pairs} {cvd[1]}/{cvd[2]} dE {cvd[0]:.1f}")
        res["normal"] = ("pass" if nv[0] >= NORMAL_FLOOR else "fail", f"worst {pairs} {nv[1]}/{nv[2]} dE {nv[0]:.1f}")
    low = [(c, round(contrast(c, surface), 2)) for c in pal if contrast(c, surface) < CONTRAST_MIN]
    res["contrast"] = ("warn" if low else "pass", f"below {CONTRAST_MIN}:1 (needs labels): {low}" if low else f"all >= {CONTRAST_MIN}:1")
    return res


def check_ordinal(ramp: list[str], surface: str) -> dict:
    """A one-hue ramp: monotone lightness, visible steps, a pale end that still shows."""
    Ls = [oklch(c)[0] for c in ramp]
    up = all(a < b for a, b in zip(Ls, Ls[1:]))
    down = all(a > b for a, b in zip(Ls, Ls[1:]))
    res = {"monotone": ("pass" if up or down else "fail", f"L {[round(v, 3) for v in Ls]}")}
    thin = [(ramp[i], ramp[i + 1]) for i in range(len(ramp) - 1) if abs(Ls[i + 1] - Ls[i]) < ORDINAL_DL]
    res["steps"] = ("fail" if thin else "pass", f"closer than dL {ORDINAL_DL}: {thin}" if thin else f"all dL >= {ORDINAL_DL}")
    end = min(ramp, key=lambda c: contrast(c, surface))
    cr = contrast(end, surface)
    res["end"] = ("pass" if cr >= ORDINAL_END else "warn", f"{end} at {cr:.2f}:1")
    return res


def _published(res: dict) -> dict:
    """A brand's own palette is the authority: its failures are reported as warnings, not fixed."""
    return {k: ("warn", d + " (published)") if s == "fail" else (s, d) for k, (s, d) in res.items()}


def worst(res: dict) -> str:
    states = [s for s, _ in res.values()]
    return "fail" if "fail" in states else "warn" if "warn" in states else "pass"


# -- selection -----------------------------------------------------------------------------------

FAMILY = 22.0       # hues closer than this many degrees are one family
NEUTRAL = 0.045     # below this chroma a color is a neutral, not a hue
SLOTS = 8
STEPS = (0.94, 0.86, 0.77, 0.68, 0.59, 0.50, 0.41)   # a generated ramp's lightness, 100..700
STATUS_HUES = {"good": 150.0, "warning": 85.0, "serious": 55.0, "critical": 27.0}


def _norm(v, palette, roles, where):
    """A role, palette name or hex -> '#RRGGBB'."""
    if isinstance(v, str) and v.startswith("#"):
        return v.upper()
    if v in roles:
        return roles[v].upper()
    if v in palette:
        return palette[v].upper()
    raise ValueError(f"charts.{where}: {v!r} is neither a role, a palette name nor a hex value")


def _feasible(mode: str, surface: str, h: float, C: float):
    """The L values (0.01 steps) inside the mode's band where a mark of hue h clears 3:1 on the
    surface; the whole band when none does (contrast then warns)."""
    lo, hi = BAND[mode]
    lo, hi = lo + 0.01, hi - 0.01   # inside the band: 8-bit rounding must not carry a mark across its edge
    Ls = [round(lo + 0.01 * i, 2) for i in range(int(round((hi - lo) / 0.01)) + 1)]
    ok = [L for L in Ls if contrast(from_oklch(L, C, h), surface) >= CONTRAST_MIN + 0.05]
    return ok or Ls


def _slot(color: str, mode: str, surface: str) -> str:
    """A hue as a categorical mark: its own color when it passes, else its lightness moved to the
    nearest feasible L and its chroma raised to the floor, hue held."""
    L, C, h = oklch(color)
    lo, hi = BAND[mode]
    if lo <= L <= hi and C >= CHROMA_FLOOR and contrast(color, surface) >= CONTRAST_MIN:
        return color
    C = max(C, CHROMA_FLOOR + 0.01)
    feas = _feasible(mode, surface, h, C)
    L = min(feas, key=lambda v: abs(v - L))
    out = from_oklch(L, C, h)
    if oklch(out)[1] < CHROMA_FLOOR:   # gamut-clipped below the floor at that L: find an L that keeps it
        cands = [v for v in feas if oklch(from_oklch(v, C, h))[1] >= CHROMA_FLOOR]
        if cands:
            out = from_oklch(min(cands, key=lambda v: abs(v - L)), C, h)
    return out


def _generate(have: list[str], n: int, mode: str, surface: str, chroma: float, avoid: list) -> list[str]:
    """n more hues, each the candidate farthest (worst of normal, protan, deutan) from those
    chosen, never within FAMILY degrees of a chosen hue or inside an avoided range."""
    lo, hi = BAND[mode]
    out = []
    for _ in range(n):
        hues = [oklch(c)[2] for c in have + out]
        best = None
        for h in range(0, 360, 3):
            if any(hue_gap(h, x) < FAMILY for x in hues) or any(hue_gap(h, a["hue"]) <= a.get("width", 30) / 2 for a in avoid):
                continue
            for L in _feasible(mode, surface, h, chroma)[::3]:
                if not lo <= L <= hi:
                    continue
                c = from_oklch(L, chroma, h)
                if oklch(c)[1] < CHROMA_FLOOR:
                    continue
                d = min(min(delta_e(c, p), cvd_e(c, p)) for p in have + out) if have + out else 99
                if best is None or d > best[0]:
                    best = (d, c)
        if best is None:
            break
        out.append(best[1])
    return out


def _order(pal: list[str], n_brand: int) -> list[str]:
    """Slot 1 stays the first brand hue; the other brand hues come next, the generated ones last
    (brand-led), each group in the order that maximizes the worst adjacent separation under color
    blindness, among the orders whose every neighbor clears the normal-vision floor (if any do).
    Deterministic: ties keep the earlier permutation."""
    head, brand, gen = pal[:1], pal[1:n_brand], pal[max(n_brand, 1):]
    nv = {(a, b): delta_e(a, b) for a in pal for b in pal}
    cv = {(a, b): cvd_e(a, b) for a in pal for b in pal}
    best, key = pal, None
    for pb, pg in itertools.product(itertools.permutations(brand), itertools.permutations(gen)):
        seq = head + list(pb) + list(pg)
        if len(seq) < 2:
            return seq
        prs = list(zip(seq, seq[1:]))
        k = (min(nv[p] for p in prs) >= NORMAL_FLOOR, min(cv[p] for p in prs), min(nv[p] for p in prs))
        if key is None or k > key:
            best, key = seq, k
    return best


def _nudge(pal: list[str], mode: str, surface: str) -> list[str]:
    """Snap to passing: while a neighbor pair falls short, move one slot's lightness within its
    feasible range (hue and chroma held) to the value that best lifts the worst pair."""
    pal = list(pal)
    for _ in range(4 * len(pal)):
        prs = [(i, i + 1) for i in range(len(pal) - 1)]
        score = lambda p: min(min(cvd_e(p[i], p[j]) / CVD_TARGET, delta_e(p[i], p[j]) / NORMAL_FLOOR) for i, j in prs)
        cur = score(pal)
        if cur >= 1:
            break
        i, j = min(prs, key=lambda q: min(cvd_e(pal[q[0]], pal[q[1]]) / CVD_TARGET, delta_e(pal[q[0]], pal[q[1]]) / NORMAL_FLOOR))
        best = (cur, None, None)
        for k in (j, i):   # prefer moving the later slot: slot 1 is the brand's own
            if k == 0:
                continue
            L, C, h = oklch(pal[k])
            for v in _feasible(mode, surface, h, max(C, CHROMA_FLOOR + 0.01)):
                trial = pal[:k] + [from_oklch(v, max(C, CHROMA_FLOOR + 0.01), h)] + pal[k + 1:]
                if oklch(trial[k])[1] < CHROMA_FLOOR:
                    continue
                s = score(trial)
                if s > best[0] + 1e-9:
                    best = (s, k, trial[k])
        if best[1] is None:
            break
        pal[best[1]] = best[2]
    return pal


def _ramp(color: str) -> list[str]:
    """A 7-step ramp, light to dark, on the color's hue; the step nearest the color is the color.
    Lighter steps lose chroma toward white, darker ones keep it (gamut-clipped)."""
    L0, C0, h = oklch(color)
    shift = min((s - L0 for s in STEPS), key=abs)
    out = []
    for s in STEPS:
        L = min(max(s - shift, 0.25), 0.97)
        if abs(L - L0) < 1e-9:
            out.append(color.upper())
            continue
        C = C0 * (1 - L) / (1 - L0) if L > L0 else C0
        out.append(from_oklch(L, C, h))
    return out


def _families(cat: list[str], surface: str, ramps: dict, mode: str) -> list[list[str]]:
    """Each categorical color with two tints toward the surface: on light a third and two thirds of
    the way, as the NCAR web theme's -33 and -66 steps; on dark less far (0.3, 0.55), or the pale
    end sinks into the surface. A brand ramp's step stands in for a tint it is within dE 3 of."""
    steps = [c for r in ramps.values() for c in r]
    out = []
    for c in cat:
        fam = [c]
        for t in ((1 / 3, 2 / 3) if mode == "light" else (0.3, 0.55)):
            m = mix(c, surface, t)
            near = min(steps, key=lambda s: delta_e(s, m)) if steps else None
            fam.append(near if near and delta_e(near, m) < 3 else m)
        out.append(fam)
    return out


def _neutral(muted: str, surface: str, target: float) -> str:
    """A near-gray on muted's hue whose contrast with the surface is closest to target, on the
    foreground's side of the surface."""
    L0, _, h = oklch(muted)
    Ls = oklch(surface)[0]
    sign = 1 if L0 > Ls else -1
    best = None
    for i in range(1, 100):
        c = from_oklch(Ls + sign * i * 0.005, 0.012, h)
        d = abs(contrast(c, surface) - target)
        if best is None or d < best[0]:
            best = (d, c)
    return best[1]


def _diverging(lo_pole: str, hi_pole: str, mode: str, surface: str, muted: str) -> list[str]:
    """Five steps: a pole, a paler step, a neutral midpoint, a paler step, the other pole. Light:
    poles at their mark lightness, the midpoint near the surface's paper (L 0.90). Dark: the poles
    lifted, the midpoint dark but at least 1.6:1 on the surface."""
    mid = _neutral(muted, surface, 1.18 if mode == "light" else MIDPOINT_MIN + 0.1)
    if mode == "light":
        p1, p2 = _slot(lo_pole, mode, surface), _slot(hi_pole, mode, surface)
        return [p1, mix(p1, mid, 0.55), mid, mix(p2, mid, 0.55), p2]
    lift = lambda c: from_oklch(max(oklch(c)[0], 0.76), max(oklch(c)[1], 0.12), oklch(c)[2])
    p1, p2 = lift(lo_pole), lift(hi_pole)
    return [p1, mix(p1, mid, 0.45), mid, mix(p2, mid, 0.45), p2]


def charts(livery: dict, knobs: dict | None) -> dict:
    """livery.json `charts`: {surfaces, mode, light: {...}, dark: {...}, sources, brand, figsize}.
    livery is the resolved json so far (roles, palette, mode, geometry, frametitle, type); knobs is
    livery.yml `charts:` (merged through extends)."""
    k = dict(knobs or {})
    roles, palette, mode = livery["roles"], livery["palette"], livery["mode"]
    unknown = set(k) - {"anchors", "extended", "avoid", "chroma", "ramps", "sets", "categorical",
                        "sequential", "diverging", "status", "muted", "dark"}
    unknown |= {f"dark.{x}" for x in set(k.get("dark") or {}) - {"categorical", "sequential", "diverging", "status", "muted"}}
    if unknown:
        raise ValueError(f"charts: unknown keys {sorted(unknown)}")
    norm = lambda v, where: _norm(v, palette, roles, where)
    light_bg = roles["background"] if mode == "light" else roles["foreground"]
    dark_bg = roles.get("dark", "#000000") if mode == "light" else roles["background"]
    surfaces = {"light": light_bg.upper(), "dark": dark_bg.upper()}
    ramps = {name: [norm(c, f"ramps.{name}") for c in steps] for name, steps in (k.get("ramps") or {}).items()}

    # 1. hues in brand order: anchors, then extended, then (only if short) generated
    def chromatic(c):
        return oklch(c)[1] >= NEUTRAL

    def new_family(c, chosen):
        return all(hue_gap(oklch(c)[2], oklch(x)[2]) >= FAMILY for x in chosen)

    if "anchors" in k:   # a livery's own: every name must resolve
        anchors = [norm(v, "anchors") for v in k["anchors"]]
    else:                # the default: the roles the livery has
        anchors = [roles[r].upper() for r in ("primary", "accent", "secondary", "highlight") if r in roles]
    hues = []
    for c in anchors:
        if chromatic(c) and new_family(c, hues):
            hues.append(c)
    extended = [norm(v, "extended") for v in k["extended"]] if "extended" in k else \
        [c for c in palette.values() if chromatic(c)]
    for c in extended:
        if len(hues) < SLOTS and chromatic(c) and new_family(c, hues):
            hues.append(c.upper())
    for steps in ramps.values():   # a brand ramp's mark step is a brand hue too
        mark = min(steps, key=lambda c: abs(oklch(c)[0] - 0.6))
        if len(hues) < SLOTS and chromatic(mark) and new_family(mark, hues):
            hues.append(mark)
    n_brand = len(hues)
    chroma = k.get("chroma") or min(max(sorted(oklch(c)[1] for c in hues)[len(hues) // 2] if hues else 0.13, 0.11), 0.17)

    out = {"surfaces": surfaces, "mode": mode}
    sources = {}
    for m in ("light", "dark"):
        surface = surfaces[m]
        given = (k.get("dark") or {}) if m == "dark" else k
        blk = {"surface": surface}
        # categorical: pinned, a published set, or selected
        if given.get("categorical"):
            cat = [norm(c, f"{m}.categorical") for c in given["categorical"]]
            sources[f"{m}.categorical"] = "pinned"
        elif m == "dark" and k.get("categorical"):
            cat = [_lift(c, surface) for c in (norm(c, "categorical") for c in k["categorical"])]
            sources[f"{m}.categorical"] = "pinned light, lifted for the dark surface"
        else:
            slots = [_slot(c, m, surface) for c in hues]
            if ramps:   # snap each slot to the nearest brand step that is a legal mark
                legal = [c for r in ramps.values() for c in r if _mark_ok(c, m, surface)]
                slots = [min(legal, key=lambda s: delta_e(s, c)) if legal else c for c in slots]
                slots = list(dict.fromkeys(slots))
            gen = _generate(slots, SLOTS - len(slots), m, surface, chroma, k.get("avoid") or [])
            cat = _order(slots + gen, len(slots))
            if not ramps:
                cat = _nudge(cat, m, surface)
            sources[f"{m}.categorical"] = f"selected: {min(n_brand, len(slots))} brand, {len(gen)} generated"
            blk["generated"] = [c for c in cat if c in gen]
        blk["categorical"] = cat
        sets = (k.get("sets") or {}).get(m)
        if sets:
            blk["sets"] = {str(n): [norm(c, f"sets.{m}.{n}") for c in v] for n, v in sets.items()}
        # the large map: at most SLOTS hues (a ninth series folds into "Other"), three steps each
        blk["families"] = _families(cat[:SLOTS], surface, ramps if m == "light" else {}, m)
        # sequential: the brand ramps when given (light to dark; reversed for dark, so the low end
        # sits near the surface), else a ramp per categorical hue
        seq = ramps or {f"data-{i + 1}": _ramp(c) for i, c in enumerate(cat)}
        if m == "dark":
            seq = {n: list(reversed(r)) for n, r in seq.items()}
        blk["sequential"] = seq
        primary_seq = given.get("sequential", k.get("sequential", "primary"))
        blk["sequential-default"] = _nearest_ramp(seq, norm(primary_seq, "sequential"))
        # diverging
        if given.get("diverging") and len(given["diverging"]) > 2:
            blk["diverging"] = [norm(c, f"{m}.diverging") for c in given["diverging"]]
            sources[f"{m}.diverging"] = "pinned"
        else:
            poles = given.get("diverging") or k.get("diverging")
            if poles:   # two poles, or a pinned light scale's ends
                a, b = norm(poles[0], "diverging"), norm(poles[-1], "diverging")
            else:
                a = norm("primary", "diverging") if chromatic(roles["primary"]) else cat[0]
                b = max(cat[1:], key=lambda c: (cvd_e(a, c), c))
            blk["diverging"] = _diverging(a, b, m, surface, roles.get("muted", roles["foreground"]))
            sources[f"{m}.diverging"] = "derived"
        # a brand's own palette is the authority: evaluate() reports its failures as warnings
        blk["published"] = {"categorical": "pinned" in sources[f"{m}.categorical"],
                            "diverging": sources[f"{m}.diverging"] == "pinned", "sequential": bool(ramps)}
        # status, reserved: a livery's own, else a fixed hue per state, on a step well apart from every
        # categorical slot (_status), so a state never passes for "series 4"
        st = dict((given.get("status") or k.get("status") or {}))
        blk["status"] = {name: norm(st[name], f"status.{name}") if name in st else _status(hue, cat, m, surface)
                         for name, hue in STATUS_HUES.items()}
        blk["muted"] = norm(given["muted"], f"{m}.muted") if given.get("muted") else \
            _neutral(roles.get("muted", roles["foreground"]), surface, MUTED_CONTRAST)
        blk["area-alpha"] = 0.85 if m == "light" else 1.0
        out[m] = blk
    out["sources"] = sources
    out["brand"] = hues[:n_brand]
    out["figsize"] = figsize(livery)
    out["chrome"] = chrome(livery, surfaces)
    return out


def chrome(livery: dict, surfaces: dict) -> dict:
    """{mode: {text, spine, grid}}: a plot's non-data ink per mode, which a dark theme swaps while the
    hues stay. The livery's own mode takes its roles (foreground, muted, derived.rule); the other mode
    the lighter (dark) or darker (light) of foreground and background, its spines and grid that text
    blended toward the surface."""
    roles, mode = livery["roles"], livery["mode"]
    fg, bg = roles["foreground"].upper(), roles["background"].upper()
    lighter, darker = sorted((fg, bg), key=luminance, reverse=True)
    out = {}
    for m in ("light", "dark"):
        if m == mode:
            out[m] = {"text": fg, "spine": roles.get("muted", fg).upper(),
                      "grid": livery.get("derived", {}).get("rule", mix(fg, surfaces[m], 0.7)).upper()}
        else:
            text = lighter if m == "dark" else darker
            out[m] = {"text": text, "spine": mix(text, surfaces[m], 0.45), "grid": mix(text, surfaces[m], 0.75)}
    return out


# OKLCH hue (degrees) -> a plain name, for PowerPoint's Custom Colors row: the upper bound of each bin
HUE_NAMES = ((15, "Pink"), (40, "Red"), (70, "Orange"), (110, "Yellow"), (165, "Green"), (215, "Teal"),
             (240, "Cyan"), (280, "Blue"), (320, "Purple"), (345, "Magenta"), (360, "Pink"))


def hue_name(c: str) -> str:
    """A color's plain name: Gray below the neutral chroma, else its hue's, a grayish cyan or blue
    Slate, a dark orange Brown and a dark yellow Gold."""
    L, C, h = oklch(c)
    if C < NEUTRAL:
        return "Gray"
    name = next(n for top, n in HUE_NAMES if h < top)
    if name in ("Teal", "Cyan", "Blue") and C < 0.08:
        return "Slate"
    if name == "Orange" and L < 0.55:
        return "Brown"
    if name == "Yellow" and L < 0.8:
        return "Gold"
    return name


def custom_colors(ch: dict) -> list[tuple[str, str]]:
    """The categorical slots of the deck's own mode as (name, hex), "Data 1 · Blue": the Custom
    Colors row livery_template.py writes into theme1.xml (a dark livery's slides are dark); the first
    SLOTS of a longer published set, as the method's eight fixed slots."""
    return [(f"Data {i} \u00b7 {hue_name(c)}", c.upper()) for i, c in enumerate(ch[ch["mode"]]["categorical"][:SLOTS], 1)]


def _status(hue: float, cat: list[str], mode: str, surface: str) -> str:
    """A state's color: its fixed hue as a legal mark, nearest the usual mid lightness among the
    steps at least dE 12 from every categorical slot (else the farthest step)."""
    cands = [from_oklch(L, 0.16, hue) for L in _feasible(mode, surface, hue, 0.16)]
    cands = [c for c in cands if oklch(c)[1] >= CHROMA_FLOOR] or cands
    far = lambda c: min(delta_e(c, x) for x in cat)
    ok = [c for c in cands if far(c) >= 12]
    if ok:
        return min(ok, key=lambda c: (abs(oklch(c)[0] - 0.6), c))
    return max(cands, key=lambda c: (far(c), c))


def _mark_ok(c: str, mode: str, surface: str) -> bool:
    lo, hi = BAND[mode]
    L, C, _ = oklch(c)
    return lo <= L <= hi and C >= CHROMA_FLOOR


def _lift(c: str, surface: str, target: float = CONTRAST_MIN) -> str:
    """c tinted toward white (sRGB, 8-bit steps) just far enough to reach target on the surface:
    sam-queries' lift_for_contrast, which keeps similar blues apart where raising lightness would
    merge them. Identity when c already clears it."""
    if contrast(c, surface) >= target:
        return c
    r, g, b = rgb(c)
    for step in range(1, 256):
        f = step / 255
        t = "#" + "".join(f"{round(255 * (x + (1 - x) * f)):02X}" for x in (r, g, b))
        if contrast(t, surface) >= target:
            return t
    return "#FFFFFF"


def _nearest_ramp(seq: dict, color: str) -> str:
    return min(seq, key=lambda n: (min(delta_e(color, c) for c in seq[n]), n))


def figsize(livery: dict) -> dict:
    """The content area in canvas inches (livery_template.py's body frame), whole and one of two
    columns, so a figure at this size carries slide-sized text."""
    w, h = livery["type"]["canvas"]["w"] / 72, livery["type"]["canvas"]["h"] / 72
    m = (livery.get("geometry") or {}).get("margin", 0.06)
    top = (livery.get("frametitle") or {}).get("body", 0.1667)
    height = (1 - 0.0778 - top) * h
    full = (1 - 2 * m) * w
    half = (1 - 2 * m - 0.03) / 2 * w
    return {"full": [round(full, 2), round(height, 2)], "half": [round(half, 2), round(height, 2)]}


def evaluate(ch: dict) -> dict:
    """{mode: {categorical, categorical-3-all, diverging: {arms, midpoint}, sequential: {name: state}}}:
    the checks of a livery.json `charts`, a published palette's failures downgraded to warnings."""
    out = {}
    for m in ("light", "dark"):
        b, surface = ch[m], ch[m]["surface"]
        pub = b.get("published", {})
        soft = lambda key: _published if pub.get(key) else (lambda r: r)
        cat, div = b["categorical"], b["diverging"]
        half = len(div) // 2   # each arm, pole to midpoint: monotone and stepped (its pale end is
        arms = [check_ordinal(div[: half + 1], surface), check_ordinal(div[half:], surface)]   # the neutral)
        mid = div[half]
        # a sequential ramp is a color map: its low end may meet the surface by design, so only
        # monotone lightness and visible steps count (discrete ordinal marks take the darker steps)
        seq = {n: worst({c: v for c, v in check_ordinal(r, surface).items() if c != "end"})
               for n, r in b["sequential"].items()}
        out[m] = {
            "categorical": soft("categorical")(check_categorical(cat, m, surface)),
            "categorical-3-all": soft("categorical")(check_categorical(cat[:3], m, surface, "all")),
            "diverging": {
                "arms": soft("diverging")({f"{side} {c}": v for side, a in zip(("low", "high"), arms)
                                           for c, v in a.items() if c != "end"}),
                "midpoint": ("pass" if contrast(mid, surface) >= (MIDPOINT_MIN if m == "dark" else 1.0) else "warn",
                             f"{mid} at {contrast(mid, surface):.2f}:1")},
            "sequential": {n: ("warn" if pub.get("sequential") and v == "fail" else v) for n, v in seq.items()},
        }
    return out


def states(ch: dict) -> list[str]:
    """Every check's state, flattened: livery_check.py fails a livery on any 'fail'."""
    out = []
    for e in evaluate(ch).values():
        out += [s for s, _ in e["categorical"].values()] + [s for s, _ in e["categorical-3-all"].values()]
        out += [s for s, _ in e["diverging"]["arms"].values()] + [e["diverging"]["midpoint"][0]]
        out += list(e["sequential"].values())
    return out


def report(name: str, ch: dict) -> list[str]:
    """Human-readable lines for livery_check.py and the command line."""
    lines = []
    ev = evaluate(ch)
    for m in ("light", "dark"):
        b = dict(ch[m], checks=ev[m])
        src = ch["sources"].get(f"{m}.categorical", "")
        lines.append(f"{name} {m} on {b['surface']}: {' '.join(b['categorical'])}  ({src})")
        for check, (state, detail) in b["checks"]["categorical"].items():
            lines.append(f"  {state:4}  {m} categorical {check}: {detail}")
        s3, d3 = b["checks"]["categorical-3-all"]["normal"]
        lines.append(f"  {s3:4}  {m} first three, all pairs: {d3}")
        for part, val in b["checks"]["diverging"].items():
            state = worst(val) if isinstance(val, dict) else val[0]
            detail = "" if isinstance(val, dict) else val[1]
            lines.append(f"  {state:4}  {m} diverging {part} {detail}".rstrip())
        seq = b["checks"]["sequential"]
        bad = [n for n, s in seq.items() if s != "pass"]
        state = "fail" if "fail" in seq.values() else "warn" if bad else "pass"
        lines.append(f"  {state:4}  {m} sequential ramps monotone and stepped{': ' + str(bad) if bad else ''}"
                     f"{' (published)' if state == 'warn' else ''}")
    return lines


def swatch(name: str, ch: dict, path) -> None:
    """A contact sheet of the selections, light above dark, each on its own surface: the
    categorical slots (generated ones marked), the families, the sequential ramps, the diverging
    scale, status and muted. Needs Pillow (in the framework's env), not the build."""
    from PIL import Image, ImageDraw, ImageFont
    W, S, G = 1700, 46, 6     # sheet width (eight families of three fit), swatch size, gap
    try:
        font = ImageFont.load_default(size=13)
    except TypeError:   # Pillow < 10.1
        font = ImageFont.load_default()
    blocks = []
    for m in ("light", "dark"):
        b = ch[m]
        rows = [("categorical", [[c] for c in b["categorical"]]), ("families", b["families"])]
        rows += [(f"seq {n}", [[c] for c in r]) for n, r in b["sequential"].items()]
        rows += [("diverging", [[c] for c in b["diverging"]]),
                 ("status", [[b["status"][k]] for k in STATUS_HUES]), ("muted", [[b["muted"]]])]
        if b.get("sets"):
            rows += [(f"set {n}", [[c] for c in v]) for n, v in b["sets"].items()]
        blocks.append((m, b, rows))
    H = sum(28 + len(rows) * (S + 18) + 12 for _, _, rows in blocks)
    img = Image.new("RGB", (W, H), "#FFFFFF")
    dr = ImageDraw.Draw(img)
    y = 0
    for m, b, rows in blocks:
        h = 28 + len(rows) * (S + 18) + 12
        bg = b["surface"]
        ink = "#FFFFFF" if luminance(bg) < 0.18 else "#000000"
        dr.rectangle([0, y, W, y + h], fill=bg)
        dr.text((12, y + 8), f"{name} - {m} on {bg} - {ch['sources'].get(m + '.categorical', '')}", fill=ink, font=font)
        yy = y + 28
        for label, groups in rows:
            dr.text((12, yy + S // 2 - 7), label[:22], fill=ink, font=font)
            x = 190
            for grp in groups:
                for c in grp:
                    if x + S > W - 8:
                        break
                    dr.rectangle([x, yy, x + S, yy + S], fill=c)
                    if c in b.get("generated", []):
                        dr.text((x + 3, yy + 2), "gen", fill="#FFFFFF" if luminance(c) < 0.3 else "#000000", font=font)
                    dr.text((x, yy + S + 2), c.lstrip("#"), fill=ink, font=font)
                    x += S + G
                x += 4 * G if len(grp) > 1 else 0
            yy += S + 18
        y += h
    img.save(path)


def main():
    import json
    from pathlib import Path
    args = sys.argv[1:]
    out = None
    if args[:1] == ["--swatch"]:
        out, args = Path(args[1]), args[2:]
    for d in args:
        L = json.loads((Path(d) / "build" / "livery.json").read_text())
        for line in report(L["name"], L["charts"]):
            print(line)
        if out:
            out.mkdir(parents=True, exist_ok=True)
            swatch(L["name"], L["charts"], out / f"charts-{Path(d).name}.png")


if __name__ == "__main__":
    main()
