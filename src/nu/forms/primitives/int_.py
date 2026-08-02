"""Int - integer interface.

Int = Form[int] + arithmetic + comparison + logical + bitwise.
Handles int/float promotion: int op float -> Float.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.lang import BoolArg, FloatArg, IntArg

    from .bool_ import Bool
    from .float_ import Float


__all__ = [
    "Int",
]


class Int(Form, TypedNu[int]):
    """Integer interface. Full numeric + comparable + logical + bitwise."""

    # =========================================================================
    # ARITHMETIC (with int/float promotion)
    # =========================================================================

    @overload
    def __add__(self, other: IntArg) -> Int: ...
    @overload
    def __add__(self, other: FloatArg) -> Float: ...
    def __add__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import Add

        from .float_ import Float

        if isinstance(other, (float, Float)):
            return Float(Add(self, other))
        return Int(Add(self, other))

    @overload
    def __radd__(self, other: IntArg) -> Int: ...
    @overload
    def __radd__(self, other: FloatArg) -> Float: ...
    def __radd__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import Add

        from .float_ import Float

        if isinstance(other, float):
            return Float(Add(other, self))
        return Int(Add(other, self))

    @overload
    def __sub__(self, other: IntArg) -> Int: ...
    @overload
    def __sub__(self, other: FloatArg) -> Float: ...
    def __sub__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import Sub

        from .float_ import Float

        if isinstance(other, (float, Float)):
            return Float(Sub(self, other))
        return Int(Sub(self, other))

    @overload
    def __rsub__(self, other: IntArg) -> Int: ...
    @overload
    def __rsub__(self, other: FloatArg) -> Float: ...
    def __rsub__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import Sub

        from .float_ import Float

        if isinstance(other, float):
            return Float(Sub(other, self))
        return Int(Sub(other, self))

    @overload
    def __mul__(self, other: IntArg) -> Int: ...
    @overload
    def __mul__(self, other: FloatArg) -> Float: ...
    def __mul__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import Mul

        from .float_ import Float

        if isinstance(other, (float, Float)):
            return Float(Mul(self, other))
        return Int(Mul(self, other))

    @overload
    def __rmul__(self, other: IntArg) -> Int: ...
    @overload
    def __rmul__(self, other: FloatArg) -> Float: ...
    def __rmul__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import Mul

        from .float_ import Float

        if isinstance(other, float):
            return Float(Mul(other, self))
        return Int(Mul(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Div

        from .float_ import Float

        return Float(Div(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Div

        from .float_ import Float

        return Float(Div(other, self))

    @overload
    def __floordiv__(self, other: IntArg) -> Int: ...
    @overload
    def __floordiv__(self, other: FloatArg) -> Float: ...
    def __floordiv__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import FloorDiv

        from .float_ import Float

        if isinstance(other, (float, Float)):
            return Float(FloorDiv(self, other))
        return Int(FloorDiv(self, other))

    @overload
    def __rfloordiv__(self, other: IntArg) -> Int: ...
    @overload
    def __rfloordiv__(self, other: FloatArg) -> Float: ...
    def __rfloordiv__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import FloorDiv

        from .float_ import Float

        if isinstance(other, float):
            return Float(FloorDiv(other, self))
        return Int(FloorDiv(other, self))

    @overload
    def __mod__(self, other: IntArg) -> Int: ...
    @overload
    def __mod__(self, other: FloatArg) -> Float: ...
    def __mod__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import Mod

        from .float_ import Float

        if isinstance(other, (float, Float)):
            return Float(Mod(self, other))
        return Int(Mod(self, other))

    @overload
    def __rmod__(self, other: IntArg) -> Int: ...
    @overload
    def __rmod__(self, other: FloatArg) -> Float: ...
    def __rmod__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import Mod

        from .float_ import Float

        if isinstance(other, float):
            return Float(Mod(other, self))
        return Int(Mod(other, self))

    @overload
    def __pow__(self, other: IntArg) -> Int: ...
    @overload
    def __pow__(self, other: FloatArg) -> Float: ...
    def __pow__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import Pow

        from .float_ import Float

        if isinstance(other, (float, Float)):
            return Float(Pow(self, other))
        return Int(Pow(self, other))

    @overload
    def __rpow__(self, other: IntArg) -> Int: ...
    @overload
    def __rpow__(self, other: FloatArg) -> Float: ...
    def __rpow__(self, other: IntArg | FloatArg) -> Int | Float:
        from nu.core import Pow

        from .float_ import Float

        if isinstance(other, float):
            return Float(Pow(other, self))
        return Int(Pow(other, self))

    def __neg__(self) -> Int:
        from nu.core import Neg

        return Int(Neg(self))

    def __pos__(self) -> Int:
        from nu.core import Pos

        return Int(Pos(self))

    def __abs__(self) -> Int:
        from nu.core import Abs

        return Int(Abs(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: IntArg | FloatArg) -> Bool:
        from nu.core import Gt

        from .bool_ import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: IntArg | FloatArg) -> Bool:
        from nu.core import Lt

        from .bool_ import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: IntArg | FloatArg) -> Bool:
        from nu.core import Ge

        from .bool_ import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: IntArg | FloatArg) -> Bool:
        from nu.core import Le

        from .bool_ import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: IntArg | FloatArg) -> Bool:  # type: ignore[override]
        from nu.core import Eq

        from .bool_ import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: IntArg | FloatArg) -> Bool:  # type: ignore[override]
        from nu.core import Ne

        from .bool_ import Bool

        return Bool(Ne(self, other))

    def is_(self, other: IntArg | FloatArg) -> Bool:
        """Identity comparison: self is other."""
        from nu.core import Is

        from .bool_ import Bool

        return Bool(Is(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg | IntArg) -> Bool:
        """Logical AND: self AND other."""
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: BoolArg | IntArg) -> Bool:
        """Logical OR: self OR other."""
        from nu.core import Or

        from .bool_ import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT: NOT self."""
        from nu.core import Not

        from .bool_ import Bool

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Convert to boolean."""
        from nu.core import ToBool

        from .bool_ import Bool

        return Bool(ToBool(self))

    # =========================================================================
    # BITWISE
    # =========================================================================

    def bitand(self, other: IntArg) -> Int:
        """Bitwise AND: self & other."""
        from nu.core import BitAnd

        return Int(BitAnd(self, other))

    def bitor(self, other: IntArg) -> Int:
        """Bitwise OR: self | other."""
        from nu.core import BitOr

        return Int(BitOr(self, other))

    def __xor__(self, other: IntArg) -> Int:
        from nu.core import BitXor

        return Int(BitXor(self, other))

    def __rxor__(self, other: IntArg) -> Int:
        from nu.core import BitXor

        return Int(BitXor(other, self))

    def bitnot(self) -> Int:
        """Bitwise NOT: ~self."""
        from nu.core import BitNot

        return Int(BitNot(self))

    def __lshift__(self, other: IntArg) -> Int:
        from nu.core import LShift

        return Int(LShift(self, other))

    def __rlshift__(self, other: IntArg) -> Int:
        from nu.core import LShift

        return Int(LShift(other, self))

    def __rshift__(self, other: IntArg) -> Int:
        from nu.core import RShift

        return Int(RShift(self, other))

    def __rrshift__(self, other: IntArg) -> Int:
        from nu.core import RShift

        return Int(RShift(other, self))
