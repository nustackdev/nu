"""Scenario: User Database -- 10 users, 5 scalar fields + 10 tags each.

Real-world pattern: shapes -> data -> trees (pre-built) -> benchmark (execution only).
Trees are built once outside the timed section. Only .execute(ctx) is measured.

Benchmarks:
  store  -- 150 values via auto_atomic (10 users x 15 values)
  read   -- 60 field reads via auto_atomic (10 users x 6 fields)
  update -- 10 field updates via auto_atomic
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile


sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from tkv.tkv.storage import StorageProtocol
from utils import (
    TimingResult,
    get_counters,
    install_counters,
    print_results,
    timed_run,
    uninstall_counters,
)

import everypv as pv
from everybase import Context
from everybase.abc import Seq
from everypv import auto_atomic
from everyshape import Shape


# ── Shapes ────────────────────────────────────────────────────────────────────


class User(Shape):
    name = pv.StrRef.slot()
    age = pv.IntRef.slot()
    email = pv.StrRef.slot()
    score = pv.FloatRef.slot()
    active = pv.IntRef.slot()
    tags = pv.ListRef.slot(item_type=str)


class UserDB(Shape):
    users = pv.ShapesDictRef.slot(shape_type=User)


# ── Data ──────────────────────────────────────────────────────────────────────

NUM_USERS = 10
NUM_TAGS = 10

USERS = {
    f"u{i}": {
        "name": f"User {i}",
        "age": 20 + i,
        "email": f"user{i}@example.com",
        "score": float(i) * 10.5,
        "active": 1 if i % 2 == 0 else 0,
        "tags": [f"tag_{j}" for j in range(NUM_TAGS)],
    }
    for i in range(NUM_USERS)
}


# ── Trees (built once) ───────────────────────────────────────────────────────

store_tree = auto_atomic(Seq(*[UserDB.users[k].store(v) for k, v in USERS.items()]))

read_tree = auto_atomic(
    Seq(
        *[
            term
            for k in USERS
            for term in (
                UserDB.users[k].name.get(),
                UserDB.users[k].age.get(),
                UserDB.users[k].email.get(),
                UserDB.users[k].score.get(),
                UserDB.users[k].active.get(),
                UserDB.users[k].tags.get(),
            )
        ]
    )
)

update_tree = auto_atomic(Seq(*[UserDB.users[k].score.set(99.0) for k in USERS]))


# ── Benchmarks ────────────────────────────────────────────────────────────────

N = 500  # iterations


async def bench_store(ctx: Context) -> TimingResult:
    """Store all 10 users (150 values) via auto_atomic, N times."""
    # Warm up
    await store_tree.execute(ctx)
    get_counters().reset()

    with timed_run(f"user_db store 10x15 x{N}", N) as results:
        for _ in range(N):
            await store_tree.execute(ctx)
    return results[0]


async def bench_read(ctx: Context) -> TimingResult:
    """Read 60 fields (10 users x 6) via auto_atomic, N times."""
    # Ensure data exists
    await store_tree.execute(ctx)
    get_counters().reset()

    with timed_run(f"user_db read 10x6 x{N}", N) as results:
        for _ in range(N):
            await read_tree.execute(ctx)
    return results[0]


async def bench_update(ctx: Context) -> TimingResult:
    """Update 10 scores via auto_atomic, N times."""
    # Ensure data exists
    await store_tree.execute(ctx)
    get_counters().reset()

    with timed_run(f"user_db update 10x1 x{N}", N) as results:
        for _ in range(N):
            await update_tree.execute(ctx)
    return results[0]


# ── Runner ────────────────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    tmpdir = tempfile.mkdtemp(prefix="bench_user_db_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)

            results.append(await bench_store(ctx))
            results.append(await bench_read(ctx))
            results.append(await bench_update(ctx))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Scenario: User Database", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
