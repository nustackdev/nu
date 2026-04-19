"""Tests for collection access ops.

AtOp, SliceOp, LenOp, ContainsOp.
"""

from __future__ import annotations

import nu

import pytest

from nu.ops import AtOp, ContainsOp, LenOp, SliceOp


# ---------------------------------------------------------------------------
# LenOp
# ---------------------------------------------------------------------------


async def test_len_list(ctx):
    assert await nu.first(LenOp([1, 2, 3]), ctx) == 3


async def test_len_str(ctx):
    assert await nu.first(LenOp("hello"), ctx) == 5


async def test_len_dict(ctx):
    assert await nu.first(LenOp({"a": 1, "b": 2}), ctx) == 2


async def test_len_empty(ctx):
    assert await nu.first(LenOp([]), ctx) == 0


async def test_len_non_sized_raises(ctx):
    with pytest.raises(TypeError):
        await nu.first(LenOp(42), ctx)


# ---------------------------------------------------------------------------
# AtOp
# ---------------------------------------------------------------------------


async def test_at_list_index(ctx):
    assert await nu.first(AtOp([10, 20, 30], 1), ctx) == 20


async def test_at_dict_key(ctx):
    assert await nu.first(AtOp({"a": 1, "b": 2}, "b"), ctx) == 2


async def test_at_str_index(ctx):
    assert await nu.first(AtOp("hello", 0), ctx) == "h"


async def test_at_list_out_of_bounds_raises(ctx):
    with pytest.raises(IndexError):
        await nu.first(AtOp([1, 2], 10), ctx)


async def test_at_dict_missing_key_raises(ctx):
    with pytest.raises(KeyError):
        await nu.first(AtOp({"a": 1}, "missing"), ctx)


async def test_at_non_subscriptable_raises(ctx):
    with pytest.raises(TypeError):
        await nu.first(AtOp(42, 0), ctx)


# ---------------------------------------------------------------------------
# SliceOp
# ---------------------------------------------------------------------------


async def test_slice_list(ctx):
    assert await nu.first(SliceOp([1, 2, 3, 4, 5], 1, 4, None), ctx) == [2, 3, 4]


async def test_slice_str(ctx):
    assert await nu.first(SliceOp("hello", 1, 3, None), ctx) == "el"


async def test_slice_with_step(ctx):
    assert await nu.first(SliceOp([1, 2, 3, 4, 5], None, None, 2), ctx) == [1, 3, 5]


async def test_slice_non_sliceable_raises(ctx):
    with pytest.raises(TypeError):
        await nu.first(SliceOp(42, 0, 1, None), ctx)


# ---------------------------------------------------------------------------
# ContainsOp
# ---------------------------------------------------------------------------


async def test_contains_list(ctx):
    assert await nu.first(ContainsOp([1, 2, 3], 2), ctx) is True


async def test_contains_list_missing(ctx):
    assert await nu.first(ContainsOp([1, 2, 3], 5), ctx) is False


async def test_contains_dict_key(ctx):
    assert await nu.first(ContainsOp({"a": 1}, "a"), ctx) is True


async def test_contains_str_substring(ctx):
    assert await nu.first(ContainsOp("hello world", "world"), ctx) is True


async def test_contains_set(ctx):
    assert await nu.first(ContainsOp({1, 2, 3}, 2), ctx) is True
