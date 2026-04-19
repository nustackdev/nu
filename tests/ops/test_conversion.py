"""Tests for conversion ops.

Primitive: ToIntOp, ToFloatOp, ToBoolOp, ToStrOp, ToBytesOp
Collection: ToListOp, ToSetOp, ToTupleOp

Ops don't catch exceptions. Bad conversions raise (ValueError, TypeError).
"""

from __future__ import annotations

import nu

import pytest

from nu.ops import (
    ToBoolOp,
    ToBytesOp,
    ToFloatOp,
    ToIntOp,
    ToListOp,
    ToSetOp,
    ToStrOp,
    ToTupleOp,
)


# ---------------------------------------------------------------------------
# ToIntOp
# ---------------------------------------------------------------------------


async def test_int_from_int(ctx):
    assert await nu.first(ToIntOp(42), ctx) == 42


async def test_int_from_float(ctx):
    assert await nu.first(ToIntOp(3.7), ctx) == 3


async def test_int_from_str(ctx):
    assert await nu.first(ToIntOp("123"), ctx) == 123


async def test_int_from_bool(ctx):
    assert await nu.first(ToIntOp(True), ctx) == 1


async def test_int_from_bad_str_raises(ctx):
    with pytest.raises(ValueError):
        await nu.first(ToIntOp("hello"), ctx)


# ---------------------------------------------------------------------------
# ToFloatOp
# ---------------------------------------------------------------------------


async def test_float_from_int(ctx):
    assert await nu.first(ToFloatOp(5), ctx) == 5.0


async def test_float_from_str(ctx):
    assert await nu.first(ToFloatOp("3.14"), ctx) == 3.14


async def test_float_from_bad_str_raises(ctx):
    with pytest.raises(ValueError):
        await nu.first(ToFloatOp("hello"), ctx)


# ---------------------------------------------------------------------------
# ToBoolOp
# ---------------------------------------------------------------------------


async def test_bool_truthy(ctx):
    assert await nu.first(ToBoolOp(1), ctx) is True


async def test_bool_falsy(ctx):
    assert await nu.first(ToBoolOp(0), ctx) is False


async def test_bool_empty_str(ctx):
    assert await nu.first(ToBoolOp(""), ctx) is False


async def test_bool_nonempty_str(ctx):
    assert await nu.first(ToBoolOp("x"), ctx) is True


# ---------------------------------------------------------------------------
# ToStrOp
# ---------------------------------------------------------------------------


async def test_str_from_int(ctx):
    assert await nu.first(ToStrOp(42), ctx) == "42"


async def test_str_from_float(ctx):
    assert await nu.first(ToStrOp(3.14), ctx) == "3.14"


async def test_str_from_none(ctx):
    assert await nu.first(ToStrOp(None), ctx) == "None"


# ---------------------------------------------------------------------------
# ToBytesOp
# ---------------------------------------------------------------------------


async def test_bytes_from_str(ctx):
    assert await nu.first(ToBytesOp("hello"), ctx) == b"hello"


async def test_bytes_passthrough(ctx):
    assert await nu.first(ToBytesOp(b"raw"), ctx) == b"raw"


async def test_bytes_from_int_iterable(ctx):
    assert await nu.first(ToBytesOp([72, 105]), ctx) == b"Hi"


# ---------------------------------------------------------------------------
# Collection conversions
# ---------------------------------------------------------------------------


async def test_list_from_tuple(ctx):
    assert await nu.first(ToListOp((1, 2, 3)), ctx) == [1, 2, 3]


async def test_list_from_str(ctx):
    assert await nu.first(ToListOp("abc"), ctx) == ["a", "b", "c"]


async def test_set_from_list(ctx):
    assert await nu.first(ToSetOp([1, 2, 2, 3]), ctx) == {1, 2, 3}


async def test_tuple_from_list(ctx):
    assert await nu.first(ToTupleOp([1, 2, 3]), ctx) == (1, 2, 3)


# ---------------------------------------------------------------------------
# Collection conversion TypeError raises (non-iterable)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls", [ToListOp, ToSetOp, ToTupleOp])
async def test_collection_from_non_iterable_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await nu.first(op_cls(42), ctx)
