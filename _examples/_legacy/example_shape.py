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

import every_pv
import every_pv.views


class SymbolInfo(every_pv.Shape):
    """Individual symbol information."""

    price = every_pv.slots.FloatSlot()
    volume = every_pv.slots.IntSlot()
    exchange = every_pv.slots.StrSlot()
    yo = every_pv.slots.BytesSlot()


class Order(every_pv.Shape):
    """Order information."""

    id = every_pv.slots.StrSlot()
    symbol = every_pv.slots.StrSlot()
    quantity = every_pv.slots.IntSlot()
    price = every_pv.slots.FloatSlot()


class Market(every_pv.Shape):
    """Market data with various collection types."""

    misc_val = every_pv.slots.IntSlot()
    signals = every_pv.slots.DictSlot(float)
    prices = every_pv.slots.ListSlot(float)
    symbols = every_pv.slots.ShapesDictSlot(SymbolInfo)
    orders = every_pv.slots.ShapesListSlot(Order)
    last_order = every_pv.slots.ShapeSlot(Order)


# =============================================================================
# EXAMPLES
# =============================================================================


def example_mapping_primitives(ctx: every_pv.KVContext) -> None:
    """Example: mapping of primitive values."""
    print("\n=== Mapping of Primitives ===")

    Market.signals["vix"].set(23.5).execute(ctx)
    Market.signals["sentiment"].set(0.75).execute(ctx)

    # Get values
    vix = Market.signals["vix"].get().execute(ctx)
    sentiment = Market.signals["sentiment"].get().execute(ctx)

    print(f"VIX: {vix}")
    print(f"Sentiment: {sentiment}")


def example_sequence_primitives(ctx: every_pv.KVContext) -> None:
    """Example: sequence of primitive values."""
    print("\n=== Sequence of Primitives ===")

    Market.misc_val.set(1).execute(ctx)

    # Set values at indices
    a = Market.prices.append(100.5)
    print("append res", a.execute(ctx))
    Market.prices.append(101.2).execute(ctx)
    Market.prices.append(99.8).execute(ctx)

    # Get values
    price_0 = Market.prices[0].get().execute(ctx)
    price_1 = Market.prices[1].get().execute(ctx)
    price_2 = Market.prices.get().map_(lambda x: x * 2).filter_(lambda a: a > 200).execute(ctx)

    print(f"Prices: [{price_0}, {price_1}, {price_2}]")

    prices = Market.prices.get().execute(ctx)
    print(prices)

    nested_acc = (Market.prices[Market.misc_val.get()].get() + 12 > 100).execute(ctx)
    print(nested_acc)

    Market.last_order.id.set("ID").execute(ctx)
    print(Market.last_order.get().execute(ctx))


def example_mapping_shapes(ctx: every_pv.KVContext) -> None:
    """Example: mapping of shapes."""
    print("\n=== Mapping of Shapes ===")

    # Store shape data
    Market.symbols["AAPL"].store(
        {
            "price": 150.0,
            "volume": 1000000,
            "exchange": "NASDAQ",
        }
    ).execute(ctx)

    Market.symbols["GOOGL"].store(
        {
            "price": 2800.0,
            "volume": 500000,
            "exchange": "NASDAQ",
        }
    ).execute(ctx)

    # Access nested fields
    aapl_price = Market.symbols["AAPL"].price.get().execute(ctx)
    googl_exchange = Market.symbols["GOOGL"].exchange.get().execute(ctx)

    print(f"AAPL Price: {aapl_price}")
    print(f"GOOGL Exchange: {googl_exchange}")

    # get entire shape
    aapl_data = Market.symbols["AAPL"].get().execute(ctx)
    print(f"AAPL Data: {aapl_data}")


def example_sequence_shapes(ctx: every_pv.KVContext) -> None:
    """Example: sequence of shapes."""
    print("\n=== Sequence of Shapes ===")

    # Store shape data
    Market.orders.append(
        {
            "id": "ORD001",
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.0,
        }
    ).execute(ctx)

    Market.orders.append(
        {
            "id": "ORD002",
            "symbol": "GOOGL",
            "quantity": 50,
            "price": 2800.0,
        }
    ).execute(ctx)

    # Access nested fields
    order_0_id = Market.orders[0].id.get().execute(ctx)
    order_1_symbol = Market.orders[1].symbol.get().execute(ctx)

    print(f"Order 0 ID: {order_0_id}")
    print(f"Order 1 Symbol: {order_1_symbol}")

    # get entire shape
    order_0_data = Market.orders[0].get().execute(ctx)
    print(f"Order 0 Data: {order_0_data}")


if __name__ == "__main__":
    from every_pv.adapters.codecs import TextCodec
    from every_pv.adapters.storages.textdb import TextStorage

    with (
        TextStorage(path=Path(".db_shape"), codec=TextCodec()) as storage,
        storage.transaction() as tx,
    ):
        root = every_pv.views.DictView.open_root(tx)
        ctx = every_pv.KVContext.create(root_view=root, storage_context=tx)

        set_res = SymbolInfo.volume.set(12)
        set_res = set_res.execute(ctx)
        print(set_res)

        SymbolInfo.exchange.set("hello").execute(ctx)
        SymbolInfo.yo.set(b"hello").execute(ctx)

        c = SymbolInfo.volume.get() + SymbolInfo.volume
        c = c.execute(ctx)
        print(c)

        a = (SymbolInfo.exchange.get() + "12").and_(None)
        resa = a.execute(ctx)
        print("A", resa)
        print("=" * 60)

        x = SymbolInfo.yo.get()[:3]
        resx = x.execute(ctx)
        print("X", resx)

        print("Shape Collections Example")
        print("=" * 60)

        # Run examples
        example_mapping_primitives(ctx)
        example_sequence_primitives(ctx)
        example_mapping_shapes(ctx)
        example_sequence_shapes(ctx)

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

        # prices_complex = Market.prices.get()
        # prices_complex = prices_complex.map_(lambda x: x + 120)
        # prices_complex = prices_complex[0]
        # prices_complex = prices_complex.execute(ctx)
        # print("ABC", prices_complex)
