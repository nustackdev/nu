"""Subscription system for storage observers.

Provides flexible filtering capabilities for subscriptions:
- Prefix matching: Subscribe to keys starting with a prefix
- Suffix matching: Subscribe to keys ending with a suffix
- Wildcard matching: Subscribe to keys with wildcard patterns (* matches any segment)
- Length filtering: Subscribe to keys of exact length
- Composite filters: Combine multiple filters with AND logic
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Generator
    from types import TracebackType

    from everykv.loc import key

    from ..filter import Filter
    from .observer import ObserverProtocol
    from .types import SubscriptionCallback, SubscriptionOptions


__all__ = [
    "Subscription",
]


@dataclass(eq=False)
class Subscription:
    """Subscription that can bind and unbind receiver callbacks.

    Subscriptions are decoupled from callbacks - create a subscription once,
    then bind/unbind callbacks as needed.

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

        >>> # Close subscription when done
        >>> sub.close()
    """

    _options: SubscriptionOptions
    _observer: ObserverProtocol
    _receivers: list[SubscriptionCallback] = field(default_factory=list, init=False)
    _closed: bool = field(default=False, init=False)

    def __hash__(self) -> int:
        """Return hash based on object identity."""
        return id(self)

    @property
    def options(self) -> SubscriptionOptions:
        """Get subscription options."""
        return self._options

    @property
    def filter(self) -> Filter:
        """Get subscription filter."""
        return self._options.filter

    @property
    def receivers(self) -> tuple[SubscriptionCallback, ...]:
        """Get bound receivers (immutable copy)."""
        return tuple(self._receivers)

    @property
    def is_closed(self) -> bool:
        """Check if subscription is closed."""
        return self._closed

    def bind(self, receiver: SubscriptionCallback) -> None:
        """Bind a receiver callback to this subscription.

        Args:
            receiver: Callback function that receives key notifications.

        Raises:
            ValueError: If subscription is closed.
        """
        if self._closed:
            raise ValueError("Cannot bind to a closed subscription")
        if receiver not in self._receivers:
            self._receivers.append(receiver)

    def unbind(self, receiver: SubscriptionCallback) -> None:
        """Unbind a receiver callback from this subscription.

        Args:
            receiver: Callback function to unbind.

        Raises:
            ValueError: If receiver is not bound.
        """
        try:
            self._receivers.remove(receiver)
        except ValueError as e:
            raise ValueError("Receiver is not bound to this subscription") from e

    def bind_context(self, receiver: SubscriptionCallback) -> _SubscriptionContext:
        """Return a context manager that binds/unbinds a receiver.

        Args:
            receiver: Callback function to bind.

        Returns:
            Context manager that binds on enter and unbinds on exit.

        Examples:
            >>> with subscription.bind_context(my_callback):
            ...     # my_callback is bound here
            ...     pass
            >>> # my_callback is automatically unbound
        """
        return _SubscriptionContext(self, receiver)

    def __call__(self, receiver: SubscriptionCallback) -> _SubscriptionContext:
        """Shorthand for bind_context.

        Args:
            receiver: Callback function to bind.

        Returns:
            Context manager that binds on enter and unbinds on exit.

        Examples:
            >>> with subscription(my_callback):
            ...     # my_callback is bound here
            ...     pass
        """
        return self.bind_context(receiver)

    def close(self) -> None:
        """Close this subscription and remove it from the observer.

        After closing, no more receivers can be bound.
        """
        if not self._closed:
            self._closed = True
            self._receivers.clear()
            self._observer._close_subscription(self)

    def notify(self, key: key.Key) -> Generator[Exception, None, None]:
        """Notify all bound receivers of a key change.

        This is called internally by the observer when a matching key changes.

        Args:
            key: Key that changed.

        Yields:
            Exceptions raised by receivers (for error handling).
        """
        for receiver in self._receivers:
            try:
                receiver(key)
            except Exception as e:
                yield e


@dataclass
class _SubscriptionContext:
    """Context manager for temporarily binding a receiver."""

    _subscription: Subscription
    _receiver: SubscriptionCallback

    def __enter__(self) -> Subscription:
        """Bind the receiver on context entry."""
        self._subscription.bind(self._receiver)
        return self._subscription

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Unbind the receiver on context exit."""
        try:
            self._subscription.unbind(self._receiver)
        except ValueError:
            # Receiver was already unbound
            pass
