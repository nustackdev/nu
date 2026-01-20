# Testing

## Structure

```
<package>/tests/
├── __init__.py       # (optional)
├── conftest.py       # Package fixtures
├── test_unit_*.py    # Unit tests
├── test_functional_*.py    # Functional tests
└── test_*.py         # Other tests

tests/                # Root-level
├── conftest.py       # Shared fixtures
└── integration/      # Cross-package tests
```

## Naming

```python
# Files
test_unit_foo.py      # Unit tests for foo
test_integration_*.py # Integration tests

# Classes
class TestFoo:        # Group related tests

# Functions
def test_foo_does_thing():
    """Foo should do thing."""
```

## Commands

```bash
make test                     # All tests
make test-abc                 # abc/ only
make test-pkg PKG=abc/every   # Specific package
make test-fast                # Skip @pytest.mark.slow
make test-cov                 # With coverage
```

## Markers

```python
import pytest

@pytest.mark.slow
def test_expensive():
    """Skip with make test-fast."""

@pytest.mark.integration
def test_cross_package():
    """Integration test."""
```

## Fixtures

Package fixtures in `<pkg>/tests/conftest.py`:

```python
import pytest

@pytest.fixture
def sample():
    return {"data": 123}
```

Shared fixtures in root `tests/conftest.py`:

```python
@pytest.fixture(scope="session")
def workspace_root():
    from pathlib import Path
    return Path(__file__).parent.parent
```

## Coverage

```bash
make test-cov
# Report: tests/reports/coverage/index.html
```

Config in root `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["abc", "std", "pkgs"]
omit = ["*/tests/*"]
```
