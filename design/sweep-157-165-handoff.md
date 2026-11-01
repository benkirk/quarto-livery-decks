# Handoff: the sweep of #157–#165 and the 26.11.0 release

**State (2026-11-01):** the sweep ran the same day (`design/unplanned-city-ledger.md`, the entry
for this window: seven findings, Ben's picks landed as #167); the release steps below are the
release PR's.

Written 2026-11-01 for a fresh-context session. The window is `adb9cd2` (Release 26.10.13) to
`main` after #164 merges (`540f4c5`); six squash merges and nothing else:

| PR | What | Squash |
|---|---|---|
| #160 | `quarto <1.10` pin (superseded by #165, which lifted it) | `444314f` |
| #162 | #158: a deck's `requirements.txt`, `make deps`, a cached venv on PYTHONPATH (`common/utils/deck_deps.py`, Make.common, CI) | `ff232ed` |
| #157 | a colleague's: a list under a table or picture, and in a cell, keeps its bullets in pptx (`single-body.lua`, `grid.py`, `style_tables.py`, `deck_qa.py`); its review landed F1–F3 (`note_style` names the shape "Note", `C.marker`, the sample slide) | `8348909` |
| #163 | #66: nasa-dark's highlight `blue-tint` (HDS); the NASA roles stay | `14a6102` |
| #165 | #161: Quarto 1.10 in the image and the env (pandoc 3.10, `QUARTO_TYPST_GATHER`), reevaluate notes in `single-body.lua` and `notes_clrmap.py` (#166) | `16ecb63` |
| #164 | the issue sweep: #142 `::: {.lead scale=}`, #143 `DECKS_RUNTIME=conda` (`common/Make.conda`), #87's CI step, #124's notes | `540f4c5` |

Issues: #158, #161, #66, #142, #143 closed by the PRs; #124 and #87 ticked with comments; #166
new (two pptx workarounds pandoc fixes in 3.10.1 and 3.13); #118, #141, #144, #154 untouched.

## Seams noticed while landing these (for the sweep's lift / consolidate / drift passes)

- **Two one-sub-make files with one shape.** `common/Make.conda` copies `Make.container`'s
  `$(DECKS_GOALS)` / `.PHONY` / `$(DECKS_GOALS): decks-<x>` / `@:` pattern. A shared snippet
  (`common/Make.dispatch`?) each includes, or one file with the run line per runtime. Both must
  stay 3.81-safe. `publish` differs: the container maps it to `site` and pushes on the host;
  conda runs it inside (same host).
- **A second marker writer.** `C.marker` (engine-common.lua) is the paragraph writer both pptx
  filters use since #157's F2, but `grid-pptx.lua`'s `prefixed()` still builds the inline
  `"⟦engine:" .. word .. "⟧"` string itself. One constant or one function for the marker text.
- **A shape's name as a signal.** `slide_layout.note_style()` names the caption shape "Note" so
  `grid.py`'s list pass leaves it centered; `grid.py` already reads "Body list", "Lead", "Card n"
  names. Fine, but the convention (names are an interface between steps) belongs in
  `pptx_steps/common.py`'s docstring or CLAUDE.md's pptx bullet, if it is not there.
- **Two `flat()` helpers over make's output.** `tests/test_new_deck.py` and
  `tests/test_deck_deps.py` each join `make -n`'s continuation lines; conftest could hold one.
- **`scale_attr` and `scale_paragraphs`.** engine-common's `scale_attr()` is the one reader for
  the heading's and the lead's `scale=`; `slide_layout.scale_paragraphs()` went public for
  `grid.py`'s lead. Check nothing else parses `scale=` or scales runs by hand (`type_step.py`?).
- **Prose describing an earlier step.** `docs/formats.md` says "You need Quarto 1.6 or newer
  (the conda env pins it)": the env now pins `>=1.10`; the engine's floor (pandoc ≥ 3.2.1,
  `\pandocbounded`) and the env's pin are two different numbers and should read so. CLAUDE.md's
  "Runtime" bullet grew the conda branch; its "PDF" bullet still says "Quarto >= 1.6" (the floor,
  fine). `docs/container.md` "Per runtime" lists Docker, Podman and Apptainer; `conda` is only in
  the `DECKS_RUNTIME` bullet.
- **The deck-deps naming.** `DECKS_DEPS` (the root) vs `DECK_REQS`/`DECK_SITE` (per deck) vs
  `DECK_DEPS_PY`: three prefixes in one block of Make.common. `deps-<key>` folders under the
  release's HOME in a container, under `~/.cache/quarto-livery-decks` natively.
- **A path only one runtime exercises.** `smoke-test.sh` 3b's `make deps pptx` runs under
  Docker in `image.yaml` and under Apptainer and Podman in `runtimes.yaml` (weekly and on
  demand); `apptainer-extra.sh`'s lived-in-HOME table has no row for a deps folder of another
  Python (a `report` row would be the convention).
- **The consumer job now runs a kernel** (`engine: jupyter` for the tabulate cell): the hello
  deck is no longer the minimal consumer; a second, minimal deck or a note that it is meant to
  exercise the kernel path.
- **`livery check --qa /tmp/scaffold` in CI** rebuilds the quickstart a second time in the sample
  job (~3 min). Acceptable; a sweep may prefer it in the `livery` matrix as one more entry.
- **The CHANGELOG's `[Unreleased]` ordering** is by insertion fights (1.10, #142, #143, #158,
  #157's three, then Liveries): worth one read for order and voice before the release renames it.

## The release, after the sweep (Ben: "pause before tag or release")

1. `version: 26.11.0` in `_extensions/engine/_extension.yml`; `livery build liveries/*/` (every
   `build/livery.json` restamped; commit `build/`); the pins `@v26.11.0` in `docs/other-repos.md`
   (the consumer example and `build-decks.yaml@v…`, the image tag `:26.11.0`) and
   `decks/plots/README.md` (the pip install); `tests/test_docs.py` holds them.
2. CHANGELOG: `## [Unreleased]` → `## [26.11.0] - <date>` with a one-paragraph summary (Quarto
   1.10, deck deps, the pptx list fixes, lead scale, the conda runtime, nasa-dark's highlight) and
   the link block (`[Unreleased]: …compare/v26.11.0...HEAD`, `[26.11.0]: …releases/tag/v26.11.0`).
3. On the Mac: `make all` in quickstart, sample, fixtures and plots, then `tests/app-open.sh`
   (Keynote and PowerPoint open every deck; the sample's new list-under-a-table and scaled-lead
   slides are in it). Ben's step.
4. The release PR merges; **Ben cuts the tag** `v26.11.0` (`release.yml` checks the version, the
   changelog entry, the tag's novelty; attaches the Overleaf zips and charts bundles). Never move
   a tag. Then `make sif` on Casper's shared install (memory: casper-apptainer-testing) and a
   `touch conda-env` or a `make conda-env` for local envs (1.10 needs the rebuild: ~10 min).

## Housekeeping

- Scratchpad worktrees of the 2026-11-01 session (`git worktree list`): pin, deps, nasa, q110
  (merged) and sweep; `git worktree remove` each once #164 is in.
- `decks/*/_qa/` in the main checkout hold the 1.9.38 before-shots; the 1.10 after-shots are in
  the q110 worktree; `scratchpad/slidediff.py` is the per-slide pixel diff used (worth a home in
  `common/utils/` if a second Quarto bump comes: #166).
