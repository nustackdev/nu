from typing import Literal, TypeVar

StorageKeyT = TypeVar("StorageKeyT")
StorageValueT = TypeVar("StorageValueT")
StorageEncodedKeyT = TypeVar("StorageEncodedKeyT")
StorageEncodedValueT = TypeVar("StorageEncodedValueT")
StorageMode = Literal["read", "write"]
