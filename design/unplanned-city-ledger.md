# Unplanned-city ledger

The record of the `unplanned-city-sweep` skill (`.claude/skills/unplanned-city-sweep/SKILL.md`):
each sweep over a window of merged PRs or an area of the tree adds an entry, newest first, and
the findings nobody picked wait in **Untriaged** until a later sweep takes them up or drops them.
Window mode starts from the newest entry's end commit.

## Entry format

```
## <date>: <window #a–#b | area <name>>

- Mode: window | area
- Range: <end of the previous entry>..<end commit> (window), or the area name
- End commit: <sha> (the `origin/main` commit the sweep read up to, or branched from)
- Done: <finding> (#PR), ...
- Tried and dropped: <finding>: <the numbers that said no>, ...
- Open: <finding>, ...
```

## Entries

## 2026-10-20: area tests

- Mode: area
- Range: `tests/`, `make test` and CI's engine-test step, read after #113 landed the ninth script
- End commit: `4ab788f`
- Done (#115): the nine scripts as pytest modules, discovery the one list of tests (the
  Makefile's and CI's hand-kept lists had drifted: `test_charts.py` never ran in CI); CI's step
  calls `make test`; the duplicated `livery schema --doc --check` dropped (test_schema holds the
  reference current); the harness once in `tests/conftest.py` (ROOT, the per-livery argument, the
  pandoc deck helper the two pptx-step tests each carried, the livery subprocess); pytest-xdist
  from the start, `-n auto --dist loadfile`, with the rules that keep the suite parallel
- Tried and dropped: none
- Open: none

## 2026-10-20: window #95–#103

- Mode: window
- Range: `113892d..62d6568` (#95–#103: the runtime sprint, the shared installation, the first-run
  fixes, releases 26.10.1 and 26.10.2); read in #106's dry run, done after 26.10.3
- End commit: `62d6568`
- Done (#108): engine-common.lua for the six functions both filters carried; the version read from
  `_extension.yml` by the revealjs filter, with a test pin; luminance, contrast and mix once in
  `livery.py`, the tools importing each other by name (the tests' by-path loading and
  `_sibling()` gone); the roadmap's log closed at 26.10.0; CLAUDE.md's test list
- Tried and dropped: none
- Open: the `version:` line's three shell readers (`image.mk`, `release.yml`, `ci.yaml`), which must
  stay shell since the host side runs without Python; `livery_mpl.py` keeps its own reader because
  it ships alone in the charts zip

## Untriaged

- `engine-revealjs.scss`: the section, closing and feature-cover slides carry one identical
  flex-column declaration block each (`display: flex !important` and the column padding); a mixin
  candidate, cosmetic.
- The six Lua functions that share a name across the two format filters with format-specific
  bodies (`take_layout`, `wrap_layout`, `unwrap_layout`, `hoist_footnotes`, `split_full`,
  `size_plots`): a consolidate candidate if their bodies converge; read before touching.
