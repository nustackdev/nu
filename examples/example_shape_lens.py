"""Shape lens demo — visualize shape storage data in the terminal.

Shows print_shape with the PV substrate.
"""

from __future__ import annotations

import asyncio

import everypv as pv
from eb_shape_lens import print_shape
from everybase import Context
from everyshape import Shape


# ── Shapes ────────────────────────────────────────────────────────────────────


class SymbolInfo(Shape):
    price = pv.FloatRef.slot()
    volume = pv.IntRef.slot()
    exchange = pv.StrRef.slot()


class Order(Shape):
    id = pv.StrRef.slot()
    symbol = pv.StrRef.slot()
    quantity = pv.IntRef.slot()
    price = pv.FloatRef.slot()


class Market(Shape):
    misc_val = pv.IntRef.slot()
    signals = pv.DictRef.slot(value_type=float)
    prices = pv.ListRef.slot(item_type=float)
    symbols = pv.ShapesDictRef.slot(shape_type=SymbolInfo)
    orders = pv.ShapesListRef.slot(shape_type=Order)
    last_order = pv.ShapeRef.slot(shape_type=Order)


# ── PV substrate demo ────────────────────────────────────────────────────────


async def run_pv() -> None:
    import time

    from pv import View

    from everypv.adapters.storage import rocksdb_storage_inmemory
    from everypv.views import DictView

    db_path = ".db_shape_lens"

    with (
        rocksdb_storage_inmemory(db_path) as storage,
        storage.transaction() as tx,
    ):
        root = DictView.open_root(tx)
        ctx = (
            Context()
            .with_handle(View, root, SymbolInfo)
            .with_handle(View, root, Order)
            .with_handle(View, root, Market)
        )

        # Populate
        await Market.misc_val.set(42).execute(ctx)
        await Market.signals.store({"vix": 23.5, "sentiment": 0.75, "rsi": 67.2}).execute(ctx)
        await Market.prices.store([100.5, 101.2, 99.8, 102.0, 98.7]).execute(ctx)

        # 100K symbols via compound .store()
        t0 = time.time()
        for i in range(100_000):
            await (
                Market.symbols[f"SYM_{i:06d}"]
                .store(
                    {"price": float(i) * 0.01, "volume": i * 10, "exchange": "NYSE"},
                )
                .execute(ctx)
            )
        t1 = time.time()
        print(f"  populated 100K symbols in {t1 - t0:.1f}s")

        await Market.orders.store(
            [
                {"id": "ORD-001", "symbol": "AAPL", "quantity": 100, "price": 150.0},
                {"id": "ORD-002", "symbol": "GOOGL", "quantity": 50, "price": 2800.0},
            ]
        ).execute(ctx)
        await Market.last_order.store(
            {"id": "ORD-002", "symbol": "GOOGL", "quantity": 50, "price": 2800.0},
        ).execute(ctx)

        # Print — pass the PV view directly, renderer iterates lazily
        t2 = time.time()
        print_shape(Market, root)
        t3 = time.time()
        print(f"\n  rendered in {t3 - t2:.4f}s")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== PV substrate ===")
    print()
    asyncio.run(run_pv())
