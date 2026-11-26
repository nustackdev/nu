"""Iterator - lazy stream form."""

from __future__ import annotations

from collections.abc import Iterator as PyIterator
from typing import TYPE_CHECKING, Generic, NoReturn, TypeVar, overload

from nu.lang import Form, Surface
from nu.lang.sentinels import UNSET
from nu.lang.typeinfo import TypeInfo


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.forms import Bool, Bytes, Float, Int, Iterator, List, Object, Set, Str, Tuple
    from nu.lang import Arg, IntArg, Nu


__all__ = [
    "IteratorSurface",
]


T = TypeVar("T")

_EQ_HINT = (
    "an Iterator has no value equality (it is a stream, not a value): "
    "drain it first, it.to_list() == other or it.to_set() == other"
)


class IteratorSurface(Surface, Generic[T]):
    """The methods of ``Iterator``. No slot holds one, so only the form carries them."""

    def __eq__(self, other: object) -> NoReturn:
        raise TypeError(_EQ_HINT)

    def __ne__(self, other: object) -> NoReturn:
        raise TypeError(_EQ_HINT)

    @property
    def _declared_elem(self) -> TypeInfo | None:
        """The element type the source declared; None when nothing is known."""
        ti = self._type_info
        return ti.elem if isinstance(ti, TypeInfo) else None

    def _holding(self, py_type: type) -> TypeInfo | None:
        """The ``type_info`` a result built from this stream carries: its declared element type."""
        elem = self._declared_elem
        return TypeInfo(py_type, elem=elem) if elem is not None else None

    def _item(self, operand: Nu) -> Form:
        """``operand`` (one of this stream's items) in the declared element's form."""
        from nu.forms import Object

        elem = self._declared_elem
        form_cls = elem.to_form() if elem is not None else Object
        return form_cls(operand)

    # ---- static overloads: narrow the item type on first() -------------
    #
    # Runtime dispatch reads the type info; here we tell mypy which concrete
    # Form to expect based on ``T``, as ``List.__getitem__`` does.

    @overload
    def first(self: IteratorSurface[bool], default: object = ...) -> Bool: ...
    @overload
    def first(self: IteratorSurface[int], default: object = ...) -> Int: ...
    @overload
    def first(self: IteratorSurface[float], default: object = ...) -> Float: ...
    @overload
    def first(self: IteratorSurface[str], default: object = ...) -> Str: ...
    @overload
    def first(self: IteratorSurface[bytes], default: object = ...) -> Bytes: ...
    @overload
    def first(self, default: object = ...) -> Object: ...
    def first(self, default=UNSET):  # type: ignore[no-untyped-def]
        """The first item this stream yields.

        Notes:
            - The stream opens fresh on every evaluation, so there is no
              cursor to advance: this is its first item, pulled and nothing
              past it. Python's `next()` is blocked by the ``Nu`` base.
            - The item takes the declared element type's form when the
              stream carries one, `Object` otherwise.

        Args:
            default: yielded for an empty stream. Leave it out to raise
                ValueError instead.

        Yields:
            The first item, or ``default`` when the stream is empty.

        Example:
            >>> nu.run(nu.List.of(1, 2).iter().first())[0]
            1
        """
        from nu.core import First

        return self._item(First(self) if default is UNSET else First(self, default))

    def map(self, transform: Nu | Callable[..., Nu]) -> Iterator:
        """Each item replaced by transform's value, still a stream.

        Args:
            transform: evaluated once per item; its value replaces the item.
                A lambda over the item, or a tree that reads none.

        Notes:
            - The same binding as `nu.Map`.

        Yields:
            An Iterator the same length as self, lazily mapped.

        Example:
            >>> xs = nu.List.of(1, 2).iter()
            >>> nu.run(xs.map(lambda x: nu.Int(x) + 1).to_list())[0]
            [2, 3]
        """
        from nu.core import Map
        from nu.forms import Iterator

        return Iterator(Map(self, transform))

    def filter(self, predicate: Nu | Callable[..., Nu]) -> Iterator[T]:
        """Only the items predicate holds for, still a stream.

        Args:
            predicate: evaluated once per item; the item stays when it is
                truthy. A lambda over the item, or a tree that reads none.

        Notes:
            - The same binding as `nu.Filter`.

        Yields:
            An Iterator over the kept items, in order.

        Example:
            >>> xs = nu.List.of(1, 2, 3).iter()
            >>> nu.run(xs.filter(lambda x: x > 1).to_list())[0]
            [2, 3]
        """
        from nu.core import Filter
        from nu.forms import Iterator

        return Iterator(Filter(self, predicate), type_info=self._holding(PyIterator))

    # ---- folds: stream to one value, the value keeps chaining -----------

    def count(self) -> Int:
        """The number of items this stream yields.

        Yields:
            The count as Int. 0 for an empty stream.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).iter().filter(lambda x: x > 1).count())[0]
            2
        """
        from nu.core import Count
        from nu.forms import Int

        return Int(Count(self))

    @overload
    def sum(self: IteratorSurface[bool]) -> Int: ...
    @overload
    def sum(self: IteratorSurface[int]) -> Int: ...
    @overload
    def sum(self: IteratorSurface[float]) -> Float: ...
    @overload
    def sum(self) -> Object: ...
    def sum(self):  # type: ignore[no-untyped-def]
        """The sum of every item this stream yields.

        Notes:
            - Folds from 0, so an empty stream yields 0, not NULL.
            - Int over a declared int or bool stream, Float over a float
              one, `Object` otherwise.

        Yields:
            The sum.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).iter().sum() > 5)[0]
            True
        """
        from nu.core import Sum
        from nu.forms import Float, Int, Object

        elem = self._declared_elem
        py_type = elem.py_type if elem is not None else None
        if py_type in (bool, int):
            return Int(Sum(self))
        if py_type is float:
            return Float(Sum(self))
        return Object(Sum(self))

    @overload
    def min(self: IteratorSurface[bool]) -> Bool: ...
    @overload
    def min(self: IteratorSurface[int]) -> Int: ...
    @overload
    def min(self: IteratorSurface[float]) -> Float: ...
    @overload
    def min(self: IteratorSurface[str]) -> Str: ...
    @overload
    def min(self: IteratorSurface[bytes]) -> Bytes: ...
    @overload
    def min(self) -> Object: ...
    def min(self):  # type: ignore[no-untyped-def]
        """The smallest item this stream yields.

        Notes:
            - The item takes the declared element type's form when the
              stream carries one, `Object` otherwise.

        Yields:
            The smallest item.

        Example:
            >>> nu.run(nu.List.of(3, 1, 2).iter().min())[0]
            1
        """
        from nu.core import Min

        return self._item(Min(self))

    @overload
    def max(self: IteratorSurface[bool]) -> Bool: ...
    @overload
    def max(self: IteratorSurface[int]) -> Int: ...
    @overload
    def max(self: IteratorSurface[float]) -> Float: ...
    @overload
    def max(self: IteratorSurface[str]) -> Str: ...
    @overload
    def max(self: IteratorSurface[bytes]) -> Bytes: ...
    @overload
    def max(self) -> Object: ...
    def max(self):  # type: ignore[no-untyped-def]
        """The largest item this stream yields.

        Notes:
            - The item takes the declared element type's form when the
              stream carries one, `Object` otherwise.

        Yields:
            The largest item.

        Example:
            >>> nu.run(nu.List.of(3, 1, 2).iter().max())[0]
            3
        """
        from nu.core import Max

        return self._item(Max(self))

    def any(self) -> Bool:
        """True if any item this stream yields is truthy.

        Notes:
            - Stops at the first truthy item; the rest is never pulled.
            - Map first to test a condition: `.map(f).any()`.

        Yields:
            True or False. False for an empty stream.

        Example:
            >>> nu.run(nu.List.of(1, 5).iter().map(lambda x: nu.Int(x) > 4).any())[0]
            True
        """
        from nu.core import AnyOf
        from nu.forms import Bool

        return Bool(AnyOf(self))

    def all(self) -> Bool:
        """True if every item this stream yields is truthy.

        Notes:
            - Stops at the first falsy item; the rest is never pulled.
            - Map first to test a condition: `.map(f).all()`.

        Yields:
            True or False. True for an empty stream.

        Example:
            >>> nu.run(nu.List.of(1, 5).iter().map(lambda x: nu.Int(x) > 0).all())[0]
            True
        """
        from nu.core import AllOf
        from nu.forms import Bool

        return Bool(AllOf(self))

    @overload
    def last(self: IteratorSurface[bool], default: object = ...) -> Bool: ...
    @overload
    def last(self: IteratorSurface[int], default: object = ...) -> Int: ...
    @overload
    def last(self: IteratorSurface[float], default: object = ...) -> Float: ...
    @overload
    def last(self: IteratorSurface[str], default: object = ...) -> Str: ...
    @overload
    def last(self: IteratorSurface[bytes], default: object = ...) -> Bytes: ...
    @overload
    def last(self, default: object = ...) -> Object: ...
    def last(self, default=UNSET):  # type: ignore[no-untyped-def]
        """The last item this stream yields.

        Notes:
            - Drains the whole stream to reach it.
            - The item takes the declared element type's form when the
              stream carries one, `Object` otherwise.

        Args:
            default: yielded for an empty stream. Leave it out to raise
                ValueError instead.

        Yields:
            The last item, or ``default`` when the stream is empty.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).iter().last())[0]
            3
        """
        from nu.core import Last

        return self._item(Last(self) if default is UNSET else Last(self, default))

    # ---- stream to stream ------------------------------------------------

    def sort_by(
        self,
        key: Nu | Callable[..., Nu],
        reverse: Arg[bool] = False,
    ) -> Iterator[T]:
        """Self ordered by a per-item key, still a stream.

        Args:
            key: evaluated once per item for its sort key. A lambda over the
                item, or a tree that reads none.
            reverse: descending order when truthy.

        Notes:
            - Drains and sorts the whole stream before yielding the first
              item.

        Yields:
            An Iterator over every item, ordered by key.

        Example:
            >>> xs = nu.List.of("bb", "a", "ccc").iter()
            >>> nu.run(xs.sort_by(lambda s: nu.Len(s), reverse=True).to_list())[0]
            ['ccc', 'bb', 'a']
        """
        from nu.core import SortBy
        from nu.forms import Iterator

        return Iterator(SortBy(self, key, reverse), type_info=self._holding(PyIterator))

    def unique(self) -> Iterator[T]:
        """Each item once, in first-seen order, still a stream.

        Notes:
            - Items must be hashable.

        Yields:
            An Iterator over the distinct items.

        Example:
            >>> nu.run(nu.List.of(1, 2, 1, 3).iter().unique().to_list())[0]
            [1, 2, 3]
        """
        from nu.core import Unique
        from nu.forms import Iterator

        return Iterator(Unique(self), type_info=self._holding(PyIterator))

    def reversed(self) -> Iterator[T]:
        """Self's items last to first, still a stream.

        Notes:
            - Drains the whole stream before yielding the first item.

        Yields:
            An Iterator over the items in reverse order.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).iter().reversed().to_list())[0]
            [3, 2, 1]
        """
        from nu.core import Reversed
        from nu.forms import Iterator

        return Iterator(Reversed(self), type_info=self._holding(PyIterator))

    def enumerate(self, start: IntArg | None = None) -> Iterator:
        """Each item paired with its running index, still a stream.

        Args:
            start: the first index. Defaults to 0.

        Yields:
            An Iterator of ``(index, item)`` tuples.

        Example:
            >>> nu.run(nu.List.of("a", "b").iter().enumerate(1).to_list())[0]
            [(1, 'a'), (2, 'b')]
        """
        from nu.core import Enumerate
        from nu.forms import Iterator

        if start is None:
            return Iterator(Enumerate(self))
        return Iterator(Enumerate(self, start))

    def zip(self, *others: Arg[Iterable]) -> Iterator:
        """Self threaded with other streams item by item, still a stream.

        Args:
            *others: the streams to pull alongside self, one item each per
                step.

        Notes:
            - Stops at the shortest stream, like Python's `zip`.

        Yields:
            An Iterator of tuples, self's item first.

        Example:
            >>> xs = nu.List.of(1, 2, 3).iter()
            >>> nu.run(xs.zip(nu.List.of("a", "b").iter()).to_list())[0]
            [(1, 'a'), (2, 'b')]
        """
        from nu.core import Zip
        from nu.forms import Iterator

        return Iterator(Zip(self, *others))

    def flatten(self) -> Iterator:
        """Self's items, each an iterable, joined one level into one stream.

        Notes:
            - One level only: an item that holds more iterables stays nested.

        Yields:
            An Iterator over every item of every sub-iterable, in order.

        Example:
            >>> nu.run(nu.List.of([1, 2], [3]).iter().flatten().to_list())[0]
            [1, 2, 3]
        """
        from nu.core import Flatten
        from nu.forms import Iterator

        return Iterator(Flatten(self))

    def to_list(self) -> List[T]:
        """Self drained into a List, in order.

        Yields:
            The List of items pulled.

        Example:
            >>> nu.run(nu.List.of(1, 2).iter().to_list())[0]
            [1, 2]
        """
        from nu.core import Collect
        from nu.forms import List

        return List(Collect(self), type_info=self._holding(list))

    def to_set(self) -> Set[T]:
        """Self drained into a Set.

        Notes:
            - Duplicate items collapse; order is not preserved.

        Yields:
            The Set of items pulled.

        Example:
            >>> nu.run(nu.List.of(1, 1, 2).iter().to_set())[0]
            {1, 2}
        """
        from nu.core import Collect, ToSet
        from nu.forms import Set

        return Set(ToSet(Collect(self)), type_info=self._holding(set))

    def to_tuple(self) -> Tuple:
        """Self drained into a Tuple, in order.

        Yields:
            The Tuple of items pulled.

        Example:
            >>> nu.run(nu.List.of(1, 2).iter().to_tuple())[0]
            (1, 2)
        """
        from nu.core import Collect, ToTuple
        from nu.forms import Tuple

        return Tuple(ToTuple(Collect(self)))

    def sorted(self) -> List[T]:
        """Self drained into a List, ascending.

        Notes:
            - Items must support ordering against each other. To order by
              a key or descending, use `sort_by`.

        Yields:
            The List of items pulled, ascending.

        Example:
            >>> nu.run(nu.List.of(3, 1, 2).iter().sorted())[0]
            [1, 2, 3]
        """
        from nu.core import Collect, Sorted
        from nu.forms import List

        return List(Sorted(Collect(self)), type_info=self._holding(list))
