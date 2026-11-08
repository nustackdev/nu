"""kv containers: collections whose elements each get an address of their own.

A container slot declares the value it holds, and that declaration types it
throughout. Descent (``ref[k]``, ``ref[i]``, ``ref.field``) lands on the kv ref
for the declared value, and every value an op reads is that value's form. A
container reads as a live View, so its collection ops run against storage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, overload

from typing_extensions import TypeVar

from nu.domains.shape import (
    ReactiveMappingRef,
    ReactiveSequenceRef,
    ReactiveSetRef,
    ReactiveShapeRef,
    Shape,
    Slot,
)
from nu.forms import Object
from nu.lang.typeinfo import TypeInfo
from virtuals.views import DictView, ListView, SetView

from .base import ViewRef, _refuse_container_value
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, ObjectRef, StrRef


if TYPE_CHECKING:
    from nu.domains.shape import StructuredRef
    from nu.forms import Iterator, List
    from nu.lang import Arg, IntArg
    from virtuals.collections import MutableMappingBase, MutableSequenceBase, MutableSetBase


__all__ = [
    "LEAVES",
    "DictRef",
    "ListRef",
    "SetRef",
    "ShapeRef",
]


#: The kv leaf that holds a value of each core Python type a container may
#: declare. A standard-library type is not here: its leaf lives with its
#: library (``nustd.decimal.kv.DecimalRef``), and a container gets it by being
#: declared with the leaf class rather than the Python type.
LEAVES: dict[object, type[ItemRef]] = {
    bool: BoolRef,
    int: IntRef,
    float: FloatRef,
    str: StrRef,
    bytes: BytesRef,
}


K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")
DK = TypeVar("DK", default=str)
DV = TypeVar("DV")
E = TypeVar("E")
S = TypeVar("S", bound=Shape)
L = TypeVar("L", bound=ItemRef)


class DictRef(ReactiveMappingRef, ViewRef[dict[K, V]], Generic[K, V]):
    """A mapping slot in KV storage, decomposed into a child per key.

    Every value lives at its own address under the slot, so keys can be read,
    written and watched one at a time without touching the rest. The declared
    value picks the child: a core Python type lands on its kv leaf (``str`` on
    ``StrRef``), a Shape on a ``ShapeRef`` for that shape, a kv leaf class on
    itself, and anything else, a standard-library type included, on
    ``ObjectRef``.

    Notes:
        - Ops run against the live View, so ``len``, ``contains`` and
          ``keys`` are answered by storage rather than by materializing the
          mapping.
        - Value reads (``get_item``, ``pop``, ``setdefault``) are the declared
          value's form, and ``values``, ``items`` and ``copy`` carry the
          declared types on.
        - A key vivifies on write: writing under a key that is not there yet
          creates it and every level above it.
        - A key that has never been written reads as NULL; use ``get_item``
          with a default when a fallback is wanted.
        - The key may itself be an expression or a ref, including a ref from
          another fabric, so a lookup can be computed at run time.
        - PrimitiveDictRef is the other choice: one opaque blob, no per-key
          addresses, but heterogeneous contents.

    Example:
        class Portfolio(Shape):
            owners = DictRef.slot(str)
            desks = DictRef.slot(Order)
        run(Portfolio.owners["core"].set("gor"), ctx)
        run(Portfolio.desks["desk-1"].symbol.set("SOL"), ctx)
    """

    extract = ViewRef.extract  # NULL on a never-written container, not core Extract

    _default_view = DictView

    @classmethod
    def slot(
        cls,
        value: type[DV],
        *,
        key: type[DK] = str,  # type: ignore[assignment]
        view: type[MutableMappingBase] | None = None,
    ) -> DictRef[DK, DV]:
        """Declare a mapping slot holding ``value`` under ``key`` keys.

        Args:
            value: what each key holds: a Python type, a Shape, or a kv leaf
                class.
            key: the key type. Defaults to ``str``.
            view: the View class laying the mapping out. Defaults to
                ``DictView``.

        Raises:
            TypeError: ``value`` is a container ref (``OrderedDictRef[...]``,
                ``SetRef[...]``, ...), which would be stored as one opaque
                value. Hold a Shape with that container as a slot instead.
                Every container slot refuses one, annotations too.

        Notes:
            - ``owners: DictRef[str, str]`` as an annotation declares the same
              slot.
        """
        _refuse_container_value(cls, value)
        declared = TypeInfo.from_annotation(cls[key, value])  # type: ignore[index]
        return Slot(cls, type_info=declared, view_type=view)  # type: ignore[return-value]

    def iter(self) -> Iterator[K]:
        """A lazy stream over the keys, each the declared key's form."""
        return super().iter()

    def keys(  # type: ignore[override]
        self, *, after: Arg[K] | None = None, limit: IntArg | None = None
    ) -> object:
        """The keys, or one page of them: those past ``after``, at most ``limit``.

        Args:
            after: the key to start past. None (or a NULL read) starts at
                the first key.
            limit: the most keys to read. None reads to the end.

        Notes:
            - With neither argument: every key, as a live keys view, the way
              ``dict.keys()`` reads.
            - With either: a page, read in one seek plus one row per key, so
              its cost tracks ``limit`` and not the size of the mapping.
              Pass the last key of a page as ``after`` to read the next one.
            - The order is the view's: key order on a dict, placed order on
              an ordered dict, oldest first on a log.
            - On a dict the cursor need not be there, so paging resumes past
              a key deleted since. On an ordered dict or a log it is an id
              the collection holds, and KeyError when it is gone.
            - A page of a never-written mapping is empty.
            - Only views that seek can page (dict, ordered and log views);
              any other raises TypeError here.

        Yields:
            Without arguments, the keys view. With either, a list of keys.

        Example:
            run(Space.planes.keys(limit=50), ctx)
            run(Space.planes.keys(after="p50", limit=50), ctx)
        """
        if after is None and limit is None:
            return super().keys()
        from nustd.kv.interactions.paging import KeysPage

        return self._page_result(KeysPage(self._paged(), after, limit))

    def reversed_keys(  # type: ignore[override]
        self, *, before: Arg[K] | None = None, limit: IntArg | None = None
    ) -> object:
        """The keys last first, or one page of them: those before ``before``, at most ``limit``.

        Args:
            before: the key to start before. None (or a NULL read) starts at
                the last key.
            limit: the most keys to read. None reads to the start.

        Notes:
            - With neither argument: every key, last first, as an iterator.
            - With either: a page, same cost and cursor rules as
              ``keys(after=, limit=)``. On a log this is newest first, the
              read a history or a trash list shows.

        Yields:
            Without arguments, an iterator over the keys. With either, a list
            of keys.

        Example:
            run(Indexes.removed.reversed_keys(limit=20), ctx)
        """
        if before is None and limit is None:
            return super().reversed_keys()
        from nustd.kv.interactions.paging import ReversedKeysPage

        return self._page_result(ReversedKeysPage(self._paged(), before, limit))

    def first(self) -> Object:
        """Read the first key in the view's order.

        Notes:
            - One seek, whatever the size of the mapping.
            - Key order on a dict, oldest first on a log; an ordered dict
              reads its placed order with its own ``first``.
            - Safe under a Snapshot. Only views that page have one: any
              other raises TypeError here.

        Yields:
            The first key. NULL when the mapping is empty, never written, or
            under a key that read NULL.

        Example:
            run(Cell.ids.first().fallback(""), ctx)
        """
        from nustd.kv.interactions.paging import FirstKey

        return Object(FirstKey(self._paged()))

    def last(self) -> Object:
        """Read the last key in the view's order.

        Same contract as ``first``, from the other end.

        Yields:
            The last key, or NULL.

        Example:
            run(Cell.ids.last(), ctx)
        """
        from nustd.kv.interactions.paging import LastKey

        return Object(LastKey(self._paged()))

    def _paged(self) -> DictRef[K, V]:
        """This ref, refused at build when its view cannot page."""
        from nustd.kv.interactions.paging import _pages

        view = self._payload.get("type_marker")
        if view is not None and not _pages(view):
            msg = f"{view.__name__} does not page its keys; use a Dict, ordered or log view"
            raise TypeError(msg)
        return self

    def _page_result(self, page: object) -> List[K]:
        """A page read, as a list typed by the declared key."""
        from nu.domains.shape.collection import holding
        from nu.forms import List

        return holding(List(page), list, elem=self._declared.key)

    @overload
    def __getitem__(self: DictRef[K, bool], key: object) -> BoolRef: ...
    @overload
    def __getitem__(self: DictRef[K, int], key: object) -> IntRef: ...
    @overload
    def __getitem__(self: DictRef[K, float], key: object) -> FloatRef: ...
    @overload
    def __getitem__(self: DictRef[K, str], key: object) -> StrRef: ...
    @overload
    def __getitem__(self: DictRef[K, bytes], key: object) -> BytesRef: ...
    @overload
    def __getitem__(self: DictRef[K, object], key: object) -> ObjectRef: ...
    @overload
    def __getitem__(self: DictRef[K, S], key: object) -> S: ...
    @overload
    def __getitem__(self: DictRef[K, L], key: object) -> L: ...
    @overload
    def __getitem__(self, key: object) -> ObjectRef: ...
    def __getitem__(self, key: object) -> StructuredRef:
        """The kv ref for the declared value at ``key``."""
        return super().__getitem__(key)


