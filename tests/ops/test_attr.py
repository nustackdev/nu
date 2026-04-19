"""Tests for attribute access ops.

GetAttrOp (Calc, pure), SetAttrOp (Cmd, impure), DelAttrOp (Cmd, impure).
"""

from __future__ import annotations

import nu

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
    assert await nu.first(GetAttrOp(Literal(obj), "name"), ctx) == "alice"


async def test_get_attr_missing_raises(ctx):
    obj = Obj()
    with pytest.raises(AttributeError):
        await nu.first(GetAttrOp(Literal(obj), "missing"), ctx)


# ---------------------------------------------------------------------------
# SetAttrOp
# ---------------------------------------------------------------------------


async def test_set_attr(ctx):
    obj = Obj()
    await nu.first(SetAttrOp(Literal(obj), "x", 42), ctx)
    assert obj.x == 42  # type: ignore


async def test_set_attr_overwrite(ctx):
    obj = Obj(x=1)
    await nu.first(SetAttrOp(Literal(obj), "x", 2), ctx)
    assert obj.x == 2  # type: ignore


# ---------------------------------------------------------------------------
# DelAttrOp
# ---------------------------------------------------------------------------


async def test_del_attr(ctx):
    obj = Obj(x=1)
    await nu.first(DelAttrOp(Literal(obj), "x"), ctx)
    assert not hasattr(obj, "x")


async def test_del_attr_missing_raises(ctx):
    obj = Obj()
    with pytest.raises(AttributeError):
        await nu.first(DelAttrOp(Literal(obj), "missing"), ctx)


