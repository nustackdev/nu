from __future__ import annotations

import time
from pathlib import Path

from everybase.abc import BinaryCodec, DictView, RocksDBStorage


def example_basic_usage() -> None:
    """Demonstrate basic view usage."""
    with RocksDBStorage(path=Path(".db_view_nested"), codec=BinaryCodec()) as storage:
        with storage.transaction() as tx:
            # Create root container
            root = DictView.open_root(tx)

            # Create users container
            users = root.open_child("users", DictView)

            # Store data with nested structures
            write_start = time.perf_counter()
            write_ops = 10_000
            for i in range(write_ops):
                users[f"user{i}"] = {
                    "name": f"Alice {i}",
                    "age": 30,
                    "tags": ["designer", "liquid-glass"],
                    "permissions": {"read", "write", "execute"},
                }
            write_end = time.perf_counter()
            print(f"Write done in {write_end - write_start}s for {write_ops}ops [nested]")

        with storage.snapshot() as snap:
            root = DictView.open_root(snap)

            # Create users container
            users = root.open_child("users", DictView)

            # Store data with nested structures
            read_start = time.perf_counter()
            read_ops = 10_000
            for i in range(read_ops):
                g = users[f"user{i}"]
                if i == 1000:
                    print(g)
            read_end = time.perf_counter()
            print(f"read done in {read_end - read_start}s for {read_ops}ops [nested]")


if __name__ == "__main__":
    example_basic_usage()
