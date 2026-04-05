"""Tests for attribute access ops.

GetAttrOp (Calc, pure), SetAttrOp (Cmd, impure), DelAttrOp (Cmd, impure).
"""

from __future__ import annotations

import pytest

from nu import Value
from nu.ops.attr import DelAttrOp, GetAttrOp, SetAttrOp


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
    assert await GetAttrOp(Value(obj), "name").execute(ctx) == "alice"


async def test_get_attr_missing_raises(ctx):
    obj = Obj()
    with pytest.raises(AttributeError):
        await GetAttrOp(Value(obj), "missing").execute(ctx)


# ---------------------------------------------------------------------------
# SetAttrOp
# ---------------------------------------------------------------------------


async def test_set_attr(ctx):
    obj = Obj()
    await SetAttrOp(Value(obj), "x", 42).execute(ctx)
    assert obj.x == 42  # type: ignore


async def test_set_attr_overwrite(ctx):
    obj = Obj(x=1)
    await SetAttrOp(Value(obj), "x", 2).execute(ctx)
    assert obj.x == 2  # type: ignore


# ---------------------------------------------------------------------------
# DelAttrOp
# ---------------------------------------------------------------------------


async def test_del_attr(ctx):
    obj = Obj(x=1)
    await DelAttrOp(Value(obj), "x").execute(ctx)
    assert not hasattr(obj, "x")


async def test_del_attr_missing_raises(ctx):
    obj = Obj()
    with pytest.raises(AttributeError):
        await DelAttrOp(Value(obj), "missing").execute(ctx)


# ---------------------------------------------------------------------------
# Purity
# ---------------------------------------------------------------------------


def test_get_attr_is_pure():
    assert GetAttrOp(Value(None), "x").is_self_pure is True


def test_set_attr_is_impure():
    assert SetAttrOp(Value(None), "x", 1).is_self_pure is False


def test_del_attr_is_impure():
    assert DelAttrOp(Value(None), "x").is_self_pure is False
