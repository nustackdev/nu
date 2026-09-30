"""Iterator - lazy stream form."""

from __future__ import annotations

from collections.abc import Iterator as PyIterator
from typing import TYPE_CHECKING, Generic, NoReturn, TypeVar, overload

from nu.lang import Form, TypedNuStream
from nu.lang.typeinfo import TypeInfo


if TYPE_CHECKING:
    from nu.forms.primitives import Bool, Bytes, Float, Int, Object, Str
    from nu.lang import Nu, StrArg

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
        - Stream-shaped, not scalar. Its surface is stream operations only:
          `map`/`filter` stay streams, `to_list`/`to_set`/`to_tuple` drain
          it into a concrete collection, `next` pulls one item.
        - No `==` / `!=`: an iterator has no value to compare, so both
          raise. Drain it first: `it.to_list() == [...]`.
        - An element type rides on the payload as ``type_info`` when the
          source declared one (a typed collection ref opened with `.iter()`).
          The item `first` reads takes that type's form, and every op whose
          items are still the source's (`filter`, `to_list`, `to_set`)
          carries it on. `map` does not: the transform makes new items.

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
        from nu.forms.primitives import Object

        elem = self._declared_elem
        form_cls = elem.to_form() if elem is not None else Object
        return form_cls(First(self))

    def map(self, transform: Nu, key: StrArg = "item") -> Iterator:
        """Each item replaced by transform's value, still a stream.

        Args:
            transform: evaluated once per item; reads the item with
                `nu.Attr(key)`.
            key: the name each item is bound under. Defaults to `"item"`.

        Yields:
            An Iterator the same length as self, lazily mapped.

        Example:
            >>> xs = nu.List.of(1, 2).iter()
            >>> nu.run(xs.map(nu.Add(nu.Attr("item"), 1)).to_list())[0]
            [2, 3]
        """
        from nu.core import Map

        return Iterator(Map(self, transform, key))

    def filter(self, predicate: Nu, key: StrArg = "item") -> Iterator[T]:
        """Only the items predicate holds for, still a stream.

        Args:
            predicate: evaluated once per item; reads the item with
                `nu.Attr(key)`.
            key: the name each item is bound under. Defaults to `"item"`.

        Yields:
            An Iterator over the kept items, in order.

        Example:
            >>> xs = nu.List.of(1, 2, 3).iter()
            >>> nu.run(xs.filter(nu.Gt(nu.Attr("item"), 1)).to_list())[0]
            [2, 3]
        """
        from nu.core import Filter

        return self._holding(Iterator(Filter(self, predicate, key)), PyIterator)

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
