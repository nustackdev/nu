"""Extensions Demo - Dict, Collection, List, Vector.

Showcases all 4 extension types:
- DictField: Hashtable of primitives
- CollectionField: Hashtable of schemas
- ListField: Ordered list (any type)
- VectorField: Homogeneous primitives
"""

from redwood.codec import TextCodecSpec
from redwood.dsl import PrimitiveField, PrimitivePath, Schema, SchemaField
from redwood.dsl.extensions import (
    CollectionField,
    CollectionItemPath,
    CollectionPath,
    VectorField,
    VectorPath,
)
from redwood.dsl.extensions.vector import VectorPrimitivePath
from redwood.observer.in_memory_observer import InMemoryObserver, InMemoryObserverSpec
from redwood.storage.file_storage import FileStorage, FileStorageSpec
from redwood.tree.backend import ObservableStorage
from redwood.tree.registry import ViewRegistry
from redwood.tree.tree import Tree
from redwood.tree.view import DictView


# ============================================================================
# SCHEMAS
# ============================================================================


class MostNestedCollection(Schema):
    """Most nested collection schema."""

    item: CollectionItemPath[float] = PrimitiveField(float)


class EvenNestedSchema(Schema):
    """Even more nested schema."""

    value: PrimitivePath[str] = PrimitiveField(str)
    nested_collection: CollectionPath[MostNestedCollection] = CollectionField(MostNestedCollection)


class Order(Schema):
    """Order with volume and price."""

    volume: CollectionItemPath[int] = PrimitiveField(int)
    price: CollectionItemPath[float] = PrimitiveField(float)
    nested: EvenNestedSchema = SchemaField(EvenNestedSchema)


class OrderVector(Schema):
    """Order with volume and price."""

    price: PrimitivePath[float] = PrimitiveField(float)


class Market(Schema):
    """Market with all extension types."""

    orders: CollectionPath[Order] = CollectionField(Order)  # Hashtable of schemas
    current: PrimitivePath[str] = PrimitiveField(str)
    list_of_orders: VectorPath[OrderVector] = VectorField(OrderVector)
    tags: VectorPrimitivePath[str] = VectorField(str)


# class User(Schema):
#     """User with lists."""

#     tags: ListField[str] = ListField(str)  # List of primitives
#     orders: ListField[Order] = ListField(Order)  # List of schemas


# class Signal(Schema):
#     """Signal with vector."""

#     samples: VectorField[float] = VectorField(float)  # Homogeneous primitives


# ============================================================================
# DEMO
# ============================================================================


