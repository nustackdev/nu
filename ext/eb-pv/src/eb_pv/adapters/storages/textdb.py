"""Text-based storage backend for debugging and learning.

WARNING: TOY IMPLEMENTATION - NOT FOR PRODUCTION USE

This storage backend prioritizes human readability and simplicity over performance.
Perfect for tutorials, examples, and understanding how storage layers work.

Purpose:
  - Learning and onboarding (understand storage concepts)
  - Debugging (inspect state.json with cat/jq/text editor)
  - Toy projects and experimentation
  - Example code and documentation

Features:
  - Human-readable JSON format
  - Simple file-based persistence
  - Optional operation logging
  - Implements StorageProtocol correctly

Limitations:
  - Writes serialized (one transaction at a time)
  - Last writer wins (no conflict detection or optimistic locking)
  - Memory-bound (entire state kept in RAM)
  - Slow writes (full state written to disk on every commit)
  - Single process only (no file locking or coordination)
  - Not suitable for datasets >1000 keys

Use RocksDB adapter for real workloads.
"""

from __future__ import annotations

from virtuals.storages.textdb import TextStorage


__all__ = [
    "TextStorage",
]
