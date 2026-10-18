# Handoff: the README as a front page, the details in companion guides

Written 2026-10-18, at the end of #58 (the customer surface) and the first release, v26.10.0, for
a fresh session. Read this, then `CLAUDE.md`, then the README itself. Decided with Ben the same
day: the homes, the length and this form (a handoff plus an issue). Conventions are as ever: one
squash-merged PR per step, CI green before merging, no compatibility shims (no stub sections, no
"moved to" placeholders), and a layman's summary before any question to Ben.

## Why

The README is about 1,000 lines in some 30 sections. It mixes a newcomer's path (what this is,
the quick start, the gallery) with reference material:
- the formats' internals (build pipeline, template constraints, beamer and revealjs notes);
- the whole LaTeX chapter, about 180 lines;
- the container, about 75 lines;
- consumer repos and publishing.

Ben wants it **much more accessible, with the details deferred to companion docs**. #58 started
the pattern: "Adding a livery" moved to `liveries/README.md`, every `livery.yml` key is in
`liveries/REFERENCE.md`, and plots have `decks/plots/README.md`.

## The design

**Four readers, the changelog's four sections.** The README is the front door for a **deck
author**, and it routes the other three readers to their own guides: the **livery owner**, the
**plot author** and the **LaTeX user**. These are `CHANGELOG.md`'s Decks, Liveries, Plots and
LaTeX.

**The README, about 150-200 lines:**
- the pitch, the hero image and the livery gallery (both from `decks/quickstart/`);
- the quick start, with the container as a one-line alternative;
- "What you get": each feature beside its screenshot, as today;
- the liveries in one table, one line each;
- a **"Where next"** table, one row per guide by reader and task;
- license and origins, short.

**The guides.** A guide sits beside its subject where a directory owns it, and in `docs/` (new)
when it cuts across:

| guide | takes from today's README |
|---|---|
| `docs/authoring.md` | Adding a new deck, Linked images, Centering and scaling a short slide, Executable shell chunks, Text sizes and the slide size, About text autofit, Checking a deck |
| `docs/formats.md` | Build pipeline, About the fonts, Installed brand fonts, Template constraints, PDF (beamer), HTML (revealjs), and Layout (the tree), unless it shrinks to five lines on the front page |
| `latex/README.md` | LaTeX and Overleaf: Overleaf, The starter and the examples, An existing LaTeX deck, Writing slides in LaTeX, Theme options, Math fonts, Colors |
| `decks/plots/README.md` (exists) | Plots and chart colors |
| `liveries/README.md` (exists) | The liveries' detail; the front page keeps the one-line table |
| `docs/container.md` | Building in the container |
| `docs/other-repos.md` | Using the framework from another repo, Publishing the HTML decks |

The README has example headings inside its code fences ("Wall of text {.smaller}", "A plot",
"Who's still on legacy", ...). They are part of the examples, not sections.

## Rules

- **Move, don't rewrite.** A section moves whole, edited only for its new place: heading levels,
  relative links and image paths, "above/below". Anything cut is listed in its PR.
- **Every pointer moves in the same PR.** `git grep -n 'README "'` lists them:
  - CLAUDE.md (8);
  - `Make.common`, `Makefile`, `Dockerfile`, `etc/entrypoint.sh`;
  - `.github/workflows/ci.yaml` and `release.yml`;
  - `CHANGELOG.md`, `liveries/README.md`.

  Two more don't match that pattern: `beamerthemeEngine.sty`'s "see README" (it means the theme
  options, now in `latex/README.md`) and CLAUDE.md's "The README covers layout, template
  constraints, and font embedding". Point each at the guide that now holds it.
- **The images stay where they are.** `decks/quickstart/screenshots.py` and `gallery.py` keep
  writing `decks/quickstart/screenshots/*.png`; a moved guide links them by its own relative path.
- **CLAUDE.md keeps its structure.** Only its README pointers change.
- **No deck changes**, so no parity run. Say so in each PR.

## Steps, one PR each

1. **`latex/README.md`**: the LaTeX chapter, the largest self-contained block. It includes the
   Overleaf table, whose links serve `releases/latest`.
2. **`docs/formats.md`, `docs/container.md` and `docs/other-repos.md`.**
3. **`docs/authoring.md`, then the README rewritten as the front page** with the "Where next"
   table. Retake `make screenshots` only if a slide title changes; none should.
4. **A docs link check, `tests/test_docs.py`**, in `make test` and in CI (the LaTeX/engine job's
   test step). It checks that:
   - every relative link and `#anchor` in the tracked `*.md` files resolves (GitHub's anchor
     rule: lower-case, spaces to `-`, punctuation dropped);
   - every `README "X"` and `<guide> "X"` names a heading that exists.

   It could come first, as step 0, so that steps 1-3 run under it. The implementer's choice;
   say which in the PR.

## Acceptance

- The README is at most about 200 lines, and a newcomer gets from it alone to a deck built in
  all three formats.
- Every section of today's README has a home, or is a listed cut.
- `tests/test_docs.py` passes in `make test` and CI.
- `git grep 'README "'` names only headings that exist.

## How to check

- `make test` (with `test_docs.py`).
- Look at each moved guide in the PR's rich diff on GitHub: images shown, links followed, the
  tables rendered.
- Read the new README top to bottom as a newcomer, then run its quick start in a fresh clone (or
  in the container: `docker run ... make` in a copy of `decks/quickstart`).

## Do not

- Change what a deck renders, or the decks' own text.
- Rewrite content while moving it. A wording pass, if Ben wants one, is its own PR.
- Leave a stub heading or a "moved to" note in the README.
- Move `design/` or `CHANGELOG.md`, or merge `liveries/REFERENCE.md` into a guide (it is
  generated).

## Pointers

- The README's sections and line counts: `awk '/^## |^### /' README.md` (mind the fenced
  examples).
- References to README sections: `git grep -n 'README "'`, and `git grep -n README -- '*.py'
  '*.sty' '*.lua' 'Make*'`.
- Companion docs today: `liveries/README.md`, `liveries/REFERENCE.md`, `decks/plots/README.md`,
  `CHANGELOG.md`.
- Earlier README work: `design/docs-handoff.md` (2026-10-17, the multi-brand rewrite).
