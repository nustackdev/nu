"""Collection aggregation morphisms.

SumOp: Sum of elements (sum(seq))
MinOp: Minimum element (min(seq))
MaxOp: Maximum element (max(seq))
AnyOp: Any truthy (any(seq))
AllOp: All truthy (all(seq))
"""

from __future__ import annotations

from every import INVALID, Operation, Sentinel, UnaryMorphism


__all__ = [
    "AllOp",
    "AnyOp",
    "MaxOp",
    "MinOp",
    "SumOp",
]


class SumOp[ResultT](Operation, UnaryMorphism[ResultT | Sentinel]):
    """Sum of sequence elements: sum(seq)."""

    def _apply(self, operand: object) -> ResultT | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"sum_() requires list or tuple, got {type(operand).__name__}")
        try:
            return sum(operand)  # type: ignore
        except TypeError:
            return INVALID


class MinOp[ResultT](Operation, UnaryMorphism[ResultT | Sentinel]):
    """Minimum element: min(seq)."""

    def _apply(self, operand: object) -> ResultT | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"min_() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        try:
            return min(operand)  # type: ignore
        except TypeError:
            return INVALID


class MaxOp[ResultT](Operation, UnaryMorphism[ResultT | Sentinel]):
    """Maximum element: max(seq)."""

    def _apply(self, operand: object) -> ResultT | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"max_() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        try:
            return max(operand)  # type: ignore
        except TypeError:
            return INVALID


class AnyOp(Operation, UnaryMorphism[bool]):
    """Any truthy element: any(seq)."""

    def _apply(self, operand: object) -> bool:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"any_() requires list or tuple, got {type(operand).__name__}")
        return any(operand)


class AllOp(Operation, UnaryMorphism[bool]):
    """All truthy elements: all(seq)."""

    def _apply(self, operand: object) -> bool:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"all_() requires list or tuple, got {type(operand).__name__}")
        return all(operand)
