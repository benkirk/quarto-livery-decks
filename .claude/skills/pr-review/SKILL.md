---
name: pr-review
description: >-
  Reviewing one of this repository's pull requests comprehensively but not
  pedantically: read it as one design, trace the few places a gap hides here
  (the three formats, pptx validity, the runtime matrix, the first run, generated
  files, the consumer layout), report in plain terms first, let Ben pick what
  lands, land it as one commit per finding on the PR branch, post one findings
  comment, record the outcome. Load when Ben gives a PR number to review
  (`/pr-review 105`).
---

# Review a pull request

`/pr-review N`. The output is a verdict Ben can act on, plain terms first, and the fixes he
picks, landed on the PR branch. Comprehensive means every claim in the PR body was checked and
every consumer of a changed contract was read; not pedantic means a finding is a logic gap, a
missing proof or a piece that will be copied, never a style note. "Nothing to change" is a
complete answer.

## 1. The brief

No script yet (a recipe that keeps paying becomes one). Inline:

```bash
gh pr view N --json number,title,body,state,headRefName,baseRefName,commits,files
gh pr checks N
gh pr diff N --name-only
```

Then, before reading any code:

- **`cat` the memory files** behind the index lines naming the PR, its head branch or the PRs
  its body cites (`~/.claude/projects/-Users-benkirk-Documents-quarto-livery-decks/memory/MEMORY.md`):
  an earlier session may have shaped the PR (the design choice, the deferral, the incident).
  When no line matches, the PR is new to memory, so scan the index for its area.
- **Read the CLAUDE.md sections for the touched areas** with the Read tool. This repository has
  no `.claude/rules/`; CLAUDE.md is the rule book, and its bullets (Dark liveries,
  Compositions, Type, Checking a change) are the contracts a diff can break.
- **Load the skills.** `unplanned-city-sweep` is the lens for every PR: its "read as one
  design" seams (prose describing an earlier step, a silent path promoted to the default, the
  assumed branch being the untested one, a later step resting on a path one runtime exercises)
  and its lift / consolidate / bypassed-helper passes answer Ben's standing question, "will this
  be repeated?". `deck-polish` when a deck or a theme changes.

## 2. Read the diff by layer

```bash
git fetch origin
git diff origin/<base>...origin/<head> -- _extensions/engine/'*.py' _extensions/engine/pptx_steps/ _extensions/engine/mpl/   # the engine
git diff origin/<base>...origin/<head> -- _extensions/engine/'*.lua'                                                      # the filters
git diff origin/<base>...origin/<head> -- _extensions/engine/'*.sty' _extensions/engine/'*.scss' _extensions/engine/'*.css' _extensions/engine/'*.js'   # the themes
git diff origin/<base>...origin/<head> -- Make.common Makefile common/ Dockerfile etc/ bin/           # make and container
git diff origin/<base>...origin/<head> -- .github/                                                    # CI and release
git diff origin/<base>...origin/<head> -- liveries/'*/livery.yml' liveries/'*/build/'                  # the liveries, then their build
git diff origin/<base>...origin/<head> -- tests/ latex/                                               # then the proofs
git diff origin/<base>...origin/<head> -- docs/ '*.md' decks/                                         # then the record
```

Source first, so the tests are read as claims about code already understood. A diff over
~30 KB lands in the persisted-output file; `sed -n '/^diff --git a\/<path>/,$p'` on that file
is cheaper than a second diff. Shell notes that cost a turn each: zsh expands `=word`, so a
separator is `echo '-----'`; `$files` does not word-split (use `${=files}`); `--include=*.py`
is globbed, so quote it; read a test's exit code from `${pipestatus[1]}`, never from a
`| tail`.

**A merged PR** (a dry run, a post-mortem): its branch is gone and `main` took one squash
commit, so diff `<squash>^..<squash>` (`gh pr view N --json mergeCommit`), and the review
stops at step 5: nothing lands, no comment, no memory, and the report says so.

**If the head moves during the review** (the owner pushes while you read), `git fetch` and
diff `<reviewed head>..origin/<head>`: run step 3 on that delta only, and say in the report
and the comment which head the review covers.

## 3. Trace where a gap hides

Each item below is where a real incident hid. Trace each one that applies; say which ones
did not.

- **The three formats.** One source becomes pptx, HTML and PDF; a look fixed in one must hold
  in the other two, and a knob added to one format's drawer belongs in the other two or in
  `livery.json` for all three. Proof: `make qa` in a deck directory (`deck_qa.py`),
  `tests/parity.sh baseline|check` for anything that can move pixels, `make measure` when a
  composition box moves, `tests/parity-latex.sh` for the LaTeX side (CLAUDE.md, the
  "Checking a change" bullet of The engine).
