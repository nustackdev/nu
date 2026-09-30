"""End-to-end: build a tree, compile, validate, and run it against a Context.

The proof that the core, the Context fabric and a mem fabric run together - a
program that reads a binder's item (Attr), writes state (``.set()`` through a mem
ref), streams (Iter / Map / Filter), and folds (Sum / Collect), driven through the
real ``run`` entry (compile -> validate -> drive) and checked for value and
mutation.
"""

from __future__ import annotations

import nu.mem
from nu.context import Attr
from nu.core import (
    Add,
    Collect,
    Filter,
    Iter,
    Lt,
    Map,
    Mul,
    Sum,
)
from nu.domains.shape import Shape
from nu.lang import Context, Literal
from nu.lang.helpers import arun, run


class State(Shape):
    total = nu.mem.IntRef.slot()


def test_read_compute_write():
    # Read a slot, compute on it, write the result back through the ref.
    data = {"total": 40}
    run(State.total.set(Add(State.total, Literal(2))), Context().bind(dict, data, State))
    assert data["total"] == 42


def test_map_then_reduce():
    tree = Sum(Map(Iter(Literal([1, 2, 3])), Mul(Attr("item"), Literal(10))))
    value, _ = run(tree)
    assert value == 60


def test_iter_into_a_reduction():
    value, _ = run(Sum(Iter(Literal(range(5)))))
    assert value == 10


def test_filtered_mapped_stream_collected():
    tree = Collect(
        Filter(
            Map(Iter(Literal([1, 2, 3, 4])), Mul(Attr("item"), Literal(10))),
            Lt(Attr("item"), Literal(35)),
        )
    )
    value, _ = run(tree)
    assert value == [10, 20, 30]


# --- async path (the acompile twins) -------------------------------------


async def test_async_map_then_reduce():
    value, _ = await arun(Sum(Map(Iter(Literal([1, 2, 3])), Mul(Attr("item"), Literal(10)))))
    assert value == 60


async def test_async_write_through_ref():
    data = {"total": 1}
    await arun(State.total.set(Add(State.total, Literal(9))), Context().bind(dict, data, State))
    assert data["total"] == 10
