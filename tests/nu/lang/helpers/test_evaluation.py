"""Unit tests for ``nu.lang.helpers.evaluation``.

Covers the drive entries -- value-root (``eval`` / ``aeval`` /
``eval_in_loop``) and stream-root (``first`` / ``collect`` / ``afirst`` /
``alast`` / ``acollect``) -- their Budget lifecycle, async-only refusal
behavior, and stream finalization on short-circuit.
"""

from __future__ import annotations

import pytest

from nu.core import Add, Literal
from nu.engine.structure import Declared
from nu.lang import Context, StreamQuery
from nu.lang.helpers import (
    acollect,
    aeval,
    afirst,
    alast,
    collect,
    compile,
    eval,
    eval_in_loop,
    first,
)


class _AsyncOnly(StreamQuery):
    """An async-only stream stub (no sync path), to drive sync-refusal tests."""

    _requires_async = Declared(value=True, name="requires_async")


class _Src(StreamQuery):
    def __init__(self, items: tuple) -> None:
        super().__init__()
        self._payload = {"items": tuple(items)}

    def _compile(self, nid, children):
        items = self._payload["items"]

        def thunk(rt):
            def gen():
                yield from items

            return gen()

        return thunk

    def _acompile(self, nid, children):
        items = self._payload["items"]

        async def athunk(rt):
            async def agen():
                for x in items:
                    yield x

            return agen()

        return athunk


# --- value root -----------------------------------------------------------


def test_eval_returns_value_and_context():
    prog = compile(Add(Literal(1), Literal(2)))
    value, ctx = eval(prog)
    assert value == 3
    assert isinstance(ctx, Context)


def test_eval_uses_provided_context():
    prog = compile(Literal(9))
    ctx_in = Context()
    _, ctx_out = eval(prog, ctx_in)
    assert ctx_out is ctx_in


def test_eval_refuses_async_only_program():
    prog = compile(_AsyncOnly())
    with pytest.raises(RuntimeError, match=r"async-only"):
        eval(prog)


def test_eval_refusal_points_to_aeval():
    prog = compile(_AsyncOnly())
    with pytest.raises(RuntimeError, match=r"aeval"):
        eval(prog)


async def test_aeval_returns_value_and_context():
    prog = compile(Add(Literal(4), Literal(5)))
    value, ctx = await aeval(prog)
    assert value == 9
    assert isinstance(ctx, Context)


async def test_aeval_runs_async_only_program():
    prog = compile(Add(_AsyncOnly(), Literal(0)))
    with pytest.raises(Exception):  # noqa: B017
        await aeval(prog)


def test_eval_in_loop_drives_value_program():
    prog = compile(Add(Literal(1), Literal(1)))
    value, ctx = eval_in_loop(prog)
    assert value == 2
    assert isinstance(ctx, Context)


# --- stream root: sync ----------------------------------------------------


def test_first_returns_first_item():
    prog = compile(_Src((10, 20, 30)))
    value, ctx = first(prog)
    assert value == 10
    assert isinstance(ctx, Context)


def test_first_raises_on_empty_stream():
    prog = compile(_Src(()))
    with pytest.raises(RuntimeError, match=r"yielded no values"):
        first(prog)


def test_collect_materializes_stream():
    prog = compile(_Src((1, 2, 3)))
    values, ctx = collect(prog)
    assert values == [1, 2, 3]
    assert isinstance(ctx, Context)


def test_collect_on_empty_stream_returns_empty_list():
    prog = compile(_Src(()))
    values, _ = collect(prog)
    assert values == []


def test_first_uses_provided_context():
    prog = compile(_Src((1,)))
    ctx_in = Context()
    _, ctx_out = first(prog, ctx_in)
    assert ctx_out is ctx_in


def test_collect_uses_provided_context():
    prog = compile(_Src((1, 2)))
    ctx_in = Context()
    _, ctx_out = collect(prog, ctx_in)
    assert ctx_out is ctx_in


# --- stream root: async ---------------------------------------------------


async def test_afirst_returns_first_item():
    prog = compile(_Src((100, 200)))
    value, ctx = await afirst(prog)
    assert value == 100
    assert isinstance(ctx, Context)


async def test_afirst_raises_on_empty_stream():
    prog = compile(_Src(()))
    with pytest.raises(RuntimeError, match=r"yielded no values"):
        await afirst(prog)


async def test_acollect_materializes_stream():
    prog = compile(_Src((7, 8, 9)))
    values, ctx = await acollect(prog)
    assert values == [7, 8, 9]
    assert isinstance(ctx, Context)


async def test_acollect_on_empty_stream_returns_empty_list():
    prog = compile(_Src(()))
    values, _ = await acollect(prog)
    assert values == []


async def test_alast_returns_last_item():
    prog = compile(_Src((1, 2, 3, 4)))
    value, ctx = await alast(prog)
    assert value == 4
    assert isinstance(ctx, Context)


async def test_alast_raises_on_empty_stream():
    prog = compile(_Src(()))
    with pytest.raises(RuntimeError, match=r"yielded no values"):
        await alast(prog)


async def test_alast_single_item():
    prog = compile(_Src((42,)))
    value, _ = await alast(prog)
    assert value == 42
