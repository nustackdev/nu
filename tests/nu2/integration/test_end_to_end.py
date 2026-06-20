"""End-to-end: build a tree, compile, validate, and run it against a Context.

The proof that the core + the Context fabric run together - a program that
reads (AttrRef), writes (Set through the ref), streams (Iter / Map / Filter),
and folds (Sum / Collect), driven through the real ``run`` entry
(compile -> validate -> drive) and checked for value and mutation.
"""

from __future__ import annotations

from nu2.context import AttrRef, Set
from nu2.core import Add, Collect, Filter, Iter, Literal, Lt, Map, Mul, Sum
from nu2.lang import Context
from nu2.lang.helpers import arun, run


def test_read_compute_write():
    # Read an attr, compute on it, write the result back through the ref.
    ctx = Context()
    ctx.attrs["total"] = 40
    _, ctx = run(Set(AttrRef("total"), Add(AttrRef("total"), Literal(2))), ctx)
    assert ctx.attrs["total"] == 42


def test_map_then_reduce():
    tree = Sum(Map(Iter(Literal([1, 2, 3])), Mul(AttrRef("item"), Literal(10))))
    value, _ = run(tree)
    assert value == 60


def test_iter_into_a_reduction():
    value, _ = run(Sum(Iter(Literal(range(5)))))
    assert value == 10


def test_filtered_mapped_stream_collected():
    tree = Collect(
        Filter(
            Map(Iter(Literal([1, 2, 3, 4])), Mul(AttrRef("item"), Literal(10))),
            Lt(AttrRef("item"), Literal(35)),
        )
    )
    value, _ = run(tree)
    assert value == [10, 20, 30]


# --- async path (the acompile twins) -------------------------------------


async def test_async_map_then_reduce():
    value, _ = await arun(Sum(Map(Iter(Literal([1, 2, 3])), Mul(AttrRef("item"), Literal(10)))))
    assert value == 60


async def test_async_write_through_ref():
    ctx = Context()
    ctx.attrs["n"] = 1
    _, ctx = await arun(Set(AttrRef("n"), Add(AttrRef("n"), Literal(9))), ctx)
    assert ctx.attrs["n"] == 10
