"""The ordering ops on Row, Column and a flowing Grid: the same frames List ships.

The ops live in one place (``collections.order``) and every ordered
container ships them the same way; a placed grid keeps no order and refuses
each one where it is written.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
import nustd.ui as ui
from nu import Context
from nustd.ui import Session


class _Recording:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _frames(term):
    sess = _Recording()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


ORDERED = [
    ui.RowRef("r"),
    ui.ColumnRef("c"),
    ui.GridRef("g"),
    ui.ListRef("l"),
]

OPS = [
    (lambda ref: ref.insert("a", at=0), "insert_item", {"key": "a", "at": 0}),
    (lambda ref: ref.move(2, before="a"), "move_item", {"key": "2", "before": "a"}),
    (lambda ref: ref.remove("a"), "remove_item", {"key": "a"}),
    (lambda ref: ref.truncate(3), "truncate_items", {"count": 3}),
    (lambda ref: ref.keep(["a", 1]), "keep_items", {"keys": ["a", "1"]}),
    (lambda ref: ref.set_order([1, "a"]), "order_items", {"keys": ["1", "a"]}),
]


@pytest.mark.parametrize("ref", ORDERED, ids=lambda r: type(r).__name__)
@pytest.mark.parametrize(("op", "wire", "payload"), OPS, ids=[o[1] for o in OPS])
def test_every_ordered_container_ships_the_same_op(ref, op, wire, payload):
    (frame,) = _frames(op(ref))
    assert (frame.op, frame.payload) == (wire, payload)


def test_insert_a_typed_child_of_a_row_places_then_inits_it():
    row = ui.RowRef("r")
    insert, init = _frames(row.insert(row["k"].to(ui.CardRef), after="a"))
    assert (insert.op, insert.payload) == ("insert_item", {"key": "k", "after": "a"})
    assert [(s, t) for s, t, _ in init.chain] == [("r", "Row"), ("k", "Card")]


def test_insert_refuses_a_child_of_another_container():
    with pytest.raises(ValueError, match="child of its own"):
        ui.RowRef("r").insert(ui.ColumnRef("c")["k"].to(ui.TextRef))


@pytest.mark.parametrize(("op", "wire", "payload"), OPS, ids=[o[1] for o in OPS])
def test_a_placed_grid_refuses_every_op(op, wire, payload):
    board = ui.GridRef("b", props={"cols": "2fr 1fr"})
    with pytest.raises(TypeError, match="placed grid"):
        op(board)


def test_keys_are_checked_like_descent():
    with pytest.raises(ValueError, match="reads as a number"):
        ui.RowRef("r").remove("0")
    with pytest.raises(TypeError, match="one of at, before, after"):
        ui.ColumnRef("c").move("a", at=0, after="b")