class ListRef(ReactiveSequenceRef, ViewRef[list[T]], Generic[T]):
    """An ordered list slot in KV storage, decomposed into per-index children.

    Every element lives at its own address under the slot, so the list can be
    appended to, indexed and watched without reading the whole thing. The
    declared value picks the child, as on a ``DictRef``: indexing lands on
    the kv ref for it, not on a plain value.

    Notes:
        - Ops run against the live View, so ``len`` and ``contains`` are
          answered by storage instead of by materializing the list.
        - Element reads (``first_elem``, ``pop``) are the declared value's
          form; a slice is a value, a List carrying the declared type on.
        - A position does not vivify: writing at an index the list does not
          reach raises IndexError, so append before assigning. Reading an
          out-of-range index yields NULL instead.
        - Change observation covers the child, the children and the whole
          subtree, each with its own hook.
        - PrimitiveListRef is the other choice: one opaque blob, no
          per-element addresses, but heterogeneous contents.

    Example:
        class Portfolio(Shape):
            tags = ListRef.slot(str)
            orders = ListRef.slot(Order)
        run(Portfolio.tags.append("core"), ctx)
        run(Portfolio.orders[0].symbol, ctx)
    """

    extract = ViewRef.extract  # NULL on a never-written container, not core Extract

    _default_view = ListView

    @classmethod
    def slot(cls, value: type[E], *, view: type[MutableSequenceBase] | None = None) -> ListRef[E]:
        """Declare a list slot holding ``value`` elements.

        Args:
            value: what each element is: a Python type, a Shape, or a kv leaf
                class.
            view: the View class laying the list out. Defaults to
                ``ListView``.

        Notes:
            - ``tags: ListRef[str]`` as an annotation declares the same slot.
        """
        _refuse_container_value(cls, value)
        declared = TypeInfo.from_annotation(cls[value])  # type: ignore[index]
        return Slot(cls, type_info=declared, view_type=view)  # type: ignore[return-value]

    def iter(self) -> Iterator[T]:
        """A lazy stream over the elements, each the declared value's form."""
        return super().iter()

    @overload
    def __getitem__(self, index: slice) -> List[T]: ...
    @overload
    def __getitem__(self: ListRef[bool], index: IntArg) -> BoolRef: ...
    @overload
    def __getitem__(self: ListRef[int], index: IntArg) -> IntRef: ...
    @overload
    def __getitem__(self: ListRef[float], index: IntArg) -> FloatRef: ...
    @overload
    def __getitem__(self: ListRef[str], index: IntArg) -> StrRef: ...
    @overload
    def __getitem__(self: ListRef[bytes], index: IntArg) -> BytesRef: ...
    @overload
    def __getitem__(self: ListRef[object], index: IntArg) -> ObjectRef: ...
    @overload
    def __getitem__(self: ListRef[S], index: IntArg) -> S: ...
    @overload
    def __getitem__(self: ListRef[L], index: IntArg) -> L: ...
    @overload
    def __getitem__(self, index: IntArg) -> ObjectRef: ...
    def __getitem__(self, index: object) -> StructuredRef:
        """The kv ref for the declared value at ``index``; a slice is a List."""
        return super().__getitem__(index)


