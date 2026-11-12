"""Movies (docs/authoring.md "Movies"): the one reader, the pptx drawer and step, the PDF's layer, the tool.

    python3 -m pytest tests/test_movie.py

engine-common.lua's movie() reads an image whose source is a movie alike for every format: its flags
on by default and off by `false`, its poster's default name (a poster-time= one its own), href the
file. movie-pptx.lua, under plain pandoc with a quarto shim, hands pandoc the poster and writes one
notes line per movie; pptx_steps/movie.py then embeds the movie over it (the media part, a:videoFile,
p14:media, the poster) in the picture's frame and stacking place, the slide's timing starting an
autoplay movie with the slide, looping and muting it by its flags, a click-to-play one in add_movie's
own form, and the line gone. The movie's length comes from its mvhd box (versions 0 and 1). The PDF's
layer, \\enginemovie and an [enginefull] frame's \\enginefullmovie, compiles clean with its link
(skipped without TeX). frames2movie.py orders frames as numbers, makes an even-sized yuv420p H.264
movie from odd-sized transparent stills, and its check names what would stop a movie playing
(skipped without ffmpeg). The HTML drawer needs Quarto: CI renders decks/movies in every format."""

import os
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from conftest import ENGINE, ROOT, lua_common, make_deck, one_line, pandoc_exe, run_steps

sys.path.insert(0, str(ROOT / "common" / "utils"))
import frames2movie  # noqa: E402

READ = r"""
local doc = pandoc.read(io.read("a"), "markdown")
doc:walk({ Image = function(img)
  if not C.is_movie(img) then print("not a movie: " .. img.src); return end
  local m = C.movie(img)
  print(table.concat({ m.src, m.mime, m.poster, m.href, tostring(m.autoplay), tostring(m.loop), tostring(m.muted), m.time }, "|"))
end })
"""


def test_reader(tmp_path):
    out, warns = lua_common(tmp_path, READ, "\n\n".join([
        "![](movies/a.mp4)",
        "![](movies/b.MOV){autoplay=false loop=no muted=0 poster=p.png href=https://x.org/b.mp4}",
        "![](movies/c.m4v){poster-time=1.5}",
        "![](images/d.png)",
        "![](my%20movie.webm)",
    ]))
    lines = out.splitlines()
    assert lines[0] == "movies/a.mp4|video/mp4|movies/a.poster.png|movies/a.mp4|true|true|true|0"
    assert lines[1] == "movies/b.MOV|video/quicktime|p.png|https://x.org/b.mp4|false|false|false|0"
    assert lines[2] == "movies/c.m4v|video/mp4|movies/c.poster-1.5.png|movies/c.m4v|true|true|true|1.5", \
        "a poster-time= poster has a name of its own"
    assert lines[3] == "not a movie: images/d.png"
    assert lines[4].startswith("my movie.webm|video/webm|my movie.poster.png|"), "the paths decoded"
    assert not warns


def test_one_list_of_extensions(tmp_path):
    """What a movie is, by extension, is said in three places that cannot share a file (Lua, Make,
    Python): engine-common.lua's MOVIE_MIME is the list, Make.common's movie_exts equals it (a movie
    the filters play and make has no poster rule for would build without its poster), and
    pptx_steps/movie.py's MIME is it less WebM (movie-pptx.lua's warning). And make's rules come
    from its list: a brought movie of each kind gets its poster's recipe."""
    from pptx_steps import movie
    lua = re.search(r"^local MOVIE_MIME = \{(.*)\}", (ENGINE / "engine-common.lua").read_text(), re.M).group(1)
    exts = set(re.findall(r"(\w+) = \"", lua))
    make = re.search(r"^movie_exts\s*:=\s*(.*)$", (ROOT / "Make.common").read_text(), re.M).group(1).split()
    assert set(make) == exts and len(make) == len(exts), f"Make.common movie_exts {make} is not MOVIE_MIME's {sorted(exts)}"
    assert {k.lstrip(".") for k in movie.MIME} == exts - {"webm"}, f"movie.py MIME {sorted(movie.MIME)}"
    d = tmp_path / "talk"
    (d / "movies").mkdir(parents=True)
    (d / "bin").mkdir()
    (d / "Makefile").write_text(f"include {ROOT}/Make.common\n")
    (d / "talk.qmd").write_text("---\ntitle: T\n---\n")
    for e in exts:
        (d / "movies" / f"m_{e}.{e}").write_bytes(b"")
    (d / "bin" / "ffmpeg").write_text("#!/bin/sh\n")   # on PATH: make then names the posters as prerequisites
    (d / "bin" / "ffmpeg").chmod(0o755)
    r = make_deck(d, "pptx", "DECKS_RUNTIME=native", dry=True, PATH=f"{d / 'bin'}:{os.environ['PATH']}")
    out = one_line(r.stdout)
    for e in exts:
        assert f"frames2movie.py poster movies/m_{e}.{e} movies/m_{e}.poster.png" in out, f".{e}: {r.stdout[-600:]}{r.stderr[-400:]}"


