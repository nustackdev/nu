"""Collection of adapters for Redwood Standard Library (rwstd)."""

from __future__ import annotations

# Adapters
from .codec_json import JSONCodec
from .codec_micropack import MicroPackCodec
from .codec_msgpack import MessagePackCodec
from .codec_passthrough import PassthroughCodec
from .codec_pickle import PickleCodec
from .codecs import (
    BinaryCodec,
    BinaryCodecSpec,
    NoOpCodec,
    NoOpCodecSpec,
    TextCodec,
    TextCodecSpec,
)
from .observer_inmemory import InMemoryObserver, InMemoryObserverSpec
from .storage_inmemory import InMemoryStorage, InMemoryStorageSpec
from .storage_json import FileStorage, FileStorageSpec
from .storage_lmdb import LMDBStorage, LMDBStorageSpec
from .storage_rocksdb import RocksDBStorage, RocksDBStorageSpec


__all__ = [
    "BinaryCodec",
    "BinaryCodecSpec",
    "FileStorage",
    "FileStorageSpec",
    "InMemoryObserver",
    "InMemoryObserverSpec",
    "InMemoryStorage",
    "InMemoryStorageSpec",
    "JSONCodec",
    "LMDBStorage",
    "LMDBStorageSpec",
    "MessagePackCodec",
    "MicroPackCodec",
    "NoOpCodec",
    "NoOpCodecSpec",
    "PassthroughCodec",
    "PickleCodec",
    "RocksDBStorage",
    "RocksDBStorageSpec",
    "TextCodec",
    "TextCodecSpec",
]
