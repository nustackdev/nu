"""Unified Type classes - the core of the everyshape type system.

This module provides unified Type classes that handle both literal and computed
values through a single interface. Each Type accepts either:
- A literal Python value: IntType(42)
- An Term expression: IntType(some_operation)
- A Sentinel: IntType(EMPTY)

Type Hierarchy:
    Type[T] (base from term.py)
    ├── IntType               # int expressions
    ├── FloatType             # float expressions
    ├── StrType               # str expressions
    ├── BoolType              # bool expressions
    ├── BytesType             # bytes expressions
    ├── NilType               # None expressions
    ├── ListType[T]           # list expressions
    ├── DictType[K, V]        # dict expressions
    ├── SetType[T]            # set expressions
    ├── TupleType[*Ts]        # tuple expressions
    ├── FrozenSetType[T]      # frozenset expressions
    ├── AnyType               # dynamic/unknown type
    └── SentinelType          # special values
        ├── EmptyType         # absence of value
        └── NAType            # not applicable

Example:
    >>> x = IntType(42)  # From literal
    >>> y = IntType(some_op)  # From operation
    >>> z = x + y  # Returns IntType
    >>> z.execute(ctx)  # Returns computed result
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, overload

from ..term import Type
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
    from everyshape.typing import Sentinel

    from ..term import Term


__all__ = [
    # Special types
    "AnyType",
    "BoolType",
    "BytesType",
    "DictType",
    "EmptyType",
    "FloatType",
    "FrozenSetType",
    # Primitive types
    "IntType",
    # Collection types
    "ListType",
    "NAType",
    "NilType",
    "SentinelType",
    "SetType",
    "StrType",
    "TupleType",
]


# =============================================================================
# PRIMITIVE TYPES
# =============================================================================


class IntType(
    ComparisonBase["int | float | FloatType | IntType"],
    LogicalBase["bool | int | BoolType | IntType", "BoolType"],
    BitwiseBase["int | IntType", "IntType"],
    CoreBase,
    Type[int],
):
    """Integer type - represents int expressions (literal or computed).

    Supports arithmetic, comparison, logical, and bitwise operations.
    Operations return appropriate Type classes matching Python semantics:
    - int + int → IntType
    - int + float → FloatType
    - int / int → FloatType (true division)

    Example:
        >>> x = IntType(42)  # From literal
        >>> y = IntType(some_op)  # From operation
        >>> z = x + y  # Returns IntType
        >>> z.execute(ctx)  # Returns computed int
    """

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        return IntType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_logical_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> Term:
        return BoolType(operand)

    # =========================================================================
    # ARITHMETIC OPERATIONS
    # =========================================================================

    @overload
    def __add__(self, other: int | IntType) -> IntType: ...
    @overload
    def __add__(self, other: float | FloatType) -> FloatType: ...
    def __add__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import AddOp
        from .conversion import literal

        if isinstance(other, (float, FloatType)):
            return FloatType(AddOp(self, literal(other)))
        return IntType(AddOp(self, literal(other)))

    @overload
    def __radd__(self, other: int) -> IntType: ...
    @overload
    def __radd__(self, other: float) -> FloatType: ...
    def __radd__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import AddOp
        from .conversion import literal

        if isinstance(other, float):
            return FloatType(AddOp(literal(other), self))
        return IntType(AddOp(literal(other), self))

    @overload
    def __sub__(self, other: int | IntType) -> IntType: ...
    @overload
    def __sub__(self, other: float | FloatType) -> FloatType: ...
    def __sub__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import SubOp
        from .conversion import literal

        if isinstance(other, (float, FloatType)):
            return FloatType(SubOp(self, literal(other)))
        return IntType(SubOp(self, literal(other)))

    @overload
    def __rsub__(self, other: int) -> IntType: ...
    @overload
    def __rsub__(self, other: float) -> FloatType: ...
    def __rsub__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import SubOp
        from .conversion import literal

        if isinstance(other, float):
            return FloatType(SubOp(literal(other), self))
        return IntType(SubOp(literal(other), self))

    @overload
    def __mul__(self, other: int | IntType) -> IntType: ...
    @overload
    def __mul__(self, other: float | FloatType) -> FloatType: ...
    def __mul__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import MulOp
        from .conversion import literal

        if isinstance(other, (float, FloatType)):
            return FloatType(MulOp(self, literal(other)))
        return IntType(MulOp(self, literal(other)))

    @overload
    def __rmul__(self, other: int) -> IntType: ...
    @overload
    def __rmul__(self, other: float) -> FloatType: ...
    def __rmul__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import MulOp
        from .conversion import literal

        if isinstance(other, float):
            return FloatType(MulOp(literal(other), self))
        return IntType(MulOp(literal(other), self))

    def __truediv__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comps.core.binary_ops import DivOp
        from .conversion import literal

        return FloatType(DivOp(self, literal(other)))

    def __rtruediv__(self, other: int | float) -> FloatType:
        from ..comps.core.binary_ops import DivOp
        from .conversion import literal

        return FloatType(DivOp(literal(other), self))

    @overload
    def __floordiv__(self, other: int | IntType) -> IntType: ...
    @overload
    def __floordiv__(self, other: float | FloatType) -> FloatType: ...
    def __floordiv__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import FloorDivOp
        from .conversion import literal

        if isinstance(other, (float, FloatType)):
            return FloatType(FloorDivOp(self, literal(other)))
        return IntType(FloorDivOp(self, literal(other)))

    @overload
    def __rfloordiv__(self, other: int) -> IntType: ...
    @overload
    def __rfloordiv__(self, other: float) -> FloatType: ...
    def __rfloordiv__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import FloorDivOp
        from .conversion import literal

        if isinstance(other, float):
            return FloatType(FloorDivOp(literal(other), self))
        return IntType(FloorDivOp(literal(other), self))

    @overload
    def __mod__(self, other: int | IntType) -> IntType: ...
    @overload
    def __mod__(self, other: float | FloatType) -> FloatType: ...
    def __mod__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import ModOp
        from .conversion import literal

        if isinstance(other, (float, FloatType)):
            return FloatType(ModOp(self, literal(other)))
        return IntType(ModOp(self, literal(other)))

    @overload
    def __rmod__(self, other: int) -> IntType: ...
    @overload
    def __rmod__(self, other: float) -> FloatType: ...
    def __rmod__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import ModOp
        from .conversion import literal

        if isinstance(other, float):
            return FloatType(ModOp(literal(other), self))
        return IntType(ModOp(literal(other), self))

    @overload
    def __pow__(self, other: int | IntType) -> IntType: ...
    @overload
    def __pow__(self, other: float | FloatType) -> FloatType: ...
    def __pow__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import PowOp
        from .conversion import literal

        if isinstance(other, (float, FloatType)):
            return FloatType(PowOp(self, literal(other)))
        return IntType(PowOp(self, literal(other)))

    @overload
    def __rpow__(self, other: int) -> IntType: ...
    @overload
    def __rpow__(self, other: float) -> FloatType: ...
    def __rpow__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import PowOp
        from .conversion import literal

        if isinstance(other, float):
            return FloatType(PowOp(literal(other), self))
        return IntType(PowOp(literal(other), self))

    def __neg__(self) -> IntType:
        from ..comps.core.unary_ops import NegOp

        return IntType(NegOp(self))

    def __pos__(self) -> IntType:
        from ..comps.core.unary_ops import PosOp

        return IntType(PosOp(self))

    def __abs__(self) -> IntType:
        from ..comps.core.unary_ops import AbsOp

        return IntType(AbsOp(self))


class FloatType(
    ComparisonBase["int | float | FloatType | IntType"],
    LogicalBase["bool | float | BoolType | FloatType", "BoolType"],
    CoreBase,
    Type[float],
):
    """Float type - represents float expressions (literal or computed).

    Supports arithmetic, comparison, and logical operations.
    All arithmetic operations return FloatType (Python semantics).

    Example:
        >>> x = FloatType(3.14)  # From literal
        >>> y = FloatType(some_op)  # From operation
        >>> z = x * 2  # Returns FloatType
    """

    def _wrap_comparison_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_logical_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> Term:
        return BoolType(operand)

    # All arithmetic returns FloatType
    def __add__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comps.core.binary_ops import AddOp
        from .conversion import literal

        return FloatType(AddOp(self, literal(other)))

    def __radd__(self, other: int | float) -> FloatType:
        from ..comps.core.binary_ops import AddOp
        from .conversion import literal

        return FloatType(AddOp(literal(other), self))

    def __sub__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comps.core.binary_ops import SubOp
        from .conversion import literal

        return FloatType(SubOp(self, literal(other)))

    def __rsub__(self, other: int | float) -> FloatType:
        from ..comps.core.binary_ops import SubOp
        from .conversion import literal

        return FloatType(SubOp(literal(other), self))

    def __mul__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comps.core.binary_ops import MulOp
        from .conversion import literal

        return FloatType(MulOp(self, literal(other)))

    def __rmul__(self, other: int | float) -> FloatType:
        from ..comps.core.binary_ops import MulOp
        from .conversion import literal

        return FloatType(MulOp(literal(other), self))

    def __truediv__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comps.core.binary_ops import DivOp
        from .conversion import literal

        return FloatType(DivOp(self, literal(other)))

    def __rtruediv__(self, other: int | float) -> FloatType:
        from ..comps.core.binary_ops import DivOp
        from .conversion import literal

        return FloatType(DivOp(literal(other), self))

    def __floordiv__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comps.core.binary_ops import FloorDivOp
        from .conversion import literal

        return FloatType(FloorDivOp(self, literal(other)))

    def __rfloordiv__(self, other: int | float) -> FloatType:
        from ..comps.core.binary_ops import FloorDivOp
        from .conversion import literal

        return FloatType(FloorDivOp(literal(other), self))

    def __mod__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comps.core.binary_ops import ModOp
        from .conversion import literal

        return FloatType(ModOp(self, literal(other)))

    def __rmod__(self, other: int | float) -> FloatType:
        from ..comps.core.binary_ops import ModOp
        from .conversion import literal

        return FloatType(ModOp(literal(other), self))

    def __pow__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comps.core.binary_ops import PowOp
        from .conversion import literal

        return FloatType(PowOp(self, literal(other)))

    def __rpow__(self, other: int | float) -> FloatType:
        from ..comps.core.binary_ops import PowOp
        from .conversion import literal

        return FloatType(PowOp(literal(other), self))

    def __neg__(self) -> FloatType:
        from ..comps.core.unary_ops import NegOp

        return FloatType(NegOp(self))

    def __pos__(self) -> FloatType:
        from ..comps.core.unary_ops import PosOp

        return FloatType(PosOp(self))

    def __abs__(self) -> FloatType:
        from ..comps.core.unary_ops import AbsOp

        return FloatType(AbsOp(self))


class BoolType(
    LogicalBase["bool | BoolType", "BoolType"],
    ComparisonBase["bool | BoolType"],
    CoreBase,
    Type[bool],
):
    """Boolean type - represents bool expressions (literal or computed).

    Supports logical operations: and_(), or_(), not_().

    Example:
        >>> x = BoolType(True)
        >>> y = x.and_(other)  # Returns BoolType
        >>> z = x.not_()  # Returns BoolType
    """

    def _wrap_logical_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> Term:
        return BoolType(operand)


class StrType(
    StringBase["StrType"],
    ComparisonBase["str | StrType"],
    LogicalBase["str | StrType", "BoolType"],
    CoreBase,
    Type[str],
):
    """String type - represents str expressions (literal or computed).

    Supports concatenation, string operations, comparison, and logical operations.

    Example:
        >>> x = StrType("hello")
        >>> y = x + " world"  # Returns StrType
        >>> z = x.upper()  # Returns StrType
    """

    def _wrap_logical_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_string_result(self, operand: Term) -> Term:
        return StrType(operand)

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        return StrType(operand)

    def __add__(self, other: str | StrType) -> StrType:
        from ..comps.core.binary_ops import AddOp
        from .conversion import literal

        return StrType(AddOp(self, literal(other)))

    def __radd__(self, other: str) -> StrType:
        from ..comps.core.binary_ops import AddOp
        from .conversion import literal

        return StrType(AddOp(literal(other), self))


class BytesType(
    BytesMethodsBase["BytesType"],
    LengthableBase,
    SliceableBase["BytesType"],
    ContainableBase["int | bytes"],
    ComparisonBase["bytes | BytesType"],
    LogicalBase["bytes | BytesType", "BoolType"],
    CoreBase,
    Type[bytes],
):
    """Bytes type - represents bytes expressions (literal or computed).

    Supports concatenation, bytes operations, comparison, and logical operations.

    Example:
        >>> x = BytesType(b"hello")
        >>> y = x + b" world"  # Returns BytesType
        >>> z = x.decode()  # Returns StrType
    """

    def _wrap_logical_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_bytes_result(self, operand: Term) -> Term:
        return BytesType(operand)

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        return BytesType(operand)

    def __add__(self, other: bytes | BytesType) -> BytesType:
        from ..comps.core.binary_ops import AddOp
        from .conversion import literal

        return BytesType(AddOp(self, literal(other)))

    def __radd__(self, other: bytes) -> BytesType:
        from ..comps.core.binary_ops import AddOp
        from .conversion import literal

        return BytesType(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> IntType: ...
    @overload
    def __getitem__(self, key: slice) -> BytesType: ...
    def __getitem__(self, key: int | slice) -> BytesType | IntType:
        from ..comps.typed.sequence import AtOp, SliceOp
        from .conversion import literal

        if isinstance(key, slice):
            return BytesType(SliceOp[bytes](self, key.start, key.stop, key.step))
        return IntType(AtOp[int](self, literal(key)))


class NilType(
    LogicalBase["None | NilType", "BoolType"],
    CoreBase,
    Type[None],
):
    """Nil type - represents None expressions (literal or computed).

    Example:
        >>> x = NilType()
        >>> x.is_empty()  # Returns BoolType
    """

    def __init__(self, source: None | Term[None] | Sentinel = None) -> None:
        """Initialize Nil type (defaults to None literal)."""
        super().__init__(source if source is not None else None)

    def _wrap_logical_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> Term:
        return BoolType(operand)


# =============================================================================
# COLLECTION TYPES
# =============================================================================


class ListType[T](
    SequenceBase[T, "ListType[T]"],
    ComparisonBase[list[T]],
    CoreBase,
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
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> BoolType:
        return BoolType(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListType:
        return ListType(operand)

    def __add__(self, other: list[T] | ListType[T]) -> ListType[T]:
        from ..comps.core.binary_ops import AddOp
        from .conversion import literal

        return ListType(AddOp(self, literal(other)))

    def __radd__(self, other: list[T]) -> ListType[T]:
        from ..comps.core.binary_ops import AddOp
        from .conversion import literal

        return ListType(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> AnyType: ...
    @overload
    def __getitem__(self, key: slice) -> ListType[T]: ...
    def __getitem__(self, key: int | slice) -> AnyType | ListType[T]:
        from ..comps.typed.sequence import AtOp, SliceOp
        from .conversion import literal

        if isinstance(key, slice):
            return ListType(SliceOp(self, key.start, key.stop, key.step))
        return AnyType(AtOp(self, literal(key)))


class DictType[K, V](
    MappingBase[K, V, "DictType[K, V]"],
    ComparisonBase[dict[K, V]],
    CoreBase,
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
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> BoolType:
        return BoolType(operand)

    def __getitem__(self, key: K) -> AnyType:
        from ..comps.typed.sequence import AtOp
        from .conversion import literal

        return AnyType(AtOp(self, literal(key)))


class TupleType[*Ts](
    SequenceBase[object, "ListType[object]"],
    ComparisonBase[tuple],
    CoreBase,
    Type[tuple[*Ts]],
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
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> BoolType:
        return BoolType(operand)

    def _wrap_sliceable_result(self, operand: Term) -> TupleType:
        return TupleType(operand)

    @overload
    def __getitem__(self, key: int) -> AnyType: ...
    @overload
    def __getitem__(self, key: slice) -> TupleType: ...
    def __getitem__(self, key: int | slice) -> AnyType | TupleType:
        from ..comps.typed.sequence import AtOp, SliceOp
        from .conversion import literal

        if isinstance(key, slice):
            return TupleType(SliceOp(self, key.start, key.stop, key.step))
        return AnyType(AtOp(self, literal(key)))


class SetType[T](
    SetBase[T, "SetType[T]"],
    ComparisonBase[set[T]],
    CoreBase,
    Type[set[T]],
):
    """Set type - represents set expressions (literal or computed).

    Supports containment testing, length, and set operations.

    Example:
        >>> x = SetType({1, 2, 3})
        >>> y = x.contains(2)  # Returns BoolType
        >>> z = x.union({4})  # Returns SetType
    """

    VALUE_TYPE: ClassVar[type] = set

    def _wrap_comparison_result(self, operand: Term) -> BoolType:
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> BoolType:
        return BoolType(operand)

    def _wrap_set_result(self, operand: Term) -> SetType[T]:
        return SetType(operand)


class FrozenSetType[T](
    SetBase[T, "FrozenSetType[T]"],
    ComparisonBase[frozenset[T]],
    CoreBase,
    Type[frozenset[T]],
):
    """FrozenSet type - represents frozenset expressions (literal or computed).

    Immutable version of SetType.

    Example:
        >>> x = FrozenSetType(frozenset({1, 2, 3}))
        >>> y = x.contains(2)  # Returns BoolType
    """

    VALUE_TYPE: ClassVar[type] = frozenset

    def _wrap_comparison_result(self, operand: Term) -> BoolType:
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> BoolType:
        return BoolType(operand)

    def _wrap_set_result(self, operand: Term) -> FrozenSetType[T]:
        return FrozenSetType(operand)


# =============================================================================
# SPECIAL TYPES
# =============================================================================


class AnyType(
    NumericBase["object", "AnyType"],
    ComparisonBase["object"],
    LogicalBase["object", "BoolType"],
    BitwiseBase["object", "AnyType"],
    CoreBase,
    Type[object],
):
    """Any type - represents expressions of unknown/dynamic type.

    AnyType can be any type and supports all operations.
    Results remain as AnyType until resolved.

    Useful for:
    - Dynamic lookups where type is not known at definition time
    - Generic operations that work on any value

    Example:
        >>> x = AnyType(some_dynamic_data)
        >>> y = x + 1  # Returns AnyType
        >>> z = x.is_empty()  # Returns BoolType
    """

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        return AnyType(operand)

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        return AnyType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_logical_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_core_result(self, operand: Term) -> Term:
        return BoolType(operand)


class SentinelType(CoreBase, Type[None]):
    """Base for sentinel types (EmptyType, NAType).

    Sentinels represent special values that indicate absence or invalidity.
    """

    def _wrap_core_result(self, operand: Term) -> Term:
        return BoolType(operand)


class EmptyType(SentinelType):
    """Empty type - represents absence of a value.

    EmptyType represents the absence of a value, distinct from None.
    It can be used as a sentinel for missing data.

    Key properties:
    - is_empty() always returns True
    - or_default(x) always returns x

    Example:
        >>> empty = EmptyType()
        >>> empty.is_empty()  # Always BoolType(True)
        >>> empty.or_default(42)  # Returns 42
    """

    def __init__(self) -> None:
        """Initialize empty type."""
        super().__init__(None)

    def execute(self, context: object) -> None:
        """Execute returns None for empty values."""
        return None


class NAType(SentinelType):
    """Not Applicable type - represents invalid/undefined operations.

    NAType represents an invalid or not-applicable result.
    Operations on NA propagate NA.

    Key properties:
    - Represents "not applicable" (N/A), not "not a number"
    - Operations with NA return NA
    - is_na() always returns True

    Example:
        >>> na = NAType()
        >>> na.is_na()  # Always BoolType(True)
    """

    def __init__(self) -> None:
        """Initialize NA type."""
        super().__init__(None)

    def execute(self, context: object) -> None:
        """Execute returns None for NA values."""
        return None
