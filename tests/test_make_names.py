"""Check the make files' names (Make.common's header): upper case is a knob (`?=`, `override`, an
export) or a documented read-out, lower case is the file's own; and no name expands undefined.

    python3 -m pytest tests/test_make_names.py

Make expands a name it does not know to nothing, silently, so a private name mistyped in one place
(`$(prereqs)` where `prereqs` is defined) builds a deck with a prerequisite less and says nothing.
`make -n --warn-undefined-variables` names every such expansion; under each runtime the set is
pinned to the knobs a deck may leave unset (DECK_META, FONTS_DIR, a PYTHONPATH not in the
environment, the LIVERY_DIR a container's host side never defines), so a typo joins the set and
fails. The convention itself is pinned by reading every definition in the four files. macOS's
/usr/bin/make (3.81) must still parse the header and the dispatch; when it is there, it does.
"""

import re
import shutil
import subprocess

import pytest

from conftest import ROOT, make_deck

MAKE_FILES = ["Make.common", "common/Make.container", "common/Make.conda", "common/image.mk"]
READ_OUTS = {"DECKS_RUNTIME_USED", "FRAMEWORK_ROOT", "APPTAINER_SIF"}   # upper, set by the file, documented
GOALS = ["pptx", "html", "pdf", "qa", "site", "deps"]
# the names make may find undefined per runtime: knobs a deck leaves unset
EXPECTED = {
    "native": {"DECK_META", "PYTHONPATH"},
    "conda": set(),
    "docker": {"DECK_META", "FONTS_DIR", "LIVERY_DIR"},
    "apptainer": {"DECK_META", "FONTS_DIR", "LIVERY_DIR"},
}
DEFINITION = re.compile(r"^(override |export )?([A-Za-z][A-Za-z0-9_]*)\s*(\?=|:=|\+=|=)")
UNDEFINED = re.compile(r"undefined variable [`']([^`']+)'")


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    d = tmp_path_factory.mktemp("names") / "talk"
    d.mkdir()
    (d / "Makefile").write_text(f"include {ROOT}/Make.common\n")
    (d / "talk.qmd").write_text("---\ntitle: T\n---\n")
    (d / "requirements.txt").write_text("tabulate==0.9.0\n")   # the deps rule's branch too
    return d


def test_upper_case_is_a_knob():
    """Every upper-case definition is `?=`, `override`, `export` or a documented read-out."""
    bad = []
    for f in MAKE_FILES:
        for n, line in enumerate((ROOT / f).read_text().splitlines(), 1):
            m = DEFINITION.match(line)
            if not m or not m.group(2).isupper():
                continue
            prefix, name, op = m.groups()
            if op == "?=" or prefix or name in READ_OUTS:
                continue
            bad.append(f"{f}:{n}: {line.strip()}")
    assert not bad, "an upper-case name that is not a knob (lower case is the file's own):\n" + "\n".join(bad)


@pytest.mark.parametrize("runtime", sorted(EXPECTED))
def test_no_undefined_name(deck, runtime):
    r = make_deck(deck, "--warn-undefined-variables", *GOALS, f"DECKS_RUNTIME={runtime}", dry=True)
    found = set(UNDEFINED.findall(r.stderr))
    assert found == EXPECTED[runtime], f"{runtime}: undefined {sorted(found)} (expected {sorted(EXPECTED[runtime])})\n{r.stderr[-800:]}"


@pytest.mark.skipif(not shutil.which("/usr/bin/make"), reason="no /usr/bin/make")
def test_system_make_parses_the_dispatch(deck):
    """The host side under macOS's GNU make 3.81: the header and Make.container/Make.conda parse, and
    the one run is dispatched."""
    v = subprocess.run(["/usr/bin/make", "--version"], capture_output=True, text=True).stdout
    if "GNU Make" not in v:
        pytest.skip("not GNU make")
    for runtime, mark in (("docker", "docker run"), ("conda", "conda run")):
        r = subprocess.run(["/usr/bin/make", "-n", "-C", str(deck), "pptx", f"DECKS_RUNTIME={runtime}"],
                           capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
        assert r.returncode == 0 and mark in r.stdout, f"{runtime}: {r.stderr[-400:]}"
