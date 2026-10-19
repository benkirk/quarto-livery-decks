#!/usr/bin/env python3
"""Check the docs' links and section pointers (#84).

    tests/test_docs.py

Every relative link and image in the tracked Markdown files resolves to a tracked path, and every
`#anchor` to a heading of its target by GitHub's rule (lower-case, spaces to `-`, punctuation
dropped, `-1`, `-2` on a repeated heading). Every section pointer in a tracked text file, the
word README or a `.md` path followed by a quoted section name, names a heading that exists in that
file (README is the root README.md; a path is from the repository root, else relative to the file).
Fenced and inline code are skipped. `design/` is exempt: its handoffs are dated records of the
sections of their day.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fails = []


def check(ok, what):
    if not ok:
        fails.append(what)


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

for md in sorted(f for f in tracked if f.endswith(".md") and not f.startswith("design/")):
    text = text_of(md)
    if text is None:
        continue
    for m in LINK.finditer(prose(text)):
        target = m.group(1)
        line = text[: m.start()].count("\n") + 1
        if SCHEME.match(target):
            continue
        path, _, anchor = target.partition("#")
        if path:
            resolved = os.path.normpath(relative(Path(md).parent / path))
            check(resolved in tracked_paths, f"{md}:{line}: link to {target}: {resolved} is not tracked")
            if resolved not in tracked_paths:
                continue
        else:
            resolved = md
        if anchor and resolved.endswith(".md"):
            check(anchor in headings(resolved)[1],
                  f"{md}:{line}: link to {target}: no heading #{anchor} in {resolved}")

# 2. section pointers: README "X" or <path>.md "X" (the quote may wrap onto a commented line)
POINTER = re.compile(r"(?<![\w/.-])((?:[\w.-]+/)*[\w.-]+\.md|README)(?:'s)? \"([^\"]{1,160})\"")
CONTINUATION = re.compile(r"\s*\n[ \t]*(?:#|%|//|--)?[ \t]*")
EXEMPT = ("design/",)

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
            check(False, f"{f}:{line}: pointer to {where} \"{section}\": {where} is not tracked")
            continue
        check(section in headings(target)[0],
              f"{f}:{line}: pointer to {where} \"{section}\": no such heading in {target}")

if fails:
    print("docs:", *fails, sep="\n  ")
    sys.exit(1)
print("docs: every link resolves and every section pointer names a heading")
