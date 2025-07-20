from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .._protocols import StorageServiceProtocol
from .._types import StorageKey, StorageValue

__all__ = [
    "InMemoryStorageKey",
    "InMemoryStorageValue",
    "InMemoryStorageEncodedKey",
    "InMemoryStorageEncodedValue",
    "InMemoryStorageProtocol",
    "TransactionOperation",
]


InMemoryStorageKey = StorageKey
InMemoryStorageValue = StorageValue
InMemoryStorageEncodedKey = str
InMemoryStorageEncodedValue = StorageValue


@dataclass
class TransactionOperation:
    """Represents a single operation in a transaction."""

    op_type: str  # "set" or "delete"
    key: InMemoryStorageKey
    value: InMemoryStorageValue | None = None


@runtime_checkable
class InMemoryStorageProtocol(
    StorageServiceProtocol[
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
