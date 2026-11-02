# The movies cookbook (docs/authoring.md "Movies"): every way a deck shows a movie, in every format.
# Its stills are drawn at build time by make_frames.py, so no binary is committed; Make.common's movie
# rules make movies/wave.mp4 from them (frames2movie.py) and its poster.
MOVIES := wave

include ../../Make.common

movies/wave.mp4: frames/wave/.drawn
frames/wave/.drawn: make_frames.py .livery   # the livery's plot style
	python3 make_frames.py frames/wave && touch $@
