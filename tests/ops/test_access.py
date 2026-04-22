"""Tests for collection access ops.

At, Slice, Len, Contains.
"""

from __future__ import annotations

import pytest

from nu.interactions import At, Contains, Len, Slice


# ---------------------------------------------------------------------------
# Len
# ---------------------------------------------------------------------------


async def test_len_list(ctx):
    assert await Len([1, 2, 3]).first(ctx) == 3


async def test_len_str(ctx):
    assert await Len("hello").first(ctx) == 5


async def test_len_dict(ctx):
    assert await Len({"a": 1, "b": 2}).first(ctx) == 2


async def test_len_empty(ctx):
    assert await Len([]).first(ctx) == 0


async def test_len_non_sized_raises(ctx):
    with pytest.raises(TypeError):
        await Len(42).first(ctx)


# ---------------------------------------------------------------------------
# At
# ---------------------------------------------------------------------------


async def test_at_list_index(ctx):
    assert await At([10, 20, 30], 1).first(ctx) == 20


async def test_at_dict_key(ctx):
    assert await At({"a": 1, "b": 2}, "b").first(ctx) == 2


async def test_at_str_index(ctx):
    assert await At("hello", 0).first(ctx) == "h"


async def test_at_list_out_of_bounds_raises(ctx):
    with pytest.raises(IndexError):
        await At([1, 2], 10).first(ctx)


async def test_at_dict_missing_key_raises(ctx):
    with pytest.raises(KeyError):
        await At({"a": 1}, "missing").first(ctx)


async def test_at_non_subscriptable_raises(ctx):
    with pytest.raises(TypeError):
        await At(42, 0).first(ctx)


# ---------------------------------------------------------------------------
# Slice
# ---------------------------------------------------------------------------


async def test_slice_list(ctx):
    assert await Slice([1, 2, 3, 4, 5], 1, 4, None).first(ctx) == [2, 3, 4]


async def test_slice_str(ctx):
    assert await Slice("hello", 1, 3, None).first(ctx) == "el"


async def test_slice_with_step(ctx):
    assert await Slice([1, 2, 3, 4, 5], None, None, 2).first(ctx) == [1, 3, 5]


async def test_slice_non_sliceable_raises(ctx):
    with pytest.raises(TypeError):
        await Slice(42, 0, 1, None).first(ctx)


# ---------------------------------------------------------------------------
# Contains
# ---------------------------------------------------------------------------


async def test_contains_list(ctx):
    assert await Contains([1, 2, 3], 2).first(ctx) is True


async def test_contains_list_missing(ctx):
    assert await Contains([1, 2, 3], 5).first(ctx) is False


async def test_contains_dict_key(ctx):
    assert await Contains({"a": 1}, "a").first(ctx) is True


async def test_contains_str_substring(ctx):
    assert await Contains("hello world", "world").first(ctx) is True


async def test_contains_set(ctx):
    assert await Contains({1, 2, 3}, 2).first(ctx) is True
