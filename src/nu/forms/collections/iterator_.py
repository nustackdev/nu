"""Iterator - lazy stream form."""

from __future__ import annotations

from collections.abc import Iterator as PyIterator
from typing import TYPE_CHECKING, Generic, NoReturn, TypeVar, overload

from nu.lang import Form, TypedNuStream
from nu.lang.typeinfo import TypeInfo


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.context import Attr
    from nu.forms.primitives import Bool, Bytes, Float, Int, Object, Str
    from nu.lang import Arg, IntArg, Nu, StrArg

    from .list_ import List
    from .set_ import Set
    from .tuple_ import Tuple


__all__ = [
    "Iterator",
]


T = TypeVar("T")
_F = TypeVar("_F", bound=Form)

_EQ_HINT = (
    "an Iterator has no value equality (it is a stream, not a value): "
    "drain it first, it.to_list() == other or it.to_set() == other"
)


class Iterator(Form, TypedNuStream[PyIterator[T]], Generic[T]):
    """Lazy stream over another form's elements.

    Opened by `.iter()` on an IterableForm, which wraps the source in
    a stream-shaped `Iter` term. A term of this shape produces its items one
    at a time rather than as a single value, so it sits wherever a stream
    goes: `nu.ForEachDo`, `nu.Map`, `nu.Collect`, and the itertools.

    Notes:
        - Stream-shaped, not scalar. Its surface is stream operations:
          `map`, `filter`, `sort_by`, `unique`, `reversed`, `enumerate`,
          `zip` and `flatten` stay streams; `count`, `sum`, `min`, `max`,
          `any`, `all`, `first` and `last` fold it to one value that keeps
          chaining (`.sum() > 10`); `to_list`, `to_set`, `to_tuple` and
          `sorted` drain it into a concrete collection.
        - No `==` / `!=`: an iterator has no value to compare, so both
          raise. Drain it first: `it.to_list() == [...]`.
        - An element type rides on the payload as ``type_info`` when the
          source declared one (a typed collection ref opened with `.iter()`).
          The item `first`/`last`/`min`/`max` read takes that type's form,
          and every op whose items are still the source's (`filter`,
          `sort_by`, `unique`, `reversed`, `to_list`, `to_set`, `sorted`)
          carries it on. `map`, `enumerate`, `zip` and `flatten` do not:
          they make new items.

    Yields:
        Its items in order, one per pull, until exhausted.

    Example:
        >>> nu.run(nu.List.of(1, 2, 3).iter().to_list())[0]
        [1, 2, 3]
    """

    def __eq__(self, other: object) -> NoReturn:
        raise TypeError(_EQ_HINT)

    def __ne__(self, other: object) -> NoReturn:
        raise TypeError(_EQ_HINT)

    @property
    def _declared_elem(self) -> TypeInfo | None:
        """The element type the source declared; None when nothing is known."""
        ti = self._payload.get("type_info")
        return ti.elem if isinstance(ti, TypeInfo) else None

    def _holding(self, result: _F, py_type: type) -> _F:
        """``result`` carrying this stream's declared element type, when it has one."""
        elem = self._declared_elem
        if elem is not None:
            result._payload["type_info"] = TypeInfo(py_type, elem=elem)  # type: ignore[attr-defined]
        return result

    def _item(self, operand: Nu) -> Form:
        """``operand`` (one of this stream's items) in the declared element's form."""
        from nu.forms.primitives import Object

        elem = self._declared_elem
        form_cls = elem.to_form() if elem is not None else Object
        return form_cls(operand)

    # ---- static overloads: narrow the item type on first() -------------
    #
    # Runtime dispatch reads the payload; here we tell mypy which concrete
    # Form to expect based on ``T``, as ``List.__getitem__`` does.

    @overload
    def first(self: Iterator[bool]) -> Bool: ...
    @overload
    def first(self: Iterator[int]) -> Int: ...
    @overload
    def first(self: Iterator[float]) -> Float: ...
    @overload
    def first(self: Iterator[str]) -> Str: ...
    @overload
    def first(self: Iterator[bytes]) -> Bytes: ...
    @overload
    def first(self) -> Object: ...
    def first(self):  # type: ignore[no-untyped-def]
        """The first item this stream yields.

        Notes:
            - The stream opens fresh on every evaluation, so there is no
              cursor to advance: this is its first item, pulled and nothing
              past it. Python's `next()` is blocked by the ``Nu`` base.
            - The item takes the declared element type's form when the
              stream carries one, `Object` otherwise.

        Yields:
            The first item. EMPTY when the stream is empty.

        Example:
            >>> nu.run(nu.List.of(1, 2).iter().first())[0]
            1
        """
        from nu.core import First

        return self._item(First(self))

    def map(self, transform: Nu | Callable[[Attr], Nu], key: StrArg | None = None) -> Iterator:
        """Each item replaced by transform's value, still a stream.

        Args:
            transform: evaluated once per item; its value replaces the item.
                A lambda over the item, or a tree reading it with
                `nu.Attr(key)`.
            key: the name each item is bound under, for a tree transform.
                Defaults to `"item"`; a lambda mints its own.

        Notes:
            - The same binding as `nu.Map`: ``key`` is passed on only when
              given, so a lambda and an explicit name never meet.

        Yields:
            An Iterator the same length as self, lazily mapped.

        Example:
            >>> xs = nu.List.of(1, 2).iter()
            >>> nu.run(xs.map(lambda x: nu.Int(x) + 1).to_list())[0]
            [2, 3]

            The same with a tree reading the default name:

            >>> nu.run(xs.map(nu.Add(nu.Attr("item"), 1)).to_list())[0]
            [2, 3]
        """
        from nu.core import Map

        return Iterator(Map(self, transform, key))

    def filter(
        self, predicate: Nu | Callable[[Attr], Nu], key: StrArg | None = None
    ) -> Iterator[T]:
        """Only the items predicate holds for, still a stream.

        Args:
            predicate: evaluated once per item; the item stays when it is
                truthy. A lambda over the item, or a tree reading it with
                `nu.Attr(key)`.
            key: the name each item is bound under, for a tree predicate.
                Defaults to `"item"`; a lambda mints its own.

        Notes:
            - The same binding as `nu.Filter`: ``key`` is passed on only
              when given, so a lambda and an explicit name never meet.

        Yields:
            An Iterator over the kept items, in order.

        Example:
            >>> xs = nu.List.of(1, 2, 3).iter()
            >>> nu.run(xs.filter(lambda x: x > 1).to_list())[0]
            [2, 3]

            The same with a tree reading an explicit name:

            >>> nu.run(xs.filter(nu.Gt(nu.Attr("n"), 1), key="n").to_list())[0]
            [2, 3]
        """
        from nu.core import Filter

        return self._holding(Iterator(Filter(self, predicate, key)), PyIterator)

    # ---- folds: stream to one value, the value keeps chaining -----------

    def count(self) -> Int:
        """The number of items this stream yields.

        Yields:
            The count as Int. 0 for an empty stream. EMPTY if any item is
            EMPTY.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).iter().filter(lambda x: x > 1).count())[0]
            2
        """
        from nu.core import Count
        from nu.forms.primitives import Int

        return Int(Count(self))

    @overload
    def sum(self: Iterator[bool]) -> Int: ...
    @overload
    def sum(self: Iterator[int]) -> Int: ...
    @overload
    def sum(self: Iterator[float]) -> Float: ...
    @overload
    def sum(self) -> Object: ...
    def sum(self):  # type: ignore[no-untyped-def]
        """The sum of every item this stream yields.

        Notes:
            - Folds from 0, so an empty stream yields 0, not EMPTY.
            - Int over a declared int or bool stream, Float over a float
              one, `Object` otherwise.

        Yields:
            The sum. EMPTY if any item is EMPTY.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).iter().sum() > 5)[0]
            True
        """
        from nu.core import Sum
        from nu.forms.primitives import Float, Int, Object

        elem = self._declared_elem
        py_type = elem.py_type if elem is not None else None
        if py_type in (bool, int):
            return Int(Sum(self))
        if py_type is float:
            return Float(Sum(self))
        return Object(Sum(self))

    @overload
    def min(self: Iterator[bool]) -> Bool: ...
    @overload
    def min(self: Iterator[int]) -> Int: ...
    @overload
    def min(self: Iterator[float]) -> Float: ...
    @overload
    def min(self: Iterator[str]) -> Str: ...
    @overload
    def min(self: Iterator[bytes]) -> Bytes: ...
    @overload
    def min(self) -> Object: ...
    def min(self):  # type: ignore[no-untyped-def]
        """The smallest item this stream yields.

        Notes:
            - The item takes the declared element type's form when the
              stream carries one, `Object` otherwise.

        Yields:
            The smallest item. EMPTY when the stream is empty or any item
            is EMPTY.

        Example:
            >>> nu.run(nu.List.of(3, 1, 2).iter().min())[0]
            1
        """
        from nu.core import Min

        return self._item(Min(self))

    @overload
    def max(self: Iterator[bool]) -> Bool: ...
    @overload
    def max(self: Iterator[int]) -> Int: ...
    @overload
    def max(self: Iterator[float]) -> Float: ...
    @overload
    def max(self: Iterator[str]) -> Str: ...
    @overload
    def max(self: Iterator[bytes]) -> Bytes: ...
    @overload
    def max(self) -> Object: ...
    def max(self):  # type: ignore[no-untyped-def]
        """The largest item this stream yields.

        Notes:
            - The item takes the declared element type's form when the
              stream carries one, `Object` otherwise.

        Yields:
            The largest item. EMPTY when the stream is empty or any item
            is EMPTY.

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
            True or False, never EMPTY. False for an empty stream.

        Example:
            >>> nu.run(nu.List.of(1, 5).iter().map(lambda x: nu.Int(x) > 4).any())[0]
            True
        """
        from nu.core import AnyOf
        from nu.forms.primitives import Bool

        return Bool(AnyOf(self))

    def all(self) -> Bool:
        """True if every item this stream yields is truthy.

        Notes:
            - Stops at the first falsy item; the rest is never pulled.
            - Map first to test a condition: `.map(f).all()`.

        Yields:
            True or False, never EMPTY. True for an empty stream.

        Example:
            >>> nu.run(nu.List.of(1, 5).iter().map(lambda x: nu.Int(x) > 0).all())[0]
            True
        """
        from nu.core import AllOf
        from nu.forms.primitives import Bool

        return Bool(AllOf(self))

    @overload
    def last(self: Iterator[bool]) -> Bool: ...
    @overload
    def last(self: Iterator[int]) -> Int: ...
    @overload
    def last(self: Iterator[float]) -> Float: ...
    @overload
    def last(self: Iterator[str]) -> Str: ...
    @overload
    def last(self: Iterator[bytes]) -> Bytes: ...
    @overload
    def last(self) -> Object: ...
    def last(self):  # type: ignore[no-untyped-def]
        """The last item this stream yields.

        Notes:
            - Drains the whole stream to reach it.
            - The item takes the declared element type's form when the
              stream carries one, `Object` otherwise.

        Yields:
            The last item. EMPTY when the stream is empty or any item is
            EMPTY.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).iter().last())[0]
            3
        """
        from nu.core import Last

        return self._item(Last(self))

    # ---- stream to stream ------------------------------------------------

    def sort_by(
        self,
        key: Nu | Callable[[Attr], Nu],
        reverse: Arg[bool] = False,
        item: StrArg | None = None,
    ) -> Iterator[T]:
        """Self ordered by a per-item key, still a stream.

        Args:
            key: evaluated once per item for its sort key. A lambda over the
                item, or a tree reading it with `nu.Attr(item)`.
            reverse: descending order when truthy.
            item: the name each item is bound under, for a tree key.
                Defaults to `"item"`; a lambda mints its own.

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

        return self._holding(Iterator(SortBy(self, key, reverse, item)), PyIterator)

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

        return self._holding(Iterator(Unique(self)), PyIterator)

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

        return self._holding(Iterator(Reversed(self)), PyIterator)

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

        from .list_ import List

        return self._holding(List(Collect(self)), list)

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

        from .set_ import Set

        return self._holding(Set(ToSet(Collect(self))), set)

    def to_tuple(self) -> Tuple:
        """Self drained into a Tuple, in order.

        Yields:
            The Tuple of items pulled.

        Example:
            >>> nu.run(nu.List.of(1, 2).iter().to_tuple())[0]
            (1, 2)
        """
        from nu.core import Collect, ToTuple

        from .tuple_ import Tuple

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

        from .list_ import List

        return self._holding(List(Sorted(Collect(self))), list)
