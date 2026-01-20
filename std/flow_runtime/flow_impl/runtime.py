"""Runtime - execution context for EveryFlow."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import attrs

from .protocol import RuntimeProtocol


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
    "Runtime",
]


@attrs.frozen
class Runtime[ServicesT: Services](RuntimeProtocol):
    """Execution runtime - carries infrastructure and provides execution primitives.

    All application data lives in EveryShape state.
    Runtime provides:
    - Where we are (structural path)
    - How to access state (services)
    - Current transaction (if in atomic block)
    - Term/child execution
    """

    path: Path  # type: ignore
    storage: StorageProvider  # type: ignore
    services: ServicesT

    # =========================================================================
    # Derivation
    # =========================================================================

    def child(self, component: int | str) -> Self:
        """Create child runtime with extended path."""
        return attrs.evolve(self, path=self.path.child(component))

    # =========================================================================
    # Path Management
    # =========================================================================

    @property
    def depth(self) -> int:
        """Get runtime depth."""
        return self.path.depth

    @property
    def is_root(self) -> bool:
        """Check if this is root runtime."""
        return self.path.is_root

    # =========================================================================
    # Service Access
    # =========================================================================

    @property
    def state(self) -> StateService:
        """Access state service."""
        return self.services.state

    @property
    def cancellation(self) -> CancellationService:
        """Access cancellation service."""
        return self.services.cancellation

    @property
    def checkpoint(self) -> CheckpointService:
        """Access checkpoint service."""
        return self.services.checkpoint

    @property
    def terms(self) -> TermsService:
        """Access term execution service."""
        return self.services.terms

    @property
    def attributes(self) -> AttributesService:
        """Access attribute service."""
        return self.services.attrbiutes

    @property
    def signal(self) -> SignalService:
        """Access signal service."""
        return self.services.signal

    # =========================================================================
    # Representation
    # =========================================================================

    def __repr__(self) -> str:
        """Get runtime representation."""
        return f"<Runtime path={self.path}>"

    def __str__(self) -> str:
        """Get runtime string representation."""
        return f"Runtime(path={self.path})"
