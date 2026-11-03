"""Functional tests for OrderedDictRef holding shapes.

Mirrors :mod:`test_ordered` for shape-valued ordered maps: descent to
sub-fields via ``ref[id].field``, placement with a row value, moves keeping
the row intact, async path, and the write atoms counting as writes for
``auto_flow_atomic``.
"""

from __future__ import annotations

import pytest

from nu import Shape, arun, run
from nustd.kv import IntRef, OrderedDictRef, StrRef, Transaction, auto_flow_atomic


class Cell(Shape):
    """Row shape stored at each id."""

    kind = StrRef.slot()
    size = IntRef.slot()


class Plane(Shape):
    """Owner shape holding an ordered map of Cells."""

    name = StrRef.slot()
    cells = OrderedDictRef.slot(Cell)


def _row(kind: str, size: int) -> dict:
    return {"kind": kind, "size": size}


# ============================================================================
# ROUNDTRIP + FIELD DESCENT
# ============================================================================


def test_store_and_field_descent(ctx) -> None:
    run(Plane.cells.set({"a": _row("text", 1), "b": _row("code", 2)}), ctx)
    assert run(Plane.cells["a"].kind, ctx)[0] == "text"
    assert run(Plane.cells["b"].size, ctx)[0] == 2


def test_insert_row_then_descend(ctx) -> None:
    run(Plane.cells.set({"a": _row("text", 1), "c": _row("code", 3)}), ctx)
    run(Plane.cells.insert_before("c", "b", _row("image", 2)), ctx)
    assert list(run(Plane.cells.keys(), ctx)[0]) == ["a", "b", "c"]
    assert run(Plane.cells["b"].kind, ctx)[0] == "image"
    assert run(Plane.cells["b"].size, ctx)[0] == 2


def test_field_write_keeps_place(ctx) -> None:
    run(Plane.cells.set({"a": _row("text", 1), "b": _row("code", 2)}), ctx)
    run(Plane.cells["a"].kind.set("mutated"), ctx)
    assert list(run(Plane.cells.keys(), ctx)[0]) == ["a", "b"]
    assert run(Plane.cells["a"].kind, ctx)[0] == "mutated"


# ============================================================================
# MOVE KEEPS THE ROW
# ============================================================================


def test_move_keeps_fields(ctx) -> None:
    run(Plane.cells.set({"a": _row("text", 1), "b": _row("code", 2), "c": _row("img", 3)}), ctx)
    run(Plane.cells.move("c", before="a"), ctx)
    assert list(run(Plane.cells.keys(), ctx)[0]) == ["c", "a", "b"]
    assert run(Plane.cells["c"].kind, ctx)[0] == "img"
    assert run(Plane.cells["c"].size, ctx)[0] == 3
    assert run(Plane.cells.first(), ctx)[0] == "c"


def test_items_yield_rows_in_order(ctx) -> None:
    run(Plane.cells.set({"z": _row("text", 26), "a": _row("code", 1)}), ctx)
    got = list(run(Plane.cells.eager.items(), ctx)[0])
    assert [k for k, _ in got] == ["z", "a"]
    assert [row["size"] for _, row in got] == [26, 1]


# ============================================================================
# ASYNC PATH
# ============================================================================


@pytest.mark.asyncio
async def test_async_insert_move_first_last(ctx) -> None:
    run(Plane.cells.set({"a": _row("text", 1)}), ctx)
    await arun(Plane.cells.insert_after("a", "b", _row("code", 2)), ctx)
    await arun(Plane.cells.insert_before("a", "z", _row("img", 0)), ctx)
    assert list((await arun(Plane.cells.keys(), ctx))[0]) == ["z", "a", "b"]
    await arun(Plane.cells.move("z", after="b"), ctx)
    assert (await arun(Plane.cells.first(), ctx))[0] == "a"
    assert (await arun(Plane.cells.last(), ctx))[0] == "z"
    assert (await arun(Plane.cells["z"].kind, ctx))[0] == "img"


# ============================================================================
# AUTO FLOW ATOMIC
# ============================================================================


@pytest.mark.parametrize(
    "cmd",
    [
        Plane.cells.insert_before("a", "b"),
        Plane.cells.insert_after("a", "b"),
        Plane.cells.move("b", before="a"),
    ],
    ids=["insert_before", "insert_after", "move"],
)
def test_write_atoms_get_a_transaction(cmd) -> None:
    out = auto_flow_atomic(cmd)
    assert isinstance(out, Transaction)
