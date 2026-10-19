# The published image: what a build in a container runs (common/Make.container) and what `make
# sif` pulls (the top Makefile), so the two always agree. FRAMEWORK_ROOT is the checkout, with its
# trailing slash (Make.common's, or ./). GNU make 3.81-safe: macOS's make reads this.

# The release this checkout carries (a release bumps _extension.yml's version), or any published
# tag (26.10, latest, pr-95); `sha` is this checkout's own build (image.yaml's sha-<7>).
# DECKS_CONTAINER_IMAGE replaces the whole reference (a digest too: the CI's runtimes.yaml).
DECKS_IMAGE     ?= ghcr.io/benkirk/quarto-livery-decks
DECKS_IMAGE_TAG ?= $(shell sed -n "s/^version:[ \"']*\([^ \"']*\).*/\1/p" $(FRAMEWORK_ROOT)_extensions/engine/_extension.yml)
ifeq ($(DECKS_IMAGE_TAG),sha)
override DECKS_IMAGE_TAG := sha-$(shell git -C $(FRAMEWORK_ROOT) rev-parse --short=7 HEAD)
endif
DECKS_CONTAINER_IMAGE ?= $(DECKS_IMAGE):$(DECKS_IMAGE_TAG)

# The installation's SIF of that image (`make sif`, docs/container.md "Sharing an installation"),
# named for its tag: after a pull to a new release, builds go back to docker:// until `make sif`
# runs again, never onto another release's toolchain.
DECKS_SIF := $(abspath $(FRAMEWORK_ROOT))/sif/quarto-livery-decks_$(DECKS_IMAGE_TAG).sif
