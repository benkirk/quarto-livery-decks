# Movies in decks

First-class movies (mp4 and kin), explored 2026-11-01 with Ben. The usual source is a
time-varying result, CFD and the like, saved as a series of stills. The rule is the engine's
(`design/engine-and-liveries.md`): one reader, one drawer per format. Here that means a movie is
read once from the deck and each format shows it as well as it can. The PDF is the one deliberate
departure: it shows a still and a link. Section 4 has the steps; sections 1 to 3 the facts and
decisions they rest on. Issue: #170.

## 1. Facts (2026-11-01)

- **Nothing handles video today.** The image has no `ffmpeg`, no Lua filter reads a movie source,
  and no pptx step embeds one.
- **The video tools on Ubuntu.** noble's `ffmpeg` (6.1, universe) is Debian's build:
  `--enable-gpl` with x264, x265, libaom, dav1d, vpx and SVT-AV1. All it lacks is
  `--enable-nonfree` (fdk-aac), which silent result movies never need. openSUSE strips these
  encoders from its own repositories, which is why Ben's Tumbleweed image
  (`benkirk/containers`, `containers/tumbleweed/gui_tools/Dockerfile`) needed Packman. Ubuntu
  needs nothing extra. Moving the base would cost the Dockerfile's apt TeX Live and its asserts,
  and also Playwright's `--with-deps`, which supports only Debian and Ubuntu. The old image's
  players (vlc, smplayer, haruna) are no use in a headless build image.
- **Size.** apt `ffmpeg` with `--no-install-recommends` adds 230 MB on disk (measured: 8.39 GB for
  26.11.0, 8.62 GB with it, arm64), a little over the 100 to 200 MB estimated. noble's build in the
  image is 6.1.1 and lists libx264, libx265, libsvtav1, libaom-av1 and libvpx-vp9.
- **pandoc's pptx writer knows no video**, only pictures: it embeds an `.mp4` image as a picture
  (`image3.mpg4`) that nothing can show. It writes an image's src as the picture's `descr`. python-pptx has
  `shapes.add_movie(file, left, top, width, height, poster_frame_image, mime_type)`. It embeds
  the blob, writes the `p14:media` extension and the picture that stands for the movie, and adds
  click-to-play timing. Autoplay and loop are not in its API (an open feature request): they mean
  editing `p:timing` and `p:cMediaNode` by hand. PowerPoint (Windows and Mac) and Keynote play
  H.264 yuv420p mp4 reliably. Google Slides' pptx import: not checked.
- **Quarto and pandoc already write `<video data-src controls>`** for an `.mp4` image in revealjs.
- **reveal.js plays `<video>`** with `data-autoplay` (it starts on entering the slide and pauses
  on leaving), along with `loop`, `muted`, `playsinline` and `poster`. HTML decks do not set
  `embed-resources` by default (`common/_quarto.yml`), so a movie is a file beside the deck. Under
  `embed-resources` it would be inlined as base64: a 50 MB movie makes a ~67 MB page.
- **PDF.** media9's video player was Flash, and Flash is gone. beamer's `multimedia` `\movie`
  hands the file to an outside player, and whether that works depends on the viewer. The
  `animate` package does play a frame sequence (Acrobat, Okular, Foxit, PDF-XChange, PDF.js and
  Firefox >= 130; XeLaTeX through dvipdfmx is supported). It does not play in Preview.app or
  Chrome's viewer, and it stores every frame in the file. **Ben's pick: no playback in the PDF,
  ever;** a still, a play badge and a link.
- **H.264 from stills has two classic failures**: odd frame dimensions (libx264 refuses them) and
  an RGB pixel format (yuv444p or rgb24 plays nowhere but VLC). The fixes are
  `-vf scale=trunc(iw/2)*2:trunc(ih/2)*2` (or `pad`) and `-pix_fmt yuv420p`; `-movflags +faststart`
  lets a browser start before the whole file has arrived.

## 2. Decisions (Ben, 2026-11-01)

- **The PDF shows the poster, a play badge and a link**, a deliberate departure documented as
  such. No `animate` path, now or later.
- **`ffmpeg` goes in the one image**, from apt. No second image and no Tumbleweed. On a host it
  is like gnuplot: brew or apt, not `conda-env.yaml` (conda-forge's needs its `gpl` variant for
  x264, and the env stays lean).
- **Both sources**: an author's own mp4 works as it is, and the framework builds one from a
  directory of stills for those who want it.
- **Autoplay, loop and muted by default**; a movie's attributes turn each one off.

## 3. Design

### 3.1 Authoring and the one reader

An image whose source is a movie (`.mp4`, `.m4v`, `.mov`, `.webm`):

```markdown
![Vortex shedding, Re = 200](movies/vortex.mp4){poster=movies/vortex.poster.png loop=false}
```

`autoplay`, `loop` and `muted` default to true; `poster=` defaults to `<name>.poster.png` beside
the movie. `href=` is the PDF's link (default: the movie file, relative). `engine-common.lua`
reads it once (`movie_attrs()`, beside the one-figure test), so every format sees the same
movie, poster and flags. A missing poster is made from the movie by `ffmpeg` (the first frame,
or `poster-time=`); without `ffmpeg` it is a warning and a placeholder still. `.webm` plays in
HTML only, so it is warned in pptx and PDF.

