.PHONY: help install dev test lint format clean build publish

# Configuration
PYTHON := python
SRC_DIR := src
TEST_DIR := tests

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

# ============================================================================
# Help
# ============================================================================

help:
	@echo "$(BLUE)EveryShape Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make install-uv      - Install uv package manager"
	@echo "  make install         - Create venv + install dependencies"
	@echo "  make dev             - Full dev setup (install + test)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make test            - Run all tests"
	@echo "  make test-cov        - Run tests with coverage report"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make format          - Format code with ruff"
	@echo "  make lint            - Check code with ruff"
	@echo "  make format-check    - Check formatting without changes"
	@echo "  make pre-commit      - Run pre-commit checks"
	@echo ""
	@echo "$(GREEN)Dependencies:$(NC)"
	@echo "  make lock            - Lock dependencies to requirements.lock"
	@echo "  make sync            - Install from lock file (exact versions)"
	@echo "  make update          - Update all dependencies"
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
		echo "$(YELLOW)⚠️  uv is not installed$(NC)"; \
		echo "Run: make install-uv"; \
		exit 1; \
	}

install-uv:
	@if command -v uv >/dev/null 2>&1; then \
		echo "$(GREEN)✓ uv is already installed$(NC)"; \
	else \
		echo "$(BLUE)Installing uv...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "$(GREEN)✓ uv installed successfully$(NC)"; \
	fi

install: check-uv
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	uv venv
	@echo "$(BLUE)Installing dependencies...$(NC)"
	uv pip install -e ".[dev,test]"
	@echo "$(GREEN)✓ Installation complete$(NC)"
	@echo ""
	@echo "Activate with: source .venv/bin/activate"

dev: install build test
	@echo ""
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. source .venv/bin/activate"
	@echo "  2. pre-commit install"
	@echo "  3. make lock"

# ============================================================================
# Testing
# ============================================================================
test:
	@echo "$(BLUE)Running all tests...$(NC)"
	pytest $(TEST_DIR) -n 4

test-fast:
	@echo "$(BLUE)Running fast tests (no slow tests)...$(NC)"
	pytest $(TEST_DIR) -m "not slow" -x -v

test-functional:
	@echo "$(BLUE)Running functional tests...$(NC)"
	pytest $(TEST_DIR) -m "functional" -v

test-verbose:
	@echo "$(BLUE)Running tests with maximum verbosity...$(NC)"
	pytest $(TEST_DIR) -vv --hypothesis-show-statistics

test-cov:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest $(TEST_DIR) --cov=everyshape --cov-report=html:tests/reports/coverage --cov-report=term-missing --cov-branch
	@echo "$(GREEN)✓ Coverage report: tests/reports/coverage/index.html$(NC)"

test-watch:
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	pytest-watch $(TEST_DIR)

# ============================================================================
# Code Quality
# ============================================================================

lint:
	@echo "$(BLUE)Running linters...$(NC)"
	ruff check $(SRC_DIR)/everyshape $(TEST_DIR)

format:
	@echo "$(BLUE)Formatting code...$(NC)"
	ruff format $(SRC_DIR)/everyshape $(TEST_DIR)
	ruff check --fix $(SRC_DIR)/everyshape $(TEST_DIR)
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check:
	@echo "$(BLUE)Checking code format...$(NC)"
	ruff format --check $(SRC_DIR)/everyshape $(TEST_DIR)
	ruff check $(SRC_DIR)/everyshape $(TEST_DIR)

pre-commit: format lint test-fast
	@echo ""
	@echo "$(GREEN)✓ Pre-commit checks passed!$(NC)"

# ============================================================================
# Dependency Management
# ============================================================================

lock: check-uv
	@echo "$(BLUE)Locking dependencies...$(NC)"
	uv pip compile pyproject.toml -o requirements.lock
	@echo "$(GREEN)✓ Dependencies locked to requirements.lock$(NC)"

sync: check-uv
	@echo "$(BLUE)Installing from lock file...$(NC)"
	uv venv
	uv pip sync requirements.lock
	@echo "$(GREEN)✓ Installed exact versions from lock$(NC)"

