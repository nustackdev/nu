"""Nu virtuals fabric wrappers: sync + async lifecycle parity per class.

Each sync-capable wrapper gets a sync-path and an async-path lifecycle
test that builds the instance in isolation, wires the minimum ctx
dependencies, drives setup + a smoke check + cleanup. Purpose:
regression-lock the shim symmetry introduced with the Fabric protocol
sync/async duality.

Post publisher/observer split: minimum wiring for a storage is
``Codec + InMemoryTransport + InMemoryPublisher``. The Observer is only
needed when subscriptions are exercised (not here); it's included in
``_pub_ctx`` for symmetry with real actor topologies.

``RedisObserver`` / ``RedisPublisher`` are async-only by design (network
IO); only their markers are asserted here since exercising them would
need a live Redis.
"""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from nu.core.reactive import ObserverProtocol
from nu.kv.fabrics import (
    Codec,
    InMemoryObserver,
    InMemoryPublisher,
    InMemoryStorage,
    InMemoryTransport,
    LMDBStorage,
    Navigator,
    RedisObserver,
    RedisPublisher,
    RocksDBStorage,
    TextStorage,
    binary_kwargs,
    text_kwargs,
)
from nu.lang import Context


if TYPE_CHECKING:
    from pathlib import Path


def _pub_ctx(codec_kwargs: dict) -> Context:
    """Codec + connected InMemoryTransport + InMemoryPublisher (+ Observer).

    Enough context to construct a storage that publishes changes and to
    subscribe on the process-scope Observer.
    """
    ctx = Context().bind(Codec, Codec(**codec_kwargs))
    transport = InMemoryTransport()
    transport.setup(ctx)
    ctx = ctx.bind(InMemoryTransport, transport)
    publisher = InMemoryPublisher()
    publisher.setup(ctx)
    ctx = ctx.bind(InMemoryPublisher, publisher)
    observer = InMemoryObserver()
    observer.setup(ctx)
    return ctx.bind(ObserverProtocol, observer)


def _mem_ctx() -> Context:
    """Binary Codec + Transport + Publisher (+ Observer). Base for binary storages."""
    return _pub_ctx(binary_kwargs())


def _text_ctx() -> Context:
    """Text Codec + Transport + Publisher (+ Observer). Base for TextStorage."""
    return _pub_ctx(text_kwargs())


# --- InMemoryTransport ---------------------------------------------------


def test_inmemory_transport_sync_lifecycle():
    ctx = Context()
    t = InMemoryTransport()
    t.setup(ctx)
    t.cleanup()


async def test_inmemory_transport_async_lifecycle():
    ctx = Context()
    t = InMemoryTransport()
    await t.asetup(ctx)
    await t.acleanup()


# --- InMemoryPublisher ---------------------------------------------------


def test_inmemory_publisher_sync_lifecycle():
    ctx = Context()
    transport = InMemoryTransport()
    transport.setup(ctx)
    ctx = ctx.bind(InMemoryTransport, transport)
    pub = InMemoryPublisher()
    pub.setup(ctx)
    pub.cleanup()


async def test_inmemory_publisher_async_lifecycle():
    ctx = Context()
    transport = InMemoryTransport()
    await transport.asetup(ctx)
    ctx = ctx.bind(InMemoryTransport, transport)
    pub = InMemoryPublisher()
    await pub.asetup(ctx)
    await pub.acleanup()


# --- InMemoryObserver ----------------------------------------------------


def test_inmemory_observer_sync_lifecycle():
    ctx = Context()
    transport = InMemoryTransport()
    transport.setup(ctx)
    ctx = ctx.bind(InMemoryTransport, transport)
    obs = InMemoryObserver()
    obs.setup(ctx)
    obs.cleanup()


async def test_inmemory_observer_async_lifecycle():
    ctx = Context()
    transport = InMemoryTransport()
    await transport.asetup(ctx)
    ctx = ctx.bind(InMemoryTransport, transport)
    obs = InMemoryObserver()
    await obs.asetup(ctx)
    await obs.acleanup()


