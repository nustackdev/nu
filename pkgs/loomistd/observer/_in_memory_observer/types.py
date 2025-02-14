from typing import Protocol, TypeAlias, runtime_checkable

from .._protocols import ObserverProtocol

InMemoryObserverKey: TypeAlias = tuple[str, ...]
InMemoryObserverEncodedKey: TypeAlias = str


@runtime_checkable
class InMemoryObserverProtocol(
    ObserverProtocol[InMemoryObserverKey, InMemoryObserverEncodedKey], Protocol
):
    """
    In-memory observer protocol.
    """

    ...
