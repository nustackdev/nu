"""Tests for Const."""

from every_flow import Const
from everybase import Context


async def test_const_int():
    c = Const(42)
    assert await c.execute(Context()) == 42


async def test_const_str():
    c = Const("hello")
    assert await c.execute(Context()) == "hello"


async def test_const_bool():
    assert await Const(True).execute(Context()) is True
    assert await Const(False).execute(Context()) is False


async def test_const_none():
    assert await Const(None).execute(Context()) is None


def test_const_is_pure():
    assert Const(1).is_self_pure is True


def test_const_is_leaf():
    assert Const(1).is_leaf is True


def test_const_repr():
    assert repr(Const(42)) == "Const(42)"
    assert repr(Const("hi")) == "Const('hi')"
