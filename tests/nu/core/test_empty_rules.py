"""EMPTY across every kind of interaction, end to end.

EMPTY is the one "no value" sentinel. Queries propagate it, conditions read it
as false, writes refuse it, ``exists()`` and ``fallback()`` observe it. These
tests pin each rule through real trees on the mem fabric, on both run paths.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
from nu.forms import Int, Object, Str
from nu.lang import EMPTY, ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


class User(nu.Shape):
    age = nu.IntRef.slot()
    name = nu.StrRef.slot()
    tags = nu.ListRef.slot(str)


class Boom(ScalarQuery):
    """An atom that raises the moment it is evaluated."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            raise AssertionError("short-circuited child was evaluated")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            raise AssertionError("short-circuited child was evaluated")

        return athunk


def _sync(term: object, ctx: nu.Context) -> object:
    return nu.run(term, ctx)[0]


def _async(term: object, ctx: nu.Context) -> object:
    return asyncio.run(nu.arun(term, ctx))[0]


@pytest.fixture(params=[_sync, _async], ids=["sync", "async"])
def run(request: pytest.FixtureRequest) -> Callable[..., object]:
    """Run a term over a fresh, unwritten ``User`` and yield its value.

    With ``then``, the term runs for its effect and ``then`` is read after it,
    over the same Context.
    """

    def go(term: object, then: object = None) -> object:
        ctx = nu.Context().bind(dict, {"tags": []}, User)
        value = request.param(term, ctx)
        return value if then is None else request.param(then, ctx)

    return go


# --- queries propagate -----------------------------------------------------


@pytest.mark.parametrize(
    "build",
    [
        lambda: User.age + 1,
        lambda: User.age * User.age,
        lambda: User.age > 3,
        lambda: User.name == "gor",
        lambda: User.name.upper(),
        lambda: User.name + "!",
        lambda: nu.Not(User.age),
        lambda: nu.ToStr(User.age),
        lambda: nu.Len(User.name),
    ],
)
def test_a_query_over_an_unwritten_ref_yields_empty(run, build):
    assert run(build()) is EMPTY


def test_an_unwritten_ref_reads_as_empty(run):
    assert run(User.age) is EMPTY


# --- conditions read EMPTY as false ----------------------------------------


def test_if_takes_the_else_branch_on_an_empty_cond(run):
    assert run(nu.If(User.age > 3, "old", "young")) == "young"
    assert run(nu.If(nu.Not(User.age > 3), "young", "old")) == "old"


def test_ifdo_runs_the_else_body_on_an_empty_cond(run):
    term = nu.IfDo(User.age > 3, User.name.set("then"), User.name.set("else"))
    assert run(term, then=User.name) == "else"


def test_whiledo_never_enters_on_an_empty_cond(run):
    assert run(nu.WhileDo(User.age < 3, User.name.set(Boom())), then=User.name) is EMPTY


def test_and_or_read_an_empty_child_as_false_without_poisoning(run):
    assert run(nu.And(User.age, Boom())) is False
    assert run(nu.Or(User.age, True)) is True
    assert run(nu.Or(User.age > 3, User.name)) is False


def test_switch_matches_no_key_on_an_empty_selector(run):
    assert run(nu.Switch(User.age, {1: "one"}, default="none")) == "none"
    assert run(nu.Switch(User.age, {1: "one"})) is EMPTY


def test_filter_drops_an_item_whose_predicate_is_empty(run):
    kept = nu.Collect(nu.Filter(nu.Iter([1, 2, 3]), nu.Gt(nu.Attr("item"), User.age)))
    assert run(kept) == []


# --- writes refuse EMPTY ---------------------------------------------------


@pytest.mark.parametrize(
    "build",
    [
        lambda: User.age.set(User.age),
        lambda: User.age.inc(),
        lambda: User.name.set(User.name + "!"),
        lambda: User.tags.append(User.name),
    ],
)
def test_a_write_of_empty_raises(run, build):
    with pytest.raises(ValueError, match="EMPTY"):
        run(build())


def test_print_shows_empty_rather_than_raising(capsys):
    nu.run(nu.print(User.name), nu.Context().bind(dict, {}, User))
    assert capsys.readouterr().out == "<EMPTY>\n"


def test_raise_with_an_empty_message_still_raises(run):
    with pytest.raises(LookupError, match="<EMPTY>"):
        run(nu.raise_(LookupError, User.name))


# --- exists ----------------------------------------------------------------


def test_exists_is_a_plain_bool_never_empty(run):
    assert run(User.age.exists()) is False
    assert run(User.age.set(0), then=User.age.exists()) is True


# --- fallback --------------------------------------------------------------


def test_fallback_yields_the_first_present_value(run):
    assert run(User.age.fallback(7)) == 7
    assert run(User.age.fallback(User.age, 9)) == 9
    assert run(User.age.set(41), then=User.age.fallback(7)) == 41


@pytest.mark.parametrize("present", [0, "", False, None])
def test_fallback_checks_presence_not_truthiness(run, present):
    assert run(nu.Object(present).fallback("other")) == present


def test_fallback_evaluates_only_as_far_as_it_needs(run):
    assert run(nu.Int(1).fallback(Boom())) == 1
    assert run(User.age.fallback(2, Boom())) == 2


def test_fallback_is_empty_only_when_all_are_empty(run):
    assert run(User.age.fallback(User.age + 1, nu.Literal(EMPTY))) is EMPTY


def test_fallback_keeps_the_form_of_its_receiver():
    assert type(User.name.fallback("guest")) is Str
    assert type(User.age.fallback(0)) is Int
    assert type(nu.Object(1).fallback(2)) is Object


def test_fallback_keeps_the_receivers_surface(run):
    assert run(User.name.fallback("guest").upper()) == "GUEST"


def test_fallback_needs_an_alternative():
    with pytest.raises(TypeError, match="at least one"):
        User.age.fallback()


# --- If --------------------------------------------------------------------


def test_if_runs_only_the_taken_branch(run):
    assert run(nu.If(True, 1, Boom())) == 1
    assert run(nu.If(User.age, Boom(), 2)) == 2


def test_if_wrapped_in_a_form_keeps_that_surface(run):
    assert run(nu.Str(nu.If(User.age.exists(), "Admin", "Member")).upper()) == "MEMBER"
