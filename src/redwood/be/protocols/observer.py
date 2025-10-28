"""Protocol definitions for coddec, storage, and observer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol


if TYPE_CHECKING:
    from redwood.abc import CallbackFn, TupleKey

    from .codec import CodecProtocol


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
        self, key: TupleKey, callback: CallbackFn, depth: int = ...
    ) -> SubscriptionProtocol:
        """Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Callback function for notifications
            depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.

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

    def notify(self, topic: TupleKey) -> None:
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
        topic_pattern:
            Topic pattern to match against notifications.
            Must be a tuple of strings matching state keys.
        callback:
            Callable that will be invoked on matching notifications.
            Must accept a single parameter of type StorageValue.

    Type Parameters:
        StorageValue: Topic type (tuple of strings)
    """

    @property
    def topic_pattern(self) -> TupleKey:
        """Get topic pattern for subscription."""
        ...

    @property
    def callback(self) -> CallbackFn:
        """Get callback for subscription."""
        ...

    @property
    def depth(self) -> int:
        """Get depth for subscription."""
        ...
