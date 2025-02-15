import abc
from types import TracebackType
from typing import Self

from loomi.app.base import SyncApp

from .base import AppCommonInitializer

__all__ = ["SyncAppInitializer"]

class SyncAppInitializer(AppCommonInitializer, SyncApp, metaclass=abc.ABCMeta):
    def initialize(self) -> None: ...
    def shutdown(self) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
