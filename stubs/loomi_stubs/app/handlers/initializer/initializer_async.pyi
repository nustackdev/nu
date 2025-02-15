import abc
from types import TracebackType
from typing import Self

from loomi.app.base import AsyncApp

from .base import AppCommonInitializer

__all__ = ["AsyncAppInitializer"]

class AsyncAppInitializer(AppCommonInitializer, AsyncApp, metaclass=abc.ABCMeta):
    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
