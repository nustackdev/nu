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

from everybase.shapes import (
    Context,
    MappingShapeSlot,
    MappingSlot,
    PrimitiveSlot,
    SequenceShapeSlot,
    SequenceSlot,
    Shape,
    ShapeSlot,
)
from everybase.views import DictView

from everyshape.adapters import TextCodec, TextStorage


class SymbolInfo(Shape):
    """Individual symbol information."""

    price = PrimitiveSlot(float)
    volume = PrimitiveSlot(int)
    exchange = PrimitiveSlot(str)


class Order(Shape):
    """Order information."""

    id = PrimitiveSlot(str)
    symbol = PrimitiveSlot(str)
    quantity = PrimitiveSlot(int)
    price = PrimitiveSlot(float)


class Market(Shape):
    """Market data with various collection types."""

    misc_val = PrimitiveSlot(int)
    signals = MappingSlot(float)
    prices = SequenceSlot(float)
    symbols = MappingShapeSlot(SymbolInfo)
    orders = SequenceShapeSlot(Order)
    last_order = ShapeSlot(Order)


# =============================================================================
# EXAMPLES
# =============================================================================


def example_mapping_primitives(ctx: Context) -> None:
    """Example: mapping of primitive values."""
    print("\n=== Mapping of Primitives ===")

    Market.signals["vix"].set(23.5).execute(ctx)
    Market.signals["sentiment"].set(0.75).execute(ctx)

    # Get values
    vix = Market.signals["vix"].get().execute(ctx)
    sentiment = Market.signals["sentiment"].get().execute(ctx)

    print(f"VIX: {vix}")
    print(f"Sentiment: {sentiment}")


def example_sequence_primitives(ctx: Context) -> None:
    """Example: sequence of primitive values."""
    print("\n=== Sequence of Primitives ===")

    Market.misc_val.set(1).execute(ctx)

    # Set values at indices
    Market.prices.append(100.5).execute(ctx)
    Market.prices.append(101.2).execute(ctx)
    Market.prices.append(99.8).execute(ctx)

    # Get values
    price_0 = Market.prices[0].get().execute(ctx)
    price_1 = Market.prices[1].get().execute(ctx)
    price_2 = Market.prices[2].get().execute(ctx)

    print(f"Prices: [{price_0}, {price_1}, {price_2}]")

    prices = Market.prices.extract().execute(ctx)
    print(prices)

    nested_acc = (Market.prices[Market.misc_val.get()].get() + 12 > 100).execute(ctx)
    print(nested_acc)

    Market.last_order.id.set("ID").execute(ctx)
    print(Market.last_order.extract().execute(ctx))


def example_mapping_shapes(ctx: Context) -> None:
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

    # Extract entire shape
    aapl_data = Market.symbols["AAPL"].extract().execute(ctx)
    print(f"AAPL Data: {aapl_data}")


def example_sequence_shapes(ctx: Context) -> None:
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

    # Extract entire shape
    order_0_data = Market.orders[0].extract().execute(ctx)
    print(f"Order 0 Data: {order_0_data}")


if __name__ == "__main__":
    with (
        TextStorage(path=Path(".db_shape"), codec=TextCodec()) as storage,
        storage.transaction() as tx,
    ):
        root = DictView.open_root(tx)
        ctx = Context.create(root_view=root, storage_context=tx)

        print("=" * 60)
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
