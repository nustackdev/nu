"""Primitive RValue implementations.

This module provides concrete RValue types for Python primitives:
- IntValue: Integer values
- FloatValue: Floating-point values
- BoolValue: Boolean values
- StrValue: String values
- BytesValue: Bytes values
- NoneValue: None value

These wrap native Python values and enable DSL operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from ..context import ContextProtocol
from .base import Literal
from .bases import (
    ArithmeticBase,
    BitwiseBase,
    ComparisonBase,
    LogicalBase,
    StringBase,
)
from .conversion import literal


if TYPE_CHECKING:
    from ..ops.binary_ops import (
        AddOp,
        DivOp,
        EqOp,
        FloorDivOp,
        GeOp,
        GtOp,
        LeOp,
        LShiftOp,
        LtOp,
        ModOp,
        MulOp,
        NeOp,
        PowOp,
        RShiftOp,
        SubOp,
        XorOp,
    )
    from ..ops.unary_ops import AbsOp, NegOp, PosOp


__all__ = [
    "BoolValue",
    "BytesValue",
    "FloatValue",
    "IntValue",
    "NoneValue",
    "StrValue",
]


# =============================================================================
# INTEGER VALUE
# =============================================================================


class IntValue[ContextT: ContextProtocol](
    ArithmeticBase[int, "IntValue", ContextT],
    ComparisonBase[int, "BoolValue", ContextT],
    BitwiseBase[int, "IntValue", ContextT],
    Literal[int, ContextT],
):
    """RValue representing an integer.

    Supports full arithmetic, comparison, and bitwise operations.
    Operations return appropriate RValue types.

    Example:
        >>> val = IntValue(42)
        >>> doubled = val * 2  # Returns MulOp
        >>> is_even = (val % 2).eq(0)  # Returns EqOp
        >>> masked = val.bitand(0xFF)  # Returns BitwiseAndOp
    """

    VALUE_TYPE: ClassVar[type] = int

    def _wrap_result(self, value: object) -> IntValue:
        """Wrap result in IntValue."""
        return IntValue(int(value))  # type: ignore[arg-type]

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)

    # Override arithmetic to return more specific types
    def __add__(self, other: int | IntValue) -> AddOp[int, ContextT]:
        """Addition: self + other."""
        from ..ops.binary_ops import AddOp

        return AddOp(self, self._get_operand(other))

    def __radd__(self, other: int) -> AddOp[int, ContextT]:
        """Right addition: other + self."""
        from ..ops.binary_ops import AddOp

        return AddOp(self._get_operand(other), self)

    def __sub__(self, other: int | IntValue) -> SubOp[int, ContextT]:
        """Subtraction: self - other."""
        from ..ops.binary_ops import SubOp

        return SubOp(self, self._get_operand(other))

    def __rsub__(self, other: int) -> SubOp[int, ContextT]:
        """Right subtraction: other - self."""
        from ..ops.binary_ops import SubOp

        return SubOp(self._get_operand(other), self)

    def __mul__(self, other: int | IntValue) -> MulOp[int, ContextT]:
        """Multiplication: self * other."""
        from ..ops.binary_ops import MulOp

        return MulOp(self, self._get_operand(other))

    def __rmul__(self, other: int) -> MulOp[int, ContextT]:
        """Right multiplication: other * self."""
        from ..ops.binary_ops import MulOp

        return MulOp(self._get_operand(other), self)

    def __truediv__(self, other: int | IntValue) -> DivOp[float, ContextT]:
        """Division: self / other."""
        from ..ops.binary_ops import DivOp

        return DivOp(self, self._get_operand(other))

    def __rtruediv__(self, other: int) -> DivOp[float, ContextT]:
        """Right division: other / self."""
        from ..ops.binary_ops import DivOp

        return DivOp(self._get_operand(other), self)

    def __floordiv__(self, other: int | IntValue) -> FloorDivOp[int, ContextT]:
        """Floor division: self // other."""
        from ..ops.binary_ops import FloorDivOp

        return FloorDivOp(self, self._get_operand(other))

    def __rfloordiv__(self, other: int) -> FloorDivOp[int, ContextT]:
        """Right floor division: other // self."""
        from ..ops.binary_ops import FloorDivOp

        return FloorDivOp(self._get_operand(other), self)

    def __mod__(self, other: int | IntValue) -> ModOp[int, ContextT]:
        """Modulo: self % other."""
        from ..ops.binary_ops import ModOp

        return ModOp(self, self._get_operand(other))

    def __rmod__(self, other: int) -> ModOp[int, ContextT]:
        """Right modulo: other % self."""
        from ..ops.binary_ops import ModOp

        return ModOp(self._get_operand(other), self)

    def __pow__(self, other: int | IntValue) -> PowOp[int, ContextT]:
        """Power: self ** other."""
        from ..ops.binary_ops import PowOp

        return PowOp(self, self._get_operand(other))

    def __rpow__(self, other: int) -> PowOp[int, ContextT]:
        """Right power: other ** self."""
        from ..ops.binary_ops import PowOp

        return PowOp(self._get_operand(other), self)

    def __neg__(self) -> NegOp[int, ContextT]:
        """Negation: -self."""
        from ..ops.unary_ops import NegOp

        return NegOp(self)

    def __pos__(self) -> PosOp[int, ContextT]:
        """Positive: +self."""
        from ..ops.unary_ops import PosOp

        return PosOp(self)

    def __abs__(self) -> AbsOp[int, ContextT]:
        """Absolute value: abs(self)."""
        from ..ops.unary_ops import AbsOp

        return AbsOp(self)

    # Comparison operations
    def __gt__(self, other: int | IntValue) -> GtOp[ContextT]:
        """Greater than: self > other."""
        from ..ops.binary_ops import GtOp

        return GtOp(self, self._get_operand(other))

    def __lt__(self, other: int | IntValue) -> LtOp[ContextT]:
        """Less than: self < other."""
        from ..ops.binary_ops import LtOp

        return LtOp(self, self._get_operand(other))

    def __ge__(self, other: int | IntValue) -> GeOp[ContextT]:
        """Greater or equal: self >= other."""
        from ..ops.binary_ops import GeOp

        return GeOp(self, self._get_operand(other))

    def __le__(self, other: int | IntValue) -> LeOp[ContextT]:
        """Less or equal: self <= other."""
        from ..ops.binary_ops import LeOp

        return LeOp(self, self._get_operand(other))

    def eq(self, other: int | IntValue) -> EqOp[ContextT]:
        """Equality: self == other."""
        from ..ops.binary_ops import EqOp

        return EqOp(self, self._get_operand(other))

    def ne(self, other: int | IntValue) -> NeOp[ContextT]:
        """Inequality: self != other."""
        from ..ops.binary_ops import NeOp

        return NeOp(self, self._get_operand(other))

    # Bitwise operations
    def __xor__(self, other: int | IntValue) -> XorOp[int, ContextT]:
        """XOR: self ^ other."""
        from ..ops.binary_ops import XorOp

        return XorOp(self, self._get_operand(other))

    def __lshift__(self, other: int | IntValue) -> LShiftOp[int, ContextT]:
        """Left shift: self << other."""
        from ..ops.binary_ops import LShiftOp

        return LShiftOp(self, self._get_operand(other))

    def __rshift__(self, other: int | IntValue) -> RShiftOp[int, ContextT]:
        """Right shift: self >> other."""
        from ..ops.binary_ops import RShiftOp

        return RShiftOp(self, self._get_operand(other))


