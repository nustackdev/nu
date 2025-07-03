from __future__ import annotations

from ..exceptions import ResourceError

__all__ = [
    "RegistryError",
    "RegistryStateError",
    "RegistryKeyError",
]


class RegistryError(ResourceError):
    """Base exception for registry-related errors."""

    pass


class RegistryStateError(RegistryError):
    """Raised when registry is in invalid state."""

    pass


class RegistryKeyError(RegistryError):
    """Raised when resource key is invalid or not found."""

    pass
