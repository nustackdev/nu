"""Tests for collection access ops.

At, Slice, Len, Contains.
"""

from __future__ import annotations

import pytest

from nu import runtime
from nu.interactions import At, Contains, Len, Slice


# ---------------------------------------------------------------------------
# Len
# ---------------------------------------------------------------------------


async def test_len_list(ctx):
    assert await runtime.afirst(Len([1, 2, 3]), ctx) == 3


async def test_len_str(ctx):
    assert await runtime.afirst(Len("hello"), ctx) == 5


async def test_len_dict(ctx):
    assert await runtime.afirst(Len({"a": 1, "b": 2}), ctx) == 2


async def test_len_empty(ctx):
    assert await runtime.afirst(Len([]), ctx) == 0


async def test_len_non_sized_raises(ctx):
    with pytest.raises(TypeError):
        await runtime.afirst(Len(42), ctx)


# ---------------------------------------------------------------------------
# At
# ---------------------------------------------------------------------------


async def test_at_list_index(ctx):
    assert await runtime.afirst(At([10, 20, 30], 1), ctx) == 20


async def test_at_dict_key(ctx):
    assert await runtime.afirst(At({"a": 1, "b": 2}, "b"), ctx) == 2


async def test_at_str_index(ctx):
    assert await runtime.afirst(At("hello", 0), ctx) == "h"


async def test_at_list_out_of_bounds_raises(ctx):
    with pytest.raises(IndexError):
        await runtime.afirst(At([1, 2], 10), ctx)


async def test_at_dict_missing_key_raises(ctx):
    with pytest.raises(KeyError):
        await runtime.afirst(At({"a": 1}, "missing"), ctx)


async def test_at_non_subscriptable_raises(ctx):
    with pytest.raises(TypeError):
        await runtime.afirst(At(42, 0), ctx)


# ---------------------------------------------------------------------------
# Slice
# ---------------------------------------------------------------------------


async def test_slice_list(ctx):
    assert await runtime.afirst(Slice([1, 2, 3, 4, 5], 1, 4, None), ctx) == [2, 3, 4]


async def test_slice_str(ctx):
    assert await runtime.afirst(Slice("hello", 1, 3, None), ctx) == "el"


async def test_slice_with_step(ctx):
    assert await runtime.afirst(Slice([1, 2, 3, 4, 5], None, None, 2), ctx) == [1, 3, 5]


async def test_slice_non_sliceable_raises(ctx):
    with pytest.raises(TypeError):
        await runtime.afirst(Slice(42, 0, 1, None), ctx)


# ---------------------------------------------------------------------------
# Contains
# ---------------------------------------------------------------------------


async def test_contains_list(ctx):
    assert await runtime.afirst(Contains([1, 2, 3], 2), ctx) is True


async def test_contains_list_missing(ctx):
    assert await runtime.afirst(Contains([1, 2, 3], 5), ctx) is False


async def test_contains_dict_key(ctx):
    assert await runtime.afirst(Contains({"a": 1}, "a"), ctx) is True


async def test_contains_str_substring(ctx):
    assert await runtime.afirst(Contains("hello world", "world"), ctx) is True


async def test_contains_set(ctx):
    assert await runtime.afirst(Contains({1, 2, 3}, 2), ctx) is True