# =============================================================================
# FLOAT VALUE
# =============================================================================


class FloatValue[ContextT: ContextProtocol](
    ArithmeticBase[float, "FloatValue", ContextT],
    ComparisonBase[float, "BoolValue", ContextT],
    Literal[float, ContextT],
):
    """RValue representing a floating-point number.

    Supports full arithmetic and comparison operations.
    Does not support bitwise operations.

    Example:
        >>> val = FloatValue(3.14)
        >>> doubled = val * 2  # Returns MulOp
        >>> is_positive = val > 0  # Returns GtOp
    """

    VALUE_TYPE: ClassVar[type] = float

    def _wrap_result(self, value: object) -> FloatValue:
        """Wrap result in FloatValue."""
        return FloatValue(float(value))  # type: ignore[arg-type]

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)


# =============================================================================
# BOOL VALUE
# =============================================================================


class BoolValue[ContextT: ContextProtocol](
    LogicalBase[bool, "BoolValue", ContextT],
    ComparisonBase[bool, "BoolValue", ContextT],
    Literal[bool, ContextT],
):
    """RValue representing a boolean.

    Supports logical operations: and_, or_, not_.

    Example:
        >>> val = BoolValue(True)
        >>> combined = val.and_(other)  # Returns AndOp
        >>> negated = val.not_()  # Returns NotOp
    """

    VALUE_TYPE: ClassVar[type] = bool

    def _wrap_result(self, value: object) -> BoolValue:
        """Wrap result in BoolValue."""
        return BoolValue(bool(value))

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)


