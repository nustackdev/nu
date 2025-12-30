"""Literal RValue implementations.

This module provides literal value wrappers for Python primitives and collections.
These wrap fixed, known values that are available at definition time.

Literal Values (this module):
- IntLiteral, FloatLiteral, BoolLiteral, StrLiteral, BytesLiteral, NoneLiteral
- ListLiteral, DictLiteral, TupleLiteral, SetLiteral, FrozenSetLiteral

Computed Values (primitive_values.py, collection_values.py):
- IntValue, FloatValue, BoolValue, StrValue, etc.
- Wrap Operations/RValues that compute results

Literals inherit from bases to get operator support. Operations on literals
produce ComputedValue results (since the result of an operation is computed).

Usage:
    >>> from everyshape.shape.values.literals import IntLiteral
    >>> lit = IntLiteral(42)  # Fixed value
    >>> lit.execute(ctx)  # Returns 42
    >>> doubled = lit * 2  # Returns IntValue (computed result)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ..term import LiteralValue
from .bases import (
    BitwiseBase,
    BytesMethodsBase,
    ComparisonBase,
    ContainableBase,
    CoreBase,
    LengthableBase,
    LogicalBase,
    MappingBase,
    NumericBase,
    SequenceBase,
    SetBase,
    SliceableBase,
    StringBase,
)


if TYPE_CHECKING:
    from ..term import RValue
    from .primitive_values import NoneValue  # noqa: F401


__all__ = [  # noqa: RUF022
    # Primitive literals
    "IntLiteral",
    "FloatLiteral",
    "BoolLiteral",
    "StrLiteral",
    "BytesLiteral",
    "NoneLiteral",
    # Collection literals
    "ListLiteral",
    "DictLiteral",
    "TupleLiteral",
    "SetLiteral",
    "FrozenSetLiteral",
]


# =============================================================================
# PRIMITIVE LITERALS
# =============================================================================


class IntLiteral(
    NumericBase[
        "int | float | FloatLiteral | IntLiteral | FloatValue | IntValue",
        "FloatValue | IntValue",
    ],
    ComparisonBase["int | float | FloatLiteral | IntLiteral | FloatValue | IntValue"],
    LogicalBase["bool | int | BoolLiteral | IntLiteral | BoolValue | IntValue", "BoolValue"],
    BitwiseBase["int | IntLiteral | IntValue", "IntValue"],
    CoreBase,
    LiteralValue[int],
):
    """Literal integer value.

    Supports arithmetic, comparison, logical, and bitwise operations.
    Operations return computed value types.

    Example:
        >>> lit = IntLiteral(42)
        >>> doubled = lit * 2  # Returns IntValue
        >>> is_positive = lit > 0  # Returns BoolValue
    """

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return IntValue(operand)

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        return IntValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


class FloatLiteral(
    NumericBase[
        "int | float | FloatLiteral | IntLiteral | FloatValue | IntValue",
        "FloatValue",
    ],
    ComparisonBase["int | float | FloatLiteral | IntLiteral | FloatValue | IntValue"],
    LogicalBase["bool | float | BoolLiteral | FloatLiteral | BoolValue | FloatValue", "BoolValue"],
    CoreBase,
    LiteralValue[float],
):
    """Literal float value.

    Supports arithmetic, comparison, and logical operations.
    Does not support bitwise operations.

    Example:
        >>> lit = FloatLiteral(3.14)
        >>> doubled = lit * 2  # Returns FloatValue
        >>> is_positive = lit > 0  # Returns BoolValue
    """

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return FloatValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


class BoolLiteral(
    LogicalBase["bool | BoolLiteral | BoolValue", "BoolValue"],
    ComparisonBase["bool | BoolLiteral | BoolValue"],
    CoreBase,
    LiteralValue[bool],
):
    """Literal boolean value.

    Supports logical operations.

    Example:
        >>> lit = BoolLiteral(True)
        >>> negated = lit.not_()  # Returns BoolValue
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


