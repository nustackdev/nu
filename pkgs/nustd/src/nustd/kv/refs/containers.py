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
from nu.lang.typeinfo import TypeInfo
from virtuals.views import DictView, ListView, SetView

from .base import ViewRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, ObjectRef, StrRef


if TYPE_CHECKING:
    from nu.domains.shape import StructuredRef
    from nu.forms import Iterator, List
    from nu.lang import IntArg
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
        - A key that has never been written reads as EMPTY; use ``get_item``
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

        Notes:
            - ``owners: DictRef[str, str]`` as an annotation declares the same
              slot.
        """
        declared = TypeInfo.from_annotation(cls[key, value])  # type: ignore[index]
        return Slot(cls, type_info=declared, view_type=view)  # type: ignore[return-value]

    def iter(self) -> Iterator[K]:
        """A lazy stream over the keys, each the declared key's form."""
        return super().iter()

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
          out-of-range index yields EMPTY instead.
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
