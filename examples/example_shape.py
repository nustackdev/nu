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

from redwood import Context
from rwstd.collections import DictView
from rwstd.shapes import (
    MappingShapeSlot,
    MappingSlot,
    PrimitiveSlot,
    SequenceShapeSlot,
    SequenceSlot,
    Shape,
    ShapeSlot,
)
from rwstd.storage import TextCodec, TextStorage


# =============================================================================
# SHAPE DEFINITIONS
# =============================================================================


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


# =============================================================================
# MAIN
# =============================================================================


def setup_logging() -> None:
    """Setup logging."""
    import logging

    from rich.console import Console
    from rich.logging import RichHandler
    from rich.traceback import install

    install()

    console = Console()
    # Create handler
    console_handler = RichHandler(
        console=console,
        tracebacks_show_locals=True,
        rich_tracebacks=True,
        markup=True,
        log_time_format="[%x %X.%f]",
    )

    # Option 2: Custom formatter that explicitly shows extra dict
    class ExtraFormatter(logging.Formatter):
        def format(self, record):
            # Get standard formatted message
            base_msg = super().format(record)

            # Add extra fields if they exist
            extra_fields = {
                k: v
                for k, v in record.__dict__.items()
                if k
                not in [
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "message",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "taskName",
                ]
            }

            if extra_fields:
                base_msg += f" | extra={extra_fields}"

            return base_msg

    console_formatter = ExtraFormatter("[cyan]%(name)s[/cyan] - %(message)s")
    console_handler.setFormatter(console_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)


if __name__ == "__main__":
    setup_logging()

    with TextStorage(path=Path(".db_shape"), codec=TextCodec()) as storage:
        with storage.transaction() as tx:
            root = DictView.open_root(tx)
            ctx = Context(root_view=root, storage_context=tx)

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
