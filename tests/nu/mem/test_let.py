"""``nu.mem.let``: a one-slot anonymous frame for a single disposable value.

What the ref hands the body, that every run and every nested ``let`` gets its
own slot, that the body may be a stream, and that the anonymous Shape belongs
to the lambda's code: two builds of one program are equal trees, nested lets
never share a Shape, and a tree holding a ``let`` survives the wire to a
worker process.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
import nu.mem as nm
from nu.lang import wire


if TYPE_CHECKING:
    from collections.abc import Callable


class Out(nu.Shape):
    """A dict the test binds itself, to see what ran inside the lets."""

    first = nm.IntRef.slot()
    second = nm.IntRef.slot()


def _sync(term: nu.Nu, ctx: nu.Context | None = None) -> object:
    return nu.run(term, ctx)[0]


def _async(term: nu.Nu, ctx: nu.Context | None = None) -> object:
    return asyncio.run(nu.arun(term, ctx))[0]


RUNNERS = pytest.mark.parametrize("run", [_sync, _async], ids=["sync", "async"])


def _out() -> tuple[dict, nu.Context]:
    data: dict = {}
    return data, nu.Context().bind(dict, data, Out)


# --- the ref -------------------------------------------------------------------


def test_fn_gets_an_object_ref_whatever_the_value() -> None:
    seen: list[object] = []
    nm.let(1, lambda n: seen.append(n) or n)
    nm.let("a", lambda s: seen.append(s) or s)
    assert [type(r) for r in seen] == [nm.ObjectRef, nm.ObjectRef]


@RUNNERS
def test_the_body_reads_the_value(run: Callable) -> None:
    assert run(nm.let(41, lambda n: nu.Add(n, 1))) == 42


@RUNNERS
def test_an_initial_term_is_evaluated_on_entry(run: Callable) -> None:
    assert run(nm.let(nu.Add(20, 1), lambda n: nu.Add(n, n))) == 42


@RUNNERS
def test_the_body_sets_the_ref(run: Callable) -> None:
    data, ctx = _out()

    def total(n: nm.ObjectRef) -> nu.Nu:
        add = nu.ForEachDo(nu.Iter([1, 2, 3]), n.set(n + nu.context.Attr("item")))
        return add >> Out.first.set(n)

    run(nm.let(0, total), ctx)
    assert data["first"] == 6


# --- isolation -----------------------------------------------------------------


@RUNNERS
def test_parallel_arms_get_their_own_slot(run: Callable) -> None:
    data, ctx = _out()
    arms = nu.Parallel(
        nm.let(0, lambda n: n.set(n + 1) >> Out.first.set(n)),
        nm.let(10, lambda n: n.set(n + 1) >> Out.second.set(n)),
    )
    run(arms, ctx)
    assert (data["first"], data["second"]) == (1, 11)


@RUNNERS
def test_a_nested_let_keeps_the_outer_ref_readable(run: Callable) -> None:
    term = nm.let(40, lambda a: nm.let(2, lambda b: nu.Add(a, b)))
    assert run(term) == 42


@RUNNERS
def test_sibling_lets_inside_one_let_shadow_and_restore(run: Callable) -> None:
    data, ctx = _out()
    term = nm.let(
        1,
        lambda a: (
            nm.let(10, lambda b: b.set(b + a) >> Out.first.set(b))
            >> nm.let(20, lambda c: Out.second.set(c + a))
        ),
    )
    run(term, ctx)
    assert (data["first"], data["second"]) == (11, 21)


@RUNNERS
def test_every_run_gets_its_own_slot(run: Callable) -> None:
    data, ctx = _out()
    term = nm.let(0, lambda n: n.set(n + 1) >> Out.first.set(n))
    run(term, ctx)
    run(term, ctx)
    assert data["first"] == 1


# --- stream body ---------------------------------------------------------------


@RUNNERS
def test_a_stream_body_reads_the_slot_across_its_drain(run: Callable) -> None:
    term = nm.let(10, lambda n: nu.Map(nu.Iter([1, 2]), n + nu.context.Attr("item")))
    assert run(nu.Collect(term)) == [11, 12]


# --- construction --------------------------------------------------------------


def _program() -> nu.Nu:
    return nm.let(1, lambda a: nm.let(a, lambda b: nu.Add(a, b)) >> nm.let(2, lambda c: c))


def test_two_builds_are_equal_trees() -> None:
    assert nu.tree.equal(_program(), _program())


def _shape(term: nu.Nu) -> type:
    return nu.tree.payload(term)["shape"]


def test_nested_lets_never_share_a_shape() -> None:
    outer = nm.let(1, lambda a: nm.let(2, lambda b: b))
    inner = nu.tree.children(outer)[0]
    assert _shape(inner) is not _shape(outer)


def test_one_function_binds_one_shape() -> None:
    def body(n: nm.ObjectRef) -> nu.Nu:
        return n

    assert _shape(nm.let(1, body)) is _shape(nm.let(2, body))


def test_let_refuses_a_callable_without_code() -> None:
    class Builder:
        def __call__(self, n: nm.ObjectRef) -> nu.Nu:
            return n

    with pytest.raises(TypeError, match="function"):
        nm.let(1, Builder())


def test_a_tree_holding_a_let_survives_the_wire() -> None:
    term = nm.let(41, lambda n: nu.Add(n, 1))
    assert nu.run(wire.loads(wire.dumps(term)))[0] == 42
