"""Collection aggregation operations.

SumOp: Sum of elements (sum(seq))
MinOp: Minimum element (min(seq))
MaxOp: Maximum element (max(seq))
AnyOp: Any truthy (any(seq))
AllOp: All truthy (all(seq))
"""

from __future__ import annotations

from everyshape.typing import NAN, Sentinel

from ..core import UnaryOp


__all__ = [
    "AllOp",
    "AnyOp",
    "MaxOp",
    "MinOp",
    "SumOp",
]


class SumOp[ResultT](UnaryOp[ResultT | Sentinel]):
    """Sum of sequence elements: sum(seq)."""

    def _apply_op(self, operand: object) -> ResultT | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"sum_() requires list or tuple, got {type(operand).__name__}")
        try:
            return sum(operand)  # type: ignore
        except TypeError:
            return NAN


class MinOp[ResultT](UnaryOp[ResultT | Sentinel]):
    """Minimum element: min(seq)."""

    def _apply_op(self, operand: object) -> ResultT | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"min_() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return NAN
        try:
            return min(operand)  # type: ignore
        except TypeError:
            return NAN


class MaxOp[ResultT](UnaryOp[ResultT | Sentinel]):
    """Maximum element: max(seq)."""

    def _apply_op(self, operand: object) -> ResultT | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"max_() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return NAN
        try:
            return max(operand)  # type: ignore
        except TypeError:
            return NAN


class AnyOp(UnaryOp[bool]):
    """Any truthy element: any(seq)."""

    def _apply_op(self, operand: object) -> bool:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"any_() requires list or tuple, got {type(operand).__name__}")
        return any(operand)


class AllOp(UnaryOp[bool]):
    """All truthy elements: all(seq)."""

    def _apply_op(self, operand: object) -> bool:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"all_() requires list or tuple, got {type(operand).__name__}")
        return all(operand)
