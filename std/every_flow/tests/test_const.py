"""Tests for Const."""

from every_flow import Const
from everyabc import Context


def test_const_int():
    c = Const(42)
    assert c.execute(Context()) == 42


def test_const_str():
    c = Const("hello")
    assert c.execute(Context()) == "hello"


def test_const_bool():
    assert Const(True).execute(Context()) is True
    assert Const(False).execute(Context()) is False


def test_const_none():
    assert Const(None).execute(Context()) is None


def test_const_is_pure():
    assert Const(1).is_pure is True


def test_const_is_leaf():
    assert Const(1).is_leaf is True


def test_const_repr():
    assert repr(Const(42)) == "Const(42)"
    assert repr(Const("hi")) == "Const('hi')"
