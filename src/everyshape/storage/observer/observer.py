"""Protocol definitions for coddec, storage, and observer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol


if TYPE_CHECKING:
    from everyshape.loc import key
    from everyshape.storage import CallbackFn, CodecProtocol


__all__ = [
    "ObserverProtocol",
    "SubscriptionProtocol",
]


class ObserverProtocol[EncodedKeyT](Protocol):
    """Protocol for observable adapters."""

    @property
    def codec(self) -> CodecProtocol[EncodedKeyT, Any]:
        """Get key codec for encoding topics."""
        ...

    def subscribe(
        self, prefix: key.Key, callback: CallbackFn, prefix_depth: int = 0
    ) -> SubscriptionProtocol:
        """Subscribe to changes under key prefix.

        Args:
            prefix: Key prefix to subscribe to
            callback: Callback function for notifications
            prefix_depth: Depth of topic pattern matching (default: 0 for exact match, 1 for prefix, -1 for all subkeys)

        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        ...

    def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...

    def notify(self, topic: key.Key) -> None:
        """Notify observers of a change at the specified topic.

        Args:
            topic: Topic identifying changed state

        Raises:
            ObserverError: If notification fails
        """

    def __hash__(self) -> int:
        """Get hash of the observer.

        Returns:
            Hash value of the observer
        """
        ...

    def __eq__(self, other: object) -> bool:
        """Check equality of the observer.

        Args:
            other: Observer to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


class SubscriptionProtocol(Protocol):
    """Represents a subscription to a topic pattern.

    Attributes:
        prefix:
            Topic pattern to match against notifications.
            Must be a tuple of strings matching state keys.
        callback:
            Callable that will be invoked on matching notifications.
            Must accept a single parameter of type StorageValue.
        prefix_depth:
            Depth of topic pattern matching.
            0 = exact match, 1 = prefix match, -1 = all subkeys
    """

    @property
    def prefix(self) -> key.Key:
        """Get topic pattern for subscription."""
        ...

    @property
    def callback(self) -> CallbackFn:
        """Get callback for subscription."""
        ...

    @property
    def prefix_depth(self) -> int:
        """Get depth for subscription."""
        ...
