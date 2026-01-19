"""Runtime - execution context for EveryFlow."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self


if TYPE_CHECKING:
    from .services import (
        AttributesService,
        CancellationService,
        CheckpointService,
        SignalService,
        StateService,
        TermsService,
    )
    from .storage import StorageProvider
    from .types import Path, Services


__all__ = [
    "RuntimeProtocol",
]


class RuntimeProtocol(Protocol):
    """Protocol for Runtime with specific capabilities."""

    def __init__(self, path: Path, storage: StorageProvider, services: Services) -> None:
        """Initialize runtime protocol."""
        ...

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

    @property
    def storage(self) -> StorageProvider:
        """Access storage."""
        ...

    @property
    def state(self) -> StateService:
        """Access state service."""
        ...

    @property
    def cancellation(self) -> CancellationService:
        """Access cancellation service."""
        ...

    @property
    def checkpoint(self) -> CheckpointService:
        """Access checkpoint service."""
        ...

    @property
    def terms(self) -> TermsService:
        """Access term execution service."""
        ...

    @property
    def attributes(self) -> AttributesService:
        """Access attribute service."""
        ...

    @property
    def signal(self) -> SignalService:
        """Access signal service."""
        ...
