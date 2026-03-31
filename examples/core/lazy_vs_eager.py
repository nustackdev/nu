"""Lazy/eager facets on eb-virtuals refs.

Shows how .lazy (default) and .eager change iteration behavior
over virtuals-backed collections.
"""

from __future__ import annotations

import asyncio

from virtuals.tkv.storage import StorageProtocol, TransactionProtocol
from virtuals.view import View
from virtuals.views import DictView

from nu_virtuals import (
    DictRef,
    FloatRef,
    IntRef,
    ListRef,
    ShapesListRef,
    StrRef,
)
from nu_virtuals.presets import memory_storage
from nu_virtuals.refs.base import Facet
from nu import Context
from nu.abc import Print, Seq
from nu.shape import Shape


class Order(Shape):
    symbol = StrRef.slot()
    price = FloatRef.slot()
    qty = IntRef.slot()


class Portfolio(Shape):
    name = StrRef.slot()
    orders = ShapesListRef.slot(Order)
    tags = ListRef.slot(str)
    metadata = DictRef.slot(str)


async def store(ref, value, ctx):
    await ref.store(value).execute(ctx)


async def main():
    with memory_storage() as storage:
        with storage.transaction() as tx:
            root = DictView.open_root(ctx=tx)
            ctx = (
                Context()
                .bind(root, View)
                .bind(root, View, Portfolio)
                .bind(tx, TransactionProtocol)
                .bind(tx, TransactionProtocol, Portfolio)
                .bind(storage, StorageProtocol)
                .bind(storage, StorageProtocol, Portfolio)
            )

            # populate
            await store(Portfolio.name, "Main", ctx)
            await store(Portfolio.tags, ["alpha", "beta", "gamma"], ctx)
            await store(Portfolio.metadata, {"strategy": "momentum", "risk": "medium"}, ctx)
            await store(
                Portfolio.orders,
                [
                    {"symbol": "AAPL", "price": 185.5, "qty": 10},
                    {"symbol": "GOOG", "price": 142.3, "qty": 5},
                    {"symbol": "TSLA", "price": 245.0, "qty": 3},
                ],
                ctx,
            )

            # --- slot navigation ---
            print("=== Slot Navigation ===")
            print(f"  name: {await Portfolio.name.execute(ctx)}")
            print(
                f"  orders[0]: {await Portfolio.orders[0].symbol.execute(ctx)} "
                f"@ {await Portfolio.orders[0].price.execute(ctx)}"
            )
            print(
                f"  orders[1]: {await Portfolio.orders[1].symbol.execute(ctx)} "
                f"@ {await Portfolio.orders[1].price.execute(ctx)}"
            )

            # --- lazy iteration (default) ---
            print("\n=== Lazy Iteration (default) ===")
            meta_ref = Portfolio.metadata
            print(f"  facet: {meta_ref._facet}")

            keys = meta_ref.keys()
            print(f"  .keys() type: {type(keys).__name__}")
            print(f"  keys: {list(await keys.execute(ctx))}")

            vals = meta_ref.values()
            print(f"  .values() type: {type(vals).__name__}")
            print(f"  values: {list(await vals.execute(ctx))}")

            items = meta_ref.items()
            print(f"  .items() type: {type(items).__name__}")
            print(f"  items: {list(await items.execute(ctx))}")

            # --- eager iteration ---
            print("\n=== Eager Iteration ===")
            eager_ref = Portfolio.metadata.eager
            print(f"  facet: {eager_ref._facet}")

            keys_e = eager_ref.keys()
            print(f"  .keys() type: {type(keys_e).__name__}")
            print(f"  keys: {list(await keys_e.execute(ctx))}")

            vals_e = eager_ref.values()
            print(f"  values: {list(await vals_e.execute(ctx))}")

            # --- facet switching ---
            print("\n=== Facet Switching ===")
            ref = Portfolio.metadata
            print(f"  default facet: {ref._facet}")
            print(f"  .eager facet:  {ref.eager._facet}")
            print(f"  .lazy facet:   {ref.lazy._facet}")
            print(f"  .eager.lazy:   {ref.eager.lazy._facet}")
            print(f"  lazy is no-op: {ref._facet is Facet.LAZY}")

            # --- term composition ---
            print("\n=== Term Composition ===")
            total = Portfolio.orders[0].price * Portfolio.orders[0].qty
            print(f"  AAPL total: {await total.execute(ctx)}")

            spread = Portfolio.orders[0].price - Portfolio.orders[2].price
            print(f"  AAPL-TSLA spread: {await spread.execute(ctx)}")

            # --- flow ---
            print("\n=== Flow ===")
            flow = Seq(
                Print("order[0]", Portfolio.orders[0].symbol),
                Print("order[1]", Portfolio.orders[1].symbol),
                Print("order[2]", Portfolio.orders[2].symbol),
            )
            await flow.execute(ctx)


if __name__ == "__main__":
    asyncio.run(main())
