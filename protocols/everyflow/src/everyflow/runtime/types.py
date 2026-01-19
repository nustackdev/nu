"""Runtime types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import attrs

from .services import (
    AttributesService,
    CancellationService,
    CheckpointService,
    SignalService,
    StateService,
    TermsService,
)


if TYPE_CHECKING:
    from .storage import StorageProvider


__all__ = [
    "Path",
    "Services",
]


@attrs.frozen
class Services:
    """Infrastructure services container - injected at root."""

    state: StateService
    cancellation: CancellationService
    checkpoint: CheckpointService
    terms: TermsService
    attrbiutes: AttributesService
    signal: SignalService

    @classmethod
    def create(cls, storage: StorageProvider) -> Services:
        """Create services from storage."""
        return cls(
            state=StateService(storage),
            cancellation=CancellationService(storage),
            checkpoint=CheckpointService(storage),
            terms=TermsService(storage),
            attrbiutes=AttributesService(storage),
            signal=SignalService(storage),
        )


type Segment = str | int


@attrs.define(frozen=True, slots=True, hash=True)
class Path:
    """Deterministic path in flow execution tree."""

    components: tuple[Segment, ...] = attrs.field(factory=tuple, converter=tuple)

    @classmethod
    def root(cls) -> Self:
        """Create root path."""
        return cls((0,))

    @classmethod
    def from_string(cls, path_str: str, separator: str = "-") -> Self:
        """Parse path from string representation."""
        if not path_str:
            raise ValueError("Empty string passed. Path should start with 0 base.")

        parts = path_str.strip(separator).split(separator)
        return cls(tuple(parts))

    @property
    def is_root(self) -> bool:
        """Check if this is the root path."""
        return len(self.components) == 1

    @property
    def depth(self) -> int:
        """Get the depth of this path."""
        return len(self.components)

    @property
    def parent(self) -> Path | None:
        """Get the parent path."""
        if self.is_root:
            return None
        return Path(self.components[:-1])

    @property
    def name(self) -> Segment:
        """Get the last component (name) of this path."""
        return self.components[-1]

    def child(self, component: Segment) -> Path:
        """Create a child path with the given component."""
        return Path((*self.components, component))

    def to_key(self) -> str:
        """Key representation."""
        return "-".join(str(c) for c in self.components)

    def __len__(self) -> int:
        """Return the depth of the path."""
        return self.depth

    def __repr__(self) -> str:
        """Representation."""
        return f"Path({self.components})"

    def __str__(self) -> str:
        """String representation."""
        return f"Path({self.components})"
