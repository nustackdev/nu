"""Set, FrozenSet - set interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.lang import TypedNu

from .abc import MutableSetForm, SetLikeForm
from .abc.set_interactions import FrozenSetCreate, FrozenSetOf, SetCreate, SetOf


if TYPE_CHECKING:
    from nu.lang import Arg, FrozenSetArg, Nu, SetArg

    from ..primitives import Any, Bool
    from .list_ import List


__all__ = [
    "FrozenSet",
    "Set",
]


T = TypeVar("T")


class Set(
    MutableSetForm[set[T], T, "Set[T]", "Any"],
    TypedNu[set[T]],
    Generic[T],
):
    """Set interface. Mutable set + comparable.

    Notes:
        - Iteration order is arbitrary, matching Python's `set`. Don't rely
          on insertion order surviving a round trip.
        - `>`, `<`, `>=`, `<=` are subset/superset relations, not size
          comparisons: `a > b` means a is a proper superset of b, not that
          a has more elements. `union`, `intersection`, `difference`,
          `symmetric_difference` and the operators `|`, `&`, `-`, `^` live
          on the shared set base, not on this class.
        - Mutating ops (`add`, `remove`, `discard`, `pop`, `clear`,
          `update`, ...) live on the shared mutable-set base too.

    Example:
        >>> nu.run(nu.Set.of(1, 2, 3))[0]
        {1, 2, 3}
    """

    @classmethod
    def create(cls) -> Set[T]:
        """Build a fresh empty set.

        Yields:
            An empty Set.

        Example:
            >>> nu.run(nu.Set.create())[0]
            set()
        """
        return cls(SetCreate())

    @classmethod
    def of(cls, *items: Arg) -> Set:
        """Build a set from positional item expressions.

        Args:
            *items: expressions to evaluate and fold into the set, in any
                order.

        Notes:
            - Sibling to `List.of` / `Tuple.of`. Duplicate values collapse,
              same as Python `set` construction.

        Yields:
            A fresh Set holding the evaluated items. INVALID when any item
            is a sentinel.

        Example:
            >>> nu.run(nu.Set.of(1, 2, 2, 3))[0]
            {1, 2, 3}
        """
        return cls(SetOf(*items))

    def _wrap_set_result(self, operand: Nu) -> Set[T]:
        """Wrap operand as Set.

        Yields:
            The operand wrapped as Set.
        """
        return Set(operand)

    def _wrap_iterable_result(self, operand: Nu) -> List:
        """Wrap operand as List.

        Yields:
            The operand wrapped as List.
        """
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        """Wrap operand as Any element.

        Yields:
            The operand wrapped as Any.
        """
        from ..primitives import Any

        return Any(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: SetArg[T]) -> Bool:
        """Self is a proper superset of other.

        Args:
            other: the set to compare against.

        Yields:
            True when self contains every element of other and at least one
            more, False otherwise. INVALID when either operand is a
            sentinel.

        Example:
            >>> nu.run(nu.Set.of(1, 2, 3) > nu.Set.of(1, 2))[0]
            True
        """
        from nu.core import Gt

        from ..primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: SetArg[T]) -> Bool:
        """Self is a proper subset of other.

        Args:
            other: the set to compare against.

        Yields:
            True when every element of self is in other and other has at
            least one more, False otherwise. INVALID when either operand is
            a sentinel.

        Example:
            >>> nu.run(nu.Set.of(1, 2) < nu.Set.of(1, 2, 3))[0]
            True
        """
        from nu.core import Lt

        from ..primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: SetArg[T]) -> Bool:
        """Self is a superset of other, or equal.

        Args:
            other: the set to compare against.

        Yields:
            True when every element of other is in self, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Set.of(1, 2) >= nu.Set.of(1, 2))[0]
            True
        """
        from nu.core import Ge

        from ..primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: SetArg[T]) -> Bool:
        """Self is a subset of other, or equal.

        Args:
            other: the set to compare against.

        Yields:
            True when every element of self is in other, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Set.of(1, 2) <= nu.Set.of(1, 2))[0]
            True
        """
        from nu.core import Le

        from ..primitives import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: SetArg[T]) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the set to compare against.

        Notes:
            - Value equality, not identity. Use `is_` for identity. Two
              sets compare equal regardless of insertion or iteration
              order.

        Yields:
            True when the sets hold the same elements, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Set.of(1, 2) == nu.Set.of(2, 1))[0]
            True
        """
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: SetArg[T]) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the set to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the sets differ, False otherwise. INVALID when either
            operand is a sentinel.

        Example:
            >>> nu.run(nu.Set.of(1, 2) != nu.Set.of(1, 3))[0]
            True
        """
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: SetArg[T]) -> Bool:
        """Identity comparison: self is other.

        Args:
            other: the value to compare identity against.

        Notes:
            - Object identity, not value equality. For value comparison use
              `==` instead.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise.

        Example:
            >>> nu.run(nu.Set.of(1, 2).is_(nu.Set.of(1, 2)))[0]
            False
        """
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))


class FrozenSet(
    SetLikeForm[frozenset[T], T, "FrozenSet[T]", "Any"],
    TypedNu[frozenset[T]],
    Generic[T],
):
    """FrozenSet interface. Immutable set + comparable.

    Notes:
        - Iteration order is arbitrary, matching Python's `frozenset`.
        - `>`, `<`, `>=`, `<=` are subset/superset relations, not size
          comparisons. `union`, `intersection`, `difference`,
          `symmetric_difference` and the operators `|`, `&`, `-`, `^` live
          on the shared set base, not on this class.
        - No `add`/`remove`/`update`/... unlike `Set`: a FrozenSet can't be
          mutated in place.

    Example:
        >>> nu.run(nu.FrozenSet.of(1, 2, 3))[0]
        frozenset({1, 2, 3})
    """

    @classmethod
    def create(cls) -> FrozenSet[T]:
        """Build an empty frozenset.

        Yields:
            An empty FrozenSet.

        Example:
            >>> nu.run(nu.FrozenSet.create())[0]
            frozenset()
        """
        return cls(FrozenSetCreate())

    @classmethod
    def of(cls, *items: Arg) -> FrozenSet:
        """Build a frozenset from positional item expressions.

        Args:
            *items: expressions to evaluate and fold into the frozenset, in
                any order.

        Notes:
            - Sibling to `Set.of`. Duplicate values collapse, same as
              Python `frozenset` construction.

        Yields:
            A fresh FrozenSet holding the evaluated items. INVALID when any
            item is a sentinel.

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2, 2, 3))[0]
            frozenset({1, 2, 3})
        """
        return cls(FrozenSetOf(*items))

    def _wrap_set_result(self, operand: Nu) -> FrozenSet[T]:
        """Wrap operand as FrozenSet.

        Yields:
            The operand wrapped as FrozenSet.
        """
        return FrozenSet(operand)

    def _wrap_iterable_result(self, operand: Nu) -> List:
        """Wrap operand as List.

        Yields:
            The operand wrapped as List.
        """
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        """Wrap operand as Any element.

        Yields:
            The operand wrapped as Any.
        """
        from ..primitives import Any

        return Any(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: FrozenSetArg[T]) -> Bool:
        """Self is a proper superset of other.

        Args:
            other: the set to compare against.

        Yields:
            True when self contains every element of other and at least one
            more, False otherwise. INVALID when either operand is a
            sentinel.

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2, 3) > nu.FrozenSet.of(1, 2))[0]
            True
        """
        from nu.core import Gt

        from ..primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: FrozenSetArg[T]) -> Bool:
        """Self is a proper subset of other.

        Args:
            other: the set to compare against.

        Yields:
            True when every element of self is in other and other has at
            least one more, False otherwise. INVALID when either operand is
            a sentinel.

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2) < nu.FrozenSet.of(1, 2, 3))[0]
            True
        """
        from nu.core import Lt

        from ..primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: FrozenSetArg[T]) -> Bool:
        """Self is a superset of other, or equal.

        Args:
            other: the set to compare against.

        Yields:
            True when every element of other is in self, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2) >= nu.FrozenSet.of(1, 2))[0]
            True
        """
        from nu.core import Ge

        from ..primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: FrozenSetArg[T]) -> Bool:
        """Self is a subset of other, or equal.

        Args:
            other: the set to compare against.

        Yields:
            True when every element of self is in other, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2) <= nu.FrozenSet.of(1, 2))[0]
            True
        """
        from nu.core import Le

        from ..primitives import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: FrozenSetArg[T]) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the set to compare against.

        Notes:
            - Value equality, not identity. Use `is_` for identity. Two
              sets compare equal regardless of insertion or iteration
              order.

        Yields:
            True when the sets hold the same elements, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2) == nu.FrozenSet.of(2, 1))[0]
            True
        """
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: FrozenSetArg[T]) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the set to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the sets differ, False otherwise. INVALID when either
            operand is a sentinel.

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2) != nu.FrozenSet.of(1, 3))[0]
            True
        """
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: FrozenSetArg[T]) -> Bool:
        """Identity comparison: self is other.

        Args:
            other: the value to compare identity against.

        Notes:
            - Object identity, not value equality. For value comparison use
              `==` instead.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise.

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2).is_(nu.FrozenSet.of(1, 2)))[0]
            False
        """
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))
