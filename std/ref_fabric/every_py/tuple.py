"""Tuple type for Term expressions.

This module provides TupleType which represents tuple expressions (literal or computed).
Supports indexing, length, and containment operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, overload

from .bases import BaseType, ComparisonBase, SequenceBase


if TYPE_CHECKING:
    from every._abc import Term

    from .any import AnyType
    from .bool import BoolType
    from .list import ListType  # noqa: F401


__all__ = [
    "TupleType",
]


class TupleType[*Ts](
    SequenceBase[object, "ListType[object]"],
    ComparisonBase[tuple],
    BaseType[tuple[*Ts]],
):
    """Tuple type - represents tuple expressions (literal or computed).

    Supports indexing, length, and containment operations.

    Example:
        >>> x = TupleType((1, "hello", 3.14))
        >>> y = x[0]  # Returns AnyType
        >>> z = x.len_()  # Returns IntType
    """

    VALUE_TYPE: ClassVar[type] = tuple

    def _wrap_comparison_result(self, operand: Term) -> BoolType:
        from .bool import BoolType

        return BoolType(operand)

    def _wrap_sliceable_result(self, operand: Term) -> TupleType:
        return TupleType(operand)

    def _wrap_iterable_result(self, operand: Term) -> Term:
        from .list import ListType

        return ListType(operand)

    def _wrap_element_result(self, operand: Term) -> Term:
        from .any import AnyType

        return AnyType(operand)

    @overload
    def __getitem__(self, key: int) -> AnyType: ...
    @overload
    def __getitem__(self, key: slice) -> TupleType: ...
    def __getitem__(self, key: int | slice) -> AnyType | TupleType:
        from term.ops import AtOp, SliceOp

        from .any import AnyType

        if isinstance(key, slice):
            return TupleType(SliceOp(self, key.start, key.stop, key.step))
        return AnyType(AtOp(self, key))
