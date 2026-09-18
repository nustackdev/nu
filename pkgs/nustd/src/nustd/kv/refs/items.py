"""Virtuals item refs: typed leaf-value holders backed by virtuals storage.

``ItemRef`` combines the shape ``ReactiveItemRef`` blueprint (slot-level CRUD +
change observation) with ``PrimitiveRef`` (virtuals leaf navigation). Typed
refs (``IntRef``, ``StrRef``, ...) add the matching primitive Form so the value
carries its full operator interface.

Reactivity is uniform: ``ReactiveItemForm.on_change()`` -> ``nu.core.reactive
.OnPrimitiveChange`` calls ``ref._afetch_parent`` + ``ref._aaddress`` on the
leaf, and the virtuals ``PrimitiveRef`` implements both -- no substrate-side
override needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Self

from nu.domains.shape import ReactiveItemRef, Slot
from nu.forms import Bool, Bytes, Float, Int, None_, Str

from .base import PrimitiveRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import IntArg, StrArg


__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "StrRef",
]


class ItemRef(ReactiveItemRef, PrimitiveRef):
    """An untyped leaf slot in KV storage: read it, set it, erase it, watch it.

    The value type and the Form its reads are wrapped in are both given at
    declaration time, so one class covers any leaf whose type is only known
    where the slot is written. A typed sibling (``IntRef``, ``StrRef``, ...)
    is the same leaf with that pair fixed and the matching operator surface
    mixed in.

    Notes:
        - Carries no operator surface of its own; reach for a typed ref when
          the value should support arithmetic, comparison or string ops.
        - Reads yield EMPTY when the leaf is absent rather than raising.
        - ``on_change`` works with no substrate-side wiring, because the leaf
          navigation already exposes the parent view and the address.

    Example:
        class Bag(Shape):
            payload = ItemRef.slot(str, Str)
        run(Bag.payload.set("hello"), ctx)
        run(Bag.payload, ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        value_type: type,
        value_value_type: type,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address, value_type=value_type, parent_ref=parent_ref, owner_shape=owner_shape
        )
        self._payload["value_value_type"] = value_value_type

    @classmethod
    def slot(cls, value_type: type, value_value_type: type) -> Self:
        """Declare a generic item slot for ``value_type`` (with its Form)."""
        return Slot(cls, value_type=value_type, value_value_type=value_value_type)  # type: ignore[return-value]


# =============================================================================
# TYPED REFS (with primitive Form interface)
# =============================================================================


class IntRef(ItemRef, Int):
    """An int leaf in KV storage, carrying the whole Int operator surface.

    Notes:
        - Stored as a plain int, so the stored form and the value form are
          the same and nothing is translated on the way in or out.
        - Arithmetic on the ref builds an expression over the stored value;
          writing the result back is what ``set``, ``inc`` and ``dec`` do.

    Example:
        class Counter(Shape):
            hits = IntRef.slot()
        run(Counter.hits.set(0), ctx)
        run(Counter.hits.inc(), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=int,
            value_value_type=Int,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    def inc(self, step: IntArg = 1) -> None_:
        """Add ``step`` to the stored int and write the result back.

        Args:
            step: how much to add. May be an expression, not just a literal.

        Notes:
            - Read-modify-write in one term, not a storage-level atomic
              increment; wrap it in a transaction when concurrent writers
              can touch the same leaf.
            - An absent leaf reads as EMPTY, so the addition collapses to
              INVALID and the write refuses to store a sentinel. Set the
              slot before incrementing it.

        Example:
            run(Counter.hits.inc(), ctx)
        """
        return self.set(self + step)

    def dec(self, step: IntArg = 1) -> None_:
        """Subtract ``step`` from the stored int and write the result back.

        Args:
            step: how much to subtract. May be an expression.

        Notes:
            - Same read-modify-write shape as ``inc``, and the same refusal
              to store a sentinel when the leaf is absent.

        Example:
            run(Counter.hits.dec(2), ctx)
        """
        return self.set(self - step)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class StrRef(ItemRef, Str):
    """A str leaf in KV storage, carrying the whole Str operator surface.

    Notes:
        - Stored as a plain str, so nothing is translated on read or write.
        - Doubles as a key source: a str leaf can be the address of another
          ref, and it is resolved when the path is walked.

    Example:
        class Portfolio(Shape):
            name = StrRef.slot()
        run(Portfolio.name.set("core"), ctx)
        run(Portfolio.name.upper(), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(ItemRef, Float):
    """A float leaf in KV storage, carrying the whole Float operator surface.

    Notes:
        - Stored as a plain float, so nothing is translated on read or write.
        - Reach for DecimalRef instead when the value is money or anything
          else that must round-trip exactly.

    Example:
        class Order(Shape):
            price = FloatRef.slot()
        run(Order.price.set(12.5), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=float,
            value_value_type=Float,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(ItemRef, Bool):
    """A bool leaf in KV storage, carrying the whole Bool logical surface.

    Notes:
        - Stored as a plain bool, so nothing is translated on read or write.
        - An absent leaf reads as EMPTY, which is not False; test with
          ``exists`` or ``is_empty`` when the difference matters.

    Example:
        class Flags(Shape):
            live = BoolRef.slot()
        run(Flags.live.set(True), ctx)
        run(Flags.live.not_(), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=bool,
            value_value_type=Bool,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(ItemRef, Bytes):
    """A bytes leaf in KV storage, carrying the whole Bytes operator surface.

    Notes:
        - Stored as plain bytes, so nothing is translated on read or write.
        - The leaf a raw payload belongs in: no decoding happens on the way
          through, unlike the std refs that serialize a domain type.

    Example:
        class Blob(Shape):
            raw = BytesRef.slot()
        run(Blob.raw.set(b"payload"), ctx)
        run(Blob.raw.hex_(), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=bytes,
            value_value_type=Bytes,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]
