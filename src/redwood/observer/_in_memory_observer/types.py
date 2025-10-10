from __future__ import annotations

from typing import Protocol

from .._protocols import ObserverServiceProtocol
from .._types import Key


__all__ = [
    "InMemoryObserverKey",
    "InMemoryObserverEncodedKey",
    "InMemoryObserverProtocol",
]

InMemoryObserverKey = Key
InMemoryObserverEncodedKey = str


class InMemoryObserverProtocol(
    ObserverServiceProtocol[InMemoryObserverKey, InMemoryObserverEncodedKey],
    Protocol,
):
    """In-memory observer protocol.
    """

    ...
