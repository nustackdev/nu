"""``sqlite_navigator``: a Nu program over the SQLite stack, end to end.

Transactions write, a Snapshot in a fresh program reads it back, on the sync
and async runners, and a navigator opened read-only on the same file sees the
committed state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
import nustd
from nustd.kv import Snapshot, Transaction


if TYPE_CHECKING:
    from pathlib import Path


class Store(nu.Shape):
    count = nustd.kv.IntRef.slot()
    names = nustd.kv.DictRef.slot(str)


WRITE = Transaction(Store.count.set(1) >> Store.names.set({"a": "x"})) >> Transaction(
    Store.count.inc() >> Store.names["b"].set("y")
)
READ = Snapshot(nu.List.of(Store.count, nu.ToDict(Store.names)))


def test_sqlite_navigator_sync(tmp_path: Path):
    path = str(tmp_path / "kv.sqlite")
    nu.run(nu.With(nustd.kv.sqlite_navigator(path), body=WRITE))
    got, _ = nu.run(nu.With(nustd.kv.sqlite_navigator(path), body=READ))
    assert list(got) == [2, {"a": "x", "b": "y"}]

    again, _ = nu.run(
        nu.With(nustd.kv.sqlite_navigator(path, read_only=True), body=Snapshot(Store.count))
    )
    assert again == 2


async def test_sqlite_navigator_async(tmp_path: Path):
    path = str(tmp_path / "kv.sqlite")
    await nu.arun(nu.With(nustd.kv.sqlite_navigator(path), body=WRITE))
    got, _ = await nu.arun(nu.With(nustd.kv.sqlite_navigator(path), body=READ))
    assert list(got) == [2, {"a": "x", "b": "y"}]


def _bump(i: int) -> nu.Nu:
    """A write, an await mid-transaction, then a second write."""
    return Transaction(Store.count.inc() >> nu.Delay(0.01) >> Store.names[f"k{i}"].set("v"))


INIT = Transaction(Store.count.set(0) >> Store.names.set({}))


async def test_sqlite_concurrent_async_transactions_wait_their_turn(tmp_path: Path):
    path = str(tmp_path / "kv.sqlite")
    n = 8
    await nu.arun(nu.With(nustd.kv.sqlite_navigator(path), body=INIT))
    await nu.arun(
        nu.With(
            nustd.kv.sqlite_navigator(path), body=nu.ParallelAsync(*(_bump(i) for i in range(n)))
        )
    )
    got, _ = await nu.arun(nu.With(nustd.kv.sqlite_navigator(path), body=READ))
    assert list(got) == [n, {f"k{i}": "v" for i in range(n)}]


async def test_sqlite_async_nested_and_idle_transactions(tmp_path: Path):
    path = str(tmp_path / "kv.sqlite")
    idle = Transaction(nu.Delay(0.01))  # holds the slot, never touches storage
    nested = Transaction(Transaction(Store.count.inc() >> nu.Delay(0.01)))
    await nu.arun(nu.With(nustd.kv.sqlite_navigator(path), body=INIT))
    await nu.arun(
        nu.With(
            nustd.kv.sqlite_navigator(path),
            body=nu.ParallelAsync(idle, nested, _bump(0)) >> nested,
        )
    )
    got, _ = await nu.arun(nu.With(nustd.kv.sqlite_navigator(path), body=READ))
    assert list(got) == [3, {"k0": "v"}]
