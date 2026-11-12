"""List as the keyed, ordered collection: the child ops and the frames they ship.

The browser keeps the order; each op is one frame on the list that names
keys and places, so nothing here needs to know which children are there.
Runs against a recording session, same harness as test_line.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd.ui import CardRef, ListRef, Session, TextRef


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _frames(term):
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _one(term):
    (frame,) = _frames(term)
    return frame.op, frame.ref, frame.payload


LST = ListRef("l")


@pytest.mark.parametrize(
    ("term", "payload"),
    [
        (LST.insert("a"), {"key": "a"}),
        (LST.insert(3, at=0), {"key": "3", "at": 0}),
        (LST.insert("a", before=2), {"key": "a", "before": "2"}),
        (LST.insert("a", after="b"), {"key": "a", "after": "b"}),
    ],
)
def test_insert_ships_key_and_place(term, payload):
    assert _one(term) == ("insert_item", ("l",), payload)


def test_insert_a_typed_child_places_then_brings_it_on_screen():
    insert, init = _frames(LST.insert(LST["c"].to(CardRef), at=1))
    assert (insert.op, insert.ref, insert.payload) == ("insert_item", ("l",), {"key": "c", "at": 1})
    assert init.op == "init"
    assert [(s, t) for s, t, _ in init.chain] == [("l", "List"), ("c", "Card")]


def test_insert_a_child_from_the_item_default():
    lst = ListRef("l", item=TextRef)
    frames = _frames(lst.insert(lst[0]))
    assert [f.op for f in frames] == ["insert_item", "init"]
    assert frames[1].chain[-1][:2] == ("0", "TextRef")


def test_insert_a_bare_child_only_places():
    assert _one(LST.insert(LST["k"])) == ("insert_item", ("l",), {"key": "k"})


def test_insert_refuses_a_child_of_another_list():
    with pytest.raises(ValueError, match="child of its own"):
        LST.insert(ListRef("m")["a"].to(TextRef))


def test_move_remove_truncate_keep_order():
    assert _one(LST.move("a", at=2)) == ("move_item", ("l",), {"key": "a", "at": 2})
    assert _one(LST.move(0, after="z")) == ("move_item", ("l",), {"key": "0", "after": "z"})
    assert _one(LST.remove(1)) == ("remove_item", ("l",), {"key": "1"})
    assert _one(LST.truncate(3)) == ("truncate_items", ("l",), {"count": 3})
    assert _one(LST.keep(["a", 1])) == ("keep_items", ("l",), {"keys": ["a", "1"]})
    assert _one(LST.set_order([2, "x"])) == ("order_items", ("l",), {"keys": ["2", "x"]})


def test_computed_keys_ship_as_text():
    assert _one(LST.remove(nu.Int(4))) == ("remove_item", ("l",), {"key": "4"})
    assert _one(LST.insert(nu.Str("k"), at=nu.Int(1))) == (
        "insert_item",
        ("l",),
        {"key": "k", "at": 1},
    )


@pytest.mark.parametrize(
    ("build", "error"),
    [
        (lambda: LST.insert("0"), ValueError),
        (lambda: LST.insert(None), TypeError),
        (lambda: LST.insert(True), TypeError),
        (lambda: LST.insert(""), ValueError),
        (lambda: LST.insert("a", at=1, before="b"), TypeError),
        (lambda: LST.move("a", at=-1), IndexError),
        (lambda: LST.move("a", at=True), TypeError),
        (lambda: LST.move("a", before="0"), ValueError),
        (lambda: LST.remove(-1), IndexError),
        (lambda: LST.truncate(-1), ValueError),
        (lambda: LST.keep("ab"), TypeError),
        (lambda: LST.keep([None]), TypeError),
    ],
)
def test_bad_keys_and_places_fail_where_written(build, error):
    with pytest.raises(error):
        build()


def test_ops_work_on_a_list_reached_through_a_shape():
    from nustd.ui import Column, List

    class Page(Column):
        links = List.slot()

    frame = _frames(Page.links.insert(Page.links["a"].to(TextRef)))[0]
    assert (frame.op, frame.ref, frame.payload) == ("insert_item", ("links",), {"key": "a"})


def test_a_list_shape_cannot_name_a_slot_after_an_op():
    from nustd.ui import List

    with pytest.raises((TypeError, ValueError)):

        class Bad(List):
            keep = TextRef.slot()
