"""Engine-scoped fixtures.

These serve unit tests for ``src/nu2/engine/``. Tests that need the actual
Nu schema or the full compile-validate-evaluate pipeline belong under
``tests/nu2/integration/``, which has its own ``conftest.py``.
"""

from __future__ import annotations

import pytest

from nu2.engine.structure import Schema


@pytest.fixture
def schema() -> Schema:
    """A fresh, unfinalized :class:`Schema` per test."""
    return Schema()
