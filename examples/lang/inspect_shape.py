"""Rendering a Shape and its storage with ``render_shape``.

``nu.inspect.render_shape`` walks a Shape's ``_slots`` and prints the backing
storage as a tree - scalars inline, collections counted, nested Shapes expanded.
Handy for eyeballing what actually sits behind a Shape at a REPL. Here the
storage is a plain dict; a live substrate view renders the same way.
"""

from __future__ import annotations

from nu.domains.shape import Shape, Slot
from nu.domains.shape.refs.item import ItemRef
from nu.domains.shape.refs.mapping import MappingRef
from nu.domains.shape.refs.sequence import SequenceRef
from nu.domains.shape.refs.shape import ShapeRef
from nu.inspect import render_shape


class Fill(Shape):
    price = Slot(ItemRef)
    qty = Slot(ItemRef)


class Order(Shape):
    symbol = Slot(ItemRef)
    tags = Slot(SequenceRef)
    meta = Slot(MappingRef)
    last_fill = Slot(ShapeRef, shape_type=Fill)


storage = {
    "symbol": "SOL",
    "tags": ["limit", "post-only"],
    "meta": {"venue": "pump", "slippage": 0.5},
    "last_fill": {"price": 142.7, "qty": 3},
}

print(render_shape(Order, storage, as_="plain"))
