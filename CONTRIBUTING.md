# Contributing to EveryShape

Thanks for your interest in contributing! This guide will help you get set up and understand the development workflow.

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip
pip install uv
```

### Clone & Setup

```bash
git clone https://github.com/loomi-lab/everyshape.git
cd everyshape

# Install dependencies and build
make dev

# Activate virtual environment
source .venv/bin/activate

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

## Development Workflow

### Available Make Commands

```bash
make help              # Show all available commands

# Development cycle
make build            # Build Cython extensions
make rebuild          # Clean + build (use after code changes)
make test             # Run all tests
make test-fast        # Run fast tests only
make quick            # rebuild + test-fast (rapid iteration)

# Code quality
make format           # Auto-format code with ruff
make lint             # Check code with ruff
make pre-commit       # Run format + lint + test-fast

# Testing variants
make test-verbose     # Run with detailed output
make test-cov         # Run with coverage report
make test-stats       # Run with Hypothesis statistics

# Dependencies
make lock             # Lock dependencies to requirements.lock
make sync             # Install exact versions from lock file
make update           # Update all dependencies

# Cleanup
make clean            # Remove build artifacts
make clean-all        # Remove everything including venv
```

### Quick Development Loop

```bash
# 1. Make changes to .pyx or .py files
# 2. Rebuild and test
make quick

# Or for thorough testing
make rebuild
make test
```

## Code Style

- **Formatter:** Ruff (automatic via `make format`)
- **Linter:** Ruff (check via `make lint`)
- **Line length:** 100 characters
- **Import order:** isort via Ruff

Run before committing:

```bash
make pre-commit
```

## Cython Development

### Building

```bash
# Standard build
make build

# Debug build (with symbols)
make build-debug

# Clean rebuild (recommended after changes)
make rebuild
```

### Cython Tips

1. **After modifying `.pyx` files, always rebuild:**

   ```bash
   make rebuild
   ```

2. **Cython generates `.c` files** - these are gitignored and regenerated on build

3. **Use `nogil` where possible** for better performance:

   ```cython
   cdef inline void some_func() noexcept nogil:
       # Pure C operations here
   ```

4. **Import Python exceptions at the top:**

   ```cython
   from everyshape.codec.errors import DecodingError
   ```

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/loomi-lab/everyshape/issues)
- **Discussions:** [GitHub Discussions](https://github.com/loomi-lab/everyshape/discussions)

## Performance Tips

When developing high-performance code:

1. **Use Cython for hot paths** (encoding/decoding loops)
2. **Minimize Python object creation** in tight loops
3. **Use typed memoryviews** for buffer operations
4. **Profile before optimizing:**

   ```bash
   python -m cProfile -o profile.stats examples/basic_usage.py
   ```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
