from __future__ import annotations

from loomicore import AsyncResource, SyncResource

__all__ = [
    "AsyncService",
    "SyncService",
]


class AsyncService(AsyncResource):
    """Asynchronous service resource."""

    pass


class SyncService(SyncResource):
    """Synchronous service resource."""

    pass
