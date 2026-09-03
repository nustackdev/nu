"""Bool - boolean interface.

Bool = Form[bool] + logical + comparison.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.lang import BoolArg


__all__ = [
    "Bool",
]


class Bool(Form, TypedNu[bool]):
    """Boolean interface. Logical + comparable.

    Notes:
        - Logical operators are the named forms `and_`, `or_`, `not_`. Python
          reserves `and`, `or`, `not` as keywords, so they cannot be method
          names.
        - Both operands are always evaluated; there is no Python-style
          short-circuit at the tree level.
        - Comparison operators yield Bool too, treating False as less than
          True.

    Example:
        >>> nu.run(nu.Bool(True).and_(nu.Bool(False)))[0]
        False
    """

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg) -> Bool:
        """Logical AND of self and other.

        Args:
            other: the value to AND with self. Any Bool or plain bool.

        Notes:
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.

        Yields:
            True when both operands are True, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bool(True).and_(nu.Bool(False)))[0]
            False
        """
        from nu.core import And

        return Bool(And(self, other))

    def or_(self, other: BoolArg) -> Bool:
        """Logical OR of self and other.

        Args:
            other: the value to OR with self. Any Bool or plain bool.

        Notes:
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.

        Yields:
            True when either operand is True, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bool(False).or_(nu.Bool(True)))[0]
            True
        """
        from nu.core import Or

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT of self.

        Yields:
            True when self is False, False when self is True. INVALID when
            self is a sentinel.

        Example:
            >>> nu.run(nu.Bool(True).not_())[0]
            False
        """
        from nu.core import Not

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Cast self to Bool.

        Notes:
            - Identity for a value that is already Bool. Kept for
              consistency with `Int.bool_` and `Float.bool_`.

        Yields:
            self, unchanged. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bool(True).bool_())[0]
            True
        """
        from nu.core import ToBool

        return Bool(ToBool(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BoolArg) -> Bool:
        """Self strictly greater than other.

        Args:
            other: the value to compare against. Any Bool or plain bool,
                with False less than True.

        Yields:
            True when self is True and other is False, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bool(True) > nu.Bool(False))[0]
            True
        """
        from nu.core import Gt

        return Bool(Gt(self, other))

    def __lt__(self, other: BoolArg) -> Bool:
        """Self strictly less than other.

        Args:
            other: the value to compare against. Any Bool or plain bool,
                with False less than True.

        Yields:
            True when self is False and other is True, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bool(True) < nu.Bool(False))[0]
            False
        """
        from nu.core import Lt

        return Bool(Lt(self, other))

    def __ge__(self, other: BoolArg) -> Bool:
        """Self greater than or equal to other.

        Args:
            other: the value to compare against. Any Bool or plain bool,
                with False less than True.

        Yields:
            True when self is at least other, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bool(True) >= nu.Bool(True))[0]
            True
        """
        from nu.core import Ge

        return Bool(Ge(self, other))

    def __le__(self, other: BoolArg) -> Bool:
        """Self less than or equal to other.

        Args:
            other: the value to compare against. Any Bool or plain bool,
                with False less than True.

        Yields:
            True when self is at most other, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bool(False) <= nu.Bool(True))[0]
            True
        """
        from nu.core import Le

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: BoolArg) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the value to compare against. Any Bool or plain bool.

        Notes:
            - Value equality, not identity. Use `is_` for identity.

        Yields:
            True when the values compare equal, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bool(True) == True)[0]
            True
        """
        from nu.core import Eq

        return Bool(Eq(self, other))

    def __ne__(self, other: BoolArg) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the value to compare against. Any Bool or plain bool.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the values differ, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bool(True) != nu.Bool(False))[0]
            True
        """
        from nu.core import Ne

        return Bool(Ne(self, other))

    def is_(self, other: BoolArg) -> Bool:
        """Identity comparison: self is other.

        Args:
            other: the value to compare identity against.

        Notes:
            - Object identity, not value equality. For scalar comparison use
              `==` instead.
            - Python interns True and False, so any two Bool True values
              test identical.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise.

        Example:
            >>> nu.run(nu.Bool(True).is_(True))[0]
            True
        """
        from nu.core import Is

        return Bool(Is(self, other))
