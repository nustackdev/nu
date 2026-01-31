"""Set morphisms — operations (pure) + commands (impure).

Operations:
    UnionOp, IntersectionOp, DifferenceOp, SymmetricDifferenceOp
    IsSubsetOp, IsSupersetOp, IsDisjointOp

Commands:
    AddCmd: Add element to set
    RemoveCmd: Remove element (returns INVALID if missing)
    DiscardCmd: Remove element if present (no error)
"""

from __future__ import annotations

from collections.abc import MutableSet, Set

from everyabc import INVALID, BinaryCommand, BinaryOperation, Sentinel


__all__ = [
    "AddCmd",
    "DifferenceOp",
    "DiscardCmd",
    "IntersectionOp",
    "IsDisjointOp",
    "IsSubsetOp",
    "IsSupersetOp",
    "RemoveCmd",
    "SymmetricDifferenceOp",
    "UnionOp",
]


# =============================================================================
# OPERATIONS (pure)
# =============================================================================


class UnionOp[T](BinaryOperation[set[T] | frozenset[T]]):
    """Set union: left | right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left | right  # type: ignore


class IntersectionOp[T](BinaryOperation[set[T] | frozenset[T]]):
    """Set intersection: left & right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left & right  # type: ignore


class DifferenceOp[T](BinaryOperation[set[T] | frozenset[T]]):
    """Set difference: left - right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left - right  # type: ignore


class SymmetricDifferenceOp[T](BinaryOperation[set[T] | frozenset[T]]):
    """Set symmetric difference: left ^ right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left ^ right  # type: ignore


class IsSubsetOp(BinaryOperation[bool]):
    """Test if subset: left <= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left <= right


class IsSupersetOp(BinaryOperation[bool]):
    """Test if superset: left >= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left >= right


class IsDisjointOp(BinaryOperation[bool]):
    """Test if disjoint: left.isdisjoint(right)."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left.isdisjoint(right)


# =============================================================================
# COMMANDS (impure)
# =============================================================================


class AddCmd[T](BinaryCommand[set[T]]):
    """Add element to set: s.add(value). Returns mutated set."""

    def apply(self, operand: object, value: object) -> set[T] | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSet):
            raise TypeError(f"add() requires mutable set, got {type(operand).__name__}")
        operand.add(value)
        return set(operand)  # type: ignore[arg-type]


class RemoveCmd[T](BinaryCommand[set[T]]):
    """Remove element from set: s.remove(value). Returns INVALID if not found."""

    def apply(self, operand: object, value: object) -> set[T] | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSet):
            raise TypeError(f"remove() requires mutable set, got {type(operand).__name__}")
        try:
            operand.remove(value)
        except KeyError:
            return INVALID
        return set(operand)  # type: ignore[arg-type]


class DiscardCmd[T](BinaryCommand[set[T]]):
    """Discard element from set: s.discard(value). Returns mutated set (no error if absent)."""

    def apply(self, operand: object, value: object) -> set[T] | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSet):
            raise TypeError(f"discard() requires mutable set, got {type(operand).__name__}")
        operand.discard(value)
        return set(operand)  # type: ignore[arg-type]
