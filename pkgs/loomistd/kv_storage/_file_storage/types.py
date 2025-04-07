from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .._protocols import StorageProtocol

__all__ = [
    "FileStorageKey",
    "FileStorageValue",
    "FileStorageEncodedKey",
    "FileStorageEncodedValue",
    "FileStorageProtocol",
    "TransactionOperation",
]

FileStorageKey = tuple[str, ...]
FileStorageValue = (
    None
    | bytes
    | bool
    | int
    | float
    | str
    | list["FileStorageValue"]
    | dict[str, "FileStorageValue"]
)
FileStorageEncodedKey = str
FileStorageEncodedValue = str


@dataclass
class TransactionOperation:
    """Represents a single operation in a transaction."""

    op_type: str  # "set" or "delete"
    key: FileStorageKey
    value: FileStorageValue | None = None


@runtime_checkable
class FileStorageProtocol(
    StorageProtocol[
        FileStorageKey, FileStorageValue, FileStorageEncodedKey, FileStorageEncodedValue
    ],
    Protocol,
):
    """
    File storage protocol.
    """

    ...
