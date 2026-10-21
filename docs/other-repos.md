# Using the framework from another repo

A project can keep its decks in its own tree and take this framework as a git
submodule, pinned to a commit. Its decks then live wherever it likes, and
nothing of the project's goes into this repo.

```bash
git submodule add https://github.com/benkirk/quarto-livery-decks.git docs/presentations/framework
mkdir docs/presentations/roadmap && cd docs/presentations/roadmap
echo 'include ../framework/Make.common' > Makefile
# author roadmap.qmd, then
make -C ../framework conda-env    # once: the framework's own environment
make pptx                         # or: make pptx LIVERY=cu
```

- **Include `Make.common`, by a path relative to the deck directory.** It finds
  everything else from that path. A symlink to it would not work: the path
  would be the link's own directory.
- **Make links the rest into the deck directory on the first build:**
  `_quarto.yml`, `_extensions` (the engine, whose formats bring their filters) and
  `_livery` (the livery in use, which it reaches the pptx template through). The consumer
  gitignores those links, and its build outputs.
- **A livery of its own**: a directory anywhere, made as in [`liveries/README.md`](../liveries/README.md), chosen
  with `make pptx LIVERY_DIR=path/to/livery`; `make overleaf LIVERY_DIR=...` packs its
  Overleaf zip, which the consumer releases itself.
- **Everything else works as it does here:** `DECKS`, `_*.qmd` fragments,
  `make qa` (with the deck's own `qa-names.txt`), `make site`, and a deck's own
  `_quarto.yml` in place of the link. A deck's own make targets (an ingest step, its tests) go
  inside `ifeq ($(DECKS_RUNTIME_USED),native)`, or a container build runs them twice
  ([container.md "From your deck's Makefile"](container.md#from-your-decks-makefile)).
- **Activate the framework's environment to build**, as in [README "Quick start"](../README.md#quick-start):
  `conda activate <path>/framework/conda-env`. It lives in the submodule and is
  gitignored there. Or install Docker, Podman or Apptainer instead: without the env, `make`
  builds in the published image ([container.md "From your deck's Makefile"](container.md#from-your-decks-makefile)).
- **A framework fix goes here first.** Merge it here, then move the
  consumer's pin (`git -C docs/presentations/framework pull`, then commit the
  new pointer). The engine is part of this repo, so the same holds for it.
- **The deck-polish skill:** a consumer can link
  `.claude/skills/deck-polish` to `docs/presentations/framework/.claude/skills/deck-polish`.

CI checks this layout on every pull request (the `consumer` job of
`.github/workflows/ci.yaml`). It checks the framework out at
`consumer/docs/presentations/framework`, writes a hello-world deck beside it,
and builds all three formats from there. The image's smoke test ([container.md](container.md))
builds a bare directory with no Makefile at all.

## Publishing the HTML decks

`make site` gathers the HTML decks of a directory into `_site/` (gitignored), a static
site that works as is: `python3 -m http.server -d _site`. Every deck's `<deck>_files/libs/`
is a subset of one union, so the site keeps a single `libs/` and rewrites the references
(a 13-deck directory goes from ~140 MB to ~16 MB); `images/` ships beside the decks, and
`index.html` lists them by their front matter, first deck first, in the livery's colors
and font (its files copied to `fonts/`, so the page needs no font CDN).

`make publish` pushes `_site/` to a GitHub Pages branch. The branch is a build artifact,
not a record: each publish replaces it with **one** parentless commit, so nothing
accumulates however often you publish (Pages serves the branch tip and keeps no versions
of its own). The price is that every publish uploads the whole site, since a commit with
no parent gives git nothing to delta against. Enable Pages once, from the branch:

```bash
gh api -X POST repos/<owner>/<repo>/pages \
  -f build_type=legacy -f 'source[branch]=gh-pages' -f 'source[path]=/'
```

Settings go in the deck Makefile, before the include:

```make
DECKS          := samuel 1-overview 2-concepts
SITE_EXTRA     := companion                # directories of hand-written pages, listed on the index
SITE_NOINDEX   := 1                        # <meta name="robots" content="noindex"> on every page
PUBLISH_PREFIX := presentations/samuel     # path under the Pages root (default: the root)
PUBLISH_BRANCH := gh-pages                 # default
PUBLISH_REMOTE := origin                   # default
include ../framework/Make.common
```

Two things to know: branch-based Pages is soft-limited to 10 builds an hour, and each push
shows in the repo's Actions tab as GitHub's own `pages-build-deployment` run. A public repo
publishes to a public URL; `SITE_NOINDEX` keeps it out of search engines, nothing more.

## Building in GitHub Actions

The decks build in the cloud on every push, with nothing installed anywhere: the framework's
reusable workflow runs `make` in the published image and attaches the pptx, PDF and HTML
decks to the run, and can deploy the HTML site to GitHub Pages. Your workflow,
`.github/workflows/decks.yaml`, is a dozen lines:

```yaml
name: decks
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
  pages: write       # these two only with `pages:` below
  id-token: write
jobs:
  decks:
    uses: benkirk/quarto-livery-decks/.github/workflows/build-decks.yaml@v26.10.5
    with:
      decks: docs/presentations/roadmap docs/presentations/samuel   # deck directories
      pages: docs/presentations/samuel                              # optional: its `make site`
```

Inputs: `decks` (the deck directories, each with its Makefile), `goals` (the make goals,
default `pptx html pdf`), `livery` (a `LIVERY=` for every deck; default each Makefile's own),
`image` (default `ghcr.io/benkirk/quarto-livery-decks:latest`, the newest release), `pages`
(one deck directory whose `make site` is deployed) and `retention-days` (the outputs' life on
the run, 14). The outputs are the run's `decks` artifact: the Actions tab, or `gh run download`.
A submodule consumer pins the workflow (`@v26.10.5`; `@main` follows the framework's main) and
`image:` to the version its submodule carries, so the workflow, the image and the deck
Makefile's framework agree.

Pages: set the repository's Pages source to "GitHub Actions" (Settings > Pages) once; the
workflow deploys the site itself, with no `gh-pages` branch. `make publish` (above) stays the
form from your laptop. Actions is free on public repositories; a private one has 2000 minutes
a month on GitHub Free (a deck in three formats takes about three) and 500 MB of artifact
storage (one HTML deck's artifact is some 10 MB; lower `retention-days` if that adds up).

CI exercises the workflow on every pull request (`ci.yaml`'s `reusable` job): the quickstart
deck at the pull request's image.
