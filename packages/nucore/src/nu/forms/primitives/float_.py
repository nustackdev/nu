"""Float - float interface.

Float = Form[float] + arithmetic + comparison + logical.
"""

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
    """Float interface. Numeric + comparable + logical.

    Notes:
        - Arithmetic against an Int, or a plain int or float, stays Float.
          There's no promotion to track since Float is already the wider
          type.
        - Division `/` and floor division `//` both stay Float. Unlike Int,
          where `/` promotes to Float but `//` stays Int, here every
          arithmetic operator returns Float.
        - Comparison operators yield Bool. Chained comparisons like
          `a > b > c` do not build a single term; write them as
          `And(a > b, b > c)`.
        - `nan` compares False against everything, including itself, so
          `Float(nan) == Float(nan)` is False.
        - Logical operators are the named forms `and_`, `or_`, `not_`.

    Example:
        >>> nu.run(nu.Float(2.5) * nu.Float(4.0))[0]
        10.0
    """

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: IntArg | FloatArg) -> Float:
        """Sum of self and other.

        Args:
            other: the value to add to self. Int, float, or plain int all
                stay Float.

        Yields:
            The sum. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Float(2.5) + nu.Float(1.5))[0]
            4.0

            >>> nu.run(nu.Float(2.0) + 1)[0]
            3.0
        """
        from nu.core import Add

        return Float(Add(self, other))

    def __radd__(self, other: IntArg | FloatArg) -> Float:
        """Sum of other and self, with self on the right.

        Args:
            other: the value on the left of the `+`.

        Notes:
            - Reached only when the left operand is a plain Python int or
              float. A Nu Int or Float on the left goes through its own
              `__add__` first and never lands here.

        Yields:
            The sum. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(1 + nu.Float(2.5))[0]
            3.5
        """
        from nu.core import Add

        return Float(Add(other, self))

    def __sub__(self, other: IntArg | FloatArg) -> Float:
        """Self minus other.

        Args:
            other: the value to subtract from self.

        Yields:
            The difference. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Float(10.0) - nu.Float(3.5))[0]
            6.5
        """
        from nu.core import Sub

        return Float(Sub(self, other))

    def __rsub__(self, other: IntArg | FloatArg) -> Float:
        """Other minus self, with self on the right.

        Args:
            other: the value on the left of the `-`, the minuend.

        Notes:
            - Reached only when the left operand is a plain Python int or
              float. A Nu Int or Float on the left uses its own `__sub__`
              instead.

        Yields:
            The difference. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(10 - nu.Float(3.5))[0]
            6.5
        """
        from nu.core import Sub

        return Float(Sub(other, self))

    def __mul__(self, other: IntArg | FloatArg) -> Float:
        """Product of self and other.

        Args:
            other: the value to multiply self by.

        Yields:
            The product. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Float(6.0) * nu.Float(7.0))[0]
            42.0
        """
        from nu.core import Mul

        return Float(Mul(self, other))

    def __rmul__(self, other: IntArg | FloatArg) -> Float:
        """Product of other and self, with self on the right.

        Args:
            other: the value on the left of the `*`.

        Notes:
            - Reached only when the left operand is a plain Python int or
              float. A Nu Int or Float on the left uses its own `__mul__`
              instead.

        Yields:
            The product. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(3 * nu.Float(4.0))[0]
            12.0
        """
        from nu.core import Mul

        return Float(Mul(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> Float:
        """Self divided by other.

        Args:
            other: the divisor.

        Notes:
            - A zero divisor is not caught here; the underlying Div raises
              at evaluation time. Unlike IEEE 754, this does not yield
              `inf`.

        Yields:
            The quotient. INVALID when either operand is a sentinel. Raises
            at evaluation time when the divisor is zero.

        Example:
            >>> nu.run(nu.Float(7.0) / nu.Float(2.0))[0]
            3.5
        """
        from nu.core import Div

        return Float(Div(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> Float:
        """Other divided by self, with self as the divisor.

        Args:
            other: the numerator, on the left of the `/`.

        Notes:
            - Reached only when the left operand is a plain Python int or
              float.

        Yields:
            The quotient. INVALID when either operand is a sentinel. Raises
            at evaluation time when self evaluates to zero.

        Example:
            >>> nu.run(10 / nu.Float(4.0))[0]
            2.5
        """
        from nu.core import Div

        return Float(Div(other, self))

    def __floordiv__(self, other: IntArg | FloatArg) -> Float:
        """Self floor-divided by other.

        Args:
            other: the divisor.

        Notes:
            - Stays Float even though the result is a whole number, unlike
              Int `//` which returns Int. Rounds toward negative infinity,
              as Python's `//` does.

        Yields:
            The floored quotient. INVALID when either operand is a
            sentinel. Raises at evaluation time when the divisor is zero.

        Example:
            >>> nu.run(nu.Float(7.5) // nu.Float(2.0))[0]
            3.0

            >>> nu.run(nu.Float(-7.5) // nu.Float(2.0))[0]
            -4.0
        """
        from nu.core import FloorDiv

        return Float(FloorDiv(self, other))

    def __rfloordiv__(self, other: IntArg | FloatArg) -> Float:
        """Other floor-divided by self, with self as the divisor.

        Args:
            other: the numerator, on the left of the `//`.

        Notes:
            - Rounds toward negative infinity, as Python's `//` does.
            - Reached only when the left operand is a plain Python int or
              float.

        Yields:
            The floored quotient. INVALID when either operand is a
            sentinel.

        Example:
            >>> nu.run(-7.5 // nu.Float(2.0))[0]
            -4.0
        """
        from nu.core import FloorDiv

        return Float(FloorDiv(other, self))

    def __mod__(self, other: IntArg | FloatArg) -> Float:
        """Self modulo other.

        Args:
            other: the divisor.

        Notes:
            - The result's sign follows the divisor, as Python's `%` does,
              so `-7.5 % 3.0` is `1.5` and not `-1.5`.

        Yields:
            The remainder. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Float(-7.5) % nu.Float(3.0))[0]
            1.5
        """
        from nu.core import Mod

        return Float(Mod(self, other))

    def __rmod__(self, other: IntArg | FloatArg) -> Float:
        """Other modulo self, with self as the divisor.

        Args:
            other: the value being divided, on the left of the `%`.

        Notes:
            - The result's sign follows the divisor, which here is self.
            - Reached only when the left operand is a plain Python int or
              float.

        Yields:
            The remainder. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(-7.5 % nu.Float(3.0))[0]
            1.5
        """
        from nu.core import Mod

        return Float(Mod(other, self))

    def __pow__(self, other: IntArg | FloatArg) -> Float:
        """Self raised to the other power.

        Args:
            other: the exponent.

        Notes:
            - Unlike Int, a negative or fractional exponent does not raise.
              A negative base with a fractional exponent yields a Python
              complex number rather than raising, matching `**`.

        Yields:
            The power. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Float(2.0) ** nu.Float(10.0))[0]
            1024.0
        """
        from nu.core import Pow

        return Float(Pow(self, other))

    def __rpow__(self, other: IntArg | FloatArg) -> Float:
        """Other raised to the self power, with self as the exponent.

        Args:
            other: the base, on the left of the `**`.

        Notes:
            - Reached only when the base is a plain Python int or float.

        Yields:
            The power. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(2.0 ** nu.Float(10.0))[0]
            1024.0
        """
        from nu.core import Pow

        return Float(Pow(other, self))

    def __neg__(self) -> Float:
        """Negation of self.

        Yields:
            The negation. INVALID when self is a sentinel.

        Example:
            >>> nu.run(-nu.Float(4.5))[0]
            -4.5
        """
        from nu.core import Neg

        return Float(Neg(self))

    def __pos__(self) -> Float:
        """Self unchanged.

        Notes:
            - Identity for numbers. Kept for symmetry with `__neg__` and so
              `+x` inside an expression is still a Nu term.

        Yields:
            The value unchanged. INVALID when self is a sentinel.

        Example:
            >>> nu.run(+nu.Float(-4.5))[0]
            -4.5
        """
        from nu.core import Pos

        return Float(Pos(self))

    def __abs__(self) -> Float:
        """Absolute value of self.

        Yields:
            The magnitude. INVALID when self is a sentinel.

        Example:
            >>> nu.run(abs(nu.Float(-4.5)))[0]
            4.5
        """
        from nu.core import Abs

        return Float(Abs(self))

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
            operand is a sentinel. False whenever either side is nan.

        Example:
            >>> nu.run(nu.Float(5.5) > nu.Float(3.0))[0]
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
            operand is a sentinel. False whenever either side is nan.

        Example:
            >>> nu.run(nu.Float(5.5) < nu.Float(3.0))[0]
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
            True when self is greater or equal, False otherwise. INVALID
            when either operand is a sentinel. False whenever either side
            is nan.

        Example:
            >>> nu.run(nu.Float(5.5) >= nu.Float(5.5))[0]
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
            either operand is a sentinel. False whenever either side is
            nan.

        Example:
            >>> nu.run(nu.Float(3.0) <= nu.Float(5.5))[0]
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
                `Float(1.0) == 1` is True.

        Notes:
            - Value equality, not identity. Use `is_` for identity.
            - `nan` is never equal to anything, including another nan.

        Yields:
            True when the values compare equal, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Float(1.0) == 1)[0]
            True

            >>> nu.run(nu.Float(float("nan")) == nu.Float(float("nan")))[0]
            False
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
            - `nan` is unequal to everything, including another nan.

        Yields:
            True when the values differ, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Float(1.0) != nu.Float(2.0))[0]
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
            - Object identity, not value equality. For scalar comparison
              use `==` instead.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise.

        Example:
            >>> nu.run(nu.Float(1.0).is_(1.0))[0]
            True
        """
        from nu.core import Is

        from .bool_ import Bool

        return Bool(Is(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg | FloatArg) -> Bool:
        """Logical AND of self and other.

        Args:
            other: the value to AND with self. Coerced to Bool by
                truthiness (zero is False, everything else is True).

        Notes:
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.

        Yields:
            True when both operands are truthy, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Float(1.5).and_(nu.Float(0.0)))[0]
            False
        """
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: BoolArg | FloatArg) -> Bool:
        """Logical OR of self and other.

        Args:
            other: the value to OR with self. Coerced to Bool by
                truthiness.

        Notes:
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.

        Yields:
            True when either operand is truthy, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Float(0.0).or_(nu.Float(5.5)))[0]
            True
        """
        from nu.core import Or

        from .bool_ import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT of self.

        Notes:
            - Zero yields True, every other value yields False.

        Yields:
            True when self is zero, False otherwise. INVALID when self is a
            sentinel.

        Example:
            >>> nu.run(nu.Float(0.0).not_())[0]
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

        Yields:
            True when self is non-zero, False when self is zero. INVALID
            when self is a sentinel.

        Example:
            >>> nu.run(nu.Float(5.5).bool_())[0]
            True
        """
        from nu.core import ToBool

        from .bool_ import Bool

        return Bool(ToBool(self))
