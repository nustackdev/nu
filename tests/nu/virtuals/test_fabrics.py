"""Nu virtuals fabric wrappers: sync + async lifecycle parity per class.

Each sync-capable wrapper gets a sync-path and an async-path lifecycle
test that builds the instance in isolation, wires the minimum ctx
dependencies, drives setup + a smoke check + cleanup. Purpose:
regression-lock the shim symmetry introduced with the Fabric protocol
sync/async duality (commit 05045a73).

``RedisObserver`` is async-only by design (network IO); only its marker
is asserted here since exercising it would need a live Redis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from nu.lang import Context
from nu.virtuals.fabrics import (
    Codec,
    InMemoryObserver,
    InMemoryStorage,
    LMDBStorage,
    Navigator,
    RedisObserver,
    RocksDBStorage,
    TextStorage,
    binary_kwargs,
    text_kwargs,
)


if TYPE_CHECKING:
    from pathlib import Path


def _mem_ctx() -> Context:
    """Binary Codec + connected InMemoryObserver. Base for binary storages."""
    ctx = Context().bind(Codec, Codec(**binary_kwargs()))
    obs = InMemoryObserver()
    obs.setup(ctx)
    return ctx.bind(InMemoryObserver, obs)


def _text_ctx() -> Context:
    """Text Codec + connected InMemoryObserver. Base for TextStorage."""
    ctx = Context().bind(Codec, Codec(**text_kwargs()))
    obs = InMemoryObserver()
    obs.setup(ctx)
    return ctx.bind(InMemoryObserver, obs)


# --- InMemoryObserver ----------------------------------------------------


def test_inmemory_observer_sync_lifecycle():
    ctx = Context().bind(Codec, Codec(**binary_kwargs()))
    obs = InMemoryObserver()
    obs.setup(ctx)
    obs.cleanup()


async def test_inmemory_observer_async_lifecycle():
    ctx = Context().bind(Codec, Codec(**binary_kwargs()))
    obs = InMemoryObserver()
    await obs.asetup(ctx)
    await obs.acleanup()


# --- InMemoryStorage -----------------------------------------------------


def test_inmemory_storage_sync_lifecycle():
    ctx = _mem_ctx()
    storage = InMemoryStorage()
    storage.setup(ctx)
    with storage.transaction():
        pass
    storage.cleanup()


async def test_inmemory_storage_async_lifecycle():
    ctx = _mem_ctx()
    storage = InMemoryStorage()
    await storage.asetup(ctx)
    with storage.transaction():
        pass
    await storage.acleanup()


# --- RocksDBStorage ------------------------------------------------------


def test_rocksdb_storage_sync_lifecycle(tmp_path: Path):
    ctx = _mem_ctx()
    storage = RocksDBStorage(path=str(tmp_path / "db"))
    storage.setup(ctx)
    with storage.transaction():
        pass
    storage.cleanup()


async def test_rocksdb_storage_async_lifecycle(tmp_path: Path):
    ctx = _mem_ctx()
    storage = RocksDBStorage(path=str(tmp_path / "db"))
    await storage.asetup(ctx)
    with storage.transaction():
        pass
    await storage.acleanup()


# --- LMDBStorage ---------------------------------------------------------


def test_lmdb_storage_sync_lifecycle(tmp_path: Path):
    pytest.importorskip("lmdb")
    ctx = _mem_ctx()
    storage = LMDBStorage(path=str(tmp_path / "db"))
    storage.setup(ctx)
    with storage.transaction():
        pass
    storage.cleanup()


async def test_lmdb_storage_async_lifecycle(tmp_path: Path):
    pytest.importorskip("lmdb")
    ctx = _mem_ctx()
    storage = LMDBStorage(path=str(tmp_path / "db"))
    await storage.asetup(ctx)
    with storage.transaction():
        pass
    await storage.acleanup()


# --- TextStorage ---------------------------------------------------------


def test_text_storage_sync_lifecycle(tmp_path: Path):
    ctx = _text_ctx()
    storage = TextStorage(path=str(tmp_path / "db"))
    storage.setup(ctx)
    with storage.transaction():
        pass
    storage.cleanup()


async def test_text_storage_async_lifecycle(tmp_path: Path):
    ctx = _text_ctx()
    storage = TextStorage(path=str(tmp_path / "db"))
    await storage.asetup(ctx)
    with storage.transaction():
        pass
    await storage.acleanup()


# --- Navigator -----------------------------------------------------------


def test_navigator_sync_lifecycle():
    ctx = _mem_ctx()
    storage = InMemoryStorage()
    storage.setup(ctx)
    ctx = ctx.bind(InMemoryStorage, storage)
    nav = Navigator(storage_type=InMemoryStorage)
    nav.setup(ctx)
    assert nav.storage is storage
    nav.cleanup()
    storage.cleanup()


async def test_navigator_async_lifecycle():
    ctx = _mem_ctx()
    storage = InMemoryStorage()
    await storage.asetup(ctx)
    ctx = ctx.bind(InMemoryStorage, storage)
    nav = Navigator(storage_type=InMemoryStorage)
    await nav.asetup(ctx)
    assert nav.storage is storage
    await nav.acleanup()
    await storage.acleanup()


# --- Async-only marker ---------------------------------------------------


def test_redis_observer_has_async_only_marker():
    assert RedisObserver._nu_async_only is True
