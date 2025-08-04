"""
Storage Specs - State management utilities

Provides utility functions for creating common state storage configurations
with sensible defaults for different use cases.
"""

from __future__ import annotations

from pathlib import Path

from loomistd.codec.json import JSONCodecSpec
from loomistd.codec.msgpack import MsgpackCodecSpec
from loomistd.codec.passthrough import PassthroughCodecSpec
from loomistd.kv.file_storage import FileStorageSpec
from loomistd.kv.in_memory import InMemoryStorageSpec
from loomistd.kv.lmdb import LMDBStorageSpec
from loomistd.observer.in_memory import InMemoryObserverSpec
from loomistd.state import StateSpec

__all__ = [
    "get_lmdb_state_spec",
    "get_memory_state_spec",
    "get_file_state_spec",
]


def get_lmdb_state_spec(
    path: str | Path = ".db",
    *,
    mode: str = "write",
    name: str = "lmdb_state",
    map_size: int = 10 * 1024 * 1024 * 1024,
    max_dbs: int = 0,
) -> StateSpec:
    """
    Create an LMDB-backed state spec for high-performance persistent storage.

    LMDB provides memory-mapped file storage with ACID transactions,
    making it ideal for production applications that need durability.

    Args:
        path: Database directory path
        map_size: Maximum database size in bytes (default 10GB)
        max_dbs: Maximum number of databases (0 = unlimited)
        mode: Access mode ("read" or "write")
        codec: Serialization codec ("binary", "json", "msgpack")
        name: State service name

    Returns:
        StateSpec configured for LMDB storage

    Examples:
        ```python
        # Basic LMDB state for trading app
        state = get_lmdb_state_spec("./trading.db", map_size=50*1024**3)

        # Read-only LMDB for analytics
        readonly_state = get_lmdb_state_spec(
            "./market_data.db",
            mode="read",
        )

        # Large-scale production setup
        prod_state = get_lmdb_state_spec(
            "/data/app.db",
            map_size=100*1024**3,  # 100GB
            max_dbs=10
        )
        ```
    """
    return StateSpec(
        name=name,
        storage=LMDBStorageSpec(
            path=Path(path) if isinstance(path, str) else path,
            map_size=map_size,
            max_dbs=max_dbs,
            mode=mode,
            codec=MsgpackCodecSpec(),
        ),
        observer=InMemoryObserverSpec(),
    )


def get_memory_state_spec(*, name: str = "memory_state") -> StateSpec:
    """
    Create an in-memory state spec for development and testing.

    Fast but non-persistent storage ideal for development,
    testing, and temporary data processing.

    Args:
        codec: Serialization codec ("passthrough", "json", "binary")
        name: State service name

    Returns:
        StateSpec configured for in-memory storage

    Examples:
        ```python
        # Development state (no serialization overhead)
        dev_state = get_memory_state_spec()

        # Testing with JSON codec for inspection
        test_state = get_memory_state_spec(codec="json")
        ```
    """
    codec = PassthroughCodecSpec()
    return StateSpec(
        name=name,
        storage=InMemoryStorageSpec(codec=codec),
        observer=InMemoryObserverSpec(codec=codec),
    )


def get_file_state_spec(
    path: str | Path = "./state.json",
    *,
    mode: str = "write",
    name: str = "file_state",
) -> StateSpec:
    """
    Create a file-based state spec for simple persistent storage.

    Single-file JSON/binary storage with backup rotation.
    Good for smaller applications and configuration data.

    Args:
        path: File path for state storage
        codec: Serialization codec ("json", "binary", "msgpack")
        backup_count: Number of backup files to maintain
        name: State service name

    Returns:
        StateSpec configured for file storage

    Examples:
        ```python
        # Simple config storage
        config_state = get_file_state_spec("./config.json")

        # Binary state with backups
        app_state = get_file_state_spec(
            "./app_state.bin",
            codec="binary",
            backup_count=5
        )
        ```
    """
    return StateSpec(
        name=name,
        storage=FileStorageSpec(
            path=Path(path) if isinstance(path, str) else path,
            mode=mode,
            codec=JSONCodecSpec(),
        ),
        observer=InMemoryObserverSpec(),
    )
