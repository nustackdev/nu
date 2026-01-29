"""Tests for If."""

from every_flow import Const, If, Seq, Var
from everyabc import Context

from .conftest import Recorder


async def test_if_true():
    log = []
    tree = If(True, Recorder(log, "then"))
    await tree.execute(Context())
    assert log == ["then"]


async def test_if_false_no_else():
    log = []
    tree = If(False, Recorder(log, "then"))
    await tree.execute(Context())
    assert log == []


async def test_if_false_with_else():
    log = []
    tree = If(False, Recorder(log, "then"), Recorder(log, "else"))
    await tree.execute(Context())
    assert log == ["else"]


async def test_if_true_with_else():
    log = []
    tree = If(True, Recorder(log, "then"), Recorder(log, "else"))
    await tree.execute(Context())
    assert log == ["then"]


async def test_if_with_term_condition():
    log = []
    cond = Const(True)
    tree = If(cond, Recorder(log, "then"))
    await tree.execute(Context())
    assert log == ["then"]


async def test_if_with_var_condition():
    log = []
    flag = Var(True)
    tree = If(flag, Recorder(log, "then"), Recorder(log, "else"))
    await tree.execute(Context())
    assert log == ["then"]

    log.clear()
    flag.set(False)
    await tree.execute(Context())
    assert log == ["else"]


def test_if_condition_is_child():
    tree = If(True, Seq())
    # children[0] should be Const(True), children[1] should be Seq
    assert tree.child_count == 2
    assert isinstance(tree.children[0], Const)