class SetRef(ReactiveSetRef, ViewRef[set[T]], Generic[T]):
    """A set slot in KV storage: unordered, unique elements, stored decomposed.

    Notes:
        - Ops run against the live View, so membership and size are answered
          by storage rather than by reading the set out.
        - Elements have no addresses of their own to descend into: a set has
          no keys, so there is no element ref and no subscript.
        - The declared value types what comes out: ``pop`` is its form, and
          the set algebra (``union``, ``intersection``, ...) yields a Set
          carrying it on. The in-place variants (``update``,
          ``difference_update``, ...) are the ones that write.
        - Change observation covers the child, the children and the whole
          subtree, each with its own hook.
        - PrimitiveSetRef is the other choice: one opaque blob written whole.

    Example:
        class Portfolio(Shape):
            members = SetRef.slot(str)
        run(Portfolio.members.add("gor"), ctx)
        run(Portfolio.members.contains("gor"), ctx)
    """

    extract = ViewRef.extract  # NULL on a never-written container, not core Extract

    _default_view = SetView

    @classmethod
    def slot(cls, value: type[E], *, view: type[MutableSetBase] | None = None) -> SetRef[E]:
        """Declare a set slot holding ``value`` elements.

        Args:
            value: the element type.
            view: the View class laying the set out. Defaults to ``SetView``.

        Notes:
            - ``members: SetRef[str]`` as an annotation declares the same slot.
        """
        _refuse_container_value(cls, value)
        declared = TypeInfo.from_annotation(cls[value])  # type: ignore[index]
        return Slot(cls, type_info=declared, view_type=view)  # type: ignore[return-value]

    def iter(self) -> Iterator[T]:
        """A lazy stream over the elements, each the declared value's form."""
        return super().iter()


