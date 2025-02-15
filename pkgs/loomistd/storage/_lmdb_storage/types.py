from __future__ import annotations

from typing import Protocol, runtime_checkable

from .._protocols import StorageProtocol

__all__ = [
    "LMDBStorageKey",
    "LMDBStorageValue",
    "LMDBStorageEncodedKey",
    "LMDBStorageEncodedValue",
    "LMDBStorageProtocol",
]

LMDBStorageKey = tuple[str, ...]
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
    StorageProtocol[
        LMDBStorageKey,
        LMDBStorageValue,
        LMDBStorageEncodedKey,
        LMDBStorageEncodedValue,
    ],
    Protocol,
):
    """
    LMDB storage protocol.
    """

    ...
