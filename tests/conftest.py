"""Root conftest - shared fixtures for all tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def workspace_root() -> Path:
    """Return the workspace root path."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def abc_path(workspace_root: Path) -> Path:
    """Return the abc/ directory path."""
    return workspace_root / "abc"


@pytest.fixture(scope="session")
def std_path(workspace_root: Path) -> Path:
    """Return the std/ directory path."""
    return workspace_root / "std"


@pytest.fixture(scope="session")
def pkgs_path(workspace_root: Path) -> Path:
    """Return the pkgs/ directory path."""
    return workspace_root / "pkgs"
