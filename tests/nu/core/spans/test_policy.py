"""Tests for the Policy span: TryCatch (full v1 parity).

TryCatch is a transparent Span: it forwards the body's yield (scalar / stream /
nothing) and, on a matching failure, runs a fallback in the body's place. The
suite pins the basis, the success/caught/propagated paths across void, scalar,
and stream bodies, the typed ``errors`` filter, the two context disciplines
(catch is isolated against a ctx copy carrying ``error``; ``finally_`` persists
against the live ctx), and the async surface. Failures come from the raising
``BoomAction`` support atom and a local failing-stream atom.
"""

from __future__ import annotations

import pytest
from _support.async_atoms import BoomAction

from nu.context import AttrRef, SetCmd
from nu.core.iteration import Iter
from nu.core.spans import TryCatch
from nu.lang import Attr, Cardinality, Literal, Policy, Span, StreamQuery
from nu.lang.helpers import arun, collect, compile, run


def _set(name: str, value: object) -> SetCmd:
    return SetCmd(AttrRef(name), Literal(value))


class _BoomStream(StreamQuery):
    """Yields ``0..n-1`` then raises ``ValueError(name)`` mid-stream."""

    def __init__(self, n: int, name: str) -> None:
        super().__init__()
        self._payload["n"] = n
        self._payload["name"] = name

    def _compile(self, nid, children):
        n = self._payload["n"]
        name = self._payload["name"]

        def thunk(rt):
            def gen():
                yield from range(n)
                raise ValueError(name)

            return gen()

        return thunk


# --- basis ----------------------------------------------------------------


def test_trycatch_is_a_policy_span() -> None:
    assert issubclass(TryCatch, Policy)
    assert issubclass(TryCatch, Span)


def test_trycatch_is_transparent_and_forwards_body_cardinality() -> None:
    program = compile(TryCatch(Literal(5)))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.TRANSPARENT
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR

    stream = compile(TryCatch(Iter(Literal([1, 2]))))
    assert stream.attr(stream.root, Attr.CHILD_CARDINALITY) is Cardinality.STREAM


# --- scalar body ----------------------------------------------------------


def test_scalar_success_forwards_the_body_value() -> None:
    value, _ = run(TryCatch(Literal(5)))
    assert value == 5


def test_scalar_failure_runs_the_catch_in_place() -> None:
    value, _ = run(TryCatch(BoomAction("boom"), Literal(9)))
    assert value == 9


def test_catch_can_read_the_error_from_its_isolated_context() -> None:
    # The catch runs against a copy carrying ``error``; reading it yields the
    # exception string, which forwards as the result.
    value, _ = run(TryCatch(BoomAction("boom"), AttrRef("error")))
    assert value == "boom"


def test_catch_context_is_isolated_so_error_does_not_leak_to_the_parent() -> None:
    # ``error`` lives on the catch's copy, not the live context.
    _, ctx = run(TryCatch(BoomAction("boom"), Literal(9)))
    assert "error" not in ctx.attrs


def test_error_key_is_customizable() -> None:
    # The handler reads the error back at the key it was written under.
    value, _ = run(TryCatch(BoomAction("boom"), AttrRef("err2"), error_key="err2"))
    assert value == "boom"


def test_failure_without_a_catch_propagates() -> None:
    with pytest.raises(ValueError, match="boom"):
        run(TryCatch(BoomAction("boom")))


# --- typed errors filter --------------------------------------------------


def test_error_outside_the_filter_propagates_unretried() -> None:
    with pytest.raises(ValueError, match="boom"):
        run(TryCatch(BoomAction("boom"), Literal(9), errors=KeyError))


def test_error_inside_the_filter_is_caught() -> None:
    value, _ = run(TryCatch(BoomAction("boom"), Literal(9), errors=ValueError))
    assert value == 9


# --- finally_ -------------------------------------------------------------


def test_finally_runs_on_success_and_persists() -> None:
    value, ctx = run(TryCatch(Literal(5), finally_=_set("done", True)))
    assert value == 5
    assert ctx.attrs["done"] is True


def test_finally_runs_after_a_caught_failure() -> None:
    value, ctx = run(TryCatch(BoomAction("boom"), Literal(9), _set("done", True)))
    assert value == 9
    assert ctx.attrs["done"] is True


def test_finally_runs_even_when_the_failure_propagates() -> None:
    from nu.lang.runtime.context.context import Context

    ctx = Context()
    tree = TryCatch(BoomAction("boom"), finally_=_set("done", True))
    with pytest.raises(ValueError, match="boom"):
        run(tree, ctx)
    # finally ran against the live ctx before the error propagated.
    assert ctx.attrs["done"] is True


# --- void body ------------------------------------------------------------


def test_void_success_forwards_nothing_and_the_body_effect_lands() -> None:
    value, ctx = run(TryCatch(_set("a", 1)))
    assert value is None
    assert ctx.attrs["a"] == 1


# --- stream body ----------------------------------------------------------


def test_stream_success_forwards_the_whole_stream() -> None:
    items, _ = collect(compile(TryCatch(Iter(Literal([1, 2, 3])))))
    assert items == [1, 2, 3]


def test_stream_failure_mid_drain_appends_the_catch_stream() -> None:
    # The body emits its prefix, then fails; the fallback stream follows it.
    tree = TryCatch(_BoomStream(2, "mid"), Iter(Literal([9])))
    items, _ = collect(compile(tree))
    assert items == [0, 1, 9]


def test_stream_finally_runs_after_the_stream_drains() -> None:
    tree = TryCatch(Iter(Literal([1, 2])), finally_=_set("done", True))
    items, ctx = collect(compile(tree))
    assert items == [1, 2]
    assert ctx.attrs["done"] is True


# --- async surface --------------------------------------------------------


async def test_async_scalar_failure_runs_the_catch() -> None:
    value, _ = await arun(TryCatch(BoomAction("boom"), Literal(9)))
    assert value == 9


async def test_async_catch_reads_the_error_and_finally_persists() -> None:
    value, ctx = await arun(
        TryCatch(BoomAction("boom"), AttrRef("error"), _set("done", True)),
    )
    assert value == "boom"
    assert ctx.attrs["done"] is True


async def test_async_failure_without_a_catch_propagates() -> None:
    with pytest.raises(ValueError, match="boom"):
        await arun(TryCatch(BoomAction("boom")))
