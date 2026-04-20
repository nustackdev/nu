"""Tests for collection access ops.

AtOp, SliceOp, LenOp, ContainsOp.
"""

from __future__ import annotations

import pytest

from nu.ops import AtOp, ContainsOp, LenOp, SliceOp


# ---------------------------------------------------------------------------
# LenOp
# ---------------------------------------------------------------------------


async def test_len_list(ctx):
    assert await LenOp([1, 2, 3]).first(ctx) == 3


async def test_len_str(ctx):
    assert await LenOp("hello").first(ctx) == 5


async def test_len_dict(ctx):
    assert await LenOp({"a": 1, "b": 2}).first(ctx) == 2


async def test_len_empty(ctx):
    assert await LenOp([]).first(ctx) == 0


async def test_len_non_sized_raises(ctx):
    with pytest.raises(TypeError):
        await LenOp(42).first(ctx)


# ---------------------------------------------------------------------------
# AtOp
# ---------------------------------------------------------------------------


async def test_at_list_index(ctx):
    assert await AtOp([10, 20, 30], 1).first(ctx) == 20


async def test_at_dict_key(ctx):
    assert await AtOp({"a": 1, "b": 2}, "b").first(ctx) == 2


async def test_at_str_index(ctx):
    assert await AtOp("hello", 0).first(ctx) == "h"


async def test_at_list_out_of_bounds_raises(ctx):
    with pytest.raises(IndexError):
        await AtOp([1, 2], 10).first(ctx)


async def test_at_dict_missing_key_raises(ctx):
    with pytest.raises(KeyError):
        await AtOp({"a": 1}, "missing").first(ctx)


async def test_at_non_subscriptable_raises(ctx):
    with pytest.raises(TypeError):
        await AtOp(42, 0).first(ctx)


# ---------------------------------------------------------------------------
# SliceOp
# ---------------------------------------------------------------------------


async def test_slice_list(ctx):
    assert await SliceOp([1, 2, 3, 4, 5], 1, 4, None).first(ctx) == [2, 3, 4]


async def test_slice_str(ctx):
    assert await SliceOp("hello", 1, 3, None).first(ctx) == "el"


async def test_slice_with_step(ctx):
    assert await SliceOp([1, 2, 3, 4, 5], None, None, 2).first(ctx) == [1, 3, 5]


async def test_slice_non_sliceable_raises(ctx):
    with pytest.raises(TypeError):
        await SliceOp(42, 0, 1, None).first(ctx)


# ---------------------------------------------------------------------------
# ContainsOp
# ---------------------------------------------------------------------------


async def test_contains_list(ctx):
    assert await ContainsOp([1, 2, 3], 2).first(ctx) is True


async def test_contains_list_missing(ctx):
    assert await ContainsOp([1, 2, 3], 5).first(ctx) is False


async def test_contains_dict_key(ctx):
    assert await ContainsOp({"a": 1}, "a").first(ctx) is True


async def test_contains_str_substring(ctx):
    assert await ContainsOp("hello world", "world").first(ctx) is True


async def test_contains_set(ctx):
    assert await ContainsOp({1, 2, 3}, 2).first(ctx) is True
