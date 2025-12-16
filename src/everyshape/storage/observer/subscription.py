"""Subscription system for storage observers.

Provides flexible filtering capabilities for subscriptions:
- Prefix matching: Subscribe to keys starting with a prefix
- Suffix matching: Subscribe to keys ending with a suffix
- Wildcard matching: Subscribe to keys with wildcard patterns (* matches any segment)
- Length filtering: Subscribe to keys of exact length
- Composite filters: Combine multiple filters with AND logic
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from types import TracebackType

    from everyshape.loc import key

    from .observer import ObserverProtocol


__all__ = [
    "CompositeFilter",
    "LengthFilter",
    "PrefixFilter",
    "Subscription",
    "SubscriptionFilter",
    "SubscriptionOptions",
    "SubscriptionReceiver",
    "SuffixFilter",
    "WildcardFilter",
]


# =============================================================================
# Subscription Callback Type
# =============================================================================

type SubscriptionReceiver = SubscriptionCallback
"""Receiver function type for subscription notifications."""

type SubscriptionCallback = "Callable[[key.Key], None]"
"""Callback function type for subscription notifications."""


# =============================================================================
# Filter Types
# =============================================================================


class SubscriptionFilter(ABC):
    """Base class for subscription filters.

    Filters define matching criteria for keys. When a key is modified,
    the filter determines if the subscription should be notified.
    """

    @abstractmethod
    def matches(self, key: key.Key) -> bool:
        """Check if a key matches this filter.

        Args:
            key: Key to check against the filter.

        Returns:
            True if the key matches the filter criteria.
        """
        raise NotImplementedError

    @abstractmethod
    def __hash__(self) -> int:
        """Return hash for use in sets and dicts."""
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Check equality with another filter."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class PrefixFilter(SubscriptionFilter):
    """Match keys that start with a given prefix.

    Examples:
        >>> f = PrefixFilter(prefix=("users",))
        >>> f.matches(("users", "alice"))  # True
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("posts",))  # False
    """

    prefix: key.Key
    """Prefix that keys must start with."""

    def matches(self, key: key.Key) -> bool:
        """Check if key starts with the prefix."""
        if len(key) < len(self.prefix):
            return False
        return key[: len(self.prefix)] == self.prefix

    def __hash__(self) -> int:
        """Return hash based on prefix."""
        return hash(("prefix", self.prefix))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, PrefixFilter):
            return NotImplemented
        return self.prefix == other.prefix


@dataclass(frozen=True, slots=True)
class SuffixFilter(SubscriptionFilter):
    """Match keys that end with a given suffix.

    Examples:
        >>> f = SuffixFilter(suffix=("profile",))
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("posts", "123", "profile"))  # True
        >>> f.matches(("users", "alice"))  # False
    """

    suffix: key.Key
    """Suffix that keys must end with."""

    def matches(self, key: key.Key) -> bool:
        """Check if key ends with the suffix."""
        if len(key) < len(self.suffix):
            return False
        return key[-len(self.suffix) :] == self.suffix

    def __hash__(self) -> int:
        """Return hash based on suffix."""
        return hash(("suffix", self.suffix))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, SuffixFilter):
            return NotImplemented
        return self.suffix == other.suffix


# Sentinel for wildcard matching
WILDCARD = "*"
"""Wildcard segment that matches any single key segment."""


@dataclass(frozen=True, slots=True)
class WildcardFilter(SubscriptionFilter):
    """Match keys with wildcard patterns.

    Use '*' to match any single segment in the pattern.

    Examples:
        >>> f = WildcardFilter(pattern=("users", "*", "profile"))
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("users", "bob", "profile"))  # True
        >>> f.matches(("users", "alice", "settings"))  # False
        >>> f.matches(("users", "alice"))  # False (length mismatch)
    """

    pattern: key.Key
    """Pattern with wildcards. '*' matches any single segment."""

    def matches(self, key: key.Key) -> bool:
        """Check if key matches the wildcard pattern."""
        if len(key) != len(self.pattern):
            return False
        return all(p == WILDCARD or k == p for k, p in zip(key, self.pattern, strict=True))

    def __hash__(self) -> int:
        """Return hash based on pattern."""
        return hash(("wildcard", self.pattern))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, WildcardFilter):
            return NotImplemented
        return self.pattern == other.pattern


@dataclass(frozen=True, slots=True)
class LengthFilter(SubscriptionFilter):
    """Match keys with exact length.

    Examples:
        >>> f = LengthFilter(length=3)
        >>> f.matches(("a", "b", "c"))  # True
        >>> f.matches(("a", "b"))  # False
        >>> f.matches(("a", "b", "c", "d"))  # False
    """

    length: int
    """Exact length that keys must have."""

    def matches(self, key: key.Key) -> bool:
        """Check if key has the exact length."""
        return len(key) == self.length

    def __hash__(self) -> int:
        """Return hash based on length."""
        return hash(("length", self.length))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, LengthFilter):
            return NotImplemented
        return self.length == other.length


@dataclass(frozen=True, slots=True)
class CompositeFilter(SubscriptionFilter):
    """Combine multiple filters with AND logic.

    All contained filters must match for the composite to match.

    Examples:
        >>> f = CompositeFilter(
        ...     filters=(
        ...         PrefixFilter(prefix=("users",)),
        ...         LengthFilter(length=3),
        ...     )
        ... )
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("users", "alice"))  # False (length mismatch)
        >>> f.matches(("posts", "123", "title"))  # False (prefix mismatch)
    """

    filters: tuple[SubscriptionFilter, ...]
    """Tuple of filters to combine with AND logic."""

    def matches(self, key: key.Key) -> bool:
        """Check if key matches all filters."""
        return all(f.matches(key) for f in self.filters)

    def __hash__(self) -> int:
        """Return hash based on all filters."""
        return hash(("composite", self.filters))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, CompositeFilter):
            return False
        return self.filters == other.filters


# =============================================================================
# Subscription Options
# =============================================================================


@dataclass(frozen=True, slots=True)
class SubscriptionOptions:
    """Options for creating a subscription.

    Attributes:
        filter: Filter that determines which keys trigger notifications.

    Examples:
        >>> # Subscribe to all keys under "users"
        >>> opts = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))

        >>> # Subscribe to keys matching a wildcard pattern
        >>> opts = SubscriptionOptions(
        ...     filter=WildcardFilter(pattern=("users", "*", "profile"))
        ... )

        >>> # Subscribe to keys with specific prefix AND length
        >>> opts = SubscriptionOptions(
        ...     filter=CompositeFilter(
        ...         filters=(
        ...             PrefixFilter(prefix=("users",)),
        ...             LengthFilter(length=3),
        ...         )
        ...     )
        ... )
    """

    filter: SubscriptionFilter
    """Filter that determines which keys trigger notifications."""

    def __hash__(self) -> int:
        """Return hash based on filter."""
        return hash(self.filter)

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, SubscriptionOptions):
            return NotImplemented
        return self.filter == other.filter


# =============================================================================
# Subscription
# =============================================================================


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
    def filter(self) -> SubscriptionFilter:
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
