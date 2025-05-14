"""
Specs of loomistd packages:
- loomistd.codec
- loomistd.akv
- loomistd.aobserver
- loomistd.kv
- loomistd.observer
- loomistd.state
- loomistd.astate
"""

# isort:skip_file

from __future__ import annotations

# --- Package imports --- #
from .codec.binary import BinaryCodecSpec
from .codec.passthrough import PassthroughCodecSpec
from .codec.json import JSONCodecSpec

# --- Async package imports --- #
from .akv.file_storage import FileStorageSpec as AsyncFileStorageSpec
from .astate import StateSpec as AsyncStateSpec

# --- Sync package imports --- #
from .kv.file_storage import FileStorageSpec as SyncFileStorageSpec
from .kv.in_memory import InMemoryStorageSpec
from .kv.lmdb import LMDBStorageSpec
from .observer.in_memory import InMemoryObserverSpec
from .state import StateSpec as SyncStateSpec

__all__ = [
    "BinaryCodecSpec",
    "PassthroughCodecSpec",
    "JSONCodecSpec",
    "AsyncFileStorageSpec",
    "SyncFileStorageSpec",
    "InMemoryStorageSpec",
    "LMDBStorageSpec",
    "InMemoryObserverSpec",
    "AsyncStateSpec",
    "SyncStateSpec",
]