class StrLiteral(
    StringBase["StrValue"],
    ComparisonBase["str | StrLiteral | StrValue"],
    LogicalBase["str | StrLiteral | StrValue", "BoolValue"],
    CoreBase,
    LiteralValue[str],
):
    """Literal string value.

    Supports concatenation, string operations, comparison, and logical operations.

    Example:
        >>> lit = StrLiteral("hello")
        >>> upper = lit.upper()  # Returns StrValue
        >>> greeting = lit + " world"  # Returns StrValue
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_string_result(self, operand: RValue) -> RValue:
        return StrValue(operand)

    def _wrap_sliceable_result(self, operand: RValue) -> RValue:
        return StrValue(operand)

    def __add__(self, other: str | StrLiteral | StrValue) -> StrValue:
        """Concatenate strings."""
        from ..computations.binary_ops import AddOp
        from .conversion import literal

        return StrValue(AddOp(self, literal(other)))

    def __radd__(self, other: str) -> StrValue:
        """Right concatenate strings."""
        from ..computations.binary_ops import AddOp
        from .conversion import literal

        return StrValue(AddOp(literal(other), self))


class BytesLiteral(
    BytesMethodsBase["BytesValue"],
    LengthableBase,
    SliceableBase["BytesValue"],
    ContainableBase["int | bytes"],
    ComparisonBase["bytes | BytesLiteral | BytesValue"],
    LogicalBase["bytes | BytesLiteral | BytesValue", "BoolValue"],
    CoreBase,
    LiteralValue[bytes],
):
    """Literal bytes value.

    Supports concatenation, bytes operations, comparison, and logical operations.

    Example:
        >>> lit = BytesLiteral(b"hello")
        >>> decoded = lit.decode()  # Returns StrValue
        >>> combined = lit + b" world"  # Returns BytesValue
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_bytes_result(self, operand: RValue) -> RValue:
        return BytesValue(operand)

    def _wrap_sliceable_result(self, operand: RValue) -> RValue:
        return BytesValue(operand)

    def __add__(self, other: bytes | BytesLiteral | BytesValue) -> BytesValue:
        """Concatenate bytes."""
        from ..computations.binary_ops import AddOp
        from .conversion import literal

        return BytesValue(AddOp(self, literal(other)))

    def __radd__(self, other: bytes) -> BytesValue:
        """Right concatenate bytes."""
        from ..computations.binary_ops import AddOp
        from .conversion import literal

        return BytesValue(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> IntValue: ...

    @overload
    def __getitem__(self, key: slice) -> BytesValue: ...

    def __getitem__(self, key: int | slice) -> BytesValue | IntValue:
        """Get byte or slice."""
        from .conversion import literal

        if isinstance(key, slice):
            from ..computations.sequence_ops import SliceOp

            return BytesValue(SliceOp[bytes](self, key.start, key.stop, key.step))

        from ..computations.sequence_ops import AtOp

        return IntValue(AtOp[int](self, literal(key)))


class NoneLiteral(
    LogicalBase["None | NoneLiteral | NoneValue", "BoolValue"],
    CoreBase,
    LiteralValue[None],
):
    """Literal None value.

    Example:
        >>> lit = NoneLiteral()
        >>> is_none = lit.eq(None)  # Returns BoolValue
    """

    def __init__(self) -> None:
        """Initialize None literal."""
        super().__init__(None)

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# COLLECTION LITERALS
# =============================================================================


class ListLiteral[T](
    SequenceBase[T, "ListValue[T]"],
    ComparisonBase[list[T]],
    CoreBase,
    LiteralValue[list[T]],
):
    """Literal list value.

    Supports indexing, slicing, length, and functional operations.

    Example:
        >>> lit = ListLiteral([1, 2, 3])
        >>> first = lit[0]  # Returns UnknownValue
        >>> length = lit.len_()  # Returns IntValue
    """

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def __add__(self, other: list[T] | ListLiteral[T] | ListValue[T]) -> ListValue[T]:
        """Concatenate lists."""
        from ..computations.binary_ops import AddOp
        from .conversion import literal

        return ListValue(AddOp(self, literal(other)))

    def __radd__(self, other: list[T]) -> ListValue[T]:
        """Right concatenate lists."""
        from ..computations.binary_ops import AddOp
        from .conversion import literal

        return ListValue(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> UnknownValue: ...

    @overload
    def __getitem__(self, key: slice) -> ListValue[T]: ...

    def __getitem__(self, key: int | slice) -> UnknownValue | ListValue[T]:
        """Get item or slice."""
        from .conversion import literal

        if isinstance(key, slice):
            from ..computations.sequence_ops import SliceOp

            return ListValue(SliceOp(self, key.start, key.stop, key.step))

        from ..computations.sequence_ops import AtOp

        return UnknownValue(AtOp(self, literal(key)))

    def len_(self) -> IntValue:
        """Get list length."""
        from ..computations.sequence_ops import LenOp

        return IntValue(LenOp(self))

    def contains(self, item: T) -> BoolValue:
        """Check if item is in list."""
        from ..computations.mapping_ops import ContainsOp
        from .conversion import literal

        return BoolValue(ContainsOp(self, literal(item)))

    def reversed_(self) -> ListValue[T]:
        """Get reversed list."""
        from ..computations.sequence_ops import ReversedOp

        return ListValue(ReversedOp(self))

    def sorted_(self, reverse: bool = False) -> ListValue[T]:
        """Get sorted list."""
        from ..computations.sequence_ops import SortedOp

        return ListValue(SortedOp(self, reverse=reverse))

    def first(self) -> UnknownValue:
        """Get first element."""
        from ..computations.sequence_ops import FirstOp

        return UnknownValue(FirstOp(self))

    def last(self) -> UnknownValue:
        """Get last element."""
        from ..computations.sequence_ops import LastOp

        return UnknownValue(LastOp(self))

    def any_(self) -> BoolValue:
        """Check if any truthy."""
        from ..computations.sequence_ops import AnyOp

        return BoolValue(AnyOp(self))

    def all_(self) -> BoolValue:
        """Check if all truthy."""
        from ..computations.sequence_ops import AllOp

        return BoolValue(AllOp(self))

    def join(self, separator: str) -> StrValue:
        """Join string elements."""
        from ..computations.sequence_ops import JoinOp

        return StrValue(JoinOp(self, separator))


class DictLiteral[K, V](
    MappingBase[K, V, "DictValue[K, V]"],
    ComparisonBase[dict[K, V]],
    CoreBase,
    LiteralValue[dict[K, V]],
):
    """Literal dict value.

    Supports key access, keys/values/items operations.

    Example:
        >>> lit = DictLiteral({"a": 1, "b": 2})
        >>> a_val = lit["a"]  # Returns UnknownValue
        >>> all_keys = lit.keys_()  # Returns ListValue[K]
    """

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_value_result(self, operand: RValue) -> UnknownValue:
        return UnknownValue(operand)

    def __getitem__(self, key: K) -> UnknownValue:
        """Get value for key."""
        from ..computations.sequence_ops import AtOp
        from .conversion import literal

        return UnknownValue(AtOp(self, literal(key)))

    def len_(self) -> IntValue:
        """Get number of items."""
        from ..computations.sequence_ops import LenOp

        return IntValue(LenOp(self))

    def contains(self, key: K) -> BoolValue:
        """Check if key exists."""
        from ..computations.mapping_ops import ContainsOp
        from .conversion import literal

        return BoolValue(ContainsOp(self, literal(key)))

    def keys_(self) -> ListValue[K]:
        """Get all keys."""
        from ..computations.mapping_ops import DictKeysOp

        return ListValue(DictKeysOp(self))

    def values_(self) -> ListValue[V]:
        """Get all values."""
        from ..computations.mapping_ops import DictValuesOp

        return ListValue(DictValuesOp(self))

    def items_(self) -> ListValue[tuple[K, V]]:
        """Get all key-value pairs."""
        from ..computations.mapping_ops import DictItemsOp

        return ListValue(DictItemsOp(self))

    def get_(self, key: K, default: V | None = None) -> UnknownValue:
        """Get value with default."""
        from ..computations.mapping_ops import DictGetOp
        from .conversion import literal

        return UnknownValue(DictGetOp(self, literal(key), literal(default)))


class TupleLiteral[*Ts](
    LengthableBase,
    SliceableBase["TupleValue"],
    ComparisonBase[tuple],
    CoreBase,
    LiteralValue[tuple[*Ts]],
):
    """Literal tuple value.

    Supports indexing, length, and containment operations.

    Example:
        >>> lit = TupleLiteral((1, "hello", 3.14))
        >>> first = lit[0]  # Returns UnknownValue
        >>> length = lit.len_()  # Returns IntValue
    """

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_sliceable_result(self, operand: RValue) -> TupleValue:
        return TupleValue(operand)

    @overload
    def __getitem__(self, key: int) -> UnknownValue: ...

    @overload
    def __getitem__(self, key: slice) -> TupleValue: ...

    def __getitem__(self, key: int | slice) -> UnknownValue | TupleValue:
        """Get item or slice."""
        from .conversion import literal

        if isinstance(key, slice):
            from ..computations.sequence_ops import SliceOp

            return TupleValue(SliceOp(self, key.start, key.stop, key.step))

        from ..computations.sequence_ops import AtOp

        return UnknownValue(AtOp(self, literal(key)))

    def contains(self, item: object) -> BoolValue:
        """Check if item is in tuple."""
        from ..computations.mapping_ops import ContainsOp
        from .conversion import literal

        return BoolValue(ContainsOp(self, literal(item)))

    def first(self) -> UnknownValue:
        """Get first element."""
        from ..computations.sequence_ops import FirstOp

        return UnknownValue(FirstOp(self))

    def last(self) -> UnknownValue:
        """Get last element."""
        from ..computations.sequence_ops import LastOp

        return UnknownValue(LastOp(self))


class SetLiteral[T](
    SetBase[T, "SetValue[T]"],
    ComparisonBase[set[T]],
    CoreBase,
    LiteralValue[set[T]],
):
    """Literal set value.

    Supports containment testing, length, and set operations.

    Example:
        >>> lit = SetLiteral({1, 2, 3})
        >>> exists = lit.contains(2)  # Returns BoolValue
        >>> union = lit.union({4, 5})  # Returns SetValue
    """

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_set_result(self, operand: RValue) -> SetValue[T]:
        return SetValue(operand)


class FrozenSetLiteral[T](
    SetBase[T, "FrozenSetValue[T]"],
    ComparisonBase[frozenset[T]],
    CoreBase,
    LiteralValue[frozenset[T]],
):
    """Literal frozenset value.

    Supports containment testing, length, and set operations.

    Example:
        >>> lit = FrozenSetLiteral(frozenset({1, 2, 3}))
        >>> exists = lit.contains(2)  # Returns BoolValue
        >>> union = lit.union(frozenset({4, 5}))  # Returns FrozenSetValue
    """

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_set_result(self, operand: RValue) -> FrozenSetValue[T]:
        return FrozenSetValue(operand)


# Import computed value types at the end to avoid circular imports
from .collection_values import (  # noqa: E402
    FrozenSetValue,
    ListValue,
    SetValue,
    TupleValue,
)
from .primitive_values import (  # noqa: E402
    BoolValue,
    BytesValue,
    FloatValue,
    IntValue,
    StrValue,
    UnknownValue,
)
