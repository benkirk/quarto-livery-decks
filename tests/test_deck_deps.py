"""Check a deck's own Python packages (common/utils/deck_deps.py, Make.common's `make deps`;
docs/container.md "From your deck's Makefile").

    python3 -m pytest tests/test_deck_deps.py

Offline: the requirement is a wheel written here with zipfile, plus a pin the env already
satisfies (numpy at its installed version), so pip reaches no index. The folder's key names the
engine, the Python, the platform and the file's hash; `install` makes the venv on the env's
packages (the wheel's package imports from its site-packages, numpy is not re-installed), says
so the second time, and refuses an unpinned line; `make pptx` without the folder stops before any
render and names `make deps`; `make deps html` in one run installs and builds (a stub quarto on
PATH writes the output); a deck without requirements.txt has nothing to install; a container
runtime forwards `deps` into the image (`make -n`). Everything under tmp_path.
"""

import hashlib
import os
import platform
import re
import stat
import subprocess
import sys
import zipfile
from importlib.metadata import version
from pathlib import Path

import pytest

from conftest import ENGINE, ROOT, bare_env, make_deck, one_line

DECK_DEPS = ROOT / "common" / "utils" / "deck_deps.py"
QMD = "---\ntitle: Talk\n---\n\n## One\n\nA slide.\n"
STUB_QUARTO = """#!/bin/sh
# a quarto that writes its output and nothing else: `-o FILE`, else <input>.html beside it
out=; prev=
for a in "$@"; do [ "$prev" = -o ] && out=$a; prev=$a; done
[ -n "$out" ] || out=$(basename "$2" .qmd).html
: > "$out"
"""


def deck_deps(*args, **kw):
    return subprocess.run([sys.executable, str(DECK_DEPS), *map(str, args)], capture_output=True, text=True, **kw)


