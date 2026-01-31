"""Tests for Seq."""

from every_flow import Seq
from everyabc import Context

from .conftest import Recorder


async def test_seq_executes_in_order():
    log = []
    tree = Seq(Recorder(log, "a"), Recorder(log, "b"), Recorder(log, "c"))
    await tree.execute(Context())
    assert log == ["a", "b", "c"]


async def test_seq_empty():
    tree = Seq()
    await tree.execute(Context())  # no-op, no error


async def test_seq_single():
    log = []
    tree = Seq(Recorder(log, "only"))
    await tree.execute(Context())
    assert log == ["only"]


def test_seq_children_count():
    tree = Seq(Seq(), Seq(), Seq())
    assert tree.child_count == 3
