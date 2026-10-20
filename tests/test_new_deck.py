#!/usr/bin/env python3
"""Check `bin/new-deck` (docs/container.md "Sharing an installation").

    tests/test_new_deck.py

A fresh deck gets the quickstart, its picture, a Makefile on `QUARTO_DECKS ?= <this checkout>` that
make parses, and a .gitignore in Quarto's own spellings; a non-empty directory is refused. `--bare`
writes only the Makefile and .gitignore beside a repository's files, adds to its .gitignore only the
lines it lacks (once), and refuses an existing Makefile. A QUARTO_DECKS from the environment reaches
the container's make (Make.container), which sees only the image's environment.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW = ROOT / "bin" / "new-deck"
fails = []


def check(ok, what):
    if not ok:
        fails.append(what)


def new(*args):
    return subprocess.run([str(NEW), *map(str, args)], capture_output=True, text=True)


def make(d, *args, **env):
    e = {k: v for k, v in os.environ.items() if k not in ("QUARTO_DECKS", "MAKEFLAGS")}
    return subprocess.run(["make", "-n", "-C", str(d), *args], capture_output=True, text=True, env={**e, **env})


with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp).resolve()
    d = t / "talk"
    r = new(d)
    check(r.returncode == 0, f"new-deck: {r.stderr.strip()}")
    check((d / "talk.qmd").exists() and (d / "images").is_dir(), "no talk.qmd or images/")
    mk = (d / "Makefile").read_text()
    check(f"QUARTO_DECKS ?= {ROOT.resolve()}\n" in mk and "include $(QUARTO_DECKS)/Make.common\n" in mk,
          f"the Makefile does not include through QUARTO_DECKS ?=:\n{mk}")
    ignore = (d / ".gitignore").read_text().splitlines()
    check("/.quarto/" in ignore and "**/*.quarto_ipynb" in ignore, "the .gitignore is not in Quarto's spellings")
    check(new(d).returncode != 0, "new-deck on a non-empty directory succeeded")
    r = make(d, "pptx", f"QUARTO_DECKS={ROOT}", "DECKS_RUNTIME=native")
    check(r.returncode == 0, f"make -n pptx: {r.stderr.strip()[-300:]}")

    # the container's make gets an environment QUARTO_DECKS; a command line one rides MAKEFLAGS
    r = make(d, "pptx", "DECKS_RUNTIME=docker", QUARTO_DECKS=str(ROOT))
    check(r.returncode == 0 and f"DECKS_RUNTIME=native QUARTO_DECKS={ROOT}" in " ".join(r.stdout.replace("\\\n", " ").split()),
          f"the environment's QUARTO_DECKS is not passed into the container: {(r.stdout + r.stderr).strip()[-300:]}")
    r = make(d, "pptx", "DECKS_RUNTIME=docker")
    check(r.returncode == 0 and "QUARTO_DECKS=" not in r.stdout, "QUARTO_DECKS passed in when the Makefile set it")

    # --bare beside a repository's files
    b = t / "repo"
    b.mkdir()
    (b / "report.qmd").write_text("---\ntitle: x\n---\n")
    (b / ".gitignore").write_text("/data/\n*.pptx\n")
    r = new("--bare", b)
    check(r.returncode == 0, f"new-deck --bare: {r.stderr.strip()}")
    check((b / "Makefile").exists() and not (b / "images").exists() and not (b / "repo.qmd").exists(),
          "--bare wrote more than a Makefile and .gitignore")
    lines = (b / ".gitignore").read_text().splitlines()
    check(lines[:2] == ["/data/", "*.pptx"] and lines.count("*.pptx") == 1 and "/.quarto/" in lines,
          f"--bare did not append only the missing lines: {lines}")
    check(new("--bare", b).returncode != 0, "--bare over an existing Makefile succeeded")
    before = (b / ".gitignore").read_text()
    (b / "Makefile").unlink()
    new("--bare", b)
    check((b / ".gitignore").read_text() == before, "a second --bare appended to the .gitignore again")
    r = new("--bare", t / "empty")
    check(r.returncode == 0 and (t / "empty" / ".gitignore").read_text().startswith("# links"),
          f"--bare into a new directory: {r.stderr.strip()}")

if fails:
    print("new-deck:", *fails, sep="\n  ")
    sys.exit(1)
print("new-deck: a fresh deck, its refusal, --bare beside files, the Makefile parses, QUARTO_DECKS reaches the container")
