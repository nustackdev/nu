"""Execution tests for the reflection atoms.

Compile and evaluate each atom over LiteralQuery operands and check it mirrors the
Python builtin it maps. Sentinel propagation (EMPTY / INVALID operand -> INVALID
result) is checked too, matching the arithmetic / comparison fold.
"""

from __future__ import annotations

import asyncio

from nu.core.literal import LiteralQuery
from nu.core.reflection import (
    CallableQuery as Callable,
)
from nu.core.reflection import (
    DirQuery as Dir,
)
from nu.core.reflection import (
    HashQuery as Hash,
)
from nu.core.reflection import (
    IdQuery as Id,
)
from nu.core.reflection import (
    IsInstanceQuery as IsInstance,
)
from nu.core.reflection import (
    IsSubclassQuery as IsSubclass,
)
from nu.core.reflection import (
    TypeQuery as Type,
)
from nu.core.reflection import (
    VarsQuery as Vars,
)
from nu.lang import EMPTY, INVALID, compile
from nu.lang.helpers import aeval, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- type / class --------------------------------------------------------


def test_type_of_a_literal():
    assert _eval(Type(LiteralQuery(5))) is int
    assert _eval(Type(LiteralQuery("hi"))) is str
    assert _eval(Type(LiteralQuery([1, 2]))) is list


def test_isinstance_checks_membership():
    assert _eval(IsInstance(LiteralQuery(5), LiteralQuery(int))) is True
    assert _eval(IsInstance(LiteralQuery(5), LiteralQuery(str))) is False
    assert _eval(IsInstance(LiteralQuery(5), LiteralQuery((int, str)))) is True


def test_issubclass_checks_lineage():
    assert _eval(IsSubclass(LiteralQuery(bool), LiteralQuery(int))) is True
    assert _eval(IsSubclass(LiteralQuery(int), LiteralQuery(str))) is False


def test_callable_detects_callables():
    assert _eval(Callable(LiteralQuery(len))) is True
    assert _eval(Callable(LiteralQuery(int))) is True
    assert _eval(Callable(LiteralQuery(5))) is False


# --- identity / value ----------------------------------------------------


def test_id_matches_python_id_in_run():
    obj = object()
    assert _eval(Id(LiteralQuery(obj))) == id(obj)


def test_hash_matches_python_hash():
    assert _eval(Hash(LiteralQuery(3))) == hash(3)
    assert _eval(Hash(LiteralQuery("nu"))) == hash("nu")


# --- namespace -----------------------------------------------------------


def test_dir_lists_attribute_names():
    result = _eval(Dir(LiteralQuery("")))
    assert result == dir("")
    assert "upper" in result


def test_vars_returns_the_object_dict():
    class Bag:
        pass

    bag = Bag()
    bag.x = 1
    assert _eval(Vars(LiteralQuery(bag))) == {"x": 1}


# --- sentinels -----------------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(Type(LiteralQuery(EMPTY))) is INVALID
    assert _eval(Hash(LiteralQuery(INVALID))) is INVALID
    assert _eval(IsInstance(LiteralQuery(EMPTY), LiteralQuery(int))) is INVALID
    assert _eval(IsInstance(LiteralQuery(5), LiteralQuery(EMPTY))) is INVALID
    assert _eval(IsSubclass(LiteralQuery(bool), LiteralQuery(INVALID))) is INVALID


# --- async mirror --------------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(Type(LiteralQuery(5)))) is int
    assert asyncio.run(_aeval(IsInstance(LiteralQuery(5), LiteralQuery(int)))) is True
    assert asyncio.run(_aeval(Callable(LiteralQuery(len)))) is True
    assert asyncio.run(_aeval(Hash(LiteralQuery(3)))) == hash(3)
    assert asyncio.run(_aeval(Type(LiteralQuery(EMPTY)))) is INVALID
