"""Shape system demo — line-by-line capability showcase."""

from __future__ import annotations

from pathlib import Path

import everypv as e
from everybase import Context
from everyshape import Shape


# =============================================================================
# SHAPES
# =============================================================================


class SymbolInfo(Shape):
    """Individual symbol information."""

    price = e.FloatRef.slot()
    volume = e.IntRef.slot()
    exchange = e.StrRef.slot()


class Order(Shape):
    """Order information."""

    id = e.StrRef.slot()
    symbol = e.StrRef.slot()
    quantity = e.IntRef.slot()
    price = e.FloatRef.slot()


class Market(Shape):
    """Market data with various collection types."""

    misc_val = e.IntRef.slot()
    signals = e.DictRef.slot(value_type=float)
    prices = e.ListRef.slot(item_type=float)
    symbols = e.ShapesDictRef.slot(shape_type=SymbolInfo)
    orders = e.ShapesListRef.slot(shape_type=Order)
    last_order = e.ShapeRef.slot(shape_type=Order)


# =============================================================================
# DEMO
# =============================================================================


async def run(ctx: Context) -> None:
    # --- Primitive fields ---------------------------------------------------
    await SymbolInfo.volume.set(12).execute(ctx)
    await SymbolInfo.exchange.set("hello").execute(ctx)
    print("set volume:", await SymbolInfo.volume.get().execute(ctx))
    print("arith:", await (SymbolInfo.volume + SymbolInfo.volume).execute(ctx))
    print("str expr:", await (SymbolInfo.exchange.get() + "12").and_(None).execute(ctx))

    # --- Dict of primitives -------------------------------------------------
    await Market.signals["vix"].set(23.5).execute(ctx)
    await Market.signals["sentiment"].set(0.75).execute(ctx)
    print("vix:", await Market.signals["vix"].get().execute(ctx))
    print("sentiment:", await Market.signals["sentiment"].get().execute(ctx))

    # --- List of primitives -------------------------------------------------
    await Market.misc_val.set(1).execute(ctx)
    await Market.prices.store([100.5, 101.2, 99.8]).execute(ctx)
    print("price[0]:", await Market.prices[0].get().execute(ctx))
    print("price[1]:", await Market.prices[1].get().execute(ctx))
    print("prices:", await Market.prices.extract().execute(ctx))
    print(
        "map+filter:",
        await Market.prices.extract().map_(lambda x: x * 2).filter_(lambda x: x > 200).execute(ctx),
    )
    print(
        "dynamic idx:", await (Market.prices[Market.misc_val.get()].get() + 12 > 100).execute(ctx)
    )

    # --- Shape (single) -----------------------------------------------------
    await Market.last_order.id.set("ID").execute(ctx)
    print("shape extract:", await Market.last_order.extract().execute(ctx))

    # --- Dict of shapes -----------------------------------------------------
    await (
        Market.symbols["AAPL"]
        .store(
            {"price": 150.0, "volume": 1000000, "exchange": "NASDAQ"},
        )
        .execute(ctx)
    )
    await (
        Market.symbols["GOOGL"]
        .store(
            {"price": 2800.0, "volume": 500000, "exchange": "NASDAQ"},
        )
        .execute(ctx)
    )
    print("AAPL price:", await Market.symbols["AAPL"].price.get().execute(ctx))
    print("GOOGL exch:", await Market.symbols["GOOGL"].exchange.get().execute(ctx))
    print("AAPL data:", await Market.symbols["AAPL"].extract().execute(ctx))

    # --- List of shapes -----------------------------------------------------
    await Market.orders.store(
        [
            {"id": "ORD001", "symbol": "AAPL", "quantity": 100, "price": 150.0},
            {"id": "ORD002", "symbol": "GOOGL", "quantity": 50, "price": 2800.0},
        ]
    ).execute(ctx)
    print("order[0].id:", await Market.orders[0].id.get().execute(ctx))
    print("order[1].sym:", await Market.orders[1].symbol.get().execute(ctx))
    print("order[0]:", await Market.orders[0].extract().execute(ctx))


# =============================================================================
# INFRA
# =============================================================================

if __name__ == "__main__":
    import asyncio

    from pv import View

    from everypv.adapters.codecs import TextCodec
    from everypv.adapters.storages.textdb import TextStorage
    from everypv.views import DictView

    async def main() -> None:
        with (
            TextStorage(path=Path(".db_shape"), codec=TextCodec()) as storage,
            storage.transaction() as tx,
        ):
            root = DictView.open_root(tx)
            ctx = (
                Context()
                .with_handle(View, root, SymbolInfo)
                .with_handle(View, root, Order)
                .with_handle(View, root, Market)
            )
            await run(ctx)

    asyncio.run(main())
