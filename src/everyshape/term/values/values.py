"""RValue implementations.

This module provides concrete RValue types for:

1. Python primitives:
- IntValue: Integer values
- FloatValue: Floating-point values
- BoolValue: Boolean values
- StrValue: String values
- BytesValue: Bytes values
- NoneValue: None value

2. Special value types:
- UnknownValue: Value of unknown type (can be any type)
- EmptyValue: Represents absence of a value
- NaNValue: Represents not-a-number

3. Collections:
- ListValue: List values
- DictValue: Dictionary values
- TupleValue: Tuple values
- SetValue: Set values
- FrozenSetValue: Frozenset values

These wrap native Python values and enable DSL operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, overload

from everyshape.types import SpecialValue

from ..term import ComputedValue
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
from .conversion import literal


if TYPE_CHECKING:
    from ..term import RValue


__all__ = [
    "BoolValue",
    "BytesValue",
    "DictValue",
    "EmptyValue",
    "FloatValue",
    "FrozenSetValue",
    "IntValue",
    "ListValue",
    "NaNValue",
    "NoneValue",
    "SetValue",
    "StrValue",
    "TupleValue",
    "UnknownValue",
]


# =============================================================================
# INTEGER VALUE
# =============================================================================


class IntValue(
    NumericBase[
        "int | float | FloatValue | IntValue",
        "FloatValue | IntValue",
    ],
    ComparisonBase["int | float | FloatValue | IntValue"],
    LogicalBase["bool | int | BoolValue | IntValue", "BoolValue"],
    BitwiseBase[
        "int | IntValue",
        "IntValue",
    ],
    CoreBase,
    ComputedValue[int | SpecialValue],
):
    """RValue representing an integer.

    Supports full arithmetic, comparison, logical, and bitwise operations.
    Operations return appropriate RValue types.

    Example:
        >>> val = IntValue(42)
        >>> doubled = val * 2  # Returns IntValue
        >>> is_positive = val > 0  # Returns BoolValue
        >>> masked = val.bitand(0xFF)  # Returns IntValue
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


# =============================================================================
# FLOAT VALUE
# =============================================================================


class FloatValue(
    NumericBase[
        "int | float | FloatValue | IntValue",
        "FloatValue",
    ],
    ComparisonBase["int | float | FloatValue | IntValue"],
    LogicalBase["bool | float | BoolValue | FloatValue", "BoolValue"],
    CoreBase,
    ComputedValue[float | SpecialValue],
):
    """RValue representing a floating-point number.

    Supports full arithmetic, comparison, and logical operations.
    Does not support bitwise operations.

    Example:
        >>> val = FloatValue(3.14)
        >>> doubled = val * 2  # Returns FloatValue
        >>> is_positive = val > 0  # Returns BoolValue
        >>> safe = val.or_default(0.0)  # Returns FloatValue if not NaN
    """

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return FloatValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# BOOL VALUE
# =============================================================================


class BoolValue(
    LogicalBase["bool | BoolValue", "BoolValue"],
    ComparisonBase["bool | BoolValue"],
    CoreBase,
    ComputedValue[bool | SpecialValue],
):
    """RValue representing a boolean.

    Supports logical operations: and_, or_, not_.

    Example:
        >>> val = BoolValue(True)
        >>> combined = val.and_(other)  # Returns BoolValue
        >>> negated = val.not_()  # Returns BoolValue
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# STRING VALUE
# =============================================================================


class StrValue(
    StringBase["StrValue"],
    ComparisonBase["str | StrValue"],
    LogicalBase["str | StrValue", "BoolValue"],
    CoreBase,
    ComputedValue[str | SpecialValue],
):
    """RValue representing a string.

    Supports concatenation, indexing, slicing, and string operations.

    Example:
        >>> val = StrValue("hello")
        >>> greeting = val + " world"  # Returns StrValue
        >>> first = val[0]  # Returns StrValue
        >>> length = val.len_()  # Returns IntValue
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

    def __add__(self, other: str | StrValue) -> StrValue:
        """Concatenate strings."""
        from ..computations.binary_ops import AddOp

        return StrValue(AddOp(self, literal(other)))

    def __radd__(self, other: str) -> StrValue:
        """Right concatenate strings."""
        from ..computations.binary_ops import AddOp

        return StrValue(AddOp[str](literal(other), self))


# =============================================================================
# BYTES VALUE
# =============================================================================


