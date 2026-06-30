"""Tests for the Noop leaf Query."""

from __future__ import annotations

from nu.core import Noop
from nu.lang import Attr, Cardinality, ScalarQuery, compile
from nu.lang.helpers import arun, run


def test_noop_is_a_scalar_query() -> None:
    assert issubclass(Noop, ScalarQuery)
    program = compile(Noop())
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.SCALAR


def test_noop_yields_none() -> None:
    value, _ = run(Noop())
    assert value is None


async def test_noop_yields_none_async() -> None:
    value, _ = await arun(Noop())
    assert value is None
