"""RocksDB storage backend implementation."""

from __future__ import annotations


try:
    from virtuals.storages.rocksdb import RocksDBStorage
except ImportError as e:
    raise ImportError("dependency missing for rocksdb ([uv] pip install tkv rdbpython)") from e


__all__ = [
    "RocksDBStorage",
]
