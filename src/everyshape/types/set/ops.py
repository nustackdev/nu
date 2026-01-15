"""Set operations for Term expressions.

This module provides type-safe operations on set Terms:

Set operations: UnionOp, IntersectionOp, DifferenceOp, SymmetricDifferenceOp
Set tests: IsSubsetOp, IsSupersetOp, IsDisjointOp

Design principles:
1. Atomic classes: one operation = one class
2. Runtime type checking: validate input is set at execution
3. Special value propagation: Empty/NaN flow through operations
4. Type safety: preserve return types
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.term.term import Operation
from everyshape.typing import NAN, Sentinel


if TYPE_CHECKING:
    from everyshape.term.context import Context
    from everyshape.term.term import Term

    from ..bases import UnionBaseType


__all__ = [
    "DifferenceOp",
    "IntersectionOp",
    "IsDisjointOp",
    "IsSubsetOp",
    "IsSupersetOp",
    "SymmetricDifferenceOp",
    "UnionOp",
]


type OpArgument = Term | UnionBaseType


class SetBinaryOp[ResultT](Operation[ResultT]):
    """Base class for binary set operations."""

    def __init__(self, operand: OpArgument, other: OpArgument) -> None:
        """Init."""
        self.children = (cast("Term", operand), cast("Term", other))

    def execute(self, context: Context) -> ResultT:
        """Execute."""
        operand_val = self.children[0].execute(context)
        other_val = self.children[1].execute(context)
        return self._apply_op(operand_val, other_val)

    def _apply_op(self, operand: object, other: object) -> ResultT:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.children[0]!r}, {self.children[1]!r})"


# Set operations
class UnionOp[T](SetBinaryOp[set[T] | frozenset[T] | Sentinel]):
    """Set union: set.union(other) or set | other."""

    def _apply_op(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return NAN
            return operand.union(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return NAN
            return operand.union(other)  # type: ignore
        return NAN


class IntersectionOp[T](SetBinaryOp[set[T] | frozenset[T] | Sentinel]):
    """Set intersection: set.intersection(other) or set & other."""

    def _apply_op(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return NAN
            return operand.intersection(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return NAN
            return operand.intersection(other)  # type: ignore
        return NAN


class DifferenceOp[T](SetBinaryOp[set[T] | frozenset[T] | Sentinel]):
    """Set difference: set.difference(other) or set - other."""

    def _apply_op(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return NAN
            return operand.difference(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return NAN
            return operand.difference(other)  # type: ignore
        return NAN


class SymmetricDifferenceOp[T](SetBinaryOp[set[T] | frozenset[T] | Sentinel]):
    """Set symmetric difference: set.symmetric_difference(other) or set ^ other."""

    def _apply_op(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return NAN
            return operand.symmetric_difference(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return NAN
            return operand.symmetric_difference(other)  # type: ignore
        return NAN


# Set tests
class IsSubsetOp(SetBinaryOp[bool | Sentinel]):
    """Test if subset: set.issubset(other) or set <= other."""

    def _apply_op(self, operand: object, other: object) -> bool | Sentinel:
        if not isinstance(operand, (set, frozenset)):
            return NAN
        if not isinstance(other, (set, frozenset)):
            return NAN
        return operand.issubset(other)


class IsSupersetOp(SetBinaryOp[bool | Sentinel]):
    """Test if superset: set.issuperset(other) or set >= other."""

    def _apply_op(self, operand: object, other: object) -> bool | Sentinel:
        if not isinstance(operand, (set, frozenset)):
            return NAN
        if not isinstance(other, (set, frozenset)):
            return NAN
        return operand.issuperset(other)


class IsDisjointOp(SetBinaryOp[bool | Sentinel]):
    """Test if disjoint: set.isdisjoint(other)."""

    def _apply_op(self, operand: object, other: object) -> bool | Sentinel:
        if not isinstance(operand, (set, frozenset)):
            return NAN
        if not isinstance(other, (set, frozenset)):
            return NAN
        return operand.isdisjoint(other)
