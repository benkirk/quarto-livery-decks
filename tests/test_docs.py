"""Check the docs' links and section pointers (#84).

    python3 -m pytest tests/test_docs.py

Every relative link and image in the tracked Markdown files resolves to a tracked path, and every
`#anchor` to a heading of its target by GitHub's rule (lower-case, spaces to `-`, punctuation
dropped, `-1`, `-2` on a repeated heading): one test per file. Every section pointer in a tracked
text file, the word README or a `.md` path followed by a quoted section name, names a heading
that exists in that file (README is the root README.md; a path is from the repository root, else
relative to the file). Fenced and inline code are skipped. `design/` is exempt: its handoffs are
dated records of the sections of their day. The consumer workflow example in docs/other-repos.md
pins the engine's version (`@v<version>`, the image tag), so a release bumps it with the rest.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

from conftest import ROOT

tracked = set(subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout.split("\n")) - {""}
tracked_paths = set(tracked)
for f in tracked:
    for parent in Path(f).parents:
        tracked_paths.add(str(parent))
tracked_paths.discard(".")


def text_of(path):
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,}).*?^[ \t]*\1[ \t]*$", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")


def prose(text):
    """The text outside fenced and inline code (the fences' lines kept blank, so numbers hold)."""
    text = FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return INLINE_CODE.sub("", text)


HEADING = re.compile(r"^#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$", re.M)
headings_cache = {}


def heading_text(raw):
    return re.sub(r"[`*]", "", raw).strip()


def slug(title):
    s = re.sub(r"[^\w\s-]", "", title.lower(), flags=re.UNICODE)
    return s.replace(" ", "-")


def headings(path):
    """The headings of a Markdown file: their texts and GitHub anchors (code fences skipped)."""
    if path not in headings_cache:
        text = text_of(path) or ""
        text = FENCE.sub("", text)
        titles = [heading_text(m.group(1)) for m in HEADING.finditer(text)]
        anchors, seen = set(), {}
        for t in titles:
            s = slug(t)
            n = seen.get(s, 0)
            seen[s] = n + 1
            anchors.add(s if n == 0 else f"{s}-{n}")
        headings_cache[path] = (set(titles), anchors)
    return headings_cache[path]


def relative(path):
    return str(path.relative_to(ROOT)) if path.is_absolute() else str(path)


# 1. links and images: ](target) outside code; a scheme or a reference definition is skipped
LINK = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
MARKDOWN = sorted(f for f in tracked if f.endswith(".md") and not f.startswith("design/"))


@pytest.mark.parametrize("md", MARKDOWN)
def test_links(md):
    text = text_of(md)
    if text is None:
        return
    bad = []
    for m in LINK.finditer(prose(text)):
        target = m.group(1)
        line = text[: m.start()].count("\n") + 1
        if SCHEME.match(target):
            continue
        path, _, anchor = target.partition("#")
        if path:
            resolved = os.path.normpath(relative(Path(md).parent / path))
            if resolved not in tracked_paths:
                bad.append(f"{md}:{line}: link to {target}: {resolved} is not tracked")
                continue
        else:
            resolved = md
        if anchor and resolved.endswith(".md") and anchor not in headings(resolved)[1]:
            bad.append(f"{md}:{line}: link to {target}: no heading #{anchor} in {resolved}")
    assert not bad, "\n".join(bad)


# 2. section pointers: README "X" or <path>.md "X" (the quote may wrap onto a commented line)
POINTER = re.compile(r"(?<![\w/.-])((?:[\w.-]+/)*[\w.-]+\.md|README)(?:'s)? \"([^\"]{1,160})\"")
CONTINUATION = re.compile(r"\s*\n[ \t]*(?:#|%|//|--)?[ \t]*")
EXEMPT = ("design/",)


def test_pointers():
    bad = []
    for f in sorted(tracked):
        if f.startswith(EXEMPT) or f == relative(Path(__file__).resolve()):
            continue
        text = text_of(f)
        if text is None or "\0" in text:
            continue
        body = prose(text) if f.endswith(".md") else text
        for m in POINTER.finditer(body):
            where, section = m.group(1), CONTINUATION.sub(" ", m.group(2)).strip()
            line = body[: m.start()].count("\n") + 1
            if where == "README":
                target = "README.md"
            elif where in tracked:
                target = where
            else:
                target = os.path.normpath(relative(Path(f).parent / where))
            if target not in tracked:
                bad.append(f"{f}:{line}: pointer to {where} \"{section}\": {where} is not tracked")
            elif section not in headings(target)[0]:
                bad.append(f"{f}:{line}: pointer to {where} \"{section}\": no such heading in {target}")
    assert not bad, "\n".join(bad)


# 3. the consumer example's release pins: every `@vX.Y.Z` and image tag in docs/other-repos.md is
# the engine's version, so the release PR that bumps `_extension.yml` bumps the example too
PIN = re.compile(r"@v(\d+\.\d+\.\d+)\b|quarto-livery-decks:(\d+\.\d+\.\d+)\b")


def test_consumer_pins():
    import livery
    version = livery.engine_version()
    pins = [m.group(1) or m.group(2) for m in PIN.finditer(text_of("docs/other-repos.md"))]
    assert pins, "docs/other-repos.md: no release pin in the consumer workflow example"
    assert set(pins) == {version}, f"docs/other-repos.md pins {sorted(set(pins))}; the engine is {version}"


# 4. the changelog's link block: every `## [x.y.z]` section has its release link, and
# `[Unreleased]` compares from the newest one (a release renames the section and adds the link)
def test_changelog_links():
    text = text_of("CHANGELOG.md")
    versions = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", text, re.M)
    links = dict(re.findall(r"^\[(\d+\.\d+\.\d+)\]: (\S+)$", text, re.M))
    assert versions, "CHANGELOG.md: no release section"
    missing = [v for v in versions if links.get(v) != f"https://github.com/benkirk/quarto-livery-decks/releases/tag/v{v}"]
    assert not missing, f"CHANGELOG.md: no release link for {missing}"
    unreleased = re.search(r"^\[Unreleased\]: \S+/compare/v(\d+\.\d+\.\d+)\.\.\.HEAD$", text, re.M)
    assert unreleased and unreleased.group(1) == versions[0], \
        f"CHANGELOG.md: [Unreleased] compares from {unreleased and unreleased.group(1)}; the newest section is {versions[0]}"
