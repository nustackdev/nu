"""Runtime - execution context for EveryFlow."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self


if TYPE_CHECKING:
    from .path import Path


__all__ = [
    "Runtime",
]


class Runtime(Protocol):
    """Protocol for Runtime with specific capabilities."""

    storage_provider: object
    services: object

    # =========================================================================
    # Derivation
    # =========================================================================

    def child(self, component: int | str) -> Self:
        """Create child runtime with extended path."""
        ...

    # =========================================================================
    # Path Management
    # =========================================================================

    @property
    def path(self) -> Path:
        """Get current structural path."""
        ...

    @property
    def depth(self) -> int:
        """Get runtime depth."""
        ...

    @property
    def is_root(self) -> bool:
        """Check if this is root runtime."""
        ...

    # =========================================================================
    # Service Access
    # =========================================================================
