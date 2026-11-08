"""nu.Stream over a kv collection: drain it, then follow it, each step on a fresh snapshot.

Verifies:
- A log and an ordered dict are drained, then followed as ids are added in
  later commits: bare, under ``auto_flow_atomic``, and under an outer Snapshot.
- The stream resumes past an id deleted under its cursor, the last id too.
- Its two source reads are kv Snapshots on the source's store.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Shape, arun
from nustd.kv import (
    DictRef,
    LogDictRef,
    OrderedDictRef,
    RingRef,
    Snapshot,
    Transaction,
    auto_flow_atomic,
    memory_navigator,
)


class Board(Shape):
    log = LogDictRef.slot(bool)
    cells = OrderedDictRef.slot(bool)


SOURCES = {"log": Board.log, "ordered": Board.cells}


def _follow(source: object, heard: list) -> nu.Nu:
    @nu.host(base=nu.lang.ScalarAction, mutates=frozenset({0}))
    def keep(value: object) -> None:
        heard.append(value)

    return nu.ForEachDo(
        nu.Stream(source, lambda key: nu.Iter(nu.List.of(key))), lambda key: keep(key)
    )


def _until_heard(heard: list, n: int) -> nu.Nu:
    @nu.host(base=nu.lang.ScalarAction, mutates=frozenset({0}))
    async def wait_heard(count: int) -> None:
        while len(heard) < count:
            await asyncio.sleep(0.005)

    return wait_heard(n)


async def _run(source: object, flow: nu.Nu, heard: list, later: nu.Nu, n: int) -> None:
    tree = nu.With(
        memory_navigator(),
        body=Transaction(source.set_item("a", True))  # type: ignore[attr-defined]
        >> nu.Race(flow, nu.DelayedDo(0.02, later) >> _until_heard(heard, n)),
    )
    await asyncio.wait_for(arun(tree), 5.0)


def _adds(source: object, *ids: str) -> nu.Nu:
    return nu.Sequential(*(Transaction(source.set_item(i, True)) for i in ids))  # type: ignore[attr-defined]


@pytest.mark.asyncio
@pytest.mark.parametrize("name", SOURCES)
async def test_drains_then_follows_later_commits(name) -> None:
    source, heard = SOURCES[name], []
    await _run(source, _follow(source, heard), heard, _adds(source, "b", "c"), 3)
    assert heard == ["a", "b", "c"]


@pytest.mark.asyncio
@pytest.mark.parametrize("name", SOURCES)
@pytest.mark.parametrize("wrap", ["auto_flow_atomic", "outer_snapshot"])
async def test_an_outer_bracket_does_not_freeze_it(name, wrap) -> None:
    source, heard = SOURCES[name], []
    flow = _follow(source, heard)
    flow = auto_flow_atomic(flow) if wrap == "auto_flow_atomic" else Snapshot(flow)
    await _run(source, flow, heard, _adds(source, "b", "c"), 3)
    assert heard == ["a", "b", "c"]


@pytest.mark.asyncio
@pytest.mark.parametrize("name", SOURCES)
async def test_resumes_past_an_id_deleted_under_its_cursor(name) -> None:
    source, heard = SOURCES[name], []
    later = Transaction(source.del_item("a")) >> _adds(source, "b")  # type: ignore[attr-defined]
    await _run(source, _follow(source, heard), heard, later, 2)
    assert heard == ["a", "b"]


def test_its_source_reads_are_snapshots_on_the_source_store() -> None:
    for source in SOURCES.values():
        stream = nu.Stream(source, lambda key: nu.Iter(nu.List.of(key)))
        advance, change = nu.tree.children(stream)[:2]
        for read in (advance, change):
            assert isinstance(read, Snapshot)
            assert read.scope is Board


def test_a_mem_source_keeps_its_bare_reads() -> None:
    class Mem(Shape):
        seen = nu.DictRef.slot(bool)

    stream = nu.Stream(Mem.seen, lambda key: nu.Iter(nu.List.of(key)))
    advance, change = nu.tree.children(stream)[:2]
    assert not isinstance(advance, Snapshot)
    assert not isinstance(change, Snapshot)


@pytest.mark.asyncio
@pytest.mark.parametrize("name", SOURCES)
@pytest.mark.parametrize("attempt", range(6))
async def test_resumes_past_the_last_id_deleted_under_its_cursor(name, attempt) -> None:
    # The fresh end key is drawn at random; repeat so a key landing below the
    # deleted one (the bug the end mark fixes) shows up.
    source, heard = SOURCES[name], []
    later = Transaction(source.del_item("a")) >> _adds(source, "b", "c")  # type: ignore[attr-defined]
    await _run(source, _follow(source, heard), heard, later, 3)
    assert heard == ["a", "b", "c"]


class Plain(Shape):
    ids = DictRef.slot(bool)
    out = RingRef.slot(list, capacity=3)


@pytest.mark.parametrize(
    ("source", "hint"),
    [(Plain.ids, "LogDictRef or an OrderedDictRef"), (Plain.out, r"entries\(after=seq\)")],
)
def test_a_source_without_a_cursor_is_refused_at_build(source, hint) -> None:
    with pytest.raises(TypeError, match=hint):
        nu.Stream(source, lambda key: nu.Iter(nu.List.of(key)))
