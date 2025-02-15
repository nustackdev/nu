from .base import ServiceMeta
from .handlers.composer import AsyncServiceComposer, SyncServiceComposer
from .handlers.initializer import AsyncServiceInitializer, SyncServiceInitializer

__all__ = ["AsyncService", "SyncService"]

class AsyncService(AsyncServiceComposer, AsyncServiceInitializer, metaclass=ServiceMeta): ...
class SyncService(SyncServiceComposer, SyncServiceInitializer, metaclass=ServiceMeta): ...
