from __future__ import annotations

from loomicore.exceptions import ResourceError

__all__ = [
    "AttachError",
]


class AttachError(ResourceError):
    """Base exception for dependency-related errors."""

    pass
