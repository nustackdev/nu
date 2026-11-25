"""None_ - none interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Surface


if TYPE_CHECKING:
    from nu.forms import Bool
    from nu.lang import NoneArg


__all__ = [
    "NoneSurface",
]


class NoneSurface(Surface):
    """The methods of ``None_``. No slot holds one, so only the form carries them."""

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: NoneArg) -> Bool:
        """Logical AND of self and other.

        Args:
            other: the value to AND with self. Coerced to Bool by
                truthiness; `None` is always falsy.

        Notes:
            - Short-circuits like Python: the right operand is only
              evaluated when the left does not already decide the result.

        Yields:
            False, since self is always falsy.

        Example:
            >>> nu.run(nu.None_().and_(nu.None_()))[0]
            False
        """
        from nu.core import And
        from nu.forms import Bool

        return Bool(And(self, other))

    def or_(self, other: NoneArg) -> Bool:
        """Logical OR of self and other.

        Args:
            other: the value to OR with self. Coerced to Bool by
                truthiness; `None` is always falsy.

        Notes:
            - Short-circuits like Python: the right operand is only
              evaluated when the left does not already decide the result.

        Yields:
            True when other is truthy, False otherwise since self never is.

        Example:
            >>> nu.run(nu.None_().or_(nu.None_()))[0]
            False
        """
        from nu.core import Or
        from nu.forms import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT of self.

        Notes:
            - Self is always falsy, so this always yields True.

        Yields:
            True.

        Example:
            >>> nu.run(nu.None_().not_())[0]
            True
        """
        from nu.core import Not
        from nu.forms import Bool

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Cast self to Bool.

        Notes:
            - `None` is falsy under Python's truthiness rule, so this
              always yields False.

        Yields:
            False.

        Example:
            >>> nu.run(nu.None_().bool_())[0]
            False
        """
        from nu.core import ToBool
        from nu.forms import Bool

        return Bool(ToBool(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __eq__(self, other: object) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the value to compare against. Any type; equality never
                raises for mismatched types, it's just False.

        Yields:
            True when other is also None, False otherwise.

        Example:
            >>> nu.run(nu.None_() == nu.None_())[0]
            True
        """
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: object) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the value to compare against.

        Yields:
            True when other is not None, False otherwise.

        Example:
            >>> nu.run(nu.None_() != 0)[0]
            True
        """
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))
