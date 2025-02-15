import abc
from dataclasses import dataclass
from typing import AsyncContextManager, Self

from loomi.app.base import AsyncApp

from .base import AppCommonModel
from .protocols import AsyncAccessorContextProtocol

__all__ = ["AsyncAppModel"]

@dataclass
class AsyncModelContext:
    transaction: AsyncAccessorContextProtocol | None = ...
    def __init__(self, transaction=...) -> None: ...

class AsyncAppModel(AppCommonModel, AsyncApp, metaclass=abc.ABCMeta):
    @property
    def context(self) -> AsyncAccessorContextProtocol: ...
    async def model_transaction(self) -> AsyncContextManager[Self]: ...
