from __future__ import annotations

from loomicore.exceptions import ResourceError

__all__ = [
    "DependencyError",
]


class DependencyError(ResourceError):
    """Base exception for dependency-related errors."""

    pass
