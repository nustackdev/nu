.PHONY: help install dev test lint format clean build publish

# Configuration
PYTHON := python

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

# ============================================================================
# Help
# ============================================================================

help:
	@echo "$(BLUE)everybase - Term Programming Platform$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make install-uv      - Install uv package manager"
	@echo "  make install         - Create venv + install dependencies"
	@echo "  make dev             - Full dev setup (install + test)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make test            - Run all tests"
	@echo "  make test-term       - Run everyterm tests"
	@echo "  make test-flow       - Run everyflow tests"
	@echo "  make test-link       - Run everylink tests"
	@echo "  make test-base       - Run everybase tests"
	@echo "  make test-cov        - Run tests with coverage report"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make format          - Format code with ruff"
	@echo "  make lint            - Check code with ruff"
	@echo "  make format-check    - Check formatting without changes"
	@echo ""
	@echo "$(GREEN)Publishing:$(NC)"
	@echo "  make dist            - Build distribution packages"
	@echo "  make publish-test    - Publish to TestPyPI"
	@echo "  make publish         - Publish to PyPI"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean           - Remove build artifacts"
	@echo "  make clean-all       - Remove everything including venv"

# ============================================================================
# Setup
# ============================================================================

check-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "$(YELLOW)uv is not installed$(NC)"; \
		echo "Run: make install-uv"; \
		exit 1; \
	}

install-uv:
	@if command -v uv >/dev/null 2>&1; then \
		echo "$(GREEN)uv is already installed$(NC)"; \
	else \
		echo "$(BLUE)Installing uv...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "$(GREEN)uv installed successfully$(NC)"; \
	fi

install: check-uv
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	uv venv
	@echo "$(BLUE)Installing dependencies...$(NC)"
	uv pip install -e ".[dev,test]"
	@echo "$(GREEN)Installation complete$(NC)"
	@echo ""
	@echo "Activate with: source .venv/bin/activate"

dev: install test
	@echo ""
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. source .venv/bin/activate"
	@echo "  2. pre-commit install"

# ============================================================================
# Testing
# ============================================================================

test:
	@echo "$(BLUE)Running all tests...$(NC)"
	pytest -v

test-term:
	@echo "$(BLUE)Running everyterm tests...$(NC)"
	pytest protocols/everyterm/tests -v

test-flow:
	@echo "$(BLUE)Running everyflow tests...$(NC)"
	pytest protocols/everyflow/tests -v

test-link:
	@echo "$(BLUE)Running everylink tests...$(NC)"
	pytest protocols/everylink/tests -v

test-base:
	@echo "$(BLUE)Running everybase tests...$(NC)"
	pytest src/everybase/tests -v

test-fast:
	@echo "$(BLUE)Running fast tests...$(NC)"
	pytest -m "not slow" -x -v

test-cov:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest --cov=everybase --cov=everyterm --cov=everyflow --cov=everylink \
		--cov-report=html:tests/reports/coverage --cov-report=term-missing --cov-branch
	@echo "$(GREEN)Coverage report: tests/reports/coverage/index.html$(NC)"

# ============================================================================
# Code Quality
# ============================================================================

lint:
	@echo "$(BLUE)Running linters...$(NC)"
	ruff check src protocols pkgs

format:
	@echo "$(BLUE)Formatting code...$(NC)"
	ruff format src protocols pkgs
	ruff check --fix src protocols pkgs
	@echo "$(GREEN)Code formatted$(NC)"

format-check:
	@echo "$(BLUE)Checking code format...$(NC)"
	ruff format --check src protocols pkgs
	ruff check src protocols pkgs

# ============================================================================
# Dependency Management
# ============================================================================

lock: check-uv
	@echo "$(BLUE)Locking dependencies...$(NC)"
	uv pip compile pyproject.toml -o requirements.lock
	@echo "$(GREEN)Dependencies locked$(NC)"

sync: check-uv
	@echo "$(BLUE)Installing from lock file...$(NC)"
	uv venv
	uv pip sync requirements.lock
	@echo "$(GREEN)Installed exact versions$(NC)"

update: check-uv
	@echo "$(BLUE)Updating dependencies...$(NC)"
	uv pip install --upgrade -e ".[dev,test]"
	@$(MAKE) lock
	@echo "$(GREEN)Dependencies updated$(NC)"

# ============================================================================
# Distribution & Publishing
# ============================================================================

dist: clean-dist
	@echo "$(BLUE)Building distribution packages...$(NC)"
	$(PYTHON) -m pip install --upgrade build twine
	$(PYTHON) -m build
	@echo "$(GREEN)Distribution built in dist/$(NC)"
	@ls -lh dist/

check-dist: dist
	@echo "$(BLUE)Checking distribution...$(NC)"
	twine check dist/*
	@echo "$(GREEN)Distribution is valid$(NC)"

publish-test: check-dist
	@echo "$(BLUE)Publishing to TestPyPI...$(NC)"
	twine upload --repository testpypi dist/*
	@echo "$(GREEN)Published to TestPyPI$(NC)"
	@echo "Test: pip install --index-url https://test.pypi.org/simple/ everybase"

publish: check-dist
	@echo "$(YELLOW)Publishing to PyPI (are you sure?)$(NC)"
	@echo "Package: everybase"
	@echo "Version: $(shell grep '^version = ' pyproject.toml | cut -d'"' -f2)"
	@read -p "Press Enter to continue or Ctrl+C to cancel..."
	twine upload dist/*
	@echo "$(GREEN)Published to PyPI!$(NC)"
	@echo "Install: pip install everybase"

# ============================================================================
# Cleanup
# ============================================================================

clean:
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete$(NC)"

clean-dist:
	@echo "$(BLUE)Cleaning distribution artifacts...$(NC)"
	rm -rf dist/ build/ *.egg-info/

clean-test:
	@echo "$(BLUE)Cleaning test artifacts...$(NC)"
	rm -rf .pytest_cache/ .coverage htmlcov/ tests/reports/

clean-all: clean clean-test
	@echo "$(BLUE)Removing virtual environment...$(NC)"
	rm -rf .venv/
	@echo "$(GREEN)Deep clean complete$(NC)"

# ============================================================================
# CI/CD
# ============================================================================

ci: format-check lint test-cov
	@echo "$(GREEN)CI checks passed!$(NC)"

# ============================================================================
# Info
# ============================================================================

info:
	@echo "$(BLUE)everybase Environment$(NC)"
	@echo "----------------------------------------"
	@echo "Python:  $(shell $(PYTHON) --version 2>&1)"
	@echo "uv:      $(shell uv --version 2>/dev/null || echo 'Not installed')"
	@echo "Venv:    $(shell [ -d .venv ] && echo 'Present' || echo 'Not created')"
	@echo ""
	@echo "$(BLUE)Structure:$(NC)"
	@echo "  protocols/everyterm  - Term algebra"
	@echo "  protocols/everyflow  - Flow algebra"
	@echo "  protocols/everylink  - Link algebra"
	@echo "  src/everybase        - Implementations"
	@echo "  pkgs/                - Fabrics"
