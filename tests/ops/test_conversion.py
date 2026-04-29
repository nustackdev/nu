"""Tests for conversion ops.

Primitive: ToInt, ToFloat, ToBool, ToStr, ToBytes
Collection: ToList, ToSet, ToTuple

Ops don't catch exceptions. Bad conversions raise (ValueError, TypeError).
"""

from __future__ import annotations

import pytest

from nu import runtime
from nu.interactions import (
    ToBool,
    ToBytes,
    ToFloat,
    ToInt,
    ToList,
    ToSet,
    ToStr,
    ToTuple,
)


# ---------------------------------------------------------------------------
# ToInt
# ---------------------------------------------------------------------------


async def test_int_from_int(ctx):
    assert await runtime.afirst(ToInt(42), ctx) == 42


async def test_int_from_float(ctx):
    assert await runtime.afirst(ToInt(3.7), ctx) == 3


async def test_int_from_str(ctx):
    assert await runtime.afirst(ToInt("123"), ctx) == 123


async def test_int_from_bool(ctx):
    assert await runtime.afirst(ToInt(True), ctx) == 1


async def test_int_from_bad_str_raises(ctx):
    with pytest.raises(ValueError):
        await runtime.afirst(ToInt("hello"), ctx)


# ---------------------------------------------------------------------------
# ToFloat
# ---------------------------------------------------------------------------


async def test_float_from_int(ctx):
    assert await runtime.afirst(ToFloat(5), ctx) == 5.0


async def test_float_from_str(ctx):
    assert await runtime.afirst(ToFloat("3.14"), ctx) == 3.14


async def test_float_from_bad_str_raises(ctx):
    with pytest.raises(ValueError):
        await runtime.afirst(ToFloat("hello"), ctx)


# ---------------------------------------------------------------------------
# ToBool
# ---------------------------------------------------------------------------


async def test_bool_truthy(ctx):
    assert await runtime.afirst(ToBool(1), ctx) is True


async def test_bool_falsy(ctx):
    assert await runtime.afirst(ToBool(0), ctx) is False


async def test_bool_empty_str(ctx):
    assert await runtime.afirst(ToBool(""), ctx) is False


async def test_bool_nonempty_str(ctx):
    assert await runtime.afirst(ToBool("x"), ctx) is True


# ---------------------------------------------------------------------------
# ToStr
# ---------------------------------------------------------------------------


async def test_str_from_int(ctx):
    assert await runtime.afirst(ToStr(42), ctx) == "42"


async def test_str_from_float(ctx):
    assert await runtime.afirst(ToStr(3.14), ctx) == "3.14"


async def test_str_from_none(ctx):
    assert await runtime.afirst(ToStr(None), ctx) == "None"


# ---------------------------------------------------------------------------
# ToBytes
# ---------------------------------------------------------------------------


async def test_bytes_from_str(ctx):
    assert await runtime.afirst(ToBytes("hello"), ctx) == b"hello"


async def test_bytes_passthrough(ctx):
    assert await runtime.afirst(ToBytes(b"raw"), ctx) == b"raw"


async def test_bytes_from_int_iterable(ctx):
    assert await runtime.afirst(ToBytes([72, 105]), ctx) == b"Hi"


# ---------------------------------------------------------------------------
# Collection conversions
# ---------------------------------------------------------------------------


async def test_list_from_tuple(ctx):
    assert await runtime.afirst(ToList((1, 2, 3)), ctx) == [1, 2, 3]


async def test_list_from_str(ctx):
    assert await runtime.afirst(ToList("abc"), ctx) == ["a", "b", "c"]


async def test_set_from_list(ctx):
    assert await runtime.afirst(ToSet([1, 2, 2, 3]), ctx) == {1, 2, 3}


async def test_tuple_from_list(ctx):
    assert await runtime.afirst(ToTuple([1, 2, 3]), ctx) == (1, 2, 3)


# ---------------------------------------------------------------------------
# Collection conversion TypeError raises (non-iterable)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls", [ToList, ToSet, ToTuple])
async def test_collection_from_non_iterable_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await runtime.afirst(op_cls(42), ctx)
