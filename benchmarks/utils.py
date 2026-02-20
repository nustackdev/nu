"""Shared benchmark instrumentation — counters, timing, reporting."""

from __future__ import annotations

import asyncio
import shutil
import tempfile
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pv.view import View
from tkv.tkv.storage import StorageProtocol

from everybase import Context
from everypv.adapters.storage import rocksdb_storage_inmemory
from everypv.views import DictView


if TYPE_CHECKING:
    from collections.abc import Generator


# ============================================================================
# COUNTERS
# ============================================================================


@dataclass
class Counters:
    """Monkey-patch counters for key subsystems."""

    counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _originals: dict[str, Any] = field(default_factory=dict, repr=False)

    def reset(self) -> None:
        self.counts.clear()

    def snapshot(self) -> dict[str, int]:
        return dict(self.counts)

    def inc(self, name: str) -> None:
        self.counts[name] += 1


_counters = Counters()


def get_counters() -> Counters:
    return _counters


def _patch_method(target: Any, attr: str, counter_name: str) -> tuple[Any, Any]:
    """Patch a method to increment a counter. Returns (original, patched)."""
    original = getattr(target, attr)

    def patched(*args: Any, **kwargs: Any) -> Any:
        _counters.inc(counter_name)
        return original(*args, **kwargs)

    return original, patched


def install_counters() -> None:
    """Monkey-patch key subsystems to count operations."""
    from pv.container import container_ops, node_ops
    from tkv._storages.rocksdb.context import ReadOperationsMixin, WriteOperationsMixin
    from tkv._storages.rocksdb.storage import RocksDBStorage
    from tkv._storages.rocksdb.transaction import RocksDBTransaction

    patches = [
        (RocksDBStorage, "begin_transaction", "storage.begin_transaction"),
        (RocksDBStorage, "begin_snapshot", "storage.begin_snapshot"),
        (ReadOperationsMixin, "get", "rocksdb.get"),
        (WriteOperationsMixin, "put", "rocksdb.put"),
        (ReadOperationsMixin, "scan", "rocksdb.scan"),
        (RocksDBTransaction, "commit", "rocksdb.commit"),
        (node_ops, "get_node_info", "pv.get_node_info"),
        (node_ops, "node_exists", "pv.node_exists"),
        (container_ops, "create_container", "pv.create_container"),
    ]

    for target, attr, name in patches:
        if name not in _counters._originals:
            orig, patched = _patch_method(target, attr, name)
            _counters._originals[name] = (target, attr, orig)
            setattr(target, attr, patched)


def uninstall_counters() -> None:
    """Restore original methods."""
    for name, (target, attr, orig) in _counters._originals.items():
        setattr(target, attr, orig)
    _counters._originals.clear()


# ============================================================================
# OBSERVER COUNTERS (separate, toggled per-scenario)
# ============================================================================


def install_observer_counters() -> None:
    """Patch observer notify/match for counting."""
    from tkv._observers._base import BaseObserver

    if "observer.notify" not in _counters._originals:
        orig, patched = _patch_method(BaseObserver, "notify", "observer.notify")
        _counters._originals["observer.notify"] = (BaseObserver, "notify", orig)
        BaseObserver.notify = patched


# ============================================================================
# TIMING
# ============================================================================


@dataclass
class TimingResult:
    name: str
    wall_time_s: float
    n_ops: int
    counters: dict[str, int]

    @property
    def per_op_ms(self) -> float:
        if self.n_ops == 0:
            return 0.0
        return (self.wall_time_s / self.n_ops) * 1000

    @property
    def ops_per_sec(self) -> float:
        if self.wall_time_s == 0:
            return float("inf")
        return self.n_ops / self.wall_time_s


@contextmanager
def timed_run(name: str, n_ops: int) -> Generator[list[TimingResult], None, None]:
    """Context manager that times a block and captures counters."""
    results: list[TimingResult] = []
    _counters.reset()
    start = time.perf_counter()
    yield results
    elapsed = time.perf_counter() - start
    results.append(
        TimingResult(
            name=name,
            wall_time_s=elapsed,
            n_ops=n_ops,
            counters=_counters.snapshot(),
        )
    )


# ============================================================================
# STORAGE SETUP
# ============================================================================


@contextmanager
def fresh_rocksdb_ctx() -> Generator[Context, None, None]:
    """Create a fresh RocksDB + InMemory observer context with a temp dir."""
    tmpdir = tempfile.mkdtemp(prefix="bench_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                root = DictView.open_root(tx)
                ctx = Context().with_handle(View, root)
                yield ctx
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@contextmanager
def fresh_rocksdb_storage() -> Generator[tuple[Any, str], None, None]:
    """Create fresh RocksDB storage (raw), returns (storage, tmpdir)."""
    tmpdir = tempfile.mkdtemp(prefix="bench_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            yield storage, tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@contextmanager
def fresh_storage_ctx() -> Generator[tuple[Context, Any], None, None]:
    """Create a fresh context with StorageProtocol handle for Atomic/auto_atomic flows."""
    tmpdir = tempfile.mkdtemp(prefix="bench_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
            yield ctx, storage
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ============================================================================
# REPORTING
# ============================================================================


def format_result_table(results: list[TimingResult]) -> str:
    """Format results as a markdown table."""
    lines = []
    lines.append("| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |")
    lines.append("|----------|-------|----------|-------------|-------|")
    for r in results:
        lines.append(
            f"| {r.name} | {r.n_ops:,} | {r.wall_time_s:.4f} | "
            f"{r.per_op_ms:.3f} | {r.ops_per_sec:,.0f} |"
        )
    return "\n".join(lines)


def format_counter_table(results: list[TimingResult]) -> str:
    """Format counter details as markdown."""
    # Collect all counter keys
    all_keys: set[str] = set()
    for r in results:
        all_keys.update(r.counters.keys())
    if not all_keys:
        return "_No counters recorded._"

    sorted_keys = sorted(all_keys)

    lines = []
    header = "| Scenario | " + " | ".join(sorted_keys) + " |"
    sep = "|----------|" + "|".join("---:" for _ in sorted_keys) + "|"
    lines.append(header)
    lines.append(sep)
    for r in results:
        vals = " | ".join(str(r.counters.get(k, 0)) for k in sorted_keys)
        lines.append(f"| {r.name} | {vals} |")
    return "\n".join(lines)


def print_results(scenario_name: str, results: list[TimingResult]) -> None:
    """Print formatted results to stdout."""
    print(f"\n{'=' * 60}")
    print(f"  {scenario_name}")
    print(f"{'=' * 60}")
    for r in results:
        print(f"\n  {r.name}:")
        print(f"    Wall time:  {r.wall_time_s:.4f}s")
        print(f"    Per-op:     {r.per_op_ms:.3f}ms")
        print(f"    Ops/sec:    {r.ops_per_sec:,.0f}")
        if r.counters:
            print("    Counters:")
            for k, v in sorted(r.counters.items()):
                print(f"      {k}: {v:,}")


# ============================================================================
# ASYNC RUNNER
# ============================================================================


def run_async(coro: Any) -> Any:
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)
