"""In-memory storage backend with copy-on-write transaction isolation.

Fast, ephemeral key-value storage for testing and prototyping. Uses overlay pattern
for efficient transaction isolation without full state copies.

Features:
- Copy-on-write transaction isolation (overlay pattern)
- Thread-safe with RLock
- Optional observer support for notifications
- No persistence - all data lost on close
- Implements full StorageProtocol

Limitations:
- No durability (in-memory only)
- No conflict detection (last commit wins)
- Memory-bound by dataset size
"""

from __future__ import annotations


try:
    from tkv.storages.mem import InMemoryStorage
except ImportError as e:
    raise ImportError(
        "tkv package is required for InMemoryStorage. Install via: pip install tkv"
    ) from e


__all__ = [
    "InMemoryStorage",
]
