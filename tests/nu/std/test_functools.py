"""Functional tests for ``nu.std.functools.reduce`` (a Reduction fold).

Drives the fold through run/arun, asserting against Python's
``functools.reduce``. The reducer is built from typed AttrRefs over core atoms.
"""

from __future__ import annotations

import functools as pyfunctools
import operator

import pytest

from nu import IntAttrRef, run
from nu.lang.helpers import arun
from nu.std.functools import reduce


def test_sum_no_initializer() -> None:
    value, _ = run(reduce(IntAttrRef("acc") + IntAttrRef("item"), [1, 2, 3, 4]))
    assert value == pyfunctools.reduce(operator.add, [1, 2, 3, 4])


def test_product_no_initializer() -> None:
    value, _ = run(reduce(IntAttrRef("acc") * IntAttrRef("item"), [1, 2, 3, 4]))
    assert value == pyfunctools.reduce(operator.mul, [1, 2, 3, 4])  # 24


def test_sum_with_initializer() -> None:
    value, _ = run(reduce(IntAttrRef("acc") + IntAttrRef("item"), [1, 2, 3], 100))
    assert value == pyfunctools.reduce(operator.add, [1, 2, 3], 100)  # 106


def test_single_element_no_initializer_returns_it() -> None:
    value, _ = run(reduce(IntAttrRef("acc") + IntAttrRef("item"), [42]))
    assert value == 42


def test_initializer_only_empty_source() -> None:
    value, _ = run(reduce(IntAttrRef("acc") + IntAttrRef("item"), [], 7))
    assert value == 7


def test_empty_no_initializer_raises() -> None:
    with pytest.raises(TypeError):
        run(reduce(IntAttrRef("acc") + IntAttrRef("item"), []))


def test_runs_on_async_path() -> None:
    import asyncio

    value, _ = asyncio.run(arun(reduce(IntAttrRef("acc") * IntAttrRef("item"), [1, 2, 3, 4])))
    assert value == 24
