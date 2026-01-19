"""Unified filter system for storage operations.

Provides composable, hashable filters for key matching.
Used by both scan operations and observer subscriptions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everykv.loc import key


__all__ = [
    "WILDCARD",
    "And",
    "Filter",
    "LengthFilter",
    "Or",
    "PassAll",
    "PassNone",
    "PrefixFilter",
    "SuffixFilter",
    "WildcardFilter",
]


WILDCARD = "*"
"""Wildcard segment matching any single key component."""


class Filter(ABC):
    """Base filter for key matching. Hashable and composable.

    Filters determine which keys match certain criteria. They are:
    - Immutable and hashable (for use in sets/dicts)
    - Composable via & (and) and | (or) operators
    - Short-circuit evaluated for efficiency

    Examples:
        >>> # Match keys starting with ("users",)
        >>> f = PrefixFilter(prefix=("users",))
        >>> f.matches(("users", "alice"))  # True

        >>> # Compose filters
        >>> f = PrefixFilter(prefix=("users",)) & LengthFilter(length=3)
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("users", "alice"))  # False (length mismatch)

        >>> # Or composition
        >>> f = PrefixFilter(prefix=("users",)) | PrefixFilter(prefix=("posts",))
        >>> f.matches(("users", "alice"))  # True
        >>> f.matches(("posts", "123"))  # True
    """

    @abstractmethod
    def matches(self, key: key.Key) -> bool:
        """Check if key matches this filter.

        Args:
            key: Key tuple to check.

        Returns:
            True if key matches filter criteria.
        """
        ...

    @abstractmethod
    def __hash__(self) -> int:
        """Return hash for use in sets and dicts."""
        ...

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Check equality with another filter."""
        ...

    def __and__(self, other: Filter) -> And:
        """Combine with AND logic: self & other."""
        return And(filters=(self, other))

    def __or__(self, other: Filter) -> Or:
        """Combine with OR logic: self | other."""
        return Or(filters=(self, other))


@dataclass(frozen=True, slots=True)
class PrefixFilter(Filter):
    """Match keys starting with prefix.

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
class SuffixFilter(Filter):
    """Match keys ending with suffix.

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
        if not self.suffix:  # Empty suffix matches everything
            return True
        return key[-len(self.suffix) :] == self.suffix

    def __hash__(self) -> int:
        """Return hash based on suffix."""
        return hash(("suffix", self.suffix))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, SuffixFilter):
            return NotImplemented
        return self.suffix == other.suffix


@dataclass(frozen=True, slots=True)
class LengthFilter(Filter):
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
class WildcardFilter(Filter):
    """Match keys with wildcard patterns.

    Use WILDCARD ('*') to match any single segment in the pattern.

    Examples:
        >>> f = WildcardFilter(pattern=("users", WILDCARD, "profile"))
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("users", "bob", "profile"))  # True
        >>> f.matches(("users", "alice", "settings"))  # False
        >>> f.matches(("users", "alice"))  # False (length mismatch)
    """

    pattern: key.Key
    """Pattern with wildcards. WILDCARD matches any single segment."""

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
class And(Filter):
    """Combine filters with AND logic. All must match.

    Short-circuits on first False for efficiency.

    Examples:
        >>> f = And(
        ...     filters=(
        ...         PrefixFilter(prefix=("users",)),
        ...         LengthFilter(length=3),
        ...     )
        ... )
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("users", "alice"))  # False (length mismatch)
    """

    filters: tuple[Filter, ...]
    """Filters to combine with AND logic."""

    def matches(self, key: key.Key) -> bool:
        """Check if key matches all filters. Short-circuits on first False."""
        return all(f.matches(key) for f in self.filters)

    def __hash__(self) -> int:
        """Return hash based on all filters."""
        return hash(("and", self.filters))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, And):
            return NotImplemented
        return self.filters == other.filters

    def __and__(self, other: Filter) -> And:
        """Flatten nested Ands: (a & b) & c -> And(a, b, c)."""
        if isinstance(other, And):
            return And(filters=self.filters + other.filters)
        return And(filters=(*self.filters, other))


@dataclass(frozen=True, slots=True)
class Or(Filter):
    """Combine filters with OR logic. Any must match.

    Short-circuits on first True for efficiency.

    Examples:
        >>> f = Or(
        ...     filters=(
        ...         PrefixFilter(prefix=("users",)),
        ...         PrefixFilter(prefix=("posts",)),
        ...     )
        ... )
        >>> f.matches(("users", "alice"))  # True
        >>> f.matches(("posts", "123"))  # True
        >>> f.matches(("comments",))  # False
    """

    filters: tuple[Filter, ...]
    """Filters to combine with OR logic."""

    def matches(self, key: key.Key) -> bool:
        """Check if key matches any filter. Short-circuits on first True."""
        return any(f.matches(key) for f in self.filters)

    def __hash__(self) -> int:
        """Return hash based on all filters."""
        return hash(("or", self.filters))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Or):
            return NotImplemented
        return self.filters == other.filters

    def __or__(self, other: Filter) -> Or:
        """Flatten nested Ors: (a | b) | c -> Or(a, b, c)."""
        if isinstance(other, Or):
            return Or(filters=self.filters + other.filters)
        return Or(filters=(*self.filters, other))


@dataclass(frozen=True, slots=True)
class PassAll(Filter):
    """Filter that always matches. Identity element for And.

    Examples:
        >>> f = PassAll()
        >>> f.matches(("any", "key"))  # True
        >>> f.matches(())  # True
    """

    def matches(self, key: key.Key) -> bool:
        """Always returns True."""
        return True

    def __hash__(self) -> int:
        """Return hash."""
        return hash(("passall",))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, PassAll):
            return NotImplemented
        return True


@dataclass(frozen=True, slots=True)
class PassNone(Filter):
    """Filter that never matches. Identity element for Or.

    Examples:
        >>> f = PassNone()
        >>> f.matches(("any", "key"))  # False
        >>> f.matches(())  # False
    """

    def matches(self, key: key.Key) -> bool:
        """Always returns False."""
        return False

    def __hash__(self) -> int:
        """Return hash."""
        return hash(("passnone",))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, PassNone):
            return NotImplemented
        return True
