"""Tests for conversion ops.

Primitive: ToInt, ToFloat, ToBool, ToStr, ToBytes
Collection: ToList, ToSet, ToTuple

Ops don't catch exceptions. Bad conversions raise (ValueError, TypeError).
"""

from __future__ import annotations

import pytest

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
    assert await ToInt(42).first(ctx) == 42


async def test_int_from_float(ctx):
    assert await ToInt(3.7).first(ctx) == 3


async def test_int_from_str(ctx):
    assert await ToInt("123").first(ctx) == 123


async def test_int_from_bool(ctx):
    assert await ToInt(True).first(ctx) == 1


async def test_int_from_bad_str_raises(ctx):
    with pytest.raises(ValueError):
        await ToInt("hello").first(ctx)


# ---------------------------------------------------------------------------
# ToFloat
# ---------------------------------------------------------------------------


async def test_float_from_int(ctx):
    assert await ToFloat(5).first(ctx) == 5.0


async def test_float_from_str(ctx):
    assert await ToFloat("3.14").first(ctx) == 3.14


async def test_float_from_bad_str_raises(ctx):
    with pytest.raises(ValueError):
        await ToFloat("hello").first(ctx)


# ---------------------------------------------------------------------------
# ToBool
# ---------------------------------------------------------------------------


async def test_bool_truthy(ctx):
    assert await ToBool(1).first(ctx) is True


async def test_bool_falsy(ctx):
    assert await ToBool(0).first(ctx) is False


async def test_bool_empty_str(ctx):
    assert await ToBool("").first(ctx) is False


async def test_bool_nonempty_str(ctx):
    assert await ToBool("x").first(ctx) is True


# ---------------------------------------------------------------------------
# ToStr
# ---------------------------------------------------------------------------


async def test_str_from_int(ctx):
    assert await ToStr(42).first(ctx) == "42"


async def test_str_from_float(ctx):
    assert await ToStr(3.14).first(ctx) == "3.14"


async def test_str_from_none(ctx):
    assert await ToStr(None).first(ctx) == "None"


# ---------------------------------------------------------------------------
# ToBytes
# ---------------------------------------------------------------------------


async def test_bytes_from_str(ctx):
    assert await ToBytes("hello").first(ctx) == b"hello"


async def test_bytes_passthrough(ctx):
    assert await ToBytes(b"raw").first(ctx) == b"raw"


async def test_bytes_from_int_iterable(ctx):
    assert await ToBytes([72, 105]).first(ctx) == b"Hi"


# ---------------------------------------------------------------------------
# Collection conversions
# ---------------------------------------------------------------------------


async def test_list_from_tuple(ctx):
    assert await ToList((1, 2, 3)).first(ctx) == [1, 2, 3]


async def test_list_from_str(ctx):
    assert await ToList("abc").first(ctx) == ["a", "b", "c"]


async def test_set_from_list(ctx):
    assert await ToSet([1, 2, 2, 3]).first(ctx) == {1, 2, 3}


async def test_tuple_from_list(ctx):
    assert await ToTuple([1, 2, 3]).first(ctx) == (1, 2, 3)


# ---------------------------------------------------------------------------
# Collection conversion TypeError raises (non-iterable)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls", [ToList, ToSet, ToTuple])
async def test_collection_from_non_iterable_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await op_cls(42).first(ctx)
