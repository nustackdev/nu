"""Execution tests for the reflection atoms.

Compile and evaluate each atom over Literal operands and check it mirrors the
Python builtin it maps. Sentinel propagation (EMPTY / INVALID operand -> INVALID
result) is checked too, matching the arithmetic / comparison fold.
"""

from __future__ import annotations

import asyncio

from nu.core.literal import Literal
from nu.core.reflection import (
    Callable as Callable,
)
from nu.core.reflection import (
    Dir as Dir,
)
from nu.core.reflection import (
    Hash as Hash,
)
from nu.core.reflection import (
    Id as Id,
)
from nu.core.reflection import (
    IsInstance as IsInstance,
)
from nu.core.reflection import (
    IsSubclass as IsSubclass,
)
from nu.core.reflection import (
    Type as Type,
)
from nu.core.reflection import (
    Vars as Vars,
)
from nu.lang import EMPTY, INVALID
from nu.lang.helpers import aeval, compile, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- type / class --------------------------------------------------------


def test_type_of_a_literal():
    assert _eval(Type(Literal(5))) is int
    assert _eval(Type(Literal("hi"))) is str
    assert _eval(Type(Literal([1, 2]))) is list


def test_isinstance_checks_membership():
    assert _eval(IsInstance(Literal(5), Literal(int))) is True
    assert _eval(IsInstance(Literal(5), Literal(str))) is False
    assert _eval(IsInstance(Literal(5), Literal((int, str)))) is True


def test_issubclass_checks_lineage():
    assert _eval(IsSubclass(Literal(bool), Literal(int))) is True
    assert _eval(IsSubclass(Literal(int), Literal(str))) is False


def test_callable_detects_callables():
    assert _eval(Callable(Literal(len))) is True
    assert _eval(Callable(Literal(int))) is True
    assert _eval(Callable(Literal(5))) is False


# --- identity / value ----------------------------------------------------


def test_id_matches_python_id_in_run():
    obj = object()
    assert _eval(Id(Literal(obj))) == id(obj)


def test_hash_matches_python_hash():
    assert _eval(Hash(Literal(3))) == hash(3)
    assert _eval(Hash(Literal("nu"))) == hash("nu")


# --- namespace -----------------------------------------------------------


def test_dir_lists_attribute_names():
    result = _eval(Dir(Literal("")))
    assert result == dir("")
    assert "upper" in result


def test_vars_returns_the_object_dict():
    class Bag:
        pass

    bag = Bag()
    bag.x = 1
    assert _eval(Vars(Literal(bag))) == {"x": 1}


# --- sentinels -----------------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(Type(Literal(EMPTY))) is INVALID
    assert _eval(Hash(Literal(INVALID))) is INVALID
    assert _eval(IsInstance(Literal(EMPTY), Literal(int))) is INVALID
    assert _eval(IsInstance(Literal(5), Literal(EMPTY))) is INVALID
    assert _eval(IsSubclass(Literal(bool), Literal(INVALID))) is INVALID


# --- async mirror --------------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(Type(Literal(5)))) is int
    assert asyncio.run(_aeval(IsInstance(Literal(5), Literal(int)))) is True
    assert asyncio.run(_aeval(Callable(Literal(len)))) is True
    assert asyncio.run(_aeval(Hash(Literal(3)))) == hash(3)
    assert asyncio.run(_aeval(Type(Literal(EMPTY)))) is INVALID
