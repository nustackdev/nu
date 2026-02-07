"""Tests for Var."""

from eb_flow import Var
from everybase import EMPTY, Context


def test_var_init_with_value():
    v = Var(42)
    assert v.get() == 42


def test_var_init_default_empty():
    v = Var()
    assert v.get() is EMPTY


def test_var_set_get():
    v = Var(0)
    v.set(99)
    assert v.get() == 99


async def test_var_fetch():
    v = Var(7)
    assert await v.fetch(Context()) == 7


async def test_var_execute():
    v = Var(7)
    assert await v.execute(Context()) == 7


async def test_var_set_then_execute():
    v = Var(0)
    v.set(42)
    assert await v.execute(Context()) == 42


def test_var_is_pure():
    assert Var(0).is_self_pure is True


def test_var_is_leaf():
    assert Var(0).is_leaf is True


async def test_var_resolve():
    v = Var(0)
    assert await v.resolve(Context()) == id(v)


def test_var_repr():
    assert repr(Var(42)) == "Var(42)"
    assert repr(Var("hi")) == "Var('hi')"
