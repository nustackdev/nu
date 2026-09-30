"""mem containers: collections whose elements each get an address of their own.

A container slot declares the value it holds, and that declaration types it
throughout. Descent (``ref[k]``, ``ref[i]``, ``ref.field``) lands on the mem
ref for the declared value, and every value an op reads is that value's form.
A container reads as the live object held in the data dict.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, overload

from typing_extensions import TypeVar

from nu.domains.shape import (
    MutableMappingRef,
    MutableSequenceRef,
    MutableSetRef,
    MutableShapeRef,
    Shape,
    Slot,
)
from nu.lang.typeinfo import TypeInfo

from .base import RefBase
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, ObjectRef, StrRef


if TYPE_CHECKING:
    from nu.domains.shape import StructuredRef
    from nu.forms import Iterator, List
    from nu.lang import IntArg


__all__ = [
    "LEAVES",
    "DictRef",
    "ListRef",
    "SetRef",
    "ShapeRef",
]


#: The mem leaf that holds a value of each core Python type a container may
#: declare. A standard-library type is not here: its leaf lives with its
#: library (``nustd.decimal.mem.DecimalRef``), and a container gets it by being
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


class DictRef(MutableMappingRef, RefBase[dict[K, V]], Generic[K, V]):
    """A mapping slot in the dict substrate, holding one plain dict of values.

    Subscripting descends rather than reads: ``ref[k]`` is a ref at that key
    inside the stored dict, settable and erasable on its own. The declared
    value picks it: a core Python type lands on its mem leaf (``int`` on
    ``IntRef``), a Shape on a ``ShapeRef`` for that shape, a mem leaf class on
    itself, and anything else, a standard-library type included, on
    ``ObjectRef``. The mapping calls (``keys``,
    ``items``, ``update``, ...) act on the dict as a whole.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The stored value is an ordinary dict and a read hands back that
          live object, so a mutation through the ref is visible to anyone
          else holding it.
        - Value reads (``get_item``, ``pop``, ``setdefault``) are the declared
          value's form, and ``values``, ``items`` and ``copy`` carry the
          declared types on.
        - Writing through a key creates the dict and every level above it;
          the in-place calls instead read the container first and do nothing
          while the slot is absent, so ``set`` an empty dict before the first
          ``set_item``.
        - The declared types shape the refs and forms; nothing coerces or
          rejects what is written.

    Yields:
        The stored dict. EMPTY when the slot was never written.

    Example:
        >>> class Port(nu.Shape):
        ...     meta = nu.DictRef.slot(int)
        >>> data = {"meta": {"a": 1}}
        >>> ctx = nu.Context().bind(dict, data, Port)
        >>> _ = nu.run(Port.meta["b"].set(2), ctx)
        >>> nu.run(Port.meta["b"] + 1, ctx)[0]
        3
        >>> nu.run(Port.meta.len(), ctx)[0]
        2
    """

    @classmethod
    def slot(cls, value: type[DV], *, key: type[DK] = str) -> DictRef[DK, DV]:  # type: ignore[assignment]
        """Declare a mapping slot holding ``value`` under ``key`` keys.

        Args:
            value: what each key holds: a Python type, a Shape, or a mem leaf
                class.
            key: the key type. Defaults to ``str``.

        Notes:
            - ``meta: DictRef[str, int]`` as an annotation declares the same
              slot.
        """
        declared = TypeInfo.from_annotation(cls[key, value])  # type: ignore[index]
        return Slot(cls, type_info=declared)  # type: ignore[return-value]

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
        """The mem ref for the declared value at ``key``."""
        return super().__getitem__(key)


class ListRef(MutableSequenceRef, RefBase[list[T]], Generic[T]):
    """A sequence slot in the dict substrate, holding one plain list of values.

    Subscripting with an int descends rather than reads: ``ref[i]`` is the mem
    ref for the declared value at that index, settable and erasable on its
    own, picked as on a ``DictRef``. A slice instead routes to the
    sequence-level ``slice`` call and yields a new list.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The stored value is an ordinary list and a read hands back that
          live object, so a mutation through the ref is visible to anyone
          else holding it.
        - Element reads (``first_elem``, ``pop``) are the declared value's
          form; a slice is a List carrying the declared type on.
        - In-place calls read the container first and do nothing when the
          slot is absent, so ``set`` an empty list before the first
          ``append``.
        - An index past the end reads EMPTY rather than raising, like any
          other broken path.

    Yields:
        The stored list. EMPTY when the slot was never written.

    Example:
        >>> class Port(nu.Shape):
        ...     tags = nu.ListRef.slot(str)
        >>> data = {"tags": ["a"]}
        >>> ctx = nu.Context().bind(dict, data, Port)
        >>> _ = nu.run(Port.tags.append("b"), ctx)
        >>> nu.run(Port.tags[1].upper(), ctx)[0]
        'B'
        >>> data
        {'tags': ['a', 'b']}
    """

    @classmethod
    def slot(cls, value: type[E]) -> ListRef[E]:
        """Declare a list slot holding ``value`` elements.

        Args:
            value: what each element is: a Python type, a Shape, or a mem
                leaf class.

        Notes:
            - ``tags: ListRef[str]`` as an annotation declares the same slot.
        """
        declared = TypeInfo.from_annotation(cls[value])  # type: ignore[index]
        return Slot(cls, type_info=declared)  # type: ignore[return-value]

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
        """The mem ref for the declared value at ``index``; a slice is a List."""
        return super().__getitem__(index)


class SetRef(MutableSetRef, RefBase[set[T]], Generic[T]):
    """A set slot in the dict substrate, holding one plain set of values.

    No descent: a set has no addresses, so there is no child ref to navigate
    to. Everything happens through the set calls - membership, the algebra
    (``union``, ``difference``, ...), and the in-place mutations.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The stored value is an ordinary set and a read hands back that live
          object, so elements must be hashable and iteration order is
          whatever Python gives.
        - The declared value types what comes out: ``pop`` is its form, and
          the set algebra yields a Set carrying it on.
        - In-place calls read the container first and do nothing when the
          slot is absent, so ``set`` an empty set before the first ``add``.

    Yields:
        The stored set. EMPTY when the slot was never written.

    Example:
        >>> class Port(nu.Shape):
        ...     members = nu.SetRef.slot(str)
        >>> ctx = nu.Context().bind(dict, {"members": {"a"}}, Port)
        >>> _ = nu.run(Port.members.add("b"), ctx)
        >>> sorted(nu.run(Port.members, ctx)[0])
        ['a', 'b']
    """

    @classmethod
    def slot(cls, value: type[E]) -> SetRef[E]:
        """Declare a set slot holding ``value`` elements.

        Args:
            value: the element type.

        Notes:
            - ``members: SetRef[str]`` as an annotation declares the same
              slot.
        """
        declared = TypeInfo.from_annotation(cls[value])  # type: ignore[index]
        return Slot(cls, type_info=declared)  # type: ignore[return-value]

    def iter(self) -> Iterator[T]:
        """A lazy stream over the elements, each the declared value's form."""
        return super().iter()


