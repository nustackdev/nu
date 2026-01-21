from __future__ import annotations

import time
from pathlib import Path

from everybase.adapters.codecs import BinaryCodec
from everybase.adapters.storages.rocksdb import RocksDBStorage
from everybase.view import DictView


def example_basic_usage() -> None:
    """Demonstrate basic view usage."""
    with (
        RocksDBStorage(path=Path(".db_bench_term_b"), codec=BinaryCodec()) as storage,
        storage.transaction() as tx,
    ):
        with storage.transaction() as tx:
            # Create root container
            root = DictView.open_root(tx)

            # Create users container
            users = root.open_child("users", DictView)

            # Store data with nested structures
            write_start = time.perf_counter()
            write_ops = 10_000
            for i in range(write_ops):
                users[f"user_flat{i}"] = 1
            write_end = time.perf_counter()
            print(f"Write done in {write_end - write_start}s for {write_ops}ops [flat]")

        with storage.snapshot() as snap:
            root = DictView.open_root(snap)

            # Create users container
            users = root.open_child("users", DictView)

            # Store data with nested structures
            read_start = time.perf_counter()
            read_ops = 10_000
            for i in range(read_ops):
                _g = users[f"user_flat{i}"]
            read_end = time.perf_counter()
            print(f"read done in {read_end - read_start}s for {read_ops}ops [flat]")


if __name__ == "__main__":
    example_basic_usage()
