"""Iterator - lazy iterator interface."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Generic, TypeVar

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.primitives import Any

    from .list_ import List
    from .set_ import Set
    from .tuple_ import Tuple


__all__ = [
    "Iterator",
]


T = TypeVar("T")


class Iterator(Form, TypedNu[Iterator[T]], Generic[T]):
    """Lazy stream over another form's elements.

    Opened by Python's `iter()` on an IterableForm, which wraps the source in
    a stream-shaped `Iter` term. A term of this shape produces its items one
    at a time rather than as a single value, and pulling from it advances a
    position that can run dry.

    Notes:
        - Stream-shaped, not scalar. `to_list`/`to_set`/`to_tuple` drain it
          into a concrete collection; `next` pulls one item at a time.
        - Once exhausted, stays exhausted; there's no rewinding.

    Yields:
        Its items in order, one per pull, until exhausted.
    """

    def __iter__(self) -> Iterator[T]:
        """Self, unchanged.

        Notes:
            - Python's `iter()` on an iterator returns itself; a pure read,
              no new term is built.
        """
        return self

    def __next__(self) -> Any:
        """The next item pulled from this iterator.

        Notes:
            - Stepping mutates the iterator's position, so the underlying
              `Next` is an Action (mutate-and-yield), not a Query.
            - The element type is opaque here, so the result is wrapped as
              `Any`.

        Yields:
            The next item. Raises at evaluation time once the iterator is
            exhausted, matching Python's `next`.
        """
        from nu.core import Next
        from nu.forms.primitives import Any

        return Any(Next(self))

    def to_list(self) -> List[T]:
        """Self drained into a List, in order.

        Notes:
            - Consumes the iterator fully; it's exhausted afterward.

        Yields:
            The List of items pulled.
        """
        from nu.core import ToList

        from .list_ import List

        return List(ToList(self))

    def to_set(self) -> Set[T]:
        """Self drained into a Set.

        Notes:
            - Consumes the iterator fully; it's exhausted afterward.
            - Duplicate items collapse; order is not preserved.

        Yields:
            The Set of items pulled.
        """
        from nu.core import ToSet

        from .set_ import Set

        return Set(ToSet(self))

    def to_tuple(self) -> Tuple:
        """Self drained into a Tuple, in order.

        Notes:
            - Consumes the iterator fully; it's exhausted afterward.

        Yields:
            The Tuple of items pulled.
        """
        from nu.core import ToTuple

        from .tuple_ import Tuple

        return Tuple(ToTuple(self))
