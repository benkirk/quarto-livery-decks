# Customer-surface handoff

The canonical copy is issue [#58](https://github.com/benkirk/quarto-livery-decks/issues/58); this file is its complement in the tree. Update the issue when the plan changes, and this file with it.

Handoff for a fresh session, after #57 (the monorepo) has landed. Read this, then `CLAUDE.md`, then README "Adding a livery" and `docs/design/engine-and-liveries.md` §4-5. Written 2026-10-18 from the same retrospective as #57; Ben chose both halves.

## Why

A customer of this repo is someone who owns a livery. Today that surface is:

- **Onboarding is five long commands and an unschema'd YAML.** README "Adding a livery": `livery_inspect.py <deck>` → hand-write `livery.yml` → `livery_build.py <dir>` → `livery_template.py <dir>` → `livery_check.py <dir> --qa` → `make … LIVERY=`, each by full path, split between `docs/common/utils/` and the engine directory. The schema is `KNOWN` in `livery_build.py` (a set of top-level names); nested keys, types and ranges are checked by whichever consumer trips over them, or not at all. ncar's `livery.yml` is ~100 lines whose comments carry the semantics; that file is the reference document.
- **The versioning story is a solo developer's.** Tags are re-cut (`release.yml` `--clobber`, README step 6, CLAUDE.md), there is no changelog, and compatibility between a livery and the engine is prose. The first customer who pins a tag and gets a different one under the same name loses trust once.

## Decisions (made with Ben, 2026-10-18)

1. One entry point for everything a livery owner does: a `livery` command in the engine directory, the existing scripts becoming its subcommands.
2. A real schema for `livery.yml`, validated by `build`, that is also the reference document (generated from it, so it cannot drift).
3. From the first release after #57 (v4.0.0 or Ben's choice), tags are immutable, every release has a changelog entry, and a livery records which schema it was written for.

## Part 1: the `livery` command

`docs/common/_extensions/engine/livery.py` grows a CLI (the module's reader API stays; `argparse` subcommands, no new dependency):

| subcommand | today | notes |
|---|---|---|
| `livery new <dir> [--from <deck.pptx>] [--extends <name>]` | `livery_inspect.py` `seed_brand`/`seed_livery` + a hand-written file | scaffolds `livery.yml`, `_brand.yml`, `reference/notes.md`, `logos/`, `fonts/`, `art/`; with `--from`, writes `reference/report.md` and seeds the palette, fonts and canvas from the deck; with `--extends`, a flavor file holding only `name`/`extends` |
| `livery inspect <deck.pptx> [-o report.md]` | `utils/livery_inspect.py` | moves into the engine directory |
| `livery build <dir>... [--check]` | `livery_build.py` | now validates against the schema first |
| `livery template <dir>` | `livery_template.py` | |
| `livery check <dir> [--qa]` | engine `livery_check.py` + `utils/livery_check.py` wrapper | `--qa` runs `make -C docs/quickstart qa LIVERY=<name>` (or `LIVERY_DIR=`); it needs the framework, so it says so when run elsewhere |
| `livery zip <dir> -o <zip>` | `overleaf_zip.py` | |
| `livery deps <dir>`, `livery mono <dir>` | the shim's two commands (deleted in #57 B.12 if not already) | `Make.common` calls them here |
| `livery all <dir>` | — | build → template → check, the onboarding loop in one command |

The scripts keep working as files (their `main()`s are what the subcommands call) so nothing in CI or `Make.common` breaks mid-way; a root `make livery NAME=<name>` (or `LIVERY=`) runs `livery all`. README "Adding a livery" becomes: `livery new`, edit, `make livery NAME=x`, look.

## Part 2: the schema

- `docs/common/_extensions/engine/livery.schema.json`: JSON Schema (draft 2020-12) for `livery.yml`, every key with a `description` carrying what the comments in ncar's and cu's files say today, `enum`s for the closed sets (`title.style`, `feature.style`, `frametitle.align`, corners, `signoff.corner`), number ranges for the fractions (0..1), `additionalProperties: false` at every level (the current `KNOWN` warning becomes an error with a path: `geometry.logo.corne: unknown key`). `_brand.yml` is the brand.yml standard and is not ours to schema; validate only what the engine reads from it (`color.palette`, `typography.base/headings/monospace`, `logo.images`).
- A `schema: 1` key at the top of `livery.yml`, required; `build` refuses a version it does not know. Bump only on a breaking key change; an added optional key is not a bump.
- Validation uses `jsonschema` (conda-forge; add to `conda-env.yaml` and the Dockerfile's env), errors reported as `livery.yml: <path>: <message>`.
- `docs/livery-reference.md` is **generated** from the schema by `livery schema --doc` (one table per object, key / type / default / description); CI runs it with `--check` so the committed copy is current. The README's "Adding a livery" links it. Ben's rule applies: a knob's description names what it looks like on the slide, not the config value.
- Each `livery.yml` gets a first line `# yaml-language-server: $schema=../../_extensions/engine/livery.schema.json` so editors validate as you type.
- Every bundled livery validates unchanged except for the new `schema:` line (if one does not, the schema is wrong, not the livery; fix the schema or record the decision in `reference/notes.md`).

## Part 3: versions and releases

- **One version**: `_extension.yml` `version:`; `release.yml` already requires the tag to equal it (carried over in #57). `livery build` writes `engine: <version>` and `schema: <n>` into `build/livery.json`; `Make.common` warns when a livery's `build/livery.json` names another engine version than the extension's ("rebuild with `livery build`"), so a consumer's own livery does not silently wear a stale build. CI's `livery_build.py --check` stays the hard check for the bundled ones.
- **Immutable tags**: `release.yml` fails if the release exists (drop `--clobber` and the "moved tag" branch); README step 6 and CLAUDE.md say "a fix is a new patch release". The container image tags follow (ci.yaml → image.yaml already tags semver).
- **`CHANGELOG.md`** at the root, Keep-a-Changelog shape, newest first, with an entry per release and three subsections where relevant: *Decks* (what an author sees), *Liveries* (what a livery owner must do: a new key, a changed default, a schema bump), *LaTeX* (theme options). Seed it with the merge release and a one-paragraph summary of 3.x. The design log §10 stays the engineering narrative; the changelog is the customer's.
- **`quarto-required`-style gate for consumers**: `Make.common` already has the framework by path; nothing else needed once the version is one.

## Steps, one PR each

1. Schema + `schema: 1` in every livery + validation in `build` + generated reference with `--check` in CI. Outputs unchanged (parity).
2. The `livery` CLI (subcommands over the existing `main()`s), `livery new`, `make livery`, README "Adding a livery" rewritten to it; `livery_inspect.py` moves into the engine directory.
3. Versions: `engine`/`schema` in `livery.json`, the `Make.common` warning, immutable tags in `release.yml`, `CHANGELOG.md`, the README/CLAUDE.md rules. Then the first immutable release.

## Acceptance

- `livery new /tmp/x --from <some deck>` followed by `make livery LIVERY_DIR=/tmp/x` produces a livery that `make -C docs/quickstart all LIVERY_DIR=/tmp/x` builds in every format (a bare scaffold with a palette and one logo is enough; it need not be pretty).
- A misspelt key or an out-of-range fraction in `livery.yml` fails `livery build` with the path to it; every bundled livery passes.
- `docs/livery-reference.md` matches the schema (`livery schema --doc --check` in CI) and documents every key the engine reads.
- `release.yml` refuses an existing tag; `CHANGELOG.md` has the release's entry before the tag is pushed.
- `parity.sh check` identical after steps 1 and 2.

## Do not

- Change what any livery renders: this sprint is surface, not look. Parity after every step.
- Schema `_brand.yml` beyond what the engine reads.
- Invent a second config file: the schema describes `livery.yml` as it is; renaming keys is a schema bump and not this sprint's work (note candidates in the issue instead).

## Pointers

- `livery_build.py`: `KNOWN` (L56), `resolve()`, `read()`, `merge()`/`rebase()` (how `extends` works; the schema must allow a flavor to carry only its overrides, so nothing is `required` below `name`/`extends`/`schema`).
- `utils/livery_inspect.py`: `seed_brand`, `seed_livery` (the start of `livery new`), `report()`.
- `livery_check.py` (engine) and `utils/livery_check.py` (`--qa`).
- `release.yml`, `ci.yaml` `livery` job matrix (a new livery joins by existing: keep that).
- README "Adding a livery" (L586-641) and "LaTeX and Overleaf" (the per-livery links a release serves).
- Memory for Claude: `sprint-tags-recut.md` is superseded by part 3; `minimal-prs-versions.md` loses its "one engine PR" half after #57.
