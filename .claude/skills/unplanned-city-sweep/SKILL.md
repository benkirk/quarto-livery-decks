---
name: unplanned-city-sweep
description: >-
  A retrospective sweep for the duplication, drift and cruft that only shows
  once a run of related PRs has landed: helpers to lift to a common home, one
  concept drawn once per format without shared livery data, prose describing an
  earlier step, a path only one runtime exercises, and plans ready to retire.
  Load after a series of merges (window mode) or to sweep one area of the tree
  (area mode). Produces a ranked report for Ben to pick from, then one PR with a
  commit per picked finding, and updates the ledger.
---

# Unplanned-city sweep

A city that grew without a plan works street by street and makes no sense from the air. A run
of PRs does the same: each was right alone, and the drift is between them. This sweep reads them
from the air.

The output is a **ranked report first**. Ben picks; the picked findings become one PR with a
commit each; the rest go to the ledger, `design/unplanned-city-ledger.md`. "Nothing worth
doing" is an acceptable report.

## 1. Pick the mode

- **Window.** Read everything merged since the ledger's newest *window* entry's end commit (an
  area entry's is where it branched, not where the reading stopped), or the PRs Ben names.
  `main` takes squash merges, so each commit is one PR: find the range with
  `git log --oneline <end>..origin/main`, then read each PR body (`gh pr view N --json body`)
  and the combined diff (`git diff <end>..origin/main`).
- **Area.** One of `engine-py` (`_extensions/engine/*.py`, `pptx_steps/`, `mpl/`), `lua`
  (`_extensions/engine/*.lua`), `themes` (the beamer `*.sty`, the revealjs `*.scss`, `*.css`,
  `*.js`, `title-slide.html`), `make-container` (`Make.common`, `Makefile`, `common/`,
  `Dockerfile`, `etc/`, `bin/`), `ci` (`.github/`), `liveries` (`liveries/*/livery.yml`, the
  schema, `liveries/README.md`), `docs` (`CLAUDE.md`, `docs/`, `README.md`, `design/`), read
  across the whole tree. Start from the ledger's untriaged list for that area.

Branch from `origin/main` before changing anything.

## 2. Read as one design

Apply the unplanned-city litmus to the window as a whole, not per commit:

- prose (docstrings, CLAUDE.md, `docs/`, a Makefile's comments) still describing an earlier
  step's behavior (#96's docs still said Apptainer used the real HOME after it stopped)
- a later step putting a silent or untested path on the default route
- the one branch a later step's assumptions rest on being the untested one
- a later step resting on a path only one runtime exercises (native, docker, podman,
  apptainer; the host side under GNU make 3.81, dash and BSD tools)
- a format drawing a thing on its own numbers while the other two read `livery.json`
- two records of progress that stopped agreeing (the roadmap's log in `design/` and
  `CHANGELOG.md`; the #95–#103 sprint reached only the changelog)

## 3. Run the inventory

By recipe, no script (a recipe that keeps paying becomes a script with a test). Every grep is a
lead, not a verdict: read the code before reporting anything it lists.

```bash
# engine-py: a _private name imported across modules; the same helper in several pptx_steps/
grep -rnE 'import .*\b_[a-z]|from \S+ import .*\b_[a-z]' _extensions/engine --include='*.py'
grep -rhoE '^def [a-z_]+' _extensions/engine/pptx_steps/*.py _extensions/engine/*.py | sort | uniq -c | sort -rn | awk '$1>1'
# a concept implemented once per format without shared livery data
grep -rnE 'engine@geom@|--engine-|compositions|type_pt|canvas_scale|livery\.mark' _extensions/engine --include='*.sty' --include='*.scss' --include='*.lua' --include='*.py' -l
# roles only: palette names and raw colors outside build/livery.sty; !important in the scss
grep -rnE '#[0-9a-fA-F]{6}\b|!important' _extensions/engine --include='*.scss' --include='*.css' --include='*.sty' --include='*.lua' --include='*.py'
# Lua duplicated between the two format filters
grep -hoE '^local function [a-z_]+' _extensions/engine/engine-revealjs.lua _extensions/engine/engine-beamer.lua | sort | uniq -d
# docs claims against the code: every file, target and flag CLAUDE.md names still exists
grep -oE '`[A-Za-z0-9_./-]+\.(py|lua|sty|scss|js|yml|yaml|md|sh|mk)`' CLAUDE.md | tr -d '`' | sort -u | while read -r f; do git ls-files --error-unmatch "$f" >/dev/null 2>&1 || find . -name "$(basename "$f")" -not -path './conda-env/*' | grep -q . || echo "named, not found: $f"; done
```

The docs gate (`tests/test_docs.py`) already holds every relative link and quoted section
pointer; the last recipe is for the names it does not read (a file named in backticks, a make
target, a flag). Expected hits, not findings: the scss's `$engine-*` hexes (ncar's values as
compile-time defaults, by design) and its `!important`s under `html.reveal-print` (reveal's
print sheet forces padding); CLAUDE.md names that live outside the tree (`activate.d/quarto.sh`,
`quarto.js`, `site.mk`); the OKLab `mix` in `livery_charts.py` and `mpl/livery_mpl.py` (the mpl
helper ships alone in the charts zip and may not import the engine).

## 4. Heuristic passes

Run each pass and collect findings. The examples are real.

- **Lift.** A helper two modules both need wants one public home in the layer both can reach.
  Example: `common/image.mk`, the image name and tag shared by `Make.container` and the top
  Makefile's `make sif` (#97). A `_private` name imported across modules, or the same helper
  written in two `pptx_steps/`, is the same shape; so is a value computed in a Makefile and
  again in Python.
- **Consolidate.** One concept done once per format, each on its own numbers, goes behind
  shared `livery.json` data read by one drawer per format. The compositions are the model
  (`livery_build.py` derives the boxes; beamer `\engine@drawcomp`, the revealjs
  `--engine-cmp-*` properties, `field_layout()` and `slide_layout.py` read them). Three
  implementations of one look that have drifted are a finding even at real refactor cost.
- **Convention drift.** Several idioms for one thing. The version's two homes
  (`_extension.yml` and a hand-copied `VERSION` in `engine-revealjs.lua`, until #108); a size written in points in one
  place and inches in another; a path resolved relative to the deck in one recipe and the
  framework in the next. Pick the house idiom and move the others to it. Grep the idiom across
  the layer before proposing.
- **Bypassed helper.** A lifted helper fixes nothing until its call sites use it, and the sites
  that still hand-roll the idiom are invisible to a duplicate grep: each copy is one line.
  After any lift, grep the raw idiom across the layer: a post-step reading a point size from
  `livery.json` by key instead of `livery.type_pt()`, an absolute pad not scaled by
  `livery.canvas_scale()`, a mark chosen by name instead of `livery.mark(livery, role, ...)`.
- **Delete.** Dead scss (a class nothing in the Lua or the templates emits), a Lua function
  nothing calls, a compatibility shim or alias whose callers are gone (none should exist:
  memory `no-compat-shims`), an option no caller passes, a Makefile variable nothing reads.
  A keyword parameter with a comment and no caller: grep each `name=` parameter's call sites;
  `grid.py`'s `top_only` was documented at its one call site, which never passed it (#105–#126).
- **Retire plans.** `design/` holds this repository's plans, handoffs and progress logs. A plan
  whose PRs have merged and whose next step is done is marked so (its progress section names
  the state) or folded into the roadmap, `design/engine-and-liveries.md`; a dated handoff
  stays as a record. Run window mode right after the merge that lands a plan's last step.
- **First run and runtime matrix.** The incidents of #95–#102 as a checklist against the
  window: a new host-side variable or path under Apptainer's `--cleanenv` and its own HOME; a
  cache the first run builds into an empty HOME; a timeout tuned on a fast machine; a recipe
  read under GNU make 3.81, dash and BSD tools; a release step that assumes an artifact the
  same release has not published yet (#101). Each is a trace with the concrete input that
  broke it, or it is not a finding.
- **Gate drift.** An element's walk is gated on a different slide set per format (`content_heading`
  with one format's kinds table, every slide in another), so one input parts them: the element on
  a composed slide, a divider or an untitled slide. Name the input and gate all three alike
  (`composed_kind()`, #127–#135: a gallery on a `.closing` slide drew in PDF and pptx, not HTML).
  Its cousin: a format filter calling a common reader twice on the same blocks, the second run on
  attributes the first mutated (beamer's `.full` frame called `split_full` twice).
- **Ratchet.** Where a fix is cheap to pin, add an equality ratchet so the city does not
  regrow. Models: `tests/test_docs.py` (every link and section pointer resolves),
  `tests/test_compositions.py`'s `EXPECTED_DELTAS` (every decided move of a box is a row),
  `livery build --check` (the generated files match). Only ratchet a count that is going down.
  A doc example pinned to a release (`@vX.Y.Z`, an image tag in prose): hold it to
  `_extension.yml`'s version, as `tests/test_docs.py` holds docs/other-repos.md's.

## 5. Report

One ranked list. For each finding, give:

| field | content |
|---|---|
| category | lift, consolidate, drift, bypassed helper, delete, retire, first run, ratchet |
| where | `file:line` for each site |
| proposal | the target home or shape, in one sentence |
| cost | files touched; whether parity, a baseline, `EXPECTED_DELTAS` or a screenshot moves |
| risk | whether a rendered deck, a livery's build or a consumer's Makefile could change |

Rank by value over cost. Mark anything that changes what a deck renders. Then stop and let Ben
pick.

## 6. Do the picked work

- One branch and one PR against `main`, with a commit per finding. Each commit passes its own
  tests (`make test`; `make -C decks/<deck> qa` for a deck or theme). Stage each commit by file
  (`git add <files>`, never `-a`): an edit waiting for its own commit rides into the next one
  otherwise (#127–#135: the CI step landed inside a Python commit and had to be split out).
  Findings in disjoint files can go to agents in worktrees in parallel (the Python steps, the
  inner theme, the scss ran beside the Lua work); a worktree is cut from `main`'s head, so the
  brief names the branch tip to reset to, and each agent takes its own baseline there and proves
  its commits flat before the lead cherry-picks them. Quarto ignores the project of a deck under a
  hidden directory (the Agent tool's `.claude/worktrees/`: `quarto inspect` shows no project, so
  the render takes the extension's defaults, ncar's template, and `LIVERY=` reaches only the
  Python steps): an agent renders its proofs from a `git archive` of its commit, or a copy of the
  deck, outside it (#136–#149). `make test` is unaffected.
- **If output could move**, capture it before and after and compare, by what can move:
  `tests/parity.sh baseline` on `origin/main` and `check` on the branch (every deck of
  quickstart, sample, fixtures and plots under ncar, cu and nsi; same checkout, same day);
  `make measure` in `decks/quickstart` when a composition drawer changes; `tests/parity-latex.sh
  baseline|check` for the LaTeX side; a Sass change is screenshotted slide by slide before and
  after (CLAUDE.md "revealjs (HTML) theme"). Keep throwaway capture scripts in the scratchpad,
  never in the tree.
- **A change meant to change looks** cannot use parity as its proof: shoot before and after and
  review by eye, name every departure in its commit and in the ledger entry.
- A change that measures flat, or a refactor that turns out to cost more than it saves, is
  dropped and recorded with its numbers, not shipped.

## 7. Close out

- Add a ledger entry: mode, range or area, end commit (in area mode, the `origin/main` commit
  the branch started from), done (with the PR), tried and dropped (with numbers), open items.
- Move the unpicked findings onto the entry's open list or the untriaged list.
- **Growth rule:** when a sweep meets a new class of problem, add the heuristic here in the
  same PR. A recipe in step 3 that has paid in three sweeps becomes a script under
  `common/utils/` with a test in `tests/`.

## Boundaries

- No compatibility shims: a rename moves every caller in the same PR and keeps no alias
  (memory `no-compat-shims`). A sweep removes code more often than it adds it.
- Roles only: no palette name outside `build/livery.sty`; the themes read `var(--engine-*)`,
  `EngineData*` and the roles (CLAUDE.md "The engine").
- A livery's `livery.yml` key is renamed only with Ben's agreement; `template.pptx` is
  generated, never edited.
- Do not build for failures nobody has seen.
- A refactor may change what a deck renders, but say so in the commit and in the ledger, with
  the parity or measure deltas that prove how much.
- A lifted helper keeps a one-line docstring; the comment density stays the file's.
