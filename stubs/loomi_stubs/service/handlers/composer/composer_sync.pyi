from loomi.service.base import SyncService

from .base import ServiceCommonComposer

__all__ = ["SyncServiceComposer"]

class SyncServiceComposer(ServiceCommonComposer, SyncService): ...
