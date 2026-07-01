"""nu-mem fabric: shapes over a plain in-memory dict.

The mem fabric is the simplest substrate. A Shape describes the layout, a
bare Python dict holds the data, and ``Context().bind(dict, data, Shape)``
wires the two together. Refs read and write straight into the dict, so the
same dict you pass in is the one that gets mutated.

mem provides both sync and async thunks, so plain ``run`` works for the
whole thing. Two shapes below, five expressions each. Every entry prints
the run result, the term type, and the expression itself - so you can see
each one is a typed Nu term, not a bare value.
"""

from __future__ import annotations

from nu import Context, run
from nu.domains.shape import Shape
from nu.mem import (
    DictRef,
    FloatRef,
    IntRef,
    ListRef,
    SetRef,
    ShapesListRef,
    StrRef,
)


# ============================================================================
# Shape 1: Order - primitives and arithmetic over them
# ============================================================================


class Order(Shape):
    symbol = StrRef.slot()
    price = FloatRef.slot()
    qty = IntRef.slot()


order_data = {"symbol": "AAPL", "price": 185.5, "qty": 10}
order_ctx = Context().bind(dict, order_data, Order)

# 1. Read a primitive straight off the dict.
e1 = Order.symbol
print(run(e1, order_ctx)[0], type(e1), e1)

# 2. Compose two refs into one arithmetic term: notional = price * qty.
e2 = Order.price * Order.qty
print(run(e2, order_ctx)[0], type(e2), e2)

# 3. Comparisons fold to booleans.
e3 = Order.price > 100
print(run(e3, order_ctx)[0], type(e3), e3)

# 4. Mix a ref with a literal.
e4 = Order.qty + 5
print(run(e4, order_ctx)[0], type(e4), e4)

# 5. A store command - now a typed StoreCommand, not a bare object.
e5 = Order.symbol.store("MSFT")
print(run(e5, order_ctx)[0], type(e5), e5)


# ============================================================================
# Shape 2: Portfolio - collections and nested shapes
# ============================================================================


class Portfolio(Shape):
    name = StrRef.slot()
    tags = ListRef.slot(str)
    metadata = DictRef.slot(str)
    members = SetRef.slot(str)
    orders = ShapesListRef.slot(Order)


portfolio_data = {
    "name": "Main",
    "tags": ["alpha", "beta", "gamma"],
    "metadata": {"strategy": "momentum", "risk": "medium"},
    "members": {"alice", "bob"},
    "orders": [
        {"symbol": "AAPL", "price": 185.5, "qty": 10},
        {"symbol": "GOOG", "price": 142.3, "qty": 5},
    ],
}
portfolio_ctx = Context().bind(dict, portfolio_data, Portfolio)

# 1. First element of a list ref.
p1 = Portfolio.tags.first_elem()
print(run(p1, portfolio_ctx)[0], type(p1), p1)

# 2. Look a value up in a dict ref by key.
p2 = Portfolio.metadata.get("strategy")
print(run(p2, portfolio_ctx)[0], type(p2), p2)

# 3. Set ref union against a plain set.
p3 = Portfolio.members.union({"carol"})
print(run(p3, portfolio_ctx)[0], type(p3), p3)

# 4. Descend into a nested shape held in a list of shapes.
p4 = Portfolio.orders[1].symbol
print(run(p4, portfolio_ctx)[0], type(p4), p4)

# 5. A mutating append command writes back into the same dict.
p5 = Portfolio.tags.append("delta")
print(run(p5, portfolio_ctx)[0], type(p5), p5)
