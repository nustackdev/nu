"""Backend-specific types."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from redwood.abc import TupleKey


# ========================================================
# Storage-specific types
# ========================================================


type StorageMode = Literal["read", "write"]


@dataclass(frozen=True, slots=True)
class StorageCapabilities:
    """Feature flags describing what a storage backend can do."""

    transactions: bool = True
    snapshots: bool = True
    scan: bool = False
    approximate_size: bool = False
    range_delete: bool = False
    batch_mutation: bool = False
    ttl: bool = False


@dataclass(frozen=True, slots=True)
class ScanOptions:
    """Configuration for ordered range scans."""

    prefix: TupleKey = ()
    start: TupleKey | None = None  # inclusive lower bound
    end: TupleKey | None = None  # exclusive upper bound
    depth: int = -1
    reverse: bool = False
    limit: int | None = None


@dataclass(frozen=True, slots=True)
class StorageDescriptor:
    """High-level description of a storage instance and capabilities."""

    name: str
    mode: StorageMode
    capabilities: StorageCapabilities
    details: Mapping[str, Any] = field(default_factory=dict)
    warnings: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # Ensure detail mapping is immutable to callers.
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))
