"""Nu fabrics wrapping virtuals storage backends.

``FabricLifecycle`` classes over the virtuals storage backends: parent
``__init__`` deferred to ``asetup`` so ``Codec`` and Publisher come from
ctx. ``acleanup`` runs the storage's ``close``.

Backends: ``InMemoryStorage`` (ephemeral), ``RocksDBStorage`` (persistent,
transactional), ``LMDBStorage`` (memory-mapped, MVCC), ``TextStorage``
(human-readable JSON).

DI convention: each storage looks up ``Codec`` under its type. The
publisher is looked up by the class passed as ``publisher_type`` (default:
``InMemoryPublisher``). Pass ``publisher_type=None`` on a read-only
storage that shouldn't publish notifications.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from virtuals.storages.mem import InMemoryStorage as _InMemoryStorage
from virtuals.storages.rocksdb import RocksDBStorage as _RocksDBStorage
from virtuals.storages.textdb import TextStorage as _TextStorage

from .codec import Codec
from .publisher import InMemoryPublisher


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["InMemoryStorage", "LMDBStorage", "RocksDBStorage", "TextStorage"]


def _resolve_publisher(ctx: Context, publisher_type: type | None) -> object | None:
    """Look up the publisher instance in ctx by its fabric class.

    ``publisher_type=None`` means "no publisher" (RO storage / silent
    writes). Anything else is looked up in ctx; missing bindings raise
    a clear error via ``ctx.get``.
    """
    if publisher_type is None:
        return None
    return ctx.get(publisher_type)


class InMemoryStorage(_InMemoryStorage):
    """FabricLifecycle wrapper over ``virtuals.InMemoryStorage``.

    Deps read from ctx at setup: ``Codec`` and a publisher of
    ``publisher_type`` (default ``InMemoryPublisher``). Pass
    ``publisher_type=None`` for silent writes.
    """

    def __init__(self, *, publisher_type: type | None = InMemoryPublisher) -> None:
        self._publisher_type = publisher_type

    def setup(self, ctx: Context) -> None:
        """Read deps from ctx, run the parent constructor, open the store."""
        codec = ctx.get(Codec)
        publisher = _resolve_publisher(ctx, self._publisher_type)
        _InMemoryStorage.__init__(self, codec=codec, publisher=publisher)
        self.open()

    def cleanup(self) -> None:
        """Close the backing store."""
        self.close()

    async def asetup(self, ctx: Context) -> None:
        """Async shim: setup is sync work."""
        self.setup(ctx)

    async def acleanup(self) -> None:
        """Async shim: cleanup is sync work."""
        self.cleanup()


class RocksDBStorage(_RocksDBStorage):
    """FabricLifecycle wrapper over ``virtuals.RocksDBStorage``.

    Config kwargs (``path``, ``read_only``, ``secondary_path``,
    ``secondary_refresh_interval``, ``disable_wal``, ``options``) go to the
    parent constructor at ``asetup`` time. Deps (``Codec``, publisher) come
    from ctx.
    """

    def __init__(
        self,
        *,
        path: str,
        publisher_type: type | None = InMemoryPublisher,
        read_only: bool = False,
        secondary_path: str | None = None,
        secondary_refresh_interval: float | None = 0.01,
        disable_wal: bool = False,
        options: dict | None = None,
    ) -> None:
        self._path = path
        self._publisher_type = publisher_type
        self._read_only = read_only
        self._secondary_path = secondary_path
        self._secondary_refresh_interval = secondary_refresh_interval
        self._disable_wal = disable_wal
        self._options = options

    def setup(self, ctx: Context) -> None:
        """Read deps from ctx, run the parent constructor, open the store."""
        codec = ctx.get(Codec)
        publisher = _resolve_publisher(ctx, self._publisher_type)
        _RocksDBStorage.__init__(
            self,
            path=Path(self._path),
            codec=codec,
            publisher=publisher,
            read_only=self._read_only,
            secondary_path=Path(self._secondary_path) if self._secondary_path else None,
            secondary_refresh_interval=self._secondary_refresh_interval,
            create_if_missing=True,
            disable_wal=self._disable_wal,
            options=self._options,
        )
        self.open()

    def cleanup(self) -> None:
        """Close the backing store."""
        self.close()

    async def asetup(self, ctx: Context) -> None:
        """Async shim: setup is sync work."""
        self.setup(ctx)

    async def acleanup(self) -> None:
        """Async shim: cleanup is sync work."""
        self.cleanup()


class LMDBStorage:
    """FabricLifecycle wrapper over ``virtuals.storages.lmdb.LMDBStorage``.

    Lazy-loaded to avoid a hard ``lmdb`` dep at import time (same shape as
    ``RedisPublisher``). The backing storage is constructed inside ``asetup``
    so importing ``nu.kv.fabrics`` never touches the ``lmdb`` module.
    Instance attribute access delegates to the backing storage once open.

    Config kwargs mirror the imperative ``lmdb_storage`` CM: ``path``,
    ``read_only``, ``map_size``, ``max_readers``, ``subdir``, ``sync``.
    Deps (``Codec``, publisher) come from ctx.
    """

    def __init__(
        self,
        *,
        path: str,
        publisher_type: type | None = InMemoryPublisher,
        read_only: bool = False,
        map_size: int = 10 * 1024 * 1024 * 1024,
        max_readers: int = 126,
        subdir: bool = True,
        sync: bool = True,
    ) -> None:
        self._path = path
        self._publisher_type = publisher_type
        self._read_only = read_only
        self._map_size = map_size
        self._max_readers = max_readers
        self._subdir = subdir
        self._sync = sync
        self._backing = None

    def setup(self, ctx: Context) -> None:
        """Import lmdb lazily, construct the backing env, and open it."""
        from virtuals.storages.lmdb import LMDBStorage as _LMDBStorage

        codec = ctx.get(Codec)
        publisher = _resolve_publisher(ctx, self._publisher_type)
        self._backing = _LMDBStorage(
            path=Path(self._path),
            codec=codec,
            publisher=publisher,
            read_only=self._read_only,
            map_size=self._map_size,
            max_readers=self._max_readers,
            subdir=self._subdir,
            sync=self._sync,
        )
        self._backing.open()

    def cleanup(self) -> None:
        """Close the backing env; drop the reference so re-open works."""
        if self._backing is not None:
            self._backing.close()
            self._backing = None

    async def asetup(self, ctx: Context) -> None:
        """Async shim: setup is sync work."""
        self.setup(ctx)

    async def acleanup(self) -> None:
        """Async shim: cleanup is sync work."""
        self.cleanup()

    def __getattr__(self, name: str) -> object:
        # Delegate storage-protocol access to the backing instance.
        if name.startswith("_"):
            raise AttributeError(name)
        if self._backing is None:
            msg = "LMDBStorage used before asetup"
            raise RuntimeError(msg)
        return getattr(self._backing, name)


class TextStorage(_TextStorage):
    """FabricLifecycle wrapper over ``virtuals.TextStorage``.

    Human-readable JSON storage. Same DI shape as the others.
    """

    def __init__(
        self,
        *,
        path: str,
        publisher_type: type | None = InMemoryPublisher,
        read_only: bool = False,
        log_operations: bool = False,
    ) -> None:
        self._path = path
        self._publisher_type = publisher_type
        self._read_only = read_only
        self._log_operations = log_operations

    def setup(self, ctx: Context) -> None:
        """Read deps from ctx, run the parent constructor, open the store."""
        codec = ctx.get(Codec)
        publisher = _resolve_publisher(ctx, self._publisher_type)
        _TextStorage.__init__(
            self,
            path=Path(self._path),
            codec=codec,
            publisher=publisher,
            log_operations=self._log_operations,
            read_only=self._read_only,
        )
        self.open()

    def cleanup(self) -> None:
        """Close the backing store."""
        self.close()

    async def asetup(self, ctx: Context) -> None:
        """Async shim: setup is sync work."""
        self.setup(ctx)

    async def acleanup(self) -> None:
        """Async shim: cleanup is sync work."""
        self.cleanup()
