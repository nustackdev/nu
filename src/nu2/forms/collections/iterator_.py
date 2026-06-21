"""IteratorForm - lazy iterator interface."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from nu2.lang import Form, TypedNu


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
        """Materialize iterator into a list."""
        from nu2.core import List

        from .list_ import ListForm

        return ListForm(List(self))

    def to_set(self) -> SetForm[T]:
        """Materialize iterator into a set."""
        from nu2.core import Set

        from .set_ import SetForm

        return SetForm(Set(self))

    def to_tuple(self) -> TupleForm:
        """Materialize iterator into a tuple."""
        from nu2.core import Tuple

        from .tuple_ import TupleForm

        return TupleForm(Tuple(self))
