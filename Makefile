.DEFAULT_GOAL := help
.PHONY: help install check lint format format-check typecheck test audit figures status generate freeze verify run evaluate report clean

PY ?= python

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package with dev extras
	$(PY) -m pip install -e ".[dev]"

# MUST stay identical to the steps in .github/workflows/ci.yml, in the same order.
# It previously omitted `format-check`, so `make check` passed while CI failed on every
# push for a week - a green local signal that could not detect the thing CI tests.
# A convenience target that is a subset of CI is worse than no target at all.
check: lint format-check typecheck test audit  ## Everything CI runs, in CI's order

lint:  ## Static lint
	ruff check .

format-check:  ## Formatting check - the one CI runs. Does not modify files
	ruff format --check .

format:  ## Auto-format (modifies files)
	ruff format .
	ruff check --fix .

typecheck:  ## Strict type check
	mypy

test:  ## Run the test suite
	pytest

audit:  ## Run only the publication-gating audit checks
	pytest -m audit

figures:  ## Regenerate publication figures from the live corpus
	$(PY) scripts/make_figures.py

status:  ## Show which pipeline steps are implemented
	$(PY) -m svgbench.cli status

# --- Experiment pipeline -----------------------------------------------------
# These become available as the frozen implementation order reaches them.
# See DESIGN_FREEZE.md. Until then they exit non-zero with an explanation.

generate:  ## [step 3-7] Generate corpus, ground truth and instructions
	$(PY) -m svgbench.cli generate

freeze:  ## [step 8] Freeze the corpus and write its manifest
	$(PY) -m svgbench.cli freeze

verify:  ## [step 8] Re-verify a frozen dataset against its manifest
	$(PY) -m svgbench.cli verify

run:  ## [step 10-13] Execute one experiment arm
	$(PY) -m svgbench.cli run

evaluate:  ## [step 9] Score stored responses (Tier 2 reproduction - no model needed)
	$(PY) -m svgbench.cli evaluate

report:  ## [step 14] Compute metrics and render the report (Tier 1 reproduction)
	$(PY) -m svgbench.cli report

clean:  ## Remove caches and the disposable working area
	rm -rf .pytest_cache .ruff_cache .mypy_cache data/generated/*
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
