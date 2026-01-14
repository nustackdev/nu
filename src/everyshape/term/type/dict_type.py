"""Dictionary type for Term expressions.

This module provides DictType which represents dict expressions (literal or computed).
Supports key access, keys/values/items operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from .base_collections import MappingBase
from .base_comparison import ComparisonBase
from .type import Type


if TYPE_CHECKING:
    from ..term import Term
    from .any_type import AnyType
    from .bool_type import BoolType


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
        from .bool_type import BoolType

        return BoolType(operand)

    def __getitem__(self, key: K) -> AnyType:
        from ..comps.typed.sequence import AtOp
        from ..conversion import literal
        from .any_type import AnyType

        return AnyType(AtOp(self, literal(key)))
