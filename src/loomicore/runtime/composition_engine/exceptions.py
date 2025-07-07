from __future__ import annotations

from loomicore.exceptions import ResourceError

__all__ = [
    "CompositionError",
]


class CompositionError(ResourceError):
    """Base exception for composition-related errors."""

    pass
