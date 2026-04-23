"""Comparison ops.

Binary: Eq, Ne, Gt, Lt, Ge, Le, IdComp
"""

from __future__ import annotations

from typing import ClassVar

from nu.terms import BinaryScalar, Mode


__all__ = [
    "Eq",
    "Ge",
    "Gt",
    "IdComp",
    "Le",
    "Lt",
    "Ne",
]


class Gt(BinaryScalar[bool]):
    """Greater than: left > right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left > right  # type: ignore


class Lt(BinaryScalar[bool]):
    """Less than: left < right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left < right  # type: ignore


class Eq(BinaryScalar[bool]):
    """Equality: left == right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left == right  # type: ignore


class Ne(BinaryScalar[bool]):
    """Not equal: left != right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left != right  # type: ignore


class Ge(BinaryScalar[bool]):
    """Greater than or equal: left >= right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left >= right  # type: ignore


class Le(BinaryScalar[bool]):
    """Less than or equal: left <= right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left <= right  # type: ignore


class IdComp(BinaryScalar[bool]):
    """Identity comparison: left is right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left is right