Checked with a real `quarto render`: Quarto leaves a movie Image alone before the engine's filters
(its `{{< video >}}` shortcode is a separate path); the HTML filter writes its own `<video>` in its
place, last, after `.full`'s one-figure test has seen an image.

### 3.2 Stills to a movie

`common/utils/frames2movie.py` wraps `ffmpeg` with the defaults section 1 names: even
dimensions, `yuv420p`, H.264 at `crf` 18, `+faststart`, `fps` 24, and a transparent frame laid on
the livery's background (matplotlib's under the livery's style are transparent: yuv420p has no
alpha, and they came out black). It also writes the poster. The background source runs at the
movie's rate: at ffmpeg's default 25 the overlay repeated frames (6 stills made 21).
`Make.common` gets a pattern rule from `frames/<name>/*.png` to `movies/<name>.mp4` and
`movies/<name>.poster.png`, and `movies/*` joins a deck's prerequisites (the fragments list), so
new frames rebuild the movie and the movie rebuilds the decks. Per-movie settings (`fps`, `crf`,
scale, `poster-time`: a run's first frame is often its blank start) live in an optional
`frames/<name>/movie.yml`. A livery switch remakes a frames movie (the `.livery` stamp is its
prerequisite: its background). A `poster-time=` poster is `<stem>.poster-<s>.png`, its own file
(the default one is another moment's), made by the filters when missing and remade by Make with its
movie. Later, perhaps: `livery_mpl` saving a matplotlib animation the same way.

Large binaries: frames and movies under a deck are the consumer's to manage (git LFS, or built
outputs left untracked). The framework commits none (section 4's fixture generates its frames).

### 3.3 The drawers

- **HTML** (`engine-revealjs.lua`): a `<video>` in the image's place, with reveal's
  `data-autoplay`, `loop`, `muted`, `playsinline` and `poster`, sized as a plot is
  (`engine-plots.lua`'s fit, `.engine-plot`). `?print-pdf` shows the poster. `make site` copies
  `movies/` (`site_index.py`). Under `embed-resources` a movie over a few MB is warned.
- **pptx**: the filter gives pandoc the poster as the picture, so pandoc lays it out in every
  layout as it does any image (a column, a `.full` slide, a folded caption), and writes a notes
  line `engine-movie: <movie> <flags>`. A new step, `pptx_steps/movie.py`, finds the picture by
  the poster's bytes, puts a movie shape in the same frame through `add_movie()` with that poster,
  deletes the picture, and edits `p:timing` for autoplay (start with the previous), loop
  (`repeatCount="indefinite"`) and mute. It runs after `svg_fallback`, before the steps that
  read a slide's shapes. Grid cells and galleries come later; a movie there is warned and stays
  a still.
- **PDF** (`engine-beamer.lua`, the inner theme): the poster sized as a figure, a play badge in
  the livery's roles (the accent ring, the on-dark glyph) and `\href` to `href=`. The LaTeX layer
  gets `\enginemovie[<graphics options>]{<poster>}{<link>}` (over `\enginemoviebox{<link>}{<picture>}`,
  and `\enginefullmovie{<link>}` for an `[enginefull=]` frame), so a hand author writes the same
  thing. An unsized poster is `0.72\textheight` at most (the `{height="72%"}` recipe, HTML's 600 px):
  at its natural size it pushed the caption off the frame. The badge has a ring in its ink: on
  nasa-dark the dark disc vanished on a black poster.

### 3.4 Checks

- `deck_qa.py` runs `ffprobe` on each movie a deck names: codec h264, `yuv420p`, even
  dimensions, a size warning past 100 MB. A movie that fails is warned with the
  `frames2movie.py --reencode` line that fixes it.
- `Dockerfile` step 1 adds `ffmpeg`; step 4's asserts check `ffmpeg -encoders` lists `libx264`.
  `smoke-test.sh` encodes a tiny movie.
- `decks/movies/` (a cookbook beside `decks/plots/`, not a fixture: the fixtures' `make measure`
  runs under every livery in CI, and a movie deck there is three renders more per job) draws its
  frames at build time (`make_frames.py`, 24 odd-sized transparent frames, no binaries committed), in
  CI's sample job and in `parity.sh`.
- `tests/test_movie.py`: the reader under `pandoc lua`, and the step's XML on a tiny generated
  mp4 (`p14:media`, the timing nodes, the loop count). Keynote and PowerPoint through
  `tests/app-open.sh` at the release: play, and no Repair? prompt.

## 4. Steps

One sprint PR, a commit per item, in this order (all done on `sprint/movies`; still to check by
hand: the movies play in PowerPoint's and Keynote's slideshows, `tests/app-open.sh` only opens
them, and Google Slides' import):

1. The image: `ffmpeg`, its assert, the smoke encode; the size in the merge summary noted here.
2. `frames2movie.py` and the `Make.common` rule and prerequisites.
3. The reader (`movie_attrs()`) and the HTML drawer; `make site`.
4. The pptx drawer (`movie.py`) and its test.
5. The PDF drawer and `\enginemovie`.
6. `deck_qa.py`'s checks, the fixture, CI and parity.
7. Docs: `docs/authoring.md` "Movies" (the PDF's departure said plainly), `latex/authoring.md`,
   `CHANGELOG.md`, CLAUDE.md.
