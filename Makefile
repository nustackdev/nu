.PHONY: help install sync dev test lint format clean web-install web-dev web-build build-nu build-nudle build-all

# =============================================================================
# Configuration
# =============================================================================
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

CORE := src
EXT_DIRS := ext/nu-virtuals ext/nu-dict ext/nu-datetime ext/nu-fin ext/nu-math ext/nu-path ext/nu-uuid ext/nu-shape-lens ext/nu-tree-view
ALL_SRC := $(CORE) $(addsuffix /src,$(EXT_DIRS))

UI_ROOT := src/nu/ui
NUDLE_APP := src/nu/ui/nudle/ts

# =============================================================================
# Help
# =============================================================================
help:
	@echo "$(BLUE)nu monorepo$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make install         Install uv if needed"
	@echo "  make sync            Sync workspace (install all packages)"
	@echo "  make dev             Full dev setup (sync + pre-commit)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make test            Run all tests"
	@echo "  make test-pkg PKG=x  Run tests for specific package (e.g., PKG=ext/eb-virtuals)"
	@echo "  make test-core       Run core tests"
	@echo "  make test-ext        Run extension tests"
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
	@echo "  make build-nu        Build the nu wheel"
	@echo "  make build-nudle     Build the nudle web-bundle wheel"
	@echo "  make build-all       Build both wheels"
	@echo ""
	@echo "$(GREEN)nudle web:$(NC)"
	@echo "  make web-install     npm install across the ui workspace (core, kit, nudle)"
	@echo "  make web-dev         Run vite dev server (HMR, ws proxy to :8080)"
	@echo "  make web-build       Build the vite bundle into $(NUDLE_APP)/dist"
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
	$(error PKG not set. Usage: make test-pkg PKG=ext/eb-virtuals)
endif
	@echo "$(BLUE)Testing $(PKG)...$(NC)"
	uv run pytest $(PKG)/tests -v

test-core:
	@echo "$(BLUE)Running core tests...$(NC)"
	uv run pytest tests/ -q

test-ext:
	@echo "$(BLUE)Running extension tests...$(NC)"
	@for dir in $(EXT_DIRS); do \
		if [ -d "$$dir/tests" ]; then \
			echo "$(YELLOW)  $$dir$(NC)"; \
			uv run pytest $$dir/tests -q || exit 1; \
		fi; \
	done

test-cov:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	uv run pytest --cov --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Report: reports/coverage/index.html$(NC)"

test-fast:
	@echo "$(BLUE)Running fast tests...$(NC)"
	uv run pytest -m "not slow" -x

# =============================================================================
# Code Quality
# =============================================================================
lint:
	@echo "$(BLUE)Linting...$(NC)"
	uv run ruff check .

format:
	@echo "$(BLUE)Formatting...$(NC)"
	uv run ruff format .
	uv run ruff check --fix .
	@echo "$(GREEN)Done$(NC)"

format-check:
	@echo "$(BLUE)Checking format...$(NC)"
	uv run ruff format --check .

check: format-check lint
	@echo "$(GREEN)All checks passed$(NC)"

# =============================================================================
# Packages
# =============================================================================
list:
	@echo "$(BLUE)Workspace packages:$(NC)"
	@echo ""
	@echo "$(GREEN)Core (src/nu/):$(NC)"
	@ls -d src/nu/*/ 2>/dev/null | sed 's|/$$||' | sed 's|^|  |' || echo "  (none)"
	@echo ""
	@echo "$(GREEN)Extensions (ext/):$(NC)"
	@ls -d ext/*/ 2>/dev/null | sed 's|/$$||' | sed 's|^|  |' || echo "  (none)"

build:
ifndef PKG
	$(error PKG not set. Usage: make build PKG=everybase)
endif
	@echo "$(BLUE)Building $(PKG)...$(NC)"
	cd $(PKG) && uv build
	@echo "$(GREEN)Built: $(PKG)/dist/$(NC)"

# =============================================================================
# nudle web + nu wheel
# =============================================================================
web-install:
	@echo "$(BLUE)Installing ui workspace deps (core, kit, nudle)...$(NC)"
	cd $(UI_ROOT) && npm install
	@echo "$(GREEN)Installed$(NC)"

web-dev:
	@echo "$(BLUE)Starting vite dev server...$(NC)"
	cd $(NUDLE_APP) && npm run dev

web-build:
	@echo "$(BLUE)Building nudle web bundle...$(NC)"
	cd $(NUDLE_APP) && npm run build
	@echo "$(GREEN)Built: $(NUDLE_APP)/dist/$(NC)"

build-nu:
	@echo "$(BLUE)Building nu wheel...$(NC)"
	uv build --wheel
	@echo "$(GREEN)Built: dist/$(NC)"

build-nudle: web-build
	@echo "$(BLUE)Building nudle web-bundle wheel...$(NC)"
	cd $(NUDLE_APP) && uv build --wheel
	@echo "$(GREEN)Built: $(NUDLE_APP)/dist/$(NC)"

build-all: build-nu build-nudle
	@echo "$(GREEN)Both wheels built$(NC)"

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
	rm -rf .coverage htmlcov/ reports/
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
