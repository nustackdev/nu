"""NULL across every kind of interaction, end to end.

A read of an unwritten slot gives NULL. Ops run plain Python, so NULL's own
interface decides: falsy and comparable by ``==``, TypeError for the rest.
Writes refuse it, ``exists()``, ``is_null()``, ``is_set_falsy()`` and
``fallback()`` know it. These tests pin each rule through real trees on the
mem fabric, on both run paths.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
from nu.forms import Int, Object, Str
from nu.lang import NULL, ScalarQuery, is_null


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


# --- reads make NULL, ops run plain python ---------------------------------


def test_an_unwritten_ref_reads_as_null_with_its_path(run):
    v = run(User.age)
    assert is_null(v)
    assert repr(v) == "<NULL User.age>"


@pytest.mark.parametrize(
    "build",
    [
        lambda: User.age + 1,
        lambda: User.age * User.age,
        lambda: User.age > 3,
        lambda: User.name.upper(),
        lambda: User.name + "!",
        lambda: nu.ToStr(User.age),
        lambda: nu.Len(User.name),
    ],
)
def test_an_unsupported_op_on_null_raises_type_error(run, build):
    with pytest.raises((TypeError, AttributeError)):
        run(build())


def test_supported_ops_on_null_answer(run):
    assert run(User.name == "gor") is False
    assert run(User.name != "gor") is True
    assert run(nu.Not(User.age)) is True
    assert run(nu.ToBool(User.age)) is False


# --- conditions read NULL as false -----------------------------------------


def test_if_takes_the_else_branch_on_a_null_cond(run):
    assert run(nu.If(User.age, "set", "unset")) == "unset"
    assert run(nu.If(nu.Not(User.age), "unset", "set")) == "unset"


def test_ifdo_runs_the_else_body_on_a_null_cond(run):
    term = nu.IfDo(User.age, User.name.set("then"), User.name.set("else"))
    assert run(term, then=User.name) == "else"


def test_whiledo_never_enters_on_a_null_cond(run):
    assert is_null(run(nu.WhileDo(User.age, User.name.set(Boom())), then=User.name))


def test_and_or_read_a_null_child_as_false(run):
    assert run(nu.And(User.age, Boom())) is False
    assert run(nu.Or(User.age, True)) is True
    assert run(nu.Or(User.age, User.name)) is False


def test_switch_on_a_null_selector_matches_no_key(run):
    assert run(nu.Switch(User.age, {1: "one"}, default="none")) == "none"
    with pytest.raises(KeyError):
        run(nu.Switch(User.age, {1: "one"}))


def test_filter_predicate_null_drops_the_item(run):
    kept = nu.Collect(nu.Filter(nu.Iter([1, 2, 3]), User.age))
    assert run(kept) == []


# --- writes refuse NULL ----------------------------------------------------


@pytest.mark.parametrize(
    "build",
    [
        lambda: User.age.set(User.age),
        lambda: User.tags.append(User.name),
    ],
)
def test_a_write_of_null_raises(run, build):
    with pytest.raises(ValueError, match="NULL"):
        run(build())


def test_a_write_built_on_null_raises_from_the_op(run):
    with pytest.raises(TypeError):
        run(User.age.inc())
    with pytest.raises(TypeError):
        run(User.name.set(User.name + "!"))


def test_print_of_null_raises(capsys):
    with pytest.raises(TypeError):
        nu.run(nu.print(User.name), nu.Context().bind(dict, {}, User))


# --- checks ----------------------------------------------------------------


def test_exists_is_a_plain_bool(run):
    assert run(User.age.exists()) is False
    assert run(User.age.set(0), then=User.age.exists()) is True
    assert run(User.tags.exists()) is True


def test_checks_are_bool_forms(run):
    for term in (User.age.exists(), User.age.is_null(), User.age.is_set_falsy()):
        assert isinstance(term, nu.Bool)
    assert run(User.age.exists().not_()) is True
    assert run(User.age.is_null()) is True
    assert run(User.tags.is_null()) is False


@pytest.mark.parametrize("falsy", [0, False])
def test_is_set_falsy_is_true_only_for_a_stored_falsy_value(run, falsy):
    assert run(User.age.is_set_falsy()) is False
    assert run(User.age.set(falsy), then=User.age.is_set_falsy()) is True
    assert run(User.age.set(3), then=User.age.is_set_falsy()) is False


def test_is_set_falsy_on_a_collection(run):
    assert run(User.tags.is_set_falsy()) is True
    assert run(User.tags.append("a"), then=User.tags.is_set_falsy()) is False


def test_init_sets_only_when_nothing_is_there(run):
    assert run(User.age.init(5), then=User.age) == 5
    assert run(nu.Sequential(User.age.set(0), User.age.init(5)), then=User.age) == 0


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


def test_fallback_is_null_only_when_all_are_null(run):
    assert is_null(run(User.age.fallback(User.name, nu.Literal(NULL))))


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
