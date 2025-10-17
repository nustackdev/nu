"""Redwood DSL - Final Demo.

Showcases core DSL capabilities:
- Schema definition
- Path navigation
- Queries (expressions)
- Mutations (commands)
- Empty/NaN handling
"""

from redwood.codec import TextCodecSpec
from redwood.dsl import PrimitiveField, PrimitivePath, Schema, SchemaField
from redwood.observer.in_memory_observer import InMemoryObserver, InMemoryObserverSpec
from redwood.storage.file_storage import FileStorage, FileStorageSpec
from redwood.tree.backend import ObservableStorage
from redwood.tree.registry import ViewRegistry
from redwood.tree.tree import Tree
from redwood.tree.view import DictView


# ============================================================================
# 1. DEFINE SCHEMAS
# ============================================================================


class Profile(Schema):
    """User profile with contact info."""

    name: PrimitivePath[str] = PrimitiveField(str)
    email: PrimitivePath[str] = PrimitiveField(str)


class User(Schema):
    """User with nested profile."""

    age: PrimitivePath[int] = PrimitiveField(int)
    active: PrimitivePath[bool] = PrimitiveField(bool)
    profile: Profile = SchemaField(Profile)


# ============================================================================
# 2. DEMO
# ============================================================================


def main():
    """Run DSL demo."""
    print("\n" + "=" * 70)
    print("REDWOOD DSL - FINAL DEMO")
    print("=" * 70 + "\n")

    with (
        InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer,
        FileStorage(FileStorageSpec(codec=TextCodecSpec())) as storage,
    ):
        tree = Tree(
            backend=ObservableStorage(storage=storage, observer=observer),
            registry=ViewRegistry(),
        )

        # ====================================================================
        # Setup: Create initial data
        # ====================================================================
        print("📝 Setting up data...")
        with tree.transaction() as ctx:
            root = tree.view(DictView, ctx=ctx)
            root.set("age", 25)
            root.set("active", True)
            root.set("profile", {"name": "Alice", "email": "alice@example.com"})
        print("   ✓ Data created\n")

        # ====================================================================
        # READ: Navigate and read values
        # ====================================================================
        print("📖 READ Operations:")
        with tree.transaction() as ctx:
            age = User.age.get().evaluate(tree, ctx)
            email = User.profile.email.get().evaluate(tree, ctx)
            print(f"   User.age = {age}")
            print(f"   User.profile.email = {email}\n")

        # ====================================================================
        # QUERY: Build and evaluate expressions
        # ====================================================================
        print("🔍 QUERY Operations:")

        # Simple comparison
        is_adult = User.age > 18
        with tree.transaction() as ctx:
            result = is_adult.evaluate(tree, ctx)
            print(f"   User.age > 18 = {result}")

        # Complex expression
        is_active_adult = (User.age >= 18) & (User.active == True)
        with tree.transaction() as ctx:
            result = is_active_adult.evaluate(tree, ctx)
            print(f"   (User.age >= 18) & (User.active == True) = {result}")

        # Arithmetic
        doubled_age = User.age * 2
        with tree.transaction() as ctx:
            result = doubled_age.evaluate(tree, ctx)
            print(f"   User.age * 2 = {result}\n")

        # ====================================================================
        # WRITE: Mutate tree state
        # ====================================================================
        print("✏️  WRITE Operations:")

        # Set value
        with tree.transaction() as ctx:
            User.age.set(30).evaluate(tree, ctx)
            new_age = User.age.get().evaluate(tree, ctx)
            print(f"   Set User.age = {new_age}")

        # Update (increment)
        with tree.transaction() as ctx:
            User.age.update(lambda x: x + 1).evaluate(tree, ctx)
            updated_age = User.age.get().evaluate(tree, ctx)
            print(f"   Updated User.age = {updated_age}\n")

        # ====================================================================
        # EMPTY/NaN: Graceful error handling
        # ====================================================================
        print("⚠️  EMPTY/NaN Handling:")

        # Delete a field
        with tree.transaction() as ctx:
            User.age.delete().evaluate(tree, ctx)
            print("   Deleted User.age")

        # Read missing field (returns Empty)
        with tree.transaction() as ctx:
            from redwood.dsl import is_empty

            missing = User.age.get().evaluate(tree, ctx)
            print(f"   User.age.get() = {missing} (is_empty: {is_empty(missing)})")

        # Operation with missing field (returns NaN)
        with tree.transaction() as ctx:
            from redwood.dsl import is_nan

            result = (User.age > 18).evaluate(tree, ctx)
            print(f"   User.age > 18 = {result} (is_nan: {is_nan(result)})")

        print()

    print("=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
