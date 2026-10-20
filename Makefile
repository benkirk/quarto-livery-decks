.ONESHELL:
SHELL := /bin/bash
CONDA_ROOT := $(shell conda info --base)

# Common way to initialize environment across various types of systems
config_env := module load conda >/dev/null 2>&1 || true && . $(CONDA_ROOT)/etc/profile.d/conda.sh

.PHONY: help latex test livery image sif clean clobber distclean

# -------------------------------------------------------------------
# Default target: help
# -------------------------------------------------------------------
help: ## Show this help message
	@echo ""
	@echo -e "\033[1;36mquarto-livery-decks - Makefile Help\033[0m"
	@echo -e "\033[1;36m=====================================\033[0m"
	@echo ""
	@echo -e "\033[1mAvailable targets:\033[0m"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[32m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo -e "\033[1mPattern rules:\033[0m"
	@echo -e "  \033[32mmake <name>\033[0m              Create conda environment from <name>.yaml"
	@echo -e "  \033[32mmake solve-<name>\033[0m        Dry-run solve for <name>.yaml (no install)"
	@echo ""
	@echo -e "\033[1mExample:\033[0m"
	@echo -e "  \033[33mmake conda-env\033[0m           Create conda environment from conda-env.yaml"
	@echo ""

# The engine's pure-LaTeX side (latex/: the starter deck, the examples and their
# variants) and the engine's tests (tests/: the compositions and the type scale).
latex: ## Build latex/: the starter deck, examples and variants (XeLaTeX; quarto for the demo)
	$(MAKE) -C latex default examples variants

test: ## Run the engine's tests: livery build --check, livery check, compositions, type, svg fallback, notes color map, charts, schema, cli, new-deck, docs
	set -e
	python3 _extensions/engine/livery.py build --check liveries/*/
	python3 _extensions/engine/livery.py check liveries/*/
	python3 -m pytest -q tests/test_compositions.py
	python3 -m pytest -q tests/test_type.py
	python3 tests/test_svg_fallback.py
	python3 tests/test_notes_clrmap.py
	python3 -m pytest -q tests/test_charts.py
	python3 -m pytest -q tests/test_schema.py
	python3 -m pytest -q tests/test_cli.py
	python3 tests/test_new_deck.py
	python3 tests/test_docs.py
	python3 _extensions/engine/livery.py schema --doc --check

# A livery's onboarding loop (`livery all`, liveries/README.md): build/ from its yml files, its
# template.pptx, then its checks. LIVERY names one under liveries/, LIVERY_DIR any directory.
livery: ## Build, template and check a livery: make livery LIVERY=<name> (or LIVERY_DIR=<dir>)
	test -n "$(or $(LIVERY_DIR),$(LIVERY))" || { echo "usage: make livery LIVERY=<name> | LIVERY_DIR=<dir>"; exit 2; }
	python3 _extensions/engine/livery.py all $(or $(LIVERY_DIR),liveries/$(LIVERY))

# The build-environment image (docs/container.md); CI publishes it
# multi-platform as ghcr.io/benkirk/quarto-livery-decks (.github/workflows/image.yaml).
IMAGE ?= ghcr.io/benkirk/quarto-livery-decks:dev
image: ## Build the container image locally as $(IMAGE), then .github/scripts/smoke-test.sh $(IMAGE)
	docker build -t $(IMAGE) --build-arg GIT_SHA=$$(git rev-parse --short HEAD) --build-arg BUILD_DATE=$$(date -u +%Y-%m-%dT%H:%MZ) .

# The installation's SIF (docs/container.md "Sharing an installation"): the image of the release
# this checkout carries, which an Apptainer build of any deck including this Make.common runs
# instead of converting docker:// for each user. Pulled under a temporary name and moved, so a
# build never reads half a file; readable by everyone. Big pulls: APPTAINER_CACHEDIR and
# APPTAINER_TMPDIR on scratch, in a batch job on an HPC system.
FRAMEWORK_ROOT := ./
-include site.mk
include common/image.mk
sif: ## Pull the release's image into sif/ for shared Apptainer builds (module load apptainer first)
	@set -e   # .ONESHELL: the @ quiets the whole recipe
	command -v apptainer >/dev/null || { echo "make sif: no apptainer on PATH (module load apptainer)" >&2; exit 1; }
	if [ -s "$(DECKS_SIF)" ]; then echo "$(DECKS_SIF): already here"; exit 0; fi
	mkdir -p sif && chmod a+rx sif
	apptainer pull --force "$(DECKS_SIF).part" docker://$(DECKS_CONTAINER_IMAGE)
	chmod a+r "$(DECKS_SIF).part"
	mv "$(DECKS_SIF).part" "$(DECKS_SIF)"
	ls -l "$(DECKS_SIF)"

clean: ## Remove temporary files (*~)
	rm *~

clobber: ## Git clean except .env, conda-env/, sif/ and site.mk
	git clean -xdf --exclude ".env" --exclude "conda-env/" --exclude "sif/" --exclude "site.mk"

distclean: ## Clean everything including conda-env/
	$(MAKE) clobber
	rm -rf conda-env/

%.py : %.ipynb Makefile ## Convert Jupyter notebook to Python script
	jupyter nbconvert --clear-output $<
	jupyter nbconvert --to=python $< >/dev/null
	chmod +x $@
	git add $@ $<

%: %.yaml ## Create conda environment from YAML file
	[ -d $@ ] && mv $@ $@.old && rm -rf $@.old & \
	$(config_env) && \
	conda env create --file $< --prefix $@ && \
	conda activate ./$@ && \
	python -m bash_kernel.install --sys-prefix && \
	{ python -m playwright install --only-shell chromium || true; } && \
	conda list && \
	pipdeptree --all 2>/dev/null || true

solve-%: %.yaml ## Dry-run solve for conda environment
	$(config_env) && conda env create --file $< --prefix $@ --dry-run
