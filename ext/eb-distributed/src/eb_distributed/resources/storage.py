"""Storage Resources - composables wrappers for virtuals storage backends.

Three backends:
- InMemoryStorage: fast, ephemeral, no persistence
- RocksDBStorage: persistent, transactional, production-grade
- TextStorage: human-readable JSON, for debugging and learning

Uses multiple inheritance: Resource IS the wrapped object.
All storages default to InMemoryObserver for change notifications.
"""

from __future__ import annotations

import attrs
from composables import Attach, Resource, ResourceSpec, Spec
from virtuals._backends.storages.mem import InMemoryStorage
from virtuals._backends.storages.rocksdb import RocksDBStorage
from virtuals._backends.storages.textdb import TextStorage

from .codec import CodecSpec, binary_codec_spec, noop_codec_spec, text_codec_spec
from .observer import InMemoryObserverSpec


__all__ = [
    "InMemoryStorageResource",
    "InMemoryStorageSpec",
    "RocksDBStorageResource",
    "RocksDBStorageSpec",
    "TextStorageResource",
    "TextStorageSpec",
]


# ============================================================================
# InMemory
# ============================================================================


class InMemoryStorageResource(Resource, InMemoryStorage):
    """Resource that IS an InMemoryStorage."""

    spec: InMemoryStorageSpec
    codec_resource = Attach()
    observer_resource = Attach()

    def __init__(self, spec: object = None, /) -> None:
        Resource.__init__(self, spec)

    async def setup(self) -> None:
        """Init storage with attached codec and open it."""
        InMemoryStorage.__init__(self, codec=self.codec_resource, observer=self.observer_resource)
        self.open()

    async def cleanup(self) -> None:
        """Close storage."""
        self.close()


@attrs.define(frozen=True, slots=True, kw_only=True)
class InMemoryStorageSpec(ResourceSpec):
    """Spec for InMemoryStorageResource."""

    factory: type = InMemoryStorageResource
    name: str = "storage"

    codec_resource: CodecSpec = attrs.Factory(noop_codec_spec)
    observer_resource: Spec = attrs.Factory(InMemoryObserverSpec)


# ============================================================================
# RocksDB
# ============================================================================


class RocksDBStorageResource(Resource, RocksDBStorage):
    """Resource that IS a RocksDBStorage."""

    spec: RocksDBStorageSpec
    codec_resource = Attach()
    observer_resource = Attach()

    def __init__(self, spec: object = None, /) -> None:
        Resource.__init__(self, spec)

    async def setup(self) -> None:
        """Init RocksDB storage with attached codec and open it."""
        from pathlib import Path

        secondary = Path(self.spec.secondary_path) if self.spec.secondary_path else None
        RocksDBStorage.__init__(
            self,
            path=Path(self.spec.path),
            codec=self.codec_resource,
            observer=self.observer_resource,
            read_only=self.spec.read_only,
            secondary_path=secondary,
            create_if_missing=True,
        )
        self.open()

    async def cleanup(self) -> None:
        """Close storage."""
        self.close()


@attrs.define(frozen=True, slots=True, kw_only=True)
class RocksDBStorageSpec(ResourceSpec):
    """Spec for RocksDBStorageResource."""

    factory: type = RocksDBStorageResource
    name: str = "rocksdb-storage"

    path: str = "/tmp/eb-rocksdb"  # noqa: S108
    read_only: bool = False
    secondary_path: str | None = None
    codec_resource: CodecSpec = attrs.Factory(binary_codec_spec)
    observer_resource: Spec = attrs.Factory(InMemoryObserverSpec)


# ============================================================================
# TextStorage
# ============================================================================


class TextStorageResource(Resource, TextStorage):
    """Resource that IS a TextStorage. Human-readable JSON, for debugging."""

    spec: TextStorageSpec
    codec_resource = Attach()
    observer_resource = Attach()

    def __init__(self, spec: object = None, /) -> None:
        Resource.__init__(self, spec)

    async def setup(self) -> None:
        """Init text storage with attached codec and open it."""
        from pathlib import Path

        TextStorage.__init__(
            self,
            path=Path(self.spec.path),
            codec=self.codec_resource,
            observer=self.observer_resource,
            log_operations=self.spec.log_operations,
            read_only=self.spec.read_only,
        )
        self.open()

    async def cleanup(self) -> None:
        """Close storage."""
        self.close()


@attrs.define(frozen=True, slots=True, kw_only=True)
class TextStorageSpec(ResourceSpec):
    """Spec for TextStorageResource."""

    factory: type = TextStorageResource
    name: str = "text-storage"

    path: str = "/tmp/eb-textdb"  # noqa: S108
    read_only: bool = False
    log_operations: bool = False
    codec_resource: CodecSpec = attrs.Factory(text_codec_spec)
    observer_resource: Spec = attrs.Factory(InMemoryObserverSpec)
