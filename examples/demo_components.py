#!/usr/bin/env python3
"""Calculator service example using Invisibles over NetKit."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.abc import TupleKey

logging.basicConfig(level=logging.INFO)


# ============================================================================
# Main
# ============================================================================


def codec() -> None:
    """Test codec."""
    from redwood.codec import BinaryCodec, BinaryCodecSpec, TextCodec, TextCodecSpec

    with BinaryCodec(BinaryCodecSpec()) as codec:
        key = ("users", 42, "profile")
        value = {"name": "Alice", "age": 30}
        encoded_key = codec.encode_key(key)
        encoded_value = codec.encode_value(value)
        print(f"Encoded key: {encoded_key}")
        print(f"Encoded value: {encoded_value}")
        assert key == codec.decode_key(encoded_key)
        assert value == codec.decode_value(encoded_value)

    with TextCodec(TextCodecSpec()) as codec:
        key = ("users", 42, "profile")
        value = 12
        encoded_key = codec.encode_key(key)
        encoded_value = codec.encode_value(value)
        print(f"Encoded key: {encoded_key}")
        print(f"Encoded value: {encoded_value}")
        assert key == codec.decode_key(encoded_key)
        assert value == codec.decode_value(encoded_value)


def storage() -> None:
    """Test storage."""
    from redwood.codec import BinaryCodecSpec
    from redwood.storage.lmdb_storage import LMDBStorage, LMDBStorageSpec

    with LMDBStorage(
        LMDBStorageSpec(
            codec=BinaryCodecSpec(),
        )
    ) as storage:
        storage.set(("users", 1), {"name": "Alice"})
        storage.set(("users", 2), {"name": "Bob"})
        print("User 1:", storage.get(("users", 1)))
        print("User 2:", storage.get(("users", 2)))
        # storage.delete(("users", 1))
        try:
            print("User 1:", storage.get(("users", 1)))
        except Exception as e:
            print("Error fetching user 1:", e)


def observer() -> None:
    """Test observer."""
    from redwood.codec import TextCodecSpec
    from redwood.observer.in_memory_observer import InMemoryObserver, InMemoryObserverSpec

    def callback(topic: Key) -> None:
        print(f"Notification received for topic: {topic}")

    with InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer:
        sub = observer.subscribe(("users", "*"), callback, depth=1)
        observer.notify(("users", 42))
        observer.notify(("users", 42, "profile"))
        observer.notify(("orders", 1001))
        observer.unsubscribe(sub)
        observer.notify(("users", 42))


def backend() -> None:
    """Test backend."""
    from redwood.codec import BinaryCodecSpec, TextCodecSpec
    from redwood.observer.in_memory_observer import InMemoryObserver, InMemoryObserverSpec
    from redwood.reactive import ReactiveStorage
    from redwood.storage.rocksdb_storage import RocksDBStorage, RocksDBStorageSpec

    with (
        InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer,
        RocksDBStorage(RocksDBStorageSpec(codec=BinaryCodecSpec())) as storage,
    ):
        backend = ReactiveStorage(storage=storage, observer=observer)

        def on_change(topic: TupleKey) -> None:
            print(f"Change detected on topic: {topic}")

        # backend.subscribe(("users",), on_change, depth=-1)

        # Start a transaction
        with backend.transaction() as transaction:
            transaction.set(("users", 1), {"name": "Alice"})
            transaction.set(("users", 2), {"name": "Bob"})
            print("User 1 in transaction:", transaction.get(("users", 1)))
            print("User 2 in transaction:", transaction.get(("users", 2)))
            # Commit the transaction

        import time

        start_time = time.perf_counter()
        with backend.transaction() as transaction:
            for i in range(100000):
                transaction.set(("users", i), f"User{i}")
        end_time = time.perf_counter()
        print(f"Committed 100000 users in {end_time - start_time:.4f} seconds")

        start_time = time.perf_counter()
        with backend.transaction() as transaction:
            for i in range(100000):
                transaction.set(("users", i), f"User{i}Updated")
        end_time = time.perf_counter()
        print(f"Updated 100000 users in {end_time - start_time:.4f} seconds")

        start_time = time.perf_counter()
        with backend.snapshot() as snapshot:
            for i in range(100000):
                user = snapshot.get(("users", i))
                assert user == f"User{i}Updated"
        end_time = time.perf_counter()
        print(f"Fetched 100000 users in {end_time - start_time:.4f} seconds")

        # Start a snapshot
        with backend.snapshot() as snapshot:
            print("Snapshot User 1:", snapshot.get(("users", 1)))
            print("Snapshot User 2:", snapshot.get(("users", 2)))


def tree() -> None:
    """Test tree."""
    from redwood.codec import BinaryCodecSpec, TextCodecSpec
    from redwood.observer.in_memory_observer import InMemoryObserver, InMemoryObserverSpec
    from redwood.reactive import ReactiveStorage

    # from redwood.storage.lmdb_storage import LMDBStorage, LMDBStorageSpec
    from redwood.storage.rocksdb_storage import RocksDBStorage, RocksDBStorageSpec
    from redwood.view.registry import ViewRegistry
    from rwstd import DictView, ListView, QueueComponent, QueueContainer, QueueView, Tree

    with (
        InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer,
        # LMDBStorage(LMDBStorageSpec(codec=BinaryCodecSpec())) as storage,
        RocksDBStorage(RocksDBStorageSpec(codec=BinaryCodecSpec())) as storage,
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

        # Work with the tree using transactions
        # with tree.at("users").with_dict_view() as users:
        #     users.set("alice", {"name": "Alice", "age": 30})
        #     users.set("bob", {"name": "Bob", "age": 25})

        #     alice_profile = users.dict_view("alice")
        #     alice_profile.set("location", "Wonderland")

        #     print("Alice's profile in transaction:", alice_profile.extract())

        #     users.list_view("names").store(["alice", "bob"])
        #     users.at("random_user", 12, "profile").dict_view().store({"name": "Random", "age": 20})

        # with tree.at("large_dict").with_dict_view() as large_dict:
        #     for i in range(100_000):
        #         large_dict.set(f"key_{i}", f"value_{i}")

        with tree.at("large_dict").with_dict_view() as large_dict:
            import time

            time_start = time.perf_counter()
            for item in large_dict.items():
                pass
            #     pass
            # # for i in range(100_000):
            # #     _ = large_dict.get(f"key_{i}")
            time_end = time.perf_counter()
            print(f"Fetched 100_000 items from large_dict in {time_end - time_start:.4f} seconds")

        # # After commit, data should be visible in the backend
        # with tree.at("users").with_dict_view(snapshot=True) as users:
        #     print("All users after commit:", users.extract())
        #     alice_profile = users.dict_view("alice")
        #     print("Alice's profile after commit:", alice_profile.extract())


if __name__ == "__main__":
    # storage()
    # backend()
    tree()
