"""Binder lambdas: a binder's body written as a function of what it hands over.

Every interaction that binds values for its body takes a lambda in that slot.
The interaction mints the names, calls the lambda once with an ``Attr`` per
name, and keeps the tree. Covered here: each binder in lambda form (sync and
async where it has both), nested lambdas keeping their names apart, the
explicit names still working, the two forms refusing to mix, arity checks,
equal trees across builds, and a cloudpickle round trip.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
import nustd
from nu.core.flows.stream import Stream
from nu.engine.structure import Declared
from nu.lang import Context, ScalarAction, wire
from nu.lang.sentinels import EMPTY
from nustd.functools.interactions import Reduce


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


# --- helpers ---------------------------------------------------------------


class Record(ScalarAction):
    """Appends its child's value to ``log``; a mutating body on either path."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, value: object, log: list) -> None:
        super().__init__(value)
        self._payload["log"] = log

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        log, (value,) = self._payload["log"], children

        def thunk(rt: Runtime) -> None:
            log.append(value(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        log, (value,) = self._payload["log"], children

        async def athunk(rt: Runtime) -> None:
            log.append(await value(rt))

        return athunk


class _Feed:
    """A Subscription the test fires by hand."""

    def __init__(self) -> None:
        self.receivers: list = []

    def __deepcopy__(self, memo: dict) -> _Feed:
        return self

    def bind(self, receiver: Callable) -> None:
        self.receivers.append(receiver)

    def unbind(self, receiver: Callable) -> None:
        self.receivers.remove(receiver)

    def close(self) -> None:
        pass

    def fire(self, key: object) -> None:
        for receiver in list(self.receivers):
            receiver(key)


async def _until(check: Callable[[], bool], timeout: float = 2.0) -> None:
    async def poll() -> None:
        while not check():
            await asyncio.sleep(0.001)

    await asyncio.wait_for(poll(), timeout)


async def _cancel(task: asyncio.Task) -> None:
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def _start(term: object, **attrs: object) -> asyncio.Task:
    return asyncio.ensure_future(nu.arun(term, Context(attrs=attrs)))


def _value(term: object) -> object:
    return nu.run(term)[0]


async def _avalue(term: object) -> object:
    return (await nu.arun(term))[0]


def _collect(stream: object) -> object:
    return _value(nu.Collect(stream))


async def _acollect(stream: object) -> object:
    return await _avalue(nu.Collect(stream))


# --- query binders: sync and async -----------------------------------------


QUERIES = [
    pytest.param(lambda: nu.Map(nu.Iter([1, 2]), lambda x: nu.Int(x) + 1), [2, 3], id="Map"),
    pytest.param(lambda: nu.Filter(nu.Iter([1, 2, 3]), lambda x: x > 1), [2, 3], id="Filter"),
    pytest.param(
        lambda: nu.SortBy(nu.Iter(["bb", "a", "ccc"]), lambda s: nu.Len(s)),
        ["a", "bb", "ccc"],
        id="SortBy",
    ),
    pytest.param(
        lambda: nustd.itertools.takewhile(lambda x: x < 3, [1, 2, 5, 1]),
        [1, 2],
        id="TakeWhile",
    ),
    pytest.param(
        lambda: nustd.itertools.dropwhile(lambda x: x < 3, [1, 2, 5, 1]),
        [5, 1],
        id="DropWhile",
    ),
    pytest.param(
        lambda: nustd.itertools.filterfalse(lambda x: x > 1, [1, 2, 3]),
        [1],
        id="FilterFalse",
    ),
    pytest.param(
        lambda: nustd.itertools.starmap(
            lambda pair: nu.Int(nu.GetItem(pair, 0)) * pair[1], [(1, 2), (3, 4)]
        ),
        [2, 12],
        id="StarMap",
    ),
    pytest.param(
        lambda: nustd.itertools.accumulate([1, 2, 3], lambda acc, x: nu.Int(acc) * x),
        [1, 2, 6],
        id="Accumulate",
    ),
    pytest.param(
        lambda: nustd.itertools.groupby([1, 3, 2, 4], lambda x: nu.Int(x) % 2),
        [(1, (1, 3)), (0, (2, 4))],
        id="GroupBy",
    ),
]


@pytest.mark.parametrize(("build", "expected"), QUERIES)
def test_a_stream_binder_takes_a_lambda(build: Callable, expected: list) -> None:
    assert _collect(build()) == expected


@pytest.mark.parametrize(("build", "expected"), QUERIES)
async def test_a_stream_binder_takes_a_lambda_async(build: Callable, expected: list) -> None:
    assert await _acollect(build()) == expected


def _reduce() -> object:
    return nustd.functools.reduce(lambda acc, x: nu.Int(acc) * 10 + x, [1, 2, 3])


def test_reduce_takes_a_lambda() -> None:
    assert _value(_reduce()) == 123


async def test_reduce_takes_a_lambda_async() -> None:
    assert await _avalue(_reduce()) == 123


# --- loops ------------------------------------------------------------------


def _loops(log: list) -> list:
    return [
        nu.ForEachDo(nu.Iter(["a", "b"]), lambda x: Record(x, log)),
        nu.ForRangeDo(0, 2, lambda i: Record(i, log)),
    ]


def test_loops_take_a_lambda() -> None:
    log: list = []
    for loop in _loops(log):
        nu.run(loop)
    assert log == ["a", "b", 0, 1]


async def test_loops_take_a_lambda_async() -> None:
    log: list = []
    for loop in _loops(log):
        await nu.arun(loop)
    assert log == ["a", "b", 0, 1]


async def test_foreach_par_async_takes_a_lambda() -> None:
    log: list = []
    await nu.arun(nu.ForEachParAsync(nu.Iter([1, 2]), lambda x: Record(x, log)))
    assert sorted(log) == [1, 2]


async def test_foreach_par_reactive_takes_a_lambda() -> None:
    feed, log = _Feed(), []
    term = nu.ForEachParReactive(nu.Iter([1, 2]), nu.Attr("feed"), lambda x: Record(x, log))
    task = _start(term, feed=feed)
    await _until(lambda: len(log) == 2)
    assert sorted(log) == [1, 2]
    await _cancel(task)


# --- policy -----------------------------------------------------------------


def _try() -> object:
    return nu.TryCatch(nu.Div(1, 0), catch=lambda err: nu.Str(err).upper())


def test_try_catch_takes_a_lambda() -> None:
    assert _value(_try()) == "DIVISION BY ZERO"


async def test_try_catch_takes_a_lambda_async() -> None:
    assert await _avalue(_try()) == "DIVISION BY ZERO"


async def test_retry_hooks_take_lambdas() -> None:
    log: list = []
    term = nu.Retry(
        nu.Div(1, 0),
        max_attempts=2,
        on_attempt_fail=lambda err, attempt: Record(nu.List.of("retry", err, attempt), log),
        on_fail=lambda err, attempt: Record(nu.List.of("gave up", err, attempt), log),
    )
    await nu.arun(term)
    assert log == [["retry", "division by zero", 1], ["gave up", "division by zero", 2]]


async def test_retry_on_success_sees_the_attempt() -> None:
    log: list = []
    term = nu.Retry(nu.Div(1, 1), on_success=lambda attempt: Record(attempt, log))
    assert (await nu.arun(term))[0] == 1.0
    assert log == [1]


async def test_retry_mixes_a_lambda_hook_with_a_plain_one() -> None:
    log: list = []
    term = nu.Retry(
        nu.Div(1, 0),
        max_attempts=2,
        on_attempt_fail=lambda err, attempt: Record(attempt, log),
        on_fail=Record(nu.Attr("error"), log),
    )
    await nu.arun(term)
    assert log == [1, "division by zero"]


# --- reactive ---------------------------------------------------------------


async def test_react_takes_a_lambda() -> None:
    feed, log = _Feed(), []
    task = _start(nu.React(nu.Attr("feed"), lambda key: Record(key, log)), feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await task
    assert log == ["a"]


async def test_react_while_takes_a_lambda() -> None:
    feed, log = _Feed(), []
    term = nu.ReactWhile(nu.Attr("feed"), True, lambda key: Record(key, log))
    task = _start(term, feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("b")
    await _until(lambda: log == ["a", "b"])
    await _cancel(task)


async def test_react_while_condition_takes_a_lambda() -> None:
    feed, log = _Feed(), []
    term = nu.ReactWhile(
        nu.Attr("feed"), lambda key: nu.Str(key) != "stop", lambda key: Record(key, log)
    )
    task = _start(term, feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("stop")
    await task
    assert log == ["a"]


async def test_react_while_condition_reads_a_named_key() -> None:
    feed, log = _Feed(), []
    term = nu.ReactWhile(
        nu.Attr("feed"),
        nu.Str(nu.Attr("k")) != "stop",
        Record(nu.Attr("k"), log),
        changed_key="k",
    )
    task = _start(term, feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("stop")
    await task
    assert log == ["a"]


@pytest.mark.parametrize("flow", [nu.ReactForever, nu.ReactLatest])
async def test_react_forever_and_latest_take_a_lambda(flow: type) -> None:
    feed, log = _Feed(), []
    task = _start(flow(nu.Attr("feed"), lambda key: Record(key, log)), feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await _until(lambda: log == ["a"])
    await _cancel(task)


async def test_react_latest_initial_run_binds_nothing() -> None:
    feed, log = _Feed(), []
    term = nu.ReactLatest(nu.Attr("feed"), lambda key: Record(key, log), initial=True)
    task = _start(term, feed=feed)
    await _until(lambda: log)
    assert log == [EMPTY]
    await _cancel(task)


async def test_react_still_takes_a_plain_body_and_binds_nothing() -> None:
    feed, log = _Feed(), []
    task = _start(nu.React(nu.Attr("feed"), Record("fired", log)), feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await task
    assert log == ["fired"]


def test_stream_binds_the_key_its_lambda_reads() -> None:
    stream = Stream(nu.Literal(None), lambda key: nu.Iter(nu.List.of(key)))
    _advance, _change, body, key, _log_key = stream._children
    assert str(nu.tree.payload(key)["value"]).startswith("key@")
    assert nu.tree.equal(body, nu.Iter(nu.List.of(nu.Attr(key))))


# --- nesting ----------------------------------------------------------------


def test_nested_lambdas_read_their_own_values() -> None:
    log: list = []
    rows = [["a", "b"], ["c"]]
    term = nu.ForEachDo(
        nu.Iter(rows),
        lambda row: nu.ForEachDo(nu.Iter(row), lambda cell: Record(nu.List.of(row, cell), log)),
    )
    nu.run(term)
    assert log == [[["a", "b"], "a"], [["a", "b"], "b"], [["c"], "c"]]


def test_one_lambda_nested_in_itself_shadows_the_outer_binding() -> None:
    # The same lambda code builds every level, so every level binds the same
    # name and the innermost one wins, as with ``nu.let``: each read sees the
    # innermost item.
    log: list = []

    def nest(depth: int, outer: tuple = ()) -> object:
        if depth == 0:
            return Record(nu.List.of(*outer), log)
        return nu.ForEachDo(nu.Iter([0, 1]), lambda x: nest(depth - 1, (*outer, x)))

    nu.run(nest(2))
    assert log == [[b, b] for _ in (0, 1) for b in (0, 1)]


def test_explicit_names_keep_a_self_nested_loop_apart() -> None:
    log: list = []

    def nest(depth: int) -> object:
        if depth == 0:
            return Record(nu.List.of(nu.Attr("level1"), nu.Attr("level2")), log)
        return nu.ForEachDo(nu.Iter([0, 1]), nest(depth - 1), item=f"level{depth}")

    nu.run(nest(2))
    assert log == [[a, b] for b in (0, 1) for a in (0, 1)]


def test_a_lambda_owns_its_names_across_builds() -> None:
    def build() -> object:
        return nu.Map(nu.Iter([1]), lambda x: x)

    first, second = build(), build()
    assert nu.tree.equal(first._children[2], second._children[2])
    assert str(nu.tree.payload(first._children[2])["value"]).startswith("x@")


def test_same_line_same_parameter_nested_keeps_apart() -> None:
    # Both loops bind a parameter ``x`` from a lambda on the same line; the
    # two lambdas are different code, so the inner body still reads both.
    log: list = []
    nu.run(nu.ForEachDo(["a"], lambda x: (lambda o: nu.ForEachDo([1], lambda x: Record(nu.List.of(o, x), log)))(x)))  # fmt: skip
    assert log == [["a", 1]]


def test_nested_lambdas_on_one_line_get_different_names() -> None:
    term = nu.Map(nu.Iter([[1]]), lambda x: nu.Map(nu.Iter(x), lambda x: x))
    outer_name = term._children[2]
    inner_name = term._children[1]._children[2]
    assert not nu.tree.equal(outer_name, inner_name)


# --- the explicit names stay --------------------------------------------------


def test_explicit_names_still_work() -> None:
    log: list = []
    nu.run(nu.ForEachDo(nu.Iter([1]), Record(nu.Attr("x"), log), item="x"))
    nu.run(nu.ForEachDo(nu.Iter([2]), Record(nu.Attr("item"), log)))
    assert log == [1, 2]
    reduced = Reduce(
        nu.Iter([1, 2]), nu.Int(nu.Attr("a")) + nu.Attr("b"), acc_key="a", item_key="b"
    )
    assert _value(reduced) == 3


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(lambda: nu.ForEachDo([1], lambda x: x, item="x"), id="ForEachDo"),
        pytest.param(lambda: nu.Map([1], lambda x: x, key="x"), id="Map"),
        pytest.param(lambda: nu.ForRangeDo(0, 1, lambda i: i, index="i"), id="ForRangeDo"),
        pytest.param(lambda: nu.TryCatch(1, catch=lambda e: e, error_key="e"), id="TryCatch"),
        pytest.param(lambda: nu.Retry(1, on_success=lambda a: a, attempt_key="a"), id="Retry"),
        pytest.param(
            lambda: nu.ReactForever(nu.Attr("f"), lambda k: k, changed_key="k"), id="ReactForever"
        ),
        pytest.param(lambda: Reduce(nu.Iter([1]), lambda a, b: a, item_key="b"), id="Reduce"),
    ],
)
def test_a_lambda_and_an_explicit_name_refuse_to_mix(build: Callable) -> None:
    with pytest.raises(ValueError, match="not both"):
        build()


def test_retry_refuses_only_the_names_a_lambda_hook_binds() -> None:
    nu.Retry(1, on_success=lambda attempt: attempt, error_key="e")  # on_success binds no error


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(lambda: nu.ForEachDo([1], lambda: 1), id="too few"),
        pytest.param(lambda: nu.Map([1], lambda a, b: a), id="too many"),
        pytest.param(lambda: nustd.functools.reduce(lambda acc: acc, [1]), id="Reduce"),
        pytest.param(lambda: nu.Retry(1, on_success=lambda e, a: a), id="Retry on_success"),
        pytest.param(lambda: nu.Retry(1, on_fail=lambda a: a), id="Retry on_fail"),
    ],
)
def test_a_lambda_of_the_wrong_arity_raises(build: Callable) -> None:
    with pytest.raises(TypeError, match="so its lambda takes"):
        build()


def test_a_lambda_returning_none_raises() -> None:
    with pytest.raises(TypeError, match="returned None"):
        nu.ForEachDo([1], lambda x: None)


# --- trees are values ---------------------------------------------------------


def _program() -> object:
    return nu.ForEachDo(
        nu.Iter([[1, 2]]),
        lambda row: nu.print(nu.Collect(nu.Map(nu.Iter(row), lambda x: nu.Int(x) * 2))),
    )


def test_the_same_program_built_twice_is_equal() -> None:
    assert nu.tree.equal(_program(), _program())


def test_a_lambda_built_tree_round_trips_through_the_wire(capsys: pytest.CaptureFixture) -> None:
    back = wire.loads(wire.dumps(_program()))
    assert nu.tree.equal(back, _program())
    nu.run(back)
    assert capsys.readouterr().out == "[2, 4]\n"
