from loomi.service import AsyncService

from .._base import BaseObserver, BaseObserverSpec
from .types import InMemoryObserverEncodedKey, InMemoryObserverKey

__all__ = ["InMemoryObserverSpec", "InMemoryObserver"]

class InMemoryObserverSpec(BaseObserverSpec): ...
class InMemoryObserver(
    BaseObserver[InMemoryObserverKey, InMemoryObserverEncodedKey], AsyncService
): ...
