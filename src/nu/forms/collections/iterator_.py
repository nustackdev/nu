"""IteratorForm - lazy iterator interface."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.primitives import AnyForm

    from .list_ import ListForm
    from .set_ import SetForm
    from .tuple_ import TupleForm


__all__ = [
    "IteratorForm",
]


class IteratorForm[T](Form, TypedNu[Iterator[T]]):
    """Lazy iterator interface. Materializes via to_list/to_set/to_tuple."""

    def __iter__(self) -> IteratorForm[T]:
        """Return self (Python's ``iter`` on an iterator). A pure read."""
        return self

    def __next__(self) -> AnyForm:
        """Advance this iterator and yield the next item (Python's ``next``).

        Stepping mutates the iterator's position and returns the item pulled,
        so the underlying ``NextAction`` is a ScalarAction (mutate-and-yield), not a
        Query. The element type is opaque, so the result is an ``AnyForm``.
        """
        from nu.core import NextAction
        from nu.forms.primitives import AnyForm

        return AnyForm(NextAction(self))

    def to_list(self) -> ListForm[T]:
        """Materialize iterator into a list."""
        from nu.core import ListQuery

        from .list_ import ListForm

        return ListForm(ListQuery(self))

    def to_set(self) -> SetForm[T]:
        """Materialize iterator into a set."""
        from nu.core import SetQuery

        from .set_ import SetForm

        return SetForm(SetQuery(self))

    def to_tuple(self) -> TupleForm:
        """Materialize iterator into a tuple."""
        from nu.core import TupleQuery

        from .tuple_ import TupleForm

        return TupleForm(TupleQuery(self))
