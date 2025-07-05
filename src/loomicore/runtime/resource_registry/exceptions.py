from __future__ import annotations

from loomicore.exceptions import ResourceError

__all__ = [
    "RegistryError",
    "RegistryKeyError",
]


class RegistryError(ResourceError):
    """Base exception for registry-related errors."""

    pass


class RegistryKeyError(RegistryError):
    """Raised when resource key is invalid or not found."""

    pass
