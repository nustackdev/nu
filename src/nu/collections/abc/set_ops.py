"""Set ops.

UnionOp, IntersectionOp, DifferenceOp, SymmetricDifferenceOp
IsSubsetOp, IsSupersetOp, IsDisjointOp
AddCmd, RemoveCmd, DiscardCmd
SetPopCmd, SetUpdateCmd
IntersectionUpdateCmd, DifferenceUpdateCmd, SymmetricDifferenceUpdateCmd
"""

from __future__ import annotations

from collections.abc import MutableSet, Set
from typing import ClassVar

from nu.terms import INVALID, BinaryScalar, Mode, Sentinel, UnaryScalar


__all__ = [
    "AddCmd",
    "DifferenceOp",
    "DifferenceUpdateCmd",
    "DiscardCmd",
    "IntersectionOp",
    "IntersectionUpdateCmd",
    "IsDisjointOp",
    "IsSubsetOp",
    "IsSupersetOp",
    "RemoveCmd",
    "SetPopCmd",
    "SetUpdateCmd",
    "SymmetricDifferenceOp",
    "SymmetricDifferenceUpdateCmd",
    "UnionOp",
]


# =============================================================================
# SET OPERATIONS
# =============================================================================


class UnionOp[T](BinaryScalar[set[T] | frozenset[T]]):
    """Set union: left | right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left | right  # type: ignore


class IntersectionOp[T](BinaryScalar[set[T] | frozenset[T]]):
    """Set intersection: left & right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left & right  # type: ignore


class DifferenceOp[T](BinaryScalar[set[T] | frozenset[T]]):
    """Set difference: left - right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left - right  # type: ignore


class SymmetricDifferenceOp[T](BinaryScalar[set[T] | frozenset[T]]):
    """Set symmetric difference: left ^ right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left ^ right  # type: ignore


class IsSubsetOp(BinaryScalar[bool]):
    """Test if subset: left <= right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left <= right


class IsSupersetOp(BinaryScalar[bool]):
    """Test if superset: left >= right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left >= right


class IsDisjointOp(BinaryScalar[bool]):
    """Test if disjoint: left.isdisjoint(right)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left.isdisjoint(right)


# =============================================================================
# SET MUTATIONS
# =============================================================================


class AddCmd[T](BinaryScalar[None]):
    """Add element to set: s.add(value). Returns None (mutates in-place)."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(f"add() requires mutable set, got {type(left).__name__}")
        left.add(right)
        return None


class RemoveCmd[T](BinaryScalar[None]):
    """Remove element from set: s.remove(value). Returns None, or INVALID if not found."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(f"remove() requires mutable set, got {type(left).__name__}")
        try:
            left.remove(right)
        except KeyError:
            return INVALID
        return None


class DiscardCmd[T](BinaryScalar[None]):
    """Discard element from set: s.discard(value). Returns None (mutates in-place)."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(f"discard() requires mutable set, got {type(left).__name__}")
        left.discard(right)
        return None


class SetPopCmd[T](UnaryScalar[T]):
    """Pop arbitrary element: s.pop(). Returns element, or INVALID if empty."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> T | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSet):
            raise TypeError(f"pop() requires mutable set, got {type(operand).__name__}")
        try:
            return operand.pop()  # type: ignore[return-value]
        except KeyError:
            return INVALID


class SetUpdateCmd[T](BinaryScalar[None]):
    """Update set with elements from other: s.update(other). Returns None."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(f"update() requires mutable set, got {type(left).__name__}")
        if not isinstance(right, Set):
            return INVALID
        left |= right
        return None


class IntersectionUpdateCmd[T](BinaryScalar[None]):
    """Keep only elements found in both: s.intersection_update(other). Returns None."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(
                f"intersection_update() requires mutable set, got {type(left).__name__}"
            )
        if not isinstance(right, Set):
            return INVALID
        left &= right
        return None


class DifferenceUpdateCmd[T](BinaryScalar[None]):
    """Remove elements found in other: s.difference_update(other). Returns None."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(f"difference_update() requires mutable set, got {type(left).__name__}")
        if not isinstance(right, Set):
            return INVALID
        left -= right
        return None


class SymmetricDifferenceUpdateCmd[T](BinaryScalar[None]):
    """Keep elements in either but not both: s.symmetric_difference_update(other). Returns None."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(
                f"symmetric_difference_update() requires mutable set, got {type(left).__name__}"
            )
        if not isinstance(right, Set):
            return INVALID
        left ^= right
        return None
