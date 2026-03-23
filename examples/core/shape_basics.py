"""Shape system demo — line-by-line capability showcase."""

from __future__ import annotations

import eb_virtuals as ebv
from everybase import Context
from everybase.abc import fn
from everybase.shape import Shape


# =============================================================================
# SHAPES
# =============================================================================


class SymbolInfo(Shape):
    """Individual symbol information."""

    price = ebv.FloatRef.slot()
    volume = ebv.IntRef.slot()
    exchange = ebv.StrRef.slot()


class Order(Shape):
    """Order information."""

    id = ebv.StrRef.slot()
    symbol = ebv.StrRef.slot()
    quantity = ebv.IntRef.slot()
    price = ebv.FloatRef.slot()


class Market(Shape):
    """Market data with various collection types."""

    misc_val = ebv.IntRef.slot()
    signals = ebv.DictRef.slot(value_type=float)
    prices = ebv.ListRef.slot(item_type=float)
    symbols = ebv.ShapesDictRef.slot(shape_type=SymbolInfo)
    orders = ebv.ShapesListRef.slot(shape_type=Order)
    last_order = ebv.ShapeRef.slot(shape_type=Order)


# =============================================================================
# DEMO
# =============================================================================


async def run(ctx: Context) -> None:
    # --- Primitive fields ---------------------------------------------------
    await SymbolInfo.volume.store(12).execute(ctx)
    await SymbolInfo.exchange.store("hello").execute(ctx)
    print("set volume:", await SymbolInfo.volume.execute(ctx))
    print("arith:", await (SymbolInfo.volume + SymbolInfo.volume).execute(ctx))
    print("str expr:", await (SymbolInfo.exchange + "12").and_(None).execute(ctx))

    # --- Dict of primitives -------------------------------------------------
    await Market.signals["vix"].store(23.5).execute(ctx)
    await Market.signals["sentiment"].store(0.75).execute(ctx)
    print("vix:", await Market.signals["vix"].execute(ctx))
    print("sentiment:", await Market.signals["sentiment"].execute(ctx))

    # --- List of primitives -------------------------------------------------
    await Market.misc_val.store(1).execute(ctx)
    await Market.prices.store([100.5, 101.2, 99.8]).execute(ctx)
    print("price[0]:", await Market.prices[0].execute(ctx))
    print("price[1]:", await Market.prices[1].execute(ctx))
    print("prices:", await Market.prices.execute(ctx))
    print(
        "map+filter:",
        await fn.Filter(fn.Map(Market.prices, lambda x: x * 2), lambda x: x > 200).execute(ctx),
    )
    print("dynamic idx:", await (Market.prices[Market.misc_val] + 12 > 100).execute(ctx))

    # --- Shape (single) -----------------------------------------------------
    await Market.last_order.id.store("ID").execute(ctx)
    print("shape extract:", await Market.last_order.execute(ctx))

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
    print("AAPL price:", await Market.symbols["AAPL"].price.execute(ctx))
    print("GOOGL exch:", await Market.symbols["GOOGL"].exchange.execute(ctx))
    print("AAPL data:", await Market.symbols["AAPL"].execute(ctx))

    # --- List of shapes -----------------------------------------------------
    await Market.orders.store(
        [
            {"id": "ORD001", "symbol": "AAPL", "quantity": 100, "price": 150.0},
            {"id": "ORD002", "symbol": "GOOGL", "quantity": 50, "price": 2800.0},
        ]
    ).execute(ctx)
    print("order[0].id:", await Market.orders[0].id.execute(ctx))
    print("order[1].sym:", await Market.orders[1].symbol.execute(ctx))
    print("order[0]:", await Market.orders[0].execute(ctx))


# =============================================================================
# INFRA
# =============================================================================

if __name__ == "__main__":
    import asyncio

    from virtuals import View
    from virtuals.views import DictView

    from eb_virtuals.presets import text_storage

    async def main() -> None:
        with text_storage(path=".db-shape") as storage, storage.transaction() as tx:
            root = DictView.open_root(tx)
            ctx = Context().bind(root, View)
            await run(ctx)

    asyncio.run(main())
