"""nu-virtuals fabric: shapes over a real RocksDB store.

The virtuals fabric backs shapes with the ``virtuals`` storage engine. A
preset factory (here ``rocksdb_storage_inmemory``) opens the store, a
``Navigator`` reads the tree, and a transaction carries the writes. The
context binds both, type-first, at the root and per shape.

Values land on disk through the binary codec, so reads go through async
views: ``arun`` drives the whole thing. Writes use the ``.store(...)``
command. Two shapes below, five expressions each. Every entry prints the
run result, the term type, and the expression itself - so you can see each
one is a typed Nu term, not a bare value.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from nu import Context, arun
from nu.domains.shape import Shape
from nu_virtuals import (
    DictRef,
    FloatRef,
    IntRef,
    ListRef,
    SetRef,
    ShapesListRef,
    StrRef,
)
from nu_virtuals.presets import rocksdb_storage_inmemory
from virtuals import Navigator
from virtuals.tkv.storage import TransactionProtocol


# ============================================================================
# Shape 1: Order - primitives and arithmetic over them
# ============================================================================


class Order(Shape):
    symbol = StrRef.slot()
    price = FloatRef.slot()
    qty = IntRef.slot()


# ============================================================================
# Shape 2: Portfolio - collections and nested shapes
# ============================================================================


class Portfolio(Shape):
    name = StrRef.slot()
    tags = ListRef.slot(str)
    metadata = DictRef.slot(str)
    members = SetRef.slot(str)
    orders = ShapesListRef.slot(Order)


def scoped(nav: Navigator, tx: TransactionProtocol, shape: type[Shape]) -> Context:
    """Context with Navigator + transaction bound at root and for one shape."""
    return (
        Context()
        .bind(Navigator, nav)
        .bind(Navigator, nav, shape)
        .bind(TransactionProtocol, tx)
        .bind(TransactionProtocol, tx, shape)
    )


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "db")
        with rocksdb_storage_inmemory(db_path) as storage:
            nav = Navigator(storage)
            with storage.transaction() as tx:
                # --- Order: populate, then five expressions ---
                order = scoped(nav, tx, Order)
                await arun(Order.symbol.store("AAPL"), order)
                await arun(Order.price.store(185.5), order)
                await arun(Order.qty.store(10), order)

                # 1. Read a primitive back through a view.
                e1 = Order.symbol
                print((await arun(e1, order))[0], type(e1), e1)

                # 2. Compose two refs: notional = price * qty.
                e2 = Order.price * Order.qty
                print((await arun(e2, order))[0], type(e2), e2)

                # 3. Comparisons fold to booleans.
                e3 = Order.price > 100
                print((await arun(e3, order))[0], type(e3), e3)

                # 4. Mix a ref with a literal.
                e4 = Order.qty + 5
                print((await arun(e4, order))[0], type(e4), e4)

                # 5. A store command - now a typed StoreCommand, not a bare object.
                e5 = Order.symbol.store("MSFT")
                print((await arun(e5, order))[0], type(e5), e5)

                # --- Portfolio: populate, then five expressions ---
                pf = scoped(nav, tx, Portfolio)
                await arun(Portfolio.name.store("Main"), pf)
                await arun(Portfolio.tags.store(["alpha", "beta", "gamma"]), pf)
                await arun(Portfolio.metadata.store({"strategy": "momentum", "risk": "medium"}), pf)
                await arun(Portfolio.members.store({"alice", "bob"}), pf)
                await arun(
                    Portfolio.orders.store(
                        [
                            {"symbol": "AAPL", "price": 185.5, "qty": 10},
                            {"symbol": "GOOG", "price": 142.3, "qty": 5},
                        ]
                    ),
                    pf,
                )

                # 1. First element of a list ref.
                p1 = Portfolio.tags.first_elem()
                print((await arun(p1, pf))[0], type(p1), p1)

                # 2. Look a value up in a dict ref by key.
                p2 = Portfolio.metadata.get("strategy")
                print((await arun(p2, pf))[0], type(p2), p2)

                # 3. Set ref union against a plain set.
                p3 = Portfolio.members.union({"carol"})
                print((await arun(p3, pf))[0], type(p3), p3)

                # 4. Descend into a nested shape held in a list of shapes.
                p4 = Portfolio.orders[1].symbol
                print((await arun(p4, pf))[0], type(p4), p4)

                # 5. A mutating append command writes back to the store.
                p5 = Portfolio.tags.append("delta")
                print((await arun(p5, pf))[0], type(p5), p5)


asyncio.run(main())
