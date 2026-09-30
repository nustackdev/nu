"""Iterator - lazy iterator interface."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Generic, NoReturn, TypeVar

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.primitives import Object

    from .list_ import List
    from .set_ import Set
    from .tuple_ import Tuple


__all__ = [
    "Iterator",
]


T = TypeVar("T")

_EQ_HINT = (
    "an Iterator has no value equality (it is a stream, not a value): "
    "drain it first, it.to_list() == other or it.to_set() == other"
)


class Iterator(Form, TypedNu[Iterator[T]], Generic[T]):
    """Lazy stream over another form's elements.

    Opened by `.iter()` on an IterableForm, which wraps the source in
    a stream-shaped `Iter` term. A term of this shape produces its items one
    at a time rather than as a single value, and pulling from it advances a
    position that can run dry.

    Notes:
        - Stream-shaped, not scalar. `to_list`/`to_set`/`to_tuple` drain it
          into a concrete collection; `.next()` pulls one item at a time.
        - Once exhausted, stays exhausted; there's no rewinding.
        - No `==` / `!=`: an iterator has no value to compare, so both
          raise. Drain it first: `it.to_list() == [...]`.

    Yields:
        Its items in order, one per pull, until exhausted.
    """

    def __eq__(self, other: object) -> NoReturn:
        raise TypeError(_EQ_HINT)

    def __ne__(self, other: object) -> NoReturn:
        raise TypeError(_EQ_HINT)

    def next(self) -> Object:
        """The next item pulled from this iterator.

        Notes:
            - Stepping mutates the iterator's position, so the underlying
              `Next` is an Action (mutate-and-yield), not a Query.
            - Named because Python's `next()` would pull at build time; the
              ``Nu`` base blocks it.
            - The element type is opaque here, so the result is wrapped as
              `Object`.

        Yields:
            The next item. Raises at evaluation time once the iterator is
            exhausted, matching Python's `next`.
        """
        from nu.core import Next
        from nu.forms.primitives import Object

        return Object(Next(self))

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