update: check-uv
	@echo "$(BLUE)Updating dependencies...$(NC)"
	uv pip install --upgrade -e ".[dev,test]"
	@$(MAKE) lock
	@echo "$(GREEN)✓ Dependencies updated and locked$(NC)"

add: check-uv
	@if [ -z "$(PKG)" ]; then \
		echo "$(YELLOW)Usage: make add PKG=package-name$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Adding $(PKG)...$(NC)"
	uv pip install $(PKG)
	@echo "$(YELLOW)⚠️  Don't forget to add '$(PKG)' to pyproject.toml!$(NC)"

# ============================================================================
# Distribution & Publishing
# ============================================================================

dist: clean-dist
	@echo "$(BLUE)Building distribution packages...$(NC)"
	$(PYTHON) -m pip install --upgrade build twine
	$(PYTHON) -m build
	@echo "$(GREEN)✓ Distribution built in dist/$(NC)"
	@echo ""
	@echo "Contents:"
	@ls -lh dist/

check-dist: dist
	@echo "$(BLUE)Checking distribution...$(NC)"
	twine check dist/*
	@echo "$(GREEN)✓ Distribution is valid$(NC)"

publish-test: check-dist
	@echo "$(BLUE)Publishing to TestPyPI...$(NC)"
	twine upload --repository testpypi dist/*
	@echo "$(GREEN)✓ Published to TestPyPI$(NC)"
	@echo ""
	@echo "Test installation:"
	@echo "  pip install --index-url https://test.pypi.org/simple/ everyshape"

publish: check-dist
	@echo "$(YELLOW)⚠️  Publishing to PyPI (are you sure?)$(NC)"
	@echo "Package: everyshape"
	@echo "Version: $(shell grep '^version = ' pyproject.toml | cut -d'"' -f2)"
	@echo ""
	@read -p "Press Enter to continue or Ctrl+C to cancel..."
	@echo "$(BLUE)Publishing to PyPI...$(NC)"
	twine upload dist/*
	@echo "$(GREEN)✓ Published to PyPI!$(NC)"
	@echo ""
	@echo "Install with: pip install everyshape"

# ============================================================================
# Cleanup
# ============================================================================

clean:
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.so" -delete
	find $(SRC_DIR) -name "*.c" -delete
	@echo "$(GREEN)✓ Clean complete$(NC)"

clean-dist:
	@echo "$(BLUE)Cleaning distribution artifacts...$(NC)"
	rm -rf dist/ build/ *.egg-info/
	@echo "$(GREEN)✓ Distribution cleaned$(NC)"

clean-test:
	@echo "$(BLUE)Cleaning test artifacts...$(NC)"
	rm -rf .pytest_cache/
	rm -rf .coverage htmlcov/
	rm -rf tests/reports/
	@echo "$(GREEN)✓ Test artifacts cleaned$(NC)"

clean-all: clean clean-test
	@echo "$(BLUE)Removing virtual environment...$(NC)"
	rm -rf .venv/
	@echo "$(GREEN)✓ Deep clean complete$(NC)"

# ============================================================================
# CI/CD Targets
# ============================================================================

ci: format-check lint test-cov
	@echo ""
	@echo "$(GREEN)✓ CI checks passed!$(NC)"

# ============================================================================
# Information
# ============================================================================

info:
	@echo "$(BLUE)Environment Information:$(NC)"
	@echo "────────────────────────────────────"
	@echo "Python:  $(shell $(PYTHON) --version 2>&1)"
	@echo "uv:      $(shell uv --version 2>/dev/null || echo 'Not installed')"
	@echo "Venv:    $(shell [ -d .venv ] && echo 'Present' || echo 'Not created')"
	@echo "Working: $(shell pwd)"
	@echo ""
	@if [ -d .venv ]; then \
		echo "$(BLUE)Installed packages (top 10):$(NC)"; \
		uv pip list 2>/dev/null | head -11 || true; \
	fi
