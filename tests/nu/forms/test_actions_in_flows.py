"""A form over an Action composes like the Action it wraps.

A value form is a Span: it wraps one body and forwards its yield, so a
mutating read like ``pop`` keeps its Action sort through the form. It runs as
a step in ``>>``, as a Flow body, and inside a Bracket or Policy, and each
time the write happens and the popped value comes out. The other side of the
same rule: a form never makes a non-yielding body acceptable, never changes
its body's cardinality, and always wraps exactly one body.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from _support.laws import assert_fails, assert_passes, violations

import nu
from nu import Context, run
from nu.domains.shape import Shape
from nu.engine import Severity
from nu.lang import Form, Surface
from nu.lang.attributes import Sort
from nu.lang.attributes.sort import subsort
from nu.mem import DictRef, ListRef, SetRef


if TYPE_CHECKING:
    from collections.abc import Callable


class Root(Shape):
    tags = ListRef.slot(str)
    names = DictRef.slot(str)
    members = SetRef.slot(str)


@pytest.fixture
def data() -> dict:
    return {}


@pytest.fixture
def ctx(data: dict) -> Context:
    return Context().bind(dict, data, Root)


# (seed command, the wrapped action, its yield, the store after it ran)
CASES = {
    "list_pop": (
        lambda: Root.tags.set(["a", "b"]),
        lambda: Root.tags.pop(),
        "b",
        {"tags": ["a"]},
    ),
    "dict_popitem": (
        lambda: Root.names.set({"k": "v"}),
        lambda: Root.names.popitem(),
        ("k", "v"),
        {"names": {}},
    ),
    "set_pop": (
        lambda: Root.members.set({"m"}),
        lambda: Root.members.pop(),
        "m",
        {"members": set()},
    ),
}

WRAPS: dict[str, Callable[[nu.Nu], nu.Nu]] = {
    "bare": lambda body: body,
    "snapshot": nu.Snapshot,
    "transaction": nu.Transaction,
    "retry": nu.Retry,
}

case = pytest.mark.parametrize("name", list(CASES))
wrap = pytest.mark.parametrize("how", list(WRAPS))


def _stored(data: dict, expected: dict) -> dict:
    return {k: data[k] for k in expected}


# --- the action is a Span-wrapped Action -----------------------------------


@case
def test_a_form_over_an_action_is_a_form_and_a_span(name: str) -> None:
    _, act, _, _ = CASES[name]
    term = act()
    sort = type(term)._attributes["sort"].value
    assert isinstance(term, Form)
    assert isinstance(term, Surface)
    assert sort is Sort.FORM
    assert subsort(sort, Sort.SPAN)


def test_a_value_form_sorts_as_form() -> None:
    assert type(nu.Str("a"))._attributes["sort"].value is Sort.FORM
    assert subsort(Sort.FORM, Sort.SPAN)


# --- standalone and wrapped: validates, runs, yields, mutates --------------


@case
@wrap
def test_a_wrapped_action_yields_and_mutates(name: str, how: str, ctx: Context, data: dict) -> None:
    seed, act, popped, after = CASES[name]
    term = WRAPS[how](act())
    assert_passes(term)
    run(seed(), ctx)
    assert run(term, ctx)[0] == popped
    assert _stored(data, after) == after


# --- a step in >> ------------------------------------------------------------


@case
@wrap
def test_a_wrapped_action_is_a_step_in_a_chain(
    name: str, how: str, ctx: Context, data: dict
) -> None:
    seed, act, _, after = CASES[name]
    chain = seed() >> WRAPS[how](act())
    assert isinstance(chain, nu.Sequential)
    assert_passes(chain)
    run(chain, ctx)
    assert _stored(data, after) == after


def test_set_then_pop_in_one_chain(ctx: Context, data: dict) -> None:
    chain = Root.tags.set(["x", "y"]) >> Root.tags.pop()
    assert_passes(chain)
    run(chain, ctx)
    assert data["tags"] == ["x"]


def test_a_snapshot_pop_follows_a_step(ctx: Context, data: dict) -> None:
    x = Root.tags.set(["x", "y"])
    chain = x >> nu.Snapshot(Root.tags.pop())
    assert_passes(chain)
    run(chain, ctx)
    assert data["tags"] == ["x"]


# --- a Flow body -------------------------------------------------------------


@case
@wrap
def test_a_wrapped_action_is_a_flow_body(name: str, how: str, ctx: Context, data: dict) -> None:
    seed, act, _, after = CASES[name]
    flow = nu.IfDo(nu.Literal(True), WRAPS[how](act()))
    assert_passes(flow)
    run(seed(), ctx)
    run(flow, ctx)
    assert _stored(data, after) == after


@pytest.mark.asyncio
@case
@wrap
async def test_a_wrapped_action_runs_async(name: str, how: str, ctx: Context, data: dict) -> None:
    seed, act, popped, after = CASES[name]
    await nu.arun(seed(), ctx)
    assert (await nu.arun(WRAPS[how](act()), ctx))[0] == popped
    assert _stored(data, after) == after


# --- what a form does not change --------------------------------------------


def test_a_form_over_a_command_is_refused() -> None:
    assert_fails(nu.List(Root.tags.set(["a"])), "composition")


def test_a_form_over_a_stream_in_a_scalar_slot_is_refused_one_level_up() -> None:
    term = nu.Add(nu.Int(nu.Iterator(nu.Iter([1, 2]))), 1)
    fired = [
        v
        for v in violations(term)
        if v.severity is Severity.ERROR and v.law == "scalar_stream_refused"
    ]
    assert [v.path for v in fired] == [()]


@pytest.mark.parametrize(
    "build",
    [lambda: nu.Int(), lambda: nu.List(), lambda: nu.Str(nu.Str("a"), nu.Str("b"))],
    ids=["int_bodyless", "list_bodyless", "str_two_bodies"],
)
def test_a_form_wraps_exactly_one_body(build: Callable[[], nu.Nu]) -> None:
    with pytest.raises(TypeError, match="wraps exactly one body"):
        build()
