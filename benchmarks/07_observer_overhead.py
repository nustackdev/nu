"""Scenario 7: Observer Overhead — InMemoryObserver vs no observer.

Measures: register/match/notify overhead.
Compares: writes with observer enabled vs without.
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile


sys.path.insert(0, "benchmarks")

from tkv.tkv.storage import StorageProtocol
from utils import (
    TimingResult,
    get_counters,
    install_counters,
    install_observer_counters,
    print_results,
    timed_run,
    uninstall_counters,
)

import everypv as pv
from everybase import Context
from everybase.abc import Seq
from everypv import Atomic
from everypv.views import DictView
from everyshape import Shape


# --------------------------------------------------------------------------
# Shapes
# --------------------------------------------------------------------------


class ObsBench(Shape):
    f0 = pv.IntRef.slot()
    f1 = pv.StrRef.slot()
    f2 = pv.FloatRef.slot()
    f3 = pv.IntRef.slot()
    f4 = pv.IntRef.slot()


S = ObsBench


# --------------------------------------------------------------------------
# Benchmarks
# --------------------------------------------------------------------------


async def bench_with_observer(n: int) -> TimingResult:
    """Writes with InMemoryObserver (default rocksdb_storage_inmemory)."""
    tmpdir = tempfile.mkdtemp(prefix="bench_obs_on_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
            # Warm up
            await Atomic(S.f0.set(0)).execute(ctx)
            get_counters().reset()

            with timed_run(f"with_observer x{n}", n) as results:
                for i in range(n):
                    await Atomic(
                        Seq(
                            S.f0.set(i),
                            S.f1.set(f"v{i}"),
                            S.f2.set(float(i)),
                            S.f3.set(i * 2),
                            S.f4.set(i * 3),
                        ),
                    ).execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_without_observer(n: int) -> TimingResult:
    """Writes with observer=None (no notification overhead)."""
    tmpdir = tempfile.mkdtemp(prefix="bench_obs_off_")
    try:
        from tkv.codecs import BinaryCodec
        from tkv.storages.rocksdb import RocksDBStorage

        with RocksDBStorage(
            path=tmpdir,
            codec=BinaryCodec(),
            observer=None,
        ) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
            # Warm up
            await Atomic(S.f0.set(0)).execute(ctx)
            get_counters().reset()

            with timed_run(f"without_observer x{n}", n) as results:
                for i in range(n):
                    await Atomic(
                        Seq(
                            S.f0.set(i),
                            S.f1.set(f"v{i}"),
                            S.f2.set(float(i)),
                            S.f3.set(i * 2),
                            S.f4.set(i * 3),
                        ),
                    ).execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_raw_dictview_with_observer(n: int) -> TimingResult:
    """Raw DictView writes with observer — isolates observer cost from term overhead."""
    tmpdir = tempfile.mkdtemp(prefix="bench_obs_raw_on_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            get_counters().reset()

            with timed_run(f"raw_dv_with_observer x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        root = DictView.open_root(tx)
                        root["f0"] = i
                        root["f1"] = f"v{i}"
                        root["f2"] = float(i)
                        root["f3"] = i * 2
                        root["f4"] = i * 3
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_raw_dictview_without_observer(n: int) -> TimingResult:
    """Raw DictView writes without observer."""
    tmpdir = tempfile.mkdtemp(prefix="bench_obs_raw_off_")
    try:
        from tkv.codecs import BinaryCodec
        from tkv.storages.rocksdb import RocksDBStorage

        with RocksDBStorage(
            path=tmpdir,
            codec=BinaryCodec(),
            observer=None,
        ) as storage:
            get_counters().reset()

            with timed_run(f"raw_dv_without_observer x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        root = DictView.open_root(tx)
                        root["f0"] = i
                        root["f1"] = f"v{i}"
                        root["f2"] = float(i)
                        root["f3"] = i * 2
                        root["f4"] = i * 3
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

N = 200


async def run_all() -> list[TimingResult]:
    install_counters()
    install_observer_counters()
    results = []

    results.append(await bench_with_observer(N))
    results.append(await bench_without_observer(N))
    results.append(await bench_raw_dictview_with_observer(N))
    results.append(await bench_raw_dictview_without_observer(N))

    uninstall_counters()
    print_results("Scenario 7: Observer Overhead", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
