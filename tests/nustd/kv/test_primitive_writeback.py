"""Mutations on the blob refs persist: each one stores the whole blob back.

A list, dict or set blob in a mutation slot evaluates to a write-through value,
so ``rows.append(2)`` reaches storage like ``rows.set(...)`` does. Every step
runs as its own program, so what a later step reads is what storage holds. On
memory and SQLite, on the sync and async runners. Under a Snapshot a mutation
raises the storage's read-only error and reads still work.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import nu
from nu import Context, Shape
from nustd.kv import (
    PrimitiveDictRef,
    PrimitiveListRef,
    PrimitiveSetRef,
    Snapshot,
    Transaction,
    sqlite_navigator,
)
from virtuals import Navigator
from virtuals.codecs import NoOpCodec
from virtuals.storages.mem import InMemoryStorage
from virtuals.tkv.storage.exceptions import StorageError


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path


class Bag(Shape):
    rows = PrimitiveListRef.slot()
    meta = PrimitiveDictRef.slot()
    tags = PrimitiveSetRef.slot()


class Store:
    """Runs each term as its own program against one store that outlives the runs."""

    def __init__(self, bind: Callable[[nu.Nu], tuple]) -> None:
        self._bind = bind

    def run(self, term: nu.Nu) -> object:
        return nu.run(*self._bind(term))[0]

    async def arun(self, term: nu.Nu) -> object:
        return (await nu.arun(*self._bind(term)))[0]


@pytest.fixture(params=["memory", "sqlite"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[Store]:
    if request.param == "sqlite":
        path = str(tmp_path / "kv.sqlite")
        yield Store(lambda term: (nu.With(sqlite_navigator(path), body=term),))
        return
    with InMemoryStorage(codec=NoOpCodec()) as storage:
        ctx = Context().bind(Navigator, Navigator(storage))
        yield Store(lambda term: (term, ctx))


LIST_STEPS = [
    (Bag.rows.append(4), [3, 1, 2, 4]),
    (Bag.rows.extend([5, 6]), [3, 1, 2, 4, 5, 6]),
    (Bag.rows.insert(0, 0), [0, 3, 1, 2, 4, 5, 6]),
    (Bag.rows.pop(), [0, 3, 1, 2, 4, 5]),
    (Bag.rows.remove(1), [0, 3, 2, 4, 5]),
    (Bag.rows.sort(), [0, 2, 3, 4, 5]),
    (Bag.rows.clear(), []),
]
DICT_STEPS = [
    (Bag.meta.set_item("b", 2), {"a": 1, "b": 2}),
    (Bag.meta.update({"c": 3}), {"a": 1, "b": 2, "c": 3}),
    (Bag.meta.pop("a"), {"b": 2, "c": 3}),
    (Bag.meta.setdefault("d", 4), {"b": 2, "c": 3, "d": 4}),
    (Bag.meta.setdefault("d", 5), {"b": 2, "c": 3, "d": 4}),
    (Bag.meta.clear(), {}),
]
SET_STEPS = [
    (Bag.tags.add(2), {1, 2}),
    (Bag.tags.discard(1), {2}),
    (Bag.tags.update({3, 4}), {2, 3, 4}),
]
CASES = {
    "list": (Bag.rows, [3, 1, 2], LIST_STEPS),
    "dict": (Bag.meta, {"a": 1}, DICT_STEPS),
    "set": (Bag.tags, {1}, SET_STEPS),
}


@pytest.mark.parametrize("kind", CASES)
def test_mutations_persist_across_runs(store: Store, kind: str) -> None:
    ref, initial, steps = CASES[kind]
    store.run(Transaction(ref.set(initial)))
    for step, expected in steps:
        store.run(Transaction(step))
        assert store.run(Snapshot(ref)) == expected


@pytest.mark.parametrize("kind", CASES)
async def test_mutations_persist_across_runs_async(store: Store, kind: str) -> None:
    ref, initial, steps = CASES[kind]
    await store.arun(Transaction(ref.set(initial)))
    for step, expected in steps:
        await store.arun(Transaction(step))
        assert await store.arun(Snapshot(ref)) == expected


def test_pop_yields_the_element_it_removed(store: Store) -> None:
    store.run(Transaction(Bag.rows.set([1, 2])))
    assert store.run(Transaction(Bag.rows.pop())) == 2
    assert store.run(Snapshot(Bag.rows)) == [1]


def test_a_plain_read_is_the_native_type(store: Store) -> None:
    store.run(Transaction(Bag.rows.set([1]) >> Bag.meta.set({"a": 1}) >> Bag.tags.set({1})))
    got = store.run(Snapshot(nu.List.of(Bag.rows, Bag.meta, Bag.tags)))
    assert [type(v) for v in got] == [list, dict, set]


@pytest.mark.parametrize(
    ("ref", "initial", "mutation"),
    [
        (Bag.rows, [1], Bag.rows.append(2)),
        (Bag.meta, {"a": 1}, Bag.meta.set_item("b", 2)),
        (Bag.tags, {1}, Bag.tags.add(2)),
    ],
)
def test_a_mutation_under_a_snapshot_raises(store: Store, ref, initial, mutation) -> None:
    store.run(Transaction(ref.set(initial)))
    with pytest.raises(StorageError):
        store.run(Snapshot(mutation))
    assert store.run(Snapshot(ref)) == initial


async def test_a_mutation_under_a_snapshot_raises_async(store: Store) -> None:
    await store.arun(Transaction(Bag.rows.set([1])))
    with pytest.raises(StorageError):
        await store.arun(Snapshot(Bag.rows.append(2)))
    assert await store.arun(Snapshot(Bag.rows)) == [1]
