"""Integration fixtures: the real Nu schema and full-pipeline helpers.

Integration tests exercise the Term -> compile -> validate -> evaluate
pipeline using the actual Nu layer-1 surface. Unit tests for individual
engine modules should not reach for these.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from nu2.lang import SCHEMA


if TYPE_CHECKING:
    from nu2.engine.structure import Schema


@pytest.fixture
def nu_schema() -> Schema:
    """The finalized Nu schema (``nu2.lang.SCHEMA``).

    Built once at import time and shared across the test session by way of
    a module-level constant; the fixture just hands it through so tests do
    not import it directly.
    """
    return SCHEMA
