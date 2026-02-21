"""Profile each layer transition to find exact overhead sources.

Runs cProfile on each layer's hot loop and prints the top cumulative
callers, so we can see exactly what functions eat the delta at each step.

L4 uses a single event loop (asyncio.run once) to avoid profiling
asyncio create/teardown noise.
"""

from __future__ import annotations

import asyncio
import cProfile
import pstats
import shutil
import sys
import tempfile
from io import StringIO


sys.path.insert(0, "benchmarks")

import rdbpy
from tkv.tkv.storage import StorageProtocol

import everypv as pv
from everybase import Context
from everypv import Atomic
from everyshape import Shape


N = 500


# ── Shapes ──────────────────────────────────────────────────────────────


class FlatShape(Shape):
    value = pv.IntRef.slot()


# ── Profiling helper ────────────────────────────────────────────────────


def profile_sync(name: str, func, top: int = 25) -> None:
    """Profile a sync callable."""
    pr = cProfile.Profile()
    pr.enable()
    func()
    pr.disable()
    _print_stats(name, pr, top)


def profile_async(name: str, coro_fn, top: int = 25) -> None:
    """Profile an async callable under a single event loop."""
    pr = cProfile.Profile()
    pr.enable()
    asyncio.run(coro_fn())
    pr.disable()
    _print_stats(name, pr, top)


def _print_stats(name: str, pr: cProfile.Profile, top: int) -> None:
    buf = StringIO()
    ps = pstats.Stats(pr, stream=buf)
    ps.strip_dirs()
    ps.sort_stats("cumulative")
    ps.print_stats(top)

    print(f"\n{'=' * 70}")
    print(f"  PROFILE: {name}  (N={N})")
    print(f"{'=' * 70}")
    print(buf.getvalue())


# ── L0: Raw rdbpy ──────────────────────────────────────────────────────


def run_l0_put():
    tmpdir = tempfile.mkdtemp(prefix="prof_l0_")
    try:
        opts = rdbpy.Options(create_if_missing=True)
        db = rdbpy.TransactionDB(tmpdir, opts)
        for i in range(N):
            txn = db.begin_transaction()
            txn.put(f"k:{i}".encode(), b"42")
            txn.commit()
            txn.close()
        db.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_l0_get():
    tmpdir = tempfile.mkdtemp(prefix="prof_l0_")
    try:
        opts = rdbpy.Options(create_if_missing=True)
        db = rdbpy.TransactionDB(tmpdir, opts)
        txn = db.begin_transaction()
        for i in range(N):
            txn.put(f"k:{i}".encode(), b"42")
        txn.commit()
        txn.close()
        for i in range(N):
            txn = db.begin_transaction()
            txn.get(f"k:{i}".encode())
            txn.rollback()
            txn.close()
        db.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── L1: TKV ────────────────────────────────────────────────────────────


def run_l1_put():
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="prof_l1_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            for i in range(N):
                with storage.transaction() as tx:
                    tx.put(("/", "k", str(i)), 42)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_l1_get():
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="prof_l1_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            with storage.transaction() as tx:
                for i in range(N):
                    tx.put(("/", "k", str(i)), 42)
            for i in range(N):
                snap = storage.begin_snapshot()
                snap.get(("/", "k", str(i)))
                snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── L2: Container ──────────────────────────────────────────────────────


def run_l2_put():
    from pv.container.container import Container
    from pv.container.container_ops import create_container
    from pv.container.types import ContainerProtocol, ContainerStructure

    from everypv.adapters.storage import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="prof_l2_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                create_container(
                    ("/",),
                    ContainerStructure(1),
                    ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE,
                    tx,
                )
            for i in range(N):
                with storage.transaction() as tx:
                    root = Container.get(("/",), tx)
                    root.put_child_primitive(f"k{i}", 42)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_l2_get():
    from pv.container.container import Container
    from pv.container.container_ops import create_container
    from pv.container.types import ContainerProtocol, ContainerStructure

    from everypv.adapters.storage import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="prof_l2_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                create_container(
                    ("/",),
                    ContainerStructure(1),
                    ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE,
                    tx,
                )
                root = Container.get(("/",), tx)
                for i in range(N):
                    root.put_child_primitive(f"k{i}", 42)
            for i in range(N):
                snap = storage.begin_snapshot()
                root = Container.get(("/",), snap)
                root.get_child_primitive(f"k{i}")
                snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── L3: DictView ───────────────────────────────────────────────────────


def run_l3_put():
    from everypv.adapters.storage import rocksdb_storage_inmemory
    from everypv.views import DictView

    tmpdir = tempfile.mkdtemp(prefix="prof_l3_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                root = DictView.open_root(tx)
                root["_warmup"] = 0
            for i in range(N):
                with storage.transaction() as tx:
                    root = DictView.open_root(tx)
                    root[f"k{i}"] = 42
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_l3_get():
    from everypv.adapters.storage import rocksdb_storage_inmemory
    from everypv.views import DictView

    tmpdir = tempfile.mkdtemp(prefix="prof_l3_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                root = DictView.open_root(tx)
                for i in range(N):
                    root[f"k{i}"] = 42
            for i in range(N):
                snap = storage.begin_snapshot()
                root = DictView.open_root(snap)
                _ = root[f"k{i}"]
                snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── L4: Shape/Ref via Atomic (single event loop) ──────────────────────


async def run_l4_put():
    from everypv.adapters.storage import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="prof_l4_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
            await Atomic(FlatShape.value.set(0)).execute(ctx)
            for i in range(N):
                await Atomic(FlatShape.value.set(i)).execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


async def run_l4_get():
    from everypv.adapters.storage import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="prof_l4_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
            await Atomic(FlatShape.value.set(42)).execute(ctx)
            for i in range(N):
                await Atomic(FlatShape.value.get()).execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── Main ───────────────────────────────────────────────────────────────


def main() -> None:
    profile_sync("L0 raw rdbpy PUT", run_l0_put)
    profile_sync("L1 tkv PUT", run_l1_put)
    profile_sync("L2 container PUT", run_l2_put)
    profile_sync("L3 dictview PUT", run_l3_put)
    profile_async("L4 shape/atomic PUT", run_l4_put)

    print("\n" + "#" * 70)
    print("#  GET PROFILES")
    print("#" * 70)

    profile_sync("L0 raw rdbpy GET", run_l0_get)
    profile_sync("L1 tkv GET", run_l1_get)
    profile_sync("L2 container GET", run_l2_get)
    profile_sync("L3 dictview GET", run_l3_get)
    profile_async("L4 shape/atomic GET", run_l4_get)


if __name__ == "__main__":
    main()
