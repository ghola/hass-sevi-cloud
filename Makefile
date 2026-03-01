PYTHON := PYENV_VERSION=3.13.3 python3
VENV   := .venv
PIP    := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF   := $(VENV)/bin/ruff

.PHONY: help install test lint fmt check clean

help:
	@echo "Available targets:"
	@echo "  install  – create .venv and install test dependencies"
	@echo "  test     – run pytest with coverage"
	@echo "  lint     – run ruff check"
	@echo "  fmt      – run ruff format"
	@echo "  check    – lint + test"
	@echo "  clean    – remove .venv and cache artefacts"

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements_test.txt

install: $(VENV)/bin/activate

test: install
	$(PYTEST) --cov --cov-report=term-missing

lint: install
	$(RUFF) check .

fmt: install
	$(RUFF) format .

check: lint test

clean:
	rm -rf $(VENV) .pytest_cache .coverage htmlcov __pycache__ \
	       custom_components/sevi_cloud/__pycache__ \
	       tests/__pycache__
