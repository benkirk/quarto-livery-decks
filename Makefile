.ONESHELL:
SHELL := /bin/bash
CONDA_ROOT := $(shell conda info --base)

# Common way to initialize environment across various types of systems
config_env := module load conda >/dev/null 2>&1 || true && . $(CONDA_ROOT)/etc/profile.d/conda.sh

.PHONY: help latex test image clean clobber distclean

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

test: ## Run the engine's tests: livery_build.py --check, livery_check.py, compositions, type, charts, schema
	set -e
	python3 _extensions/engine/livery_build.py --check liveries/*/
	python3 _extensions/engine/livery_check.py liveries/*/
	python3 tests/test_compositions.py
	python3 tests/test_type.py
	python3 tests/test_charts.py
	python3 tests/test_schema.py
	python3 _extensions/engine/livery.py schema --doc --check

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
