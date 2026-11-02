#!/usr/bin/env python3
"""Movies for decks (docs/authoring.md "Movies"), by ffmpeg, with the settings every format plays.

    frames2movie.py frames DIR OUT.mp4 [--poster OUT.png] [--fps N] [--crf N] [--width PX] [--background COLOR]
    frames2movie.py poster MOVIE OUT.png [--time SECONDS]
    frames2movie.py reencode MOVIE OUT.mp4 [--crf N] [--width PX]
    frames2movie.py check MOVIE ...

`frames` makes a movie from a directory of stills (a CFD run's frames, say), in name order with numbers
read as numbers (frame_9 before frame_10), all of one extension, and with --poster its poster too; a
`movie.yml` in the directory sets fps, crf, width, background and poster-time (seconds; a run's first
frame is often its blank start) for that movie (the command line wins). Make.common runs it for every
frames/<name>/ into movies/<name>.mp4 and movies/<name>.poster.png; `poster` makes a brought movie's. `reencode` turns a
movie that is not H.264 yuv420p into one that is; `check` says what would stop a movie playing
everywhere, and deck_qa.py runs it on every movie a deck shows.

H.264 from stills fails in two classic ways, and these defaults avoid both: libx264 refuses odd
dimensions (the frame is padded to even ones, never stretched), and a 4:4:4 or RGB pixel format plays
in VLC alone (yuv420p always). A transparent frame (matplotlib under the livery's style draws
transparent figures) is laid on --background: the livery's background role when LIVERY_DIR names a
built livery (Make.common exports it), else white. +faststart puts the index first, so a browser plays
before the whole file has arrived. No audio: a result movie is silent (reencode keeps a movie's own)."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FPS, CRF = 24, 18          # a smooth loop; visually lossless for flat-shaded plots and fields
EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
EVEN = "pad=ceil(iw/2)*2:ceil(ih/2)*2"   # reencode: a movie's odd edge padded, never stretched
H264 = ["-c:v", "libx264", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
KEYS = {"fps", "crf", "width", "background", "poster-time"}   # a frames directory's movie.yml
SIZE_WARN = 100 * 2**20   # a deck's movie past this: worth a smaller width or a higher crf


def tool(name: str) -> str:
    exe = shutil.which(name)
    if exe is None:
        sys.exit(f"frames2movie: {name} not found (the image has it; on a host: brew or apt install ffmpeg,"
                 ' docs/authoring.md "Movies")')
    return exe


def ffmpeg(*args: str) -> None:
    subprocess.run([tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def natural(path: Path):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", path.name)]


def frames_of(d: Path) -> list[Path]:
    files = sorted((p for p in d.iterdir() if p.suffix.lower() in EXTS and not p.name.startswith(".")), key=natural)
    if not files:
        sys.exit(f"frames2movie: no frames in {d} (one of {', '.join(sorted(EXTS))})")
    exts = {p.suffix.lower() for p in files}
    if len(exts) > 1:
        sys.exit(f"frames2movie: {d} mixes {', '.join(sorted(exts))}: one kind of frame per movie")
    return files


def livery_background() -> str:
    d = os.environ.get("LIVERY_DIR")
    try:
        return json.loads((Path(d) / "build" / "livery.json").read_text())["roles"]["background"] if d else "white"
    except (OSError, KeyError, ValueError):
        return "white"


def settings(d: Path, args) -> dict:
    """The movie's settings: the command line over the directory's movie.yml over the defaults."""
    own = {}
    yml = d / "movie.yml"
    if yml.exists():
        import yaml   # the env's (the livery tools read YAML too); only when a movie.yml is there
        own = yaml.safe_load(yml.read_text()) or {}
        unknown = set(own) - KEYS
        if unknown:
            sys.exit(f"frames2movie: {yml}: unknown key(s) {', '.join(sorted(unknown))} ({', '.join(sorted(KEYS))})")
    pick = lambda k, default: getattr(args, k) if getattr(args, k) is not None else own.get(k, default)   # noqa: E731
    return {"fps": pick("fps", FPS), "crf": pick("crf", CRF), "width": pick("width", None),
            "background": pick("background", None) or livery_background(), "poster-time": own.get("poster-time", 0)}


def out_size(first: Path, width) -> tuple[int, int]:
    """The movie's size: the first frame's, scaled to width (the aspect kept), both made even."""
    from PIL import Image   # the env's
    with Image.open(first) as im:
        w, h = im.size
    if width:
        w, h = int(width), h * int(width) / w
    return (int(w) + 1) // 2 * 2, (round(h) + 1) // 2 * 2


def make_from_frames(d: Path, out: Path, args) -> None:
    files = frames_of(d)
    s = settings(d, args)
    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_name(f".{out.stem}.part{out.suffix}")
    with tempfile.TemporaryDirectory(prefix="frames2movie.") as tmp:
        ext = files[0].suffix.lower()
        for k, f in enumerate(files):   # any names: ffmpeg's image2 reader wants a numbered sequence
            os.symlink(f.resolve(), Path(tmp) / f"{k:06d}{ext}")
        w, h = out_size(files[0], s["width"])
        bg = str(s["background"])
        bg = "0x" + bg.lstrip("#") if re.fullmatch(r"#?[0-9A-Fa-f]{6}", bg) else bg
        # the frame scaled into w x h (aspect kept, padded to it, never stretched) over the background,
        # whose rate is the movie's (the overlay keeps its first input's: color's own 25 repeats frames)
        graph = (f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos[v];"
                 f"color=c={bg}:s={w}x{h}:r={s['fps']}[c];[c][v]overlay=(W-w)/2:(H-h)/2:shortest=1:format=auto,format=yuv420p[out]")
        ffmpeg("-framerate", str(s["fps"]), "-i", str(Path(tmp) / f"%06d{ext}"), "-filter_complex", graph,
               "-map", "[out]", *H264, "-crf", str(s["crf"]), "-an", str(part))
    part.replace(out)
    print(f"frames2movie: {len(files)} frame(s) at {s['fps']} fps → {out}")
    if args.poster:
        make_poster(out, args.poster, str(s["poster-time"]))


def make_poster(movie: Path, out: Path, time: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_name(f".{out.stem}.part{out.suffix}")
    ffmpeg("-ss", str(time), "-i", str(movie), "-frames:v", "1", "-update", "1", str(part))
    part.replace(out)
    print(f"frames2movie: poster at {time} s → {out}")


def reencode(movie: Path, out: Path, args) -> None:
    size = [f"scale={int(args.width)}:-2:flags=lanczos"] if args.width else []
    part = out.with_name(f".{out.stem}.part{out.suffix}")
    ffmpeg("-i", str(movie), "-vf", ",".join(size + [EVEN, "format=yuv420p"]), *H264,
           "-crf", str(args.crf if args.crf is not None else CRF), "-c:a", "aac", "-b:a", "128k", str(part))
    part.replace(out)
    print(f"frames2movie: {movie} as H.264 yuv420p → {out}")


def problems(movie: Path) -> tuple[list[str], list[str]]:
    """(failures, hints) for a movie: what would stop it playing in PowerPoint, Keynote and every
    browser (not found, not H.264, not yuv420p, odd dimensions), and what is only worth a look (its
    size; no ffprobe to check it with)."""
    if not movie.exists():
        return ["not found"], []
    hints = []
    if movie.stat().st_size > SIZE_WARN:
        hints.append(f"{movie.stat().st_size / 2**20:.0f} MB (past {SIZE_WARN // 2**20}: a smaller --width or a higher --crf)")
    if shutil.which("ffprobe") is None:
        return [], hints + ['not checked: ffprobe not found (ffmpeg\'s; docs/authoring.md "Movies")']
    r = subprocess.run([shutil.which("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=codec_name,pix_fmt,width,height", "-of", "json", str(movie)],
                       capture_output=True, text=True)
    streams = json.loads(r.stdout or "{}").get("streams") or []
    if r.returncode or not streams:
        return ["not a movie ffprobe can read"], hints
    v, fails = streams[0], []
    if v.get("codec_name") != "h264":
        fails.append(f"codec {v.get('codec_name')}, not h264")
    if v.get("pix_fmt") != "yuv420p":
        fails.append(f"pixel format {v.get('pix_fmt')}, not yuv420p")
    if v.get("width", 0) % 2 or v.get("height", 0) % 2:
        fails.append(f"odd dimensions {v.get('width')}x{v.get('height')}")
    return fails, hints


FIX = "frames2movie.py reencode <movie> <out>.mp4 makes one that plays everywhere"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="frames2movie.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("frames", help="a movie from a directory of stills")
    f.add_argument("dir", type=Path)
    f.add_argument("out", type=Path)
    f.add_argument("--poster", type=Path, help="its poster too, at movie.yml's poster-time (default 0 s)")
    f.add_argument("--fps", type=float)
    f.add_argument("--background", help="behind a transparent frame (default: the livery's background, else white)")
    p = sub.add_parser("poster", help="a movie's poster, one frame as a PNG")
    p.add_argument("movie", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--time", default="0", help="seconds into the movie (default 0)")
    r = sub.add_parser("reencode", help="a movie as H.264 yuv420p mp4")
    r.add_argument("movie", type=Path)
    r.add_argument("out", type=Path)
    for q in (f, r):
        q.add_argument("--crf", type=int, help=f"quality, lower is better (default {CRF})")
        q.add_argument("--width", type=int, help="scale to this width in pixels, the aspect kept")
    c = sub.add_parser("check", help="what would stop a movie playing everywhere")
    c.add_argument("movies", nargs="+", type=Path)
    args = ap.parse_args(argv)
    if args.cmd == "frames":
        make_from_frames(args.dir, args.out, args)
    elif args.cmd == "poster":
        make_poster(args.movie, args.out, args.time)
    elif args.cmd == "reencode":
        reencode(args.movie, args.out, args)
    else:
        bad = 0
        for m in args.movies:
            fails, hints = problems(m)
            bad += bool(fails)
            print(f"{m}: {'; '.join(fails + hints) or 'ok'}{' (' + FIX + ')' if fails else ''}")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