- **pptx validity beyond LibreOffice.** LibreOffice opens files PowerPoint repairs. #94:
  `style_tables.py` wrote `w="5715.0"`, a float in an integer EMU attribute, and every deck with
  a table prompted "Repair?". For any change under `pptx_steps/` or `livery_template.py`,
  scan the slide XML for decimals in integer attributes (`unzip -p deck.pptx 'ppt/slides/*.xml' |
  grep -oE '\b(x|y|cx|cy|w|h|sz|marL|indent)="[0-9]+\.[0-9]+"'`); only PowerPoint judges
  (memory `pptx-repair-bisect`: cumulative post-step copies Ben opens; never script keystrokes).
- **The runtime matrix.** Native, docker, podman, apptainer (#95). macOS's `/usr/bin/make` is
  GNU make 3.81 and must parse `Make.common`'s header, `common/image.mk` and
  `common/Make.container`; a `$(shell ...)` with a `case` needs `(pattern)` or its `)` ends the
  function (#99); Linux's `/bin/sh` is dash (no `read -d`, no `[[`); BSD versus GNU tools
  (`sed -i ''`, `stat -f` / `-c`, `realpath`, `date -d`). Every recipe a deck's make can run on
  the host side is read against all four.
- **Apptainer's host environment and HOME.** Apptainer passes the host's environment and binds
  the real HOME: a Casper profile's `TMPDIR=$SCRATCH/tmp` named a directory the container lacked
  and stopped Quarto (#96: `--cleanenv` everywhere); a host IPython startup script killed the
  build's kernel until the container got its own HOME (#99: `DECKS_HOME`). A new host-side
  variable, path or dotfile must survive both: trace how it reaches the container
  (`APPTAINERENV_*`, `MAKEFLAGS`, a bind) and what `--cleanenv` strips.
- **The first run, an empty HOME, a cold cache.** A new user's first build hung on a Casper
  login node: Chromium indexed every font into an empty HOME (#98: the index now ships in the
  image), and the root was Quarto's 3 s `waitForServer`, after which it awaits a healthy
  browser's exit forever (#102: patched to 30 s in the image, asserted). A change to the image,
  the entrypoint or a cache (`/opt/matplotlib`, `/var/cache/fontconfig`, `~/.cache/quarto-livery-decks`)
  is tested from a fresh HOME, several times when timing is involved; Ben can run commands as
  `cmipap`, a second account, on crlogin2 (memory `casper-apptainer-testing`).
- **Generated files in sync.** `livery build --check liveries/*/` (every `build/livery.json`
  stamps the engine version), `livery schema --doc --check` (`liveries/REFERENCE.md`),
  `template.pptx` is generated by `livery template` and never edited by hand; the version lives
  in two places (`_extensions/engine/_extension.yml` and `VERSION` in `engine-revealjs.lua`).
  A PR that touches a livery's `livery.yml`, the schema or the version carries the regenerated
  files; CI's `--check` says so, but read it before CI does.
- **The consumer layout.** Nothing may assume a deck sits in `decks/<deck>/`: a submodule
  consumer (`docs/other-repos.md`), a deck beside a checkout (`bin/new-deck`, an absolute
  `include`), a bare directory in the image (`make -f .../Make.common DECKS=...`). A path in
  `Make.common` is relative to the framework, never to the deck; `ci.yaml`'s `consumer` job and
  `smoke-test.sh` are the proofs.
- **Release and CI assumptions.** #101: `release.yml`'s zip step dispatched to the release's
  own image, not yet published (`manifest unknown`); a Python-only target says
  `DECKS_RUNTIME=native`. A workflow change is traced on the runner it runs on (`container:`
  bypasses the entrypoint; a fork's PR has no `packages: write`) and at the moment it runs
  (what exists on ghcr then).
- **Roles only.** No palette name outside `build/livery.sty`; the Sass sets every color as
  `var(--engine-*)`; the pptx theme slots follow the roles (CLAUDE.md "The engine"). A raw
  hex or a palette name in a theme file is a finding.
- **The PR body's own claims.** "Byte-identical", "no pixels move", "parity clean", "works
  under Apptainer": each is one check, and the review says which held and which did not.
- **CHANGELOG.** Every user-visible change has an `[Unreleased]` entry in the PR that makes it
  (Decks, Liveries, Plots, LaTeX). A fix nobody sees needs none.

## 4. Verify the tests prove the claim

For each fix the PR describes, find the test and ask what assertion the bug would have
passed. A test that imports a new name cannot have failed on the old code, so it proves the
name exists, not the fix. A change that moves something regenerates its record in the same
commit: a moved composition box is a row in `tests/test_compositions.py`'s `EXPECTED_DELTAS`,
an edited quickstart re-shoots `decks/quickstart/screenshots/`, a plots change reruns
`make gallery` in `decks/plots`, a version bump rebuilds `liveries/*/build/`. Report CI from
`gh pr checks`; when it is still pending, say so.

## 5. Report

In this order, in the terminal:

1. **In plain terms.** Four to eight sentences on what the PR does and what was checked, with
   no file paths, variable names or make targets. Ben relays this to people who do not read
   the code, and it comes before any question.
2. **Verified sound.** Bullets, each with a `file:line`, one per trace in step 3 that held.
3. **Findings.** Ranked `F1..Fn`. Each carries a tag, *fix now* / *note, no change* / *ops*,
   the mechanism in two or three sentences, and the fix with its size (files, lines, whether
   parity, a baseline or a screenshot moves). Recommend on merit; the cost is a separate fact
   in the description.

Then one `AskUserQuestion`, multi-select, the recommended fixes first and "None, merge as is"
last. Never ask while an Explore agent is still running: every option must rest on finished
research.

An *ops* finding that one run would settle gets that run after the comment, offered, not
assumed: a fresh-HOME build on Casper is Ben's (`cmipap`, a qcmd job; memory
`casper-apptainer-testing`), and a "Repair?" verdict is PowerPoint's, which Ben opens
(`pptx-repair-bisect`). A deck or theme look is this session's: `make qa` and the contact
sheets, or parity before and after.

## 6. Land the picks

- **Get onto the PR head.** Already checked out here: `git pull --ff-only origin <head>`.
  Elsewhere: `git checkout <head>`. When `git worktree list` shows it checked out in another
  worktree (another session's), do not touch that tree: `git checkout -B review-<head>
  origin/<head>` here, and push later with `git push origin HEAD:<head>`. Say so in the
  comment, since that worktree is then behind.
- **One commit per finding**, named paths staged (`git add <paths>`), the house message: a
  one-line title, a body saying the mechanism and the fix, the session's attribution lines.
  A fix keeps the trap in a short comment where the code is, never a changelog in the source;
  a user-visible one gets its CHANGELOG line in the same commit.
- **Tests.** Run what the diff touches: `make test` for anything under `liveries/`, `tests/`,
  `_extensions/engine/livery*.py` or a tracked `.md` (the docs gate reads every link and
  section pointer); `make -C decks/<deck> qa` for a deck or a theme; `tests/parity.sh
  baseline` on the reviewed head and `check` after a fix that can move pixels, same checkout,
  same day; `tests/parity-latex.sh` for the LaTeX side. CI runs the full matrix (the image,
  every livery, the consumer layout); the review does not.
- **Push**, then read the SHAs for the comment.

## 7. Comment

```bash
gh pr comment N --body-file - <<'EOF'
## Review
<one-sentence verdict>; <what landed, with SHAs>; <what was noted>.

### Verified sound
- ...

### F1 — landed (`<sha>`)
### F2 — note, no change
### F3 — ops
...
🤖 Generated with [Claude Code](https://claude.com/claude-code)

<session link>
EOF
```

Always, after the picks land, even when nothing was picked: the comment is the record. Write
the F sections as the terminal report had them, plus the SHA, and name the head the review
covers.

## 8. Close out

Update the PR's project memory, or write one: reviewed on which date, what landed (SHAs), what
was noted and why it was left. One index line in `MEMORY.md` says the same in a few words.
When Ben merges while the session is open, add the squash SHA to both (`main` takes squash
merges only, so the PR's commits are not on `main`). The local branch is then gone; the
worktree stays, whatever `gh pr merge` suggests about removing it.

## Boundaries

- No compatibility shims: Ben is the only consumer, so a renamed name, path or key moves every
  caller in the same PR and keeps no alias (memory `no-compat-shims`). A review does not ask
  for one.
- Minimal PRs: a late finding lands on the PR's branch, not as a PR of its own; a version bump
  is a release's own small PR (memory `minimal-prs-versions`).
- Tags are immutable and asked for first; a broken release gets the next `N` and a superseded
  note, never a moved tag (memory `sprint-tags-recut`).
- Do not build for a failure nobody has seen: a finding names a trace with a concrete input,
  not a hypothetical.
- A fix lands on the PR branch, never on `main`; the PR owner merges.
- The review changes nothing in another session's worktree.
