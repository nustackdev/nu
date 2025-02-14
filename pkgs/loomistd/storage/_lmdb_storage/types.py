from typing import Protocol, TypeAlias, runtime_checkable

from .._protocols import StorageProtocol

LMDBStorageKey: TypeAlias = tuple[str, ...]
LMDBStorageValue: TypeAlias = (
    None
    | bytes
    | bool
    | int
    | float
    | str
    | list["LMDBStorageValue"]
    | dict[str, "LMDBStorageValue"]
)
LMDBStorageEncodedKey: TypeAlias = bytes
LMDBStorageEncodedValue: TypeAlias = bytes


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
