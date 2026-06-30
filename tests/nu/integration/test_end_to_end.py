"""End-to-end: build a tree, compile, validate, and run it against a Context.

The proof that the core + the Context fabric run together - a program that
reads (AttrRef), writes (SetCommand through the ref), streams (IterQuery / MapQuery / FilterQuery),
and folds (SumQuery / CollectQuery), driven through the real ``run`` entry
(compile -> validate -> drive) and checked for value and mutation.
"""

from __future__ import annotations

from nu.context import AttrRef, SetCommand
from nu.core import (
    AddQuery,
    CollectQuery,
    FilterQuery,
    IterQuery,
    LiteralQuery,
    LtQuery,
    MapQuery,
    MulQuery,
    SumQuery,
)
from nu.lang import Context
from nu.lang.helpers import arun, run


def test_read_compute_write():
    # Read an attr, compute on it, write the result back through the ref.
    ctx = Context()
    ctx.attrs["total"] = 40
    _, ctx = run(SetCommand(AttrRef("total"), AddQuery(AttrRef("total"), LiteralQuery(2))), ctx)
    assert ctx.attrs["total"] == 42


def test_map_then_reduce():
    tree = SumQuery(
        MapQuery(IterQuery(LiteralQuery([1, 2, 3])), MulQuery(AttrRef("item"), LiteralQuery(10)))
    )
    value, _ = run(tree)
    assert value == 60


def test_iter_into_a_reduction():
    value, _ = run(SumQuery(IterQuery(LiteralQuery(range(5)))))
    assert value == 10


def test_filtered_mapped_stream_collected():
    tree = CollectQuery(
        FilterQuery(
            MapQuery(
                IterQuery(LiteralQuery([1, 2, 3, 4])), MulQuery(AttrRef("item"), LiteralQuery(10))
            ),
            LtQuery(AttrRef("item"), LiteralQuery(35)),
        )
    )
    value, _ = run(tree)
    assert value == [10, 20, 30]


# --- async path (the acompile twins) -------------------------------------


async def test_async_map_then_reduce():
    value, _ = await arun(
        SumQuery(
            MapQuery(
                IterQuery(LiteralQuery([1, 2, 3])), MulQuery(AttrRef("item"), LiteralQuery(10))
            )
        )
    )
    assert value == 60


async def test_async_write_through_ref():
    ctx = Context()
    ctx.attrs["n"] = 1
    _, ctx = await arun(SetCommand(AttrRef("n"), AddQuery(AttrRef("n"), LiteralQuery(9))), ctx)
    assert ctx.attrs["n"] == 10
