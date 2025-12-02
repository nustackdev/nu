"""Shared test configuration and fixtures for all test types."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    # Package markers
    config.addinivalue_line("markers", "everyshape: Tests for core everyshape package")
    config.addinivalue_line("markers", "esrocks: Tests for RocksDB bindings")
    config.addinivalue_line("markers", "esstd: Tests for standard library utils")
    config.addinivalue_line("markers", "estup: Tests for tuple codec")
