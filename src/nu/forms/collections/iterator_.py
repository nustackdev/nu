"""Iterator - lazy iterator interface."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.primitives import Any

    from .list_ import List
    from .set_ import Set
    from .tuple_ import Tuple


__all__ = [
    "Iterator",
]


class Iterator[T](Form, TypedNu[Iterator[T]]):
    """Lazy iterator interface. Materializes via to_list/to_set/to_tuple."""

    def __iter__(self) -> Iterator[T]:
        """Return self (Python's ``iter`` on an iterator). A pure read."""
        return self

    def __next__(self) -> Any:
        """Advance this iterator and yield the next item (Python's ``next``).

        Stepping mutates the iterator's position and returns the item pulled,
        so the underlying ``Next`` is a ScalarAction (mutate-and-yield), not a
        Query. The element type is opaque, so the result is an ``Any``.
        """
        from nu.core import Next
        from nu.forms.primitives import Any

        return Any(Next(self))

    def to_list(self) -> List[T]:
        """Materialize iterator into a list."""
        from nu.core import ToList

        from .list_ import List

        return List(ToList(self))

    def to_set(self) -> Set[T]:
        """Materialize iterator into a set."""
        from nu.core import ToSet

        from .set_ import Set

        return Set(ToSet(self))

    def to_tuple(self) -> Tuple:
        """Materialize iterator into a tuple."""
        from nu.core import ToTuple

        from .tuple_ import Tuple

        return Tuple(ToTuple(self))