@pytest.fixture(scope="module")
def req(tmp_path_factory):
    """requirements.txt: a wheel of hello_dep (VALUE = 42) by its path, and numpy at the env's version."""
    d = tmp_path_factory.mktemp("req")
    whl = d / "hello_dep-1.0-py3-none-any.whl"
    with zipfile.ZipFile(whl, "w") as z:
        z.writestr("hello_dep/__init__.py", "VALUE = 42\n")
        z.writestr("hello_dep-1.0.dist-info/METADATA", "Metadata-Version: 2.1\nName: hello-dep\nVersion: 1.0\n")
        z.writestr("hello_dep-1.0.dist-info/WHEEL", "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
        z.writestr("hello_dep-1.0.dist-info/RECORD", "hello_dep/__init__.py,,\nhello_dep-1.0.dist-info/METADATA,,\n"
                   "hello_dep-1.0.dist-info/WHEEL,,\nhello_dep-1.0.dist-info/RECORD,,\n")
    r = d / "requirements.txt"
    r.write_text(f"{whl}\nnumpy=={version('numpy')}   # the env's own: nothing to fetch\n")
    return r


@pytest.fixture(scope="module")
def deck(tmp_path_factory, req):
    """A deck beside a framework checkout, with the requirements."""
    d = tmp_path_factory.mktemp("deck") / "talk"
    d.mkdir()
    (d / "Makefile").write_text(f"include {ROOT}/Make.common\n")
    (d / "talk.qmd").write_text(QMD)
    (d / "requirements.txt").write_text(req.read_text())
    return d


def expected_key(req):
    engine = re.search(r"^version:\s*(\S+)", (ENGINE / "_extension.yml").read_text(), re.M)[1]
    return (f"deps-{engine}-py{sys.version_info[0]}.{sys.version_info[1]}-{sys.platform}-{platform.machine()}"
            f"-{hashlib.sha256(req.read_bytes()).hexdigest()[:8]}")


def test_dir_is_the_key(req, tmp_path):
    r = deck_deps("dir", tmp_path, req)
    assert r.returncode == 0 and r.stderr == "" and r.stdout == f"{tmp_path / expected_key(req)}\n", r.stdout + r.stderr


def test_install_only_what_the_env_lacks(req, tmp_path):
    r = deck_deps("install", tmp_path, req)
    assert r.returncode == 0, r.stderr
    folder = tmp_path / expected_key(req)
    site = folder / "site-packages"
    assert site.is_symlink() and site.is_dir() and not list(tmp_path.glob("*.part-*")), list(tmp_path.iterdir())
    assert (site / "hello_dep").is_dir() and not (site / "numpy").exists(), "numpy re-installed over the env's"
    probe = subprocess.run([sys.executable, "-c", "import hello_dep, numpy; print(hello_dep.VALUE, numpy.__file__)"],
                           capture_output=True, text=True, env={**bare_env(), "PYTHONPATH": str(site)})
    assert probe.returncode == 0 and probe.stdout.startswith("42 ") and str(site) not in probe.stdout, probe.stdout + probe.stderr
    again = deck_deps("install", tmp_path, req)
    assert again.returncode == 0 and "already installed" in again.stdout, again.stdout + again.stderr


@pytest.mark.parametrize("line", ["numpy>=1", "-r other.txt", "-e .", "hello-dep"])
def test_unpinned_is_refused(line, tmp_path):
    r = tmp_path / "requirements.txt"
    r.write_text(f"{line}\n")
    out = deck_deps("install", tmp_path / "root", r)
    assert out.returncode == 2 and line in out.stderr and "pinned" in out.stderr, out.stderr
    assert not (tmp_path / "root").exists(), "a folder for a refused file"
    assert deck_deps("dir", tmp_path / "root", r).returncode == 0, "dir judges nothing"


def test_option_lines_pass(tmp_path):
    r = tmp_path / "requirements.txt"
    r.write_text("--index-url https://example.invalid/simple\n--find-links ./wheels\nfoo==1.0 --hash=sha256:00\nbar @ https://example.invalid/bar.whl\n")
    sys.path.insert(0, str(DECK_DEPS.parent))
    try:
        import deck_deps as mod
    finally:
        sys.path.pop(0)
    assert mod.unpinned(r.read_text()) == []


def test_missing_folder_says_make_deps(deck, tmp_path):
    r = make_deck(deck, "pptx", "DECKS_RUNTIME=native", f"DECKS_DEPS={tmp_path / 'empty'}")
    assert r.returncode != 0 and "make deps" in r.stderr and "requirements.txt" in r.stderr, r.stdout + r.stderr
    assert "quarto render" not in r.stdout and not (deck / "talk.pptx").exists(), "the render ran"


def test_deps_then_build_in_one_go(deck, tmp_path):
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "quarto").write_text(STUB_QUARTO)
    (stub / "quarto").chmod((stub / "quarto").stat().st_mode | stat.S_IEXEC)
    r = make_deck(deck, "deps", "html", "DECKS_RUNTIME=native", f"DECKS_DEPS={tmp_path / 'deps'}",
             PATH=f"{stub}:{os.environ['PATH']}")
    assert r.returncode == 0, r.stdout[-500:] + r.stderr[-800:]
    assert (deck / "talk.html").exists() and (tmp_path / "deps" / expected_key(deck / "requirements.txt") / "site-packages").is_dir()


def test_no_requirements_is_a_noop(tmp_path):
    d = tmp_path / "plain"
    d.mkdir()
    (d / "Makefile").write_text(f"include {ROOT}/Make.common\n")
    (d / "plain.qmd").write_text(QMD)
    r = make_deck(d, "deps", "DECKS_RUNTIME=native")
    assert r.returncode == 0 and "nothing to install" in r.stdout, r.stdout + r.stderr


def test_container_forwards_deps(deck):
    r = make_deck(deck, "deps", "DECKS_RUNTIME=docker", dry=True)
    flat = one_line(r.stdout)
    assert r.returncode == 0 and "docker run" in flat and "make deps DECKS_RUNTIME=native" in flat, r.stdout + r.stderr


def test_decks_deps_under_a_container_warns(deck, tmp_path):
    r = make_deck(deck, "deps", "DECKS_RUNTIME=docker", f"DECKS_DEPS={tmp_path}", dry=True)
    assert r.returncode == 0 and "DECKS_DEPS is for a native build" in r.stderr, r.stderr
