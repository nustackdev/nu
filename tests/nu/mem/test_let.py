"""``nu.mem.let`` over a lambda: a frame over a Shape generated from it.

What the refs hand the body, that every run and every nested ``let`` gets its
own frame, that the body may be a stream, that the generated Shape belongs to
the lambda's code (two builds of one program are equal trees, nested lets
never share a Shape, a tree holding a ``let`` survives the wire to a worker
process), the values by name, and the arity rule every dynamic binding
shares. The Shape form lives in ``test_let_shape.py``.
"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest

import nu
import nu.mem as nm
from nu.lang import wire
from nu.lang.binding import _DynamicBinding


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


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
    nm.let(lambda n: seen.append(n) or n, n=1)
    nm.let(lambda s: seen.append(s) or s, s="a")
    assert [type(r) for r in seen] == [nm.ObjectRef, nm.ObjectRef]


@RUNNERS
def test_the_body_reads_the_value(run: Callable) -> None:
    assert run(nm.let(lambda n: nu.Add(n, 1), n=41)) == 42


@RUNNERS
def test_an_initial_term_is_evaluated_on_entry(run: Callable) -> None:
    assert run(nm.let(lambda n: nu.Add(n, n), n=nu.Add(20, 1))) == 42


@RUNNERS
def test_the_body_sets_the_ref(run: Callable) -> None:
    data, ctx = _out()

    def total(n: nm.ObjectRef) -> nu.Nu:
        add = nu.ForEachDo(nu.Iter([1, 2, 3]), lambda item: n.set(n + item))
        return add >> Out.first.set(n)

    run(nm.let(total, n=0), ctx)
    assert data["first"] == 6


# --- isolation -----------------------------------------------------------------


@RUNNERS
def test_parallel_arms_get_their_own_slot(run: Callable) -> None:
    data, ctx = _out()
    arms = nu.Parallel(
        nm.let(lambda n: n.set(n + 1) >> Out.first.set(n), n=0),
        nm.let(lambda n: n.set(n + 1) >> Out.second.set(n), n=10),
    )
    run(arms, ctx)
    assert (data["first"], data["second"]) == (1, 11)


@RUNNERS
def test_a_nested_let_keeps_the_outer_ref_readable(run: Callable) -> None:
    term = nm.let(lambda a: nm.let(lambda b: nu.Add(a, b), b=2), a=40)
    assert run(term) == 42


@RUNNERS
def test_sibling_lets_inside_one_let_shadow_only_inside(run: Callable) -> None:
    data, ctx = _out()
    term = nm.let(
        lambda a: (
            nm.let(lambda b: b.set(b + a) >> Out.first.set(b), b=10)
            >> nm.let(lambda c: Out.second.set(c + a), c=20)
        ),
        a=1,
    )
    run(term, ctx)
    assert (data["first"], data["second"]) == (11, 21)


@RUNNERS
def test_every_run_gets_its_own_slot(run: Callable) -> None:
    data, ctx = _out()
    term = nm.let(lambda n: n.set(n + 1) >> Out.first.set(n), n=0)
    run(term, ctx)
    run(term, ctx)
    assert data["first"] == 1


# --- stream body ---------------------------------------------------------------


@RUNNERS
def test_a_stream_body_reads_the_slot_across_its_drain(run: Callable) -> None:
    term = nm.let(lambda n: nu.Map(nu.Iter([1, 2]), lambda item: n + item), n=10)
    assert run(nu.Collect(term)) == [11, 12]


# --- construction --------------------------------------------------------------


def _program() -> nu.Nu:
    return nm.let(lambda a: nm.let(lambda b: nu.Add(a, b), b=a) >> nm.let(lambda c: c, c=2), a=1)


def test_two_builds_are_equal_trees() -> None:
    assert nu.tree.equal(_program(), _program())


def _shape(term: nu.Nu) -> type:
    return term._bind_shape  # type: ignore[attr-defined]


def test_nested_lets_never_share_a_shape() -> None:
    outer = nm.let(lambda a: nm.let(lambda b: b, b=2), a=1)
    inner = nu.tree.children(outer)[0]
    assert _shape(inner) is not _shape(outer)


def test_one_function_binds_one_shape() -> None:
    def body(n: nm.ObjectRef) -> nu.Nu:
        return n

    assert _shape(nm.let(body, n=1)) is _shape(nm.let(body, n=2))


def test_let_refuses_a_callable_without_code() -> None:
    class Builder:
        def __call__(self, n: nm.ObjectRef) -> nu.Nu:
            return n

    with pytest.raises(TypeError, match="function"):
        nm.let(Builder(), n=1)


def test_a_tree_holding_a_let_survives_the_wire() -> None:
    term = nm.let(lambda n: nu.Add(n, 1), n=41)
    assert nu.run(wire.loads(wire.dumps(term)))[0] == 42


# --- values by name ----------------------------------------------------------


@RUNNERS
def test_several_values_by_name(run: Callable) -> None:
    assert run(nm.let(lambda a, b: nu.Sub(a, b), b=2, a=44)) == 42


@RUNNERS
def test_values_are_evaluated_before_the_frame(run: Callable) -> None:
    # The inner let's value reads the outer frame of the same lambda's Shape.
    def step(n: nm.ObjectRef) -> nu.Nu:
        return n

    term = nm.let(lambda a: nm.let(lambda a: a, a=nu.Add(a, 1)), a=41)
    assert run(term) == 42
    assert run(nm.let(step, n=nm.let(step, n=7))) == 7


def test_a_value_naming_no_parameter_fails_at_build() -> None:
    with pytest.raises(TypeError, match=r"\['m'\] name no parameter"):
        nm.let(lambda n: n, n=1, m=2)


def test_a_parameter_without_a_value_fails_at_build() -> None:
    with pytest.raises(TypeError, match=r"no value for \['b'\]"):
        nm.let(lambda a, b: a, a=1)


def test_a_body_passed_with_a_lambda_fails_at_build() -> None:
    with pytest.raises(TypeError, match="by name"):
        nm.let(lambda n: n, nu.Add(1, 2))


def test_a_lambda_returning_none_fails_at_build() -> None:
    with pytest.raises(TypeError, match="returned None"):
        nm.let(lambda n: None, n=1)


def test_a_variadic_lambda_fails_at_build() -> None:
    with pytest.raises(TypeError, match="fixed list"):
        nm.let(lambda *ns: ns[0], n=1)


@RUNNERS
def test_a_parameter_named_after_a_ref_method_still_works(run: Callable) -> None:
    # ``items`` is a ref method, so the generated slot takes another name.
    assert run(nm.let(lambda items, set: nu.Add(items, set), items=40, set=2)) == 42


# --- free form arity (every dynamic binding) -----------------------------------


class _Hands(_DynamicBinding, nu.Bracket):
    """A test binding handing its body two values, ``10`` and ``20``."""

    def __init__(self, fn: object) -> None:
        super().__init__(self._dynamic("_Hands", fn, 2))

    @contextmanager
    def _open(self, ctx: nu.Context) -> Iterator[nu.Context]:
        yield self._push(ctx, (10, 20))


@RUNNERS
def test_a_lambda_may_take_fewer_values_than_handed(run: Callable) -> None:
    assert run(_Hands(lambda a: a)) == 10
    assert run(_Hands(lambda a, b: nu.Add(a, b))) == 30


def test_a_lambda_taking_none_of_the_values_still_builds() -> None:
    assert nu.run(_Hands(lambda: nu.Add(1, 1)))[0] == 2


def test_a_lambda_taking_more_values_than_handed_fails_at_build() -> None:
    with pytest.raises(TypeError, match="hands its body 2 values, so its lambda takes at most 2"):
        _Hands(lambda a, b, c: a)
