"""Set ops.

UnionOp, IntersectionOp, DifferenceOp, SymmetricDifferenceOp
IsSubsetOp, IsSupersetOp, IsDisjointOp
AddCmd, RemoveCmd, DiscardCmd
SetPopCmd, SetUpdateCmd
IntersectionUpdateCmd, DifferenceUpdateCmd, SymmetricDifferenceUpdateCmd
"""

from __future__ import annotations

from collections.abc import MutableSet, Set

from nu.terms import INVALID, BinaryOp, Sentinel, UnaryOp


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


class UnionOp[T](BinaryOp[set[T] | frozenset[T]]):
    """Set union: left | right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left | right  # type: ignore


class IntersectionOp[T](BinaryOp[set[T] | frozenset[T]]):
    """Set intersection: left & right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left & right  # type: ignore


class DifferenceOp[T](BinaryOp[set[T] | frozenset[T]]):
    """Set difference: left - right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left - right  # type: ignore


class SymmetricDifferenceOp[T](BinaryOp[set[T] | frozenset[T]]):
    """Set symmetric difference: left ^ right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left ^ right  # type: ignore


class IsSubsetOp(BinaryOp[bool]):
    """Test if subset: left <= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left <= right


class IsSupersetOp(BinaryOp[bool]):
    """Test if superset: left >= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left >= right


class IsDisjointOp(BinaryOp[bool]):
    """Test if disjoint: left.isdisjoint(right)."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left.isdisjoint(right)


# =============================================================================
# SET MUTATIONS
# =============================================================================


class AddCmd[T](BinaryOp[None]):
    """Add element to set: s.add(value). Returns None (mutates in-place)."""

    writes = 0

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(f"add() requires mutable set, got {type(left).__name__}")
        left.add(right)
        return None


class RemoveCmd[T](BinaryOp[None]):
    """Remove element from set: s.remove(value). Returns None, or INVALID if not found."""

    writes = 0

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(f"remove() requires mutable set, got {type(left).__name__}")
        try:
            left.remove(right)
        except KeyError:
            return INVALID
        return None


class DiscardCmd[T](BinaryOp[None]):
    """Discard element from set: s.discard(value). Returns None (mutates in-place)."""

    writes = 0

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(f"discard() requires mutable set, got {type(left).__name__}")
        left.discard(right)
        return None


class SetPopCmd[T](UnaryOp[T]):
    """Pop arbitrary element: s.pop(). Returns element, or INVALID if empty."""

    writes = 0

    def apply(self, operand: object) -> T | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSet):
            raise TypeError(f"pop() requires mutable set, got {type(operand).__name__}")
        try:
            return operand.pop()  # type: ignore[return-value]
        except KeyError:
            return INVALID


class SetUpdateCmd[T](BinaryOp[None]):
    """Update set with elements from other: s.update(other). Returns None."""

    writes = 0

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(f"update() requires mutable set, got {type(left).__name__}")
        if not isinstance(right, Set):
            return INVALID
        left |= right
        return None


class IntersectionUpdateCmd[T](BinaryOp[None]):
    """Keep only elements found in both: s.intersection_update(other). Returns None."""

    writes = 0

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


class DifferenceUpdateCmd[T](BinaryOp[None]):
    """Remove elements found in other: s.difference_update(other). Returns None."""

    writes = 0

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSet):
            raise TypeError(f"difference_update() requires mutable set, got {type(left).__name__}")
        if not isinstance(right, Set):
            return INVALID
        left -= right
        return None


class SymmetricDifferenceUpdateCmd[T](BinaryOp[None]):
    """Keep elements in either but not both: s.symmetric_difference_update(other). Returns None."""

    writes = 0

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
