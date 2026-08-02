"""Set, FrozenSet - set interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import TypedNu

from .abc import MutableSetForm, SetLikeForm
from .abc.set_interactions import FrozenSetCreate, SetCreate


if TYPE_CHECKING:
    from nu.lang import FrozenSetArg, Nu, SetArg

    from ..primitives import Any, Bool
    from .list_ import List


__all__ = [
    "FrozenSet",
    "Set",
]


class Set[T](
    MutableSetForm[set[T], T, "Set[T]", "Any"],
    TypedNu[set[T]],
):
    """Set interface. Mutable set + comparable."""

    @classmethod
    def create(cls) -> Set[T]:
        """Yield a fresh empty set."""
        return cls(SetCreate())

    def _wrap_set_result(self, operand: Nu) -> Set[T]:
        """Wrap operand as Set."""
        return Set(operand)

    def _wrap_iterable_result(self, operand: Nu) -> List:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        """Wrap operand as Any element."""
        from ..primitives import Any

        return Any(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: SetArg[T]) -> Bool:
        from nu.core import Gt

        from ..primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: SetArg[T]) -> Bool:
        from nu.core import Lt

        from ..primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: SetArg[T]) -> Bool:
        from nu.core import Ge

        from ..primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: SetArg[T]) -> Bool:
        from nu.core import Le

        from ..primitives import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: SetArg[T]) -> Bool:  # type: ignore[override]
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: SetArg[T]) -> Bool:  # type: ignore[override]
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: SetArg[T]) -> Bool:
        """Identity comparison: self is other."""
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))


class FrozenSet[T](
    SetLikeForm[frozenset[T], T, "FrozenSet[T]", "Any"],
    TypedNu[frozenset[T]],
):
    """FrozenSet interface. Immutable set + comparable."""

    @classmethod
    def create(cls) -> FrozenSet[T]:
        """Yield an empty frozenset."""
        return cls(FrozenSetCreate())

    def _wrap_set_result(self, operand: Nu) -> FrozenSet[T]:
        """Wrap operand as FrozenSet."""
        return FrozenSet(operand)

    def _wrap_iterable_result(self, operand: Nu) -> List:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        """Wrap operand as Any element."""
        from ..primitives import Any

        return Any(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: FrozenSetArg[T]) -> Bool:
        from nu.core import Gt

        from ..primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: FrozenSetArg[T]) -> Bool:
        from nu.core import Lt

        from ..primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: FrozenSetArg[T]) -> Bool:
        from nu.core import Ge

        from ..primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: FrozenSetArg[T]) -> Bool:
        from nu.core import Le

        from ..primitives import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: FrozenSetArg[T]) -> Bool:  # type: ignore[override]
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: FrozenSetArg[T]) -> Bool:  # type: ignore[override]
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: FrozenSetArg[T]) -> Bool:
        """Identity comparison: self is other."""
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))
