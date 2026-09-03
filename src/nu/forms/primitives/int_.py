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
    """Integer interface. Full numeric + comparable + logical + bitwise.

    Notes:
        - Arithmetic against a Float or a Python float promotes the result to
          Float. Everything else stays Int.
        - Division `/` always yields Float regardless of operand type; use
          `//` for integer floor division that stays Int.
        - Comparison operators yield Bool. Chained comparisons like
          `a > b > c` do not build a single term; write them as
          `And(a > b, b > c)`.
        - Logical operators are the named forms `and_`, `or_`, `not_`. The
          symbols `&`, `|`, `~` are bitwise and stay Int.

    Example:
        >>> nu.run(nu.Int(6) * nu.Int(7))[0]
        42
    """

    # =========================================================================
    # ARITHMETIC (with int/float promotion)
    # =========================================================================

    @overload
    def __add__(self, other: IntArg) -> Int: ...
    @overload
    def __add__(self, other: FloatArg) -> Float: ...
    def __add__(self, other: IntArg | FloatArg) -> Int | Float:
        """Sum of self and other.

        Args:
            other: the value to add to self. Int or plain int keeps the
                result Int; Float or plain float promotes it to Float.

        Yields:
            The sum. Promoted to Float when either operand is Float.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(2) + nu.Int(3))[0]
            5

            >>> nu.run(nu.Int(2) + 1.5)[0]
            3.5
        """
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
        """Sum of other and self, with self on the right.

        Args:
            other: the value on the left of the `+`. A plain float promotes
                the result to Float; a plain int keeps it Int.

        Notes:
            - Reached only when the left operand is a plain Python int or
              float. A Nu Int or Float on the left goes through its own
              `__add__` first and never lands here.

        Yields:
            The sum. Promoted to Float when the left operand is a plain float.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(3 + nu.Int(4))[0]
            7
        """
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
        """Self minus other.

        Args:
            other: the value to subtract from self. Int or plain int keeps
                the result Int; Float or plain float promotes it to Float.

        Yields:
            The difference. Promoted to Float when either operand is Float.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(10) - nu.Int(3))[0]
            7
        """
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
        """Other minus self, with self on the right.

        Args:
            other: the value on the left of the `-`, the minuend. A plain
                float promotes the result to Float; a plain int keeps it Int.

        Notes:
            - Reached only when the left operand is a plain Python int or
              float. A Nu Int or Float on the left uses its own `__sub__`
              instead.

        Yields:
            The difference. Promoted to Float when the left operand is a
            plain float. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(10 - nu.Int(3))[0]
            7
        """
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
        """Product of self and other.

        Args:
            other: the value to multiply self by. Int or plain int keeps the
                result Int; Float or plain float promotes it to Float.

        Yields:
            The product. Promoted to Float when either operand is Float.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(6) * nu.Int(7))[0]
            42
        """
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
        """Product of other and self, with self on the right.

        Args:
            other: the value on the left of the `*`. A plain float promotes
                the result to Float; a plain int keeps it Int.

        Notes:
            - Reached only when the left operand is a plain Python int or
              float. A Nu Int or Float on the left uses its own `__mul__`
              instead.

        Yields:
            The product. Promoted to Float when the left operand is a plain
            float. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(3 * nu.Int(4))[0]
            12
        """
        from nu.core import Mul

        from .float_ import Float

        if isinstance(other, float):
            return Float(Mul(other, self))
        return Int(Mul(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> Float:
        """Self divided by other.

        Args:
            other: the divisor. Any type accepted, the result is always Float.

        Notes:
            - Always yields Float, even when both operands are Int. Use `//`
              for integer floor division that stays Int.
            - A zero divisor is not caught here; the underlying Div raises at
              evaluation time.

        Yields:
            The quotient as Float. INVALID when either operand is a sentinel.
            Raises at evaluation time when the divisor is zero.

        Example:
            >>> nu.run(nu.Int(6) / nu.Int(2))[0]
            3.0

            >>> nu.run(nu.Int(7) / nu.Int(2))[0]
            3.5
        """
        from nu.core import Div

        from .float_ import Float

        return Float(Div(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> Float:
        """Other divided by self, with self as the divisor.

        Args:
            other: the numerator, on the left of the `/`.

        Notes:
            - Always yields Float, matching `__truediv__`.
            - Reached only when the left operand is a plain Python int or
              float.

        Yields:
            The quotient as Float. INVALID when either operand is a sentinel.
            Raises at evaluation time when self evaluates to zero.

        Example:
            >>> nu.run(10 / nu.Int(4))[0]
            2.5
        """
        from nu.core import Div

        from .float_ import Float

        return Float(Div(other, self))

    @overload
    def __floordiv__(self, other: IntArg) -> Int: ...
    @overload
    def __floordiv__(self, other: FloatArg) -> Float: ...
    def __floordiv__(self, other: IntArg | FloatArg) -> Int | Float:
        """Self floor-divided by other.

        Args:
            other: the divisor. Int or plain int keeps the result Int;
                Float or plain float promotes it to Float.

        Notes:
            - Rounds toward negative infinity, as Python's `//` does, so
              `-7 // 2` is `-4` and not `-3`.

        Yields:
            The floored quotient. Promoted to Float when either operand is
            Float. INVALID when either operand is a sentinel. Raises at
            evaluation time when the divisor is zero.

        Example:
            >>> nu.run(nu.Int(7) // nu.Int(2))[0]
            3

            >>> nu.run(nu.Int(-7) // nu.Int(2))[0]
            -4
        """
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
        """Other floor-divided by self, with self as the divisor.

        Args:
            other: the numerator, on the left of the `//`. Plain float
                promotes to Float; plain int keeps the result Int.

        Notes:
            - Rounds toward negative infinity, as Python's `//` does.
            - Reached only when the left operand is a plain Python int or
              float.

        Yields:
            The floored quotient. Promoted to Float when the left operand is
            a plain float. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(-7 // nu.Int(2))[0]
            -4
        """
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
        """Self modulo other.

        Args:
            other: the divisor. Int or plain int keeps the result Int;
                Float or plain float promotes it to Float.

        Notes:
            - The result's sign follows the divisor, as Python's `%` does,
              so `-7 % 3` is `2` and not `-1`.

        Yields:
            The remainder. Promoted to Float when either operand is Float.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(-7) % nu.Int(3))[0]
            2
        """
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
        """Other modulo self, with self as the divisor.

        Args:
            other: the value being divided, on the left of the `%`. Plain
                float promotes to Float; plain int keeps the result Int.

        Notes:
            - The result's sign follows the divisor, which here is self.
            - Reached only when the left operand is a plain Python int or
              float.

        Yields:
            The remainder. Promoted to Float when the left operand is a
            plain float. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(-7 % nu.Int(3))[0]
            2
        """
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
        """Self raised to the other power.

        Args:
            other: the exponent. Int or plain int keeps the result Int;
                Float or plain float promotes it to Float.

        Notes:
            - A negative exponent raises at evaluation time under Int since
              the result would be non-integer. Promote self to Float first
              for fractional powers.

        Yields:
            The power. Promoted to Float when either operand is Float.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(2) ** nu.Int(10))[0]
            1024
        """
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
        """Other raised to the self power, with self as the exponent.

        Args:
            other: the base, on the left of the `**`. Plain float promotes
                to Float; plain int keeps the result Int.

        Notes:
            - Reached only when the base is a plain Python int or float.

        Yields:
            The power. Promoted to Float when the base is a plain float.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(2 ** nu.Int(10))[0]
            1024
        """
        from nu.core import Pow

        from .float_ import Float

        if isinstance(other, float):
            return Float(Pow(other, self))
        return Int(Pow(other, self))

    def __neg__(self) -> Int:
        """Negation of self.

        Yields:
            The negation. INVALID when self is a sentinel.

        Example:
            >>> nu.run(-nu.Int(4))[0]
            -4
        """
        from nu.core import Neg

        return Int(Neg(self))

    def __pos__(self) -> Int:
        """Self unchanged.

        Notes:
            - Identity for numbers. Kept for symmetry with `__neg__` and so
              `+x` inside an expression is still a Nu term.

        Yields:
            The value unchanged. INVALID when self is a sentinel.

        Example:
            >>> nu.run(+nu.Int(-4))[0]
            -4
        """
        from nu.core import Pos

        return Int(Pos(self))

    def __abs__(self) -> Int:
        """Absolute value of self.

        Yields:
            The magnitude. INVALID when self is a sentinel.

        Example:
            >>> nu.run(abs(nu.Int(-4)))[0]
            4
        """
        from nu.core import Abs

        return Int(Abs(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: IntArg | FloatArg) -> Bool:
        """Self strictly greater than other.

        Args:
            other: the value to compare against. Any Int, Float, or plain
                number.

        Yields:
            True when self is greater, False otherwise. INVALID when either
            operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(5) > nu.Int(3))[0]
            True
        """
        from nu.core import Gt

        from .bool_ import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: IntArg | FloatArg) -> Bool:
        """Self strictly less than other.

        Args:
            other: the value to compare against. Any Int, Float, or plain
                number.

        Yields:
            True when self is less, False otherwise. INVALID when either
            operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(5) < nu.Int(3))[0]
            False
        """
        from nu.core import Lt

        from .bool_ import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: IntArg | FloatArg) -> Bool:
        """Self greater than or equal to other.

        Args:
            other: the value to compare against. Any Int, Float, or plain
                number.

        Yields:
            True when self is greater or equal, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(5) >= nu.Int(5))[0]
            True
        """
        from nu.core import Ge

        from .bool_ import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: IntArg | FloatArg) -> Bool:
        """Self less than or equal to other.

        Args:
            other: the value to compare against. Any Int, Float, or plain
                number.

        Yields:
            True when self is less or equal, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(3) <= nu.Int(5))[0]
            True
        """
        from nu.core import Le

        from .bool_ import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: IntArg | FloatArg) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the value to compare against. Compared numerically, so
                `Int(1) == 1.0` is True.

        Notes:
            - Value equality, not identity. Use `is_` for identity.

        Yields:
            True when the values compare equal, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(1) == 1.0)[0]
            True
        """
        from nu.core import Eq

        from .bool_ import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: IntArg | FloatArg) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the value to compare against. Compared numerically.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the values differ, False otherwise. INVALID when either
            operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(1) != nu.Int(2))[0]
            True
        """
        from nu.core import Ne

        from .bool_ import Bool

        return Bool(Ne(self, other))

    def is_(self, other: IntArg | FloatArg) -> Bool:
        """Identity comparison: self is other.

        Args:
            other: the value to compare identity against.

        Notes:
            - Object identity, not value equality. For scalar comparison use
              `==` instead.
            - Named `is_` because `is` is a Python keyword and cannot be a
              method name.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise. For small ints Python interns values, so
            distinct Int literals of equal value can still test identical.

        Example:
            >>> nu.run(nu.Int(1).is_(1.0))[0]
            False

            >>> nu.run(nu.Int(1) == 1.0)[0]
            True
        """
        from nu.core import Is

        from .bool_ import Bool

        return Bool(Is(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg | IntArg) -> Bool:
        """Logical AND of self and other.

        Args:
            other: the value to AND with self. Coerced to Bool by truthiness
                (zero is False, everything else is True).

        Notes:
            - Named `and_` because `and` is a Python keyword.
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.
            - Bitwise AND is `bitand`, not this.

        Yields:
            True when both operands are truthy, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(1).and_(nu.Int(0)))[0]
            False
        """
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: BoolArg | IntArg) -> Bool:
        """Logical OR of self and other.

        Args:
            other: the value to OR with self. Coerced to Bool by truthiness.

        Notes:
            - Named `or_` because `or` is a Python keyword.
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.
            - Bitwise OR is `bitor`, not this.

        Yields:
            True when either operand is truthy, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(0).or_(nu.Int(5)))[0]
            True
        """
        from nu.core import Or

        from .bool_ import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT of self.

        Notes:
            - Named `not_` because `not` is a Python keyword.
            - Zero yields True, every other value yields False.
            - Bitwise NOT is `bitnot`, not this.

        Yields:
            True when self is zero, False otherwise. INVALID when self is a
            sentinel.

        Example:
            >>> nu.run(nu.Int(0).not_())[0]
            True
        """
        from nu.core import Not

        from .bool_ import Bool

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Cast self to Bool.

        Notes:
            - Zero becomes False, every other value becomes True, matching
              Python's truthiness rule.
            - Named `bool_` because `bool` is a Python builtin and shadowing
              it as a method name would be misleading.

        Yields:
            True when self is non-zero, False when self is zero. INVALID when
            self is a sentinel.

        Example:
            >>> nu.run(nu.Int(5).bool_())[0]
            True
        """
        from nu.core import ToBool

        from .bool_ import Bool

        return Bool(ToBool(self))

    # =========================================================================
    # BITWISE
    # =========================================================================

    def bitand(self, other: IntArg) -> Int:
        """Bitwise AND: self & other.

        Args:
            other: the integer to AND with self, bit by bit.

        Notes:
            - Named form rather than `__and__` to keep the logical `and_`
              and the bitwise AND from stepping on each other across the
              Bool / Int split.

        Yields:
            The bitwise AND. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(0b1100).bitand(0b1010))[0]
            8
        """
        from nu.core import BitAnd

        return Int(BitAnd(self, other))

    def bitor(self, other: IntArg) -> Int:
        """Bitwise OR: self | other.

        Args:
            other: the integer to OR with self, bit by bit.

        Notes:
            - Named form rather than `__or__`, symmetric with `bitand`.

        Yields:
            The bitwise OR. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(0b1100).bitor(0b1010))[0]
            14
        """
        from nu.core import BitOr

        return Int(BitOr(self, other))

    def __xor__(self, other: IntArg) -> Int:
        """Bitwise XOR: self ^ other.

        Args:
            other: the integer to XOR with self, bit by bit.

        Yields:
            The bitwise XOR. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Int(0b1100) ^ nu.Int(0b1010))[0]
            6
        """
        from nu.core import BitXor

        return Int(BitXor(self, other))

    def __rxor__(self, other: IntArg) -> Int:
        """Bitwise XOR: other ^ self, with self on the right.

        Args:
            other: the integer on the left of the `^`.

        Notes:
            - Reached only when the left operand is a plain Python int.

        Yields:
            The bitwise XOR. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(0b1100 ^ nu.Int(0b1010))[0]
            6
        """
        from nu.core import BitXor

        return Int(BitXor(other, self))

    def bitnot(self) -> Int:
        """Bitwise NOT: ~self.

        Notes:
            - Named form rather than `__invert__`, symmetric with `bitand`
              and `bitor`.
            - Two's complement, so `bitnot(x)` equals `-x - 1`.

        Yields:
            The bitwise complement. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Int(5).bitnot())[0]
            -6
        """
        from nu.core import BitNot

        return Int(BitNot(self))

    def __lshift__(self, other: IntArg) -> Int:
        """Left shift: self shifted left by other bits.

        Args:
            other: the shift amount in bits. Must be non-negative at
                evaluation time.

        Notes:
            - Fills the low bits with zeros. Equivalent to `self * 2**other`
              for non-negative shifts.

        Yields:
            The shifted value. INVALID when either operand is a sentinel.
            Raises at evaluation time when the shift amount is negative.

        Example:
            >>> nu.run(nu.Int(1) << nu.Int(4))[0]
            16
        """
        from nu.core import LShift

        return Int(LShift(self, other))

    def __rlshift__(self, other: IntArg) -> Int:
        """Left shift: other shifted left by self bits.

        Args:
            other: the value on the left of the `<<`, the value being
                shifted.

        Notes:
            - Fills the low bits with zeros.
            - Reached only when the left operand is a plain Python int.

        Yields:
            The shifted value. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(1 << nu.Int(4))[0]
            16
        """
        from nu.core import LShift

        return Int(LShift(other, self))

    def __rshift__(self, other: IntArg) -> Int:
        """Right shift: self shifted right by other bits.

        Args:
            other: the shift amount in bits. Must be non-negative at
                evaluation time.

        Notes:
            - Arithmetic shift, so the sign bit is preserved: shifting a
              negative number stays negative.
            - Equivalent to `self // 2**other` for non-negative shifts.

        Yields:
            The shifted value. INVALID when either operand is a sentinel.
            Raises at evaluation time when the shift amount is negative.

        Example:
            >>> nu.run(nu.Int(16) >> nu.Int(2))[0]
            4
        """
        from nu.core import RShift

        return Int(RShift(self, other))

    def __rrshift__(self, other: IntArg) -> Int:
        """Right shift: other shifted right by self bits.

        Args:
            other: the value on the left of the `>>`, the value being
                shifted.

        Notes:
            - Arithmetic shift, sign-preserving.
            - Reached only when the left operand is a plain Python int.

        Yields:
            The shifted value. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(16 >> nu.Int(2))[0]
            4
        """
        from nu.core import RShift

        return Int(RShift(other, self))
