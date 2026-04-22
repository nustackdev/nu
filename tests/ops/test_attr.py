"""Tests for attribute access ops.

GetAttr (Calc, pure), SetAttr (Cmd, impure), DelAttr (Cmd, impure).
"""

from __future__ import annotations

import pytest

from nu import Literal
from nu.interactions import DelAttr, GetAttr, SetAttr


# ---------------------------------------------------------------------------
# Test object
# ---------------------------------------------------------------------------


class Obj:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# GetAttr
# ---------------------------------------------------------------------------


async def test_get_attr(ctx):
    obj = Obj(name="alice")
    assert await GetAttr(Literal(obj), "name").first(ctx) == "alice"


async def test_get_attr_missing_raises(ctx):
    obj = Obj()
    with pytest.raises(AttributeError):
        await GetAttr(Literal(obj), "missing").first(ctx)


# ---------------------------------------------------------------------------
# SetAttr
# ---------------------------------------------------------------------------


async def test_set_attr(ctx):
    obj = Obj()
    await SetAttr(Literal(obj), "x", 42).first(ctx)
    assert obj.x == 42  # type: ignore


async def test_set_attr_overwrite(ctx):
    obj = Obj(x=1)
    await SetAttr(Literal(obj), "x", 2).first(ctx)
    assert obj.x == 2  # type: ignore


# ---------------------------------------------------------------------------
# DelAttr
# ---------------------------------------------------------------------------


async def test_del_attr(ctx):
    obj = Obj(x=1)
    await DelAttr(Literal(obj), "x").first(ctx)
    assert not hasattr(obj, "x")


async def test_del_attr_missing_raises(ctx):
    obj = Obj()
    with pytest.raises(AttributeError):
        await DelAttr(Literal(obj), "missing").first(ctx)