class ShapeRef(ReactiveShapeRef, ViewRef[dict[str, object]], Generic[T]):
    """A nested shape slot in KV storage: a fixed set of named fields.

    Descending by field name resolves the declared slot into that field's own
    ref, with this one as its parent, so a whole hierarchy is written as
    nested Shape classes and navigated with dots.

    Notes:
        - ``ref.field`` and ``ref["field"]`` are the same descent; the second
          is what to write when the field name is computed.
        - Fields carry their own types, so descent lands on a typed leaf ref
          or on another container ref, not on a plain value.
        - Nothing is created until a leaf underneath is written; the write
          then materializes every level along the way.
        - The mapping surface (``keys``, ``items``, ``len``) reads the
          stored fields, so it only sees the fields actually written.

    Example:
        class Order(Shape):
            symbol = StrRef.slot()
        class Portfolio(Shape):
            latest = ShapeRef.slot(Order)
        run(Portfolio.latest.symbol.set("SOL"), ctx)
    """

    extract = ViewRef.extract  # NULL on a never-written container, not core Extract

    _default_view = DictView

    @classmethod
    def slot(cls, shape: type[S], *, view: type[MutableMappingBase] | None = None) -> S:
        """Declare a slot holding a nested ``shape``.

        Args:
            shape: the Shape class held at this slot.
            view: the View class laying the fields out. Defaults to
                ``DictView``.

        Notes:
            - Statically it returns the Shape class itself, so
              ``latest: Order = ShapeRef.slot(Order)`` type-checks and dot
              navigation autocompletes over ``Order``'s slots.
            - ``latest: ShapeRef[Order]`` as an annotation declares the same
              slot.
        """
        return Slot(cls, shape_type=shape, view_type=view)  # type: ignore[return-value]
