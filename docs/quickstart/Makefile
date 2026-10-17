OUT := $(notdir $(CURDIR))

include ../Make.common

# The README's images (screenshots/*.png, committed): rerun after editing the deck.
.PHONY: screenshots gallery
screenshots: $(OUT).html $(OUT).pdf
	python3 screenshots.py

# The README's livery gallery (screenshots/liveries.png): the deck under every livery.
gallery:
	python3 gallery.py
