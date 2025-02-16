from dataclasses import dataclass
from typing import Protocol

from _typeshed import Incomplete

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
FileStorageValue: Incomplete
FileStorageEncodedKey = str
FileStorageEncodedValue = str

@dataclass
class TransactionOperation:
    op_type: str
    key: FileStorageKey
    value: FileStorageValue | None = ...

class FileStorageProtocol(
    StorageProtocol[
        FileStorageKey, FileStorageValue, FileStorageEncodedKey, FileStorageEncodedValue
    ],
    Protocol,
): ...
