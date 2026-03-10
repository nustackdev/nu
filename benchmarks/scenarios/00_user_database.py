"""Scenario: User Database -- 10 users, 5 scalar fields + 10 tags each.

Real-world pattern: shapes with mixed scalar + collection fields.
Trees are built once outside the timed section. Only .execute(ctx) is measured.

Modes:
  pure dict        -- imperative Python baseline
  PV auto_atomic   -- each Term wrapped in its own Atomic
  PV Atomic        -- single Atomic wrapping entire Seq
  PV Atomic+inline -- PV with inline_refs deformation
  everydict        -- plain dict substrate
  everydict+inline -- everydict with inline_refs deformation

Benchmarks:
  store  -- 10 users x (5 scalars + 10 tags) = 150 field writes
  read   -- 10 users x 6 field reads (5 scalars + tags list)
  update -- 10 score updates
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
import time


sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from utils import (
    TimingResult,
    get_counters,
    install_counters,
    print_results,
    timed_run,
    uninstall_counters,
)
from virtuals.tkv.storage import StorageProtocol

import eb_dict as ed
import eb_virtuals as ebv
from eb_dict.meta import inline_refs as dict_inline_refs
from eb_virtuals import Atomic, auto_atomic
from eb_virtuals.meta import inline_refs as v_inline_refs
from everybase import Context
from everybase.abc import Seq
from everybase.shape import Shape


# ── Shapes (PV substrate) ────────────────────────────────────────────────────


class User(Shape):
    name = ebv.StrRef.slot()
    age = ebv.IntRef.slot()
    email = ebv.StrRef.slot()
    score = ebv.FloatRef.slot()
    active = ebv.IntRef.slot()
    tags = ebv.ListRef.slot(item_type=str)


class UserDB(Shape):
    users = ebv.ShapesDictRef.slot(shape_type=User)


# ── Shapes (dict substrate) ──────────────────────────────────────────────────


class DUser(Shape):
    name = ed.StrRef.slot()
    age = ed.IntRef.slot()
    email = ed.StrRef.slot()
    score = ed.FloatRef.slot()
    active = ed.IntRef.slot()
    tags = ed.ListRef.slot(item_type=str)


class DUserDB(Shape):
    users = ed.ShapesDictRef.slot(shape_type=DUser)


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

# Field-level op counts per tree execution:
#   store (PV): 10 users x 1 store = 10 ops (compound store)
#   store (dict): 10 users x (5 scalars + 10 tags) = 150 ops
#   read (PV): 10 users x 6 field reads = 60 ops
#   read (dict): 10 users x (5 scalars + 10 tags) = 150 ops
#   update: 10 score updates
FIELD_OPS_V = {"store": 10, "read": 60, "update": 10}
FIELD_OPS_DICT = {"store": 150, "read": 150, "update": 10}


# ── Pure Python dict ─────────────────────────────────────────────────────────


def py_store(data: dict) -> None:
    users = data.setdefault("users", {})
    for k, v in USERS.items():
        users[k] = {**v, "tags": list(v["tags"])}


def py_read(data: dict) -> None:
    users = data["users"]
    for k in USERS:
        u = users[k]
        _ = u["name"], u["age"], u["email"], u["score"], u["active"]
        tags = u["tags"]
        for j in range(NUM_TAGS):
            _ = tags[j]


def py_update(data: dict) -> None:
    users = data["users"]
    for k in USERS:
        users[k]["score"] = 99.0


def _bench_pure_dict(label: str, fn, setup_fn, field_ops: int) -> TimingResult:
    data: dict = {}
    setup_fn(data)
    fn(data)  # warmup
    t0 = time.perf_counter()
    for _ in range(N):
        fn(data)
    elapsed = time.perf_counter() - t0
    return TimingResult(name=label, wall_time_s=elapsed, n_ops=N * field_ops, counters={})


# ── Trees: PV (built once) ───────────────────────────────────────────────────

_store_seq = Seq(*[UserDB.users[k].store(v) for k, v in USERS.items()])

_read_seq = Seq(
    *[
        term
        for k in USERS
        for term in (
            UserDB.users[k].name,
            UserDB.users[k].age,
            UserDB.users[k].email,
            UserDB.users[k].score,
            UserDB.users[k].active,
            UserDB.users[k].tags,
        )
    ]
)

_update_seq = Seq(*[UserDB.users[k].score.store(99.0) for k in USERS])

# auto_atomic
store_tree_aa = auto_atomic(_store_seq)
read_tree_aa = auto_atomic(_read_seq)
update_tree_aa = auto_atomic(_update_seq)

# Atomic
store_tree_at = Atomic(_store_seq)
read_tree_at = Atomic(_read_seq)
update_tree_at = Atomic(_update_seq)

# Atomic + inline_refs
store_tree_ai = v_inline_refs(Atomic(_store_seq))
read_tree_ai = v_inline_refs(Atomic(_read_seq))
update_tree_ai = v_inline_refs(Atomic(_update_seq))


# ── Trees: everydict (built once) ────────────────────────────────────────────

_d_store_seq = Seq(
    *[
        term
        for k, v in USERS.items()
        for term in (
            DUserDB.users[k].name.store(v["name"]),
            DUserDB.users[k].age.store(v["age"]),
            DUserDB.users[k].email.store(v["email"]),
            DUserDB.users[k].score.store(v["score"]),
            DUserDB.users[k].active.store(v["active"]),
            # tags: set each tag individually (store() not supported on dict substrate)
            *[DUserDB.users[k].tags[j].store(v["tags"][j]) for j in range(NUM_TAGS)],
        )
    ]
)

_d_read_seq = Seq(
    *[
        term
        for k in USERS
        for term in (
            DUserDB.users[k].name,
            DUserDB.users[k].age,
            DUserDB.users[k].email,
            DUserDB.users[k].score,
            DUserDB.users[k].active,
            # tags: read each individually (collection load not supported on dict substrate)
            *[DUserDB.users[k].tags[j] for j in range(NUM_TAGS)],
        )
    ]
)

_d_update_seq = Seq(*[DUserDB.users[k].score.store(99.0) for k in USERS])

d_store_tree = _d_store_seq
d_read_tree = _d_read_seq
d_update_tree = _d_update_seq

di_store_tree = dict_inline_refs(_d_store_seq)
di_read_tree = dict_inline_refs(_d_read_seq)
di_update_tree = dict_inline_refs(_d_update_seq)


# ── Benchmarks ────────────────────────────────────────────────────────────────

N = 500  # iterations


async def _bench_v(label: str, tree, seed_tree, field_ops: int) -> TimingResult:
    tmpdir = tempfile.mkdtemp(prefix="bench_user_db_")
    try:
        from eb_virtuals.presets import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().bind(storage, StorageProtocol)
            await seed_tree.execute(ctx)
            get_counters().reset()
            with timed_run(label, N * field_ops) as results:
                for _ in range(N):
                    await tree.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def _bench_dict(label: str, tree, seed_tree, field_ops: int) -> TimingResult:
    data: dict = {}
    ctx = Context().bind(data, dict, DUserDB)
    await seed_tree.execute(ctx)
    get_counters().reset()
    with timed_run(label, N * field_ops) as results:
        for _ in range(N):
            await tree.execute(ctx)
    return results[0]


# ── Runner ────────────────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    ps, pr, pu = FIELD_OPS_V["store"], FIELD_OPS_V["read"], FIELD_OPS_V["update"]
    ds, dr, du = FIELD_OPS_DICT["store"], FIELD_OPS_DICT["read"], FIELD_OPS_DICT["update"]

    # Pure dict (matches dict field ops)
    results.append(_bench_pure_dict("store pure dict", py_store, py_store, ds))
    results.append(_bench_pure_dict("read pure dict", py_read, py_store, dr))
    results.append(_bench_pure_dict("update pure dict", py_update, py_store, du))

    # PV auto_atomic
    results.append(await _bench_v("store virtuals auto_atomic", store_tree_aa, store_tree_aa, ps))
    results.append(await _bench_v("read virtuals auto_atomic", read_tree_aa, store_tree_aa, pr))
    results.append(await _bench_v("update virtuals auto_atomic", update_tree_aa, store_tree_aa, pu))

    # PV Atomic
    results.append(await _bench_v("store virtuals Atomic", store_tree_at, store_tree_at, ps))
    results.append(await _bench_v("read virtuals Atomic", read_tree_at, store_tree_at, pr))
    results.append(await _bench_v("update virtuals Atomic", update_tree_at, store_tree_at, pu))

    # PV Atomic + inline_refs
    results.append(await _bench_v("store virtuals Atomic+inline", store_tree_ai, store_tree_ai, ps))
    results.append(await _bench_v("read virtuals Atomic+inline", read_tree_ai, store_tree_ai, pr))
    results.append(
        await _bench_v("update virtuals Atomic+inline", update_tree_ai, store_tree_ai, pu)
    )

    # everydict
    results.append(await _bench_dict("store everydict", d_store_tree, d_store_tree, ds))
    results.append(await _bench_dict("read everydict", d_read_tree, d_store_tree, dr))
    results.append(await _bench_dict("update everydict", d_update_tree, d_store_tree, du))

    # everydict + inline_refs
    results.append(await _bench_dict("store everydict+inline", di_store_tree, di_store_tree, ds))
    results.append(await _bench_dict("read everydict+inline", di_read_tree, di_store_tree, dr))
    results.append(await _bench_dict("update everydict+inline", di_update_tree, di_store_tree, du))

    uninstall_counters()
    print_results("Scenario: User Database", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
