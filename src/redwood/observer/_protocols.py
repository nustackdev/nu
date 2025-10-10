from __future__ import annotations

from typing import Any, Protocol

from loomi.tree import ObserverProtocol
from loomistd.codec import CodecProtocol

from ._types import ObserverEncodedKeyT, ObserverKeyT


__all__ = [
    "ObserverServiceProtocol",
]


class ObserverServiceProtocol(ObserverProtocol, Protocol[ObserverKeyT, ObserverEncodedKeyT]):
    """Protocol defining state change observation operations.

    Observer implementations handle state change notifications with:
    - Topic-based routing using StorageKeyT (tuple[str, ...])
    - Sync notification delivery
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
        """Get codec for encoding/decoding topics.
        """
        ...

    def connect(self) -> None:
        """Establish connection to notification system.

        Raises:
            ObserverConnectionError: If connection fails
        """
        ...

    def disconnect(self) -> None:
        """Close connection to notification system.

        Raises:
            ObserverConnectionError: If disconnection fails
            ObserverError: If cleanup fails
        """
        ...

    def notify(self, topic: ObserverKeyT) -> None:
        """Notify all subscribers of state change.

        Args:
            topic: Topic identifying changed state

        Raises:
            ObserverConnectionError: If not connected
            ObserverOperationError: If notification fails
            ObserverValidationError: If topic invalid
        """
        ...
