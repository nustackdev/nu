"""Dict view interfaces - DictKeys, DictValues, DictItems."""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView
from typing import TYPE_CHECKING, Generic, TypeVar

from nu.lang import TypedNu

from .abc import CollectionForm
from .abc.set_ import SetLikeForm


if TYPE_CHECKING:
    from nu.lang import Nu

    from ..primitives import Any
    from .list_ import List
    from .set_ import Set


__all__ = [
    "DictItems",
    "DictKeys",
    "DictValues",
]


K = TypeVar("K")
V = TypeVar("V")


class DictKeys(
    SetLikeForm[KeysView[K], K, "Set[K]", "Any"],
    TypedNu[KeysView[K]],
    Generic[K],
):
    """Dict key view interface - set-like, lazy, live."""

    def _wrap_set_result(self, operand: Nu) -> Set[K]:
        """Wrap operand as Set."""
        from .set_ import Set

        return Set(operand)

    def _wrap_iterable_result(self, operand: Nu) -> List[K]:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        """Wrap operand as Any element."""
        from ..primitives import Any

        return Any(operand)

    def to_list(self) -> List[K]:
        """Materialize keys view into a list."""
        from nu.core import ToList

        from .list_ import List

        return List(ToList(self))

    def to_set(self) -> Set[K]:
        """Materialize keys view into a set."""
        from nu.core import ToSet

        from .set_ import Set

        return Set(ToSet(self))


class DictValues(
    CollectionForm[V, "List[V]", "Any"],
    TypedNu[ValuesView[V]],
    Generic[V],
):
    """Dict value view interface - iterable, sized, containment."""

    def _wrap_iterable_result(self, operand: Nu) -> List[V]:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        """Wrap operand as Any element."""
        from ..primitives import Any

        return Any(operand)

    def to_list(self) -> List[V]:
        """Materialize values view into a list."""
        from nu.core import ToList

        from .list_ import List

        return List(ToList(self))

    def to_set(self) -> Set[V]:
        """Materialize values view into a set."""
        from nu.core import ToSet

        from .set_ import Set

        return Set(ToSet(self))


class DictItems(
    SetLikeForm[ItemsView[K, V], tuple[K, V], "Set[tuple[K, V]]", "Any"],
    TypedNu[ItemsView[K, V]],
    Generic[K, V],
):
    """Dict item view interface - set-like, lazy, live."""

    def _wrap_set_result(self, operand: Nu) -> Set[tuple[K, V]]:
        """Wrap operand as Set."""
        from .set_ import Set

        return Set(operand)

    def _wrap_iterable_result(self, operand: Nu) -> List[tuple[K, V]]:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        """Wrap operand as Any element."""
        from ..primitives import Any

        return Any(operand)

    def to_list(self) -> List[tuple[K, V]]:
        """Materialize items view into a list."""
        from nu.core import ToList

        from .list_ import List

        return List(ToList(self))

    def to_set(self) -> Set[tuple[K, V]]:
        """Materialize items view into a set."""
        from nu.core import ToSet

        from .set_ import Set

        return Set(ToSet(self))
