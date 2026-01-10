"""View layer exception hierarchy.

This module defines all view-specific exceptions.
"""

from __future__ import annotations

from everyshape._exception import EveryShapeError


__all__ = [
    "RegistryError",
    "ViewError",
    "ViewOperationError",
]


class ViewError(EveryShapeError):
    """Base exception for view-related errors."""


class RegistryError(ViewError):
    """Raised when registry operations fail."""


class ViewOperationError(ViewError):
    """Raised when view operations fail."""
