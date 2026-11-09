"""Tests for ``.with_parent(ref)``: one chain's head placed under a parent ref.

Structural checks on blueprint refs, then runs on the mem fabric: the placed
chain reads and writes typed under the parent, in the parent's store.
"""

from __future__ import annotations

import pytest

import nu
from nu.domains.shape import Shape, with_parent
from nu.domains.shape.base import ANCHOR, StructuredRef
from nu.lang import Literal


class Counter(Shape):
    value = nu.IntRef.slot()


class Board(Shape):
    title = nu.StrRef.slot()
    entries = nu.DictRef.slot(Counter)


class Cells(Shape):
    pass


class Here(Shape):
    cell = nu.StrRef.slot()


class State(Shape):
    cells = nu.DictRef.slot(Cells)


class Other(Shape):
    cells = nu.DictRef.slot(Cells)


def path(node):
    """Static addresses of a chain, root-first; a ref address shows as the ref."""
    segs = []
    while isinstance(node, StructuredRef):
        seg = nu.tree.children(node)[1]
        segs.append(nu.tree.payload(seg)["value"] if isinstance(seg, Literal) else seg)
        node = nu.tree.children(node)[0]
    segs.reverse()
    return tuple(segs), node


# --- structure --------------------------------------------------------------


def test_the_head_lands_under_the_parent():
    placed = Counter.value.with_parent(State.cells["c1"])
    segs, bottom = path(placed)
    assert segs == ("cells", "c1", "value")
    assert bottom is ANCHOR


def test_the_method_and_the_function_agree():
    a = Counter.value.with_parent(State.cells["c1"])
    b = with_parent(Counter.value, State.cells["c1"])
    assert path(a)[0] == path(b)[0]


def test_every_spine_node_takes_the_parents_root_shape():
    placed = Board.entries["x"].value.with_parent(State.cells["c1"])
    node = placed
    for _ in range(3):  # value, entries["x"], entries
        assert nu.shape.root_shape(node) is State
        node = nu.tree.children(node)[0]


def test_the_source_chain_is_untouched():
    source = Board.entries["x"].value
    source.with_parent(State.cells["c1"])
    assert path(source)[0] == ("entries", "x", "value")
    assert nu.shape.root_shape(source) is Board
    assert not nu.tree.payload(source).get("placed")


def test_an_index_that_is_a_ref_stays_as_it_is():
    index = Here.cell
    placed = Board.entries[index].value.with_parent(State.cells["c1"])
    segs, _ = path(placed)
    assert segs[:2] == ("cells", "c1")
    assert segs[3] is index
    assert nu.shape.root_shape(segs[3]) is Here


def test_a_placed_chain_cannot_be_placed_again():
    placed = Counter.value.with_parent(State.cells["c1"])
    with pytest.raises(ValueError, match="already has a parent"):
        placed.with_parent(State.cells["c2"])


def test_the_parent_must_be_a_shape_ref():
    with pytest.raises(TypeError, match="shape ref"):
        Counter.value.with_parent("cells")  # type: ignore[arg-type]


def test_a_placed_chain_can_be_a_parent():
    inner = Board.entries.with_parent(State.cells["c1"])
    placed = Counter.value.with_parent(inner["x"])
    assert path(placed)[0] == ("cells", "c1", "entries", "x", "value")


def test_the_name_is_reserved_for_slots():
    with pytest.raises(TypeError, match="with_parent"):

        class Clash(Shape):
            with_parent = nu.IntRef.slot()


# --- runs on the mem fabric -------------------------------------------------


def test_a_placed_leaf_writes_and_reads_typed_in_the_parents_store():
    store: dict = {}
    other: dict = {}
    ctx = nu.Context().bind(dict, store, State).bind(dict, other, Other)
    value = Counter.value.with_parent(State.cells["c1"])

    nu.run(value.set(41) >> value.set(value + 1), ctx)
    assert store == {"cells": {"c1": {"value": 42}}}
    assert other == {}
    assert nu.run(value * 2, ctx)[0] == 84


def test_a_deep_chain_with_a_ref_index_resolves_through_its_own_root():
    store: dict = {}
    ctx = nu.Context().bind(dict, store, State).bind(dict, {"cell": "x"}, Here)
    entry = Board.entries[Here.cell].value.with_parent(State.cells["c1"])

    nu.run(entry.set(5), ctx)
    assert store == {"cells": {"c1": {"entries": {"x": {"value": 5}}}}}


def test_a_placed_read_of_nothing_is_null():
    from nu.lang import is_null

    ctx = nu.Context().bind(dict, {}, State)
    value = Counter.value.with_parent(State.cells["nope"])
    assert is_null(nu.run(value, ctx)[0])
    assert nu.run(nu.Int(value).fallback(0), ctx)[0] == 0
