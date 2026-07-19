.PHONY: lint lintfix lint-ruff lint-mypy venv

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
VENV_STAMP := $(VENV)/.installed

venv: $(VENV_STAMP)

lintfix: $(VENV_STAMP)
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

lint: $(VENV_STAMP) lint-ruff lint-mypy

$(VENV_STAMP): requirements-dev.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	touch $(VENV_STAMP)

lint-ruff:
	$(PYTHON) -m ruff check .

lint-mypy:
	$(PYTHON) -m mypy
