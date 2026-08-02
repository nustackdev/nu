"""Float - float interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.lang import BoolArg, FloatArg, IntArg

    from .bool_ import Bool


__all__ = [
    "Float",
]


class Float(Form, TypedNu[float]):
    """Float interface. Numeric + comparable + logical."""

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Add

        return Float(Add(self, other))

    def __radd__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Add

        return Float(Add(other, self))

    def __sub__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Sub

        return Float(Sub(self, other))

    def __rsub__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Sub

        return Float(Sub(other, self))

    def __mul__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Mul

        return Float(Mul(self, other))

    def __rmul__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Mul

        return Float(Mul(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Div

        return Float(Div(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Div

        return Float(Div(other, self))

    def __floordiv__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import FloorDiv

        return Float(FloorDiv(self, other))

    def __rfloordiv__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import FloorDiv

        return Float(FloorDiv(other, self))

    def __mod__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Mod

        return Float(Mod(self, other))

    def __rmod__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Mod

        return Float(Mod(other, self))

    def __pow__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Pow

        return Float(Pow(self, other))

    def __rpow__(self, other: IntArg | FloatArg) -> Float:
        from nu.core import Pow

        return Float(Pow(other, self))

    def __neg__(self) -> Float:
        from nu.core import Neg

        return Float(Neg(self))

    def __pos__(self) -> Float:
        from nu.core import Pos

        return Float(Pos(self))

    def __abs__(self) -> Float:
        from nu.core import Abs

        return Float(Abs(self))

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

    def and_(self, other: BoolArg | FloatArg) -> Bool:
        """Logical AND: self AND other."""
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: BoolArg | FloatArg) -> Bool:
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
