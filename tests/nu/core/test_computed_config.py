"""Config a node reads only while it runs is a child, so it can be computed.

A field is what has to be known before the program runs; everything else is a
child. Each test here takes one value that used to be a field (a switch's case
labels, a parallel arm's mode, a raise's exception class, a policy's error
filter, a remove's ``missing_ok``) and feeds it from a mem read or a
computation instead of a constant, which only a child allows.
"""

from __future__ import annotations

import threading

import pytest
from _support.async_atoms import RunsAnywhereAction, recording

import nu
from nu.core.flows import Parallel


class Cfg(nu.Shape):
    """The values the trees below read their config from."""

    label = nu.StrRef.slot()
    mode = nu.StrRef.slot()
    flag = nu.BoolRef.slot()


class Port(nu.Shape):
    owners = nu.DictRef.slot(str)
    tags = nu.ListRef.slot(str)
    members = nu.SetRef.slot(str)
    ok = nu.BoolRef.slot()


def _framed(body: nu.Nu, **init: object) -> object:
    return nu.run(nu.Frame(Cfg, body, **init))[0]


# --- Switch / SwitchDo: case labels -------------------------------------


def test_switch_labels_come_from_a_mem_read() -> None:
    switch = nu.Switch("b", {Cfg.label: "hit"}, default="miss")
    assert _framed(switch, label="b") == "hit"
    assert _framed(switch, label="a") == "miss"


async def test_switch_labels_are_read_on_the_async_path() -> None:
    switch = nu.Switch("b", {Cfg.label: "hit"}, default="miss")
    assert (await nu.arun(nu.Frame(Cfg, switch, label="b")))[0] == "hit"


def test_switch_case_count_is_the_only_field() -> None:
    switch = nu.Switch(1, {1: "one", 2: "two"}, default="none")
    assert nu.tree.fields(switch) == {"n_cases": 2}
    assert nu.run(nu.tree.children(switch)[1])[0] == (1, 2)


def test_switch_without_default_still_raises_on_a_miss() -> None:
    with pytest.raises(KeyError):
        _framed(nu.Switch("z", {Cfg.label: "hit"}), label="b")


def test_switchdo_labels_come_from_a_mem_read(capsys: pytest.CaptureFixture[str]) -> None:
    switch = nu.SwitchDo(nu.Literal("b"), {Cfg.label: nu.print("hit")}, default=nu.print("miss"))
    _framed(switch, label="b")
    _framed(switch, label="a")
    assert capsys.readouterr().out == "hit\nmiss\n"


def test_switchdo_validates_with_its_labels_as_a_param() -> None:
    switch = nu.SwitchDo(nu.Literal("b"), {Cfg.label: nu.print("hit")})
    nu.lang.helpers.validate(nu.lang.helpers.compile(nu.Frame(Cfg, switch)))


# --- Parallel: per-arm modes --------------------------------------------


async def test_parallel_modes_come_from_a_mem_read() -> None:
    ran: dict = {}
    arms = Parallel((RunsAnywhereAction("t"), Cfg.mode), RunsAnywhereAction("bare"))
    await nu.arun(nu.Frame(Cfg, arms, mode="threaded"), recording(ran), max_parallel=2)
    assert ran["t"].startswith("nu-worker")
    ran.clear()
    await nu.arun(nu.Frame(Cfg, arms, mode="async"), recording(ran), max_parallel=2)
    assert ran["t"] == threading.current_thread().name


def test_a_computed_mode_is_checked_when_it_runs() -> None:
    arms = Parallel((RunsAnywhereAction("t"), Cfg.mode))
    with pytest.raises(ValueError, match="'threaded' or 'async'"):
        nu.run(nu.Frame(Cfg, arms, mode="sideways"), recording({}))


def test_a_plain_mode_is_still_checked_at_construction() -> None:
    with pytest.raises(ValueError, match="'threaded' or 'async'"):
        Parallel((RunsAnywhereAction("t"), "sideways"))


def test_unpinned_parallel_keeps_only_its_arms() -> None:
    a, b = RunsAnywhereAction("a"), RunsAnywhereAction("b")
    assert nu.tree.children(Parallel(a, b)) == (a, b)
    assert nu.tree.fields(Parallel(a, b)) == {}


# --- Raise: exception class ---------------------------------------------


def test_raise_class_is_computed() -> None:
    boom = nu.raise_(nu.If(Cfg.flag, ValueError, KeyError), "boom")
    with pytest.raises(ValueError, match="boom"):
        _framed(boom, flag=True)
    with pytest.raises(KeyError, match="boom"):
        _framed(boom, flag=False)


def test_raise_refuses_a_computed_non_exception_when_it_runs() -> None:
    with pytest.raises(TypeError, match="exc_cls must be an exception class"):
        nu.run(nu.raise_(nu.Literal(int), "boom"))


def test_raise_refuses_a_plain_non_exception_at_construction() -> None:
    with pytest.raises(TypeError, match="exc_cls must be an exception class"):
        nu.raise_(int, "boom")  # type: ignore[arg-type]


# --- TryCatch / Retry: the error filter ---------------------------------


def _filtered(errors: nu.Nu) -> nu.Nu:
    return nu.TryCatch(nu.Div(1, 0), catch=nu.Literal("caught"), errors=errors)


def test_trycatch_errors_are_computed() -> None:
    errors = nu.If(Cfg.flag, ZeroDivisionError, KeyError)
    assert _framed(_filtered(errors), flag=True) == "caught"
    with pytest.raises(ZeroDivisionError):
        _framed(_filtered(errors), flag=False)


async def test_trycatch_errors_are_computed_on_the_async_path() -> None:
    errors = nu.If(Cfg.flag, ZeroDivisionError, KeyError)
    assert (await nu.arun(nu.Frame(Cfg, _filtered(errors), flag=True)))[0] == "caught"


def test_trycatch_refuses_a_plain_non_exception_filter() -> None:
    with pytest.raises(TypeError, match="errors must be exception classes"):
        nu.TryCatch(nu.Div(1, 0), catch=nu.Literal("caught"), errors=int)  # type: ignore[arg-type]


def test_retry_errors_are_computed() -> None:
    retry = nu.Retry(nu.Div(1, 0), max_attempts=2, errors=nu.If(Cfg.flag, KeyError, ValueError))
    with pytest.raises(ZeroDivisionError):
        _framed(retry, flag=True)


# --- missing_ok ---------------------------------------------------------


def _port(**data: object) -> nu.Context:
    return nu.Context().bind(dict, dict(data), Port)


def test_del_item_missing_ok_is_computed() -> None:
    ctx = _port(owners={}, ok=True)
    nu.run(Port.owners.del_item("core", missing_ok=Port.ok), ctx)
    with pytest.raises(KeyError):
        nu.run(Port.owners.del_item("core", missing_ok=Port.ok.not_()), ctx)


def test_list_remove_missing_ok_is_computed() -> None:
    ctx = _port(tags=["a"], ok=True)
    nu.run(Port.tags.remove("z", missing_ok=Port.ok), ctx)
    with pytest.raises(ValueError):
        nu.run(Port.tags.remove("z", missing_ok=Port.ok.not_()), ctx)


def test_set_remove_missing_ok_is_computed() -> None:
    ctx = _port(members={"a"}, ok=True)
    nu.run(Port.members.remove("z", missing_ok=Port.ok), ctx)
    with pytest.raises(KeyError):
        nu.run(Port.members.remove("z", missing_ok=Port.ok.not_()), ctx)
