"""None_ - none interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.lang import NoneArg

    from .bool_ import Bool


__all__ = [
    "None_",
]


class None_(Form, TypedNu[None]):  # noqa: N801
    """None interface. Logical only.

    Notes:
        - Wraps Python's `None`. It's the typical return of an effect-only
          Command, one that runs for a side effect and yields nothing
          meaningful (`sleep`, `inc`, `dec`).
        - `==` / `!=` build an `Eq` / `Ne` term like every other Form, so
          `x == nu.None_()` asks whether x yields None at run time. There is
          no `is_`.
        - EMPTY is a distinct sentinel from None: an address that resolved
          to no value at all, not one that resolved to the value `None`.

    Example:
        >>> nu.run(nu.None_())[0] is None
        True
    """

    def __init__(self, source: object = None) -> None:
        """Wrap source as a None_ term.

        Args:
            source: the value to wrap. Defaults to `None`.

        Example:
            >>> nu.run(nu.None_())[0] is None
            True
        """
        super().__init__(source)

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
            False, since self is always falsy. INVALID when either operand
            is a sentinel.

        Example:
            >>> nu.run(nu.None_().and_(nu.None_()))[0]
            False
        """
        from nu.core import And

        from .bool_ import Bool

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
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.None_().or_(nu.None_()))[0]
            False
        """
        from nu.core import Or

        from .bool_ import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT of self.

        Notes:
            - Self is always falsy, so this always yields True.

        Yields:
            True. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.None_().not_())[0]
            True
        """
        from nu.core import Not

        from .bool_ import Bool

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Cast self to Bool.

        Notes:
            - `None` is falsy under Python's truthiness rule, so this
              always yields False.

        Yields:
            False. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.None_().bool_())[0]
            False
        """
        from nu.core import ToBool

        from .bool_ import Bool

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
            True when other is also None, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.None_() == nu.None_())[0]
            True
        """
        from nu.core import Eq

        from .bool_ import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: object) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the value to compare against.

        Yields:
            True when other is not None, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.None_() != 0)[0]
            True
        """
        from nu.core import Ne

        from .bool_ import Bool

        return Bool(Ne(self, other))
