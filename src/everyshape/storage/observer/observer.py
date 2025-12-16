"""Protocol definitions for observer system.

Defines the abstract interfaces for observers and subscriptions.
The new subscription system provides:
- Flexible filtering (prefix, suffix, wildcard, length, composite)
- Decoupled subscription from callbacks (subscribe once, bind/unbind callbacks)
- Efficient pattern matching with hash-based indexing
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from everyshape.loc import key
    from everyshape.storage import CallbackFn, CodecProtocol

    from .subscription import (
        Subscription,
        SubscriptionCallback,
        SubscriptionOptions,
    )


__all__ = [
    "ObserverProtocol",
    "SubscriptionProtocol",
]


@runtime_checkable
class SubscriptionProtocol(Protocol):
    """Protocol for subscriptions.

    Subscriptions are decoupled from callbacks - create a subscription once,
    then bind/unbind callbacks as needed.

    The subscription provides:
    - `bind(receiver)`: Bind a callback to receive notifications
    - `unbind(receiver)`: Unbind a previously bound callback
    - `bind_context(receiver)`: Context manager for temporary binding
    - `close()`: Close the subscription and remove from observer

    Examples:
        >>> # Create subscription
        >>> sub = observer.subscribe(
        ...     SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        ... )

        >>> # Bind callbacks
        >>> sub.bind(lambda key: print(f"Changed: {key}"))

        >>> # Use as context manager
        >>> with sub.bind_context(my_callback):
        ...     # my_callback is bound here
        ...     pass
        >>> # my_callback is automatically unbound

        >>> # Or use shorthand
        >>> with sub(my_callback):
        ...     pass

        >>> # Close subscription when done
        >>> sub.close()
    """

    @property
    def options(self) -> SubscriptionOptions:
        """Get subscription options."""
        ...

    @property
    def receivers(self) -> tuple[SubscriptionCallback, ...]:
        """Get bound receivers (immutable copy)."""
        ...

    @property
    def is_closed(self) -> bool:
        """Check if subscription is closed."""
        ...

    def bind(self, receiver: SubscriptionCallback) -> None:
        """Bind a receiver callback to this subscription.

        Args:
            receiver: Callback function that receives key notifications.

        Raises:
            ValueError: If subscription is closed.
        """
        ...

    def unbind(self, receiver: SubscriptionCallback) -> None:
        """Unbind a receiver callback from this subscription.

        Args:
            receiver: Callback function to unbind.

        Raises:
            ValueError: If receiver is not bound.
        """
        ...

    def bind_context(self, receiver: SubscriptionCallback) -> _SubscriptionContextProtocol:
        """Return a context manager that binds/unbinds a receiver.

        Args:
            receiver: Callback function to bind.

        Returns:
            Context manager that binds on enter and unbinds on exit.
        """
        ...

    def __call__(self, receiver: SubscriptionCallback) -> _SubscriptionContextProtocol:
        """Shorthand for bind_context."""
        ...

    def close(self) -> None:
        """Close this subscription and remove it from the observer."""
        ...

    # Legacy properties for backward compatibility
    @property
    def prefix(self) -> key.Key:
        """Get topic pattern for subscription (legacy).

        Deprecated:
            Use `options.filter` instead.
        """
        ...

    @property
    def callback(self) -> CallbackFn:
        """Get first callback for subscription (legacy).

        Deprecated:
            Use `receivers` instead.
        """
        ...

    @property
    def prefix_depth(self) -> int:
        """Get depth for subscription (legacy).

        Deprecated:
            Use `options.filter` instead.
        """
        ...


class _SubscriptionContextProtocol(Protocol):
    """Protocol for subscription context managers."""

    def __enter__(self) -> SubscriptionProtocol:
        """Bind receiver on entry."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Unbind receiver on exit."""
        ...


class ObserverProtocol[EncodedKeyT](Protocol):
    """Protocol for observable adapters.

    Observers provide subscription capabilities for storage changes, such as:
    - Flexible filtering (prefix, suffix, wildcard, length, composite)
    - Decoupled subscriptions from callbacks
    - Efficient pattern matching

    Examples:
        >>> # Subscribe with options
        >>> sub = observer.subscribe(
        ...     SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        ... )
        >>> sub.bind(lambda key: print(f"Changed: {key}"))
    """

    @property
    def codec(self) -> CodecProtocol[EncodedKeyT, Any]:
        """Get key codec for encoding topics."""
        ...

    def subscribe(self, options: SubscriptionOptions) -> Subscription:
        """Subscribe to key changes with flexible filtering.

        Args:
            options: Subscription options including filter specification.

        Returns:
            Subscription object for binding callbacks and managing lifecycle.

        Raises:
            ObserverError: If subscription fails.

        Examples:
            >>> # Subscribe to all keys under "users"
            >>> sub = observer.subscribe(
            ...     SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
            ... )

            >>> # Subscribe with wildcard pattern
            >>> sub = observer.subscribe(
            ...     SubscriptionOptions(
            ...         filter=WildcardFilter(pattern=("users", "*", "profile"))
            ...     )
            ... )

            >>> # Subscribe to keys with specific prefix AND length
            >>> sub = observer.subscribe(
            ...     SubscriptionOptions(
            ...         filter=CompositeFilter(
            ...             filters=(
            ...                 PrefixFilter(prefix=("users",)),
            ...                 LengthFilter(length=3),
            ...             )
            ...         )
            ...     )
            ... )
        """
        ...

    def notify(self, topic: key.Key) -> None:
        """Notify observers of a change at the specified topic.

        Args:
            topic: Topic identifying changed state.

        Raises:
            ObserverError: If notification fails.
        """
        ...

    def _close_subscription(self, subscription: Subscription) -> None:
        """Internal method to close a subscription.

        Called by Subscription.close() to remove subscription from observer.

        Args:
            subscription: Subscription to close.
        """
        ...