# =============================================================================
# STRING VALUE
# =============================================================================


class StrValue[ContextT: ContextProtocol](
    StringBase["StrValue", ContextT],
    ComparisonBase[str, "BoolValue", ContextT],
    Literal[str, ContextT],
):
    """RValue representing a string.

    Supports concatenation, indexing, slicing, and string operations.

    Example:
        >>> val = StrValue("hello")
        >>> greeting = val + " world"  # Returns AddOp
        >>> first = val[0]  # Returns AtOp
        >>> length = val.len_()  # Returns LenOp
    """

    VALUE_TYPE: ClassVar[type] = str

    def _wrap_result(self, value: object) -> StrValue:
        """Wrap result in StrValue."""
        return StrValue(str(value))

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)


# =============================================================================
# BYTES VALUE
# =============================================================================


class BytesValue[ContextT: ContextProtocol](
    ComparisonBase[bytes, "BoolValue", ContextT],
    Literal[bytes, ContextT],
):
    """RValue representing bytes.

    Supports concatenation, indexing, and slicing.

    Example:
        >>> val = BytesValue(b"hello")
        >>> combined = val + b" world"  # Returns AddOp
        >>> first = val[0]  # Returns AtOp
    """

    VALUE_TYPE: ClassVar[type] = bytes

    def _wrap_result(self, value: object) -> BytesValue:
        """Wrap result in BytesValue."""
        return BytesValue(bytes(value))  # type: ignore[arg-type]

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)

    def __add__(self, other: bytes | BytesValue) -> object:
        """Concatenate bytes."""
        from ..ops.binary_ops import AddOp

        return AddOp(self, self._get_operand(other))

    def __radd__(self, other: bytes) -> object:
        """Right concatenate bytes."""
        from ..ops.binary_ops import AddOp

        return AddOp(self._get_operand(other), self)

    def __getitem__(self, key: int | slice) -> object:
        """Get byte or slice."""
        if isinstance(key, slice):
            from ..ops.sequence_ops import SliceOp

            return SliceOp(self, key.start, key.stop, key.step)

        from ..ops.sequence_ops import AtOp

        return AtOp(self, self._get_operand(key))

    def len_(self) -> object:
        """Get length of bytes.

        Returns:
            Length value
        """
        from ..ops.sequence_ops import LenOp

        return LenOp(self)


# =============================================================================
# NONE VALUE
# =============================================================================


class NoneValue[ContextT: ContextProtocol](Literal[None, ContextT]):
    """RValue representing None.

    Useful for representing absence of value in expressions.

    Example:
        >>> val = NoneValue()
        >>> is_none = val.eq(None)  # Returns EqOp
    """

    VALUE_TYPE: ClassVar[type] = type(None)

    def __init__(self) -> None:
        """Initialize NoneValue."""
        super().__init__(None)

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)

    def eq(self, other: object) -> object:
        """Check equality with None."""
        from ..ops.binary_ops import EqOp

        return EqOp(self, self._get_operand(other))

    def ne(self, other: object) -> object:
        """Check inequality with None."""
        from ..ops.binary_ops import NeOp

        return NeOp(self, self._get_operand(other))
