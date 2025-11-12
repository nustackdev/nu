"""Operator overloading for RValue expressions.

This mixin provides Python operator syntax for building binary operation expressions.
All operators automatically convert literals to LiteralValue.

Safe vs Unsafe Operations:
    Safe (operator syntax):
    - Arithmetic: +, -, *, /, %, **
    - Comparison: >, <, >=, <=
    - Logical (safe methods): .and_(), .or_()
    - Equality (safe methods): .eq(), .ne()

    Unsafe (raise TypeError):
    - == (use .eq() instead)
    - != (use .ne() instead)
    - & (use .and_() instead - prevents Python's short-circuit semantics)
    - | (use .or_() instead - prevents Python's short-circuit semantics)
    - bool() (use explicit comparison instead)
    - ~ (not supported)

Example:
    >>> price = item.price.get()
    >>> # Arithmetic
    >>> total = price + 10  # AddOp
    >>> discounted = price * 0.9  # MulOp
    >>> # Comparison (safe)
    >>> is_expensive = price > 100  # GtOp
    >>> is_exact = price.eq(100)  # EqOp
    >>> # Logical (safe methods)
    >>> valid = price.and_(price < 1000)  # AndOp
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..term import RValue
    from .binary_ops import (
        AddOp,
        AndOp,
        DivOp,
        EqOp,
        GeOp,
        GtOp,
        LeOp,
        LtOp,
        ModOp,
        MulOp,
        NeOp,
        OrOp,
        PowOp,
        SubOp,
    )


class ErgonomicsMixin[T]:
    """Operator overloading mixin for RValue expressions."""

    def _operand(self, other: object) -> RValue:
        """Convert operand to RValue.

        Args:
            other: Right operand (RValue or literal)

        Returns:
            RValue (either as-is, or wrapped in LiteralValue)
        """
        from .literal_value import literal

        return literal(other)

    # =========================================================================
    # SAFETY - Blocked unsafe operations
    # =========================================================================

    def __bool__(self) -> bool:
        """Convert to bool is unsafe in DSL context.

        Raises:
            TypeError: Cannot convert expression to bool.
                Use explicit comparison: expr > 0, expr == value, etc.
        """
        raise TypeError(
            "Cannot convert expression to bool. "
            "Use explicit comparison: expr > 0, expr == value, or use and_() / or_() methods."
        )

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        """Equality check is disabled to prevent DSL/Python semantic confusion.

        Raises:
            TypeError: Use eq(other) method to create equality expression.
        """
        raise TypeError(
            "Cannot use == directly on expressions. Use .eq(other) method instead. "
            "This prevents Python's default object identity comparison semantics."
        )

    def __ne__(self, other: object) -> bool:  # type: ignore[override]
        """Not-equal check is disabled to prevent DSL/Python semantic confusion.

        Raises:
            TypeError: Use ne(other) method to create not-equal expression.
        """
        raise TypeError("Cannot use != directly on expressions. Use .ne(other) method instead.")

    def __and__(self, other: object) -> AndOp[T]:  # type: ignore[override]
        """Bitwise AND is unsafe; use and_() method instead.

        Raises:
            TypeError: Use and_(other) method for logical AND operation.
        """
        raise TypeError(
            "Cannot use & operator on expressions. Use .and_(other) method instead. "
            "This prevents accidental use of Python's short-circuit semantics."
        )

    def __rand__(self, other: object) -> AndOp[T]:  # type: ignore[override]
        """Right bitwise AND is unsafe; use and_() method instead.

        Raises:
            TypeError: Use and_(other) method for logical AND operation.
        """
        raise TypeError("Cannot use & operator on expressions. Use .and_(other) method instead.")

    def __or__(self, other: object) -> OrOp[T]:  # type: ignore[override]
        """Bitwise OR is unsafe; use or_() method instead.

        Raises:
            TypeError: Use or_(other) method for logical OR operation.
        """
        raise TypeError(
            "Cannot use | operator on expressions. Use .or_(other) method instead. "
            "This prevents accidental use of Python's short-circuit semantics."
        )

    def __ror__(self, other: object) -> OrOp[T]:  # type: ignore[override]
        """Right bitwise OR is unsafe; use or_() method instead.

        Raises:
            TypeError: Use or_(other) method for logical OR operation.
        """
        raise TypeError("Cannot use | operator on expressions. Use .or_(other) method instead.")

    def __invert__(self) -> None:
        """Logical NOT (~) is not supported.

        Raises:
            TypeError: Logical NOT is not supported in DSL.
        """
        raise TypeError(
            "Logical NOT (~) is not supported. Use explicit comparison instead: expr == False, expr > 0, etc."
        )

    # =========================================================================
    # ARITHMETIC OPERATIONS
    # =========================================================================

    def __add__(self, other: object) -> AddOp[T]:
        """Addition: self + other."""
        from .binary_ops import AddOp

        return AddOp(self, self._operand(other))

    def __radd__(self, other: object) -> AddOp[T]:
        """Right addition: other + self."""
        from .binary_ops import AddOp

        return AddOp(self._operand(other), self)

    def __sub__(self, other: object) -> SubOp[T]:
        """Subtraction: self - other."""
        from .binary_ops import SubOp

        return SubOp(self, self._operand(other))

    def __rsub__(self, other: object) -> SubOp[T]:
        """Right subtraction: other - self."""
        from .binary_ops import SubOp

        return SubOp(self._operand(other), self)

    def __mul__(self, other: object) -> MulOp[T]:
        """Multiplication: self * other."""
        from .binary_ops import MulOp

        return MulOp(self, self._operand(other))

    def __rmul__(self, other: object) -> MulOp[T]:
        """Right multiplication: other * self."""
        from .binary_ops import MulOp

        return MulOp(self._operand(other), self)

    def __truediv__(self, other: object) -> DivOp[T]:
        """Division: self / other."""
        from .binary_ops import DivOp

        return DivOp(self, self._operand(other))

    def __rtruediv__(self, other: object) -> DivOp[T]:
        """Right division: other / self."""
        from .binary_ops import DivOp

        return DivOp(self._operand(other), self)

    def __mod__(self, other: object) -> ModOp[T]:
        """Modulo: self % other."""
        from .binary_ops import ModOp

        return ModOp(self, self._operand(other))

    def __rmod__(self, other: object) -> ModOp[T]:
        """Right modulo: other % self."""
        from .binary_ops import ModOp

        return ModOp(self._operand(other), self)

    def __pow__(self, other: object) -> PowOp[T]:
        """Power: self ** other."""
        from .binary_ops import PowOp

        return PowOp(self, self._operand(other))

    def __rpow__(self, other: object) -> PowOp[T]:
        """Right power: other ** self."""
        from .binary_ops import PowOp

        return PowOp(self._operand(other), self)

    # =========================================================================
    # COMPARISON OPERATIONS
    # =========================================================================

    def __gt__(self, other: object) -> GtOp[bool]:
        """Greater than: self > other."""
        from .binary_ops import GtOp

        return GtOp(self, self._operand(other))

    def __lt__(self, other: object) -> LtOp[bool]:
        """Less than: self < other."""
        from .binary_ops import LtOp

        return LtOp(self, self._operand(other))

    def __ge__(self, other: object) -> GeOp[bool]:
        """Greater than or equal: self >= other."""
        from .binary_ops import GeOp

        return GeOp(self, self._operand(other))

    def __le__(self, other: object) -> LeOp[bool]:
        """Less than or equal: self <= other."""
        from .binary_ops import LeOp

        return LeOp(self, self._operand(other))

    def eq(self, other: object) -> EqOp[bool]:
        """Equality: self == other (safe method).

        Use this instead of == operator to avoid Python's default comparison semantics.

        Args:
            other: Value to compare (RValue or literal)

        Returns:
            EqOp expression
        """
        from .binary_ops import EqOp

        return EqOp(self, self._operand(other))

    def ne(self, other: object) -> NeOp[bool]:
        """Not-equal: self != other (safe method).

        Use this instead of != operator to avoid Python's default comparison semantics.

        Args:
            other: Value to compare (RValue or literal)

        Returns:
            NeOp expression
        """
        from .binary_ops import NeOp

        return NeOp(self, self._operand(other))

    # =========================================================================
    # LOGICAL OPERATIONS (Safe methods: and_(), or_())
    # =========================================================================

    def and_(self, other: object) -> AndOp[T]:
        """Logical AND (safe method).

        Use this method instead of & operator to avoid Python's short-circuit semantics
        in the DSL context.

        Args:
            other: Right operand (RValue or literal)

        Returns:
            AndOp expression
        """
        from .binary_ops import AndOp

        return AndOp(self, self._operand(other))

    def or_(self, other: object) -> OrOp[T]:
        """Logical OR (safe method).

        Use this method instead of | operator to avoid Python's short-circuit semantics
        in the DSL context.

        Args:
            other: Right operand (RValue or literal)

        Returns:
            OrOp expression
        """
        from .binary_ops import OrOp

        return OrOp(self, self._operand(other))
