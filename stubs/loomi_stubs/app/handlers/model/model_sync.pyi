import abc
from dataclasses import dataclass
from typing import ContextManager, Self

from loomi.app.base import SyncApp

from .base import AppCommonModel
from .protocols import SyncAccessorContextProtocol

__all__ = ["SyncAppModel"]

@dataclass
class SyncModelContext:
    transaction: SyncAccessorContextProtocol | None = ...

class SyncAppModel(AppCommonModel, SyncApp, metaclass=abc.ABCMeta):
    @property
    def context(self) -> SyncAccessorContextProtocol: ...
    async def model_transaction(self) -> ContextManager[Self]: ...
