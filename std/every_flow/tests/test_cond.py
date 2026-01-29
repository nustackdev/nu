"""Tests for If."""

from every_flow import Const, If, Var
from everyabc import Context

from .conftest import Recorder


def test_if_true():
    log = []
    tree = If(True, Recorder(log, "then"))
    tree.execute(Context())
    assert log == ["then"]


def test_if_false_no_else():
    log = []
    tree = If(False, Recorder(log, "then"))
    tree.execute(Context())
    assert log == []


def test_if_false_with_else():
    log = []
    tree = If(False, Recorder(log, "then"), Recorder(log, "else"))
    tree.execute(Context())
    assert log == ["else"]


def test_if_true_with_else():
    log = []
    tree = If(True, Recorder(log, "then"), Recorder(log, "else"))
    tree.execute(Context())
    assert log == ["then"]


def test_if_with_term_condition():
    log = []
    cond = Const(True)
    tree = If(cond, Recorder(log, "then"))
    tree.execute(Context())
    assert log == ["then"]


def test_if_with_var_condition():
    log = []
    flag = Var(True)
    tree = If(flag, Recorder(log, "then"), Recorder(log, "else"))
    tree.execute(Context())
    assert log == ["then"]

    log.clear()
    flag.set(False)
    tree.execute(Context())
    assert log == ["else"]


def test_if_condition_is_child():
    tree = If(True, Seq())
    # children[0] should be Const(True), children[1] should be Seq
    assert tree.child_count == 2
    assert isinstance(tree.children[0], Const)


# avoid circular import in test
from every_flow import Seq  # noqa: E402
