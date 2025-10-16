"""Redwood DSL Demo - End-to-end usage examples.

This script demonstrates the core DSL capabilities:
1. Schema definition
2. Path construction (lazy)
3. Query evaluation (reads)
4. Command execution (writes)
5. Empty/NaN propagation
6. Complex expressions
"""

from __future__ import annotations

from redwood.codec import TextCodecSpec
from redwood.dsl import Field, Schema, is_empty, is_nan
from redwood.observer.in_memory_observer import InMemoryObserver, InMemoryObserverSpec
from redwood.storage.file_storage import FileStorage, FileStorageSpec
from redwood.tree import DictView, Tree
from redwood.tree.backend import ObservableStorage


# ============================================================================
# Schema Definitions
# ============================================================================


class Order(Schema):
    """Order schema."""

    symbol = Field(primitive=str)
    price = Field(primitive=float)
    qty = Field(primitive=int)
    status = Field(primitive=str)


class Indicator(Schema):
    """Technical indicator schema."""

    ema_20 = Field(primitive=float)
    ema_50 = Field(primitive=float)
    rsi = Field(primitive=float)


class Market(Schema):
    """Market data schema."""

    orders = Field(view=DictView, schema=Order)
    indicators = Field(view=DictView, schema=Indicator)
    counter = Field(primitive=int)
    current_symbol = Field(primitive=str)


# ============================================================================
# Demo Functions
# ============================================================================


def setup_tree() -> Tree:
    """Create and populate a test tree."""
    observer = InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec()))
    storage = FileStorage(FileStorageSpec(codec=TextCodecSpec()))

    try:
        observer.initialize()
        storage.initialize()

        tree = Tree(
            backend=ObservableStorage(storage=storage, observer=observer),
        )

        # Populate data
        with tree.transaction() as ctx:
            # Orders
            orders_view = tree.at("orders").view(DictView, ctx=ctx)
            orders_view.set(
                "AAPL", {"symbol": "AAPL", "price": 150.0, "qty": 100, "status": "active"}
            )
            orders_view.set(
                "GOOGL", {"symbol": "GOOGL", "price": 95.0, "qty": 50, "status": "pending"}
            )
            orders_view.set(
                "MSFT", {"symbol": "MSFT", "price": 310.0, "qty": 75, "status": "active"}
            )

            # Indicators
            indicators_view = tree.at("indicators").view(DictView, ctx=ctx)
            indicators_view.set("AAPL", {"ema_20": 148.5, "ema_50": 145.0, "rsi": 45.0})
            indicators_view.set("GOOGL", {"ema_20": 92.0, "ema_50": 95.5, "rsi": 25.0})
            indicators_view.set("MSFT", {"ema_20": 308.0, "ema_50": 305.0, "rsi": 75.0})

            # Metadata
            root_view = tree.view(DictView, ctx=ctx)
            root_view.set("counter", 0)
            root_view.set("current_symbol", "AAPL")

        yield tree
    finally:
        observer.shutdown()
        storage.shutdown()


def demo_path_construction():
    """Demo 1: Lazy path construction."""
    print("\n" + "=" * 60)
    print("DEMO 1: Path Construction (Lazy)")
    print("=" * 60)

    from redwood.dsl import RootPath

    # Construct paths without tree access
    market_path = RootPath(Market)

    price_path = market_path.orders["AAPL"].price
    print("Path constructed: Market.orders['AAPL'].price")
    print(f"  Resolved path: {price_path.meta.resolved_path}")
    print(f"  Is pure: {price_path.meta.is_pure}")
    print(f"  Has dynamic components: {price_path.meta.has_dynamic_components}")


def demo_explicit_reads(tree: Tree):
    """Demo 2: Explicit reads with .get()."""
    print("\n" + "=" * 60)
    print("DEMO 2: Explicit Reads (.get())")
    print("=" * 60)

    price_path = Market.orders["AAPL"].price

    with tree.transaction() as ctx:
        # Explicit get
        price_value = price_path.get()
        result = price_value.evaluate(tree, ctx)
        print(f"Price: ${result}")
        print(f"  Query is pure: {price_value.meta.is_pure}")


def demo_implicit_reads(tree: Tree):
    """Demo 3: Implicit reads in value context."""
    print("\n" + "=" * 60)
    print("DEMO 3: Implicit Reads (in value context)")
    print("=" * 60)

    # PathTerm auto-converts to ValueTerm via .get()
    is_expensive = Market.orders["AAPL"].price > 100

    with tree.transaction() as ctx:
        result = is_expensive.evaluate(tree, ctx)
        print(f"Is AAPL expensive? {result}")
        print(f"  Expression is pure: {is_expensive.meta.is_pure}")


