from loomi.service.base import AsyncService

from .base import ServiceCommonComposer

__all__ = ["AsyncServiceComposer"]

class AsyncServiceComposer(ServiceCommonComposer, AsyncService): ...
