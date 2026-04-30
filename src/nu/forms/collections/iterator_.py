"""IteratorForm - lazy iterator interface."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from nu.terms import Form, TypedNu


if TYPE_CHECKING:
    from .list_ import ListForm
    from .set_ import SetForm
    from .tuple_ import TupleForm


__all__ = [
    "IteratorForm",
]


class IteratorForm[T](Form, TypedNu[Iterator[T]]):
    """Lazy iterator interface. Materializes via to_list/to_set/to_tuple."""

    def to_list(self) -> ListForm[T]:
        from nu import ToList

        from .list_ import ListForm

        return ListForm(ToList(self))

    def to_set(self) -> SetForm[T]:
        from nu import ToSet

        from .set_ import SetForm

        return SetForm(ToSet(self))

    def to_tuple(self) -> TupleForm:
        from nu import ToTuple

        from .tuple_ import TupleForm

        return TupleForm(ToTuple(self))
