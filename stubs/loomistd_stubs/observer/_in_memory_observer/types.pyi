from typing import Protocol

from .._protocols import ObserverProtocol

__all__ = ["InMemoryObserverKey", "InMemoryObserverEncodedKey", "InMemoryObserverProtocol"]

InMemoryObserverKey = tuple[str, ...]
InMemoryObserverEncodedKey = str

class InMemoryObserverProtocol(
    ObserverProtocol[InMemoryObserverKey, InMemoryObserverEncodedKey], Protocol
): ...
