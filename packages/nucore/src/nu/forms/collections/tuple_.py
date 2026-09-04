"""Tuple - tuple interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from typing_extensions import TypeVarTuple, Unpack

from nu.lang import TypedNu

from .abc import SequenceForm
from .abc.sequence_interactions import TupleCreate, TupleOf


if TYPE_CHECKING:
    from nu.lang import Arg, IntArg, Nu, TupleArg

    from ..primitives import Any, Bool
    from .list_ import List


__all__ = [
    "Tuple",
]


Ts = TypeVarTuple("Ts")


class Tuple(
    SequenceForm[tuple[Unpack[Ts]], object, "List[object]", "Any"],
    TypedNu[tuple[Unpack[Ts]]],
    Generic[Unpack[Ts]],
):
    """Tuple interface. Immutable sequence + comparable.

    Notes:
        - No mutation methods: no `append`, `insert`, `pop`, `remove`. Every
          op that would change contents yields a new Tuple instead, unlike
          List which mutates in place.
        - Arity is fixed at construction; there's no way to grow or shrink
          one after `of`/`create`.
        - Indexing with an out-of-range int raises at evaluation time,
          matching Python. Slicing never raises, bounds are clamped.
        - `+` and `*` concatenate and repeat like List's, but always
          produce a new Tuple.
        - Slicing yields Tuple; iterating or mapping over the whole
          collection yields List, matching `_wrap_iterable_result`.

    Example:
        >>> nu.run(nu.Tuple.of(1, 2, 3))[0]
        (1, 2, 3)
    """

    @classmethod
    def create(cls) -> Tuple[Unpack[Ts]]:
        """Empty tuple.

        Yields:
            `()`.

        Example:
            >>> nu.run(nu.Tuple.create())[0]
            ()
        """
        return cls(TupleCreate())

    @classmethod
    def of(cls, *items: Arg) -> Tuple:
        """Tuple built from positional item expressions.

        Args:
            items: the expressions to evaluate and pack, in order.

        Notes:
            - Each argument is evaluated in the current context and packed:
              `Tuple.of(x, y, z)` yields `(<x>, <y>, <z>)`. Sibling to
              `List.of` and `Dict.of`.

        Yields:
            The packed tuple. INVALID when any item resolves to a sentinel.

        Example:
            >>> nu.run(nu.Tuple.of(1, 2, 3))[0]
            (1, 2, 3)
        """
        return cls(TupleOf(*items))

    def _wrap_sliceable_result(self, operand: Nu) -> Tuple:
        """Wrap operand as Tuple for slice results."""
        return Tuple(operand)

    def _wrap_iterable_result(self, operand: Nu) -> List:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        """Wrap operand as Any element."""
        from ..primitives import Any

        return Any(operand)

    # =========================================================================
    # ARITHMETIC (concatenation / repeat): new value, no mutation
    # =========================================================================

    def __add__(self, other: TupleArg[Unpack[Ts]]) -> Tuple:
        """Concatenation of self and other.

        Args:
            other: the tuple to append after self.

        Yields:
            A new tuple with self's items followed by other's. INVALID when
            either operand is not a Tuple or is a sentinel.

        Example:
            >>> nu.run(nu.Tuple.of(1, 2) + nu.Tuple.of(3, 4))[0]
            (1, 2, 3, 4)
        """
        from nu.core import Add

        return Tuple(Add(self, other))

    def __radd__(self, other: TupleArg[Unpack[Ts]]) -> Tuple:
        """Concatenation of other and self, with self on the right.

        Args:
            other: the tuple on the left of the `+`.

        Notes:
            - Reached only when the left operand is a plain Python tuple. A
              Nu Tuple on the left goes through its own `__add__` first and
              never lands here.

        Yields:
            A new tuple with other's items followed by self's. INVALID when
            either operand is not a Tuple or is a sentinel.

        Example:
            >>> nu.run((1, 2) + nu.Tuple.of(3, 4))[0]
            (1, 2, 3, 4)
        """
        from nu.core import Add

        return Tuple(Add(other, self))

    def __mul__(self, n: IntArg) -> Tuple:
        """Self repeated n times.

        Args:
            n: the number of repetitions.

        Yields:
            A new tuple with self's items repeated n times, in order.
            INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Tuple.of(1, 2) * 3)[0]
            (1, 2, 1, 2, 1, 2)
        """
        from nu.core import Mul

        return Tuple(Mul(self, n))

    def __rmul__(self, n: IntArg) -> Tuple:
        """Self repeated n times, with self on the right.

        Args:
            n: the value on the left of the `*`, the repeat count.

        Notes:
            - Reached only when the left operand is a plain Python int.

        Yields:
            A new tuple with self's items repeated n times. INVALID when
            self is a sentinel.

        Example:
            >>> nu.run(2 * nu.Tuple.of(1, 2))[0]
            (1, 2, 1, 2)
        """
        from nu.core import Mul

        return Tuple(Mul(n, self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: TupleArg[Unpack[Ts]]) -> Bool:
        """Self strictly greater than other, lexicographically.

        Args:
            other: the tuple to compare against.

        Notes:
            - Compares element by element, Python tuple ordering: the first
              differing pair decides.

        Yields:
            True when self sorts after other, False otherwise. INVALID when
            either operand is not a Tuple or is a sentinel.

        Example:
            >>> nu.run(nu.Tuple.of(1, 3) > nu.Tuple.of(1, 2))[0]
            True
        """
        from nu.core import Gt

        from ..primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: TupleArg[Unpack[Ts]]) -> Bool:
        """Self strictly less than other, lexicographically.

        Args:
            other: the tuple to compare against.

        Notes:
            - Compares element by element, Python tuple ordering: the first
              differing pair decides.

        Yields:
            True when self sorts before other, False otherwise. INVALID
            when either operand is not a Tuple or is a sentinel.

        Example:
            >>> nu.run(nu.Tuple.of(1, 2) < nu.Tuple.of(1, 3))[0]
            True
        """
        from nu.core import Lt

        from ..primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: TupleArg[Unpack[Ts]]) -> Bool:
        """Self greater than or equal to other, lexicographically.

        Args:
            other: the tuple to compare against.

        Yields:
            True when self sorts after or equal to other, False otherwise.
            INVALID when either operand is not a Tuple or is a sentinel.

        Example:
            >>> nu.run(nu.Tuple.of(1, 2) >= nu.Tuple.of(1, 2))[0]
            True
        """
        from nu.core import Ge

        from ..primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: TupleArg[Unpack[Ts]]) -> Bool:
        """Self less than or equal to other, lexicographically.

        Args:
            other: the tuple to compare against.

        Yields:
            True when self sorts before or equal to other, False otherwise.
            INVALID when either operand is not a Tuple or is a sentinel.

        Example:
            >>> nu.run(nu.Tuple.of(1, 2) <= nu.Tuple.of(1, 3))[0]
            True
        """
        from nu.core import Le

        from ..primitives import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: TupleArg[Unpack[Ts]]) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the tuple to compare against.

        Notes:
            - Value equality, not identity. Use `is_` for identity.

        Yields:
            True when the tuples have the same length and equal items in
            order, False otherwise. INVALID when either operand is not a
            Tuple or is a sentinel.

        Example:
            >>> nu.run(nu.Tuple.of(1, 2) == nu.Tuple.of(1, 2))[0]
            True
        """
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: TupleArg[Unpack[Ts]]) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the tuple to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the tuples differ, False otherwise. INVALID when
            either operand is not a Tuple or is a sentinel.

        Example:
            >>> nu.run(nu.Tuple.of(1, 2) != nu.Tuple.of(1, 3))[0]
            True
        """
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: TupleArg[Unpack[Ts]]) -> Bool:
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
            >>> nu.run(nu.Tuple.of(1, 2).is_(nu.Tuple.of(1, 2)))[0]
            False
        """
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))
