"""Example demonstrating mapping and sequence support in Shape system.

This example shows:
1. Mapping of primitives (dict-like)
2. Mapping of shapes (dict of structured objects)
3. Sequence of primitives (list-like)
4. Sequence of shapes (list of structured objects)
5. Nested collections (infinite nesting)
"""

from __future__ import annotations

from pathlib import Path

import every_pv as e
from everyabc import Context


class SymbolInfo(e.Shape):
    """Individual symbol information."""

    price = e.FloatRef.slot()
    volume = e.IntRef.slot()
    exchange = e.StrRef.slot()
    yo = e.BytesRef.slot()


class Order(e.Shape):
    """Order information."""

    id = e.StrRef.slot()
    symbol = e.StrRef.slot()
    quantity = e.IntRef.slot()
    price = e.FloatRef.slot()


class Market(e.Shape):
    """Market data with various collection types."""

    misc_val = e.IntRef.slot()
    signals = e.DictRef.slot(value_type=float)
    prices = e.ListRef.slot(item_type=float)
    symbols = e.ShapesDictRef.slot(shape_type=SymbolInfo)
    orders = e.ShapesListRef.slot(shape_type=Order)
    last_order = e.ShapeRef.slot(shape_type=Order)


# =============================================================================
# EXAMPLES
# =============================================================================


async def example_mapping_primitives(ctx: Context) -> None:
    """Example: mapping of primitive values."""
    print("\n=== Mapping of Primitives ===")

    await Market.signals["vix"].set(23.5).execute(ctx)
    await Market.signals["sentiment"].set(0.75).execute(ctx)

    # Get values
    vix = await Market.signals["vix"].get().execute(ctx)
    sentiment = await Market.signals["sentiment"].get().execute(ctx)

    print(f"VIX: {vix}")
    print(f"Sentiment: {sentiment}")


async def example_sequence_primitives(ctx: Context) -> None:
    """Example: sequence of primitive values."""
    print("\n=== Sequence of Primitives ===")

    await Market.misc_val.set(1).execute(ctx)

    # Set values at indices
    a = Market.prices.append(100.5)
    print("append res", await a.execute(ctx))
    await Market.prices.append(101.2).execute(ctx)
    await Market.prices.append(99.8).execute(ctx)

    # Get values
    price_0 = await Market.prices[0].get().execute(ctx)
    price_1 = await Market.prices[1].get().execute(ctx)
    price_2 = (
        await Market.prices.get().map_(lambda x: x * 2).filter_(lambda a: a > 200).execute(ctx)
    )

    print(f"Prices: [{price_0}, {price_1}, {price_2}]")

    prices = await Market.prices.get().execute(ctx)
    print(prices)

    nested_acc = await (Market.prices[Market.misc_val.get()].get() + 12 > 100).execute(ctx)
    print(nested_acc)

    await Market.last_order.id.set("ID").execute(ctx)
    print(await Market.last_order.get().execute(ctx))


async def example_mapping_shapes(ctx: Context) -> None:
    """Example: mapping of shapes."""
    print("\n=== Mapping of Shapes ===")

    # Store shape data
    await (
        Market.symbols["AAPL"]
        .store(
            {
                "price": 150.0,
                "volume": 1000000,
                "exchange": "NASDAQ",
            }
        )
        .execute(ctx)
    )

    await (
        Market.symbols["GOOGL"]
        .store(
            {
                "price": 2800.0,
                "volume": 500000,
                "exchange": "NASDAQ",
            }
        )
        .execute(ctx)
    )

    # Access nested fields
    aapl_price = await Market.symbols["AAPL"].price.get().execute(ctx)
    googl_exchange = await Market.symbols["GOOGL"].exchange.get().execute(ctx)

    print(f"AAPL Price: {aapl_price}")
    print(f"GOOGL Exchange: {googl_exchange}")

    # get entire shape
    aapl_data = await Market.symbols["AAPL"].get().execute(ctx)
    print(f"AAPL Data: {aapl_data}")


async def example_sequence_shapes(ctx: Context) -> None:
    """Example: sequence of shapes."""
    print("\n=== Sequence of Shapes ===")

    # Store shape data
    await Market.orders.append(
        {
            "id": "ORD001",
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.0,
        }
    ).execute(ctx)

    await Market.orders.append(
        {
            "id": "ORD002",
            "symbol": "GOOGL",
            "quantity": 50,
            "price": 2800.0,
        }
    ).execute(ctx)

    # Access nested fields
    order_0_id = await Market.orders[0].id.get().execute(ctx)
    order_1_symbol = await Market.orders[1].symbol.get().execute(ctx)

    print(f"Order 0 ID: {order_0_id}")
    print(f"Order 1 Symbol: {order_1_symbol}")

    # get entire shape
    order_0_data = await Market.orders[0].get().execute(ctx)
    print(f"Order 0 Data: {order_0_data}")


if __name__ == "__main__":
    import asyncio

    from pv import View

    from every_pv.adapters.codecs import TextCodec
    from every_pv.adapters.storages.textdb import TextStorage
    from every_pv.views import DictView
    from everyshape import Shape

    async def main() -> None:
        with (
            TextStorage(path=Path(".db_shape"), codec=TextCodec()) as storage,
            storage.transaction() as tx,
        ):
            root = DictView.open_root(tx)
            ctx = Context().with_handle(View, root, Shape)

            set_res = SymbolInfo.volume.set(12)
            set_res = await set_res.execute(ctx)
            print(set_res)

            await SymbolInfo.exchange.set("hello").execute(ctx)
            await SymbolInfo.yo.set(b"hello").execute(ctx)

            c = SymbolInfo.volume.get() + SymbolInfo.volume
            c = await c.execute(ctx)
            print(c)

            a = (SymbolInfo.exchange.get() + "12").and_(None)
            resa = await a.execute(ctx)
            print("A", resa)
            print("=" * 60)

            x = SymbolInfo.yo.get()[:3]
            resx = await x.execute(ctx)
            print("X", resx)

            print("Shape Collections Example")
            print("=" * 60)

            # Run examples
            await example_mapping_primitives(ctx)
            await example_sequence_primitives(ctx)
            await example_mapping_shapes(ctx)
            await example_sequence_shapes(ctx)

            print("\n" + "=" * 60)
            print("All examples completed successfully!")
            print("=" * 60)

            # prices_complex = Market.prices.get()
            # prices_complex = prices_complex.map_(lambda x: x + 120)
            # prices_complex = prices_complex[0]
            # prices_complex = await prices_complex.execute(ctx)
            # print("ABC", prices_complex)

    asyncio.run(main())
