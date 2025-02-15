from typing import Protocol

from loomi.app.base import AsyncApp, SyncApp

__all__ = ["AsyncOperationProtocol", "SyncOperationProtocol"]

class AsyncOperationProtocol(Protocol):
    async def execute(self, app: AsyncApp) -> None: ...

class SyncOperationProtocol(Protocol):
    def execute(self, app: SyncApp) -> None: ...
