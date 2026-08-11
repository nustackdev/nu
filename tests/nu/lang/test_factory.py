"""Unit + functional tests for ``InteractionFactory``.

The factory produces real ``Nu`` subclasses, so the tests do both unit
checks (declared attributes land on the class, sentinel handling, sync vs
async inference, rejected bases) and end-to-end checks (compile + run a
program built from a generated atom).
"""

from __future__ import annotations

import asyncio

import pytest

from nu.core import Literal
from nu.engine.structure import Declared
from nu.factory import InteractionFactory, host
from nu.lang import (
    Command,
    Reduction,
    ScalarQuery,
    Span,
    StreamQuery,
)
from nu.lang.helpers import arun, run
from nu.lang.sentinels import EMPTY, INVALID


# --- class shape --------------------------------------------------------


def test_returns_a_subclass_of_the_base() -> None:
    Add = InteractionFactory(ScalarQuery, "Add", lambda *xs: sum(xs))
    assert issubclass(Add, ScalarQuery)
    assert Add.__name__ == "Add"


def test_declared_attribute_is_wrapped() -> None:
    Add = InteractionFactory(
        ScalarQuery, "Add", lambda *xs: sum(xs), commutative=True, associative=True
    )
    assert "commutative" in Add._attributes
    assert "associative" in Add._attributes
    assert Add._attributes["commutative"].value is True


def test_pre_wrapped_attribute_passes_through() -> None:
    decl = Declared(value=True)
    Cls = InteractionFactory(ScalarQuery, "Cls", lambda: 0, commutative=decl)
    assert Cls._commutative is decl


def test_rejects_unsupported_base() -> None:
    for bad in (StreamQuery, Reduction, Span):
        with pytest.raises(TypeError):
            InteractionFactory(bad, "X", lambda: 0)


# --- sync evaluation ----------------------------------------------------


def test_scalar_query_runs_end_to_end() -> None:
    Add = InteractionFactory(ScalarQuery, "Add", lambda *xs: sum(xs))
    value, _ = run(Add(1, 2, 3))
    assert value == 6


def test_unary_atom_works() -> None:
    Neg = InteractionFactory(ScalarQuery, "Neg", lambda x: -x)
    value, _ = run(Neg(7))
    assert value == -7


def test_nested_built_atoms_compose() -> None:
    Add = InteractionFactory(ScalarQuery, "Add", lambda a, b: a + b)
    Mul = InteractionFactory(ScalarQuery, "Mul", lambda a, b: a * b)
    value, _ = run(Add(Mul(2, 3), 4))
    assert value == 10


# --- keyword arguments --------------------------------------------------


def test_keyword_children_dispatch_to_kwargs() -> None:
    Sub = InteractionFactory(ScalarQuery, "Sub", lambda a, *, b: a - b)
    value, _ = run(Sub(10, b=3))
    assert value == 7


def test_mixed_positional_and_keyword() -> None:
    def fn(a: int, b: int, *, c: int, d: int) -> int:
        return a + b + c + d

    Mix = InteractionFactory(ScalarQuery, "Mix", fn)
    value, _ = run(Mix(1, 2, c=3, d=4))
    assert value == 10


def test_keyword_child_sentinel_short_circuits() -> None:
    Sub = InteractionFactory(ScalarQuery, "Sub", lambda a, *, b: a - b)
    value, _ = run(Sub(10, b=Literal(EMPTY)))
    assert value is INVALID


def test_keyword_args_run_on_async_path() -> None:
    Sub = InteractionFactory(ScalarQuery, "Sub", lambda a, *, b: a - b)
    value, _ = asyncio.run(arun(Sub(10, b=4)))
    assert value == 6


# --- host helper ------------------------------------------


def test_scalar_query_factory_builds_scalar_query() -> None:
    Add = host(lambda a, b: a + b, name="Add", commutative=True)
    assert issubclass(Add, ScalarQuery)
    assert Add._attributes["commutative"].value is True
    value, _ = run(Add(2, 3))
    assert value == 5


def test_scalar_query_factory_binds_an_unbound_method() -> None:
    # an unbound method is a plain callable whose first arg is the receiver
    Upper = host(str.upper, name="Upper")
    value, _ = run(Upper("nu"))
    assert value == "NU"


# --- sentinel propagation -----------------------------------------------


def test_sentinel_short_circuits_by_default() -> None:
    Add = InteractionFactory(ScalarQuery, "Add", lambda a, b: a + b)
    value, _ = run(Add(Literal(EMPTY), 1))
    assert value is INVALID
    value, _ = run(Add(1, Literal(INVALID)))
    assert value is INVALID


def test_propagate_off_passes_sentinels_through() -> None:
    seen: list[object] = []

    def keep(a: object, b: object) -> object:
        seen.append((a, b))
        return "ok"

    NoProp = InteractionFactory(ScalarQuery, "NoProp", keep, propagate_sentinels=False)
    value, _ = run(NoProp(Literal(EMPTY), Literal(INVALID)))
    assert value == "ok"
    assert seen == [(EMPTY, INVALID)]


# --- command shape ------------------------------------------------------


def test_command_thunk_returns_none_and_calls_fn() -> None:
    calls: list[tuple[object, ...]] = []

    def side_effect(*xs: object) -> object:
        calls.append(xs)
        return "ignored"

    Touch = InteractionFactory(
        Command,
        "Touch",
        side_effect,
        mutates=frozenset({0}),
    )
    # A Command must wrap a Ref in slot 0; for a unit check we drive the
    # built thunk directly. compile() gives us back a (rt) -> None thunk.
    instance = Touch.__new__(Touch)
    instance._children = ()
    instance._payload = {}
    thunk = instance._compile(0, ())
    assert thunk(rt=None) is None
    assert calls == [()]


def test_command_short_circuits_to_none_on_sentinel() -> None:
    calls: list[object] = []

    def fn(x: object) -> object:
        calls.append(x)

    Touch = InteractionFactory(Command, "Touch", fn, mutates=frozenset({0}))
    instance = Touch.__new__(Touch)
    instance._children = ()
    instance._payload = {}

    def child_thunk(rt: object) -> object:
        return EMPTY

    thunk = instance._compile(0, (child_thunk,))
    assert thunk(rt=None) is None
    assert calls == []  # fn never ran


# --- async inference ----------------------------------------------------


def test_async_def_infers_requires_async() -> None:
    async def afn(x: int) -> int:
        return x + 1

    Inc = InteractionFactory(ScalarQuery, "Inc", afn)
    assert "requires_async" in Inc._attributes
    assert Inc._attributes["requires_async"].value is True


def test_async_atom_runs_on_async_path() -> None:
    async def adouble(x: int) -> int:
        await asyncio.sleep(0)
        return x * 2

    Double = InteractionFactory(ScalarQuery, "Double", adouble)
    value, _ = asyncio.run(arun(Double(5)))
    assert value == 10


def test_sync_def_runs_on_async_path_too() -> None:
    Square = InteractionFactory(ScalarQuery, "Square", lambda x: x * x)
    value, _ = asyncio.run(arun(Square(6)))
    assert value == 36
