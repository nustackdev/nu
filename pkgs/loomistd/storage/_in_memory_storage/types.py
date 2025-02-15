from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .._protocols import StorageProtocol

__all__ = [
    "InMemoryStorageKey",
    "InMemoryStorageValue",
    "InMemoryStorageEncodedKey",
    "InMemoryStorageEncodedValue",
    "InMemoryStorageProtocol",
    "TransactionOperation",
]


InMemoryStorageKey = tuple[str, ...]
InMemoryStorageValue = Any
InMemoryStorageEncodedKey = str
InMemoryStorageEncodedValue = Any


@dataclass
class TransactionOperation:
    """Represents a single operation in a transaction."""

    op_type: str  # "set" or "delete"
    key: InMemoryStorageKey
    value: InMemoryStorageValue | None = None


@runtime_checkable
class InMemoryStorageProtocol(
    StorageProtocol[
        InMemoryStorageKey,
        InMemoryStorageValue,
        InMemoryStorageEncodedKey,
        InMemoryStorageEncodedValue,
    ],
    Protocol,
):
    """
    In-memory storage protocol.
    """

    ...
