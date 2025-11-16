"""Demo: Shape collections with SequenceShapeRef and MappingShapeRef.

This example demonstrates typed homogeneous collections of shapes,
allowing navigation to individual shape fields.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from redwood import Context
from rwstd.collections import DictView
from rwstd.shapes import (
    MappingShapeSlot,
    PrimitiveSlot,
    SequenceShapeSlot,
    Shape,
)
from rwstd.storage import BinaryCodec, RocksDBStorage


# =============================================================================
# SHAPE DEFINITIONS
# =============================================================================


class Order(Shape):
    """Order information."""

    id = PrimitiveSlot(str)
    symbol = PrimitiveSlot(str)
    quantity = PrimitiveSlot(int)
    price = PrimitiveSlot(float)


class SymbolInfo(Shape):
    """Individual symbol information."""

    price = PrimitiveSlot(float)
    volume = PrimitiveSlot(int)
    exchange = PrimitiveSlot(str)


class Market(Shape):
    """Market data with shape collections."""

    # Sequence of Order shapes
    orders = SequenceShapeSlot(Order)

    # Mapping of symbol name to SymbolInfo
    symbols = MappingShapeSlot(SymbolInfo)


# =============================================================================
# EXAMPLES
# =============================================================================


def example_sequence_shapes(ctx: Context) -> None:
    """Example: sequence of homogeneous shapes."""
    print("\n=== Sequence of Shapes ===")

    # Append orders to the sequence
    Market.orders.append(
        {
            "id": "ORD001",
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.5,
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

    Market.orders.append(
        {
            "id": "ORD003",
            "symbol": "MSFT",
            "quantity": 200,
            "price": 380.25,
        }
    ).execute(ctx)

    # Navigate to individual order fields
    order_0_id = Market.orders[0].id.get().execute(ctx)
    order_0_price = Market.orders[0].price.get().execute(ctx)
    print(f"Order 0 - ID: {order_0_id}, Price: {order_0_price}")

    order_1_symbol = Market.orders[1].symbol.get().execute(ctx)
    order_1_quantity = Market.orders[1].quantity.get().execute(ctx)
    print(f"Order 1 - Symbol: {order_1_symbol}, Quantity: {order_1_quantity}")

    # Update a field in an order
    Market.orders[2].price.set(385.0).execute(ctx)
    updated_price = Market.orders[2].price.get().execute(ctx)
    print(f"Order 2 - Updated Price: {updated_price}")

    # Extract all orders
    all_orders = Market.orders.extract().execute(ctx)
    print(f"\nAll orders: {all_orders}")


def example_mapping_shapes(ctx: Context) -> None:
    """Example: mapping of homogeneous shapes."""
    print("\n=== Mapping of Shapes ===")

    # Store multiple symbols at once
    Market.symbols.store(
        {
            "AAPL": {
                "price": 150.5,
                "volume": 1000000,
                "exchange": "NASDAQ",
            },
            "GOOGL": {
                "price": 2800.0,
                "volume": 500000,
                "exchange": "NASDAQ",
            },
            "TSLA": {
                "price": 245.75,
                "volume": 2000000,
                "exchange": "NASDAQ",
            },
        }
    ).execute(ctx)

    # Navigate to individual symbol fields
    aapl_price = Market.symbols["AAPL"].price.get().execute(ctx)
    aapl_volume = Market.symbols["AAPL"].volume.get().execute(ctx)
    print(f"AAPL - Price: {aapl_price}, Volume: {aapl_volume}")

    googl_exchange = Market.symbols["GOOGL"].exchange.get().execute(ctx)
    print(f"GOOGL - Exchange: {googl_exchange}")

    # Update individual fields
    Market.symbols["TSLA"].price.set(250.0).execute(ctx)
    Market.symbols["TSLA"].volume.set(2500000).execute(ctx)

    tsla_price = Market.symbols["TSLA"].price.get().execute(ctx)
    tsla_volume = Market.symbols["TSLA"].volume.get().execute(ctx)
    print(f"TSLA - Updated Price: {tsla_price}, Volume: {tsla_volume}")

    # Extract all symbols
    all_symbols = Market.symbols.extract().execute(ctx)
    print(f"\nAll symbols: {all_symbols}")


def example_complex_operations(ctx: Context) -> None:
    """Example: complex operations with shape collections."""
    print("\n=== Complex Operations ===")

    # Get prices from both orders and symbols
    order_price = Market.orders[0].price.get().execute(ctx)
    symbol_price = Market.symbols["AAPL"].price.get().execute(ctx)
    print(f"Order price: {order_price}, Symbol price: {symbol_price}")

    # Compute derived values
    total_order_value = (Market.orders[0].price.get() * Market.orders[0].quantity.get()).execute(
        ctx
    )
    print(f"Total order value: {total_order_value}")


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """Run all examples."""
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        RocksDBStorage(path=Path(tmpdir) / "db", codec=BinaryCodec()) as storage,
    ):
        with storage.transaction() as tx:
            root = DictView.create(tx)
            ctx = Context(root_view=root, storage_context=tx)

        # Run examples
        example_sequence_shapes(ctx)
        example_mapping_shapes(ctx)
        example_complex_operations(ctx)


if __name__ == "__main__":
    main()