def tiny_mp4(path: Path, ms: int, version: int = 0) -> Path:
    """An MP4 that is only its boxes (ftyp, moov/mvhd at timescale 1000): enough for python-pptx, which
    embeds the bytes, and duration_ms(), which reads the mvhd."""
    if version == 0:
        mvhd = struct.pack(">B3sIIII", 0, b"\0\0\0", 0, 0, 1000, ms) + bytes(80)
    else:
        mvhd = struct.pack(">B3sQQIQ", 1, b"\0\0\0", 0, 0, 1000, ms) + bytes(80)
    box = lambda kind, body: struct.pack(">I4s", 8 + len(body), kind) + body   # noqa: E731
    path.write_bytes(box(b"ftyp", b"isom\0\0\0\0isom") + box(b"moov", box(b"mvhd", mvhd)))
    return path


@pytest.mark.parametrize("version", [0, 1])
def test_duration(tmp_path, version):
    from pptx_steps import movie
    assert movie.duration_ms(tiny_mp4(tmp_path / "m.mp4", 2500, version)) == 2500


def movie_shim(tmp: Path) -> Path:
    shim = tmp / "movie-pptx-shim.lua"
    shim.write_text(
        'quarto = { doc = { is_format = function(f) return f == "pptx" end },\n'
        '           log = { warning = function(s) io.stderr:write("WARNING: " .. s .. "\\n") end } }\n'
        f'PANDOC_SCRIPT_FILE = "{ENGINE / "movie-pptx.lua"}"\n'
        'dofile(PANDOC_SCRIPT_FILE)\n')
    return shim


DECK = """
## Auto

![A wave](movies/wave.mp4)

## Click

![](movies/wave.mp4){autoplay=false loop=false}

## Missing

![](movies/gone.mp4)
"""


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("movie")
    from PIL import Image
    (tmp / "movies").mkdir()
    Image.new("RGB", (320, 160), "#0057C2").save(tmp / "movies" / "wave.poster.png")
    tiny_mp4(tmp / "movies" / "wave.mp4", 2000)
    out = tmp / "deck.pptx"
    r = subprocess.run([pandoc_exe(), "--lua-filter", str(movie_shim(tmp)), "-o", str(out)],
                       input=DECK, text=True, cwd=tmp, capture_output=True, check=True)
    with zipfile.ZipFile(out) as z:
        before = {n: z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith(".xml")}
    return tmp, out, before, r.stderr


def test_filter(deck):
    _, _, parts, stderr = deck
    s1, s2, s3 = (parts[f"ppt/slides/slide{k}.xml"] for k in (1, 2, 3))
    assert 'descr="movies/wave.poster.png"' in s1 and 'descr="movies/wave.poster.png"' in s2, "the poster is the picture"
    notes = " ".join(v for k, v in parts.items() if k.startswith("ppt/notesSlides/"))
    assert "engine-movie: movies/wave.poster.png movies/wave.mp4 autoplay loop muted" in notes
    assert "engine-movie: movies/wave.poster.png movies/wave.mp4 muted" in notes
    assert "▶ movies/gone.mp4" in s3 and "movies/gone.mp4 not found" in stderr, "no poster: its path, warned"


def test_step(deck, livery_dir=ROOT / "liveries" / "ncar"):
    tmp, out, _, _ = deck
    pptx = tmp / "stepped.pptx"
    shutil.copy(out, pptx)
    r = run_steps(pptx, ["movie"], livery_dir)
    assert "embedded 2 movie(s)" in r.stdout, r.stdout
    from pptx import Presentation
    prs = Presentation(pptx)
    with zipfile.ZipFile(pptx) as z:
        names = z.namelist()
        s1, s2 = (z.read(f"ppt/slides/slide{k}.xml").decode() for k in (1, 2))
        notes = " ".join(z.read(n).decode() for n in names if n.startswith("ppt/notesSlides/") and n.endswith(".xml"))
    assert [n for n in names if n.startswith("ppt/media/") and n.endswith(".mp4")], "the movie is a media part"
    for s in (s1, s2):
        assert "a:videoFile" in s and "p14:media" in s and 'name="Movie 1"' in s
        assert 'descr="movies/wave.poster.png"' not in s, "the poster picture is replaced"
    auto = s1[s1.index("<p:timing"):]
    assert 'nodeType="mainSeq"' in auto and 'evt="onBegin"' in auto and 'cmd="playFrom(0.0)"' in auto
    assert 'dur="2000"' in auto, "the play command lasts the movie (its mvhd)"
    assert 'repeatCount="indefinite"' in auto and 'mute="1"' in auto
    click = s2[s2.index("<p:timing"):]
    assert "mainSeq" not in click and "repeatCount" not in click and 'mute="1"' in click, "click to play, once"
    assert "engine-movie:" not in notes, "the lines are gone"
    pic = next(s for s in prs.slides[0].shapes if s.name == "Movie 1")
    assert pic.width > 0 and pic.height > 0


