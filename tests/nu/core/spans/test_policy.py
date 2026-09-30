"""Tests for the Policy span: TryCatch (full v1 parity).

TryCatch is a transparent Span: it forwards the body's yield (scalar / stream /
nothing) and, on a matching failure, runs a fallback in the body's place. The
suite pins the basis, the success/caught/propagated paths across void, scalar,
and stream bodies, the typed ``errors`` filter, the two context disciplines
(catch runs with ``error`` let-bound for as long as it runs, a stream catch for
its whole drain; ``finally_`` persists against the live ctx), and the async
surface. Failures come from the raising
``BoomAction`` support atom and a local failing-stream atom.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from _support.async_atoms import BoomAction

import nu
from nu.context import Attr as AttrRef
from nu.core.iteration import Iter
from nu.core.spans import TryCatch
from nu.core.transform import Map
from nu.lang import Attr, Cardinality, Context, Literal, Policy, Span, StreamQuery
from nu.lang.helpers import arun, collect, compile, run


if TYPE_CHECKING:
    from nu.domains.shape.interactions import SetCmd


class S(nu.Shape):
    """The mem slots the bodies, catches and finallys below write."""

    a = nu.mem.ObjectRef.slot()
    done = nu.mem.ObjectRef.slot()
    seen = nu.mem.ObjectRef.slot()


def _set(name: str, value: object) -> SetCmd:
    return getattr(S, name).set(Literal(value))


def _mem() -> tuple[dict, Context]:
    """An empty mem dict for ``S``, and a Context with it bound."""
    data: dict = {}
    return data, Context().bind(dict, data, S)


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


def test_catch_can_read_the_error_bound_for_it() -> None:
    # The catch runs with ``error`` bound; reading it yields the exception
    # string, which forwards as the result.
    value, _ = run(TryCatch(BoomAction("boom"), AttrRef("error")))
    assert value == "boom"


def test_error_is_bound_only_while_the_catch_runs() -> None:
    # ``error`` is a let scoped to the catch; it is gone once the catch returns.
    _, ctx = run(TryCatch(BoomAction("boom"), Literal(9)))
    assert not ctx.attrs.exists("error")


def test_catch_writes_land_on_the_live_context() -> None:
    # No isolated copy: a catch writing a mem slot bound outside is seen after.
    catch = S.seen.set(AttrRef("error"))
    data, ctx = _mem()
    run(TryCatch(BoomAction("boom"), catch), ctx)
    assert data["seen"] == "boom"


def test_stream_catch_reads_the_error_for_its_whole_drain() -> None:
    # The fallback stream reads ``error`` per item, lazily, while it drains.
    tree = TryCatch(_BoomStream(1, "mid"), Map(Iter(Literal([1, 2])), AttrRef("error")))
    items, _ = collect(compile(tree))
    assert items == [0, "mid", "mid"]


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
    data, ctx = _mem()
    value, _ = run(TryCatch(Literal(5), finally_=_set("done", True)), ctx)
    assert value == 5
    assert data["done"] is True


def test_finally_runs_after_a_caught_failure() -> None:
    data, ctx = _mem()
    value, _ = run(TryCatch(BoomAction("boom"), Literal(9), _set("done", True)), ctx)
    assert value == 9
    assert data["done"] is True


def test_finally_runs_even_when_the_failure_propagates() -> None:
    data, ctx = _mem()
    tree = TryCatch(BoomAction("boom"), finally_=_set("done", True))
    with pytest.raises(ValueError, match="boom"):
        run(tree, ctx)
    # finally ran against the live ctx before the error propagated.
    assert data["done"] is True


# --- void body ------------------------------------------------------------


def test_void_success_forwards_nothing_and_the_body_effect_lands() -> None:
    data, ctx = _mem()
    value, _ = run(TryCatch(_set("a", 1)), ctx)
    assert value is None
    assert data["a"] == 1


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
    data, ctx = _mem()
    items, _ = collect(compile(tree), ctx)
    assert items == [1, 2]
    assert data["done"] is True


# --- async surface --------------------------------------------------------


async def test_async_scalar_failure_runs_the_catch() -> None:
    value, _ = await arun(TryCatch(BoomAction("boom"), Literal(9)))
    assert value == 9


async def test_async_catch_reads_the_error_and_finally_persists() -> None:
    data, ctx = _mem()
    value, _ = await arun(TryCatch(BoomAction("boom"), AttrRef("error"), _set("done", True)), ctx)
    assert value == "boom"
    assert data["done"] is True


async def test_async_failure_without_a_catch_propagates() -> None:
    with pytest.raises(ValueError, match="boom"):
        await arun(TryCatch(BoomAction("boom")))
