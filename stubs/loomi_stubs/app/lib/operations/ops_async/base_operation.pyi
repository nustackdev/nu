import abc
from abc import ABC, abstractmethod

from loomi.app.base import AsyncApp as AsyncApp

class BaseOperation(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    async def execute(self, app: AsyncApp) -> None: ...
