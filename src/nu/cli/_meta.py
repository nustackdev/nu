"""Shared helpers for CLI commands."""

from __future__ import annotations

import importlib.resources as resources
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def nu_version() -> str:
    try:
        return version("nustack-py")
    except PackageNotFoundError:
        return "0.0.0+dev"


def demos_root() -> Path:
    """Locate packaged demo scripts (ships as nu.cli.demos)."""
    return Path(str(resources.files("nu.cli").joinpath("demos")))


def demos() -> dict[str, Path]:
    root = demos_root()
    if not root.is_dir():
        return {}
    return {p.stem: p for p in sorted(root.glob("*.py")) if not p.stem.startswith("_")}
