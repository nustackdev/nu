"""Scenario: User Database -- 10 users, 5 scalar fields + 10 tags each.

Real-world pattern: shapes -> data -> trees (pre-built) -> benchmark (execution only).
Trees are built once outside the timed section. Only .execute(ctx) is measured.

Two atomicity modes:
  auto_atomic -- each Term wrapped in its own Atomic (1 txn per field op)
  Atomic      -- single Atomic wrapping entire Seq (1 txn for all ops)

Benchmarks (x2 modes):
  store  -- 150 values (10 users x 15 values)
  read   -- 60 field reads (10 users x 6 fields)
  update -- 10 field updates
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
from everypv import Atomic, auto_atomic
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

# Raw Seq (unwrapped) -- shared base for both modes
_store_seq = Seq(*[UserDB.users[k].store(v) for k, v in USERS.items()])

_read_seq = Seq(
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

_update_seq = Seq(*[UserDB.users[k].score.set(99.0) for k in USERS])

# auto_atomic: each Term gets its own Atomic (1 txn per field op)
store_tree_aa = auto_atomic(_store_seq)
read_tree_aa = auto_atomic(_read_seq)
update_tree_aa = auto_atomic(_update_seq)

# Atomic: single txn wrapping entire Seq
store_tree_at = Atomic(_store_seq)
read_tree_at = Atomic(_read_seq)
update_tree_at = Atomic(_update_seq)


# ── Benchmarks ────────────────────────────────────────────────────────────────

N = 500  # iterations


async def _bench(label: str, tree, seed_tree) -> TimingResult:
    """Benchmark with fresh db: seed once, then time tree N times."""
    tmpdir = tempfile.mkdtemp(prefix="bench_user_db_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
            await seed_tree.execute(ctx)
            get_counters().reset()

            with timed_run(label, N) as results:
                for _ in range(N):
                    await tree.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ── Runner ────────────────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    # auto_atomic (1 txn per field op)
    results.append(await _bench(f"store auto_atomic x{N}", store_tree_aa, store_tree_aa))
    results.append(await _bench(f"read auto_atomic x{N}", read_tree_aa, store_tree_aa))
    results.append(await _bench(f"update auto_atomic x{N}", update_tree_aa, store_tree_aa))

    # Atomic (1 txn for all ops)
    results.append(await _bench(f"store Atomic x{N}", store_tree_at, store_tree_at))
    results.append(await _bench(f"read Atomic x{N}", read_tree_at, store_tree_at))
    results.append(await _bench(f"update Atomic x{N}", update_tree_at, store_tree_at))

    uninstall_counters()
    print_results("Scenario: User Database", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
