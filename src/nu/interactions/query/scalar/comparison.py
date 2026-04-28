"""Comparison ops.

Binary: Eq, Ne, Gt, Lt, Ge, Le, IdComp
"""

from __future__ import annotations

from typing import ClassVar

from nu.terms import BinaryQuery, Mode


__all__ = [
    "Eq",
    "Ge",
    "Gt",
    "IdComp",
    "Le",
    "Lt",
    "Ne",
]


class Gt(BinaryQuery[bool]):
    """Greater than: left > right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left > right  # type: ignore


class Lt(BinaryQuery[bool]):
    """Less than: left < right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left < right  # type: ignore


class Eq(BinaryQuery[bool]):
    """Equality: left == right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left == right  # type: ignore


class Ne(BinaryQuery[bool]):
    """Not equal: left != right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left != right  # type: ignore


class Ge(BinaryQuery[bool]):
    """Greater than or equal: left >= right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left >= right  # type: ignore


class Le(BinaryQuery[bool]):
    """Less than or equal: left <= right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left <= right  # type: ignore


class IdComp(BinaryQuery[bool]):
    """Identity comparison: left is right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left is right
