from __future__ import annotations

from typing import Any, Protocol

from loomi.state.interface.observer import AsyncObservableProtocol
from loomistd.codec import CodecProtocol

from ._types import ObserverEncodedKeyT, ObserverKeyT

__all__ = [
    "ObserverServiceProtocol",
]


class ObserverServiceProtocol(AsyncObservableProtocol, Protocol[ObserverKeyT, ObserverEncodedKeyT]):
    """
    Protocol defining state change observation operations.

    Observer implementations handle state change notifications with:
    - Topic-based routing using StorageKeyT (tuple[str, ...])
    - Async notification delivery
    - Proper error handling and validation
    - Type safety through StorageKeyT constraints

    Type Parameters:
        StorageKeyT: Topic type (tuple of strings matching state keys)

    Implementation Requirements:
        - Must validate topic formats
        - Must handle concurrent subscriptions
        - Must guarantee notification delivery
        - Must support pattern matching on topics
    """

    @property
    def codec(self) -> CodecProtocol[ObserverKeyT, Any, ObserverEncodedKeyT, Any]:
        """
        Get codec for encoding/decoding topics.
        """
        ...

    async def connect(self) -> None:
        """
        Establish connection to notification system.

        Raises:
            ObserverConnectionError: If connection fails
        """
        ...

    async def disconnect(self) -> None:
        """
        Close connection to notification system.

        Raises:
            ObserverConnectionError: If disconnection fails
            ObserverError: If cleanup fails
        """
        ...

    async def notify(self, topic: ObserverKeyT) -> None:
        """
        Notify all subscribers of state change.

        Args:
            topic: Topic identifying changed state

        Raises:
            ObserverConnectionError: If not connected
            ObserverOperationError: If notification fails
            ObserverValidationError: If topic invalid
        """
        ...
