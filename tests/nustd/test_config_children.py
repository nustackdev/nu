"""Config a node works with is a child: Print's options, Log's extra, a queue's
capacity, a ui placed op's anchor. None of it is stored on the node besides
its children, so each can be computed in the tree.
"""

from __future__ import annotations

import io
import logging as pylogging

import nu
import nustd
from nu.core.io import STDOUT, Print, StdioBackend
from nustd.logging import Log


class Opts(nu.Shape):
    sep = nu.StrRef.slot()


def test_print_options_are_its_last_three_children() -> None:
    node = Print(STDOUT, "a", "b", sep="-", end="!", flush=True)
    assert [c.value for c in nu.tree.children(node)[-3:]] == ["-", "!", True]
    assert not nu.tree.fields(node)


def test_a_print_separator_can_be_read_from_the_tree() -> None:
    out = io.StringIO()
    ctx = nu.Context().bind(StdioBackend, StdioBackend(stdout=out))
    nu.run(nu.Frame(Opts, Print(STDOUT, "a", "b", sep=Opts.sep), sep="+"), ctx)
    assert out.getvalue() == "a+b\n"


def test_log_extra_is_always_the_last_child() -> None:
    plain = Log("info", "nu.t", "hi %s", "x")
    with_extra = Log("info", "nu.t", "hi %s", "x", extra={"k": 1})
    assert nu.tree.children(plain)[-1].value == {}
    assert nu.tree.children(with_extra)[-1].value == {"k": 1}
    # the args sit between msg and extra
    assert [c.value for c in nu.tree.children(with_extra)[4:-1]] == ["x"]


def test_log_extra_reaches_the_record(caplog) -> None:
    with caplog.at_level(pylogging.INFO, logger="nu.t"):
        nu.run(Log("info", "nu.t", "hi %s", "x", extra={"k": 1}))
    (record,) = caplog.records
    assert record.getMessage() == "hi x"
    assert record.k == 1


def test_queue_capacity_is_a_child_after_the_address() -> None:
    class Buf(nu.Shape):
        queue = nustd.queue.JQueueRef.slot(capacity=2, item_type=int)

    assert nu.tree.children(Buf.queue)[2].value == 2
    ctx = nu.Context().bind(dict, {}, Buf)
    q = nu.run(Buf.queue, ctx)[0]
    assert q.maxsize == 2


def test_a_placed_op_anchor_is_its_last_child() -> None:
    lst = nustd.ui.ListRef("l")
    assert nu.tree.children(lst.insert("a", at=0))[-1].value == "at"
    assert nu.tree.children(lst.insert("a", before=2))[-1].value == "before"
    assert nu.tree.children(lst.insert("a"))[-1].value is None
    assert not nu.tree.fields(lst.insert("a", at=0))
