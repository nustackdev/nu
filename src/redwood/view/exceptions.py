"""View layer exception hierarchy.

This module defines all view-specific exceptions.
"""

from __future__ import annotations

from redwood._rw_exception import RedwoodError


__all__ = [
    "RegistryError",
    "ViewError",
    "ViewOperationError",
]


class ViewError(RedwoodError):
    """Base exception for view-related errors."""


class RegistryError(ViewError):
    """Raised when registry operations fail."""


class ViewOperationError(ViewError):
    """Raised when view operations fail."""
