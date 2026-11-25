"""Set, FrozenSet - set interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from .abc import MutableSetSurface, SetLikeSurface


if TYPE_CHECKING:
    from nu.forms import Bool, FrozenSet, Object, Set
    from nu.lang import FrozenSetArg, Nu, SetArg


__all__ = [
    "FrozenSetSurface",
    "SetSurface",
]


T = TypeVar("T")


class SetSurface(MutableSetSurface[set[T], T, "Set[T]", "Object"], Generic[T]):
    """The methods of ``Set``, shared by the ``Set`` form and every ref that holds one."""

    def _wrap_set_result(self, operand: Nu) -> Set[T]:
        """Wrap operand as Set.

        Yields:
            The operand wrapped as Set.
        """
        from nu.forms import Set

        return Set(operand)

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as an elem-typed Form when known; Object otherwise.

        Notes:
            - A Set carrying a `TypeInfo` in its `type_info` field (a result of a
              typed set ref, like `SetRef.slot(str).union(...)`) dispatches
              the element to its concrete Form, as `List` does.
        """
        ti = self._type_info
        if ti is not None and ti.elem is not None:
            return ti.elem.to_form()(operand)  # type: ignore[return-value]
        from nu.forms import Object

        return Object(operand)

    def copy(self) -> Set[T]:
        """Shallow copy of self.

        Notes:
            - Built-in only: `collections.abc.Set` has no `copy`.

        Yields:
            A new set with the same elements as self.

        Example:
            >>> nu.run(nu.Set({1, 2, 3}).copy())[0]
            {1, 2, 3}
        """
        from .abc.set_interactions import Copy

        return self._wrap_set_result(Copy(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

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

        Example:
            >>> nu.run(nu.Set.of(1, 2) == nu.Set.of(2, 1))[0]
            True
        """
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: SetArg[T]) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the set to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the sets differ, False otherwise.

        Example:
            >>> nu.run(nu.Set.of(1, 2) != nu.Set.of(1, 3))[0]
            True
        """
        from nu.core import Ne
        from nu.forms import Bool

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
        from nu.forms import Bool

        return Bool(Is(self, other))


class FrozenSetSurface(SetLikeSurface[frozenset[T], T, "FrozenSet[T]", "Object"], Generic[T]):
    """The methods of ``FrozenSet``, shared by the ``FrozenSet`` form and every ref that holds one."""

    def _wrap_set_result(self, operand: Nu) -> FrozenSet[T]:
        """Wrap operand as FrozenSet.

        Yields:
            The operand wrapped as FrozenSet.
        """
        from nu.forms import FrozenSet

        return FrozenSet(operand)

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object element.

        Yields:
            The operand wrapped as Object.
        """
        from nu.forms import Object

        return Object(operand)

    def copy(self) -> FrozenSet[T]:
        """Shallow copy of self.

        Notes:
            - Built-in only: `collections.abc.Set` has no `copy`.

        Yields:
            A new frozenset with the same elements as self.

        Example:
            >>> nu.run(nu.FrozenSet(frozenset({1, 2})).copy())[0]
            frozenset({1, 2})
        """
        from .abc.set_interactions import Copy

        return self._wrap_set_result(Copy(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

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

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2) == nu.FrozenSet.of(2, 1))[0]
            True
        """
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: FrozenSetArg[T]) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the set to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the sets differ, False otherwise.

        Example:
            >>> nu.run(nu.FrozenSet.of(1, 2) != nu.FrozenSet.of(1, 3))[0]
            True
        """
        from nu.core import Ne
        from nu.forms import Bool

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
        from nu.forms import Bool

        return Bool(Is(self, other))
