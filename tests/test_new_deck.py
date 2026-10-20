"""Check `bin/new-deck` (docs/container.md "Sharing an installation").

    python3 -m pytest tests/test_new_deck.py

A fresh deck gets the quickstart, its picture, a Makefile on `QUARTO_DECKS ?= <this checkout>` that
make parses, and a .gitignore in Quarto's own spellings; a non-empty directory is refused. `--bare`
writes only the Makefile and .gitignore beside a repository's files, adds to its .gitignore only the
lines it lacks (once), and refuses an existing Makefile. A QUARTO_DECKS from the environment reaches
the container's make (Make.container), which sees only the image's environment. make runs `-n`:
nothing renders.
"""

import os
import subprocess

import pytest

from conftest import ROOT

NEW = ROOT / "bin" / "new-deck"


def new(*args):
    return subprocess.run([str(NEW), *map(str, args)], capture_output=True, text=True)


def make(d, *args, **env):
    e = {k: v for k, v in os.environ.items() if k not in ("QUARTO_DECKS", "MAKEFLAGS")}
    return subprocess.run(["make", "-n", "-C", str(d), *args], capture_output=True, text=True, env={**e, **env})


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    """A fresh deck, talk/, from new-deck."""
    d = tmp_path_factory.mktemp("deck") / "talk"
    r = new(d)
    assert r.returncode == 0, f"new-deck: {r.stderr.strip()}"
    return d


def test_fresh_deck_files(deck):
    assert (deck / "talk.qmd").exists() and (deck / "images").is_dir(), "no talk.qmd or images/"
    mk = (deck / "Makefile").read_text()
    assert f"QUARTO_DECKS ?= {ROOT.resolve()}\n" in mk and "include $(QUARTO_DECKS)/Make.common\n" in mk, \
        f"the Makefile does not include through QUARTO_DECKS ?=:\n{mk}"
    ignore = (deck / ".gitignore").read_text().splitlines()
    assert "/.quarto/" in ignore and "**/*.quarto_ipynb" in ignore, "the .gitignore is not in Quarto's spellings"


def test_refuses_nonempty(deck):
    assert new(deck).returncode != 0, "new-deck on a non-empty directory succeeded"


def test_make_parses(deck):
    r = make(deck, "pptx", f"QUARTO_DECKS={ROOT}", "DECKS_RUNTIME=native")
    assert r.returncode == 0, f"make -n pptx: {r.stderr.strip()[-300:]}"


def test_env_quarto_decks_reaches_container(deck):
    # the container's make gets an environment QUARTO_DECKS; a command line one rides MAKEFLAGS
    r = make(deck, "pptx", "DECKS_RUNTIME=docker", QUARTO_DECKS=str(ROOT))
    assert r.returncode == 0 and f"DECKS_RUNTIME=native QUARTO_DECKS={ROOT}" in " ".join(r.stdout.replace("\\\n", " ").split()), \
        f"the environment's QUARTO_DECKS is not passed into the container: {(r.stdout + r.stderr).strip()[-300:]}"


def test_makefile_quarto_decks_not_passed(deck):
    r = make(deck, "pptx", "DECKS_RUNTIME=docker")
    assert r.returncode == 0 and "QUARTO_DECKS=" not in r.stdout, "QUARTO_DECKS passed in when the Makefile set it"


def test_bare_beside_repo(tmp_path):
    b = tmp_path / "repo"
    b.mkdir()
    (b / "report.qmd").write_text("---\ntitle: x\n---\n")
    (b / ".gitignore").write_text("/data/\n*.pptx\n")
    r = new("--bare", b)
    assert r.returncode == 0, f"new-deck --bare: {r.stderr.strip()}"
    assert (b / "Makefile").exists() and not (b / "images").exists() and not (b / "repo.qmd").exists(), \
        "--bare wrote more than a Makefile and .gitignore"
    lines = (b / ".gitignore").read_text().splitlines()
    assert lines[:2] == ["/data/", "*.pptx"] and lines.count("*.pptx") == 1 and "/.quarto/" in lines, \
        f"--bare did not append only the missing lines: {lines}"
    assert new("--bare", b).returncode != 0, "--bare over an existing Makefile succeeded"
    before = (b / ".gitignore").read_text()
    (b / "Makefile").unlink()
    new("--bare", b)
    assert (b / ".gitignore").read_text() == before, "a second --bare appended to the .gitignore again"


def test_bare_into_new_dir(tmp_path):
    r = new("--bare", tmp_path / "empty")
    assert r.returncode == 0 and (tmp_path / "empty" / ".gitignore").read_text().startswith("# links"), \
        f"--bare into a new directory: {r.stderr.strip()}"