TEX = r"""
\documentclass[aspectratio=169]{beamer}
\usetheme[livery=liveries/ncar,fonts=bundled]{Engine}
\begin{document}
\begin{frame}{A movie}
\centering\enginemovie[width=0.6\linewidth]{poster.png}{https://example.org/wave.mp4}
\end{frame}
\begin{frame}[enginefull=poster.png]
\enginefullmovie{https://example.org/full.mp4}\enginefullcaption{The full movie.}
\end{frame}
\end{document}
"""


def test_latex(tmp_path):
    if not (shutil.which("xelatex") and shutil.which("latexmk")):
        pytest.skip("xelatex and latexmk: the LaTeX layer compiles only with TeX")
    from PIL import Image
    from test_latex import compile_tex
    Image.new("RGB", (640, 320), "#0057C2").save(tmp_path / "poster.png")
    r, log = compile_tex(tmp_path, "movie", TEX)
    assert r.returncode == 0, log[-2000:]
    assert "Overfull" not in log
    pdf = (tmp_path / "movie.pdf").read_bytes()
    import re
    import zlib
    blob = pdf + b"".join(zlib.decompress(m.group(1)) for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf, re.S)
                          if m.group(1)[:1] == b"x")
    for url in (b"https://example.org/wave.mp4", b"https://example.org/full.mp4"):
        assert url in blob, f"the poster links to {url}"


def test_frame_order(tmp_path):
    for n in ("frame_10.png", "frame_9.png", "frame_1.png", ".hidden.png", "notes.txt"):
        (tmp_path / n).write_bytes(b"")
    assert [p.name for p in frames2movie.frames_of(tmp_path)] == ["frame_1.png", "frame_9.png", "frame_10.png"]


def test_check_missing(tmp_path):
    fails, hints = frames2movie.problems(tmp_path / "nope.mp4")
    assert fails == ["not found"] and not hints


@pytest.fixture(scope="module")
def ffmpeg():
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        pytest.skip("ffmpeg: the image has it; on a host, brew or apt install ffmpeg")


def probe(movie: Path) -> str:
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=codec_name,pix_fmt,width,height,nb_frames", "-of", "csv=p=0", str(movie)],
                          capture_output=True, text=True, check=True).stdout.strip()


def test_frames_to_movie(tmp_path, ffmpeg):
    from PIL import Image
    d = tmp_path / "frames"
    d.mkdir()
    for k in range(6):   # 101 x 51: odd both ways, transparent but for a bar
        im = Image.new("RGBA", (101, 51), (0, 0, 0, 0))
        im.paste((200, 30, 30, 255), (k * 15, 10, k * 15 + 10, 40))
        im.save(d / f"f{k}.png")
    (d / "movie.yml").write_text("fps: 6\nposter-time: 0.5\n")
    movie = tmp_path / "movies" / "m.mp4"
    assert frames2movie.main(["frames", str(d), str(movie), "--poster", str(tmp_path / "movies" / "m.poster.png"),
                              "--background", "#00ff00"]) == 0
    assert probe(movie) == "h264,102,52,yuv420p,6", "even, yuv420p, every frame"
    assert frames2movie.problems(movie) == ([], [])
    poster = Image.open(tmp_path / "movies" / "m.poster.png").convert("RGB")
    r, g, b = poster.getpixel((100, 1))
    assert g > 200 and r < 60 and b < 60, "a transparent frame lies on the background"
    (d / "movie.yml").write_text("fps: 6\nspeed: 2\n")
    with pytest.raises(SystemExit, match="unknown key"):
        frames2movie.main(["frames", str(d), str(movie)])


def test_check_and_reencode(tmp_path, ffmpeg):
    bad = tmp_path / "bad.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=65x33:rate=5",
                    "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv444p", str(bad)], check=True)
    fails, _ = frames2movie.problems(bad)
    assert any("yuv444p" in f for f in fails) and any("odd dimensions" in f for f in fails), fails
    assert frames2movie.main(["check", str(bad)]) == 1
    good = tmp_path / "good.mp4"
    frames2movie.main(["reencode", str(bad), str(good)])
    assert frames2movie.problems(good) == ([], []) and probe(good).startswith("h264,66,34,yuv420p")
