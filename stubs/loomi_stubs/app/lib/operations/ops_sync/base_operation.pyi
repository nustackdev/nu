import abc
from abc import ABC, abstractmethod

from loomi.app.base import SyncApp as SyncApp

class BaseOperation(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def execute(self, app: SyncApp) -> None: ...