class ShapeRef(MutableShapeRef, RefBase[dict[str, object]], Generic[T]):
    """A nested Shape slot in the dict substrate, stored as an inner dict.

    Attribute access descends: ``ref.field`` resolves the named slot on the
    held Shape class and hands back that field's own ref, parented here, so
    dot chains navigate arbitrarily deep before anything is read. The mapping
    calls on the ref itself act on the inner dict as a whole.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The inner dict does not have to exist first: writing through a
          field creates every level on the way down.
        - Nothing enforces the Shape: keys the class never declared can sit
          in the same dict and are read only through the mapping calls.

    Yields:
        The inner dict as stored. EMPTY when nothing was ever written under
        it.

    Example:
        >>> class Order(nu.Shape):
        ...     symbol = nu.StrRef.slot()
        >>> class Book(nu.Shape):
        ...     best = nu.ShapeRef.slot(Order)
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Book)
        >>> _ = nu.run(Book.best.symbol.set("AAPL"), ctx)
        >>> data
        {'best': {'symbol': 'AAPL'}}
    """

    @classmethod
    def slot(cls, shape: type[S]) -> S:
        """Declare a slot holding a nested ``shape``.

        Args:
            shape: the Shape class held at this slot.

        Notes:
            - Statically it returns the Shape class itself, so
              ``best: Order = ShapeRef.slot(Order)`` type-checks and dot
              navigation autocompletes over ``Order``'s slots.
            - ``best: ShapeRef[Order]`` as an annotation declares the same
              slot.
        """
        return Slot(cls, shape_type=shape)  # type: ignore[return-value]
