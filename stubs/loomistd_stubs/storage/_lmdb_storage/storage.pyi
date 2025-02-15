from pathlib import Path
from typing import AsyncGenerator

import lmdb
from _typeshed import Incomplete

from loomi.service import AsyncService, Spec

from .._base import BaseStorage, BaseStorageSpec
from .._protocols import TransactionProtocol
from .types import LMDBStorageEncodedKey, LMDBStorageEncodedValue, LMDBStorageKey, LMDBStorageValue

__all__ = ["LMDBStorage", "LMDBStorageSpec", "LMDBStorageTransaction"]

class LMDBStorageSpec(BaseStorageSpec):
    path: Path
    codec: Spec
    map_size: int
    max_dbs: int
    lmdb_kwargs: dict
    @classmethod
    def identity_fields(cls) -> set[str]: ...
    def serialize_path(self, path: Path) -> str: ...

class LMDBStorage(
    BaseStorage[LMDBStorageKey, LMDBStorageValue, LMDBStorageEncodedKey, LMDBStorageEncodedValue],
    AsyncService,
):
    path: Incomplete
    map_size: Incomplete
    max_dbs: Incomplete
    lmdb_kwargs: Incomplete
    def __init__(self, spec: LMDBStorageSpec) -> None: ...

class LMDBStorageTransaction(TransactionProtocol[LMDBStorageKey, LMDBStorageValue]):
    def __init__(self, storage: LMDBStorage, txn: lmdb.Transaction) -> None: ...
    async def get(self, key: LMDBStorageKey) -> LMDBStorageValue: ...
    async def set(self, key: LMDBStorageKey, value: LMDBStorageValue) -> None: ...
    async def delete(self, key: LMDBStorageKey) -> None: ...
    async def exists(self, key: LMDBStorageKey) -> bool: ...
    async def list_keys(self, prefix: LMDBStorageKey) -> AsyncGenerator[LMDBStorageKey, None]: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
