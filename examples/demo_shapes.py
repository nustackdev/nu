"""Complete example demonstrating Shape/Slot system.

This shows the full declarative → runtime flow:
1. Define Shapes with Slots (declarative)
2. Access slots to create Refs (automatic)
3. Build operations and commands (expressions)
4. Execute against tree (runtime)
"""

import time

from redwood.semantics.structure.shape import Shape
from redwood.semantics.structure.slots import MapSlot, ShapeSlot, ValueSlot
from redwood.semantics.types import Context
from redwood.storage import ReactiveStorage
from redwood.tree.registry import ViewRegistry
from rwstd.adapters import (
    BinaryCodecSpec,
    InMemoryObserver,
    InMemoryObserverSpec,
    LMDBStorage,
    LMDBStorageSpec,
    RocksDBStorage,
    RocksDBStorageSpec,
    TextCodecSpec,
)
from rwstd.views import DictView, ListView, QueueComponent, QueueContainer, QueueView, Tree


# ============================================================================
# Define Shapes (Declarative)
# ============================================================================


class Profile(Shape):
    """User profile with personal info."""

    email: str = ValueSlot(str)
    age: int = ValueSlot(int)
    verified: bool = ValueSlot(bool)


class Order(Shape):
    """Trading order."""

    price: float = ValueSlot(float)
    volume: int = ValueSlot(int)
    symbol: str = ValueSlot(str)


class Market(Shape):
    """Market data structure."""

    signal: float = ValueSlot(float)
    active: bool = ValueSlot(bool)
    orders: dict = MapSlot(Order)


class User(Shape):
    """User with profile and orders."""

    name: str = ValueSlot(str)
    profile: Profile = ShapeSlot(Profile)
    balance: float = ValueSlot(float)


# ============================================================================
# Usage Examples
# ============================================================================


def run_examples() -> None:
    with (
        InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer,
        RocksDBStorage(RocksDBStorageSpec(codec=BinaryCodecSpec(), path=".db-layer4")) as storage,
    ):
        reactive_storage = ReactiveStorage(storage=storage, observer=observer)
        view_registry = ViewRegistry()
        view_registry.register_view(DictView, 1, dict, [str, int])
        view_registry.register_view(ListView, 2, list, [int])
        view_registry.register_view(QueueView, 101, QueueContainer, [QueueComponent])

        tree = Tree(
            backend=reactive_storage,
            registry=view_registry,
        )

        # --- Example 1: Shape inspection ---
        print("=" * 60)
        print("Example 1: Shape Introspection")
        print("=" * 60)

        print(f"\nProfile slots: {Profile.field_names()}")
        print(f"Market slots: {Market.field_names()}")
        print(f"User has 'profile' slot: {User.has_slot('profile')}")

        profile_slot = Profile.get_slot("email")
        print(f"\nProfile.email slot: {profile_slot}")
        print(f"  Type: {profile_slot.value_type}")
        print(f"  View: {profile_slot.view_type}")

        with tree.transaction() as tx:
            User.name.set("Charlie").execute(Context(tree=tree, storage_context=tx))
            print(
                f"\nSet User.name to '{User.name.get().execute(Context(tree=tree, storage_context=tx))}'"
            )

        # --- Example 2: Nested Shape access ---
        print("\n" + "=" * 60)
        print("Example 2: Nested Shape Access")
        print("=" * 60)
        with tree.transaction() as tx:
            User.profile.email.set("charlie@example.com").execute(
                Context(tree=tree, storage_context=tx)
            )
            email = User.profile.email.get().execute(Context(tree=tree, storage_context=tx))
            print(f"User.profile.email: {email}")

        # --- Example 3: MapSlot usage ---
        print("\n" + "=" * 60)
        print("Example 3: MapSlot Usage")
        print("=" * 60)
        with tree.transaction() as tx:
            Market.orders["ORDER001"].set(12).execute(Context(tree=tree, storage_context=tx))
            order = Market.orders["ORDER001"].get().execute(Context(tree=tree, storage_context=tx))
            print(f"Market.orders['ORDER001']: {order}")


def run_benchmarks() -> None:
    with (
        InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer,
        LMDBStorage(LMDBStorageSpec(codec=BinaryCodecSpec())) as storage,
    ):
        reactive_storage = ReactiveStorage(storage=storage, observer=observer)
        view_registry = ViewRegistry()
        view_registry.register_view(DictView, 1, dict, [str, int])
        view_registry.register_view(ListView, 2, list, [int])
        view_registry.register_view(QueueView, 101, QueueContainer, [QueueComponent])

        tree = Tree(
            backend=reactive_storage,
            registry=view_registry,
        )

        # --- Benchmark 1: read performance ---
        print("\n" + "=" * 60)
        print("Benchmark 1: Read Performance")
        print("=" * 60)

        start_time = time.perf_counter()
        with tree.with_dict_view() as users_view:
            for _ in range(10_000):
                users_view.get("name")
        end_time = time.perf_counter()
        print(f"Elapsed time: {end_time - start_time:.4f} seconds for 10,000 view reads")

        # --- Benchmark 2: command execution performance ---
        print("\n" + "=" * 60)
        print("Benchmark 2: Command Execution Performance")
        print("=" * 60)
        start_time = time.perf_counter()
        with tree.transaction() as tx:
            for _ in range(10_000):
                User.name.get().execute(Context(tree=tree, storage_context=tx))
        end_time = time.perf_counter()

        print(f"Elapsed time: {end_time - start_time:.4f} seconds")


if __name__ == "__main__":
    run_examples()
    run_benchmarks()
