"""Tests for attribute access ops.

GetAttrOp (Calc, pure), SetAttrOp (Cmd, impure), DelAttrOp (Cmd, impure).
"""

from __future__ import annotations

import pytest

from nu import Literal
from nu.ops import DelAttrOp, GetAttrOp, SetAttrOp


# ---------------------------------------------------------------------------
# Test object
# ---------------------------------------------------------------------------


class Obj:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# GetAttrOp
# ---------------------------------------------------------------------------


async def test_get_attr(ctx):
    obj = Obj(name="alice")
    assert await GetAttrOp(Literal(obj), "name").first(ctx) == "alice"


async def test_get_attr_missing_raises(ctx):
    obj = Obj()
    with pytest.raises(AttributeError):
        await GetAttrOp(Literal(obj), "missing").first(ctx)


# ---------------------------------------------------------------------------
# SetAttrOp
# ---------------------------------------------------------------------------


async def test_set_attr(ctx):
    obj = Obj()
    await SetAttrOp(Literal(obj), "x", 42).first(ctx)
    assert obj.x == 42  # type: ignore


async def test_set_attr_overwrite(ctx):
    obj = Obj(x=1)
    await SetAttrOp(Literal(obj), "x", 2).first(ctx)
    assert obj.x == 2  # type: ignore


# ---------------------------------------------------------------------------
# DelAttrOp
# ---------------------------------------------------------------------------


async def test_del_attr(ctx):
    obj = Obj(x=1)
    await DelAttrOp(Literal(obj), "x").first(ctx)
    assert not hasattr(obj, "x")


async def test_del_attr_missing_raises(ctx):
    obj = Obj()
    with pytest.raises(AttributeError):
        await DelAttrOp(Literal(obj), "missing").first(ctx)
