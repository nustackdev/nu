"""Tests for attribute access ops.

GetAttr (Calc, pure), SetAttr (Cmd, impure), DelAttr (Cmd, impure).
"""

from __future__ import annotations

import pytest

from nu import Literal, runtime
from nu import DelAttr, GetAttr, SetAttr


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
    assert await runtime.afirst(GetAttr(Literal(obj), "name"), ctx) == "alice"


async def test_get_attr_missing_raises(ctx):
    obj = Obj()
    with pytest.raises(AttributeError):
        await runtime.afirst(GetAttr(Literal(obj), "missing"), ctx)


# ---------------------------------------------------------------------------
# SetAttr
# ---------------------------------------------------------------------------


async def test_set_attr(ctx):
    obj = Obj()
    await runtime.afirst(SetAttr(Literal(obj), "x", 42), ctx)
    assert obj.x == 42  # type: ignore


async def test_set_attr_overwrite(ctx):
    obj = Obj(x=1)
    await runtime.afirst(SetAttr(Literal(obj), "x", 2), ctx)
    assert obj.x == 2  # type: ignore


# ---------------------------------------------------------------------------
# DelAttr
# ---------------------------------------------------------------------------


async def test_del_attr(ctx):
    obj = Obj(x=1)
    await runtime.afirst(DelAttr(Literal(obj), "x"), ctx)
    assert not hasattr(obj, "x")


async def test_del_attr_missing_raises(ctx):
    obj = Obj()
    with pytest.raises(AttributeError):
        await runtime.afirst(DelAttr(Literal(obj), "missing"), ctx)
