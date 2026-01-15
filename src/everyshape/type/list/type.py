"""List type for Term expressions.

This module provides ListType which represents list expressions (literal or computed).
Supports indexing, slicing, length, and functional operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, overload

from everyshape.term.type import ComparisonBase, SequenceBase, Type


if TYPE_CHECKING:
    from everyshape.term.term import Term

    from ..any.type import AnyType
    from ..bool.type import BoolType


__all__ = [
    "ListType",
]


class ListType[T](
    SequenceBase[T, "ListType[T]"],
    ComparisonBase[list[T]],
    Type[list[T]],
):
    """List type - represents list expressions (literal or computed).

    Supports indexing, slicing, length, and functional operations.

    Example:
        >>> x = ListType([1, 2, 3])
        >>> y = x[0]  # Returns AnyType
        >>> z = x.len_()  # Returns IntType
    """

    VALUE_TYPE: ClassVar[type] = list

    def _wrap_comparison_result(self, operand: Term) -> BoolType:
        from ..bool.type import BoolType

        return BoolType(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListType:
        return ListType(operand)

    def _wrap_sliceable_result(self, operand: Term) -> ListType:
        return ListType(operand)

    def _wrap_element_result(self, operand: Term) -> Term:
        from ..any.type import AnyType

        return AnyType(operand)

    def __add__(self, other: list[T] | ListType[T]) -> ListType[T]:
        from everyshape.term.comp import AddOp
        from everyshape.term.conversion import literal

        return ListType(AddOp(self, literal(other)))

    def __radd__(self, other: list[T]) -> ListType[T]:
        from everyshape.term.comp import AddOp
        from everyshape.term.conversion import literal

        return ListType(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> AnyType: ...
    @overload
    def __getitem__(self, key: slice) -> ListType[T]: ...
    def __getitem__(self, key: int | slice) -> AnyType | ListType[T]:
        from everyshape.term.comp import AtOp, SliceOp
        from everyshape.term.conversion import literal

        from ..any.type import AnyType

        if isinstance(key, slice):
            return ListType(SliceOp(self, key.start, key.stop, key.step))
        return AnyType(AtOp(self, literal(key)))
