from __future__ import annotations

from .composer import AsyncServiceComposer, SyncServiceComposer
from .initializer import AsyncServiceInitializer, SyncServiceInitializer
from .meta import ServiceMeta

__all__ = [
    "AsyncService",
    "SyncService",
    "Service",
]


class AsyncService(
    AsyncServiceComposer,
    AsyncServiceInitializer,
    metaclass=ServiceMeta,
):
    pass


class SyncService(
    SyncServiceComposer,
    SyncServiceInitializer,
    metaclass=ServiceMeta,
):
    pass


Service = AsyncService | SyncService