class BytesValue(
    BytesMethodsBase["BytesValue"],
    LengthableBase,
    SliceableBase["BytesValue"],
    ContainableBase["int | bytes"],
    ComparisonBase["bytes | BytesValue"],
    LogicalBase["bytes | BytesValue", "BoolValue"],
    CoreBase,
    ComputedValue[bytes | SpecialValue],
):
    """RValue representing bytes.

    Supports concatenation, indexing, slicing, and bytes operations.

    Example:
        >>> val = BytesValue(b"hello")
        >>> combined = val + b" world"  # Returns BytesValue
        >>> first = val[0]  # Returns IntValue
        >>> decoded = val.decode()  # Returns StrValue
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

    def __add__(self, other: bytes | BytesValue) -> BytesValue:
        """Concatenate bytes."""
        from ..computations.binary_ops import AddOp

        return BytesValue(AddOp(self, literal(other)))

    def __radd__(self, other: bytes) -> BytesValue:
        """Right concatenate bytes."""
        from ..computations.binary_ops import AddOp

        return BytesValue(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> IntValue: ...

    @overload
    def __getitem__(self, key: slice) -> BytesValue: ...

    def __getitem__(self, key: int | slice) -> BytesValue | IntValue:
        """Get byte or slice."""
        if isinstance(key, slice):
            from ..computations.sequence_ops import SliceOp

            return BytesValue(SliceOp[bytes](self, key.start, key.stop, key.step))

        from ..computations.sequence_ops import AtOp

        return IntValue(AtOp[int](self, literal(key)))


# =============================================================================
# NONE VALUE
# =============================================================================


class NoneValue(
    LogicalBase["None | NoneValue", "BoolValue"],
    CoreBase,
    ComputedValue[None | SpecialValue],
):
    """RValue representing None.

    Useful for representing absence of value in expressions.

    Example:
        >>> val = NoneValue()
        >>> is_none = val.eq(None)  # Returns BoolValue
    """

    def __init__(self, value: None | RValue = None) -> None:
        """Initialize literal with value.

        Args:
            value: The native Python value to wrap (or an RValue that computes to None)
        """
        self._value = value

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# SPECIAL VALUE TYPES
# =============================================================================


class UnknownValue(
    NumericBase["object", "UnknownValue"],
    ComparisonBase["object"],
    LogicalBase["object", "BoolValue"],
    BitwiseBase["object", "UnknownValue"],
    CoreBase,
    ComputedValue[object],
):
    """RValue representing an unknown/dynamic type.

    UnknownValue can be any type and supports all operations.
    Results remain as UnknownValue until resolved.

    Useful for:
    - Dynamic lookups where type is not known at definition time
    - Generic operations that work on any value
    - Placeholder values in expressions

    Example:
        >>> val = UnknownValue(some_dynamic_data)
        >>> result = val + 1  # Returns UnknownValue
        >>> typed = val.is_empty()  # Returns BoolValue
    """

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return UnknownValue(operand)

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        return UnknownValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


class EmptyValue(
    CoreBase,
    ComputedValue[None],
):
    """RValue representing an empty/missing value.

    EmptyValue represents the absence of a value, distinct from None.
    It can be used as a sentinel for missing data.

    Key properties:
    - is_empty() always returns True
    - is_special() always returns True
    - or_default(x) always returns x

    Example:
        >>> empty = EmptyValue()
        >>> empty.is_empty()  # Always BoolValue(True)
        >>> empty.or_default(42)  # Returns 42
    """

    def __init__(self) -> None:
        """Initialize empty value."""
        self._value = None

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def execute(self, context: object) -> None:
        """Execute returns None for empty values.

        Args:
            context: Execution context (unused)

        Returns:
            None
        """
        return None

    def __repr__(self) -> str:
        """Return machine-friendly representation."""
        return "EmptyValue()"


class NaNValue(
    NumericBase["object", "NaNValue"],
    ComparisonBase["object"],
    CoreBase,
    ComputedValue[float],
):
    """RValue representing Not-a-Number.

    NaNValue represents an invalid numeric result (like 0/0).
    Arithmetic operations propagate NaN.

    Key properties:
    - is_nan() always returns True
    - is_special() always returns True
    - Comparisons with NaN return False (including self)
    - Arithmetic with NaN returns NaN

    Example:
        >>> nan = NaNValue()
        >>> nan.is_nan()  # Always BoolValue(True)
        >>> nan + 1  # Returns NaNValue
        >>> nan.eq(nan)  # Returns BoolValue(False)
    """

    def __init__(self) -> None:
        """Initialize NaN value."""
        self._value = float("nan")

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return NaNValue()

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def execute(self, context: object) -> float:
        """Execute returns NaN.

        Args:
            context: Execution context (unused)

        Returns:
            float('nan')
        """
        return float("nan")

    def __repr__(self) -> str:
        """Return machine-friendly representation."""
        return "NaNValue()"


# =============================================================================
# LIST VALUE
# =============================================================================


class ListValue[T](
    SequenceBase[T, "ListValue[T]"],
    ComparisonBase[list[T]],
    CoreBase,
    ComputedValue[list[T] | SpecialValue],
):
    """RValue representing a list.

    Supports indexing, slicing, length, and functional operations
    (map, filter, reduce, etc.).

    Type Parameters:
        T: Type of elements in the list

    Example:
        >>> val = ListValue([1, 2, 3])
        >>> first = val[0]  # Returns typed value
        >>> doubled = val.map_(lambda x: x * 2)  # Returns ListValue
        >>> total = val.sum_()  # Returns IntValue/FloatValue
    """

    VALUE_TYPE: ClassVar[type] = list

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        from .values import BoolValue

        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        from .values import BoolValue

        return BoolValue(operand)

    def __add__(self, other: list[T] | ListValue[T]) -> ListValue[T]:
        """Concatenate lists."""
        from ..computations.binary_ops import AddOp

        return ListValue(AddOp(self, literal(other)))

    def __radd__(self, other: list[T]) -> ListValue[T]:
        """Right concatenate lists."""
        from ..computations.binary_ops import AddOp

        return ListValue(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> UnknownValue: ...

    @overload
    def __getitem__(self, key: slice) -> ListValue[T]: ...

    def __getitem__(self, key: int | slice) -> UnknownValue | ListValue[T]:
        """Get item or slice."""
        if isinstance(key, slice):
            from ..computations.sequence_ops import SliceOp

            return ListValue(SliceOp(self, key.start, key.stop, key.step))

        from ..computations.sequence_ops import AtOp
        from .values import UnknownValue

        return UnknownValue(AtOp(self, literal(key)))


# =============================================================================
# TUPLE VALUE
# =============================================================================


class TupleValue[*Ts](
    SequenceBase[object, "ListValue[object]"],
    ComparisonBase[tuple],
    CoreBase,
    ComputedValue[tuple[*Ts] | SpecialValue],
):
    """RValue representing a tuple.

    Supports indexing, length, and containment operations.
    Tuples are immutable so no mutation operations.

    Type Parameters:
        *Ts: Types of elements in the tuple

    Example:
        >>> val = TupleValue((1, "hello", 3.14))
        >>> first = val[0]  # Returns typed value
        >>> length = val.len_()  # Returns IntValue
    """

    VALUE_TYPE: ClassVar[type] = tuple

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        from .values import BoolValue

        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        from .values import BoolValue

        return BoolValue(operand)

    def _wrap_sliceable_result(self, operand: RValue) -> TupleValue:
        return TupleValue(operand)

    @overload
    def __getitem__(self, key: int) -> UnknownValue: ...

    @overload
    def __getitem__(self, key: slice) -> TupleValue: ...

    def __getitem__(self, key: int | slice) -> UnknownValue | TupleValue:
        """Get item or slice."""
        if isinstance(key, slice):
            from ..computations.sequence_ops import SliceOp

            return TupleValue(SliceOp(self, key.start, key.stop, key.step))

        from ..computations.sequence_ops import AtOp
        from .values import UnknownValue

        return UnknownValue(AtOp(self, literal(key)))


# =============================================================================
# DICT VALUE
# =============================================================================


class DictValue[K, V](
    MappingBase[K, V, "DictValue[K, V]"],
    ComparisonBase[dict[K, V]],
    CoreBase,
    ComputedValue[dict[K, V] | SpecialValue],
):
    """RValue representing a dictionary.

    Supports key access, keys/values/items, and functional operations.

    Type Parameters:
        K: Type of keys
        V: Type of values

    Example:
        >>> val = DictValue({"a": 1, "b": 2})
        >>> a_val = val["a"]  # Returns typed value
        >>> all_keys = val.keys_()  # Returns ListValue[K]
        >>> doubled = val.map_values(lambda x: x * 2)  # Returns DictValue
    """

    VALUE_TYPE: ClassVar[type] = dict

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        from .values import BoolValue

        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        from .values import BoolValue

        return BoolValue(operand)

    def __getitem__(self, key: K) -> UnknownValue:
        """Get value for key."""
        from ..computations.sequence_ops import AtOp
        from .values import UnknownValue

        return UnknownValue(AtOp(self, literal(key)))


# =============================================================================
# SET VALUE
# =============================================================================


class SetValue[T](
    SetBase[T, "SetValue[T]"],
    ComparisonBase[set[T]],
    CoreBase,
    ComputedValue[set[T] | SpecialValue],
):
    """RValue representing a set.

    Supports containment testing, length, and set operations.

    Type Parameters:
        T: Type of elements in the set

    Example:
        >>> val = SetValue({1, 2, 3})
        >>> exists = val.contains(2)  # Returns BoolValue
        >>> union = val.union({4, 5})  # Returns SetValue
    """

    VALUE_TYPE: ClassVar[type] = set

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        from .values import BoolValue

        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        from .values import BoolValue

        return BoolValue(operand)

    def _wrap_set_result(self, operand: RValue) -> SetValue[T]:
        return SetValue(operand)


# =============================================================================
# FROZENSET VALUE
# =============================================================================


class FrozenSetValue[T](
    SetBase[T, "FrozenSetValue[T]"],
    ComparisonBase[frozenset[T]],
    CoreBase,
    ComputedValue[frozenset[T] | SpecialValue],
):
    """RValue representing a frozenset.

    Supports containment testing, length, and set operations.
    Immutable version of SetValue.

    Type Parameters:
        T: Type of elements in the set

    Example:
        >>> val = FrozenSetValue(frozenset({1, 2, 3}))
        >>> exists = val.contains(2)  # Returns BoolValue
        >>> union = val.union(frozenset({4, 5}))  # Returns FrozenSetValue
    """

    VALUE_TYPE: ClassVar[type] = frozenset

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        from .values import BoolValue

        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        from .values import BoolValue

        return BoolValue(operand)

    def _wrap_set_result(self, operand: RValue) -> FrozenSetValue[T]:
        return FrozenSetValue(operand)
