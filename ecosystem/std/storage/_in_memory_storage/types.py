from dataclasses import dataclass
from typing import Any, Protocol, TypeAlias, runtime_checkable

from .._protocols import StorageProtocol

InMemoryStorageKey: TypeAlias = tuple[str, ...]
InMemoryStorageValue: TypeAlias = Any
InMemoryStorageEncodedKey: TypeAlias = str
InMemoryStorageEncodedValue: TypeAlias = Any


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
