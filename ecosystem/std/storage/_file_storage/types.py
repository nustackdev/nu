from dataclasses import dataclass
from typing import Protocol, TypeAlias, runtime_checkable

from .._protocols import StorageProtocol

FileStorageKey: TypeAlias = tuple[str, ...]
FileStorageValue: TypeAlias = (
    None | bool | int | float | str | list["FileStorageValue"] | dict[str, "FileStorageValue"]
)
FileStorageEncodedKey: TypeAlias = str
FileStorageEncodedValue: TypeAlias = str


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
