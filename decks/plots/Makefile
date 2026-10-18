OUT := $(notdir $(CURDIR))

include ../../Make.common

# The README's images (screenshots/liveries.png, palettes.png; committed): the deck's plots under
# every livery and their chart colors. Rerun after a livery's charts change.
.PHONY: gallery
gallery:
	python3 gallery.py