def test_inmemory_observer_binds_under_observer_protocol():
    """Observer fabrics carry ``_nu_bind_as = ObserverProtocol`` so
    ``nu.core.reactive`` queries can resolve "the observer" without
    knowing which backend is active.
    """
    assert InMemoryObserver._nu_bind_as is ObserverProtocol
    assert RedisObserver._nu_bind_as is ObserverProtocol


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


def test_inmemory_storage_publisher_none():
    """publisher_type=None -> RO/silent storage, no publisher resolution."""
    ctx = Context().bind(Codec, Codec(**binary_kwargs()))
    storage = InMemoryStorage(publisher_type=None)
    storage.setup(ctx)
    with storage.transaction():
        pass
    storage.cleanup()


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


def test_rocksdb_storage_roundtrip(tmp_path: Path):
    """A real store writes and reads back through the fabric path."""
    ctx = _mem_ctx()
    storage = RocksDBStorage(path=str(tmp_path / "db"))
    storage.setup(ctx)
    with storage.transaction() as tx:
        tx.put(("k",), "v")
    with storage.snapshot() as snap:
        assert snap.get(("k",)) == "v"
    storage.cleanup()
    assert storage._backing is None


def test_storage_attr_before_setup_is_attribute_error():
    """Pre-setup access raises AttributeError so ``hasattr`` stays usable."""
    for storage in (RocksDBStorage(path="/nope"), LMDBStorage(path="/nope")):
        with pytest.raises(AttributeError, match="before setup"):
            _ = storage.transaction
        assert not hasattr(storage, "transaction")


# --- rdbpy is not needed to import nu.kv ---------------------------------


_NO_RDBPY_PRELUDE = """
import sys

class _Block:
    def find_spec(self, name, path=None, target=None):
        if name == "rdbpy" or name.startswith("rdbpy."):
            raise ImportError("blocked for test: rdbpy")
        return None

sys.meta_path.insert(0, _Block())
for mod in [m for m in sys.modules if m == "rdbpy" or m.startswith("rdbpy.")]:
    del sys.modules[mod]
"""

_IMPORT_WITHOUT_RDBPY = (
    _NO_RDBPY_PRELUDE
    + """
import nu.kv
import nu.kv.fabrics
assert "rdbpy" not in sys.modules, "importing nu.kv pulled in rdbpy"
print("OK")
"""
)

_SETUP_WITHOUT_RDBPY = (
    _NO_RDBPY_PRELUDE
    + """
from nu.kv.fabrics import Codec, RocksDBStorage, binary_kwargs
from nu.lang import Context

ctx = Context().bind(Codec, Codec(**binary_kwargs()))
storage = RocksDBStorage(path="/tmp/nu-kv-no-rdbpy", publisher_type=None)
try:
    storage.setup(ctx)
except ImportError as e:
    assert "rdbpy" in str(e), f"error does not name the bindings: {e}"
    print("OK")
else:
    raise AssertionError("setup succeeded with rdbpy blocked")
"""
)


def _run_isolated(script: str) -> str:
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    return proc.stdout


def test_import_nu_kv_without_rdbpy():
    """``import nu.kv`` must not require the RocksDB bindings."""
    assert "OK" in _run_isolated(_IMPORT_WITHOUT_RDBPY)


def test_rocksdb_storage_setup_without_rdbpy_names_the_bindings():
    """The dep is paid at setup, and the error says what is missing."""
    assert "OK" in _run_isolated(_SETUP_WITHOUT_RDBPY)


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


# --- Async-only markers --------------------------------------------------


def test_redis_observer_has_async_only_marker():
    assert RedisObserver._nu_async_only is True


def test_redis_publisher_has_async_only_marker():
    assert RedisPublisher._nu_async_only is True
