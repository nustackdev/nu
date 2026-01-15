"""Dictionary type for Term expressions.

This module provides DictType which represents dict expressions (literal or computed).
Supports key access, keys/values/items operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from everyshape.term.type import ComparisonBase, MappingBase, Type


if TYPE_CHECKING:
    from everyshape.term.term import Term

    from ..any.type import AnyType
    from ..bool.type import BoolType


__all__ = [
    "DictType",
]


class DictType[K, V](
    MappingBase[K, V, "DictType[K, V]"],
    ComparisonBase[dict[K, V]],
    Type[dict[K, V]],
):
    """Dict type - represents dict expressions (literal or computed).

    Supports key access, keys/values/items operations.

    Example:
        >>> x = DictType({"a": 1, "b": 2})
        >>> y = x["a"]  # Returns AnyType
        >>> z = x.keys_()  # Returns ListType[K]
    """

    VALUE_TYPE: ClassVar[type] = dict

    def _wrap_comparison_result(self, operand: Term) -> BoolType:
        from ..bool.type import BoolType

        return BoolType(operand)

    def __getitem__(self, key: K) -> AnyType:
        from everyshape.term.comp import AtOp
        from everyshape.term.conversion import literal

        from ..any.type import AnyType

        return AnyType(AtOp(self, literal(key)))
