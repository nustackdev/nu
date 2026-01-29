"""Tests for While and ForRange."""

from every_flow import Const, ForRange, Var, While
from everyabc import Context

from .conftest import Recorder


# --- While ---


async def test_while_false_condition():
    log = []
    tree = While(False, Recorder(log, "body"))
    await tree.execute(Context())
    assert log == []


async def test_while_with_var_condition():
    log = []
    counter = Var(3)

    class Decrement(Recorder):
        async def execute(self, ctx):
            await super().execute(ctx)
            counter.set(counter.get() - 1)

    tree = While(counter, Decrement(log, "tick"))
    await tree.execute(Context())
    assert log == ["tick", "tick", "tick"]
    assert counter.get() == 0


def test_while_children_layout():
    tree = While(True, Recorder([], "body"))
    # children: [Const(True), body]
    assert tree.child_count == 2
    assert isinstance(tree.children[0], Const)


# --- ForRange ---


async def test_for_range_basic():
    log = []
    tree = ForRange(0, 3, Recorder(log, "step"))
    await tree.execute(Context())
    assert log == ["step", "step", "step"]


async def test_for_range_with_index():
    idx = Var(0)
    collected = []

    class Collector(Recorder):
        async def execute(self, ctx):
            collected.append(idx.get())

    tree = ForRange(0, 5, Collector([], "c"), index=idx)
    await tree.execute(Context())
    assert collected == [0, 1, 2, 3, 4]


async def test_for_range_with_step():
    idx = Var(0)
    collected = []

    class Collector(Recorder):
        async def execute(self, ctx):
            collected.append(idx.get())

    tree = ForRange(0, 10, Collector([], "c"), step=3, index=idx)
    await tree.execute(Context())
    assert collected == [0, 3, 6, 9]


async def test_for_range_empty():
    log = []
    tree = ForRange(0, 0, Recorder(log, "step"))
    await tree.execute(Context())
    assert log == []


async def test_for_range_with_term_params():
    log = []
    tree = ForRange(Const(1), Const(4), Recorder(log, "step"), step=Const(1))
    await tree.execute(Context())
    assert log == ["step", "step", "step"]


def test_for_range_children_layout():
    tree = ForRange(0, 10, Recorder([], "body"), step=2)
    # children: [Const(0), Const(10), Const(2), body]
    assert tree.child_count == 4
    assert isinstance(tree.children[0], Const)
    assert isinstance(tree.children[1], Const)
    assert isinstance(tree.children[2], Const)
