from typing import AsyncGenerator

from loomi.service import AsyncService
from loomistd.codec import CodecProtocol

from .._base import BaseStorage, BaseStorageSpec
from .._protocols import TransactionProtocol
from .types import (
    InMemoryStorageEncodedKey,
    InMemoryStorageEncodedValue,
    InMemoryStorageKey,
    InMemoryStorageValue,
)

__all__ = ["InMemoryStorage", "InMemoryStorageSpec", "InMemoryStorageTransaction"]

class InMemoryStorageSpec(BaseStorageSpec): ...

class InMemoryStorage(
    BaseStorage[
        InMemoryStorageKey,
        InMemoryStorageValue,
        InMemoryStorageEncodedKey,
        InMemoryStorageEncodedValue,
    ],
    AsyncService,
):
    codec: CodecProtocol[
        InMemoryStorageKey,
        InMemoryStorageValue,
        InMemoryStorageEncodedKey,
        InMemoryStorageEncodedValue,
    ]
    def __init__(self, spec: BaseStorageSpec) -> None: ...

class InMemoryStorageTransaction(TransactionProtocol[InMemoryStorageKey, InMemoryStorageValue]):
    def __init__(self, storage: InMemoryStorage) -> None: ...
    async def get(self, key: InMemoryStorageKey) -> InMemoryStorageValue: ...
    async def set(self, key: InMemoryStorageKey, value: InMemoryStorageValue) -> None: ...
    async def delete(self, key: InMemoryStorageKey) -> None: ...
    async def exists(self, key: InMemoryStorageKey) -> bool: ...
    async def list_keys(
        self, prefix: InMemoryStorageKey
    ) -> AsyncGenerator[InMemoryStorageKey, None]: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
