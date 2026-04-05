"""Tests for conversion ops.

Primitive: ToIntOp, ToFloatOp, ToBoolOp, ToStrOp, ToBytesOp
Collection: ToListOp, ToSetOp, ToTupleOp

Ops don't catch exceptions. Bad conversions raise (ValueError, TypeError).
"""

from __future__ import annotations

import pytest

from nu.ops.conversion import (
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
    assert await ToIntOp(42).execute(ctx) == 42


async def test_int_from_float(ctx):
    assert await ToIntOp(3.7).execute(ctx) == 3


async def test_int_from_str(ctx):
    assert await ToIntOp("123").execute(ctx) == 123


async def test_int_from_bool(ctx):
    assert await ToIntOp(True).execute(ctx) == 1


async def test_int_from_bad_str_raises(ctx):
    with pytest.raises(ValueError):
        await ToIntOp("hello").execute(ctx)


# ---------------------------------------------------------------------------
# ToFloatOp
# ---------------------------------------------------------------------------


async def test_float_from_int(ctx):
    assert await ToFloatOp(5).execute(ctx) == 5.0


async def test_float_from_str(ctx):
    assert await ToFloatOp("3.14").execute(ctx) == 3.14


async def test_float_from_bad_str_raises(ctx):
    with pytest.raises(ValueError):
        await ToFloatOp("hello").execute(ctx)


# ---------------------------------------------------------------------------
# ToBoolOp
# ---------------------------------------------------------------------------


async def test_bool_truthy(ctx):
    assert await ToBoolOp(1).execute(ctx) is True


async def test_bool_falsy(ctx):
    assert await ToBoolOp(0).execute(ctx) is False


async def test_bool_empty_str(ctx):
    assert await ToBoolOp("").execute(ctx) is False


async def test_bool_nonempty_str(ctx):
    assert await ToBoolOp("x").execute(ctx) is True


# ---------------------------------------------------------------------------
# ToStrOp
# ---------------------------------------------------------------------------


async def test_str_from_int(ctx):
    assert await ToStrOp(42).execute(ctx) == "42"


async def test_str_from_float(ctx):
    assert await ToStrOp(3.14).execute(ctx) == "3.14"


async def test_str_from_none(ctx):
    assert await ToStrOp(None).execute(ctx) == "None"


# ---------------------------------------------------------------------------
# ToBytesOp
# ---------------------------------------------------------------------------


async def test_bytes_from_str(ctx):
    assert await ToBytesOp("hello").execute(ctx) == b"hello"


async def test_bytes_passthrough(ctx):
    assert await ToBytesOp(b"raw").execute(ctx) == b"raw"


async def test_bytes_from_int_iterable(ctx):
    assert await ToBytesOp([72, 105]).execute(ctx) == b"Hi"


# ---------------------------------------------------------------------------
# Collection conversions
# ---------------------------------------------------------------------------


async def test_list_from_tuple(ctx):
    assert await ToListOp((1, 2, 3)).execute(ctx) == [1, 2, 3]


async def test_list_from_str(ctx):
    assert await ToListOp("abc").execute(ctx) == ["a", "b", "c"]


async def test_set_from_list(ctx):
    assert await ToSetOp([1, 2, 2, 3]).execute(ctx) == {1, 2, 3}


async def test_tuple_from_list(ctx):
    assert await ToTupleOp([1, 2, 3]).execute(ctx) == (1, 2, 3)


# ---------------------------------------------------------------------------
# Collection conversion TypeError raises (non-iterable)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls", [ToListOp, ToSetOp, ToTupleOp])
async def test_collection_from_non_iterable_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await op_cls(42).execute(ctx)
