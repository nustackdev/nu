"""kv leaves: one value at one address, read and written whole.

``ItemRef`` is the leaf itself (slot-level read, write, erase and observe over
a kv leaf) and declares a slot once for every leaf. Each value leaf mixes in
the reactive shape cell of its value (``ReactivePyIntRef`` for an int), so the
ref is an operand of the value it names; the cell decides the surface, the leaf
decides where the value lives.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Self

from nu.domains.shape import (
    ReactiveItemRef,
    ReactivePyBoolRef,
    ReactivePyBytesRef,
    ReactivePyFloatRef,
    ReactivePyIntRef,
    ReactivePyObjectRef,
    ReactivePyStrRef,
    Slot,
)

from .base import PrimitiveRef


if TYPE_CHECKING:
    from nu.forms import None_
    from nu.lang import IntArg

__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ObjectRef",
    "StrRef",
]


class ItemRef(ReactiveItemRef, PrimitiveRef):
    """A leaf slot in KV storage: read it, set it, erase it, watch it.

    The base every kv leaf builds on. It carries no value surface of its own;
    a leaf class mixes in the reactive shape cell of the value it holds
    (``IntRef`` is this plus ``ReactivePyIntRef``), and that one pairing is the
    whole of a leaf class.

    Notes:
        - Reads yield NULL, hinted with the path, when the leaf is absent.
        - ``on_change`` works with no substrate-side wiring, because the leaf
          navigation already exposes the parent view and the address.
    """

    @classmethod
    def slot(cls) -> Self:
        """Declare a slot holding this leaf."""
        return Slot(cls)  # type: ignore[return-value]


class ObjectRef(ItemRef, ReactivePyObjectRef):
    """A leaf in KV storage holding a value of no declared type.

    What a container descends to when its value is ``object``, undeclared, or
    a type with no kv leaf of its own. It carries the whole ``Object`` surface,
    so the ref is still an operand: ``==`` builds an ``Eq``, attribute and
    subscript access descend into the value read, and a cast narrows it.

    Notes:
        - A dict or list stored here reads back as a plain value, not a View.

    Example:
        class Bag(Shape):
            meta = DictRef.slot(object)
        run(Bag.meta["title"] == "hello", ctx)
        run(nu.Str(Bag.meta["title"]).upper(), ctx)
    """


# =============================================================================
# TYPED REFS (with primitive Form interface)
# =============================================================================


class IntRef(ItemRef, ReactivePyIntRef):
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

    def inc(self, step: IntArg = 1) -> None_:
        """Add ``step`` to the stored int and write the result back.

        Args:
            step: how much to add. May be an expression, not just a literal.

        Notes:
            - Read-modify-write in one term, not a storage-level atomic
              increment; wrap it in a transaction when concurrent writers
              can touch the same leaf.
            - An absent leaf reads as NULL and NULL has no ``+``, so this
              raises TypeError. Set the slot before incrementing it.

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


class StrRef(ItemRef, ReactivePyStrRef):
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


class FloatRef(ItemRef, ReactivePyFloatRef):
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


class BoolRef(ItemRef, ReactivePyBoolRef):
    """A bool leaf in KV storage, carrying the whole Bool logical surface.

    Notes:
        - Stored as a plain bool, so nothing is translated on read or write.
        - An absent leaf reads as NULL, which is falsy but not False; test
          ``== False`` or ``is_set_falsy()`` when the difference matters.

    Example:
        class Flags(Shape):
            live = BoolRef.slot()
        run(Flags.live.set(True), ctx)
        run(Flags.live.not_(), ctx)
    """


class BytesRef(ItemRef, ReactivePyBytesRef):
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
