"""``.with_parent`` over kv stores: a placed chain routes to its parent's store."""

from __future__ import annotations

import nu
import nustd


kv = nustd.kv


class Counter(nu.Shape):
    value = kv.IntRef.slot()


class Board(nu.Shape):
    entries = kv.DictRef.slot(Counter)


class Cells(nu.Shape):
    pass


class Space(nu.Shape):
    cell_keys = kv.DictRef.slot(str)


class State(nu.Shape):
    cells = kv.DictRef.slot(Cells)


def _stores(body: nu.Nu) -> nu.Nu:
    return nu.With(
        kv.memory_navigator(tags=(Space,)),
        kv.memory_navigator(tags=(State,)),
        body=body,
    )


def test_a_placed_chain_writes_into_its_parents_store():
    value = Counter.value.with_parent(State.cells["c1"])

    class Out(nu.Shape):
        got = nu.mem.IntRef.slot()

    got: dict = {}
    body = (
        kv.Transaction(value.set(41), scope=State)
        >> kv.Transaction(value.set(value + 1), scope=State)
        >> kv.Snapshot(Out.got.set(value), scope=State)
    )
    nu.run(_stores(body), nu.Context().bind(dict, got, Out))
    assert got == {"got": 42}


def test_a_key_read_from_another_store_places_the_chain():
    class Out(nu.Shape):
        got = nu.mem.IntRef.slot()

    entry = Board.entries["x"].value.with_parent(State.cells[Space.cell_keys["summary"]])
    got: dict = {}
    body = (
        kv.Transaction(Space.cell_keys["summary"].set("c7"), scope=Space)
        >> kv.Snapshot(kv.Transaction(entry.set(5), scope=State), scope=Space)
        >> kv.Snapshot(kv.Snapshot(Out.got.set(entry), scope=State), scope=Space)
    )
    nu.run(_stores(body), nu.Context().bind(dict, got, Out))
    assert got == {"got": 5}


def test_auto_flow_atomic_brackets_the_parents_store():
    value = Counter.value.with_parent(State.cells["c1"])

    class Out(nu.Shape):
        got = nu.mem.IntRef.slot()

    got: dict = {}
    body = kv.auto_flow_atomic(value.set(3) >> Out.got.set(value), scope=State)
    nu.run(_stores(body), nu.Context().bind(dict, got, Out))
    assert got == {"got": 3}
