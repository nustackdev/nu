from _typeshed import Incomplete

from ._protocols import (
    TransactionalHandlerProtocol,
    TransactionContextManagerProtocol,
    TransactionProtocol,
)
from ._types import StorageKeyT, StorageValueT

__all__ = ["TransactionContextManager"]

class TransactionContextManager(TransactionContextManagerProtocol[StorageKeyT, StorageValueT]):
    handler: Incomplete
    transaction: Incomplete
    def __init__(
        self, handler: TransactionalHandlerProtocol[StorageKeyT, StorageValueT]
    ) -> None: ...
    async def __aenter__(self) -> TransactionProtocol[StorageKeyT, StorageValueT]: ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
