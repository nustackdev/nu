from __future__ import annotations

from typing import Protocol, runtime_checkable

from .._protocols import StorageServiceProtocol
from .._types import Key


__all__ = [
    "LMDBStorageKey",
    "LMDBStorageValue",
    "LMDBStorageEncodedKey",
    "LMDBStorageEncodedValue",
    "LMDBStorageProtocol",
]

LMDBStorageKey = Key
LMDBStorageValue = (
    None
    | bytes
    | bool
    | int
    | float
    | str
    | list["LMDBStorageValue"]
    | dict[str, "LMDBStorageValue"]
)
LMDBStorageEncodedKey = bytes
LMDBStorageEncodedValue = bytes


@runtime_checkable
class LMDBStorageProtocol(
    StorageServiceProtocol[
        LMDBStorageKey,
        LMDBStorageValue,
        LMDBStorageEncodedKey,
        LMDBStorageEncodedValue,
    ],
    Protocol,
):
    """LMDB storage protocol.
    """

    ...
