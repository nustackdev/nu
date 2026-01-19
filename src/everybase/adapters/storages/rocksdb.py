"""RocksDB storage backend implementation."""

from __future__ import annotations


try:
    from evkv.rocksdb import RocksDBStorage
except ImportError as e:
    raise ImportError("dependency missing for rocksdb (pip install evkv, rdbpy)") from e


__all__ = [
    "RocksDBStorage",
]
