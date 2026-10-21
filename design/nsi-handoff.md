# Handoff: the `nsi` livery (CU Center for National Security Initiatives)

**State:** done; `liveries/nsi` is the livery, and the refactor it prompted is
`refactor-handoff.md`.

Written 2026-10-16 at the end of the cleanup sprint, for a fresh session. Everything below is
on `main` of both repos unless marked otherwise. Read this, then `docs/design/engine-and-liveries.md`
section 10 (the log, newest first) and `docs/common/liveries/cu/reference/notes.md`.

## The two repos and how work flows

| | path | remote | role |
|---|---|---|---|
| framework | `/Users/benkirk/Documents/quarto-livery-decks` | `benkirk/quarto-livery-decks` | Make, pptx post-processors, QA, the `cu` livery, the vendored engine in `docs/common/_extensions/benkirk/engine/` |
| engine | `/Users/benkirk/Documents/beamer-livery-theme` | `benkirk/beamer-livery-theme` | the beamer and revealjs themes, `livery_build.py`, the reference liveries ncar/ucar/ucp/ncarucar |

- Env: `source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate /Users/benkirk/Documents/quarto-livery-decks/conda-env`
  (absolute path: the shell's cwd drifts). Build with `make -C docs/quickstart pptx html pdf LIVERY=<name>`;
  `make -C docs/quickstart qa LIVERY=<name>`; renders for review: LibreOffice
  (`/opt/homebrew/bin/soffice --headless --convert-to pdf x.pptx`, then `pdftoppm -r 48 -png`) for pptx
  (it lacks Helvetica Neue, so text falls back to a serif: judge geometry, not type), the Playwright
  shooter for HTML (write one: serve the deck dir, `Reveal.configure({transition:'none'})`, walk
  `Reveal.getSlides()`), `pdftoppm` for PDF. Contact sheets with Pillow; send them to Ben with
  SendUserFile before a PR.
- An engine change goes: engine branch → PR → merge → in the framework `cd docs/common && quarto update
  benkirk/beamer-livery-theme` (must show no diff if the branch was synced in earlier with `make
  vendor-engine ENGINE=../beamer-livery-theme`, which rsyncs an unmerged engine branch into the
  vendored copy for building against it).
- Conventions: one step per PR with CI green; stacked PRs get CI only once their base merges and
  they retarget `main` (push an empty commit then). Ben has authorized merging PRs (`gh pr merge
  --squash --delete-branch`, in stack order). Commit messages and PR bodies end with the attribution
  lines the session reminder gives. Comment budget: 10-line module docstrings, 1-line function
  docstrings, 3-line in-body comments; keep a comment that records a trap. Ben wants a layman's
  summary before any round of questions, and "the visual results are the real test".
- Parity: `docs/common/utils/parity.sh baseline|check` (both decks under `PARITY_LIVERIES`, default
  `ncar cu`; rebuild the ncar baseline from a detached worktree of main first:
  `git worktree add --detach ../fw-main main`, symlink `conda-env` in, run `baseline` there, move
  `_baseline/` over). ncar PDF and pptx must stay byte-identical except for a change you name; HTML
  differs whenever the theme's scss changes.

## What the livery contract offers now (all in `livery.yml` unless noted)

- `_brand.yml` (brand.yml standard): palette, `primary/secondary/foreground/background`, `typography`
  (`fonts` with files; `base`; `headings` may be a second family with files of its own: the beamer
  titles, reveal's heading font and the pptx major font follow), `logo.images` and `logo.medium.light/dark`.
- `roles`: primary-text, primary-contrast, accent, highlight, muted, surface, warning, dark.
- `signoff`: `{light, dark (logo.images names), aspect, height, bottom, corner: bottom-left|bottom-right}`,
  a second lockup at the foot of every slide but feature and full; dark variant on fields.
- `geometry.logo.corner`: `top-right` (default) | `top-left` (the title gives way beside it) | `none`
  (no mark anywhere, its room kept on fields). `geometry.pagenumber.corner`: `bottom-left` | `bottom-right`.
- `art`: `waves` (curves as data) or none (straight-edged title field); `title`, `section`, `content`
  files (`closing` too in HTML/PDF; pptx has no closing layout). Paths rebase under `extends`.
- `pptx`: `template`, `typeface`, `heading-typeface` (optional), `fonts` (blobs, optional; absent =
  no embedding), `scheme` overrides slot by slot.
- `overrides/livery-extra.sty` and `livery-extra.css`: appended to the generated files.
- `extends: cu`: a flavor inherits everything and overrides keys; it gets its own `template.pptx`
  (run `livery_template.py` on the flavor).
- Tools: `livery_inspect.py deck.pptx <dir>` (report + seeds), the engine's `livery_build.py <dir>`
  (build/), `utils/livery_template.py <dir>` (template.pptx; the engine's own `livery_template.py`
  since 3.3.0), `utils/livery_check.py <dir> [--qa]`.
  README "Adding a livery" is the walkthrough; CI builds and checks every directory under
  `docs/common/liveries/`.

## What `cu` is (the parent)

`docs/common/liveries/cu/`: CU palette (gold `#CFB87C` primary with black text, accessible gold
`#8D7334` for small text, sky blue highlight, dark gray muted, light gold surface), TeX Gyre Heros
(+ Heros Cn headings) bundled for HTML/PDF with the pptx naming Helvetica Neue unembedded, no waves,
the Research & Innovation Office lockup (`logos/cu-rio-lockup.png`, and a white recoloring) as the
sign-off bottom-left, `logo.corner: none`, page number bottom-right, a muted Flatirons photo as
`art.content` (a Reddit wallpaper, rights unverified: notes.md). Its `reference/notes.md` holds every
decision; `reference/report.md` the inspect tool's reading of the NSI deck.

## The NSI deck, what the flavor must reproduce

The reference is `~/Downloads/NSI MASTER SLIDE DECK JULY2026 EXTERNAL.pptx` (from Lindsay at NSI;
a Google Slides export, 16:9 at our canvas; not in git). Unzip its `ppt/media/` to read the files
named here (`unzip -o deck.pptx 'ppt/media/*' -d <scratch>`).

- **Marks** (the NSI lockup, aspect 1316/719 = 1.83): `image10.png` gold NSI + dark text (content
  slides, light fields), `image4.png` gold NSI + white text (dark fields: the title), `image7.png`
  black NSI + white text, `image8.png` a small copy of image10. The RIO lockup: `image6.png` dark
  (= cu's), `image2.emf` white (vector; cu's white PNG is a recoloring of image6).
- **Title slide** (deck slide 1): black field with a faint constellation/network picture
  (`image1.jpeg`, 4400x2475, dark); a gold band from about 27% to 72% of the height carrying the
  title (serif in LibreOffice only; Helvetica Neue bold in truth) and the date, the band's right
  38% filled by a campus photo (`image3.png`, the Flatirons); below the band the white RIO lockup
  bottom-left and the NSI lockup (image4) bottom-right. Slides 2 and 3 are variants (photo-only
  with a gold panel; photo-only).
- **Content slides**: white, NSI mark (image10) top-left about 0.08 of the height, title centered
  (ours stays left with the tab), RIO lockup bottom-left as sign-off, page number bottom-right, a
  faint satellite/ISS photo behind (`image71.jpg`, pre-faded, 2002x1014).
- **Closing** (slide 27): the constellation field with the two lockups.
- Fonts: Helvetica Neue (and "Helvetica Neue Extra Black Cond" for a few headlines), Arial second.

## The plan for `nsi`

Two PRs, engine first.

**Engine PR: a `title: band` style.** Today the title page is one composition in each theme:
beamer `beamerinnerthemeEngine.sty` (title page: logo, date, title, rule, subtitle, author on the
field) + `beamerouterthemeEngine.sty` (`\engine@drawtitlebg`: field, waves or the photo clipped
at 52%), revealjs `title-slide.html` + `engine-revealjs.scss` (`.engine-title`, the photo as
`.engine-title-photo-img` at 48%..100%, waves SVG from the Lua `photo_waves`), and the framework's
`livery_template.py` `title_slide()` + `slide_layout.py` `title_cover()` / `feature_cover()`
(photo at the back, the field and lines over it). Add a livery knob, e.g. `title: {style: band,
top: 0.27, bottom: 0.72, split: 0.62, band: primary, field: dark}` (default `style: cover`, today's
look), and draw: the field (`dark` role, `art.title` picture over it), the band in `primary` from
`top` to `bottom` with the title/date/subtitle inside it left of `split`, the `titlegraphic`
photo cropped to cover the band right of `split`, the sign-off and the mark along the bottom
strip (sign-off in its corner, the top mark in the other corner when the style is band). Keep
the three formats identical in geometry: fractions of the slide, as everything else. The
`.feature` slide can stay the cover style. Verify on cu with `title: {style: band}` temporarily
and on ncar unchanged (parity).

**Framework PR: the livery.** `docs/common/liveries/nsi/` with `extends: cu`: `_brand.yml` adds
`logo.images` nsi-light (image10) / nsi-dark (image4) and sets `logo.medium` to them;
`livery.yml`: `name: nsi`, `geometry.logo.corner: top-left` with `aspect: 1.83` and a height that
makes the mark about 0.08 of the slide, `signoff` the RIO lockup (inherited), `art.title:
art/constellation.jpg` (image1 cropped 16:9, maybe darkened), `art.content` the deck's satellite
photo (image71, cropped) or cu's Flatirons, `title: {style: band}`, `meta.name` "Center for
National Security Initiatives". Build, template, check, quickstart in three formats, sheets to
Ben, PR. Then `reference/notes.md` for nsi (provenance, the mapping, the choices) and a log entry.

## Pitfalls met this week

- pandoc matches content placeholders by `idx` too: chrome placeholders are idx 20-22 (builder).
- pandoc writes no slide-number box; `slide_layout.py` copies the layout's onto each slide.
- Slide shapes draw above layout shapes, so a cover redraws the field, lines, logo and sign-off
  on the slide itself (`slide_layout.cover`).
- `embed_fonts.py` is a no-op without `pptx.fonts`; the CI check reads the same key.
- The HTML autofit script and `deck_qa.py` must skip furniture boxes (`.engine-signoff` was
  counted as content once); if a new box appears on every slide, add it to both skip lists.
- `deck_qa.py`'s PDF overlap check now passes sub/superscripts; another font may need the same look.
- `gh` defaults to this repo now (`gh repo set-default`); the `upstream` remote is the old NCAR framework.
- `.playwright-mcp/` is ignored; keep browser-session files out of commits.
- The Google Slides CU template and the lockup library are CU-only; Ben's wife at NSI can supply
  files (the plain CU Boulder lockup is still wanted for `cu`).

## Open questions for Ben (ask with a layman's summary first)

1. Content-slide background for nsi: the deck's satellite photo, cu's Flatirons, or none.
2. The title's photo: per deck via `titlegraphic:` (the band shows the field color when absent),
   or a livery default photo (the campus shot) when a deck sets none.
3. Whether the closing slide should carry the constellation field like the deck's last slide.
4. Any NSI brand rule beyond the deck (there is no NSI guide; the CU rules apply).
