# Handoff: #57 Phase B, the pptx format made whole

Written 2026-10-18 at the end of the charts work, for a fresh session. Read this, then
`CLAUDE.md`, then issue #57's "Phase B" section (`gh issue view 57`; its paths predate the
flatten: `docs/common/...` is now `common/...`, `docs/Make.common` is `Make.common`), then the
newest entries of `design/engine-and-liveries.md` section 10. Release v1.1.0 comes after Phase B
(Ben, 2026-10-18), and the tag is cut only when he says so.

## State

- **Charts and plots are done**, design steps 1-5 (`design/charts-and-plots.md`): #64, #67, #68
  and #69 squash-merged in order, then #70 (cu's campus colors, vivid NCAR maps, the plots
  README, small fixes). If #69 or #70 is still open, land it first: `gh pr checks`, then
  `gh pr merge --squash`.
- **`main` is protected.** It takes PRs only (no approval needed), keeps a linear history and
  has 12 required checks: the image manifest merge, the LaTeX and engine tests, the consumer
  job, the sample/quickstart/fixture/plots job, and one `Check livery <name>` per livery. Squash
  is the only merge method, and branches are deleted on merge. Renaming a CI job, or adding or
  renaming a livery, means updating the required list
  (`gh api repos/benkirk/quarto-livery-decks/branches/main/protection/required_status_checks/contexts`).
  Ben has admin bypass.
- **CI runs on PRs into `main` (or `staging`), docs-only ones included.** A stacked PR gets its
  checks only once it is retargeted to `main`. Changing the base does not start a run; a push,
  or a close and reopen, does.

## The plan (one PR each, as #57 says)

**B.11, the `engine-pptx` format.** `_extensions/engine/_extension.yml` contributes `pptx` with
`slide-level: 2`, `toc: false`, `highlight-style` and the pptx filters in today's order:
`strip-raw-figure`, `slide-layout`, `notes-last`, `single-body`, `linked-images`,
`diagram-dark`. `linked-images` and `diagram-dark` serve beamer and revealjs too, so declare
them there as well. The six `.lua` files move from `common/` into the extension, and
`common/utils/diagram_dark.py` moves beside its filter. `common/_quarto.yml` loses its
`filters:` block and sets `engine-pptx:` options instead of `pptx:`. In `Make.common`, the pptx
recipe renders `--to engine-pptx`. Outputs stay byte-identical.

Check before deleting the `_engine` link. It has these users:
- `Make.common`: `DEPS` and the link's rule;
- `ci.yaml` line ~211 (`ls -l ... _engine ...`);
- `common/diagram-dark.lua`, whose fallback path is `_engine`;
- `decks/quickstart/screenshots.py` and `decks/plots/gallery.py`, which import
  `_engine/utils/deck_qa.py`;
- prose in `decks/sample/sample.qmd`.

To verify: a per-deck `reference-doc: _livery/template.pptx` has to override the extension's
default (Quarto resolves an extension's paths lexically against the extension's directory; the
`highlight-style` default is `../../liveries/ncar/build/livery.theme`).

**B.12, `pptx_post.py`.** The eight post-render scripts in `common/utils/` become one driver in
the engine directory: `section_subtitle`, `enable_autofit`, `embed_fonts`, `style_footnotes`,
`link_captions`, `slide_layout`, `style_tables`, and `type_step` last. It opens the deck once,
runs the steps as functions in that order with the reasons as comments, and saves once. The
recipe becomes `quarto render ... --to engine-pptx` plus `python3 $(PPTX_POST) $@`. Moves and
renames only, no logic changes; parity must be byte-identical. `common/utils/livery.py` (the
shim) and `engine_module()` go away. `Make.common` still needs `livery.py deps|mono|figsize`:
give the engine's `livery.py` a `__main__`.

**B.13, one text measurer.** `slide_layout.py`'s two size heuristics are replaced by
`section_subtitle.py`'s PIL measurement on the livery's font. This changes output on purpose:
run `make qa` and `make measure` on quickstart, sample and fixtures under every livery, and
show Ben a contact sheet before merging.

## How to check (learned this session)

- **Parity.** Build the baseline the same day, in a git worktree that the check reuses: a
  deck's `date: last-modified` is its `.qmd`'s mtime, so a fresh checkout dates differently.
  - `git worktree add --detach <scratchpad>/parity main`, then `tests/parity.sh baseline`
    there (quickstart, sample, fixtures and plots under ncar, cu and nsi: about 8 minutes).
  - For each step: `git checkout --detach <branch>` in the worktree, then `tests/parity.sh check`.
  - An expected change can be folded with `NORMALIZE` (a sed program, applied to the check side;
    apply it to `_baseline/` by hand). Example for the compiled theme's file hash:
    `s#theme/quarto-[0-9a-f]{32}\.css#theme/quarto-HASH.css#`.
- **The sample deck prints `common/_quarto.yml` on a PDF page with no spare lines** ("Project
  config", page 29; beamer has no autofit). Any change to that file shows up there; render that
  page and check its last line. B.11's removal of `filters:` shortens it: an expected diff.
- **`make html` and `make pdf` do not rebuild on an engine Lua or scss change**, because
  `_extensions` is a link. Delete the outputs or `touch` the `.qmd`.
- **The image's smoke test runs on the runner host.** Tools such as `pdffonts` must run inside
  the image (`run -v "$work:/work" "$img" ...`). Locally, `make image` then
  `.github/scripts/smoke-test.sh <image>` (it handles macOS's `arm64` and BSD `stat` now).
- **A negated command never fails a `bash -e` step:** write the absence as an explicit `if`,
  using `grep -c ... >/dev/null`, not `grep -q`, under pipefail.
- **pptx on the Mac:** LibreOffice (`soffice --headless --convert-to pdf`) for contact sheets;
  it ignores embedded fonts. PowerPoint can be driven with `osascript`: Terminal has
  Accessibility and Screen Recording. Popovers open off screen, so read them through the
  accessibility tree (`entire contents of window "<name>"`).

## Open after Phase B

- **Release v1.1.0:** bump `version:` in `_extension.yml` and `VERSION` in
  `engine-revealjs.lua` (it names the HTML dependency), merge, then tag only on Ben's word.
  `release.yml` attaches the Overleaf zip and the charts bundle per livery.
- **#66:** the NASA screen colors (HDS roles, the Office cyan).
- **#58, the customer surface:** the `livery` command and schema. It has a note on `charts:`.
- **PowerPoint chart templates (`.crtx`)** per livery, only if people ask.
