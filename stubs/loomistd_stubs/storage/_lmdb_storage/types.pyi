from typing import Protocol

from _typeshed import Incomplete

from .._protocols import StorageProtocol

__all__ = [
    "LMDBStorageKey",
    "LMDBStorageValue",
    "LMDBStorageEncodedKey",
    "LMDBStorageEncodedValue",
    "LMDBStorageProtocol",
]

LMDBStorageKey = tuple[str, ...]
LMDBStorageValue: Incomplete
LMDBStorageEncodedKey = bytes
LMDBStorageEncodedValue = bytes

class LMDBStorageProtocol(
    StorageProtocol[
        LMDBStorageKey, LMDBStorageValue, LMDBStorageEncodedKey, LMDBStorageEncodedValue
    ],
    Protocol,
): ...
