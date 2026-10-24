# Roadmap: closing the static-content catalogue (two sprints, a sweep, a release)

**State (2026-10-24):** designed, not started; planned by the reviewing session after #146 and release 26.10.11, from three code explorations and two design passes. Ben's picks of 2026-10-24 are marked where they fall.

## Context

Ben (2026-10-24): the framework is feature-complete for static images and text after several real
decks; the remaining gaps are the ones a deck is most likely to hit next. He wants ONE PR sprint per
pair of items, each executed in a clean session with fresh context from a handoff file in `design/`,
reviewed by this session (`/pr-review N`), then an unplanned-city sweep and the next release. Added
during planning: a general four-corner marks model (future-proof, not a one-off second mark) and a
faint diagonal "DRAFT" watermark on every slide (a review copy he distributed lacked one).

The sequence:

| step | branch / PR | what | after it |
|---|---|---|---|
| Sprint A | `decks/cells-dark` → PR | pictures and tables in grid columns and cards (pptx); the inverted content slide `{.brand-dark}` in every format | `/pr-review`, squash merge |
| Sprint B | `decks/marks-watermark-mpl` → PR | marks in any of the four corners (nasa-ccp's second mark); a watermark on every slide; a pip-installable `livery_mpl` (#81) | `/pr-review`, squash merge |
| Sweep | `sweep/...` → PR | window mode from `f493a70` (#135, the ledger's newest window end) through A and B: #136–#147 plus the two sprints | merge |
| Release | `release/<ver>` → PR, tag | `26.10.N` if October, else `26.11.0`; the usual bump (version, ten stamps, docs pins, CHANGELOG), app-open sweep, tag | done |

Both sprints follow the house handoff shape (`design/gallery-handoff.md`): a State line, "For a
fresh session" (branch, reading list, house rules), Context anchors with `file:line`, ordered
commits (commit 0 is the handoff itself), Verification, Open questions for Ben. Line numbers are
on `2a1cf0a` (release 26.10.11, main's head); the executing session re-greps after each commit.

**The handoffs**: `design/cells-dark-handoff.md` (sprint A) and `design/marks-watermark-mpl-handoff.md` (sprint B); each is commit 0 of its sprint, by the session that executes it, and this roadmap rides with sprint A's commit 0. `design/unplanned-city-ledger.md` is untouched until the sweep.

### Cross-sprint rules (so B extends A, not redoes it)

- Sprint A lifts the content furniture's boxes into `livery.json` (`furniture`: tab, rule, title,
  and the marks). A names the mark boxes **by corner** from the start
  (`furniture.marks.top-right`, `furniture.marks.bottom-left`), so sprint B's four-corner model
  only adds corners and never renames.
- Sprint A emits marks per role as `\engine@mark@<role>@<name>` / `--engine-mark-<role>-<name>`
  (`<name>` one of `marks[role]`'s keys: `logo`, `signoff`, later `insignia`...), looping over the
  keys; `\enginelogo{light|dark}` stays the author's command over them (light = background, dark =
  primary). Sprint B keeps exactly that scheme (NOT a per-name light/dark pair): its per-corner
  drawers read `\engine@mark@background@<name>` on a content slide and `@dark@<name>` on a dark
  one; its css per-corner rules read `--engine-mark-<role>-<name>` urls.
- Sprint A's HTML dark mark is `section.engine-dark::after` (the content mark is still the
  `::after` pseudo-element then). Sprint B retires `::after` for content slides (marks become
  real `.engine-mark-<corner>` elements) and moves A's rule to `section.engine-dark
  .engine-mark-<corner>` in its commit 1. Both named in each handoff.
- Sprint A's `slide_layout.draw_dark()` draws the dark marks from `furniture.marks.<corner>` with
  `livery_mod.mark(LIVERY, "dark", name)`; after B that call is unchanged (`mark()` stays keyed by
  name).
- Sprint B's watermark is the marking strips' sibling and reuses `test_marking.py`'s harness,
  `slide_layout_shim()`, `livery placeholders` (SAMPLE text if a livery sets a default).
- Neither sprint bumps the version; CHANGELOG `[Unreleased]` lines per user-visible change; the
  release PR after the sweep renames the section.
- The reviewer (this session) runs `/pr-review` on each PR; the ops items it cannot settle
  (Keynote/PowerPoint open on new shape kinds) are run on the Mac at the review, as for #146.

## The release after the sweep

The sweep (window mode from `f493a70`, #135, the ledger's newest window end: #136–#147, A, B)
lands as one PR with a commit per pick and the ledger entry, then the release PR as #147 was:
`version:`, ten stamps, the two docs pins, the CHANGELOG section (`[26.10.N]` if it is still
October, else `[26.11.0]`), `make test`, `tests/app-open.sh` on every built deck (the sprints add
new shape kinds: a grouped picture, a native table, a slide background fill, a rotated alpha
text box), merge, tag, `release.yml` green, the image tags.
