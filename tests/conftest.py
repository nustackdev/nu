"""Shared test configuration and fixtures for all test types."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    # Package markers
    config.addinivalue_line("markers", "redwood: Tests for core redwood package")
    config.addinivalue_line("markers", "rwrocks: Tests for RocksDB bindings")
    config.addinivalue_line("markers", "rwstd: Tests for standard library utils")
    config.addinivalue_line("markers", "rwtup: Tests for tuple codec")
