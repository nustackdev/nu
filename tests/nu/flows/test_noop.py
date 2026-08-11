"""Tests for Noop: the empty Flow, the identity of flow composition.

Noop is a childless Strategy. It yields nothing, mutates nothing, and slot-fits
wherever work fits - a Strategy child, a Control body, a Span body. It is
correctly rejected in value slots and param slots: a no-op belongs where a
mutator would go, never where a value is read.
"""

from __future__ import annotations

import pytest

from nu.core import Add
from nu.domains.shape import Shape
from nu.engine.validation import ValidationError
from nu.flows import DelayedDo, IfDo, Noop, Sequential
from nu.kv import IntRef
from nu.lang import LAWS, Attr, Cardinality, Flow, Sort, Strategy, compile, validate
from nu.lang.helpers import arun, run
from nu.spans import Retry


class _S(Shape):
    n = IntRef.slot()


def _validate(term: object) -> None:
    validate(compile(term), *LAWS)


def _rejects(term: object) -> None:
    with pytest.raises(ValidationError):
        _validate(term)


def test_noop_is_an_empty_strategy() -> None:
    assert issubclass(Noop, Strategy)
    assert issubclass(Noop, Flow)
    program = compile(Noop())
    assert program.attr(program.root, Attr.SORT) is Sort.STRATEGY
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.VOID
    assert not Noop()._children


def test_noop_yields_none() -> None:
    value, _ = run(Noop())
    assert value is None


async def test_noop_yields_none_async() -> None:
    value, _ = await arun(Noop())
    assert value is None


# --- fits every work slot ------------------------------------------------


def test_noop_fits_strategy_child() -> None:
    _validate(Sequential(_S.n.set(1), Noop(), _S.n.set(2)))


def test_noop_fits_control_body() -> None:
    _validate(DelayedDo(0.02, Noop()))


def test_noop_fits_span_body() -> None:
    _validate(Retry(Noop()))


def test_bare_noop_validates() -> None:
    _validate(Noop())


# --- rejected where a value or param is expected -------------------------


def test_noop_rejected_in_value_slot() -> None:
    _rejects(Add(Noop(), 3))


def test_noop_rejected_in_control_param() -> None:
    _rejects(IfDo(Noop(), _S.n.set(1)))
