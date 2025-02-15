from dataclasses import dataclass
from typing import Any, Protocol

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
    op_type: str
    key: InMemoryStorageKey
    value: InMemoryStorageValue | None = ...
    def __init__(self, op_type, key, value=...) -> None: ...

class InMemoryStorageProtocol(
    StorageProtocol[
        InMemoryStorageKey,
        InMemoryStorageValue,
        InMemoryStorageEncodedKey,
        InMemoryStorageEncodedValue,
    ],
    Protocol,
): ...
