from typing import TypeAlias

from .base import ServiceMeta
from .handlers.composer.composer_async import ServiceComposer as ServiceAsyncComposer
from .handlers.composer.composer_sync import ServiceComposer as ServiceSyncComposer
from .handlers.initializer.initializer_async import ServiceInitializer as ServiceAsyncInitializer

# from .handlers.initializer.initializer_sync import ServiceInitializer as ServiceSyncInitializer


class AsyncService(ServiceAsyncComposer, ServiceAsyncInitializer, metaclass=ServiceMeta):
    pass


class SyncService(ServiceSyncComposer, metaclass=ServiceMeta):
    pass


Service: TypeAlias = AsyncService | SyncService


__all__ = ["Service", "AsyncService", "SyncService"]
