# KOSMA developer commands. Run `make help` for the list.

PYTHON ?= python3.11
VENV   ?= .venv
PIP     = $(VENV)/bin/pip
PY      = $(VENV)/bin/python

.PHONY: help install dev fmt lint type test smoke audit ci docker run sample clean

help:           ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "} {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:        ## Create a venv and install runtime + dev deps editable.
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

dev:            ## Run the dev server with hot reload on http://127.0.0.1:8000.
	$(VENV)/bin/uvicorn kosma.main:app --reload --port 8000

fmt:            ## Auto-format with ruff.
	$(VENV)/bin/ruff format .
	$(VENV)/bin/ruff check . --fix

lint:           ## Lint + format check (no writes).
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

type:           ## Type-check with mypy.
	$(VENV)/bin/mypy kosma

test:           ## Run pytest with coverage.
	$(VENV)/bin/pytest --cov=kosma

smoke:          ## Engine + HTTP smoke checks (in-process).
	$(PY) scripts/smoke_test.py
	$(PY) scripts/smoke_http.py

audit:          ## Run pip-audit against pinned runtime deps.
	$(VENV)/bin/pip-audit -r requirements.txt --strict

ci: lint type test audit smoke   ## Run everything CI runs, locally.

docker:         ## Build the production Docker image.
	docker build -t kosma:dev .

run:            ## Run the production image on http://127.0.0.1:8000.
	docker run --rm -p 8000:8000 kosma:dev

sample:         ## Regenerate docs/sample-blueprint.pdf for the v1.0 reference chart.
	$(PY) scripts/generate_sample.py

clean:          ## Remove caches and the test PDF.
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov build dist *.egg-info
	find . -type d -name __pycache__ -not -path './$(VENV)/*' -exec rm -rf {} +
	rm -f scripts/out_test.pdf
