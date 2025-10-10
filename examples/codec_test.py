#!/usr/bin/env python3
"""Calculator service example using Invisibles over NetKit."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.types import Key

logging.basicConfig(level=logging.INFO)


# ============================================================================
# Main
# ============================================================================


def codec() -> None:
    """Test codecs."""
    from redwood.codec import BinaryCodec, BinaryCodecSpec, TextCodec, TextCodecSpec

    class A:
        pass

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
    from redwood.codec import TextCodecSpec
    from redwood.observer.in_memory_observer import InMemoryObserver, InMemoryObserverSpec
    from redwood.storage.in_memory_storage import InMemoryStorage, InMemoryStorageSpec
    from redwood.tree.backend import ObservableStorage

    with (
        InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer,
        InMemoryStorage(InMemoryStorageSpec(codec=TextCodecSpec())) as storage,
    ):
        backend = ObservableStorage(storage=storage, observer=observer)

        def on_change(topic: Key) -> None:
            print(f"Change detected on topic: {topic}")

        backend.subscribe(("users",), on_change, depth=-1)

        # Start a transaction
        with backend.transaction() as transaction:
            transaction.set(("users", 1), {"name": "Alice"})
            transaction.set(("users", 2), {"name": "Bob"})
            print("User 1 in transaction:", transaction.get(("users", 1)))
            print("User 2 in transaction:", transaction.get(("users", 2)))
            # Commit the transaction

        print("User 1 after commit:", backend.get(("users", 1)))
        print("User 2 after commit:", backend.get(("users", 2)))

        # Start a snapshot
        with backend.snapshot() as snapshot:
            print("Snapshot User 1:", snapshot.get(("users", 1)))
            print("Snapshot User 2:", snapshot.get(("users", 2)))


if __name__ == "__main__":
    # storage()
    backend()
