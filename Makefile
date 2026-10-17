.ONESHELL:
SHELL := /bin/bash
CONDA_ROOT := $(shell conda info --base)

# Common way to initialize environment across various types of systems
config_env := module load conda >/dev/null 2>&1 || true && . $(CONDA_ROOT)/etc/profile.d/conda.sh

.PHONY: help vendor-engine image clean clobber distclean

# -------------------------------------------------------------------
# Default target: help
# -------------------------------------------------------------------
help: ## Show this help message
	@echo ""
	@echo -e "\033[1;36mquarto-docs-framework - Makefile Help\033[0m"
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

# The engine (the vendored theme) comes from benkirk/beamer-livery-theme through
# `cd docs/common && quarto update benkirk/beamer-livery-theme` once a change is on its main.
# To build against an engine branch first, sync a checkout of it in; after the merge the
# quarto update must then show no diff.
ENGINE ?= ../beamer-livery-theme
vendor-engine: ## Sync $(ENGINE)/_extensions/engine/ into the vendored copy (an unmerged engine branch)
	rsync -a --delete --exclude __pycache__ --exclude 'reference/media' --exclude 'reference/*.pptx' \
	  $(ENGINE)/_extensions/engine/ docs/common/_extensions/benkirk/engine/
	git status --short docs/common/_extensions

# The build-environment image (README "Building in the container"); CI publishes it
# multi-platform as ghcr.io/benkirk/quarto-livery-decks (.github/workflows/image.yaml).
IMAGE ?= ghcr.io/benkirk/quarto-livery-decks:dev
image: ## Build the container image locally as $(IMAGE), then .github/scripts/smoke-test.sh $(IMAGE)
	docker build -t $(IMAGE) --build-arg GIT_SHA=$$(git rev-parse --short HEAD) --build-arg BUILD_DATE=$$(date -u +%Y-%m-%dT%H:%MZ) .

clean: ## Remove temporary files (*~)
	rm *~

clobber: ## Git clean except .env and conda-env/
	git clean -xdf --exclude ".env" --exclude "conda-env/"

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
