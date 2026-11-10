#!/usr/bin/env python3
"""Embed each movie a deck shows, over the poster pandoc laid out in its place.

pandoc's pptx writer knows no video, so movie-pptx.lua hands it the movie's poster, a picture pandoc
places as any other (a column, a .full slide, a caption under it), and writes a notes line per movie,
`engine-movie: <poster> <movie> [autoplay] [loop] [muted]` (the paths percent-encoded). This step finds
the picture by its path (pandoc writes an image's src as the picture's descr), puts the movie in the same
frame through python-pptx's add_movie() with that poster (the media part, a:videoFile and the p14:media
extension, the picture PowerPoint shows until it plays) at the picture's place in the stacking order,
deletes the picture and the line, and writes the slide's p:timing: an autoplay movie starts with the
slide (the main sequence's first step, after the previous, PowerPoint's "Automatically"), a loop one
repeats until stopped, a muted one plays silent; without autoplay a click on it plays it (add_movie's
own form). After the steps that move pictures (slide_layout's .full fit, columns, grid), so the movie
takes the poster's final frame. A movie in a grid cell or a gallery is drawn from a marker, not by
pandoc, and stays its poster, warned. Runs once: the lines are gone after it."""

import struct
from pathlib import Path
from urllib.parse import unquote

from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn

KEY = "engine-movie:"
MIME = {".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime"}
VOLUME = 80000   # PowerPoint's default, 80%


def duration_ms(path: Path):
    """The movie's length in ms from its mvhd box (MP4 and QuickTime share the layout), else None."""
    def boxes(f, start, end):
        at = start
        while at + 8 <= end:
            f.seek(at)
            size, kind = struct.unpack(">I4s", f.read(8))
            head = 8
            if size == 1:
                size, head = struct.unpack(">Q", f.read(8))[0], 16
            elif size == 0:
                size = end - at
            if size < head:
                return
            yield kind, at + head, at + size
            at += size

    with open(path, "rb") as f:
        end = f.seek(0, 2)
        for kind, s, e in boxes(f, 0, end):
            if kind != b"moov":
                continue
            for kind2, s2, _ in boxes(f, s, e):
                if kind2 == b"mvhd":
                    f.seek(s2)
                    head = f.read(32)
                    if head[0] == 1:
                        scale, dur = struct.unpack(">IQ", head[20:32])
                    else:
                        scale, dur = struct.unpack(">II", head[12:20])
                    return round(dur * 1000 / scale) if scale else None
    return None


def timing_xml(movies) -> str:
    """The slide's p:timing for its movies [(shape id, ms, autoplay, loop, muted)]: the autoplay ones in
    the main sequence's first step, started with the slide (each after or with the one before), and a
    p:video media node per movie with its loop and mute."""
    ids = iter(range(1, 1000))
    nxt = lambda: next(ids)   # noqa: E731
    root, seq_id = nxt(), None
    auto = [m for m in movies if m[2]]
    seq = ""
    if auto:
        seq_id, step, group = nxt(), nxt(), nxt()
        effects = []
        for k, (spid, ms, *_rest) in enumerate(auto):
            node = "afterEffect" if k == 0 else "withEffect"
            effects.append(
                f'<p:par><p:cTn id="{nxt()}" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold"'
                f' nodeType="{node}"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                f'<p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr><p:cTn id="{nxt()}" dur="{ms or 1}" fill="hold"/>'
                f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:cmd>'
                f'</p:childTnLst></p:cTn></p:par>')
        seq = (
            f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{seq_id}" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
            f'<p:par><p:cTn id="{step}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
            f'<p:cond evt="onBegin" delay="0"><p:tn val="{seq_id}"/></p:cond></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{group}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            + "".join(effects) +
            '</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn>'
            '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
            '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
            '</p:seq>')
    mute, repeat = ' mute="1"', ' repeatCount="indefinite"'
    media = "".join(
        f'<p:video><p:cMediaNode vol="{VOLUME}"{mute if muted else ""}>'
        f'<p:cTn id="{nxt()}"{repeat if loop else ""} fill="hold" display="0">'
        f'<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst></p:cTn>'
        f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cMediaNode></p:video>'
        for spid, _ms, _auto, loop, muted in movies)
    return (f'<p:timing {nsdecls("p")}><p:tnLst><p:par><p:cTn id="{root}" dur="indefinite" restart="never"'
            f' nodeType="tmRoot"><p:childTnLst>{seq}{media}</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')


def descr(shape) -> str:
    """A picture's descr: pandoc writes its image's src there."""
    found = shape._element.xpath("./p:nvPicPr/p:cNvPr/@descr")
    return found[0] if found else ""


def run(prs, path) -> None:
    from .common import is_picture, take_marker_lines   # here: the rest of the step reads no livery (its tests)
    base = Path(path).parent
    done = 0
    for n, slide in enumerate(prs.slides, start=1):
        lines = take_marker_lines(slide, KEY)
        if not lines:
            continue
        movies = []
        for words in lines:
            if len(words) < 2:
                continue
            poster, src = unquote(words[0]), unquote(words[1])
            flags = set(words[2:])
            pic = next((s for s in slide.shapes if is_picture(s) and descr(s) == poster), None)
            movie = base / src
            mime = MIME.get(movie.suffix.lower())
            if pic is None:
                print(f"movie: WARNING slide {n}: {src} stays its poster (a movie in a grid cell or a gallery "
                      "is drawn from a marker; give it a slide or a plain column of its own)")
                continue
            if mime is None or not movie.exists():
                print(f"movie: WARNING slide {n}: {src} {'not found' if mime else 'is not an MP4 or QuickTime movie'};"
                      " its poster stands in")
                continue
            mv = slide.shapes.add_movie(str(movie), pic.left, pic.top, pic.width, pic.height,
                                        poster_frame_image=str(base / poster), mime_type=mime)
            mv.name = f"Movie {len(movies) + 1}"
            pic._element.addprevious(mv._element)   # the poster's place in the stacking order
            pic._element.getparent().remove(pic._element)
            movies.append((mv.shape_id, duration_ms(movie), "autoplay" in flags, "loop" in flags, "muted" in flags))
        if not movies:
            continue
        sld = slide._element
        old = sld.find(qn("p:timing"))
        if old is not None:
            sld.remove(old)
        sld._insert_timing(parse_xml(timing_xml(movies)))
        done += len(movies)
    print(f"movie: embedded {done} movie(s) → {Path(path).name}")
