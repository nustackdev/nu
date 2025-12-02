from __future__ import annotations

from pathlib import Path
from typing import cast

from esstd.collections import DictView, ListView
from esstd.storage import BinaryCodec, RocksDBStorage


def example_basic_usage() -> None:
    """Demonstrate basic view usage."""
    with RocksDBStorage(path=Path(".db_view"), codec=BinaryCodec()) as storage:
        with storage.transaction() as tx:
            # Create root container
            root = DictView.open_root(tx)

            # Create users container
            users = root.open_child("users", DictView)

            # Store data with nested structures
            users["alice"] = {
                "name": "Alice Smith",
                "age": 30,
                "tags": ["designer", "liquid-glass"],
                "permissions": {"read", "write", "execute"},
            }

            users["bob"] = {
                "name": "Bob Jones",
                "tags": ["engineer", "AI"],
                "age": 25,
            }

            # Read back
            alice = cast("dict", users["alice"])
            print(f"Alice: {alice}")
            print(f"Alice's tags: {alice['tags']}")
            print(f"All users: {list(users.keys())}")

            # Update
            alice_data = cast("dict", users["alice"])
            alice_data["age"] = 31
            users["alice"] = alice_data

            # Iterate
            for username, data in users.items():
                print(f"User {username}: {cast('dict', data)['name']}")

            bob_view = users.open_child("bob", DictView)
            for k, v in bob_view.items():
                print(f"Bob's {k}: {v}")

        with storage.transaction() as tx:
            # Create root container
            tags = ListView.open_at(
                (
                    ("users", DictView),
                    ("alice", DictView),
                ),
                "tags",
                tx,
            )

            print(tags.extract())

            tags = ListView.open_at_key(
                ("/", "users", "alice", "tags"),
                tx,
            )

            print(tags.extract())


if __name__ == "__main__":
    example_basic_usage()
