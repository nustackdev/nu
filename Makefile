.PHONY: help install sync dev test lint format clean

# =============================================================================
# Configuration
# =============================================================================
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

CORE_DIRS := everybase
PKG_DIRS := pkg-every-dict pkg-every-flow pkg-every-flow-ext pkg-every-notion pkg-every-pv pkg-every-shape pkg-every-stdtypes pkg-every-table
ALL_DIRS := $(CORE_DIRS) $(PKG_DIRS)

# =============================================================================
# Help
# =============================================================================
help:
	@echo "$(BLUE)everybase monorepo$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make install         Install uv if needed"
	@echo "  make sync            Sync workspace (install all packages)"
	@echo "  make dev             Full dev setup (sync + pre-commit)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make test            Run all tests"
	@echo "  make test-pkg PKG=x  Run tests for specific package (e.g., PKG=core-every)"
	@echo "  make test-core       Run core-* tests"
	@echo "  make test-packages   Run pkg-* tests"
	@echo "  make test-cov        Run tests with coverage"
	@echo "  make test-fast       Run tests (fail fast, no slow)"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make lint            Check code with ruff"
	@echo "  make format          Format code with ruff"
	@echo "  make check           Run format-check + lint"
	@echo ""
	@echo "$(GREEN)Packages:$(NC)"
	@echo "  make list            List workspace packages"
	@echo "  make build PKG=x     Build specific package"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean           Remove build artifacts"
	@echo "  make clean-all       Remove everything including .venv"

# =============================================================================
# Setup
# =============================================================================
install:
	@command -v uv >/dev/null 2>&1 || { \
		echo "$(BLUE)Installing uv...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@echo "$(GREEN)uv ready$(NC)"

sync: install
	@echo "$(BLUE)Syncing workspace...$(NC)"
	uv sync
	@echo "$(GREEN)Workspace synced$(NC)"

dev: sync
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	uv run pre-commit install
	@echo "$(GREEN)Dev environment ready$(NC)"

# =============================================================================
# Testing
# =============================================================================
test:
	@echo "$(BLUE)Running all tests...$(NC)"
	uv run pytest

test-pkg:
ifndef PKG
	$(error PKG not set. Usage: make test-pkg PKG=core-every)
endif
	@echo "$(BLUE)Testing $(PKG)...$(NC)"
	uv run pytest $(PKG)/tests -v

test-core:
	@echo "$(BLUE)Running core-* tests...$(NC)"
	uv run pytest $(CORE_DIRS) -v

test-packages:
	@echo "$(BLUE)Running pkg-* tests...$(NC)"
	uv run pytest $(PKG_DIRS) -v

test-cov:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	uv run pytest --cov --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Report: tests/reports/coverage/index.html$(NC)"

test-fast:
	@echo "$(BLUE)Running fast tests...$(NC)"
	uv run pytest -m "not slow" -x

# =============================================================================
# Code Quality
# =============================================================================
lint:
	@echo "$(BLUE)Linting...$(NC)"
	uv run ruff check $(ALL_DIRS)

format:
	@echo "$(BLUE)Formatting...$(NC)"
	uv run ruff format $(ALL_DIRS)
	uv run ruff check --fix $(ALL_DIRS)
	@echo "$(GREEN)Done$(NC)"

format-check:
	@echo "$(BLUE)Checking format...$(NC)"
	uv run ruff format --check $(ALL_DIRS)

check: format-check lint
	@echo "$(GREEN)All checks passed$(NC)"

# =============================================================================
# Packages
# =============================================================================
list:
	@echo "$(BLUE)Workspace packages:$(NC)"
	@echo ""
	@echo "$(GREEN)core-*:$(NC)"
	@ls -d core-*/ 2>/dev/null | sed 's|/$$||' | sed 's|^|  |' || echo "  (none)"
	@echo ""
	@echo "$(GREEN)pkg-*:$(NC)"
	@ls -d pkg-*/ 2>/dev/null | sed 's|/$$||' | sed 's|^|  |' || echo "  (none)"

build:
ifndef PKG
	$(error PKG not set. Usage: make build PKG=core-every)
endif
	@echo "$(BLUE)Building $(PKG)...$(NC)"
	cd $(PKG) && uv build
	@echo "$(GREEN)Built: $(PKG)/dist/$(NC)"

# =============================================================================
# Cleanup
# =============================================================================
clean:
	@echo "$(BLUE)Cleaning...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ tests/reports/
	@echo "$(GREEN)Clean$(NC)"

clean-all: clean
	@echo "$(BLUE)Removing .venv...$(NC)"
	rm -rf .venv/
	@echo "$(GREEN)Deep clean$(NC)"

# =============================================================================
# CI
# =============================================================================
ci: check test-cov
	@echo "$(GREEN)CI passed$(NC)"
