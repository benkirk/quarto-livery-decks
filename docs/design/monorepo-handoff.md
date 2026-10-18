# Monorepo handoff

The canonical copy is issue [#57](https://github.com/benkirk/quarto-livery-decks/issues/57); this file is its complement in the tree. Update the issue when the plan changes, and this file with it.

Handoff for a fresh session. Read this, then `CLAUDE.md`, then `docs/design/engine-and-liveries.md` §10 (the log). Written 2026-10-18 from an "unplanned city" retrospective of this repo and the engine; Ben chose the bold option: **one repository**.

## Why

The engine (`benkirk/beamer-livery-theme`, vendored here as `docs/common/_extensions/benkirk/engine/`) and this framework are one product with one author and, soon, customers who own a livery. Today a livery is a contract against two version numbers, and the seam runs through the middle of the pptx format:

- 11 of the 26 entries in the design log are an engine release **plus** a framework branch; 39 commits here are vendor syncs (`quarto update` / `make vendor-engine`); CLAUDE.md carries nine `engine >= x.y.z` gates.
- The pptx format is half engine (`livery_template.py`, `pptx_waves.py`: the template) and half framework (eight post-processors in `docs/common/utils/` that read `livery.json` and draw the rest: `slide_layout.py` `draw_cover`/`band_stack`, `section_subtitle.py`, `style_tables.py`, …).
- `docs/common/utils/livery.py` is a shim that loads the engine's reader by file path and `globals().update()`s it, and `engine_module()` reaches `livery_build.mono_font` the same way: two repos sharing a module through the file system.
- The pptx chain is eight scripts, eight open/decompress/save cycles, three XML stacks (raw zip+regex in `enable_autofit`/`embed_fonts`, lxml in `section_subtitle`, python-pptx in the other five), the step order living only in `Make.common`'s recipe, and **two text-height estimators** (PIL on the real font in `section_subtitle.py`; a 0.5-em-per-char guess in `slide_layout.py` `_text_height` and again in `band_stack`).

The engine's reasons to stand alone (Overleaf users, cherry-picks from `NCAR_beamer_template`) both survive a merge: the per-livery Overleaf zips are already this repo's release output, and the `upstream` remote still works from any checkout. Ben has decided to retire `beamer-livery-theme` before this repo gains customers.

## Decisions (made with Ben, 2026-10-18)

1. **Merge the engine repo into this one, with its history**, and archive `benkirk/beamer-livery-theme`.
2. `benkirk/NCAR_beamer_template` is untouched and no longer cherry-picked from; a fix wanted there is ported by hand. (If Ben meant it should be archived too, that is his call, not this issue's.)
3. After the merge, every reader of `livery.json` lives in the engine directory: the pptx post-processors and the pptx-only Lua filters move in, as a third contributed format `engine-pptx`. The framework that remains is Make, deps, livery switching, QA, site, container: thin and stable.
4. One version number. Proposal: continue the engine's line, the merge release being **v4.0.0** (`_extension.yml` `version:` equals the tag, as the engine's `release.yml` already requires). Ben may prefer continuing the framework's `v1.x`; ask before tagging. Tags stop being re-cut from this release on (#58 makes that policy).

## Target layout

```
docs/common/_extensions/engine/      the engine, source (was _extensions/benkirk/engine/, vendored)
  *.sty *.lua *.scss *.js *.theme title-slide.html talk.tex
  livery.py livery_build.py livery_template.py livery_check.py pptx_waves.py overleaf_zip.py
  pptx_post.py                       phase B: the eight post-processors as one driver
  *.lua for pptx (phase B)           slide-layout, notes-last, single-body, strip-raw-figure, diagram-dark, linked-images
docs/common/liveries/                ONE directory: ncar ucar ncarucar ucp cu nsi nasa nasa-dark
                                     (ncar becomes a real directory, not a link into the engine)
docs/common/utils/                   what is left: deck_qa.py comp_measure.py site_index.py livery_inspect.py
                                     livery_check.py (the --qa wrapper), gallery/screenshots stay in docs/quickstart
docs/latex/                          the engine's pure-LaTeX examples: examples/*.tex, variants, latexmkrc,
                                     images/, its Makefile targets (default/examples/variants/previews/diagrams)
tests/                               the engine's tools/test_compositions.py, tools/test_type.py, tools/parity.sh
                                     (→ parity-latex.sh) and this repo's utils/parity.sh (→ parity.sh)
docs/design/                         this repo's copy of engine-and-liveries.md is canonical; the engine's pointer copy is dropped
```

Keep the extension's relative path the same as in the engine repo (`_extensions/engine/`): the engine's tests reach it as `ROOT / "_extensions" / "engine"` and need only a new `ROOT`.

## Steps, one PR each unless noted

**Phase A: the merge (byte-identical outputs).**

1. **Baseline.** `docs/common/utils/parity.sh baseline` (ncar, cu, nsi, plus `PARITY_LIVERIES="nasa nasa-dark"` in a second run or extend the default) and, in the engine checkout, `tools/parity.sh baseline`. Same day, same checkout (the `date: last-modified` trap in the script's header).
2. **Import the history.** On a fresh clone of the engine: `git filter-repo --to-subdirectory-filter engine-import` (pip `git-filter-repo`; `git subtree add --prefix` is the fallback if filter-repo is unavailable, at the cost of `git log --follow` across the move). Then here, on a branch: `git merge --allow-unrelated-histories` of that clone, and move files from `engine-import/` into the target layout in the same PR, so the diff reviewed is the move. Drop the engine's `_baseline/`, `_check/`, build outputs, `docs/design/engine-and-liveries.md` (the pointer), `talk-quarto.qmd` (the quickstart is its twin).
3. **Delete the vendored copy** (`docs/common/_extensions/benkirk/`) and replace `docs/common/liveries/ncar` (a symlink) with the real directory; move ucar, ncarucar, ucp beside it. Every path that said `_extensions/benkirk/engine` → `_extensions/engine`: `Make.common` (`OVERLEAF_ZIP`), `utils/livery.py` (`ENGINE`), `utils/livery_check.py`, `livery_inspect.py`, `ci.yaml`, `release.yml`, `Dockerfile`, README, CLAUDE.md, the design docs that still matter (leave the historical handoffs alone).
4. **The bundled-livery default.** The Lua filters default `livery:` to `<extdir>/liveries/<brand>` (`engine-beamer.lua` ~L341, `engine-revealjs.lua` ~L90) and `_extension.yml` names `liveries/ncar/build/livery.theme`. Trap: a deck directory reaches the extension through a symlinked `_extensions`, and Lua does not resolve symlinks, so an extdir-relative `../../liveries` resolves against the deck directory and is wrong. Decide: in Quarto the livery is always explicit (`Make.common`'s `_livery` link and `livery: _livery`; the `brand=` fallback may simply resolve to `<extdir>/../../liveries/<brand>` with a clear error when absent), and in LaTeX `brand=` keeps resolving through `TEXINPUTS` (`docs/latex/Makefile` adds `docs/common//`). `overleaf_zip.py`'s zip layout (`liveries/<name>/` beside `_extensions/engine/`) is self-contained and unchanged.
5. **Root `Makefile`**: delete `vendor-engine` and `ENGINE`; add `latex` (→ `docs/latex`) and `test` (→ `tests/`). **`Make.common`**: nothing changes in phase A beyond the path.
6. **CI**: the engine's `ci.yml` steps become one `latex` job in `ci.yaml`, inside the container (it has TeX Live, Quarto, Chromium, poppler): `tests/test_compositions.py`, `tests/test_type.py`, `make -C docs/latex examples variants`, the `pdffonts` Poppins and math-font checks. Dedupe against what `sample` and `livery` already do (`livery_build.py --check`, `livery_check.py`, the per-livery Overleaf compile). The engine's `release.yml` tag-equals-version check moves into this repo's `release.yml`. `cron-clean-action-log.yaml` unchanged.
7. **Docs**: README gains a "LaTeX" chapter from the engine README's Quick Start (LaTeX rows), Theme options, Math fonts, Colors and the 2020-brand appendix; the engine's preview PNGs land in `docs/latex/`. CLAUDE.md: rewrite "What this is" for one repo, delete the vendoring paragraph and every `engine >= x.y.z` gate (history now, not a contract), fold the engine CLAUDE.md's "by area" list in. Design log §10: one entry for the merge.
8. **Parity check**: `parity.sh check` on every livery; the engine's `parity-latex.sh check`. Everything identical (use `NORMALIZE` for the `_extensions/benkirk/engine` → `_extensions/engine` path if it appears in any snapshot; it should not, the HTML dependency is named `engine-revealjs-<version>`).
9. **Retire**: archive `benkirk/beamer-livery-theme` on GitHub with a README banner pointing here; its releases stay downloadable. Remove this repo's references to `quarto update benkirk/beamer-livery-theme` (README L394, CLAUDE.md). Memory note for Claude: `gh` in the engine checkout defaulted to `upstream`; that checkout can be deleted.
10. **Tag v4.0.0** (or Ben's choice), after asking.

**Phase B: pptx made whole (after A is merged; one PR per bullet, outputs byte-identical until the last).**

11. **`engine-pptx` format.** `_extension.yml` contributes `pptx` with `reference-doc`, `highlight-style`, `slide-level: 2`, `toc: false` and the pptx-only filters in their current order (`strip-raw-figure`, `slide-layout`, `notes-last`, `single-body`, `linked-images`, `diagram-dark`). `linked-images.lua` and `diagram-dark.lua` also serve beamer/revealjs: declare them on those formats too. `_quarto.yml` loses its `filters:` block and `Make.common` the `_engine` link (check nothing else uses `_engine/`). `diagram_dark.py` moves beside its filter.
12. **`pptx_post.py`.** The eight scripts become one driver in the engine directory: open once (python-pptx; `enable_autofit`'s and `embed_fonts`' raw-zip work can be done on the package `python-pptx` holds, or as a final zip pass), the steps as functions in today's order with the order's reasons as comments (`type_step` last; `section_subtitle` first), save once. `Make.common`'s recipe becomes `quarto render … --to engine-pptx` + `python3 $(PPTX_POST) $@`. `utils/livery.py` and `engine_module()` are deleted (same directory now: a plain import, or `sys.path`). Optional: a Lua filter sets `meta.monofont` from `livery.json` so `LIVERY_MONO` leaves `Make.common` too. Byte-identical (parity).
13. **One text measurer.** Replace `slide_layout.py`'s two heuristics with `section_subtitle.py`'s PIL measurement on the livery's font (a shared helper). This one changes output on purpose: `make measure` and `make qa` on quickstart, sample and fixtures under every livery, a contact sheet for Ben before merging.

## Acceptance

- `git log --follow docs/common/_extensions/engine/beamerouterthemeEngine.sty` shows the engine's history.
- No `_extensions/benkirk`, no `vendor-engine`, no `quarto update` instruction, no shim, no `_engine` link (after B).
- `parity.sh check` identical for every livery after A and after B.12; `make qa` and `make measure` green under every livery after B.13 (MEASURE_FAIL as CI has it).
- `ci.yaml` green including the new `latex` job; `release.yml` publishes eight Overleaf zips on the tag, each compiling in a clean directory.
- `beamer-livery-theme` archived with a banner; this README's Overleaf table unchanged (it already points at this repo's releases).

## Do not

- Rewrite the post-processors' logic in phase A or B.12: moves and renames only, parity-checked. B.13 is the one behavioural change and stands alone.
- Edit `template.pptx` by hand (regenerate with `livery_template.py`); the templates must rebuild byte-identically after the move (`livery_check.py` checks this).
- Touch `NCAR_beamer_template`.
- Re-cut a tag once v4.0.0 is out (#58).

## Pointers

- `docs/Make.common`: the pptx recipe (`render_pptx`), the five links and the `.livery` stamp (keep), `LIVERY_FILES`/`LIVERY_MONO` (the shim's two commands).
- `docs/common/_quarto.yml`: the six filters by `_engine/` path; `livery: _livery`.
- The engine checkout's `Makefile` (its LaTeX targets and `TEXENV`), `.github/workflows/ci.yml` (the steps to carry), `CLAUDE.md` (the "by area" list), `README.md` (the chapters to carry).
- `docs/design/engine-and-liveries.md` §5 (the engine contract) and §10; `docs/design/composition-handoff.md` for the shape of a handoff that worked.
- Memory for Claude in `~/.claude/projects/…/memory/`: `gh-repo-flag-engine.md`, `sprint-tags-recut.md`, `minimal-prs-versions.md` need updating when this lands.
