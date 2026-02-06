.PHONY: install install-dev lint format type-check check clean help run run-verbose run-quiet

PYTHON := python
UV := uv

# Installation
install:
	$(UV) pip install -e .

install-dev:
	$(UV) pip install -e ".[dev]"
	pre-commit install

# Code quality
lint:
	ruff check src main.py

format:
	ruff format src main.py
	ruff check --fix src main.py

type-check:
	mypy src main.py

check: lint type-check

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Run pipeline
run:
	$(PYTHON) main.py

run-verbose:
	$(PYTHON) main.py --verbose

run-quiet:
	$(PYTHON) main.py --quiet

# Help
help:
	@echo "Available targets:"
	@echo "  install      Install project dependencies"
	@echo "  install-dev  Install dev dependencies and pre-commit hooks"
	@echo "  lint         Run ruff linter"
	@echo "  format       Format code with ruff"
	@echo "  type-check   Run mypy type checker"
	@echo "  check        Run all checks (lint + type-check)"
	@echo "  clean        Remove cache files"
	@echo "  run          Run the optimization pipeline"
	@echo "  run-verbose  Run with detailed output"
	@echo "  run-quiet    Run with minimal output"