def demo_commands(tree: Tree):
    """Demo 4: Command execution (mutations)."""
    print("\n" + "=" * 60)
    print("DEMO 4: Commands (Mutations)")
    print("=" * 60)

    # Create set command
    set_cmd = Market.orders["AAPL"].price.set(155.0)
    print(f"Command is pure: {set_cmd.meta.is_pure}")

    # Execute command
    with tree.transaction() as ctx:
        set_cmd.evaluate(tree, ctx)
        print("Set AAPL price to $155.0")

        # Read back
        new_price = Market.orders["AAPL"].price.get().evaluate(tree, ctx)
        print(f"New price: ${new_price}")


def demo_complex_expressions(tree: Tree):
    """Demo 5: Complex composed expressions."""
    print("\n" + "=" * 60)
    print("DEMO 5: Complex Expressions")
    print("=" * 60)

    # Complex query
    query = (Market.orders["AAPL"].price > 100) & (Market.orders["AAPL"].qty > 50)

    with tree.transaction() as ctx:
        result = query.evaluate(tree, ctx)
        print(f"AAPL: price > 100 AND qty > 50? {result}")

        # Another complex query
        all_expensive = (
            (Market.orders["AAPL"].price > 100)
            & (Market.orders["GOOGL"].price > 90)
            & (Market.orders["MSFT"].price > 300)
        )
        result = all_expensive.evaluate(tree, ctx)
        print(f"All orders expensive? {result}")


def demo_empty_propagation(tree: Tree):
    """Demo 6: Empty/NaN propagation."""
    print("\n" + "=" * 60)
    print("DEMO 6: Empty/NaN Propagation")
    print("=" * 60)

    with tree.transaction() as ctx:
        # Missing field returns Empty
        missing = Market.orders["UNKNOWN"].price.get()
        result = missing.evaluate(tree, ctx)
        print(f"Missing order price: {result}")
        print(f"  Is Empty: {is_empty(result)}")

        # Operation on Empty returns NaN
        invalid_comparison = Market.orders["UNKNOWN"].price > 100
        result = invalid_comparison.evaluate(tree, ctx)
        print(f"Missing price > 100: {result}")
        print(f"  Is NaN: {is_nan(result)}")

        # Chained missing path
        deep_missing = Market.orders["AAPL"].nonexistent.deeper.get()
        result = deep_missing.evaluate(tree, ctx)
        print(f"Deep missing path: {result}")
        print(f"  Is Empty: {is_empty(result)}")


def demo_dynamic_paths(tree: Tree):
    """Demo 7: Dynamic path resolution."""
    print("\n" + "=" * 60)
    print("DEMO 7: Dynamic Paths")
    print("=" * 60)

    # Path with dynamic index
    symbol_path = Market.current_symbol
    dynamic_order = Market.orders[symbol_path]

    with tree.transaction() as ctx:
        # Resolve current_symbol first, then access order
        price = dynamic_order.price.get().evaluate(tree, ctx)
        print(f"Current symbol order price: ${price}")
        print(f"  Path has dynamic components: {dynamic_order.meta.has_dynamic_components}")


def demo_arithmetic(tree: Tree):
    """Demo 8: Arithmetic operations."""
    print("\n" + "=" * 60)
    print("DEMO 8: Arithmetic Operations")
    print("=" * 60)

    with tree.transaction() as ctx:
        # Calculate total value
        total = Market.orders["AAPL"].price * Market.orders["AAPL"].qty
        result = total.evaluate(tree, ctx)
        print(f"AAPL total value: ${result}")

        # Price difference
        diff = Market.orders["MSFT"].price - Market.orders["AAPL"].price
        result = diff.evaluate(tree, ctx)
        print(f"MSFT vs AAPL price diff: ${result}")


# ============================================================================
# Main Demo
# ============================================================================


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("Redwood DSL Demo")
    print("=" * 60)

    # Setup
    tree = setup_tree()
    print("\n✓ Tree populated with test data")

    # Run demos
    demo_path_construction()
    demo_explicit_reads(tree)
    demo_implicit_reads(tree)
    demo_commands(tree)
    demo_complex_expressions(tree)
    demo_empty_propagation(tree)
    demo_dynamic_paths(tree)
    demo_arithmetic(tree)

    print("\n" + "=" * 60)
    print("Demo complete! ✨")
    print("=" * 60)


if __name__ == "__main__":
    main()
