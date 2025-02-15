import abc

from loomi.app.base import AsyncApp

from .base import AppCommonServices

__all__ = ["AsyncAppServices"]

class AsyncAppServices(AppCommonServices, AsyncApp, metaclass=abc.ABCMeta):
    async def initialize_services(self) -> None: ...
    async def shutdown_services(self) -> None: ...
