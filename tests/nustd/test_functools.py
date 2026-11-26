"""Functional tests for ``nustd.functools.reduce`` (a Reduction fold).

Drives the fold through run/arun, asserting against Python's
``functools.reduce``. The reducer is a lambda over mem refs to the accumulator and the item.
"""

from __future__ import annotations

import functools as pyfunctools
import operator

import pytest

import nu
from nu import run
from nu.lang import Context
from nu.lang.helpers import arun
from nustd.functools import reduce


def test_sum_no_initializer() -> None:
    value, _ = run(reduce(lambda acc, x: acc + x, [1, 2, 3, 4]))
    assert value == pyfunctools.reduce(operator.add, [1, 2, 3, 4])


def test_product_no_initializer() -> None:
    value, _ = run(reduce(lambda acc, x: acc * x, [1, 2, 3, 4]))
    assert value == pyfunctools.reduce(operator.mul, [1, 2, 3, 4])  # 24


def test_sum_with_initializer() -> None:
    value, _ = run(reduce(lambda acc, x: acc + x, [1, 2, 3], 100))
    assert value == pyfunctools.reduce(operator.add, [1, 2, 3], 100)  # 106


def test_single_element_no_initializer_returns_it() -> None:
    value, _ = run(reduce(lambda acc, x: acc + x, [42]))
    assert value == 42


def test_initializer_only_empty_source() -> None:
    value, _ = run(reduce(lambda acc, x: acc + x, [], 7))
    assert value == 7


def test_empty_no_initializer_raises() -> None:
    with pytest.raises(TypeError):
        run(reduce(lambda acc, x: acc + x, []))


def test_runs_on_async_path() -> None:
    import asyncio

    value, _ = asyncio.run(arun(reduce(lambda acc, x: acc * x, [1, 2, 3, 4])))
    assert value == 24


class Out(nu.Shape):
    log = nu.mem.ListRef.slot(object)


def _outer() -> tuple[dict, Context]:
    data: dict = {"log": []}
    return data, Context().bind(dict, data, Out)


def test_the_step_frame_never_reaches_the_caller() -> None:
    data, ctx = _outer()
    value, out = run(reduce(lambda acc, x: acc + x, [1, 2, 3]), ctx)
    assert value == 6
    assert out is ctx
    assert data == {"log": []}


async def test_the_step_frame_never_reaches_the_caller_async() -> None:
    _, ctx = _outer()
    value, out = await arun(reduce(lambda acc, x: acc + x, [1, 2, 3]), ctx)
    assert value == 6
    assert out is ctx


def test_each_step_reads_its_own_pair() -> None:
    value, _ = run(reduce(lambda acc, x: nu.List.of(acc, x), [1, 2, 3]))
    assert value == [[1, 2], 3]


def test_a_lambda_may_take_only_the_accumulator() -> None:
    value, _ = run(reduce(lambda acc: acc * 2, [1, 2, 3]))
    assert value == 4


def test_a_lambda_taking_more_than_two_raises() -> None:
    with pytest.raises(TypeError, match="so its lambda takes at most 2"):
        reduce(lambda a, b, c: a, [1])
