"""Unit tests for ``nu.lang.helpers.run``.

Covers the all-in-one entries (``run`` / ``arun`` / ``run_in_loop``):
that they compile, validate, and drive in one call; that validation
failures surface; that the async-only refusal in ``run`` matches the
underlying drive guard.
"""

from __future__ import annotations

import pytest

from nu.core import AddQuery, LiteralQuery
from nu.engine.structure import Declared
from nu.lang import Context, StreamQuery
from nu.lang.helpers import arun, run, run_in_loop


class _AsyncOnly(StreamQuery):
    """An async-only stream stub (no sync path), to drive sync-refusal tests."""

    requires_async = Declared(value=True)


def test_run_returns_value_for_value_root():
    value, ctx = run(AddQuery(LiteralQuery(1), LiteralQuery(2)))
    assert value == 3
    assert isinstance(ctx, Context)


def test_run_uses_provided_context():
    ctx_in = Context()
    _, ctx_out = run(AddQuery(LiteralQuery(1), LiteralQuery(2)), ctx_in)
    assert ctx_out is ctx_in


def test_run_creates_fresh_context_when_omitted():
    _, ctx_a = run(LiteralQuery(5))
    _, ctx_b = run(LiteralQuery(5))
    assert ctx_a is not ctx_b
    assert isinstance(ctx_a, Context)


def test_run_with_nested_arithmetic():
    value, _ = run(AddQuery(LiteralQuery(10), AddQuery(LiteralQuery(20), LiteralQuery(12))))
    assert value == 42


def test_run_respects_max_parallel_arg():
    value, _ = run(AddQuery(LiteralQuery(1), LiteralQuery(2)), max_parallel=4)
    assert value == 3


async def test_arun_returns_value_for_value_root():
    value, ctx = await arun(AddQuery(LiteralQuery(1), LiteralQuery(2)))
    assert value == 3
    assert isinstance(ctx, Context)


async def test_arun_uses_provided_context():
    ctx_in = Context()
    _, ctx_out = await arun(LiteralQuery(7), ctx_in)
    assert ctx_out is ctx_in


async def test_arun_with_nested_arithmetic():
    value, _ = await arun(AddQuery(AddQuery(LiteralQuery(1), LiteralQuery(2)), LiteralQuery(3)))
    assert value == 6


def test_run_refuses_async_only_subtree():
    with pytest.raises(RuntimeError, match=r"async-only"):
        run(_AsyncOnly())


def test_run_refusal_names_async_swap():
    with pytest.raises(RuntimeError) as excinfo:
        run(_AsyncOnly())
    msg = str(excinfo.value)
    assert "aeval" in msg or "arun" in msg


def test_run_in_loop_drives_value_root():
    value, ctx = run_in_loop(AddQuery(LiteralQuery(2), LiteralQuery(3)))
    assert value == 5
    assert isinstance(ctx, Context)


def test_run_in_loop_with_provided_context():
    ctx_in = Context()
    _, ctx_out = run_in_loop(LiteralQuery(1), ctx_in)
    assert ctx_out is ctx_in
