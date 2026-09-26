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
