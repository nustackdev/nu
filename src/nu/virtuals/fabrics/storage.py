"""Nu fabrics wrapping virtuals storage backends.

``FabricLifecycle`` classes over the virtuals storage backends: parent
``__init__`` deferred to ``asetup`` so ``Codec`` and Observer come from ctx.
``acleanup`` runs the storage's ``close``.

Three backends:
- ``InMemoryStorage`` - ephemeral, fast, no persistence.
- ``RocksDBStorage`` - persistent, transactional, production.
- ``TextStorage`` - human-readable JSON, for debugging and learning.

DI convention: each storage looks up ``Codec`` under its type. Observer is
looked up by the class passed as ``observer_type`` (default:
``InMemoryObserver``).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from virtuals.storages.mem import InMemoryStorage as _InMemoryStorage
from virtuals.storages.rocksdb import RocksDBStorage as _RocksDBStorage
from virtuals.storages.textdb import TextStorage as _TextStorage

from .codec import Codec
from .observer import InMemoryObserver


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["InMemoryStorage", "RocksDBStorage", "TextStorage"]


class InMemoryStorage(_InMemoryStorage):
    """FabricLifecycle wrapper over ``virtuals.InMemoryStorage``.

    Deps read from ctx at setup: ``Codec`` and an observer of
    ``observer_type`` (default ``InMemoryObserver``).
    """

    def __init__(self, *, observer_type: type = InMemoryObserver) -> None:
        self._observer_type = observer_type

    async def asetup(self, ctx: Context) -> None:
        codec = ctx.get(Codec)
        observer = ctx.get(self._observer_type)
        _InMemoryStorage.__init__(self, codec=codec, observer=observer)
        self.open()

    async def acleanup(self) -> None:
        self.close()


class RocksDBStorage(_RocksDBStorage):
    """FabricLifecycle wrapper over ``virtuals.RocksDBStorage``.

    Config kwargs (``path``, ``read_only``, ``secondary_path``,
    ``secondary_refresh_interval``, ``disable_wal``, ``options``) go to the
    parent constructor at ``asetup`` time. Deps (``Codec``, observer) come
    from ctx.
    """

    def __init__(
        self,
        *,
        path: str,
        observer_type: type = InMemoryObserver,
        read_only: bool = False,
        secondary_path: str | None = None,
        secondary_refresh_interval: float | None = 0.01,
        disable_wal: bool = False,
        options: dict | None = None,
    ) -> None:
        self._path = path
        self._observer_type = observer_type
        self._read_only = read_only
        self._secondary_path = secondary_path
        self._secondary_refresh_interval = secondary_refresh_interval
        self._disable_wal = disable_wal
        self._options = options

    async def asetup(self, ctx: Context) -> None:
        codec = ctx.get(Codec)
        observer = ctx.get(self._observer_type)
        _RocksDBStorage.__init__(
            self,
            path=Path(self._path),
            codec=codec,
            observer=observer,
            read_only=self._read_only,
            secondary_path=Path(self._secondary_path) if self._secondary_path else None,
            secondary_refresh_interval=self._secondary_refresh_interval,
            create_if_missing=True,
            disable_wal=self._disable_wal,
            options=self._options,
        )
        self.open()

    async def acleanup(self) -> None:
        self.close()


class TextStorage(_TextStorage):
    """FabricLifecycle wrapper over ``virtuals.TextStorage``.

    Human-readable JSON storage. Same DI shape as the others.
    """

    def __init__(
        self,
        *,
        path: str,
        observer_type: type = InMemoryObserver,
        read_only: bool = False,
        log_operations: bool = False,
    ) -> None:
        self._path = path
        self._observer_type = observer_type
        self._read_only = read_only
        self._log_operations = log_operations

    async def asetup(self, ctx: Context) -> None:
        codec = ctx.get(Codec)
        observer = ctx.get(self._observer_type)
        _TextStorage.__init__(
            self,
            path=Path(self._path),
            codec=codec,
            observer=observer,
            log_operations=self._log_operations,
            read_only=self._read_only,
        )
        self.open()

    async def acleanup(self) -> None:
        self.close()