def main():
    """Run extensions demo."""
    print("\n" + "=" * 70)
    print("REDWOOD DSL - EXTENSIONS DEMO")
    print("=" * 70 + "\n")

    with (
        InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer,
        FileStorage(FileStorageSpec(codec=TextCodecSpec())) as storage,
    ):
        tree = Tree(
            backend=ObservableStorage(storage=storage, observer=observer),
            registry=ViewRegistry(),
        )

        # # ====================================================================
        # # DictField: Hashtable of primitives
        # # ====================================================================
        # print("📊 DictField (Hashtable of Primitives):")

        # with tree.transaction() as ctx:
        #     root = tree.view(DictView, ctx=ctx)
        #     root.set("prices", {"AAPL": 150.0, "GOOGL": 2800.0})

        # # Read
        # with tree.transaction() as ctx:
        #     aapl = Market.prices["AAPL"].get().evaluate(tree, ctx)
        #     googl = Market.prices["GOOGL"].get().evaluate(tree, ctx)
        #     print(f"   Market.prices['AAPL'] = {aapl}")
        #     print(f"   Market.prices['GOOGL'] = {googl}")

        # # Write
        # with tree.transaction() as ctx:
        #     Market.prices["MSFT"].set(380.0).evaluate(tree, ctx)
        #     msft = Market.prices["MSFT"].get().evaluate(tree, ctx)
        #     print(f"   Set Market.prices['MSFT'] = {msft}\n")

        # ====================================================================
        # CollectionField: Hashtable of schemas
        # ====================================================================
        print("📦 CollectionField (Hashtable of Schemas):")

        with tree.transaction() as ctx:
            root = tree.view(DictView, ctx=ctx)
            root.set(
                "orders",
                {
                    "AAPL": {"volume": 1000, "price": 150.0, "nested": {"value": "42"}},
                    "GOOGL": {"volume": 500, "price": 2800.0, "nested": {"value": "84"}},
                },
            )
            root.set("current", "AAPL")
            root.set("tags", ["tech", "bluechip"])
            root.set(
                "list_of_orders",
                [{"price": 150.0}, {"price": 2800.0}, {"price": 380.0}],
            )

        # Navigate schema
        with tree.transaction() as ctx:
            vol = Market.orders["AAPL"].volume.get().evaluate(tree, ctx)
            price = Market.orders["AAPL"].price.get().evaluate(tree, ctx)
            nested = Market.orders["AAPL"].nested.value.get().evaluate(tree, ctx)

            print(f"   Market.orders['AAPL'].volume = {vol}")
            print(f"   Market.orders['AAPL'].price = {price}")
            print(f"   Market.orders['AAPL'].nested.value = {nested}\n")

            print("   Tags:")
            for i in range(2):
                tag = Market.tags[i]
                tag = tag.get().evaluate(tree, ctx)
                print(f"     Market.tags[{i}] = {tag}")

            print("   List of Orders:")
            for i in range(3):
                order = Market.list_of_orders[i]
                order = order.price.get().evaluate(tree, ctx)
                print(f"     Market.list_of_orders[{i}].price = {order}")

            total_volume = (
                Market.orders[Market.current.get()].volume.get()
                + Market.orders[Market.current.get()].volume.get()
            )
            print(total_volume.evaluate(tree, ctx))
            # print(f"   Total volume (AAPL + GOOGL) = {total_volume.evaluate(tree, ctx)}\n")

    #     # ====================================================================
    #     # ListField: Ordered list
    #     # ====================================================================
    #     print("📝 ListField (Ordered List):")

    #     with tree.transaction() as ctx:
    #         root = tree.view(DictView, ctx=ctx)
    #         root.set("tags", ["python", "rust", "go"])
    #         root.set("orders", [{"volume": 100, "price": 150.0}, {"volume": 200, "price": 151.0}])

    #     # Primitive list
    #     with tree.transaction() as ctx:
    #         tag0 = User.tags[0].get().evaluate(tree, ctx)
    #         tag1 = User.tags[1].get().evaluate(tree, ctx)
    #         print(f"   User.tags[0] = {tag0}")
    #         print(f"   User.tags[1] = {tag1}")

    #     # Schema list
    #     with tree.transaction() as ctx:
    #         vol = User.orders[0].volume.get().evaluate(tree, ctx)
    #         price = User.orders[1].price.get().evaluate(tree, ctx)
    #         print(f"   User.orders[0].volume = {vol}")
    #         print(f"   User.orders[1].price = {price}\n")

    #     # ====================================================================
    #     # VectorField: Homogeneous primitives
    #     # ====================================================================
    #     print("📈 VectorField (Homogeneous Primitives):")

    #     with tree.transaction() as ctx:
    #         root = tree.view(DictView, ctx=ctx)
    #         root.set("samples", [1.5, 2.3, 3.1, 4.7])

    #     # Access
    #     with tree.transaction() as ctx:
    #         s0 = Signal.samples[0].get().evaluate(tree, ctx)
    #         s1 = Signal.samples[1].get().evaluate(tree, ctx)
    #         print(f"   Signal.samples[0] = {s0}")
    #         print(f"   Signal.samples[1] = {s1}\n")

    # print("=" * 70)
    # print("✅ Extensions Demo Complete!")
    # print("=" * 70)
    # print("\nAll 4 Extension Types Working:")
    # print("  ✓ DictField - Hashtable of primitives")
    # print("  ✓ CollectionField - Hashtable of schemas")
    # print("  ✓ ListField - Ordered list (any type)")
    # print("  ✓ VectorField - Homogeneous primitives")
    # print()


if __name__ == "__main__":
    main()
